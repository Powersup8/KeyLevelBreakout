# Key Level Breakout — Single Symbol

Visual indicator that plots breakout arrows directly on your chart when price closes through key levels.

## Features

- **Green triangle-up** (bullish) / **Red triangle-down** (bearish) with text labels (e.g. "PM H", "Yest L")
- **Optional level lines** — Horizontal lines for all active levels (off by default to reduce clutter)
- **First Cross Only** — One clean signal per level per day (on by default); turn off for re-test analysis
- **`alert()` calls** — One alert covers all levels with descriptive messages
- **11 `alertcondition()` entries** — 8 individual (one per level) + "Any Bullish" + "Any Bearish" + "Any Breakout"

## Setup

1. Open TradingView Pine Editor, paste `KeyLevelBreakout.pine`, click **Add to chart** (works on any timeframe ≤ the Signal Timeframe — e.g. 1m chart with 5m signals)
2. Enable **Extended Trading Hours** in chart settings (required for premarket levels)
3. Set up alerts:
   - **Quick (recommended)**: Add one alert → Condition: `Key Level Breakout` → `Any alert() function call` — covers all levels, one toggle to switch on/off
   - **Granular**: Use individual `alertcondition()` entries from the dropdown for specific levels
   - Visual markers (triangles + labels) always appear on the chart regardless of alert setup — alerts and visuals fire from the same signals

## Inputs

| Input | Default | Description |
|-------|---------|-------------|
| Premarket High/Low | On | Track and alert on premarket levels |
| Yesterday High/Low | On | Track and alert on previous day levels |
| Last Week High/Low | On | Track and alert on previous week levels |
| ORB High/Low | On | Track and alert on opening range levels |
| First Cross Only | On | One signal per level per day |
| Signal Timeframe | 5 (5m) | Timeframe for breakout evaluation — signals only fire on closed bars of this TF |
| Show Level Lines | Off | Plot horizontal lines for active levels |

## Alert Messages

When using `Any alert() function call`, messages look like:
- `Bullish breakout above Premarket High`
- `Bearish breakout below Yesterday Low`
- `Bullish breakout above ORB High`
