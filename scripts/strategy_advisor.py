#!/usr/bin/env python3
import argparse
import json
import subprocess

PROFILE_MULT = {
    "conservative": 0.6,
    "balanced": 1.0,
    "aggressive": 1.5,
}


def get_snapshot():
    p = subprocess.run(["python3", "scripts/ponzi_api.py", "snapshot"], capture_output=True, text=True, check=True)
    return json.loads(p.stdout)


def get_price(snapshot):
    price = snapshot.get("price")
    if isinstance(price, list) and price:
        return float(price[0].get("ratio", 0) or 0)
    if isinstance(price, dict):
        for k in ("ratio", "price", "value", "usd"):
            if k in price:
                return float(price[k])
    return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", choices=["conservative", "balanced", "aggressive"], default="balanced")
    args = ap.parse_args()

    snap = get_snapshot()
    price = get_price(snap)
    flow_raw = json.dumps(snap.get("flow", {})).lower()
    flow_bias = 0
    flow_bias += 1 if "buy" in flow_raw else 0
    flow_bias -= 1 if "sell" in flow_raw else 0

    mult = PROFILE_MULT[args.profile]

    strats = [
        {
            "name": "momentum-scalp",
            "thesis": "Follow short-term directional flow when bias and price trend align.",
            "action": "buy" if flow_bias > 0 else ("sell" if flow_bias < 0 else "hold"),
            "suggested_size_pct": round(4 * mult, 2),
            "confidence": 70 if flow_bias != 0 else 48,
            "risk": "tight",
            "invalid_if": "flow flips for 2 consecutive checks",
        },
        {
            "name": "mean-reversion",
            "thesis": "Fade overstretched moves and target normalization.",
            "action": "hold" if flow_bias != 0 else "buy",
            "suggested_size_pct": round(3 * mult, 2),
            "confidence": 62 if flow_bias == 0 else 45,
            "risk": "medium",
            "invalid_if": "deviation expands after entry",
        },
        {
            "name": "rotation",
            "thesis": "Rotate exposure into most active token cohorts.",
            "action": "hold",
            "suggested_size_pct": round(2.5 * mult, 2),
            "confidence": 55,
            "risk": "medium",
            "invalid_if": "liquidity/volume drops materially",
        },
    ]

    out = {
        "ok": True,
        "profile": args.profile,
        "market": {"price_ref": price, "flow_bias": flow_bias, "snapshot_errors": snap.get("errors", [])},
        "strategies": strats,
        "next_step": "Pick one strategy, then generate calls in plan mode and confirm before execute.",
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
