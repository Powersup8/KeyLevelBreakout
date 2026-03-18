# Touch & Turn Scalper — Design Document

## Overview

Pine Script v6 indicator for TradingView that implements the "Touch and Turn" scalping strategy. Detects the first 15-minute candle after market open, confirms it as a liquidity candle via ATR, then monitors for a reversal entry on the 1-minute chart within 90 minutes.

## Strategy Logic

### State Machine

```
WAITING_FOR_OPEN → QUALIFYING → ARMED → IN_TRADE → DONE_FOR_DAY
```

1. **WAITING_FOR_OPEN**: Before market open. Reset all state.
2. **QUALIFYING**: First 15m candle closes. If range >= 25% of daily ATR(14), determine direction. If not → DONE_FOR_DAY.
3. **ARMED**: Limit order placed at range edge. Monitor on 1m bars. Timeout after 90 minutes from open.
4. **IN_TRADE**: Price touched entry level. Monitor for TP or SL.
5. **DONE_FOR_DAY**: Trade completed or window expired.

### Rules

- One trade per day maximum
- Direction always opposite to the opening candle (red open → long, green open → short)
- Entry at the extreme of the range (low for longs, high for shorts)
- TP = Fibonacci 38.2% or 61.8% of the opening range (configurable)
- SL = half the TP distance from entry (fixed 2:1 R:R)
- 90-minute window from market open

### Direction Logic

- **Bearish opening candle** (close < open): Go LONG at `rangeLow`, TP toward `fib382`/`fib618`
- **Bullish opening candle** (close > open): Go SHORT at `rangeHigh`, TP toward `fib382`/`fib618`

## Architecture

**Approach A: Single-Timeframe on 1m chart**

- Runs on the 1-minute chart
- Pulls 15m opening candle OHLC via `request.security`
- Pulls daily ATR via `request.security` (non-repainting)
- All entry/exit monitoring happens natively on 1m bars

## Data & Non-Repainting

### Daily ATR

```pine
dailyATR = request.security(syminfo.tickerid, "D", ta.atr(14)[1], lookahead=barmerge.lookahead_on)
```

### Opening 15m Candle

```pine
[o15, h15, l15, c15] = request.security(syminfo.tickerid, "15",
     [open[1], high[1], low[1], close[1]], lookahead=barmerge.lookahead_on)
```

### Session Detection

- `time("15", "0930-0945:1234567")` to detect the first 15m bar after open
- 90-minute window: 9:30–11:00 AM ET

### Calculated Levels

| Level | Long Setup | Short Setup |
|-------|-----------|-------------|
| Entry | `rangeLow` | `rangeHigh` |
| TP (38.2%) | `rangeLow + range * 0.382` | `rangeHigh - range * 0.382` |
| TP (61.8%) | `rangeLow + range * 0.618` | `rangeHigh - range * 0.618` |
| SL | `entry - (TP - entry) / 2` | `entry + (entry - TP) / 2` |

## Visuals

### Opening Range
- Shaded background box from high to low of opening candle, extending across the day

### Fibonacci Levels
- 38.2% — dashed line
- 50% — dotted line (reference)
- 61.8% — dashed line

### Trade Levels
- Entry — green dashed line at range edge
- TP — blue dashed line at selected Fibonacci target
- SL — red solid line

### Markers
- Arrow at entry when price touches limit order level
- "TP" label when target hit
- "SL" label when stop hit
- "Timeout" label if 90-min window expires
- "Not Qualified" label (gray range box) when ATR threshold not met

## Inputs

| Input | Default | Group | Description |
|-------|---------|-------|-------------|
| TP Level | 38.2% | Parameters | Target profit Fibonacci level: 38.2% or 61.8% |
| ATR Length | 14 | Parameters | Period for daily ATR calculation |
| Session | 0930-1600 | Parameters | Market session (for detecting open) |

Everything else is fixed: 25% ATR threshold, 2:1 R:R, 90-min window, 15m opening range, opposite direction only.

## Alerts

| Alert | Message |
|-------|---------|
| Qualified opening | `Touch&Turn: Qualified [LONG/SHORT] setup – TICKER` |
| Entry filled | `Touch&Turn: Entry filled [LONG/SHORT] – TICKER` |
| TP hit | `Touch&Turn: TP hit – TICKER` |
| SL hit | `Touch&Turn: SL hit – TICKER` |
| Timeout | `Touch&Turn: Timeout (no fill) – TICKER` |

Plus `alertcondition()` entries for granular alert setup.

## Files

- `TouchAndTurn.pine` — the indicator
- `TouchAndTurn.md` — documentation
- Update `README.md` — add to indicator table
