---
name: ponziclaw
description: Use Cartridge Controller CLI plus PonziLand APIs to fetch live market/game info, generate strategy decisions, and optionally execute Starknet transactions for PonziLand. Use when the user asks to check PonziLand price/state, run bot strategies, prepare calldata/calls, or execute a play/trade flow through controller sessions.
---

# PonziClaw

Use this skill to operate a PonziLand bot with four capabilities:
1. Read live data from PonziLand endpoints (price + Torii SQL)
2. Answer analytics questions (token usage, drops, land health, closed PnL)
3. Propose strategy actions from current data
4. Execute approved actions through `controller` CLI

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

Default mainnet wiring in this skill:
- `PUBLIC_PONZI_API_URL=https://api.runelabs.xyz/ponziland-mainnet-temp/api`
- `PUBLIC_DOJO_TORII_URL=https://api.cartridge.gg/x/ponziland-mainnet-world-new/torii`
- `references/mainnet.tokens.json` (copied from PonziLand `client/data/mainnet.json`)
- `references/manifest_mainnet.json` (copied from PonziLand `contracts/manifest_mainnet.json`)

Optional env overrides:
- `PUBLIC_PONZI_API_URL`
- `PUBLIC_DOJO_TORII_URL`
- `PONZI_TOKENS_CONFIG`
- `PONZI_MANIFEST_PATH`

### 2) Query analytics Q&A

```bash
python3 scripts/ponzi_insights.py most-used-token --limit 5
python3 scripts/ponzi_insights.py last-drops --limit 10
python3 scripts/ponzi_insights.py land-health --account 0xYOUR_ADDRESS
python3 scripts/ponzi_insights.py closed-pnl --account 0xYOUR_ADDRESS --limit 20
```

### 3) Run strategy (plan only)

```bash
python3 scripts/strategy_runner.py momentum-scalp
python3 scripts/strategy_runner.py mean-reversion
```

### 4) Run strategy and emit calls payload

```bash
python3 scripts/strategy_runner.py momentum-scalp \
  --emit-calls out/calls.momentum.json \
  --land-location 1234 \
  --token-address 0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d \
  --sell-price-wei 1000000000000000000 \
  --stake-wei 10000000000000000
```

`--emit-calls` uses `manifest_mainnet.json` to resolve `ponzi_land-actions` and emits `buy`/`bid` calldata in proper u256 low/high form.

### 5) Execute with guardrails (only after user approval)

```bash
python3 scripts/execute_plan.py --calls-file out/calls.momentum.json --confirm
```

Guardrails include:
- active controller session required
- explicit `--confirm` required
- empty plans blocked
- duplicate execution cooldown (default 5 min)

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

For analytics questions, report:
- Direct answer first
- Top rows or summary metrics
- Data caveats if partial
- For `closed-pnl`, data comes from `/land-historical/<address>` (closed positions API)

For strategy questions, always report:
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