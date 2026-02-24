# Key Level Breakout — Single Symbol

Visual indicator that plots breakout arrows directly on your chart when price closes through key levels.

## Features

- **Green labels** (bullish) / **Red labels** (bearish) with dynamic text (e.g. "PM H 2.1x", "Yest L 1.8x")
- **Volume Confirmation** — filter breakouts by above-average volume with directional 2-bar lookback (toggleable, on by default)
- **ATR Buffer Zone** — require wick beyond level ± X% of daily ATR and close beyond raw level (toggleable, on by default)
- **Close Position %** — shows where the close landed within the bar's range (e.g. `^78` = 78% toward the high = strong buying pressure)
- **Post-Breakout Confirmation** — monitors chart-TF bars after breakout for follow-through (✓), retest-and-hold (⟳✓), or failure (✗)
- **Conviction coloring** — label opacity scales with volume ratio (faded = barely passed, bright = strong conviction)
- **Confluence merging** — when multiple levels break on the same bar, labels and alerts merge (e.g. "PM H + Yest H 2.1x") with a larger label size
- **Reversal setups** — detects rejection off level zones (wick enters zone, close rejects); bullish at LOW levels (blue), bearish at HIGH levels (orange)
- **Reclaim setups** — context-enriched reversal when a prior breakout was invalidated (false breakout → rejection); labeled with `~~` prefix
- **Level zones** — wick-to-body zones for daily/weekly levels (candle body data), ATR-derived for PM/ORB (toggleable)
- **Setup time window** — configurable active window for reversal/reclaim signals (default 9:30-11:30 ET)
- **Optional level lines** — Horizontal lines for all active levels (off by default to reduce clutter)
- **Once Per Breakout** — One signal per level, re-arms after invalidation (on by default); turn off for backtesting
- **`alert()` calls** — One merged alert per direction per bar (e.g. "Bullish breakout: PM H + Yest H")
- **3 `alertcondition()` entries** — "Any Bullish" + "Any Bearish" + "Any Breakout" for simple filtering in TradingView's alert dropdown

## Setup

1. Open TradingView Pine Editor, paste `KeyLevelBreakout.pine`, click **Add to chart** (works on any timeframe ≤ the Signal Timeframe — e.g. 1m chart with 5m signals)
2. Enable **Extended Trading Hours** in chart settings (required for premarket levels)
3. Set up alerts:
   - **Quick (recommended)**: Add one alert → Condition: `Key Level Breakout` → `Any alert() function call` — covers all levels, one toggle to switch on/off
   - **Granular**: Use `alertcondition()` entries from the dropdown — "Any Bullish", "Any Bearish", or "Any Breakout"
   - Visual markers (labels) always appear on the chart regardless of alert setup — alerts and visuals fire from the same signals

## Inputs

| Input | Default | Group | Description |
|-------|---------|-------|-------------|
| Premarket High/Low | On | Level Toggles | Track and alert on premarket levels |
| Yesterday High/Low | On | Level Toggles | Track and alert on previous day levels |
| Last Week High/Low | On | Level Toggles | Track and alert on previous week levels |
| ORB High/Low | On | Level Toggles | Track and alert on opening range levels |
| Once Per Breakout | On | Signals | One signal per level; re-arms after invalidation |
| Signal Timeframe | 5 (5m) | Signals | Timeframe for breakout evaluation — signals only fire on closed bars of this TF |
| Show Level Lines | Off | Visuals | Plot horizontal lines for active levels |
| Fade Old Labels | On | Visuals | Gray out labels older than N bars from chart edge — toggle off for historical analysis |
| Fade After (bars) | 100 | Visuals | Age threshold for fading (100 bars ≈ one session on 5m chart) |
| Require Above-Avg Volume | On | Filters | Gate breakouts on above-average volume (directional 2-bar lookback: borrows prior bar volume only if same direction) |
| Volume Baseline | Signal TF SMA | Filters | Compare against signal-TF SMA (granular) or daily average (stable) |
| Volume Multiplier | 1.5 | Filters | How many times above average volume is required (e.g. 1.5 = 150%) |
| Volume SMA Length | 20 | Filters | Lookback period for the volume moving average |
| Use ATR Buffer | On | Filters | Require wick beyond level ± X% of daily ATR(14) and close beyond raw level |
| Breakout Buffer (% of ATR) | 5.0 | Filters | How far past the level the wick must push to trigger a breakout (close only needs to hold above raw level) |
| Re-arm Buffer (% of ATR) | 3.0 | Filters | How far back through the level price must close to re-arm the signal |
| Show Close Position % | On | Quality | Display where the close landed within the bar's range (0-100%) |
| Post-Breakout Confirmation | On | Confirmation | Monitor chart-TF bars after breakout for follow-through or failure |
| Confirmation Window | 10 | Confirmation | How many chart bars to monitor (e.g. 10 bars = 10 min on 1m chart) |
| Show Reversal Setups | On | Setups | Enable reversal signal detection at level zones |
| Show Reclaim Setups | On | Setups | Enable reclaim labeling (reversal after failed breakout) |
| Setup Active Window (ET) | 0930-1130 | Setups | Time window for reversal/reclaim signals (ET format) |
| Use Level Zones | On | Zones | Use wick-to-body zones instead of single-price levels |
| Zone Width for PM/ORB | 3.0 | Zones | ATR% zone width for levels without candle body data |
| PM H/L Reversal/Reclaim | On | Rev/Recl Toggles | Enable reversal/reclaim at premarket levels |
| Yest H/L Reversal/Reclaim | On | Rev/Recl Toggles | Enable reversal/reclaim at yesterday levels |
| Week H/L Reversal/Reclaim | On | Rev/Recl Toggles | Enable reversal/reclaim at weekly levels |
| ORB H/L Reversal/Reclaim | On | Rev/Recl Toggles | Enable reversal/reclaim at opening range levels |

## Once Per Breakout (Invalidation Logic)

When enabled (default), each level fires **one signal** then stays suppressed until **invalidated**:

- Bullish breakout above PM High fires — suppressed while price holds above
- Price closes back below PM High minus the re-arm buffer (on a signal-TF bar) — **invalidated** (re-armed)
- Next bullish close above PM High plus the breakout buffer — fires again

Each level is tracked independently — a suppressed PM High does not block a subsequent Yesterday High breakout. All flags reset at each regular session open. Turn **off** to fire on every qualifying cross (useful for backtesting).

## Signal Timeframe

The **Signal Timeframe** input (default: 5m) controls which candle closes are evaluated for breakouts. This lets you view a lower timeframe chart (e.g. 1m) for more detail while only triggering signals on completed 5m candles.

- **Chart on 5m, Signal TF = 5m**: Markers appear directly on the breakout candle
- **Chart on 1m, Signal TF = 5m**: Markers appear on the last 1m candle of the 5m period (where the 5m bar closed) — only one signal per 5m bar, not on every 1m candle
- **Chart timeframe must be ≤ Signal Timeframe** (e.g. 1m or 3m chart with 5m signals works; 15m chart with 5m signals does not)

Level tracking (premarket, ORB) still uses chart-native data for maximum granularity.

## Post-Breakout Confirmation

When enabled (default), the indicator monitors chart-timeframe bars after a breakout fires. The breakout label is updated with a confirmation marker:

- **✓** (follow-through) — price stayed above the broken level for the entire confirmation window (default: 10 chart bars)
- **⟳✓** (retest confirmed) — price pulled back to the level, then closed back on the breakout side (classic "broken resistance becomes support")
- **✗** (failed) — price closed back through the level beyond the re-arm buffer (label turns gray)

Retest detection requires at least 2 chart bars after the breakout (prevents false instant confirmation). If a new breakout fires while the previous one is still being monitored, the previous one is auto-promoted to confirmed (it survived long enough for another level to break).

Confirmation also fires separate `alert()` calls: `"Confirmed: ORB H 2.1x ^78"` or `"Failed: ORB H 2.1x ^78"`.

## Reversal & Reclaim Setups

When enabled, the indicator detects two additional setup types at level zones:

**Reversal (`~` prefix):** A single-bar rejection pattern. The signal-TF bar's wick enters the level zone, but the close rejects back outside. Bullish reversals fire at LOW levels (e.g., `~ Yest L`), bearish at HIGH levels (e.g., `~ Yest H`). Labels are blue (bull) and orange (bear).

**Reclaim (`~~` prefix):** A reversal that occurs after a prior breakout at the same level was invalidated. For example: price breaks above Yesterday High, falls back below (invalidated), then a bearish reversal fires at Yesterday High — labeled as `~~ Yest H` instead of `~ Yest H`. This "false breakout → rejection" pattern often carries stronger conviction.

**Level Zones:** Each level is treated as a range (body edge to wick edge) rather than a single price:
- **Daily/Weekly levels:** Zone from candle body edge (`max(open, close)` for highs, `min(open, close)` for lows) to the wick (high/low)
- **PM/ORB levels:** Zone derived from ATR (configurable width, default 3%)
- When zones are disabled, all levels collapse back to single-price lines

Reversal/reclaim signals respect all existing filters (volume, Once Per Breakout) and only fire within the Setup Active Window (default 9:30-11:30 ET). Breakout signals continue to fire all session regardless of this window.

## Alert Messages

When using `Any alert() function call`, messages are merged per direction per bar:
- `Bullish breakout: PM H` — single level
- `Bearish breakout: Yest L` — single level
- `Bullish breakout: PM H + Yest H` — confluent (multiple levels on same bar)

For directional filtering, use `alertcondition()` entries from the dropdown — "Any Bullish Breakout", "Any Bearish Breakout", or "Any Breakout".

## Updating

Edit the script in Pine Editor and click **Save** — all charts using the indicator update automatically. Don't click "Add to chart" again (that creates a duplicate).

## Changelog

- **v1.7** — Reversal + Reclaim + Zones: wick-to-body zone detection for all levels (D/W from candle body, PM/ORB from ATR); reversal signals at level zones (~ prefix, blue/orange labels); reclaim signals when prior breakout invalidated (~~ prefix); configurable setup time window (default 9:30-11:30 ET); per-level reversal/reclaim toggles; 4 new alert conditions (Any Bullish/Bearish Reversal, Any Reversal, Any Setup)
- **v1.6** — Directional volume + close position + post-breakout confirmation: volume borrowing now direction-aware (only borrows prior bar if same-direction momentum); ATR buffer uses wick for push, close for hold; close position % shows buying/selling pressure in labels; post-breakout monitoring on chart TF with follow-through (✓), retest (⟳✓), and failure (✗) markers plus confirmation alerts
- **v1.5** — Fix cross-detection bug: 2-bar lookback prevents missed breakouts when a bearish candle crosses the level before a bullish confirmation (e.g., TSLA ORB High). Removed per-level alertcondition entries (duplicate alerts with "Any alert() function call")
- **v1.4** — Volume Confirmation filter (toggleable, Signal TF SMA or Daily Average baseline, multiplier in labels, conviction coloring), ATR Buffer Zone (separate breakout/re-arm buffers as % of daily ATR), confluence merging (combined labels + alerts when multiple levels break same bar), fade old labels (toggle for clean chart vs analysis mode), labels replace plotshape for dynamic text
- **v1.3** — Invalidation-based signal logic: re-arms after price closes back through the level (replaces first-cross-only-per-day)
- **v1.2** — Signal Timeframe input: view 1m charts while only triggering on 5m closes; marker placed on last candle of signal-TF period
- **v1.1** — Added `alert()` calls for single-alert setup (one alert covers all levels)
- **v1.0** — Initial release: 4 level types, toggleable pairs, first-cross-only, visual markers, 11 alert conditions
