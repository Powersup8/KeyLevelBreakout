# Key Level Breakout — Single Symbol

Visual indicator that plots breakout arrows directly on your chart when price closes through key levels.

## Features

- **Green triangle-up** (bullish) / **Red triangle-down** (bearish) with text labels (e.g. "PM H", "Yest L")
- **Optional level lines** — Horizontal lines for all active levels (off by default to reduce clutter)
- **Once Per Breakout** — One signal per level, re-arms after invalidation (on by default); turn off for backtesting
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
| Once Per Breakout | On | One signal per level; re-arms after invalidation |
| Signal Timeframe | 5 (5m) | Timeframe for breakout evaluation — signals only fire on closed bars of this TF |
| Show Level Lines | Off | Plot horizontal lines for active levels |

## Once Per Breakout (Invalidation Logic)

When enabled (default), each level fires **one signal** then stays suppressed until **invalidated**:

- Bullish breakout above PM High fires — suppressed while price holds above
- Price closes back below PM High (on a signal-TF bar) — **invalidated** (re-armed)
- Next bullish close above PM High — fires again

Each level is tracked independently — a suppressed PM High does not block a subsequent Yesterday High breakout. All flags reset at each regular session open. Turn **off** to fire on every qualifying cross (useful for backtesting).

## Signal Timeframe

The **Signal Timeframe** input (default: 5m) controls which candle closes are evaluated for breakouts. This lets you view a lower timeframe chart (e.g. 1m) for more detail while only triggering signals on completed 5m candles.

- **Chart on 5m, Signal TF = 5m**: Markers appear directly on the breakout candle
- **Chart on 1m, Signal TF = 5m**: Markers appear on the last 1m candle of the 5m period (where the 5m bar closed) — only one signal per 5m bar, not on every 1m candle
- **Chart timeframe must be ≤ Signal Timeframe** (e.g. 1m or 3m chart with 5m signals works; 15m chart with 5m signals does not)

Level tracking (premarket, ORB) still uses chart-native data for maximum granularity.

## Alert Messages

When using `Any alert() function call`, messages look like:
- `Bullish breakout above Premarket High`
- `Bearish breakout below Yesterday Low`
- `Bullish breakout above ORB High`

## Updating

Edit the script in Pine Editor and click **Save** — all charts using the indicator update automatically. Don't click "Add to chart" again (that creates a duplicate).

## Changelog

- **v1.3** — Invalidation-based signal logic: re-arms after price closes back through the level (replaces first-cross-only-per-day)
- **v1.2** — Signal Timeframe input: view 1m charts while only triggering on 5m closes; marker placed on last candle of signal-TF period
- **v1.1** — Added `alert()` calls for single-alert setup (one alert covers all levels)
- **v1.0** — Initial release: 4 level types, toggleable pairs, first-cross-only, visual markers, 11 alert conditions
