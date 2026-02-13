# Key Level Breakout Alert Indicator

TradingView Pine Script v6 indicator that detects when a bullish/bearish candle closes through key price levels. Designed for US stocks (NYSE/NASDAQ) on 5-minute charts.

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

## Setup

1. Open TradingView Pine Editor, paste `KeyLevelBreakout.pine`, click **Add to chart** on a 5-min US stock chart
2. Enable **Extended Trading Hours** in chart settings (required for premarket levels)
3. Set up alerts via the alert dialog — all 11 conditions appear in the dropdown

## Inputs

| Input | Default | Description |
|-------|---------|-------------|
| Premarket High/Low | On | Track and alert on premarket levels |
| Yesterday High/Low | On | Track and alert on previous day levels |
| Last Week High/Low | On | Track and alert on previous week levels |
| ORB High/Low | On | Track and alert on opening range levels |
| First Cross Only | On | One signal per level per day |
| Show Level Lines | Off | Plot horizontal lines for active levels |
