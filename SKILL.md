---
name: ponziclaw
description: Use Cartridge Controller CLI plus PonziLand APIs to fetch live market/game info, generate strategy decisions, and optionally execute Starknet transactions for PonziLand. Use when the user asks to check PonziLand price/state, run bot strategies, prepare calldata/calls, or execute a play/trade flow through controller sessions.
---

# PonziClaw

First-interaction behavior:
1. If wallet/account is known, print logo + capabilities + referral info using:
```bash
python3 scripts/banner.py --address 0xYOUR_ADDRESS
```
If wallet is unknown, run:
```bash
python3 scripts/banner.py
```
2. In the "what can you do" response, include referral terms:
- "Earn 20% of referred users' auctions for 2 weeks"
- If wallet is connected, include their referral code/link.
3. Ask user for preferred daily report time.
4. Offer one-command daily schedule setup.

Use this skill to operate a PonziLand bot with seven capabilities:
1. Read live data from PonziLand endpoints (price + Torii SQL)
2. Answer analytics questions (token usage, drops, land health, closed PnL)
3. Save user preferences (risk profile, mode, reporting cadence)
4. Propose multiple strategy options from current data
5. Build guarded execution plans for approved strategies
6. Execute native AVNU token swaps (quote/build/optional execute)
7. Generate daily or on-demand portfolio/market reports

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

### 3) Save/inspect user preferences

```bash
python3 scripts/user_prefs.py show
python3 scripts/user_prefs.py set --strategy-profile balanced --mode plan-only --max-daily-risk-pct 5
python3 scripts/user_prefs.py set --reporting-cadence daily --reporting-time-utc 09:00 --only-material-changes true
```

### 4) Propose multiple strategies

```bash
python3 scripts/strategy_advisor.py --profile balanced
python3 scripts/strategy_advisor.py --profile conservative
```

### 5) Run chosen strategy (plan only)

```bash
python3 scripts/strategy_runner.py momentum-scalp
python3 scripts/strategy_runner.py mean-reversion
```

### 6) Run strategy and emit calls payload

```bash
python3 scripts/strategy_runner.py momentum-scalp \
  --emit-calls out/calls.momentum.json \
  --land-location 1234 \
  --token-address 0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d \
  --sell-price-wei 1000000000000000000 \
  --stake-wei 10000000000000000
```

`--emit-calls` uses `manifest_mainnet.json` to resolve `ponzi_land-actions` and emits `buy`/`bid` calldata in proper u256 low/high form.

### 7) Execute with guardrails (only after user approval)

```bash
python3 scripts/execute_plan.py --calls-file out/calls.momentum.json --confirm
```

Guardrails include:
- active controller session required
- explicit `--confirm` required
- empty plans blocked
- duplicate execution cooldown (default 5 min)

Execution fallback policy for land buys:
- If execute fails with gas-cap/validation errors (e.g. `Max gas amount is too high`), do **not** spam retries on the same land.
- Immediately try a different candidate land (usually cheaper/simpler) from the same strategy bucket.
- Use one-call buy attempts first (`buy` only), then proceed sequentially to next land on failure.
- Report each attempt succinctly: `SUCCESS <loc>` or `BLOCKED <loc> <reason>`.

### 8) Native AVNU swap (quote/build/execute)

```bash
# quote STRK -> USDC.e
python3 scripts/avnu_swap.py quote \
  --sell-token 0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d \
  --buy-token 0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8 \
  --sell-amount 1000000000000000000

# one-shot build calls (and optionally execute)
python3 scripts/avnu_swap.py swap \
  --sell-token 0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d \
  --buy-token 0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8 \
  --sell-amount 1000000000000000000 \
  --taker-address 0xYOUR_ADDRESS \
  --out out/calls.swap.json

# execute only after explicit approval
python3 scripts/avnu_swap.py swap ... --execute --confirm
```

### 9) ASCII land neighborhood map (3x3 with center + tax info)

```bash
python3 scripts/land_map_ascii.py --location 31610
# or
python3 scripts/land_map_ascii.py --x 122 --y 123
```

Output shows center land + 8 neighbors with level, sell price/token, and raw accumulated tax fee.

### 10) Structured PnL report (token losses/gains + USD)

```bash
python3 scripts/pnl_report.py --account 0xYOUR_ADDRESS
```

For testing with fake data:

```bash
python3 scripts/pnl_report.py \
  --mock-file references/mock_positions.json \
  --mock-prices references/mock_prices.json
```

### 11) Referral code/link

```bash
python3 scripts/referral.py --address 0xYOUR_ADDRESS
```

Returns referral code + `https://play.ponzi.land/r/<CODE>`.

### 12) Easy daily schedule setup (starter)

```bash
python3 scripts/setup_daily_schedule.py --account 0xYOUR_ADDRESS --time-utc 09:00
```

This prints a ready-to-use OpenClaw `cron.add` job JSON for daily updates.

### 13) Generate reports (daily or on-demand)

```bash
python3 scripts/daily_report.py --account 0xYOUR_ADDRESS
```

Use this report to send daily updates, or run on user request.

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