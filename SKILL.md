---
name: ponziclaw
description: Use Cartridge Controller CLI plus PonziLand APIs to fetch live market/game info, generate strategy decisions, and optionally execute Starknet transactions for PonziLand. Use when the user asks to check PonziLand price/state, run bot strategies, prepare calldata/calls, or execute a play/trade flow through controller sessions.
---

# PonziClaw

Use this skill to operate a PonziLand bot with three capabilities:
1. Read live data from PonziLand endpoints (price + Torii SQL)
2. Propose strategy actions from current data
3. Execute approved actions through `controller` CLI

## Required workflow

1. Read market snapshot first.
2. Run strategy in **plan mode** first.
3. Show concise recommendation with confidence and risk.
4. Ask for confirmation before any onchain execute.
5. If approved, build calls JSON and execute through `controller execute --file ... --json`.

## Commands

### 1) Fetch data

```bash
python3 scripts/ponzi_api.py snapshot
```

Optional env overrides:
- `PUBLIC_PONZI_API_URL` (default `https://play.ponzis.fun`)
- `PUBLIC_DOJO_TORII_URL` (default `https://api.cartridge.gg/x/ponziland-mainnet-world-new/torii`)

### 2) Run strategy (plan only)

```bash
python3 scripts/strategy_runner.py momentum-scalp
python3 scripts/strategy_runner.py mean-reversion
```

### 3) Run strategy and emit calls payload

```bash
python3 scripts/strategy_runner.py momentum-scalp --emit-calls out/calls.momentum.json
```

### 4) Execute (only after user approval)

```bash
controller execute --file out/calls.momentum.json --json
```

## Session/auth through Controller CLI

Check status:

```bash
controller session status --json
```

Authorize (example):

```bash
controller session auth --preset loot-survivor --chain-id SN_MAIN --json
```

If not active, request user authorization before any execute.

## Strategy list

- `momentum-scalp`: Follow short-term trend when price and flow align.
- `mean-reversion`: Fade extreme deviations and target reversion.

Read details in `references/strategies.md`.

## Output format to user

Always report:
- Current price
- Signal + confidence (0-100)
- Suggested action (buy/sell/hold)
- Position size guidance (%)
- Stop/invalid condition
- Whether execution is pending user confirmation

## Safety rules

- Never execute transactions without explicit user confirmation in the current chat.
- Default to plan mode.
- If API is down, degrade gracefully and return best-effort analysis with clear caveat.
- If controller session is inactive, stop at planning and ask for auth.