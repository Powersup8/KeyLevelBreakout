# EMA Pullback — Options Entry Indicator

Detects pullback entries to the 9 EMA after strong moves away from it. Designed for 5-min charts with daily ATR as the volatility filter. Plays both sides: **Puts** (short) and **Calls** (long).

## Strategy Logic

### Short Side (Puts)

```
SCANNING → qualifying bull candle → WAITING → bear pullback to EMA → IN_TRADE → candle above EMA → SCANNING
```

1. **Qualifying Candle**: Green candle with close (or high, configurable) at least 20% of the daily ATR **above** the 9 EMA
2. **Entry Signal**: Next red candle whose wick touches the 9 EMA (low <= EMA) — marked with red "Put" triangle
3. **Entry Price**: 1/3 of the qualifying candle's range below its high — `qualHigh - (qualHigh - qualLow) / 3`
4. **Stop Loss**: At the high of the qualifying candle
5. **Exit**: First candle completely above the 9 EMA (low > EMA) — marked with orange "Exit" triangle

### Long Side (Calls)

```
SCANNING → qualifying bear candle → WAITING → bull pullback to EMA → IN_TRADE → candle below EMA → SCANNING
```

1. **Qualifying Candle**: Red candle with close (or low, configurable) at least 20% of the daily ATR **below** the 9 EMA
2. **Entry Signal**: Next green candle whose wick touches the 9 EMA (high >= EMA) — marked with green "Call" triangle
3. **Entry Price**: 1/3 of the qualifying candle's range above its low — `qualLow + (qualHigh - qualLow) / 3`
4. **Stop Loss**: At the low of the qualifying candle
5. **Exit**: First candle completely below the 9 EMA (high < EMA) — marked with orange "Exit" triangle

### Key Behaviors

- Both sides run **independently** — a short signal does not block a long signal
- While WAITING, a new qualifying candle **replaces** the previous one (latest strong move wins)
- While IN_TRADE, new qualifying candles are **ignored** until the exit fires
- Entry/SL lines are drawn as a fixed span around the qualifying + signal candles
- Old lines are deleted when a new signal fires (keeps the chart clean)

## Inputs

| Input | Default | Group | Description |
|-------|---------|-------|-------------|
| Enable Short (Puts) | On | Direction | Toggle short side on/off |
| Enable Long (Calls) | On | Direction | Toggle long side on/off |
| Short Qualify Mode | Close | Direction | Whether **Close** or **High** must clear the ATR threshold |
| Long Qualify Mode | Close | Direction | Whether **Close** or **Low** must clear the ATR threshold |
| ATR Threshold % | 20 | Parameters | Min % of daily ATR the qualifying candle must exceed EMA by |
| ATR Length (Daily) | 14 | Parameters | Period for the daily ATR calculation |
| EMA Length | 9 | Parameters | Period for the EMA |
| Line Extend (bars) | 2 | Visuals | How many bars the entry/SL lines extend beyond the candle pair |

## Visuals

| Marker | Shape | Location | Meaning |
|--------|-------|----------|---------|
| Red "Put" triangle | Triangle down | Above bar | Short entry signal |
| Green "Call" triangle | Triangle up | Below bar | Long entry signal |
| Orange "Exit" triangle | Triangle up/down | Below/above bar | Exit signal (short/long) |
| Green dashed line | Horizontal | Entry price | Entry level (1/3 into qualifying candle) |
| Red solid line | Horizontal | Stop loss | SL level (high/low of qualifying candle) |
| Yellow line | Continuous | On price | 9 EMA |

## Setup

1. Open TradingView Pine Editor, paste `EMAPullback.pine`, click **Add to chart**
2. Use on a **5-minute chart** — the ATR comes from the daily timeframe automatically
3. Set up alerts:
   - **Quick**: Add one alert → Condition: `EMA Pullback` → `Any alert() function call` — covers all entry and exit signals
   - **Granular**: Use individual `alertcondition()` entries:
     - Short Entry (Puts)
     - Short Exit
     - Long Entry (Calls)
     - Long Exit

## Alert Messages

| Alert | Message |
|-------|---------|
| Short entry | `EMA Pullback Short Entry – TICKER` |
| Short exit | `EMA Pullback Short Exit – TICKER` |
| Long entry | `EMA Pullback Long Entry – TICKER` |
| Long exit | `EMA Pullback Long Exit – TICKER` |

## Non-Repainting

- **Daily ATR** uses `[1]` + `lookahead_on` — always references yesterday's completed ATR value, never the current forming day
- **All signals** are evaluated on closed bars only (Pine default on 5m charts)

## Updating

Edit the script in Pine Editor and click **Save** — all charts using the indicator update automatically. Don't click "Add to chart" again (that creates a duplicate).

## Changelog

- **v1.0** — Initial release: dual-side EMA pullback detection, entry/SL lines, exit alerts, daily ATR filter
