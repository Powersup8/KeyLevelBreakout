# KeyLevelBreakout v2.9 — Reference

| Doc | What's Inside |
|-----|---------------|
| [KLB_PLAYBOOK.md](KLB_PLAYBOOK.md) | Signal Catalog, Time Windows, Avoid List, Decision Flowchart, Execution, Symbols |
| **KLB_Reference.md** | Setup, Signal Types, Label Anatomy, CONF System, Levels, Filters, Visuals, Alerts, Settings |
| [KLB_DESIGN-JOURNAL.md](KLB_DESIGN-JOURNAL.md) | The Idea, Data Foundation, Key Discoveries, Filter Validation, Evolution, Dead Ends |

---

## 1. Setup

1. **Paste** `KeyLevelBreakout.pine` into TradingView Pine Editor, click **Add to chart**. Works on any timeframe at or below Signal Timeframe (e.g. 1m chart with 5m signals).
2. **Enable Extended Trading Hours** in chart settings (gear icon → Symbol → Extended Hours). Required for premarket level tracking.
3. **Add alert** → Condition: `Key Level Breakout` → `Any alert() function call`. This single alert covers all signal types, confirmations, retests, failures, VWAP exits, and QBS/MC.

---

## 2. Signal Types

Six signal types, each with a specific trigger and visual style.

**Breakout** — Signal-TF bar closes through a key level as a directional candle (bullish or bearish), with prior bar(s) on the other side of the level. Green labels (bull) / red labels (bear).

**Reversal (~)** — Wick enters a level zone, close rejects back out. Bullish reversals fire at LOW levels (blue labels), bearish reversals at HIGH levels (orange labels). No volume gate — reversals are judged by rejection quality, not volume.

**Reclaim (~~)** — Reversal after a prior breakout at that level was invalidated (CONF ✗). "False breakout then rejection." Same color scheme as reversals, brighter hue. Requires CONF system to be ON for the invalidation context.

**Retest (◆)** — After a breakout, price pulls back to the broken level within configurable proximity and holds. Each broken level is tracked independently. Fires an independent label at the retest bar (e.g. `◆³ ORB H 2.1x ^85`) and also appends a retest line to the original breakout label. The superscript number is the count of signal-TF bars since breakout.

**QBS (🔇 Quiet Before Storm)** — Pre-move volume drying (ramp < 0.5×) followed by a big bar (range ≥ 1.5× signal-TF ATR). Cyan labels. Once per direction per session. Does not require a key-level breakout.

**MC (🔊 Momentum Cascade)** — Pre-move volume surging (ramp > 5×) followed by a big bar (range ≥ 1.5× signal-TF ATR). Orange labels. Once per direction per session. Suppressed before 9:50 ET (opening auction is noise — 126 opposing pairs showed 45% coin flip; 9:50+ direction matches 30-min outcome 79%). Does not require a key-level breakout.

### Direction Reference

| Setup | At HIGH level | At LOW level |
|-------|--------------|-------------|
| Breakout | ▲ LONG (green) | ▼ SHORT (red) |
| Reversal ~ | ▼ SHORT (orange) | ▲ LONG (blue) |
| Reclaim ~~ | ▼ SHORT (orange, brighter) | ▲ LONG (blue, brighter) |
| Retest ◆ | Confirms original break direction | Confirms original break direction |

QBS and MC signals are direction-agnostic relative to levels — they fire based on candle direction (close > open = bull, close < open = bear).

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
| `①`–`⑤` | Runner Score (5 factors) | Higher = more factors aligned |
| `⚡` | Big move (bar range ≥ 2× signal-TF ATR) | Informational marker (no size change) |
| `🔇` | Vol drying (ramp < 0.5×) — quiet before storm | Cyan label for standalone QBS |
| `🔊` | Vol surging (ramp > 5×) — momentum cascade | Orange label for standalone MC |
| `⚠` | Body ≥ 80% — fakeout warning | Appended to quality line |
| `?` | Dimmed signal (failed filter or moderate ramp) | Gray, size.tiny |
| `CHOP?` | 3+ consecutive CONF failures at session open | Orange label, no passes yet |

---

## 4. Confirmation System

The CONF system tracks whether a breakout "survives" or fails.

**Auto-promote (✓):** When a new breakout fires in the same direction, the previous breakout's label is promoted to ✓ — it survived long enough for another signal to follow. 100% of CONF passes use this mechanism.

**CONF ✓** — Label turns solid green (bull) or solid red (bear) with white text. Label resizes to `size.normal`.

**CONF ✓★** — Gold label with black text. BRK signals only: requires volume < 5× and confirmation before 11:00 ET (hour 9 or 10). QBS/MC signals always get plain ✓ (✓★ was net negative at -1.47 ATR in v2.8b analysis). Same resize to `size.normal`.

**CONF ✗** — Label turns gray. Fires when price closes back through the most conservative level (lowest for bull breakouts, highest for bear) beyond the re-arm buffer. Resets the level for new signals.

**5-minute checkpoint** — One signal-TF bar after CONF ✓/✓★, evaluates P&L relative to the confirming breakout's close. Appends `5m✓` (positive P&L = hold) or `5m✗` (negative P&L = bail) to the confirmed label. Fires a HOLD or BAIL alert.

**VWAP exit alert** — After CONF ✓/✓★, monitors for price crossing VWAP against the confirmed direction. Fires an alert when a bull position crosses below VWAP, or a bear position crosses above VWAP. Resets at session start.

---

## 5. Levels

Nine level types across five sources.

| Level Type | Source | Zone Width | Reset |
|------------|--------|------------|-------|
| Premarket H/L | 04:00–09:30 ET live bars | ATR-derived (configurable, default 3%) | Daily |
| Yesterday H/L | Prior day candle (non-repainting) | Wick-to-body range from daily OHLC | Daily |
| Last Week H/L | Prior week candle (non-repainting) | Wick-to-body range from weekly OHLC | Weekly |
| ORB H/L | First signal-TF bar of regular session | ATR-derived (configurable, default 3%) | Daily |
| VWAP zone | Session VWAP ± 0.1× daily ATR | ATR-derived, continuous | Continuous |

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
| RS vs SPY | Blocks long signals when the symbol underperforms SPY (and vice versa for shorts). Auto-bypasses SPY, QQQ, GLD, SLV. | ON |
| ADX > 20 | Blocks signals when 5m ADX(14) < 20 (choppy/trendless environment). | ON |
| Candle Body Quality | Blocks wick-heavy candles: body < 30% of range, or close in the wrong 40% of the bar. | ON |
| Filter Mode | **Suppress:** filtered signals are hidden entirely. **Dim:** filtered signals show as gray with `?` suffix, size.tiny. | Suppress |

Breakout signals must pass both Volume and ATR Buffer. Reversal/reclaim signals must pass VWAP Direction but do not require the Volume gate. QBS/MC signals pass through the reversal filter gate (EMA, RS, ADX, Body).

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

### Label Modifiers

| Condition | Visual Effect |
|-----------|--------------|
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
| `🔊 MC Bear: vol surging → continuation 6.2x` | MC signal fires |

### alertcondition() Entries

These appear in TradingView's alert condition dropdown for selective subscriptions.

1. Any Bullish Breakout
2. Any Bearish Breakout
3. Any Breakout
4. Any Bullish Reversal
5. Any Bearish Reversal
6. Any Reversal
7. QBS — Quiet Before Storm
8. MC — Momentum Cascade
9. Any Setup
10. VWAP Exit Signal

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
| QBS/MC Signals | On | Signals |
| Show Runner Score ①–⑤ | On | Signals |
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

Signal TF (default 5m) controls which candle closes are evaluated for breakout, reversal, reclaim, and QBS/MC signals. The chart can run on any lower timeframe (e.g. 1m) for visual detail — labels are identical regardless of chart TF.

Level tracking uses chart-native data for granularity (premarket high/low updates every chart bar). Retest detection uses chart-TF bars for wick precision. SL line duration is computed in chart-TF bars (1800s / bar duration).

All signal-TF data is fetched via `request.security()` with `lookahead = barmerge.lookahead_on` and `[1]` offset for non-repainting behavior.

---

## 11. Runner Score

Five factors, each worth 1 point, displayed as ①–⑤ on labels.

| Factor | Condition |
|--------|-----------|
| VWAP aligned | Close above VWAP (bull) or below VWAP (bear) |
| Volume 2–5× | Volume ratio ≥ 2.0× and < 5.0× SMA(20) baseline |
| Time 9:30–10:00 | Signal fires in the first 30 minutes of regular session |
| Not D-tier symbol | Symbol is not AMD, MSFT, GLD, or TSM |
| Level quality | **Bear:** always +1 (bear breakouts are at LOW levels, which have higher follow-through). **Bull:** +1 only when 2+ levels break simultaneously (confluence). |

Score is capped at ⑤. Only displayed when score ≥ 1 and Runner Score is enabled.

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
