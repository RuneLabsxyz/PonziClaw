#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

AVNU_URL = os.getenv("PUBLIC_AVNU_URL", "https://starknet.api.avnu.fi").rstrip("/")


def http_get_json(url: str):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "PonziClaw/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def http_post_json(url: str, payload: dict):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "PonziClaw/0.1"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def normalize_calls(raw):
    # AVNU returns starknet.js style calls in most cases.
    if isinstance(raw, dict) and "calls" in raw and isinstance(raw["calls"], list):
        calls = raw["calls"]
    elif isinstance(raw, list):
        calls = raw
    else:
        calls = []

    out = []
    for c in calls:
        contract = c.get("contractAddress") or c.get("to") or c.get("contract_address")
        entry = c.get("entrypoint") or c.get("entrypoint_name") or c.get("selector")
        calldata = c.get("calldata") or c.get("data") or []
        out.append(
            {
                "contractAddress": contract,
                "entrypoint": entry,
                "calldata": [str(x) for x in calldata],
            }
        )
    return {"calls": out}


def _to_hex_amount(v: str):
    if v is None:
        return None
    v = str(v).strip()
    if v.startswith("0x"):
        return v
    return hex(int(v))


def fetch_quotes(sell_token: str, buy_token: str, sell_amount: str = None, buy_amount: str = None):
    params = {
        "sellTokenAddress": sell_token,
        "buyTokenAddress": buy_token,
    }
    if sell_amount:
        params["sellAmount"] = _to_hex_amount(sell_amount)
    if buy_amount:
        params["buyAmount"] = _to_hex_amount(buy_amount)

    url = f"{AVNU_URL}/swap/v2/quotes?{urllib.parse.urlencode(params)}"
    return http_get_json(url)


def build_calls(quote_id: str, taker_address: str, slippage: float, include_approve: bool = True):
    # Endpoint shape follows AVNU v2 build transaction contract used by SDK.
    # Try canonical endpoint first, then fallback variants.
    payload = {
        "quoteId": quote_id,
        "takerAddress": taker_address,
        "slippage": slippage,
        "includeApprove": include_approve,
    }

    errors = []
    for ep in (
        f"{AVNU_URL}/swap/v2/build",
        f"{AVNU_URL}/swap/v2/build-transaction",
        f"{AVNU_URL}/swap/v2/execute",
    ):
        try:
            return http_post_json(ep, payload)
        except Exception as e:
            errors.append(f"{ep}: {e}")

    raise RuntimeError("Failed to build swap calls. Tried endpoints:\n" + "\n".join(errors))


def run_json(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or p.stdout.strip())
    return json.loads(p.stdout)


def controller_execute(calls_file: Path):
    out = run_json(["controller", "execute", "--file", str(calls_file), "--json"])
    tx = out.get("transaction_hash")
    return {"ok": True, "transaction_hash": tx, "voyager": f"https://voyager.online/tx/{tx}" if tx else None, "raw": out}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("quote")
    q.add_argument("--sell-token", required=True)
    q.add_argument("--buy-token", required=True)
    q.add_argument("--sell-amount")
    q.add_argument("--buy-amount")

    b = sub.add_parser("build-calls")
    b.add_argument("--quote-id", required=True)
    b.add_argument("--taker-address", required=True)
    b.add_argument("--slippage", type=float, default=0.01)
    b.add_argument("--include-approve", choices=["true", "false"], default="true")
    b.add_argument("--out", required=True)

    x = sub.add_parser("swap")
    x.add_argument("--sell-token", required=True)
    x.add_argument("--buy-token", required=True)
    x.add_argument("--sell-amount", required=True)
    x.add_argument("--taker-address", required=True)
    x.add_argument("--slippage", type=float, default=0.01)
    x.add_argument("--out", default="out/calls.swap.json")
    x.add_argument("--execute", action="store_true")
    x.add_argument("--confirm", action="store_true", help="Required with --execute")

    args = ap.parse_args()

    try:
        if args.cmd == "quote":
            if not args.sell_amount and not args.buy_amount:
                raise SystemExit("Provide --sell-amount or --buy-amount")
            quotes = fetch_quotes(args.sell_token, args.buy_token, args.sell_amount, args.buy_amount)
            print(json.dumps({"ok": True, "quotes": quotes}, indent=2))
            return

        if args.cmd == "build-calls":
            raw = build_calls(args.quote_id, args.taker_address, args.slippage, args.include_approve == "true")
            calls = normalize_calls(raw)
            out_path = Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(calls, indent=2), encoding="utf-8")
            print(json.dumps({"ok": True, "calls_file": str(out_path), "calls_count": len(calls.get("calls", []))}, indent=2))
            return

        # one-shot swap pipeline
        quotes = fetch_quotes(args.sell_token, args.buy_token, sell_amount=args.sell_amount)
        if not isinstance(quotes, list) or len(quotes) == 0:
            raise RuntimeError("No AVNU quote returned")
        quote = quotes[0]
        quote_id = quote.get("quoteId") or quote.get("quote_id")
        if not quote_id:
            raise RuntimeError("Quote does not contain quoteId")

        raw = build_calls(quote_id, args.taker_address, args.slippage, True)
        calls = normalize_calls(raw)
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(calls, indent=2), encoding="utf-8")

        result = {
            "ok": True,
            "quote_id": quote_id,
            "sell_amount": quote.get("sellAmount"),
            "buy_amount": quote.get("buyAmount"),
            "calls_file": str(out_path),
            "calls_count": len(calls.get("calls", [])),
        }

        if args.execute:
            if not args.confirm:
                raise RuntimeError("Refusing execute without --confirm")
            exec_result = controller_execute(out_path)
            result["execution"] = exec_result

        print(json.dumps(result, indent=2))

    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
