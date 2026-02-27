#!/usr/bin/env python3
import argparse
import json
import os
import urllib.request

from ponzi_manifest import token_symbol

TORII = os.getenv("PUBLIC_DOJO_TORII_URL", "https://api.cartridge.gg/x/ponziland-mainnet-world-new/torii").rstrip("/")


def torii_sql(query: str):
    req = urllib.request.Request(
        f"{TORII}/sql",
        data=query.encode("utf-8"),
        headers={"Content-Type": "text/plain", "User-Agent": "PonziClaw/0.1"},
        method="POST",
    )
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


def q_closed_pnl(account: str, limit: int):
    # Approximation by location: sum sells - sum buys where both sides exist.
    return f"""
WITH bought AS (
  SELECT
    (em.data ->> '$.land_location') AS location,
    (em.data ->> '$.token_used') AS token,
    SUM(CAST((em.data ->> '$.sold_price') AS INTEGER)) AS total_buy
  FROM event_messages_historical em
  LEFT JOIN models m ON em.model_id = m.id
  WHERE m.name LIKE '%LandBoughtEvent%'
    AND (em.data ->> '$.buyer') = '{account}'
  GROUP BY (em.data ->> '$.land_location'), (em.data ->> '$.token_used')
),
sold AS (
  SELECT
    (em.data ->> '$.land_location') AS location,
    (em.data ->> '$.token_used') AS token,
    SUM(CAST((em.data ->> '$.sold_price') AS INTEGER)) AS total_sell
  FROM event_messages_historical em
  LEFT JOIN models m ON em.model_id = m.id
  WHERE m.name LIKE '%LandBoughtEvent%'
    AND (em.data ->> '$.seller') = '{account}'
  GROUP BY (em.data ->> '$.land_location'), (em.data ->> '$.token_used')
)
SELECT
  sold.location,
  sold.token,
  bought.total_buy,
  sold.total_sell,
  (sold.total_sell - bought.total_buy) AS pnl
FROM sold
JOIN bought ON sold.location = bought.location AND sold.token = bought.token
ORDER BY pnl DESC
LIMIT {limit}
""".strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["most-used-token", "last-drops", "land-health", "closed-pnl"])
    ap.add_argument("--account", help="Wallet/controller address for account-scoped queries")
    ap.add_argument("--limit", type=int, default=10)
    args = ap.parse_args()

    if args.command in {"land-health", "closed-pnl"} and not args.account:
        raise SystemExit("--account is required for land-health and closed-pnl")

    if args.command == "most-used-token":
        q = q_most_used_token(args.limit)
    elif args.command == "last-drops":
        q = q_last_drops(args.limit)
    elif args.command == "land-health":
        q = q_account_land_health(args.account)
    else:
        q = q_closed_pnl(args.account, args.limit)

    try:
        data = torii_sql(q)
        if args.command in {"most-used-token", "closed-pnl"} and isinstance(data, list):
            for row in data:
                token = row.get("token")
                if token:
                    row["token_symbol"] = token_symbol(token)
        print(json.dumps({"ok": True, "command": args.command, "data": data}, indent=2))
    except Exception as e:
        print(json.dumps({"ok": False, "command": args.command, "error": str(e), "query": q}, indent=2))


if __name__ == "__main__":
    main()
