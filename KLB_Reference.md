# KeyLevelBreakout v3.1 — Reference

| Doc | What's Inside |
|-----|---------------|
| [KLB_PLAYBOOK.md](KLB_PLAYBOOK.md) | Signal Catalog, Time Windows, Avoid List, Decision Flowchart, Execution, Symbols |
| **KLB_Reference.md** | Setup, Signal Types, Label Anatomy, CONF System, Levels, Filters, Visuals, Alerts, Settings |
| [KLB_DESIGN-JOURNAL.md](KLB_DESIGN-JOURNAL.md) | The Idea, Data Foundation, Key Discoveries, Filter Validation, Evolution, Dead Ends |

---

## 1. Setup

1. **Paste** `KeyLevelBreakout.pine` into TradingView Pine Editor, click **Add to chart**. Works on any timeframe at or below Signal Timeframe (e.g. 1m chart with 5m signals).
2. **Enable Extended Trading Hours** in chart settings (gear icon → Symbol → Extended Hours). Required for premarket level tracking.
3. **Add alert** → Condition: `Key Level Breakout` → `Any alert() function call`. This single alert covers all signal types, confirmations, retests, failures, VWAP exits, QBS, FADE, and RNG.

---

## 2. Signal Types

Eight signal types, each with a specific trigger and visual style.

**Breakout** — Signal-TF bar closes through a key level as a directional candle (bullish or bearish), with prior bar(s) on the other side of the level. Green labels (bull) / red labels (bear).

**Reversal (~)** — Wick enters a level zone, close rejects back out. Bullish reversals fire at LOW levels (blue labels), bearish reversals at HIGH levels (orange labels). No volume gate — reversals are judged by rejection quality, not volume.

**Reclaim (~~)** — Reversal after a prior breakout at that level was invalidated (CONF ✗). "False breakout then rejection." Same color scheme as reversals, brighter hue. Requires CONF system to be ON for the invalidation context.

**Retest (◆)** — After a breakout, price pulls back to the broken level within configurable proximity and holds. Each broken level is tracked independently. Fires an independent label at the retest bar (e.g. `◆³ ORB H 2.1x ^85`) and also appends a retest line to the original breakout label. The superscript number is the count of signal-TF bars since breakout.

**QBS (🔇 Quiet Before Storm)** — Pre-move volume drying (ramp < 0.5×) followed by a big bar (range ≥ 1.5× signal-TF ATR). Cyan labels. Once per direction per session. Does not require a key-level breakout.

**FADE** — Fires after a CONF ✗ (failed breakout) when price crosses back through the level in the opposite direction within 30 minutes. A contrarian signal that trades the failure. Purple labels.

**RNG (Range+Vol)** — 12-bar range breakout combined with volume ≥ 3× SMA(20). The only profitable non-EMA signal type — does NOT require EMA alignment. Teal labels. Independent of key levels.

### Direction Reference

| Setup | At HIGH level | At LOW level |
|-------|--------------|-------------|
| Breakout | ▲ LONG (green) | ▼ SHORT (red) |
| Reversal ~ | ▼ SHORT (orange) | ▲ LONG (blue) |
| Reclaim ~~ | ▼ SHORT (orange, brighter) | ▲ LONG (blue, brighter) |
| Retest ◆ | Confirms original break direction | Confirms original break direction |
| FADE | ▼ SHORT (purple) after failed bull BRK | ▲ LONG (purple) after failed bear BRK |
| RNG | ▲ LONG (teal) | ▼ SHORT (teal) |

QBS, FADE, and RNG signals are direction-agnostic relative to levels — they fire based on candle direction (close > open = bull, close < open = bear).

---

## 3. Label Anatomy

Every label stacks information on separate lines. A fully-loaded example:

```
⚡🔇 ORB L + PM L
5.5x ^92 ④ ⚠
◆³ ORB L 2.1x ^85
✓★
```

Line 1: `⚡🔇 ORB L + PM L` — Big-move flag, volume ramp glyph, level names (merged when confluent).
Line 2: `5.5x ^92 ④ ⚠` — Volume ratio, close position, Runner Score, body warning.
Line 3: `◆³ ORB L 2.1x ^85` — Retest line (per-level, superscript = signal bars since breakout).
Line 4: `✓★` — Confirmation status.

### Metrics Reference

| Symbol | Meaning | Example |
|--------|---------|---------|
| `2.1x` | Volume ratio vs SMA(20) baseline | 2.1× average volume |
| `^82` | Bull close position (82% toward bar high) | — |
| `v85` | Bear close position (85% toward bar low) | — |
| `◆³` | Retest, 3 signal bars after breakout | — |
| `✓` | Confirmed (auto-promoted) | Solid green/red, white text |
| `✓★` | High-conviction confirmed (BRK: vol < 5× + hour ≤ 10:xx) | Gold label, black text |
| `✗` | Failed (closed back through level) | Grayed out |
| `~` | Reversal (rejection off zone) | Blue/orange label |
| `~~` | Reclaim (reversal after failed breakout) | Blue/orange, brighter |
| `①`–`⑥` | Runner Score (6 factors) | Higher = more factors aligned |
| `⚡` | Big move (bar range ≥ 2× signal-TF ATR) | Informational marker (no size change) |
| `🔇` | Vol drying (ramp < 0.5×) — quiet before storm | Cyan label for standalone QBS |
| `R0`/`R1`/`R2` | Regime Score (EMA + VWAP alignment, 0-2) | R2 = best, R1 bull dimmed |
| `FADE` | Reverse signal after CONF ✗ + price crosses back | Purple label |
| `RNG` | Range+Vol breakout (12-bar range + vol ≥3x) | Teal label |
| `⚠` | Body ≥ 80% — fakeout warning | Appended to quality line |
| `?` | Dimmed signal (failed filter or moderate ramp) | Gray, size.tiny |
| `CHOP?` | 3+ consecutive CONF failures at session open | Orange label, no passes yet |

---

## 4. Confirmation System

The CONF system tracks whether a breakout "survives" or fails.

**CONF window:** Signals get 3 signal-TF bars (15 min on 5m TF) to confirm, up from 1 bar in v2.9. Significantly increases CONF rate.

**Auto-promote (✓):** When a new breakout fires in the same direction, the previous breakout's label is promoted to ✓ — it survived long enough for another signal to follow.

**Auto-Confirm R1:** EMA-aligned signals receive instant CONF ✓ — no time restriction, no waiting for a follow-through bar. Originally gated to before 10:30 ET, but v3.0b research showed the time cutoff caused unnecessary failures on profitable signals. The 5-minute HOLD/BAIL check (83% win vs 51%) is the real quality gate downstream.

**CONF ✓** — Label turns solid green (bull) or solid red (bear) with white text. Label resizes to `size.normal`.

**CONF ✓★** — Gold label with black text. BRK signals only: requires volume < 5× and confirmation before 11:00 ET (hour 9 or 10). QBS signals always get plain ✓ (✓★ was net negative at -1.47 ATR in v2.8b analysis). Same resize to `size.normal`.

**CONF ✗** — Label turns gray. Fires when price closes back through the most conservative level (lowest for bull breakouts, highest for bear) beyond the re-arm buffer. Resets the level for new signals.

**5-minute checkpoint** — One signal-TF bar after CONF ✓/✓★, evaluates P&L relative to the confirming breakout's close. Regime-aware BAIL (v3.1): signal aligned with SPY direction (>0.3%) → never BAIL; SPY neutral → loose BAIL (pnl > -0.10 ATR); signal opposes SPY → strict BAIL (pnl > 0.05 ATR). Appends `5m✓` or `5m✗` plus regime tag (✓/✗/~) to the label. Fires a HOLD or BAIL alert.

**VWAP exit alert** — After CONF ✓/✓★, monitors for price crossing VWAP against the confirmed direction. Fires an alert when a bull position crosses below VWAP, or a bear position crosses above VWAP. Resets at session start.

---

## 5. Levels

Twelve level types across eight sources.

| Level Type | Source | Zone Width | Reset |
|------------|--------|------------|-------|
| Premarket H/L | 04:00–09:30 ET live bars | ATR-derived (configurable, default 3%) | Daily |
| Yesterday H/L | Prior day candle (non-repainting) | Wick-to-body range from daily OHLC | Daily |
| Last Week H/L | Prior week candle (non-repainting) | Wick-to-body range from weekly OHLC | Weekly |
| ORB H/L | First signal-TF bar of regular session | ATR-derived (configurable, default 3%) | Daily |
| VWAP zone | Session VWAP ± 0.1× daily ATR | ATR-derived, continuous | Continuous |
| PD Last Hr Low | Prior day 15:00–16:00 ET low | ATR-derived | Daily |
| PD Mid | (Yesterday H + Yesterday L) / 2 | ATR-derived | Daily |
| VWAP Lower Band | VWAP − daily ATR | ATR-derived | Continuous |

New levels (v3.0) provide midday coverage. PD Mid fires as **REV only** (v3.1) — it's a magnet level where touch-and-turn is the correct signal type, not breakout. PD Last Hr Low and VWAP Lower Band participate in both BRK and REV detection.

**Zones:** When "Use Level Zones" is ON, each level expands to a range:
- Yesterday/Week: body edge (min/max of open, close) to wick edge (high/low). Wide zone = strong rejection area.
- PM/ORB: ATR-derived fixed width above and below the wick price.
- VWAP: ± 0.1× daily ATR around the live VWAP value.

Zone bands are visible as shaded fills when Show Level Lines is ON.

**ORB guard:** The first signal-TF bar after the ORB window is skipped for ORB signals, since that bar's data formed the ORB itself (self-referencing).

---

## 6. Filters

Nine configurable filters. Each can be independently toggled. Filter Mode controls what happens to blocked signals.

| Filter | What it does | Default |
|--------|-------------|---------|
| Volume | Requires signal-TF volume > multiplier × SMA(20). Uses directional 2-bar lookback (borrows prior bar's volume if same direction). | ON, 1.5× |
| ATR Buffer | Wick must push past level ± X% of daily ATR; close must hold beyond the raw level price. | ON, 5% |
| VWAP Direction | Suppresses counter-trend reversals: bear reversals above VWAP, bull reversals below VWAP. | ON |
| Once Per Breakout | One signal per level per direction. Re-arms when price closes back through level (invalidation). | ON |
| 5m EMA Alignment | Blocks signals against the 5m EMA(20)/EMA(50) trend direction. | ON |
| EMA Hard Gate | After 9:50 ET: non-EMA signals suppressed entirely. Before 9:50: dimmed only (EMA not established at open). Recovers +45.6 ATR. | ON |
| RS vs SPY | Blocks long signals when the symbol underperforms SPY (and vice versa for shorts). Auto-bypasses SPY, QQQ, GLD, SLV. | ON |
| ADX > 20 | Blocks signals when 5m ADX(14) < 20 (choppy/trendless environment). | ON |
| Candle Body Quality | Blocks wick-heavy candles: body < 30% of range, or close in the wrong 40% of the bar. | ON |
| Filter Mode | **Suppress:** filtered signals are hidden entirely. **Dim:** filtered signals show as gray with `?` suffix, size.tiny. | Suppress |

Breakout signals must pass both Volume and ATR Buffer. Reversal/reclaim signals must pass VWAP Direction but do not require the Volume gate. QBS signals pass through the reversal filter gate (EMA, RS, ADX, Body). RNG signals skip EMA requirement (the only profitable non-EMA signal type). FADE signals inherit context from the failed breakout.

---

## 7. Visual Elements

### Chart Overlays

| Element | Style | When Visible |
|---------|-------|-------------|
| VWAP line | Orange (`#FF6D00`), width 2, semi-transparent | Regular session, when Show VWAP Line ON |
| SL 0.10 ATR | Orange dashed, width 1 | 30 min after CONF ✓/✓★ signal |
| SL 0.15 ATR | Red solid, width 1 | 30 min after CONF ✓/✓★ signal |
| PM H/L lines | Orange, width 1 | Regular session, when Show Level Lines ON |
| Yest H/L lines | Blue, width 1 | Regular session, when Show Level Lines ON |
| Week H/L lines | Purple, width 1 | Regular session, when Show Level Lines ON |
| ORB H/L lines | Teal, width 1 | Regular session, when Show Level Lines ON |
| Zone fills | Same color as level line, 85% transparent | When Show Level Lines ON + Use Level Zones ON |

SL line duration adapts to chart timeframe: 1800 seconds / timeframe-in-seconds = number of bars. On a 1m chart, SL lines extend 30 bars. Entry proxy is the confirming breakout's close price.

### Regime Score

| Score | Meaning | Visual |
|-------|---------|--------|
| R2 | EMA aligned + VWAP aligned | Best regime, normal display |
| R1 | One of EMA/VWAP aligned | R1 bears normal; R1 bulls dimmed (31.2% win = harmful) |
| R0 | Neither aligned | Weak, be selective |

### Label Modifiers

| Condition | Visual Effect |
|-----------|--------------|
| R1 bull | Dimmed (31.2% win rate) |
| Afternoon (after 11:00 ET) | Smaller size, more transparent |
| Cooldown (within N signal bars of prior signal) | Gray, size.tiny |
| Confluence (2+ levels on same bar) | size.large |
| Big move (⚡, range ≥ 2× signal-TF ATR) | Glyph only, no size change (v2.8b: data showed 48% lower MFE) |
| Moderate vol ramp (1–2× ramp ratio) | Auto-dimmed: gray + `?` |
| CONF ✓ / ✓★ | Resized to size.normal, color changed |
| Volume-scaled opacity | Alpha = max(0, 60 − volRatio × 10), saturates at 6× |

---

## 8. Alerts

### Programmatic Alerts (via "Any alert() function call")

These fire through `alert()` calls. A single TradingView alert set to "Any alert() function call" catches all of them.

| Alert Message Pattern | When |
|-----------------------|------|
| `Bullish breakout: PM H + Yest H 2.1x ^82` | Bull breakout fires |
| `Bearish breakout: Yest L 1.5x v78` | Bear breakout fires |
| `Bullish reversal: ~ PM L 1.9x ^75` | Bull reversal fires |
| `Bearish reversal: ~ Yest H 2.0x v80` | Bear reversal fires |
| `Retest: ◆³ ORB H 2.1x ^85` | Retest detected at broken level |
| `Failed: ORB H + Yest H` | Breakout invalidated (CONF ✗) |
| `5m HOLD ▲ +0.12 ATR` | 5-minute checkpoint positive |
| `5m BAIL ▲ -0.05 ATR` | 5-minute checkpoint negative |
| `VWAP exit ▼ — bull CONF position crossed below VWAP` | VWAP exit triggered |
| `🔇 QBS Bull: vol drying → explosion 0.3x` | QBS signal fires |
| `FADE Bull: ✗ reversal at Yest H` | FADE signal fires |
| `RNG Bear: 12-bar range break 3.5x` | RNG signal fires |

### alertcondition() Entries

These appear in TradingView's alert condition dropdown for selective subscriptions.

1. Any Bullish Breakout
2. Any Bearish Breakout
3. Any Breakout
4. Any Bullish Reversal
5. Any Bearish Reversal
6. Any Reversal
7. QBS — Quiet Before Storm
8. FADE — Failed Breakout Reverse
9. RNG — Range+Vol Breakout
10. Any Setup
11. VWAP Exit Signal

---

## 9. Settings Reference

All `input.*` parameters, organized by group.

| Setting | Default | Group |
|---------|---------|-------|
| Premarket High/Low | On | Level Toggles |
| Yesterday High/Low | On | Level Toggles |
| Last Week High/Low | On | Level Toggles |
| ORB High/Low | On | Level Toggles |
| Signal Timeframe | 5m | Signals |
| Once Per Breakout | On | Signals |
| QBS Signals | On | Signals |
| FADE Signals | On | Signals |
| RNG Signals | On | Signals |
| Show Runner Score ①–⑥ | On | Signals |
| Signal Cooldown | 2 bars | Signals |
| VWAP Zone Signals | On | Signals |
| Retest-Only Mode | Off | Signals |
| Show Reversal Setups | On | Setups |
| Limit Reversal Window | Off | Setups |
| Show Reclaim Setups | On | Setups |
| Setup Active Window | 0930-1130 | Setups |
| Post-Breakout Confirmation | On | Confirmation |
| Retest Window | Session | Confirmation |
| Retest Proximity | 3% ATR | Confirmation |
| Require Above-Avg Volume | On | Filters |
| Volume Baseline | Signal TF SMA | Filters |
| Volume Multiplier | 1.5 | Filters |
| Volume SMA Length | 20 | Filters |
| Use ATR Buffer | On | Filters |
| Breakout Buffer | 5% ATR | Filters |
| Re-arm Buffer | 3% ATR | Filters |
| VWAP Directional Filter | On | Filters |
| 5m EMA Alignment Filter | On | Filters |
| EMA Hard Gate | On | Filters |
| RS vs SPY Filter | On | Filters |
| ADX Trend Strength Filter | On | Filters |
| Candle Body Quality Filter | On | Filters |
| Filter Mode | Suppress | Filters |
| Show Close Position % | On | Quality |
| Show Level Lines | Off | Visuals |
| Show VWAP Line | On | Visuals |
| Show SL Lines | On | Visuals |
| Dim Afternoon Signals | On | Visuals |
| Fade Old Labels | On | Visuals |
| Fade After | 100 bars | Visuals |
| Chop Day Warning | On | Signals |
| Use Level Zones | On | Zones |
| Zone Width PM/ORB | 3% ATR | Zones |
| PM H/L Reversal/Reclaim | On | Reversal/Reclaim Toggles |
| Yest H/L Reversal/Reclaim | On | Reversal/Reclaim Toggles |
| Week H/L Reversal/Reclaim | On | Reversal/Reclaim Toggles |
| ORB H/L Reversal/Reclaim | On | Reversal/Reclaim Toggles |
| Show Signal Table | Off | Debug |
| Log Signals (Pine Logs) | Off | Debug |
| Table Position | bottom_right | Debug |
| Max Table Rows | 20 | Debug |

---

## 10. Signal Timeframe

Signal TF (default 5m) controls which candle closes are evaluated for breakout, reversal, reclaim, QBS, FADE, and RNG signals. The chart can run on any lower timeframe (e.g. 1m) for visual detail — labels are identical regardless of chart TF.

Level tracking uses chart-native data for granularity (premarket high/low updates every chart bar). Retest detection uses chart-TF bars for wick precision. SL line duration is computed in chart-TF bars (1800s / bar duration).

All signal-TF data is fetched via `request.security()` with `lookahead = barmerge.lookahead_on` and `[1]` offset for non-repainting behavior.

---

## 11. Runner Score

Six factors, each worth 1 point, displayed as ①–⑥ on labels. Redesigned in v3.0, SPY-aligned added in v3.1.

| Factor | Condition |
|--------|-----------|
| EMA aligned | 5m EMA(20)/EMA(50) aligned with trade direction |
| Regime = 2 | Both EMA and VWAP aligned (R2) |
| Volume ≥ 10× | Volume ratio ≥ 10.0× SMA(20) baseline |
| Morning | Signal fires before 11:00 ET |
| SPY-aligned | Signal direction matches SPY market regime (>±0.3% from open) |
| CONF pass | Signal has been confirmed (✓ or ✓★) |

Score is capped at ⑥. Only displayed when score ≥ 1 and Runner Score is enabled.

---

## 12. Debug

### Signal Table

Chart overlay table showing all session signals. Columns: Time, Dir, Type, Levels, Vol, Pos, Conf, OHLC. Color-coded by setup type. Configurable position and max rows (5–50).

### Pine Logs

`log.info()` output with `[KLB]` prefix, gated by `barstate.isconfirmed` to prevent duplicate entries on real-time ticks.

Format:
```
[KLB] 9:40 ▲ BRK PM H vol=5.5x pos=^94 vwap=above ema=bull rs=+0.3% adx=28 body=72% O595.20 H596.10 L594.80 C596.05 ATR=1.25 SL=595.93/595.86 rawVol=1234567 volSMA=224000 buf=0.063 prices=596.10
```

Fields: time (ET), direction, type, levels, vol (ratio), pos (close position), vwap (above/below), ema (bull/bear trend), rs (% vs SPY), adx (5m value), body (candle body %), OHLC, ATR, SL (0.10/0.15 ATR), rawVol, volSMA, buf (ATR buffer), prices (level values).

Confirmation state changes log separately with `[KLB] CONF` prefix.
