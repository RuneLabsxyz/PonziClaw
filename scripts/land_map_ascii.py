#!/usr/bin/env python3
import argparse
import json
import os
import urllib.request
from decimal import Decimal

from ponzi_manifest import token_map_by_address

TORII = os.getenv("PUBLIC_DOJO_TORII_URL", "https://api.cartridge.gg/x/ponziland-mainnet-world-new/torii").rstrip("/")
COORD_MULTIPLIER = 256


def to_location(x: int, y: int) -> int:
    return y * COORD_MULTIPLIER + x


def to_xy(location: int):
    x = location & 0xFF
    y = location // COORD_MULTIPLIER
    return x, y


def torii_sql(query: str):
    req = urllib.request.Request(
        f"{TORII}/sql",
        data=query.encode("utf-8"),
        headers={"Content-Type": "text/plain", "User-Agent": "PonziClaw/0.1"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def format_price(hex_price: str, decimals: int):
    try:
        v = int(hex_price, 16)
        d = Decimal(v) / (Decimal(10) ** decimals)
        if d >= 1000:
            return f"{d:.0f}"
        if d >= 10:
            return f"{d:.2f}"
        return f"{d:.4f}"
    except Exception:
        return "?"


def level_short(level: str):
    return {"Zero": "L0", "First": "L1", "Second": "L2"}.get(level, level[:2])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--location", type=int, help="Center location int")
    ap.add_argument("--x", type=int, help="Center x")
    ap.add_argument("--y", type=int, help="Center y")
    args = ap.parse_args()

    if args.location is None and (args.x is None or args.y is None):
        raise SystemExit("Provide --location or both --x and --y")

    if args.location is not None:
        cx, cy = to_xy(args.location)
    else:
        cx, cy = args.x, args.y

    cells = []
    for yy in range(cy - 1, cy + 2):
        for xx in range(cx - 1, cx + 2):
            if xx < 0 or yy < 0 or xx > 255 or yy > 255:
                continue
            cells.append((xx, yy, to_location(xx, yy)))

    loc_csv = ",".join(str(c[2]) for c in cells)

    land_q = f'''
SELECT location, owner, level, sell_price, token_used
FROM "ponzi_land-Land"
WHERE location IN ({loc_csv})
'''.strip()

    stake_q = f'''
SELECT location, amount, accumulated_taxes_fee
FROM "ponzi_land-LandStake"
WHERE location IN ({loc_csv})
'''.strip()

    lands = torii_sql(land_q)
    stakes = torii_sql(stake_q)

    land_by_loc = {int(r["location"]): r for r in lands}
    stake_by_loc = {int(r["location"]): r for r in stakes}

    tokens = token_map_by_address()

    print(f"Center: ({cx},{cy}) loc={to_location(cx, cy)}")
    print("Legend: [C]=center | L0/L1/L2 level | tax=accumulated_taxes_fee(raw)\n")

    for yy in range(cy - 1, cy + 2):
        row_parts = []
        for xx in range(cx - 1, cx + 2):
            if xx < 0 or yy < 0 or xx > 255 or yy > 255:
                row_parts.append("(out)")
                continue
            loc = to_location(xx, yy)
            land = land_by_loc.get(loc)
            stake = stake_by_loc.get(loc)

            prefix = "[C]" if (xx == cx and yy == cy) else "[ ]"
            if not land:
                cell = f"{prefix}{xx:03},{yy:03} empty"
            else:
                token_addr = str(land.get("token_used", "")).lower()
                tok = tokens.get(token_addr, {})
                sym = tok.get("symbol", token_addr[:6])
                dec = int(tok.get("decimals", 18))
                price = format_price(land.get("sell_price", "0x0"), dec)
                lvl = level_short(str(land.get("level", "?")))
                if stake:
                    t = str(stake.get("accumulated_taxes_fee", "0") or "0")
                    tax_raw = int(t, 16) if t.startswith("0x") else int(t)
                else:
                    tax_raw = 0
                cell = f"{prefix}{xx:03},{yy:03} {lvl} {price}{sym} tax={tax_raw}"
            row_parts.append(cell)
        print(" | ".join(row_parts))


if __name__ == "__main__":
    main()
