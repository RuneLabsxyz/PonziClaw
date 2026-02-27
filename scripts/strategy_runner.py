#!/usr/bin/env python3
import argparse
import json
import math
import os
import subprocess
from pathlib import Path
from typing import Dict, Any

from ponzi_manifest import actions_contract_address, load_tokens_config


def run_snapshot() -> Dict[str, Any]:
    proc = subprocess.run(
        ["python3", "scripts/ponzi_api.py", "snapshot"],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def extract_price(snapshot: Dict[str, Any]) -> float:
    p = snapshot.get("price")
    if isinstance(p, dict):
        for key in ("price", "value", "usd", "last"):
            if key in p:
                try:
                    return float(p[key])
                except Exception:
                    pass
    if isinstance(p, list):
        cfg = load_tokens_config()
        main_addr = str(cfg.get("mainCurrencyAddress", "")).lower()
        for item in p:
            if str(item.get("address", "")).lower() == main_addr:
                try:
                    return float(item.get("ratio"))
                except Exception:
                    pass
        if p:
            try:
                return float(p[0].get("ratio"))
            except Exception:
                pass
    if isinstance(p, (int, float)):
        return float(p)
    return float("nan")


def calc_confidence(price: float, flow_strength: float) -> int:
    if math.isnan(price):
        return 30
    base = 50 + min(35, abs(flow_strength) * 5)
    return max(5, min(95, int(base)))


def decide(strategy: str, price: float, flow_strength: float) -> Dict[str, Any]:
    if strategy == "momentum-scalp":
        if flow_strength > 0.5:
            action = "buy"
        elif flow_strength < -0.5:
            action = "sell"
        else:
            action = "hold"
    elif strategy == "mean-reversion":
        if flow_strength > 1.2:
            action = "sell"
        elif flow_strength < -1.2:
            action = "buy"
        else:
            action = "hold"
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    confidence = calc_confidence(price, flow_strength)
    size_pct = 0 if action == "hold" else min(12, max(4, int(confidence / 8)))

    return {
        "strategy": strategy,
        "action": action,
        "confidence": confidence,
        "size_pct": size_pct,
        "price": None if math.isnan(price) else price,
        "invalid_if": "opposite signal persists for 2 reads",
        "execution_pending_confirmation": True,
    }


def _u256_parts(v: int):
    v = max(0, int(v))
    low = v & ((1 << 128) - 1)
    high = v >> 128
    return str(low), str(high)


def build_calls_from_manifest(rec: Dict[str, Any], land_location: int, token_address: str, sell_price_wei: int, stake_wei: int) -> Dict[str, Any]:
    if rec["action"] == "hold":
        return {"calls": []}

    sell_low, sell_high = _u256_parts(sell_price_wei)
    stake_low, stake_high = _u256_parts(stake_wei)
    entrypoint = "buy" if rec["action"] == "buy" else "bid"

    return {
        "calls": [
            {
                "contractAddress": actions_contract_address(),
                "entrypoint": entrypoint,
                "calldata": [
                    str(land_location),
                    token_address,
                    sell_low,
                    sell_high,
                    stake_low,
                    stake_high,
                ],
            }
        ]
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("strategy", choices=["momentum-scalp", "mean-reversion"])
    ap.add_argument("--emit-calls", help="Write calls JSON file for controller execute")
    ap.add_argument("--land-location", type=int, help="Target land location (required when emitting non-hold calls)")
    ap.add_argument("--token-address", help="Token address for sale/payment leg")
    ap.add_argument("--sell-price-wei", type=int, default=1000000000000000000)
    ap.add_argument("--stake-wei", type=int, default=10000000000000000)
    args = ap.parse_args()

    snap = run_snapshot()
    flow = snap.get("flow")

    # Very lightweight flow proxy. Override with stronger SQL + parser as needed.
    flow_strength = 0.0
    if isinstance(flow, dict):
        raw = json.dumps(flow).lower()
        if "buy" in raw:
            flow_strength += 0.8
        if "sell" in raw:
            flow_strength -= 0.8

    price = extract_price(snap)
    rec = decide(args.strategy, price, flow_strength)

    out = {
        "snapshot_errors": snap.get("errors", []),
        "recommendation": rec,
    }

    if args.emit_calls:
        cfg = load_tokens_config()
        token_address = args.token_address or cfg.get("mainCurrencyAddress")
        if rec["action"] != "hold" and args.land_location is None:
            raise SystemExit("--land-location is required when action is buy/sell and emitting calls")

        calls = build_calls_from_manifest(
            rec,
            land_location=(args.land_location or 1),
            token_address=token_address,
            sell_price_wei=args.sell_price_wei,
            stake_wei=args.stake_wei,
        )
        out_path = Path(args.emit_calls)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(calls, f, indent=2)
        out["calls_file"] = str(out_path)

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
