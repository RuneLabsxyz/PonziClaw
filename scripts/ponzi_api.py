#!/usr/bin/env python3
import json
import os
import sys
import urllib.request
import urllib.parse

PONZI_API = os.getenv("PUBLIC_PONZI_API_URL", "https://play.ponzis.fun").rstrip("/")
TORII = os.getenv("PUBLIC_DOJO_TORII_URL", "https://api.cartridge.gg/x/ponziland-mainnet-world-new/torii").rstrip("/")


def fetch_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "PonziClaw/0.1"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def post_json(url: str, payload: dict):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "PonziClaw/0.1"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read().decode("utf-8")
        try:
            return json.loads(raw)
        except Exception:
            return {"raw": raw}


def cmd_price():
    print(json.dumps(fetch_json(f"{PONZI_API}/price"), indent=2))


def cmd_torii_flow():
    # Conservative generic query placeholder; callers can override by editing.
    sql = os.getenv(
        "PONZI_FLOW_SQL",
        "SELECT COUNT(*) AS tx_count FROM events LIMIT 1",
    )
    print(json.dumps(post_json(f"{TORII}/sql", {"query": sql}), indent=2))


def cmd_snapshot():
    out = {"price": None, "flow": None, "errors": []}
    try:
        out["price"] = fetch_json(f"{PONZI_API}/price")
    except Exception as e:
        out["errors"].append(f"price_error: {e}")

    try:
        sql = os.getenv("PONZI_FLOW_SQL", "SELECT COUNT(*) AS tx_count FROM events LIMIT 1")
        out["flow"] = post_json(f"{TORII}/sql", {"query": sql})
    except Exception as e:
        out["errors"].append(f"flow_error: {e}")

    print(json.dumps(out, indent=2))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "snapshot"
    if cmd == "price":
        cmd_price()
    elif cmd == "torii-flow":
        cmd_torii_flow()
    elif cmd == "snapshot":
        cmd_snapshot()
    else:
        print("Usage: ponzi_api.py [price|torii-flow|snapshot]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
