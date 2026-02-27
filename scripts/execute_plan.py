#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

STATE_PATH = Path(os.getenv("PONZI_STATE_PATH", "state/execution_state.json"))
COOLDOWN_SECONDS = int(os.getenv("PONZI_EXEC_COOLDOWN_SECONDS", "300"))


def run_json(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(cmd)}\n{p.stderr.strip()}")
    return json.loads(p.stdout)


def ensure_session_active():
    status = run_json(["controller", "session", "status", "--json"])
    if status.get("status") != "active":
        raise RuntimeError("Controller session is not active. Run session auth first.")
    return status


def load_calls(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    calls = data.get("calls", [])
    if not isinstance(calls, list):
        raise RuntimeError("Invalid calls file format")
    return data


def call_fingerprint(calls_data):
    raw = json.dumps(calls_data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_state():
    if not STATE_PATH.exists():
        return {"executions": []}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"executions": []}


def save_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def enforce_cooldown(fp):
    state = load_state()
    now = int(time.time())
    state["executions"] = [e for e in state.get("executions", []) if now - e.get("ts", 0) < 86400]
    for e in state["executions"]:
        if e.get("fp") == fp and now - e.get("ts", 0) < COOLDOWN_SECONDS:
            raise RuntimeError(f"Duplicate execution blocked by cooldown ({COOLDOWN_SECONDS}s)")
    return state


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calls-file", required=True)
    ap.add_argument("--chain-id", default="SN_MAIN")
    ap.add_argument("--confirm", action="store_true", help="Required flag to execute")
    args = ap.parse_args()

    if not args.confirm:
        raise SystemExit("Refusing to execute without --confirm")

    calls_path = Path(args.calls_file)
    if not calls_path.exists():
        raise SystemExit("calls file not found")

    ensure_session_active()
    calls_data = load_calls(calls_path)
    if len(calls_data.get("calls", [])) == 0:
        raise SystemExit("No calls to execute (empty plan)")

    fp = call_fingerprint(calls_data)
    state = enforce_cooldown(fp)

    tx = run_json(["controller", "execute", "--file", str(calls_path), "--json"])
    txh = tx.get("transaction_hash", "")

    state["executions"].append({"ts": int(time.time()), "fp": fp, "tx": txh})
    save_state(state)

    out = {
        "ok": True,
        "transaction_hash": txh,
        "voyager": f"https://voyager.online/tx/{txh}" if txh else None,
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, indent=2))
        sys.exit(1)
