# Key Level Breakout — Single Symbol

Overlay indicator for US equities (NYSE/NASDAQ) that detects four types of price action setups at key intraday levels: breakouts (continuation through a level), reversals (rejection off a level zone), reclaims (reversal after a failed breakout), and retests (pullback to a broken level that holds). Monitors Premarket High/Low, Yesterday High/Low, Last Week High/Low, and Opening Range Breakout High/Low — each toggleable independently.

All signals evaluate on confirmed signal-timeframe candle closes (default 5m) to avoid noise, while the chart can run on any lower timeframe (e.g. 1m) for detail. Breakouts require above-average volume (directional 2-bar lookback) and ATR-buffered level clearance. Level zones use wick-to-body ranges from daily/weekly candle data (or ATR-derived width for PM/ORB), visualized as shaded bands when level lines are enabled. Per-level retest tracking monitors each broken level independently after a breakout, recording bar count and price action quality (volume multiple + close position %) on the retest candle. Labels use line breaks to separate level names, quality metrics, and retest lines for readability. A Retest-Only Mode suppresses breakout labels entirely, showing only retest entries — useful for traders who use the breakout as confirmation but trade the retest.

## Features

- **Green labels** (bullish) / **Red labels** (bearish) with dynamic text (e.g. "PM H 2.1x", "Yest L 1.8x")
- **Volume Confirmation** — filter breakouts by above-average volume with directional 2-bar lookback (toggleable, on by default)
- **ATR Buffer Zone** — require wick beyond level ± X% of daily ATR and close beyond raw level (toggleable, on by default)
- **Close Position %** — shows where the close landed within the bar's range (e.g. `^78` = 78% toward the high = strong buying pressure)
- **Post-Breakout Confirmation** — monitors after breakout for retest-and-hold (◆), or failure (✗); retests fire independent labels and alerts
- **Conviction coloring** — label opacity scales with volume ratio (transparent = low conviction, opaque = strong conviction); wider alpha range makes differences more visible
- **CONF ✓ visual boost** — confirmed breakouts (auto-promoted) change to lime green; high-conviction (✓ + ≥5x volume + ≥80% close position) turn gold with ✓★ marker
- **Afternoon dimming** — signals after 11:00 ET render smaller and more transparent (toggleable, on by default); follow-through drops to near zero in the afternoon based on 6-week analysis
- **Chop day warning** — after 3+ consecutive CONF failures with zero passes at session start, an orange "CHOP?" label appears (toggleable, on by default)
- **VWAP Directional Filter** — suppress counter-trend reversals (bear reversals above VWAP, bull reversals below VWAP); on by default
- **Confluence merging** — when multiple levels break on the same bar, labels and alerts merge (e.g. "PM H + Yest H 2.1x") with a larger label size
- **Reversal setups** — detects rejection off level zones (wick enters zone, close rejects); bullish at LOW levels (blue), bearish at HIGH levels (orange)
- **Reclaim setups** — context-enriched reversal when a prior breakout was invalidated (false breakout → rejection); labeled with `~~` prefix
- **Level zones** — wick-to-body zones for daily/weekly levels (candle body data), ATR-derived for PM/ORB (toggleable)
- **Setup time window** — configurable active window for reversal/reclaim signals (default 9:30-11:30 ET); optional via "Limit Reversal Window" toggle (off by default = reversals fire all session)
- **Zone band visualization** — Shaded bands between wick and body edge for each level when level lines are on; wide band = strong rejection zone
- **Per-level retest tracking** — Each broken level tracked independently with configurable window (Short/Extended/Session); retests fire independent labels at the retest bar (e.g. `◆³ ORB H 2.1x ^85`) plus alerts in all modes
- **Retest-Only Mode** — Suppress breakout labels (small gray dot); only retest signals fire their own labels and alerts
- **Label management** — Same-bar breakout + reversal merge into one label; cooldown dimming for rapid signals (configurable, default 2 signal bars); vertical offset for adjacent labels to prevent overlap
- **Optional level lines** — Horizontal lines for all active levels (off by default to reduce clutter)
- **Once Per Breakout** — One signal per level, re-arms after invalidation (on by default); turn off for backtesting
- **`alert()` calls** — One merged alert per direction per bar (e.g. "Bullish breakout: PM H + Yest H")
- **7 `alertcondition()` entries** — "Any Bullish/Bearish Breakout", "Any Breakout", "Any Bullish/Bearish Reversal", "Any Reversal", "Any Setup" for filtering in TradingView's alert dropdown
- **Debug Signal Table** — togglable chart overlay table listing all session signals with Time, Dir, Type, Levels, Vol, Pos, Conf, OHLC columns; configurable position and max rows; color-coded by setup type
- **Debug Pine Logs** — togglable `log.info()` output with full signal data (`[KLB]` prefix) plus confirmation state change entries (`[KLB] CONF`); includes extended data (ATR, raw volume, volume SMA, buffer, level prices); all log calls gated by `barstate.isconfirmed` to prevent duplicate entries on real-time ticks

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
| Fade After (signal bars) | 100 | Visuals | Age threshold for fading in signal-TF bars (100 × 5m = ~8 hours, well beyond one session) |
| Dim Afternoon Signals | On | Visuals | Reduce size and opacity for signals after 11:00 ET (follow-through drops to near zero) |
| Require Above-Avg Volume | On | Filters | Gate breakouts on above-average volume (directional 2-bar lookback: borrows prior bar volume only if same direction) |
| Volume Baseline | Signal TF SMA | Filters | Compare against signal-TF SMA (granular) or daily average (stable) |
| Volume Multiplier | 1.5 | Filters | How many times above average volume is required (e.g. 1.5 = 150%) |
| Volume SMA Length | 20 | Filters | Lookback period for the volume moving average |
| Use ATR Buffer | On | Filters | Require wick beyond level ± X% of daily ATR(14) and close beyond raw level |
| Breakout Buffer (% of ATR) | 5.0 | Filters | How far past the level the wick must push to trigger a breakout (close only needs to hold above raw level) |
| Re-arm Buffer (% of ATR) | 3.0 | Filters | How far back through the level price must close to re-arm the signal |
| Show Close Position % | On | Quality | Display where the close landed within the bar's range (0-100%) |
| Post-Breakout Confirmation | On | Confirmation | Monitor after breakout for retest-and-hold or failure |
| Retest Window | Session | Confirmation | How long to track retests: Short (50 min), Extended (2.5 hr), or Session (until invalidated) |
| Retest Proximity (% of ATR) | 3.0 | Confirmation | How close a wick must come to the broken level to count as a retest |
| Retest-Only Mode | Off | Signals | Suppress breakout labels; only fire retest labels and alerts |
| Signal Cooldown (signal bars) | 2 | Signals | Dim same-direction signals within N signal bars of the previous signal (0 = off) |
| Chop Day Warning | On | Signals | Show "CHOP?" label after 3+ consecutive CONF failures with zero passes at session start |
| Show Reversal Setups | On | Setups | Enable reversal signal detection at level zones |
| Limit Reversal Window | Off | Setups | When ON, reversals only fire within Setup Active Window; when OFF (default), reversals fire all session |
| Show Reclaim Setups | On | Setups | Enable reclaim labeling (reversal after failed breakout) |
| Setup Active Window (ET) | 0930-1130 | Setups | Time window for reversal/reclaim signals when Limit Reversal Window is ON |
| VWAP Directional Filter | On | Filters | Suppress counter-trend reversals: bear reversals above VWAP, bull reversals below VWAP |
| Use Level Zones | On | Zones | Use wick-to-body zones instead of single-price levels |
| Zone Width for PM/ORB | 3.0 | Zones | ATR% zone width for levels without candle body data |
| PM H/L Reversal/Reclaim | On | Rev/Recl Toggles | Enable reversal/reclaim at premarket levels |
| Yest H/L Reversal/Reclaim | On | Rev/Recl Toggles | Enable reversal/reclaim at yesterday levels |
| Week H/L Reversal/Reclaim | On | Rev/Recl Toggles | Enable reversal/reclaim at weekly levels |
| ORB H/L Reversal/Reclaim | On | Rev/Recl Toggles | Enable reversal/reclaim at opening range levels |
| Show Signal Table | Off | Debug | Display a summary table of all session signals on the chart |
| Log Signals (Pine Logs) | Off | Debug | Output full signal data to Pine Logs panel with `[KLB]` prefix |
| Table Position | bottom_right | Debug | Chart corner for the debug table (6 positions) |
| Max Table Rows | 20 | Debug | Maximum number of signals shown in the table (5-50) |

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

## Post-Breakout Confirmation & Retest Tracking

When enabled (default), the indicator tracks retests **per level** after a breakout. Each broken level (e.g. PM H, Yest H) is monitored independently on every chart bar for maximum precision.

**Retest detection:** After a breakout, retest monitoring begins on the very next chart bar (e.g. the first 1m candle after the breakout's 5m period). If a candle's wick comes within the Retest Proximity (default 3% of ATR) of a broken level and the close holds on the breakout side, that level's retest is recorded. Early retests (1-2 bars after breakout) are stronger signals. Detection uses chart-TF data (e.g. 1m bars on a 1m chart) for precise wick detection, while timeout uses signal-TF bar counts for chart-independent consistency. Each retest creates an **independent label** at the retest bar showing:
- `◆` + superscript bar count (signal bars since breakout)
- Level name
- Volume multiple and close position % of the retest candle

The original breakout label is also updated with the retest information.

**Retest Window:** Controls how long retests are tracked:
- **Short (50 min):** 10 signal bars — original behavior
- **Extended (2.5 hr):** 30 signal bars — catches most intraday retests
- **Session (default):** Tracks until invalidated or market close — catches all retests

**Label format:**
```
◆³ ORB H 2.1x ^85
```
Independent label at the retest bar. Original breakout label also updated:
```
ORB H + Yest H
1.8x ^82
◆³ ORB H 2.1x ^85
◆⁷ Yest H 1.4x ^71
```

**Failure:** If price closes back through the most conservative level beyond the re-arm buffer, the label is updated with `✗` and grayed out.

**Auto-promotion:** If a new breakout fires while a previous one is being monitored, the previous one gets promoted to ✓ (it survived). The label turns **lime green** for regular confirmations, or **gold with ✓★** for high-conviction signals (≥5x volume AND ≥80% close position). High-conviction signals have a 54% win rate with 0% loss rate based on 6-week analysis. This is the only confirmation mechanism — 100% of CONF passes are auto-promotes.

**Alerts:** Retest alerts fire in all modes (not just Retest-Only): `"Retest: ◆³ ORB H 2.1x ^85"`.

**Retest-Only Mode:** When `i_retestOnly` is ON:
- Breakout labels are suppressed (replaced by small gray dots)
- Retest signals create their own labels at the retest bar
- Only retest alerts fire; breakout alerts are suppressed
- Reversal/reclaim labels are unchanged

## Reversal & Reclaim Setups

When enabled, the indicator detects two additional setup types at level zones:

**Reversal (`~` prefix):** A single-bar rejection pattern. The signal-TF bar's wick enters the level zone, but the close rejects back outside. Bullish reversals fire at LOW levels (e.g., `~ Yest L`), bearish at HIGH levels (e.g., `~ Yest H`). Labels are blue (bull) and orange (bear).

**Reclaim (`~~` prefix):** A reversal that occurs after a prior breakout at the same level was invalidated. For example: price breaks above Yesterday High, falls back below (invalidated), then a bearish reversal fires at Yesterday High — labeled as `~~ Yest H` instead of `~ Yest H`. This "false breakout → rejection" pattern often carries stronger conviction.

**Level Zones:** Each level is treated as a range (body edge to wick edge) rather than a single price:
- **Daily/Weekly levels:** Zone from candle body edge (`max(open, close)` for highs, `min(open, close)` for lows) to the wick (high/low)
- **PM/ORB levels:** Zone derived from ATR (configurable width, default 3%)
- When zones are disabled, all levels collapse back to single-price lines

Reversal/reclaim signals respect all existing filters (volume, Once Per Breakout). By default, reversals fire during the entire regular session (9:30-16:00 ET). Enable "Limit Reversal Window" to restrict them to the Setup Active Window (default 9:30-11:30 ET). An optional VWAP Directional Filter suppresses counter-trend reversals. Breakout signals always fire all session regardless of these settings.

When a new reversal/reclaim fires at a level that already had a prior reversal/reclaim signal, the prior label is grayed out (superseded by the newer signal with more context).

## Zone Band Visualization

When **Show Level Lines** and **Use Level Zones** are both ON, shaded bands are drawn between the wick line and the body edge for each level. The band width carries information:

- **Daily/Weekly levels:** Band width varies based on actual candle body-to-wick distance — a wide band means a long wick (strong rejection)
- **PM/ORB levels:** Uniform width derived from ATR (no single candle to reference)

Colors match the level type: orange (PM), blue (Yesterday), purple (Weekly), teal (ORB) at 85% transparency.

## Setup Direction Reference

Four setup types, each with a clear directional rule:

| Setup | At HIGH level (resistance) | At LOW level (support) | Rule |
|-------|---------------------------|----------------------|------|
| **Breakout** | Bullish break above → LONG | Bearish break below → SHORT | Trade the break |
| **Reversal `~`** | Bearish rejection down → SHORT | Bullish rejection up → LONG | Fade the approach |
| **Reclaim `~~`** | Bearish rejection after failed bull break → SHORT | Bullish rejection after failed bear break → LONG | Fade the trapped side |
| **Retest `◆✓`** | Pullback to level, held above → confirms LONG | Bounce to level, held below → confirms SHORT | Confirms original break |

**Breakout example (Yest H = $150):** Price closes above $150 on a green candle with volume → LONG.
```
Yest H
2.1x ^78
```

**Reversal example (Yest H = $150):** Price wicks into $150 zone from below, closes back below on a red candle → SHORT.
```
~ Yest H
1.8x v82
```

**Reclaim example (Yest H = $150):** Earlier bullish breakout above $150 failed. Price approaches again, wicks in, closes back below → SHORT.
```
~~ Yest H
2.3x v85
```

**Retest example (Yest H + ORB H = $150):** Confluent bullish breakout. 3 bars later, ORB H retested and held. 7 bars later, Yest H retested and held.
```
ORB H + Yest H
1.8x ^82
◆³ ORB H 2.1x ^85
◆⁷ Yest H 1.4x ^71
```

**Failed example:** Price closed back through the level → label grayed out.
```
Yest H
1.8x ^82
✗
```

**Retest-Only Mode:** Breakout becomes gray `·` dot. Retest fires its own label:
```
◆³ ORB H
2.1x ^85
```

### Visual Reference

```
  AT HIGH LEVELS (resistance)            AT LOW LEVELS (support)
  ═══════════════════════════            ═════════════════════════

  BREAKOUT                               BREAKOUT
  Price breaks ABOVE                     Price breaks BELOW
  ▲ LONG (green label)                   ▼ SHORT (red label)
  ┌────────────┐                         ┌────────────┐
  │ Yest H     │                         │ Yest L     │
  │ 2.1x ^78   │                         │ 1.8x v72   │
  └────────────┘                         └────────────┘

  REVERSAL ~                             REVERSAL ~
  Wick enters zone, close rejects        Wick enters zone, close rejects
  ▼ SHORT (orange label)                 ▲ LONG (blue label)
  ┌────────────┐                         ┌────────────┐
  │ ~ Yest H   │                         │ ~ Yest L   │
  │ 1.8x v82   │                         │ 2.0x ^75   │
  └────────────┘                         └────────────┘

  RECLAIM ~~                             RECLAIM ~~
  Prior break FAILED, now rejecting      Prior break FAILED, now rejecting
  ▼ SHORT (orange, brighter)             ▲ LONG (blue, brighter)
  ┌────────────┐                         ┌────────────┐
  │ ~~ Yest H  │                         │ ~~ Yest L  │
  │ 2.3x v85   │                         │ 2.5x ^80   │
  └────────────┘                         └────────────┘

  RETEST ◆                              RETEST ◆
  Pullback to level, held                Bounce to level, held
  ▲ confirms LONG                        ▼ confirms SHORT
  ┌──────────────────────┐               ┌──────────────────────┐
  │ Yest H               │               │ Yest L               │
  │ 2.1x ^78             │               │ 1.8x v72             │
  │ ◆³ Yest H 1.9x ^80  │               │ ◆³ Yest L 1.7x v78  │
  └──────────────────────┘               └──────────────────────┘

  FAILED ✗                               FAILED ✗
  Closed back through level              Closed back through level
  Label grayed out                       Label grayed out
  ┌────────────┐                         ┌────────────┐
  │ Yest H     │                         │ Yest L     │
  │ 2.1x ^78   │                         │ 1.8x v72   │
  │ ✗          │                         │ ✗          │
  └────────────┘                         └────────────┘
```

### Flow at a HIGH Level

```
  Price at HIGH level (e.g. Yest H):

       breaks above ──→ BREAKOUT (LONG) ──→ holds? ──→ ✓ auto-promoted
            │                                    │
            │                               pulls back to level
            │                                    │
            │                              ◆³ retest (per level)
            │                              with PA quality
            │                                 or
            │                              ✗ failed ──→ hadBrk = true
            │                                                │
            └── rejected ──→ REVERSAL (SHORT)                │
                                  │                          │
                                  └── if hadBrk ──→ RECLAIM (SHORT)
                                       (stronger conviction)
```

### Retest vs Reclaim

Both happen after a breakout — the difference is whether it held or failed:

```
  Breakout fires (e.g. bull break above Yest H)
       │
       ├── price pulls back to level, holds ABOVE
       │   → ◆³ RETEST — confirms original direction (LONG)
       │   per-level tracking with PA quality
       │   "broken resistance is now support"
       │
       └── price closes back BELOW level (invalidation)
           → ✗ FAILED — breakout is dead
                │
                └── price approaches level again, rejected
                    → ~~ RECLAIM — opposite direction (SHORT)
                    "breakout was a trap, fade it"
```

|  | Retest `◆` | Reclaim `~~` |
|---|---|---|
| Breakout outcome | Held (successful) | Failed (invalidated) |
| Direction | Same as breakout | Opposite to breakout |
| What it means | Level flipped role (resistance → support) | Trapped participants, fade them |
| Tracking | Per-level with bar count + PA quality | New label at reclaim bar |
| Visually | Appended as lines on breakout label | Creates a new label |

These are **mutually exclusive** — at the same level, you either get a retest (breakout worked) or eventually a reclaim (breakout failed). Never both.

## Alert Messages

When using `Any alert() function call`, messages are merged per direction per bar:
- `Bullish breakout: PM H 1.8x ^82` — single level (suppressed in Retest-Only Mode)
- `Bearish breakout: Yest L 1.5x v78` — single level (suppressed in Retest-Only Mode)
- `Bullish breakout: PM H + Yest H 2.1x ^82` — confluent (multiple levels on same bar)
- `Retest: ◆³ ORB H 2.1x ^85` — retest detected (fires in all modes)
- `Failed: ORB H + Yest H` — price closed back through level
- `Bullish reversal: ~ PM L 1.9x ^75` — reversal detected
- `Bearish reversal: ~ Yest H 2.0x v82` — reversal detected

For directional filtering, use `alertcondition()` entries from the dropdown — "Any Bullish Breakout", "Any Bearish Breakout", or "Any Breakout".

## Updating

Edit the script in Pine Editor and click **Save** — all charts using the indicator update automatically. Don't click "Add to chart" again (that creates a duplicate).

## Changelog

- **v2.4** — Visual quality tiers: CONF ✓ labels turn lime green (regular) or gold with ✓★ (high-conviction: ≥5x volume + ≥80% close position); afternoon dimming reduces size/opacity for signals after 11:00 ET (toggleable); chop day warning shows orange "CHOP?" label after 3+ consecutive CONF failures at session start (toggleable); volume alpha range widened (35→60) for better visual differentiation of low vs high volume signals; VWAP position added to Pine Log output (`vwap=above/below`); dead code cleanup: removed window expiry promotion path (never fired in 6-week analysis — all CONF passes are auto-promotes)
- **v2.3** — Signal quality fixes based on 3-day analysis (229 signals, 12 symbols): retest diamond bar count uses `bar_index` (1m accuracy) instead of `sigBarIdx` (display fix); reclaim (`~~`) gated behind CONF ✗ (only fires when preceding breakout's confirmation failed); VWAP directional filter default changed to ON (counter-trend reversals scored ~10% win rate); CONF race condition fix: `elapsed > 0` guard prevents immediate ✗ on same bar as CONF setup
- **v2.2** — Retest timing fix: retest eligible from first chart bar after breakout (no multi-bar delay); self-retest guard aligned with label placement (`shapeOff`); early retests (1-2 bars) are stronger signals. Alert timing fix: breakout/reversal alerts now use `freq_once_per_bar` for immediate firing (data is from completed previous bar); retest/failure alerts stay `freq_once_per_bar_close` (current-bar data). Pine Logs fix: all 7 `log.info()` calls gated with `barstate.isconfirmed` to emit one entry per confirmed bar instead of 50-100+ duplicates on real-time ticks
- **v2.1** — Debug Signal Table: togglable chart overlay table (8 columns: Time, Dir, Type, Levels, Vol, Pos, Conf, OHLC) with color-coded rows by setup type, configurable position and max rows; togglable Pine Logs output with full signal data (`[KLB]` prefix, extended fields: ATR, raw volume, volume SMA, buffer, level prices) plus confirmation state change entries (`[KLB] CONF`); both outputs independent, zero overhead when OFF
- **v2.0** — Signal Quality: VWAP directional filter for reversals (suppress counter-trend signals); reversal time window now optional (default full session, toggle to limit); retest system overhaul with session-long tracking (Short/Extended/Session dropdown), chart-TF precision detection, configurable proximity (% of ATR), independent retest labels at the retest bar, ◆ diamond symbol, and alerts in all modes; label management with same-bar merge (breakout + reversal → one label), cooldown dimming for rapid signals, and vertical offset to prevent overlap
- **v1.9** — Chart-TF independence: retest monitoring, failure detection, bar counts, and PA quality all evaluate on signal-TF data now (previously used chart-TF bars, causing different labels on 1m vs 5m charts); `sigQual()` replaces `chartQual()` for consistent retest metrics; `sigBarIdx` counter ensures bar counts are signal-TF bars regardless of chart timeframe; retest-only mode labels use consistent `shapeOff` placement; confirmation window input now in signal bars
- **v1.8** — Zone Band Visualization + Per-Level Retest + Retest-Only Mode: shaded fill bands between wick and body-edge plots for all 8 levels (gated by Show Level Lines + Use Level Zones); per-level retest tracking with independent monitoring of each broken level, superscript bar count, and PA quality metrics on retest candle (volume + close position %); label format upgraded to line breaks (level names / quality / retest lines); Retest-Only Mode toggle suppresses breakout labels and alerts, fires own retest labels; breakout alert suppression in retest-only mode
- **v1.7** — Reversal + Reclaim + Zones: wick-to-body zone detection for all levels (D/W from candle body, PM/ORB from ATR); reversal signals at level zones (~ prefix, blue/orange labels); reclaim signals when prior breakout invalidated (~~ prefix); configurable setup time window (default 9:30-11:30 ET); per-level reversal/reclaim toggles; 4 new alert conditions (Any Bullish/Bearish Reversal, Any Reversal, Any Setup)
- **v1.6** — Directional volume + close position + post-breakout confirmation: volume borrowing now direction-aware (only borrows prior bar if same-direction momentum); ATR buffer uses wick for push, close for hold; close position % shows buying/selling pressure in labels; post-breakout monitoring with follow-through (✓), retest (◆✓), and failure (✗) markers plus confirmation alerts
- **v1.5** — Fix cross-detection bug: 2-bar lookback prevents missed breakouts when a bearish candle crosses the level before a bullish confirmation (e.g., TSLA ORB High). Removed per-level alertcondition entries (duplicate alerts with "Any alert() function call")
- **v1.4** — Volume Confirmation filter (toggleable, Signal TF SMA or Daily Average baseline, multiplier in labels, conviction coloring), ATR Buffer Zone (separate breakout/re-arm buffers as % of daily ATR), confluence merging (combined labels + alerts when multiple levels break same bar), fade old labels (toggle for clean chart vs analysis mode), labels replace plotshape for dynamic text
- **v1.3** — Invalidation-based signal logic: re-arms after price closes back through the level (replaces first-cross-only-per-day)
- **v1.2** — Signal Timeframe input: view 1m charts while only triggering on 5m closes; marker placed on last candle of signal-TF period
- **v1.1** — Added `alert()` calls for single-alert setup (one alert covers all levels)
- **v1.0** — Initial release: 4 level types, toggleable pairs, first-cross-only, visual markers, 11 alert conditions
