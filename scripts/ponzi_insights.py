#!/usr/bin/env python3
import argparse
import json
import os
import urllib.request

from ponzi_manifest import token_symbol

TORII = os.getenv("PUBLIC_DOJO_TORII_URL", "https://api.cartridge.gg/x/ponziland-mainnet-world-new/torii").rstrip("/")
PONZI_API = os.getenv("PUBLIC_PONZI_API_URL", "https://api.runelabs.xyz/ponziland-mainnet-temp/api").rstrip("/")


def torii_sql(query: str):
    req = urllib.request.Request(
        f"{TORII}/sql",
        data=query.encode("utf-8"),
        headers={"Content-Type": "text/plain", "User-Agent": "PonziClaw/0.1"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "PonziClaw/0.1"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))


def q_most_used_token(limit: int):
    return f"""
SELECT
  (em.data ->> '$.token_used') AS token,
  COUNT(*) AS trades,
  SUM(CAST((em.data ->> '$.sold_price') AS INTEGER)) AS gross_volume
FROM event_messages_historical em
LEFT JOIN models m ON em.model_id = m.id
WHERE m.name LIKE '%LandBoughtEvent%'
GROUP BY (em.data ->> '$.token_used')
ORDER BY trades DESC
LIMIT {limit}
""".strip()


def q_last_drops(limit: int):
    return f"""
SELECT
  em.created_at,
  (em.data ->> '$.owner_nuked') AS owner,
  (em.data ->> '$.land_location') AS land_location
FROM event_messages_historical em
LEFT JOIN models m ON em.model_id = m.id
WHERE m.name LIKE '%LandNukedEvent%'
ORDER BY em.created_at DESC
LIMIT {limit}
""".strip()


def q_account_land_health(account: str):
    return f"""
SELECT
  SUM(CASE WHEN (em.data ->> '$.buyer') = '{account}' THEN 1 ELSE 0 END) AS lands_bought,
  SUM(CASE WHEN (em.data ->> '$.seller') = '{account}' THEN 1 ELSE 0 END) AS lands_sold,
  SUM(CASE WHEN (em.data ->> '$.owner_nuked') = '{account}' THEN 1 ELSE 0 END) AS lands_nuked
FROM event_messages_historical em
LEFT JOIN models m ON em.model_id = m.id
WHERE
  m.name LIKE '%LandBoughtEvent%'
  OR m.name LIKE '%LandNukedEvent%'
""".strip()


def closed_pnl_from_api(account: str, limit: int):
    formatted = account
    if formatted.startswith("0x0") and len(formatted) == 66:
        formatted = "0x" + formatted[3:]

    positions = fetch_json(f"{PONZI_API}/land-historical/{formatted}")
    out = []
    for p in positions[:limit]:
        token = p.get("sale_token_used") or p.get("buy_token_used")
        out.append(
            {
                "id": p.get("id"),
                "land_location": p.get("land_location"),
                "close_date": p.get("close_date"),
                "close_reason": p.get("close_reason"),
                "token": token,
                "token_symbol": token_symbol(token) if token else None,
                "buy_cost_token": p.get("buy_cost_token"),
                "sale_revenue_token": p.get("sale_revenue_token"),
                "net_profit_token": p.get("net_profit_token"),
            }
        )
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["most-used-token", "last-drops", "land-health", "closed-pnl"])
    ap.add_argument("--account", help="Wallet/controller address for account-scoped queries")
    ap.add_argument("--limit", type=int, default=10)
    args = ap.parse_args()

    if args.command in {"land-health", "closed-pnl"} and not args.account:
        raise SystemExit("--account is required for land-health and closed-pnl")

    try:
        if args.command == "most-used-token":
            q = q_most_used_token(args.limit)
            data = torii_sql(q)
            if isinstance(data, list):
                for row in data:
                    token = row.get("token")
                    if token:
                        row["token_symbol"] = token_symbol(token)
        elif args.command == "last-drops":
            q = q_last_drops(args.limit)
            data = torii_sql(q)
        elif args.command == "land-health":
            q = q_account_land_health(args.account)
            data = torii_sql(q)
        else:
            q = None
            data = closed_pnl_from_api(args.account, args.limit)

        print(json.dumps({"ok": True, "command": args.command, "data": data}, indent=2))
    except Exception as e:
        print(json.dumps({"ok": False, "command": args.command, "error": str(e), "query": q if 'q' in locals() else None}, indent=2))


if __name__ == "__main__":
    main()
