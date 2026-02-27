#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

PREFS_PATH = Path("state/user_prefs.json")

DEFAULTS = {
    "mode": "plan-only",
    "strategy_profile": "balanced",
    "max_daily_risk_pct": 5,
    "reporting": {
        "enabled": True,
        "cadence": "daily",
        "time_utc": "09:00",
        "only_material_changes": True,
    },
}


def load_prefs():
    if not PREFS_PATH.exists():
        return dict(DEFAULTS)
    try:
        data = json.loads(PREFS_PATH.read_text(encoding="utf-8"))
        out = dict(DEFAULTS)
        out.update(data)
        if "reporting" in data:
            out["reporting"] = {**DEFAULTS["reporting"], **data["reporting"]}
        return out
    except Exception:
        return dict(DEFAULTS)


def save_prefs(prefs):
    PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREFS_PATH.write_text(json.dumps(prefs, indent=2), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("show")

    setp = sub.add_parser("set")
    setp.add_argument("--mode", choices=["plan-only", "auto-execute"])
    setp.add_argument("--strategy-profile", choices=["conservative", "balanced", "aggressive"])
    setp.add_argument("--max-daily-risk-pct", type=int)
    setp.add_argument("--reporting-enabled", choices=["true", "false"])
    setp.add_argument("--reporting-cadence", choices=["daily", "intraday", "weekly"])
    setp.add_argument("--reporting-time-utc")
    setp.add_argument("--only-material-changes", choices=["true", "false"])

    args = ap.parse_args()
    prefs = load_prefs()

    if args.cmd == "show":
        print(json.dumps({"ok": True, "prefs": prefs}, indent=2))
        return

    if args.mode:
        prefs["mode"] = args.mode
    if args.strategy_profile:
        prefs["strategy_profile"] = args.strategy_profile
    if args.max_daily_risk_pct is not None:
        prefs["max_daily_risk_pct"] = max(1, min(100, args.max_daily_risk_pct))
    if args.reporting_enabled:
        prefs["reporting"]["enabled"] = args.reporting_enabled == "true"
    if args.reporting_cadence:
        prefs["reporting"]["cadence"] = args.reporting_cadence
    if args.reporting_time_utc:
        prefs["reporting"]["time_utc"] = args.reporting_time_utc
    if args.only_material_changes:
        prefs["reporting"]["only_material_changes"] = args.only_material_changes == "true"

    save_prefs(prefs)
    print(json.dumps({"ok": True, "prefs": prefs}, indent=2))


if __name__ == "__main__":
    main()
