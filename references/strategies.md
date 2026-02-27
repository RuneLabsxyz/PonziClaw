# Strategies

## 1) momentum-scalp

Objective: capture short trend continuation with tight invalidation.

Inputs:
- current price (`/price`)
- recent directional pressure from Torii SQL aggregate

Heuristic:
- Bullish when short flow is positive and price change is positive.
- Bearish when short flow is negative and price change is negative.
- Otherwise hold.

Sizing:
- Base 5% notional.
- Increase up to 12% when confidence >= 75.

Risk:
- Invalidate if opposite flow persists for 2 consecutive reads.

## 2) mean-reversion

Objective: trade pullbacks from stretched moves.

Inputs:
- current price (`/price`)
- rolling baseline from recent points

Heuristic:
- If price is significantly below baseline and sell pressure is exhausted: buy.
- If price is significantly above baseline and buy pressure is exhausted: sell.
- Else hold.

Sizing:
- Base 4% notional.
- Increase up to 10% when deviation is large and confidence >= 80.

Risk:
- Invalidate if deviation expands by another threshold step.

## Notes

- These are starter strategies for operator-guided usage.
- Use plan mode first, then require user approval before execute.
- Adjust thresholds over time as real performance data accumulates.