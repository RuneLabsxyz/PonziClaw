#!/usr/bin/env python3
import argparse
import json
import os
import urllib.request
from collections import defaultdict
from decimal import Decimal, InvalidOperation

from ponzi_manifest import token_map_by_address

PONZI_API = os.getenv("PUBLIC_PONZI_API_URL", "https://api.runelabs.xyz/ponziland-mainnet-temp/api").rstrip("/")


def fetch_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "PonziClaw/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def parse_dec(v):
    if v is None:
        return Decimal("0")
    if isinstance(v, (int, float)):
        return Decimal(str(v))
    s = str(v).strip()
    if s == "":
        return Decimal("0")
    try:
        if s.startswith("0x"):
            return Decimal(int(s, 16))
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return Decimal("0")


def to_human_amount(raw_amount: Decimal, decimals: int) -> Decimal:
    q = Decimal(10) ** Decimal(decimals)
    if q == 0:
        return raw_amount
    return raw_amount / q


def normalize_amount(value, decimals: int):
    """
    Return (raw_decimal, human_decimal).
    - If value looks decimal (contains '.' or scientific notation), treat as already human.
    - Else treat as raw integer units and convert using decimals.
    """
    s = "" if value is None else str(value).strip().lower()
    raw = parse_dec(value)
    is_human_like = ("." in s) or ("e" in s and not s.startswith("0x"))
    if is_human_like:
        human = raw
        raw_units = raw * (Decimal(10) ** Decimal(decimals))
    else:
        human = to_human_amount(raw, decimals)
        raw_units = raw
    return raw_units, human


def load_positions(account: str = None, mock_file: str = None):
    if mock_file:
        with open(mock_file, "r", encoding="utf-8") as f:
            return json.load(f)
    if not account:
        raise ValueError("account required unless --mock-file is used")
    formatted = account
    if formatted.startswith("0x0") and len(formatted) == 66:
        formatted = "0x" + formatted[3:]
    return fetch_json(f"{PONZI_API}/land-historical/{formatted}")


def load_price_map(mock_prices: str = None):
    if mock_prices:
        with open(mock_prices, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {k.lower(): Decimal(str(v)) for k, v in data.items()}

    # Best effort: if endpoint exposes usd use it, otherwise leave empty.
    try:
        raw = fetch_json(f"{PONZI_API}/price")
        out = {}
        for item in raw:
            addr = str(item.get("address", "")).lower()
            usd = item.get("usd")
            if addr and usd is not None:
                out[addr] = Decimal(str(usd))
        return out
    except Exception:
        return {}


def summarize(positions, price_map):
    token_meta = token_map_by_address()

    token_rows = defaultdict(lambda: {
        "token_address": None,
        "token_symbol": None,
        "decimals": 18,
        "positions": 0,
        "inflow_token": Decimal("0"),
        "outflow_token": Decimal("0"),
        "realized_profit_token": Decimal("0"),
        "realized_loss_token": Decimal("0"),
        "net_token": Decimal("0"),
        "realized_profit_usd": Decimal("0"),
        "realized_loss_usd": Decimal("0"),
        "net_usd": Decimal("0"),
        "usd_estimated_from_token": Decimal("0"),
    })

    out_positions = []
    totals = {
        "positions_total": len(positions),
        "closed_positions": 0,
        "open_positions": 0,
        "realized_profit_usd": Decimal("0"),
        "realized_loss_usd": Decimal("0"),
        "net_usd": Decimal("0"),
    }

    for p in positions:
        token = (p.get("sale_token_used") or p.get("buy_token_used") or "").lower()
        meta = token_meta.get(token, {})
        symbol = meta.get("symbol") or token or "UNKNOWN"
        decimals = int(meta.get("decimals", 18))

        buy_token_raw, buy_token = normalize_amount(p.get("buy_cost_token"), decimals)
        sale_token_raw, sale_token = normalize_amount(p.get("sale_revenue_token"), decimals)
        net_token_raw, net_token = normalize_amount(p.get("net_profit_token"), decimals)
        net_usd = p.get("net_profit_usd")
        close_reason = p.get("close_reason")
        is_closed = bool(close_reason)

        if is_closed:
            totals["closed_positions"] += 1
        else:
            totals["open_positions"] += 1

        row = token_rows[symbol]
        row["token_address"] = token
        row["token_symbol"] = symbol
        row["decimals"] = decimals
        row["positions"] += 1
        row["inflow_token"] += sale_token
        row["outflow_token"] += buy_token
        row["net_token"] += net_token

        if net_token >= 0:
            row["realized_profit_token"] += net_token
        else:
            row["realized_loss_token"] += abs(net_token)

        net_usd_val = parse_dec(net_usd)
        if net_usd is not None:
            row["net_usd"] += net_usd_val
        else:
            px = price_map.get(token)
            if px is not None:
                est = net_token * px
                row["usd_estimated_from_token"] += est
                row["net_usd"] += est
                net_usd_val = est

        if net_usd_val >= 0:
            row["realized_profit_usd"] += net_usd_val
        else:
            row["realized_loss_usd"] += abs(net_usd_val)

        out_positions.append({
            "id": p.get("id"),
            "land_location": p.get("land_location"),
            "close_reason": close_reason,
            "token_symbol": symbol,
            "token_address": token,
            "decimals": decimals,
            "buy_cost_token": str(buy_token),
            "sale_revenue_token": str(sale_token),
            "net_profit_token": str(net_token),
            "buy_cost_token_raw": str(buy_token_raw),
            "sale_revenue_token_raw": str(sale_token_raw),
            "net_profit_token_raw": str(net_token_raw),
            "net_profit_usd": str(net_usd_val),
            "is_closed": is_closed,
        })

    token_list = []
    for _, r in sorted(token_rows.items(), key=lambda kv: kv[0]):
        token_list.append({
            "token_symbol": r["token_symbol"],
            "token_address": r["token_address"],
            "decimals": r["decimals"],
            "positions": r["positions"],
            "inflow_token": str(r["inflow_token"]),
            "outflow_token": str(r["outflow_token"]),
            "realized_profit_token": str(r["realized_profit_token"]),
            "realized_loss_token": str(r["realized_loss_token"]),
            "net_token": str(r["net_token"]),
            "realized_profit_usd": str(r["realized_profit_usd"]),
            "realized_loss_usd": str(r["realized_loss_usd"]),
            "net_usd": str(r["net_usd"]),
            "usd_estimated_from_token": str(r["usd_estimated_from_token"]),
        })

        totals["realized_profit_usd"] += r["realized_profit_usd"]
        totals["realized_loss_usd"] += r["realized_loss_usd"]
        totals["net_usd"] += r["net_usd"]

    totals_fmt = {k: (str(v) if isinstance(v, Decimal) else v) for k, v in totals.items()}

    return {
        "summary": totals_fmt,
        "by_token": token_list,
        "positions": out_positions,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--account")
    ap.add_argument("--mock-file")
    ap.add_argument("--mock-prices")
    args = ap.parse_args()

    positions = load_positions(args.account, args.mock_file)
    prices = load_price_map(args.mock_prices)
    result = summarize(positions, prices)

    print(json.dumps({"ok": True, **result}, indent=2))


if __name__ == "__main__":
    main()
