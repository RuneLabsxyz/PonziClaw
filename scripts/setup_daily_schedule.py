#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", required=True, help="Wallet/controller account to report on")
    ap.add_argument("--time-utc", default="09:00", help="HH:MM UTC")
    ap.add_argument("--channel", default="telegram")
    ap.add_argument("--target", default="current-chat")
    args = ap.parse_args()

    hh, mm = args.time_utc.split(":")
    cron_expr = f"{int(mm)} {int(hh)} * * *"

    suggested_prompt = (
        f"Run PonziClaw daily report for account {args.account}. "
        f"Execute: python3 /home/server/clawd/skills/ponziclaw/scripts/daily_report.py --account {args.account}. "
        f"Then send a concise summary with key deltas, top token moves, and actionable strategy recommendation."
    )

    job = {
        "name": "PonziClaw Daily Report",
        "schedule": {"kind": "cron", "expr": cron_expr, "tz": "UTC"},
        "payload": {
            "kind": "agentTurn",
            "message": suggested_prompt,
            "thinking": "low",
        },
        "sessionTarget": "isolated",
        "notify": True,
    }

    print("# Use this with OpenClaw cron.add")
    print(json.dumps(job, indent=2))
    print("\n# Example assistant action")
    print("cron.add(job=<json above>)")
    print("\nGenerated at:", datetime.now(timezone.utc).isoformat())


if __name__ == "__main__":
    main()
