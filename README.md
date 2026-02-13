# Key Level Breakout

TradingView Pine Script v6 indicators that detect when a bullish/bearish candle closes through key price levels. Designed for US stocks (NYSE/NASDAQ) on 5-minute charts.

Two variants:
- **`KeyLevelBreakout.pine`** — Single-symbol indicator with visual markers on chart
- **`KeyLevelScanner.pine`** — Multi-symbol scanner (up to 8 tickers) with status table and unified alerts

## Levels

| Level | Source |
|-------|--------|
| **Premarket High/Low** | Tracked bar-by-bar during premarket (0400-0930 ET), frozen at open |
| **Yesterday High/Low** | Previous daily high/low via `request.security` (non-repainting) |
| **Last Week High/Low** | Previous weekly high/low via `request.security` (non-repainting) |
| **ORB High/Low** | High/low of the first 5-min bar at 9:30 ET |

## Breakout Logic

- **Bullish**: Candle is green + closes above a high level + previous close was at or below
- **Bearish**: Candle is red + closes below a low level + previous close was at or above

## Features

- **Toggleable level pairs** — Enable/disable each of the 4 level pairs independently
- **First Cross Only** — One clean signal per level per day (on by default); turn off for re-test analysis
- **Visual markers** — Green triangle-up (bullish) / red triangle-down (bearish) with text labels (e.g. "PM H", "Yest L")
- **Optional level lines** — Horizontal lines for all active levels (off by default to reduce clutter)
- **11 alert conditions** — 8 individual (one per level) + "Any Bullish" + "Any Bearish" + "Any Breakout"

## Setup — Single Symbol (`KeyLevelBreakout.pine`)

1. Open TradingView Pine Editor, paste the script, click **Add to chart** on a 5-min US stock chart
2. Enable **Extended Trading Hours** in chart settings (required for premarket levels)
3. Set up alerts:
   - **Quick**: Add one alert → Condition: `Key Level Breakout` → `Any alert() function call` — covers all levels
   - **Granular**: Use individual `alertcondition()` entries from the dropdown

## Setup — Multi-Symbol Scanner (`KeyLevelScanner.pine`)

1. Add the script to any 5-min US stock chart (the chart symbol doesn't matter)
2. Enable **Extended Trading Hours** in chart settings
3. Configure up to 8 symbols in the **Watchlist** input group (first 4 enabled by default)
4. Add **one alert** → Condition: `Key Level Breakout Scanner` → `Any alert() function call`
5. That single alert covers all symbols — messages include the ticker name (e.g. *"AAPL ▲ PM High"*)
6. A status table in the top-right corner shows each symbol's last signal for the day

## Inputs

### Shared (both variants)

| Input | Default | Description |
|-------|---------|-------------|
| Premarket High/Low | On | Track and alert on premarket levels |
| Yesterday High/Low | On | Track and alert on previous day levels |
| Last Week High/Low | On | Track and alert on previous week levels |
| ORB High/Low | On | Track and alert on opening range levels |
| First Cross Only | On | One signal per level per day |

### Single-symbol only

| Input | Default | Description |
|-------|---------|-------------|
| Show Level Lines | Off | Plot horizontal lines for active levels |

### Scanner only

| Input | Default | Description |
|-------|---------|-------------|
| Symbol 1–8 | AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA, SPY | Tickers to monitor |
| Enable toggles | 1–4 on, 5–8 off | Enable/disable each slot |
