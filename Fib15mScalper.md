# 15m Fib Scalper — Opening Range Reversal Indicator

Detects liquidity candles on the first 15-minute candle after market open, confirms via daily ATR, then signals reversal entries with Fibonacci-based take profit and fixed 2:1 risk-reward ratio. Designed for 1-minute charts.

## Strategy Logic

```
WAITING_FOR_OPEN → first 15m candle qualifies → ARMED → price touches entry → IN_TRADE → TP or SL → DONE
```

1. **Liquidity Candle**: First 15m candle after market open. Range must be >= 25% of daily ATR(14).
2. **Direction**: Opposite to the candle — bearish open → LONG, bullish open → SHORT.
3. **Entry**: Limit order at range edge — low for longs, high for shorts.
4. **Take Profit**: Fibonacci 38.2% or 61.8% of the opening range (configurable).
5. **Stop Loss**: Half the TP distance from entry, giving 2:1 reward-to-risk ratio.
6. **Time Window**: Entry must occur within 90 minutes of market open. After that → timeout.
7. **One trade per day maximum.**

## Inputs

| Input | Default | Group | Description |
|-------|---------|-------|-------------|
| TP Level | 38.2% | Parameters | Target profit Fibonacci level: 38.2% or 61.8% |
| ATR Length (Daily) | 14 | Parameters | Period for daily ATR calculation |
| Session | 0930-1600 | Parameters | Market session for detecting open |

## Visuals

| Element | Style | Color | Meaning |
|---------|-------|-------|---------|
| Range box (qualified) | Shaded rectangle | Blue | Opening 15m range that qualified |
| Range box (not qualified) | Shaded rectangle | Gray | Opening 15m range that didn't qualify |
| 38.2% Fibonacci line | Dashed | Purple | Fibonacci retracement level |
| 50% Fibonacci line | Dotted | Gray | Fibonacci midpoint (reference) |
| 61.8% Fibonacci line | Dashed | Purple | Fibonacci retracement level |
| Entry line | Dashed | Green | Limit order entry level |
| TP line | Dashed | Blue | Take profit target |
| SL line | Solid | Red | Stop loss level |
| "Qualified: LONG/SHORT" label | Label | Green/Red | Qualified setup notification |
| "Not Qualified" label | Label | Gray | Opening range didn't meet ATR threshold |
| Green "Long" triangle | Triangle up | Green | Long entry fill |
| Red "Short" triangle | Triangle down | Red | Short entry fill |
| "TP" label | Label | Blue | Take profit hit |
| "SL" label | Label | Red | Stop loss hit |
| "Timeout" label | Label | Gray | 90-min window expired |

## Setup

1. Open TradingView Pine Editor, paste `Fib15mScalper.pine`, click **Add to chart**
2. Use on a 1-minute chart — the indicator handles 15m and daily data internally
3. Set up alerts:
   - **Quick**: Add one alert → Condition: `15m Fib Scalper` → `Any alert() function call` — covers all signals
   - **Granular**: Use individual `alertcondition()` entries:
     - Qualified Setup
     - Entry Filled
     - TP Hit
     - SL Hit
     - Timeout

## Alert Messages

| Alert | Message |
|-------|---------|
| Qualified setup | `15mFib: Qualified LONG/SHORT setup – TICKER` |
| Entry filled | `15mFib: Entry filled LONG/SHORT – TICKER` |
| TP hit | `15mFib: TP hit – TICKER` |
| SL hit | `15mFib: SL hit – TICKER` |
| Timeout | `15mFib: Timeout – TICKER` |

## Non-Repainting

- **Daily ATR** uses `[1]` + `lookahead_on` — always references yesterday's completed ATR value, never the current forming day
- **15m candle** uses `[1]` + `lookahead_on` — always references the last completed 15m bar

## Updating

Edit the script in Pine Editor and click **Save** — all charts using the indicator update automatically. Don't click "Add to chart" again (that creates a duplicate).
