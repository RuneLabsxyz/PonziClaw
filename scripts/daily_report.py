#!/usr/bin/env python3
import argparse
import json
import subprocess
from datetime import datetime, timezone


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(p.stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", required=True)
    ap.add_argument("--drops-limit", type=int, default=5)
    ap.add_argument("--tokens-limit", type=int, default=5)
    args = ap.parse_args()

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    snap = run(["python3", "scripts/ponzi_api.py", "snapshot"])
    top_tokens = run(["python3", "scripts/ponzi_insights.py", "most-used-token", "--limit", str(args.tokens_limit)])
    drops = run(["python3", "scripts/ponzi_insights.py", "last-drops", "--limit", str(args.drops_limit)])
    health = run(["python3", "scripts/ponzi_insights.py", "land-health", "--account", args.account])
    pnl = run(["python3", "scripts/ponzi_insights.py", "closed-pnl", "--account", args.account, "--limit", "10"])
    advisor = run(["python3", "scripts/strategy_advisor.py", "--profile", "balanced"])

    report = {
        "ok": True,
        "generated_at": now,
        "account": args.account,
        "market_snapshot_errors": snap.get("errors", []),
        "top_tokens": top_tokens.get("data", []),
        "recent_drops": drops.get("data", []),
        "land_health": (health.get("data") or [{}])[0],
        "closed_positions": pnl.get("data", []),
        "strategy_proposals": advisor.get("strategies", []),
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
