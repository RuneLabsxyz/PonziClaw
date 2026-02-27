# PonziClaw

PonziClaw is a Cartridge + PonziLand operator skill for:
- live data and analytics
- strategy planning
- AVNU swaps
- guarded transaction execution
- daily reporting

## First run behavior

On first interaction, run:

```bash
python3 scripts/banner.py
```

This prints the PonziClaw ASCII logo and a capability list.

## Core commands

### Data + analytics
```bash
python3 scripts/ponzi_api.py snapshot
python3 scripts/ponzi_insights.py most-used-token --limit 5
python3 scripts/ponzi_insights.py last-drops --limit 10
python3 scripts/ponzi_insights.py land-health --account 0xYOUR_ADDRESS
python3 scripts/ponzi_insights.py closed-pnl --account 0xYOUR_ADDRESS --limit 20
```

### Land map (ASCII 3x3)
```bash
python3 scripts/land_map_ascii.py --location 31610
```

### Strategy
```bash
python3 scripts/strategy_advisor.py --profile balanced
python3 scripts/strategy_runner.py momentum-scalp --emit-calls out/calls.json --land-location 31610
```

### Execute (guarded)
```bash
python3 scripts/execute_plan.py --calls-file out/calls.json --confirm
```

### AVNU swap
```bash
python3 scripts/avnu_swap.py quote \
  --sell-token 0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d \
  --buy-token 0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8 \
  --sell-amount 1000000000000000000
```

## Daily schedule setup (easy)

Generate a ready-to-use OpenClaw cron job payload:

```bash
python3 scripts/setup_daily_schedule.py --account 0xYOUR_ADDRESS --time-utc 09:00
```

Then use the printed JSON with `cron.add`.

## Defaults

- Mainnet Torii: `https://api.cartridge.gg/x/ponziland-mainnet-world-new/torii`
- Mainnet Ponzi API: `https://api.runelabs.xyz/ponziland-mainnet-temp/api`
- AVNU: `https://starknet.api.avnu.fi`

See `.env.example` for all overrides.
