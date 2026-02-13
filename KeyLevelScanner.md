# Key Level Breakout — Multi-Symbol Scanner

Monitors up to 8 tickers from a single chart. One alert covers all symbols and levels. A status table shows today's signals at a glance.

## Features

- **8 symbol slots** with individual enable toggles (defaults: AAPL, MSFT, GOOGL, AMZN on; META, NVDA, TSLA, SPY off)
- **Status table** in top-right corner — shows each symbol's last signal, highlighted green (bull) or red (bear)
- **Single alert setup** — one `alert()` covers all symbols; messages include the ticker name
- **All 4 level types** tracked per symbol (Premarket, Yesterday, Last Week, ORB)
- **First Cross Only** per symbol per level per day
- Uses 24 of 40 allowed `request.security()` calls (3 per symbol)

## Setup

1. Add `KeyLevelScanner.pine` to any 5-min US stock chart (the chart symbol doesn't matter)
2. Enable **Extended Trading Hours** in chart settings
3. Configure tickers in the **Watchlist** input group
4. Add **one alert** → Condition: `Key Level Breakout Scanner` → `Any alert() function call`
5. Toggle that single alert on/off to enable/disable all scanning

## Inputs

| Input | Default | Description |
|-------|---------|-------------|
| Premarket High/Low | On | Track premarket levels for all symbols |
| Yesterday High/Low | On | Track previous day levels for all symbols |
| Last Week High/Low | On | Track previous week levels for all symbols |
| ORB High/Low | On | Track opening range levels for all symbols |
| First Cross Only | On | One signal per level per symbol per day |
| Symbol 1–4 | AAPL, MSFT, GOOGL, AMZN | Enabled by default |
| Symbol 5–8 | META, NVDA, TSLA, SPY | Disabled by default |

## Alert Messages

Messages include the ticker and direction:
- `AAPL ▲ PM High`
- `MSFT ▼ Yest Low`
- `GOOGL ▲ Week High`

## Status Table

The top-right table updates on each bar:

| Symbol | Signal |
|--------|--------|
| AAPL   | ▲ PM H |
| MSFT   | —      |
| GOOGL  | ▼ Yest L |
| AMZN   | —      |

Cells turn green for bullish signals, red for bearish, gray for no signal. Resets at each regular session open.
