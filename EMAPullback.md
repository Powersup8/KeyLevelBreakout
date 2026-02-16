# EMA Pullback — Options Entry Indicator

Detects pullback entries to the 9 EMA after strong moves away from it. Designed for 5-min charts with daily ATR as the volatility filter. Plays both sides: **Puts** (short) and **Calls** (long).

## Strategy Logic

### Short Side (Puts)

```
SCANNING → qualifying bull candle → WAITING → bear retest (EMA touch or any red) → IN_TRADE → body above EMA → SCANNING
```

1. **Qualifying Candle**: Green candle with close (or high, configurable) at least 20% of the daily ATR **above** the 9 EMA. Must have body > 75% of total range (strong conviction). Previous candle must have closed at/below EMA (fresh cross).
2. **Entry Signal**: Next red candle — in **EMA Touch** mode its wick must reach the 9 EMA (low <= EMA); in **Any Opposite** mode any red candle qualifies — marked with red "Put" triangle
3. **Entry Price**: 1/3 of the qualifying candle's range below its high — `qualHigh - (qualHigh - qualLow) / 3`
4. **Stop Loss**: At the high of the qualifying candle — triggers immediately if hit
5. **Exit**: First candle whose **body** is above the 9 EMA (min(open,close) > EMA), but only after price has crossed below EMA first — marked with orange "Exit" triangle
6. **Invalidation**: While WAITING, if EMA rises past the qualifying candle's close, the setup resets to SCANNING

### Long Side (Calls)

```
SCANNING → qualifying bear candle → WAITING → bull retest (EMA touch or any green) → IN_TRADE → body below EMA → SCANNING
```

1. **Qualifying Candle**: Red candle with close (or low, configurable) at least 20% of the daily ATR **below** the 9 EMA. Must have body > 75% of total range (strong conviction). Previous candle must have closed at/above EMA (fresh cross).
2. **Entry Signal**: Next green candle — in **EMA Touch** mode its wick must reach the 9 EMA (high >= EMA); in **Any Opposite** mode any green candle qualifies — marked with green "Call" triangle
3. **Entry Price**: 1/3 of the qualifying candle's range above its low — `qualLow + (qualHigh - qualLow) / 3`
4. **Stop Loss**: At the low of the qualifying candle — triggers immediately if hit
5. **Exit**: First candle whose **body** is below the 9 EMA (max(open,close) < EMA), but only after price has crossed above EMA first — marked with orange "Exit" triangle
6. **Invalidation**: While WAITING, if EMA drops past the qualifying candle's close, the setup resets to SCANNING

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
| Retest Mode | EMA Touch | Direction | **EMA Touch**: wick must reach EMA; **Any Opposite**: just the next opposite-color candle |
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
     - Short SL Hit
     - Short Exit
     - Long Entry (Calls)
     - Long SL Hit
     - Long Exit

## Alert Messages

| Alert | Message |
|-------|---------|
| Short entry | `EMA Pullback Short Entry – TICKER` |
| Short SL hit | `EMA Pullback Short SL – TICKER` |
| Short exit | `EMA Pullback Short Exit – TICKER` |
| Long entry | `EMA Pullback Long Entry – TICKER` |
| Long SL hit | `EMA Pullback Long SL – TICKER` |
| Long exit | `EMA Pullback Long Exit – TICKER` |

## Non-Repainting

- **Daily ATR** uses `[1]` + `lookahead_on` — always references yesterday's completed ATR value, never the current forming day
- **All signals** are evaluated on closed bars only (Pine default on 5m charts)

## Updating

Edit the script in Pine Editor and click **Save** — all charts using the indicator update automatically. Don't click "Add to chart" again (that creates a duplicate).

## Changelog

- **v1.2** — Fresh cross filter (qualifying candle must cross EMA), body > 75% filter, close-based invalidation, SL exit with crossing requirement
- **v1.1** — Retest Mode toggle (EMA Touch vs Any Opposite), body-based exit logic, backtest strategy file
- **v1.0** — Initial release: dual-side EMA pullback detection, entry/SL lines, exit alerts, daily ATR filter
