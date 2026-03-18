# KeyLevelBreakout.pine — Improvement Plan

**Date:** 2026-02-24 (updated 2026-03-03)
**Status:** Tiers 1-2 complete, v2.4-v2.8 shipped. v2.8: Big-Move Fingerprint Integration — vol ramp (🔇QBS/🔊MC signals), 2x ATR flag (⚡), body warning (⚠), moderate ramp dimming, Runner Score tuned (9:30-10, TSM D-tier, closeLoc 0.3). Remaining: items 4-6, 9-10, 12-13.
**Source:** Analysis of current code + Tom Vorwald's Mag 7 / volume / liquidity methodology

---

## Session Context

### Tom Vorwald Video Analysis
Video: ["Der PERFEKTE Frühindikator"](https://www.youtube.com/watch?v=ut9eUdP6-YE) by Tom Vorwald (TradeTheTraders, mentor to 2x World Cup Trading Champion Patrick Nill).

**His "Perfect Leading Indicator" method:**
1. **Four Quadrant Model** (Growth vs Inflation) → determine macro phase (Recovery = Risk-On, overvalue stocks)
2. **Fear & Greed Index** across multiple timeframes (day/week/month/year) → gauge sentiment extremes for contrarian signals
3. **Analyze each Mag 7 stock individually** — they hold >30% of S&P/Nasdaq weight:
   - Check volume (declining = no dominant side)
   - Apply PBD/auction logic (price vs value area, balance zones)
   - Consider fundamental context (e.g., Amazon weak = consumer spending weak)
   - Rate each: **+** (bullish), **−** (bearish), **?** (wait)
4. **Aggregate into index bias** — majority bearish Mag 7 → short bias for index futures; only flip long if Mag 7 get explosively bought above key levels
5. **Apply to swing/intraday** — trade in direction of macro bias, let winners run when institutional liquidity confirms

**Key takeaways for our indicators:**
- Volume/liquidity is essential for confirming breakouts (we have none)
- Macro context matters — trading against the trend is lower probability
- Levels are zones where institutional capital acts, not exact prices

---

## Current State of KeyLevelBreakout.pine (v2.8)

`KeyLevelBreakout.pine` (~1585 lines) detects five setup types at key intraday levels on a configurable signal timeframe:

- **Breakout** — closes through a level with volume + ATR buffer confirmation
- **Reversal (`~`)** — wick enters level zone, close rejects back (blue/orange labels)
- **Reclaim (`~~`)** — reversal after a prior breakout was invalidated (false breakout trap)
- **Retest (`◆`)** — per-level pullback tracking after breakout, with PA quality metrics

**4 level types:** Premarket H/L (live 04:00–09:30 ET), Yesterday H/L, Last Week H/L, ORB H/L.

**Filters:** Volume confirmation (directional 2-bar lookback), ATR buffer zone (wick push + close hold), VWAP directional filter (reversals only), Once Per Breakout with invalidation re-arm. **Evidence Stack Filters** (v2.5): 5m EMA Alignment, RS vs SPY, ADX > 20, Candle Body Quality — all toggleable, Suppress or Dim mode.

- **QBS (Quiet Before Storm)** — pre-move volume drying (<0.5x ramp) + big bar (≥1.5x 5m-ATR). Cyan labels. Once per direction per session.
- **MC (Momentum Cascade)** — explosive pre-move volume (>5x ramp) + big bar (≥1.5x 5m-ATR). Orange labels. Once per direction per session.

**Quality metrics:** Close position % (`^78`/`v85`), volume ratio (`2.1x`), conviction coloring, label management (merge, cooldown dimming, vertical offset). **Runner Score ①-⑤** (v2.6, tuned v2.8: time 9:30-10, +TSM D-tier) on labels. **CONF ✓** (lime green) / **✓★** (gold) visual tiers. Afternoon dimming after 11:00 ET. **Body ≥80% warning** (⚠ on labels). **Volume ramp glyphs** (🔇 quiet / 🔊 explosive). **Big-move flag** (⚡ on 2x ATR bars). **Moderate ramp dimming** (1-2x vol ramp = gray + ?).

**Trade management (v2.6+):** VWAP line plotted on chart, SL reference lines at 0.10/0.15 ATR for 5 minutes after signal, VWAP cross exit alert after CONF ✓/✓★. 5-minute checkpoint (v2.7).

**Retest system:** Session-long per-level tracking, chart-TF wick precision, configurable proximity, independent labels (`◆³ ORB H 2.1x ^85`), Retest-Only Mode.

**Debug system (v2.1, fixed v2.2):** Chart overlay table (8 columns, color-coded) + Pine Logs (`log.info()` with `[KLB]` prefix, extended data including ema/rs/adx/body fields, `barstate.isconfirmed` guard). Both togglable independently.

**Companion file:** `KeyLevelScanner.pine` (~187 lines) — multi-symbol version (v1.2) monitoring up to 8 tickers with a status table. Uses breakout-only logic; does not yet include volume, ATR buffer, reversals, retests, or debug features.

---

## Improvements — Priority Tier 1 (Implement First)

### 1. Volume Confirmation (HIGH impact, ~15 lines) ✅ IMPLEMENTED v1.4, refined v1.6

**Problem:** A breakout on below-average volume is unreliable. Currently no volume awareness at all.

**Implementation:**
```pine
// New inputs
i_volFilter = input.bool(true, "Require Above-Avg Volume", group="Filters")
i_volMult   = input.float(1.5, "Volume Multiplier", minval=0.5, step=0.1, group="Filters")
i_volLen    = input.int(20, "Volume SMA Length", minval=5, group="Filters")

// In signal timeframe data section — fetch volume alongside OHLC
// Add vol[1] to the request.security tuple (sigC, sigO, sigPC)
// Compute: sigVol > i_volMult * ta.sma(sigVol, i_volLen)

// Modify bullBreak / bearBreak helpers to include volume gate:
bullBreak(float level) =>
    not na(level) and isRegular and newSigBar
     and sigC > sigO and sigC > level and sigPC <= level
     and (not i_volFilter or sigVol > volThreshold)
```

**For KeyLevelScanner.pine:** Add volume to `request.security` tuple per symbol, pass it through `scan()` → `chk()`.

**Optional enhancement:** Show volume multiplier in label text (e.g., "PM H 2.1x").

---

### 2. ATR Buffer Zone (HIGH impact, ~5 lines) ✅ IMPLEMENTED v1.4, refined v1.6

**Problem:** A close 1 cent above Yesterday High is noise, not a real breakout. Levels are zones, not exact prices.

**Implementation:**
```pine
// New inputs
i_atrBuf   = input.bool(true, "Use ATR Buffer", group="Filters")
i_atrPct   = input.float(5.0, "Buffer (% of ATR)", minval=0, step=1, group="Filters")

// Compute buffer
atr14  = ta.atr(14)
buffer = i_atrBuf ? atr14 * i_atrPct / 100.0 : 0.0

// Modify breakout helpers — add buffer to level comparison:
bullBreak(float level) =>
    not na(level) and isRegular and newSigBar
     and sigC > sigO and sigC > (level + buffer) and sigPC <= level

bearBreak(float level) =>
    not na(level) and isRegular and newSigBar
     and sigC < sigO and sigC < (level - buffer) and sigPC >= level
```

**Note:** Only the *close* comparison gets the buffer. The *prev_close* comparison stays at the raw level (otherwise we'd miss setups where price was hovering just past the level).

---

### 3. VWAP Bias Filter (MEDIUM impact, ~10 lines) ✅ IMPLEMENTED v2.0

**Problem:** No intraday directional context. Counter-trend reversals are the #1 noise source.

**Implemented:** VWAP directional filter gates **reversal helpers** (not breakouts) — bull reversals suppressed below VWAP, bear reversals suppressed above VWAP. Default OFF. Applied to `bullRev`/`bearRev` helper functions.

---

## Improvements — Priority Tier 2 (Implement After Tier 1 Proves Valuable)

### 4. Level Confluence Detection (MEDIUM-HIGH impact)

**Problem:** PM High, Yesterday High, and Week High might cluster within pennies of each other — that's a much stronger level than any single one, but the indicator treats them independently.

**Implementation approach:**
- After computing all levels, check pairwise distances
- If 2+ levels are within a threshold (e.g., 0.3% of ATR(14)), treat as confluent
- On breakout, show combined label: "PM H + Yest H" instead of two separate signals
- Optional: different color/size for confluent breakouts

**Complexity:** Medium — need to compare all level pairs (up to 8 levels = 28 pairs, but most will be `na`).

---

### 5. Breakout Quality / Conviction Scoring (MEDIUM impact)

**Problem:** Not all breakouts are equal. A strong body close far beyond the level is much more convincing than a small candle barely past it.

**Implementation approach:**
- Compute distance of close beyond level as % of ATR
- Compute candle body ratio: `abs(close - open) / (high - low)`
- Score: weak (small distance, long wicks), moderate, strong (large distance, full body)
- Color code labels: gray/yellow/green for bull, gray/orange/red for bear

---

### 6. Level Proximity Warning (MEDIUM impact)

**Problem:** You only find out about a breakout after it happens. A heads-up when price approaches a key level lets you prepare.

**Implementation approach:**
- Define "approaching" as price within X% of ATR from a level (e.g., 0.2%)
- Show subtle visual (dotted line, small label) when approaching
- Fire a separate alert condition: "Approaching PM High"
- Auto-dismiss if price moves away

---

### 7. Retest Detection (MEDIUM impact) ✅ IMPLEMENTED v1.6, upgraded v1.8, overhauled v2.0

**Problem:** Many traders prefer the retest entry over the initial break — better risk/reward. After a breakout, flag when price pulls back to the level and holds.

**v1.6:** Integrated into the post-breakout confirmation system with single-tracker per direction.

**v1.8 upgrade:** Per-level retest tracking (each broken level tracked independently), PA quality metrics on retest candle (volume + close position), smart label summarization with line breaks and superscript bar counts, retest-only toggle mode.

**v2.0 overhaul:** Session-long retest tracking (Short/Extended/Session dropdown replaces fixed 10-bar window); chart-TF detection for wick precision (un-gated from newSigBar); configurable proximity (% of ATR); independent retest labels at the retest bar (◆ diamond symbol); alerts fire in all modes (not just retest-only). Resolves the TODO about alerts in normal mode.

---

### 8.6. Zone Band Visualization + Retest-Only Mode (MEDIUM-HIGH impact) ✅ IMPLEMENTED v1.8

**Problem:** Level zones were computed but not visually displayed. Retest entry wasn't a first-class signal.

**Implemented:** Shaded fill bands between wick and body-edge plots for all 8 levels (gated by Show Level Lines + Use Level Zones). Retest-Only Mode input suppresses breakout labels and alerts, fires own retest labels with PA quality. Label format upgraded to use line breaks.

### 8.7. Reversal Window Toggle ✅ IMPLEMENTED v2.0

**Problem:** Setup window 0930-1130 missed all afternoon reversals.

**Implemented:** New `Limit Reversal Window` toggle (default OFF). When OFF, reversals fire during entire regular session. When ON, existing Setup Active Window controls the time range. Allows catching afternoon reversals (e.g., GOOGL PM Low bounce at 12:00+).

### 8.8. Label Management ✅ IMPLEMENTED v2.0

**Problem:** Label clustering at open (3-5 labels in 15 min), overlapping labels from different setup types.

**Implemented:** Three improvements: (a) Same-bar merge — breakout + reversal in same direction → one combined label; (b) Cooldown dimming — rapid same-direction signals within N signal bars render dimmer/smaller (default 2 bars); (c) Vertical offset — adjacent same-direction labels shifted by ATR to prevent overlap.

### 8.5. Reversal + Reclaim Setups (HIGH impact) ✅ IMPLEMENTED v1.7

**Problem:** Only detected breakouts (continuation). Missed reversal (rejection off level) and reclaim (false breakout + rejection) patterns from the PDH/PDL strategy.

**Implemented:** Three setup types in one indicator: Continuation (existing breakout, refined), Reversal (wick enters zone, close rejects), Reclaim (reversal after invalidated breakout). Level zones (wick-to-body) for D/W, ATR-derived for PM/ORB. Configurable time window (default 9:30-11:30 ET). Per-level toggles. Blue/orange labels for reversals.

---

### 9. Retest as Fair Value Gap (FVG) — needs deep analysis

**Idea:** Treat the retest zone as a Fair Value Gap. Instead of just checking "did price dip back to the level?", detect whether the pullback creates an FVG pattern — an imbalance gap between candles that institutional capital tends to fill. This could significantly improve retest quality filtering by distinguishing mechanical retests from true liquidity-driven pullbacks.

**Open questions (think deeply before implementing):**
- How to define the FVG zone relative to the broken key level
- Does the FVG need to overlap with the key level zone, or is proximity enough?
- Should FVG detection run on signal TF or a lower TF for finer granularity?
- Integration with existing retest PA quality metrics (volume ratio, close position)
- Risk of over-filtering: FVG retests are higher quality but much rarer

---

### 10. Weekly Level Naming + Current Week H/L — think later

**Ideas:**
- **Rename "Week H/L" to "Last Week H/L"** in labels and inputs for clarity (currently says "Week H" which is ambiguous)
- **Consider adding Current Week H/L** as a new level type — this week's developing high/low as intraday reference. Only qualifies if the current week's range is established (e.g., after Monday's session). Could provide tighter, more relevant weekly levels compared to last week's range on stocks that have moved significantly.

**Open questions:**
- When does "this week's H/L" qualify? After first full session? After N sessions?
- Does it need special handling on Mondays (range too narrow)?
- Would this conflict with or duplicate PM/Yesterday levels in some cases?
- `request.security("W", high/low)` gives current week's developing range — but needs `lookahead` handling to avoid repainting

---

### 11. Debug Signal Table (MEDIUM impact) ✅ IMPLEMENTED v2.1

**Problem:** Reading label text from the chart is tedious and error-prone (small text, overlapping labels, hard to screenshot). Need a way to export/inspect all fired signals with exact data for debugging and signal quality analysis.

**Ideas:**
- **Pine table** (like the debug table from v1.9): Show last N signals in a `table.new()` with columns: Time, Type (breakout/reversal/reclaim/retest), Levels, Volume, Close Position, Direction
- **CSV export via `log.info()`** or Pine Logs: Pine v6 supports `log.info()` which outputs to TradingView's Pine Logs panel — could log each signal as a structured line for copy-paste
- **`label.get_text()` loop**: Iterate over recent labels and dump their text into a table
- **Dedicated debug mode input**: `i_debugTable = input.bool(false, "Show Signal Table")` — when ON, renders a summary table in a corner of the chart

**Open questions:**
- What's the max rows in a Pine table before it becomes unreadable?
- Should the table show ALL signals or just the last N?
- Could we combine this with the backtest strategy version for automated analysis?

---

### 14. Fix: Retest timing + log.info() spam ✅ FIXED v2.2

**Problem 1:** Retest had multi-bar timing delays (`chartElapsed >= 2`, then `elapsed >= 1`) that blocked legitimate early retests. Early retests (1-2 bars after breakout) are actually stronger signals.

**Fix:** Minimal self-retest guard (`bar_index > bRTBar0`) — only the breakout bar itself is excluded. `bRTBar0 := bar_index - 1` aligns with `shapeOff = -1` so the visual breakout bar is blocked, but the very next chart bar is eligible. Proximity (retestPct, configurable) does the filtering.

**Problem 2:** `log.info()` is permanent in Pine Script — not rolled back on real-time ticks like `var` variables. Every `log.info()` call fired 50-100+ times per signal on real-time bars (one per tick).

**Fix:** Added `barstate.isconfirmed` guard to all 7 `log.info()` calls (1 in `dbAppend()`, 6 CONF state transition logs). Now logs fire once per confirmed bar.

---

### 12. Fix: ORB L/H reversal on first bar — trivially true

**Problem:** The first 5m bar defines ORB H/L, then the reversal helper checks if the bar's wick enters the ORB zone and closes on the other side. Since the bar's own high/low ARE ORB H/L, `sigL <= orbLBody` and `sigH >= orbHBody` are trivially true. A ~ ORB L bull reversal fires on virtually every opening bar — it's noise, not a real rejection signal.

**Fix:** Skip ORB reversal evaluation on the bar that defines the ORB (`na(orbHigh[1])` or similar guard).

---

### 13. Fix: Chart-TF retest can contradict 5m reclaim — think later

**Problem:** A 1m retest can confirm at 10:00 (◆ ORB H — wick touches level, close holds), but then the full 5m bar (10:00-10:04) closes below the level and fires a reclaim (~~ ORB H). The retest was premature — it confirmed on a single 1m candle that didn't hold through the 5m bar.

**Ideas:**
- Only allow retests on signal-TF bar boundaries (when `newSigBar` fires)?
- Require the retest to survive until the next signal-TF close before confirming?
- Retroactively remove/gray the retest label if the same 5m bar invalidates?

---

### 8. Backtest Strategy Version (LOW-MEDIUM impact)

**Problem:** No way to validate if breakout signals actually produce profitable trades.

**Implementation approach:**
- Create `KeyLevelBreakout_Backtest.pine` as `strategy()` version
- Define TP/SL rules (e.g., TP = 1x ATR from entry, SL = 0.5x ATR)
- Use `strategy.entry` / `strategy.exit` on breakout signals
- Compare results with/without the new filters (volume, ATR buffer, VWAP)

---

## Implementation Notes

### Impact Analysis
| File | Changes |
|------|---------|
| `KeyLevelBreakout.pine` | Inputs section, signal TF data section, `bullBreak`/`bearBreak` helpers |
| `KeyLevelScanner.pine` | Same filters, but volume comes from per-symbol `request.security` calls; ATR needs per-symbol fetch too |
| `EMAPullback.pine` | No impact |
| `EMAPullback_Backtest.pine` | No impact |
| `Fib15mScalper.pine` | No impact |

### Key Constraints
- **request.security limit:** Pine Script allows max 40 `request.security` calls. KeyLevelScanner.pine already uses 24 (3 per symbol × 8). Adding volume + ATR per symbol could hit the limit. **Solution:** bundle volume into the existing current-TF tuple (line 124: already fetches `[high, low, close, open, close[1]]` — add `volume` to make it 6 values). ATR can be computed from the fetched OHLC data using `ta.atr` on the signal TF — no extra `request.security` needed.
- **All filters should be toggleable** via `input.bool` with sensible defaults (volume ON, ATR ON, VWAP OFF).
- **Existing behavior must be unchanged** when all filters are toggled off.
- **KeyLevelBreakout.pine refactoring note:** Previous session identified that the 8 boolean flags + 8 signal variables could be refactored into arrays (like Scanner already does). Consider doing this cleanup alongside the improvements.

### Testing Checklist
- [ ] With all filters OFF → signals identical to current version
- [ ] Volume filter ON → fewer signals, only on above-average volume bars
- [ ] ATR buffer ON → no more "1-tick" breakouts, clean breaks only
- [ ] VWAP filter ON → bull signals only above VWAP, bear only below
- [ ] "Once Per Breakout" re-arm logic still works with filters
- [ ] KeyLevelScanner shows consistent signals with KeyLevelBreakout
- [ ] No `request.security` limit errors in Scanner (max 40)
- [ ] Confluence labels display correctly when levels overlap
- [ ] All alert() and alertcondition() calls still fire correctly
- [ ] Visual labels don't overlap / remain readable

### Suggested Implementation Order
1. Add Tier 1 filters (volume, ATR, VWAP) to `KeyLevelBreakout.pine` first
2. Test thoroughly on a single chart
3. Port the same filters to `KeyLevelScanner.pine` (watch `request.security` budget)
4. Once stable, proceed to Tier 2 features one at a time

---

## v2.4 Improvement Proposals (from 6-week analysis, Feb 28 2026)

**Evidence base:** 3,753 signals, 13 symbols, Jan 20 - Feb 27 (~24 trading days). 525 signals with candle follow-through data. Full analysis in `debug/master-summary.md`.

### Problems Identified

| # | Problem | Evidence | Severity |
|---|---------|----------|----------|
| P1 | **CONF ✓ visually invisible** — CONF ✗ changes label to gray, but CONF ✓ only appends "✓" text with no color change. The gold standard signal (53% GOOD, 0% BAD) looks identical to an unconfirmed breakout. | Lines 749/864: `label.set_text()` only. Lines 912-915: CONF ✗ sets gray + small. Asymmetry. | HIGH |
| P2 | **Afternoon noise** — Signals after 11:00 have 0-6.9% GOOD rate but get equal visual weight as morning signals (31.3% GOOD). | 116 signals in 11:00-16:00 window: 6.9% GOOD overall, 0% in 11-13 dead zone. | HIGH |
| P3 | **Reclaims get equal weight** — `~~` signals score 8.1% GOOD vs 33.5% for reversals `~`, yet look the same (aqua/orange). | 62 reclaims measured: 8.1% GOOD, 8.1% BAD. Weakest signal type by far. | MEDIUM |
| P4 | **Volume encoding too subtle** — Alpha transparency range is 0-35 (lines 307-308: `35 - volRatioBull * 10`). At 3.5x volume the label is already fully opaque. The 5x-10x "conviction zone" is invisible. | Volume ≥10x has 59.6% CONF rate vs 32.2% for <2x — huge signal, zero visual difference above 3.5x. | MEDIUM |
| P5 | **No day health indicator** — Chop days (18% of sample) identifiable by early CONF failures, but no visual warning exists. | Chop day early CONF rate: 27.6% vs Mixed: 51.1%. Detectable by bar 3-4 of day. | MEDIUM |
| P6 | **Window expiry is dead code** — Lines 945-950 (bull) and 990-995 (bear) promote CONF to ✓ when signal doesn't retrace within `retestMaxElapsed` bars. Default "Session" = 99999 bars. **Fires zero times in 6 weeks.** | 0 out of 3,753 signals used this path. All 352 passes were auto-promotes. | LOW |
| P7 | **Logging gaps** — No VWAP position in log output (cannot validate Fix 3). No cascade/auto-promote info logged. | Rule 8 (VWAP filter) marked UNVALIDATABLE due to missing data. | LOW |

### Proposed Changes (Tiered by Impact × Simplicity)

#### Tier A: CONF ✓ Visual Boost (1-2 lines, HIGH impact) ✅ IMPLEMENTED v2.4

**What:** When CONF passes (auto-promote), change the label color to a distinct "confirmed" color (e.g., bright green border, or prepend a ✅ emoji).

**Why:** CONF ✓ signals are 53.3% GOOD with 0% BAD — the gold standard. Currently invisible among all breakouts.

**Code location:** Lines 749 (bull) and 864 (bear) — add `label.set_color()` or `label.set_textcolor()` after the existing `label.set_text()`.

**Risk:** NONE — display only.

---

#### Tier B: Add VWAP to Log Output (~2 lines, LOW risk) ✅ IMPLEMENTED v2.4

**What:** Add `vwap=above/below` to `log.info()` messages so we can validate the VWAP filter against historical data.

**Why:** Fix 3 (VWAP filter ON) cannot be validated without this. Rule 8 is currently UNVALIDATABLE.

**Code location:** `dbAppend()` function or the log.info() calls — add `ta.vwap(close)` comparison.

**Risk:** NONE — logging only.

---

#### Tier C: Afternoon Visual Dimming (~5 lines, LOW risk) ✅ IMPLEMENTED v2.4

**What:** Reduce label opacity/size for signals firing after 11:00 ET. Already partially implemented via cooldown dimming — extend concept to time-based dimming.

**Why:** 11:00-13:00 = 0% GOOD rate. 13:00-16:00 = 6.9% GOOD. These signals are noise for most traders.

**Code location:** Label creation blocks (lines ~683-731 for bull, mirror for bear). Add time check alongside existing cooldown logic.

**Risk:** LOW — may hide rare but valid afternoon breakouts (15:00 CONF rate = 42.9%, but tiny sample).

**Recommendation:** Make it toggleable with default ON. Don't suppress — just dim (smaller size, lighter color).

---

#### Tier D: Day Health Counter / Chop Warning (~15 lines, MEDIUM risk) ✅ IMPLEMENTED v2.4

**What:** Track consecutive CONF failures from session open. After 2-3 consecutive ✗, show a "CHOP?" table cell or label. Reset at session open.

**Why:** Chop days (18% of sample) have 27.6% early CONF rate vs 51.1% for mixed days. Detectable early.

**Code location:** New `var int confFailStreak = 0` counter, reset on `session.isfirstbar`. Display in debug table or as standalone label.

**Risk:** MEDIUM — chop detection is probabilistic (not guaranteed). Over-reliance could cause missing mixed-day opportunities.

**Recommendation:** Display-only warning, not a filter. Let trader decide.

---

#### Tier E: High-Conviction Visual Tier (~10 lines, LOW risk) ✅ IMPLEMENTED v2.4

**What:** Visually distinguish signals that meet ALL of: CONF Pass + >5x volume + extreme position (≥80%). These are the "54.1% GOOD, 0% BAD" gold standard.

**Why:** Only 37 signals in 6 weeks met all criteria — rare but extremely reliable. Currently look the same as any other breakout.

**Code location:** After CONF pass (lines 749/864), check volume ratio and position. If all pass, upgrade label style (larger, brighter, border).

**Risk:** LOW — visual enhancement only. But combines with Tier A (CONF ✓ boost), so implement A first.

---

#### Tier F: Widen Volume Alpha Range (1 line, LOW risk) ✅ IMPLEMENTED v2.4

**What:** Change alpha formula from `35 - volRatioBull * 10` to `70 - volRatioBull * 10` (or similar). Makes low-volume signals significantly more transparent while preserving high-volume labels.

**Why:** Current range saturates at 3.5x volume. The 5x-10x zone (where CONF rate jumps from 40% to 60%) has no visual differentiation.

**Code location:** Lines 307-308.

**Risk:** LOW — may make some labels too transparent. Test visually before committing.

---

#### Tier G: Dead Code Cleanup (~10 lines removed, ZERO risk) ✅ IMPLEMENTED v2.4

**What:** Remove or simplify the window expiry promotion path (lines 945-950 bull, 990-995 bear).

**Why:** Fires zero times in 6 weeks. Default "Session" = 99999 bars means this code path literally never executes. All CONF passes are auto-promotes.

**Risk:** ZERO — removing code that never runs. But keep the `retestMaxElapsed` input for retest tracking (which does use it).

**Recommendation:** Comment out or remove, with a note explaining why (auto-promote handles all cases).

---

### NOT Recommended (Over-Optimization Risk)

| Proposal | Why NOT |
|----------|---------|
| Raise volume minimum above 2x | Would lose too many valid signals. Current 2x is well-calibrated. |
| Suppress afternoon signals entirely | Rare but some run well (15:00 CONF = 42.9%). Dim, don't suppress. |
| Symbol-specific tuning | Spread too narrow (30-51% CONF) to justify per-symbol rules. |
| Change CONF timeout | Auto-promote mechanism works perfectly (100% of passes). |
| Position filter as hard gate | pos≥80 gives +9.9pp lift but may be over-fitting to sample. |

### Signal Quality Ranking (for reference)

| Rank | Setup | GOOD% | BAD% | n | Action |
|------|-------|-------|------|---|--------|
| 1 | BRK + CONF ✓ + >5x vol | 54.1% | 0.0% | 37 | Trade with full size |
| 2 | CONF ✓ (any) | 53.3% | 0.0% | 75 | Trade with confidence |
| 3 | Week L/H level | 33.3-38.5% | 3.3% | 30 | Selective, high conviction |
| 4 | Reversals (~) | 33.5% | 13.2% | 167 | Manage risk actively |
| 5 | Morning BRK (9:30-10:00) | 31.3% | 13.8% | 319 | Best window, both directions |
| 6 | Afternoon (13:00-16:00) | 9.8% | 0.0% | 116 | Skip unless extraordinary |
| 7 | Reclaims (~~) | 8.1% | 8.1% | 62 | Weakest — proceed with caution |

### Implementation Priority

1. ~~**Tier A + B** — CONF ✓ boost + VWAP logging~~ ✅ Done in v2.4
2. ~~**Tier C** — Afternoon dimming~~ ✅ Done in v2.4
3. ~~**Tier D** — Chop warning~~ ✅ Done in v2.4
4. ~~**Tier E + F** — High-conviction tier + volume alpha~~ ✅ Done in v2.4
5. ~~**Tier G** — Dead code cleanup~~ ✅ Done in v2.4
6. **Evidence Stack Filters** — ✅ Done in v2.5 (EMA, RS, ADX, Candle Body)
7. **Runner Score + VWAP line + SL lines + VWAP exit alert** — ✅ Done in v2.6
8. **Big-Move Fingerprint Integration** — ✅ Done in v2.8 (vol ramp, QBS/MC signals, ⚡ big-move flag, ⚠ body warning, moderate dim, Runner Score tuned)

---

## Multi-Symbol Fingerprint Analysis (March 2026)

**Evidence base:** 1,841 signals across 13 symbols (AAPL, AMD, AMZN, GLD, GOOGL, META, MSFT, NVDA, QQQ, SLV, SPY, TSLA, TSM). 231 CONF ✓/✓★, 809 CONF ✗, 777 reversals. Period: Jan 20 – Mar 2, 2026. Indicators (ADX, EMA, Body%, RS, VWAP) computed from 5m IB cache data. MFE/MAE measured from 5s candles over 60 minutes.

**Data files:** `debug/enriched-signals.csv` (1841 rows, 22 columns — pre-computed, ready for future analysis), `debug/multi-symbol-fingerprint.md` (full report), `debug/multi_symbol_fingerprint.py` (script).

### Strongest Differentiators: Good vs Bad Breakouts

| Rank | Metric | GOOD (n=231) | BAD (n=809) | Gap | Actionable? |
|------|--------|-------------|------------|-----|-------------|
| 1 | **LOW levels** (PM L, Yest L, ORB L, Week L) | 65% | 49% | **+17%** | Yes — Runner Score already gives bear +1 for LOW level |
| 2 | **Bear direction** | 65% | 49% | **+17%** | Correlated with #1, inherent property |
| 3 | **EMA aligned** (close on right side of 5m EMA20+EMA50) | 90% | 78% | **+13%** | Yes — v2.5 EMA filter **validated**, keep ON |
| 4 | **Vol ≥ 5x** | 39% | 33% | **+6%** | Yes — vol factor in Runner Score |
| 5 | Vol 2-5x | 38% | 43% | **-5%** | Mid-range vol slightly worse; 10x+ is better |
| 6 | ADX ≥ 25 | 49% | 53% | **-4%** | Counterintuitive — see ADX section below |
| 7 | Multi-level | 16% | 19% | **-3%** | NOT a positive signal (more levels ≠ better) |
| 8 | VWAP aligned | 95% | 93% | **+2%** | Small gap but nearly universal in GOOD trades |

### Filter Validation Results

| Filter (v2.5) | Validated? | Evidence | Recommendation |
|----------------|-----------|----------|----------------|
| **EMA Alignment** | **YES** | 90% vs 78% (+13% gap) — strongest filter | Keep ON, threshold correct |
| **VWAP Direction** | **YES** | 95% vs 93% — small gap but nearly universal | Keep ON for reversals |
| **ADX > 20** | **PARTIAL** | 20-25 has best CONF rate (26%), <20 is worst (22%). But ADX 35-50 only 19% CONF | Threshold 20 is correct — removes weakest bucket |
| **Body ≥ 50%** | **NO** | avg 49% (good) vs 48% (bad) — zero differentiation | **Consider lowering to 30% or removing** |
| **RS vs SPY** | **WEAK** | -0.3% (good) vs 0.0% (bad) — small gap, bear-biased | Keep ON but low impact |

### ADX Barbell Pattern (new finding)

| ADX Range | CONF Rate | Avg MFE (good) | Interpretation |
|-----------|-----------|----------------|----------------|
| <20 | 22% | 0.36 | Low trend — filter removes these ✓ |
| **20-25** | **26%** | 0.28 | **Sweet spot for hit rate** |
| 25-30 | 23% | 0.29 | Solid |
| 30-35 | 21% | 0.39 | Decent, better MFE |
| 35-50 | 19% | 0.32 | Lower hit rate |
| 50+ | 13% | **0.68** | Rare but explosive — few wins, big wins |

**Implication:** ADX > 20 filter is correctly calibrated. Do NOT raise the threshold — 20-25 is the best bucket. High ADX (50+) has low CONF rate but highest MFE, suggesting a "barbell" strategy: the moderate-ADX trades win often, the rare extreme-ADX trades win big.

### CONF Rate by Level Type

| Level | CONF Rate | Avg MFE (good) | Tier |
|-------|-----------|----------------|------|
| **Yest L** | **30%** | **0.41** | A — Best overall |
| **PM L** | **27%** | 0.35 | A |
| **ORB L** | **27%** | 0.32 | A |
| Week L | 22% | 0.28 | B |
| Week H | 20% | 0.29 | B |
| PM H | 18% | 0.36 | C |
| Yest H | 15% | 0.33 | C |
| **ORB H** | **14%** | 0.33 | C — Worst |

**Implication:** LOW levels (PM L, Yest L, ORB L) have ~2x the CONF rate of HIGH levels (PM H, Yest H, ORB H). The Runner Score already accounts for this with the asymmetric level quality factor (bear gets +1 for LOW level). Consider whether HIGH-level breakouts deserve a visual penalty (dimming?).

### Volume — 10x+ Is King

| Volume | CONF Rate | Avg MFE (good) |
|--------|-----------|----------------|
| <2x | 21% | 0.22 |
| 2-5x | 20% | 0.30 |
| 5-10x | 20% | 0.34 |
| **10x+** | **32%** | **0.50** |

**Correction:** v2.4 finding that "2-5x is the sweet spot" was TSLA-specific. Across all 13 symbols, 10x+ volume has both the highest CONF rate (32%) and the best MFE (0.50 ATR). The relationship is monotonic: more volume = better. Runner Score currently gives +1 for 2-5x — consider revising to +1 for ≥5x or ≥10x.

### Symbol Tiers (by CONF Rate)

| Tier | Symbols | CONF Rate | Best MFE |
|------|---------|-----------|----------|
| **A** | GOOGL (35%), TSLA (32%), QQQ (28%) | 28-35% | QQQ 0.47, NVDA 0.45 |
| **B** | SPY (24%), NVDA (23%), AMZN (23%), SLV (22%) | 22-24% | SPY 0.39, NVDA 0.45 |
| **C** | META (21%), AMD (20%), MSFT (20%), TSM (19%) | 19-21% | AMD 0.39 |
| **D** | AAPL (13%), GLD (6%) | 6-13% | AAPL 0.39 |

**Note:** NVDA appears in B-tier by CONF rate but has the 2nd-best MFE (0.45) — it's a "when it works, it works big" symbol. GLD is an outlier at 6% CONF rate — consider excluding from breakout signals or flagging as low-probability.

### Time of Day — MFE Tells a Different Story

| Time | CONF Rate | Avg MFE (good) |
|------|-----------|----------------|
| 9:30-10:00 | 22% | **0.42** |
| 10:00-11:00 | 22% | 0.31 |
| 11:00-12:00 | 28% | 0.38 |
| 12:00+ | 22% | 0.15 |

CONF rate is flat across time buckets (22%), but MFE drops sharply after 12:00 (0.15 vs 0.42 for 9:30-10:00). The 11:00-12:00 bucket has the highest CONF rate (28%) but small sample. Afternoon dimming after 11:00 is validated — CONF may pass but follow-through is poor.

### Actionable Recommendations

| # | Change | Impact | Risk | Priority |
|---|--------|--------|------|----------|
| R1 | ~~**Lower or remove Body% filter**~~ | ✅ **IMPLEMENTED v2.7** — lowered 50%→30%, closeLoc 60%→40% | LOW | ~~HIGH~~ |
| R2 | ~~**Revise Runner Score vol factor**~~ | ✅ **IMPLEMENTED v2.7** — changed 2-5x→≥5x | LOW | ~~MEDIUM~~ |
| R3 | **Consider HIGH-level dimming**: ORB H (14% CONF) vs Yest L (30%) | Reduces noise from weak HIGH-level signals | MEDIUM | MEDIUM |
| R4 | **GLD special handling**: 6% CONF rate is extreme outlier | Could exclude or require extra filter | LOW | LOW |
| R5 | Keep EMA filter ON, ADX > 20 ON, VWAP ON | All validated — especially EMA (+13% gap) | ZERO | DONE |

### Corrections to Previous Findings

| Previous Finding | Correction | Source |
|-----------------|------------|--------|
| "2-5x volume is the sweet spot" (v2.4) | **WRONG across all symbols.** 10x+ has 32% CONF and 0.50 MFE. 2-5x = 20% CONF. | Multi-symbol fingerprint (n=1841) |
| "ADX 38 is better than 33" (TSLA-only) | **TSLA-specific.** Multi-symbol avg ADX is 26 (good) vs 27 (bad). 20-25 has best CONF rate. | Multi-symbol fingerprint |
| "Body% matters" (TSLA 77% vs 76%) | **Noise.** Multi-symbol: 49% vs 48%, zero differentiation. | Multi-symbol fingerprint |
| "10:00-11:00 is the best window" (v2.4) | **PARTIALLY confirmed.** CONF rate is flat (22%), but 9:30-10:00 has best MFE (0.42). 12:00+ MFE drops to 0.15. | Multi-symbol fingerprint |

---

## Big Move Fingerprint Analysis (March 2026)

**Evidence base:** 9,596 significant 5m bars across 13 symbols (body≥60%, range≥0.12 ATR). Period: Jan 20 – Mar 2, 2026. For each bar: ADX, EMA9/20/50, VWAP distance, volume ratio, body%, direction, time. MFE/MAE measured from 5s candle data. 5-minute checkpoint P&L computed.

**Classification:** Runners (MFE>0.3 ATR): 8,098 (84%) | Fakeouts (MFE<0.1, MAE<-0.15): 268 (3%) | Middle: 1,230

**Data files:** `debug/big-moves.csv` (9596 rows), `debug/big-move-fingerprint.md` (full report), `debug/big_move_fingerprint.py` (script).

### Top Differentiators: Runner vs Fakeout

| Rank | Metric | Runners | Fakeouts | Gap | Direction |
|------|--------|---------|----------|-----|-----------|
| 1 | **5min P&L positive** | 50% | 16% | **+34%** | Runners higher — strongest predictor |
| 2 | **5min P&L > 0.05 ATR** | 31% | 2% | **+30%** | Runners higher — near-perfect filter |
| 3 | **Body ≥ 80%** | 36% | 55% | **-19%** | **FAKEOUTS higher — body is INVERSE!** |
| 4 | **Before 11:00** | 24% | 16% | **+8%** | Runners higher — morning edge |
| 5 | **Bear direction** | 51% | 44% | **+7%** | Runners higher — bear edge persists |
| 6 | **Vol ≥ 2x** | 8% | 15% | **-7%** | **FAKEOUTS higher — high vol = exhaustion** |
| 7 | **ADX ≥ 30** | 33% | 29% | **+4%** | Runners slightly higher |

### Key Finding 1: Body ≥ 80% is a FAKEOUT Indicator

55% of fakeouts have body ≥80%, vs only 36% of runners. **Very clean candles with no wick at the extreme of a move signal exhaustion/capitulation, not conviction.** This confirms the multi-symbol signal finding (49% good vs 48% bad for body%) from a completely independent angle.

**Action:** Lower body filter from ≥50% to ≥30% or remove entirely. It actively suppresses valid signals.

### Key Finding 2: VWAP Proximity = Best Follow-Through

| VWAP Distance (ATR) | n | Runner% | Avg MFE | Interpretation |
|---------------------|---|---------|---------|----------------|
| At VWAP (±0.1 ATR) | 412 | **89%** | **1.98** | **Best zone — inflection point** |
| Near VWAP (0.1-0.3) | 565 | 87% | 1.45 | Good |
| Extended (>0.3) | 8,619 | 84% | 1.45 | Average |

Moves originating right at VWAP have 89% runner rate and **1.98 ATR MFE** — 37% better than extended moves. This directly validates the "VWAP as signal level" proposal from the TSLA 2/26 analysis. The VWAP acts as an inflection point: breaks AT VWAP have the best follow-through.

**Action:** Implement VWAP rejection/break as a signal type (highest-priority "level desert" fix).

### Key Finding 3: 5-Minute Gate is Universal

| 5min P&L bucket | n | Runner% | Fakeout% | Avg MFE |
|-----------------|---|---------|----------|---------|
| < -0.05 ATR | 2,556 | 81% | 5% | 1.38 |
| -0.05 to 0 | 1,646 | 86% | 3% | 1.42 |
| 0 to +0.05 | 2,628 | 78% | 3% | 1.32 |
| **+0.05 to +0.15** | 1,870 | **91%** | **0%** | 1.62 |
| **> +0.15** | 896 | **98%** | **0%** | 1.98 |

Not just for key-level signals — across ALL 9,596 significant bars: if the move is >+0.05 ATR after 5 minutes, fakeout rate drops to 0%. Combined with EMA + VWAP alignment → **93% runner rate, 0% fakeout** (n=1,411).

**Action:** The 5-minute gate should inform runner management. Consider a post-signal checkpoint indicator or alert.

### Key Finding 4: High Volume = More Fakeouts (for general big moves)

Vol ≥ 2x bars are 15% of fakeouts but only 8% of runners. For **general big moves** (not key-level signals), high volume relative to the 20-bar average signals exhaustion — the volume spike comes AT the end of a move, not the beginning.

**Note:** This does NOT contradict the key-level signal finding (10x+ volume = 32% CONF). At key levels, volume confirms institutional participation in the breakout. Away from key levels, volume spikes signal capitulation. Context matters.

### Key Finding 5: Time & Fakeout Patterns

| Time | Runner% | MFE | Key Pattern |
|------|---------|-----|-------------|
| **9:30-10:00** | **92%** | **2.35** | Best window by far |
| 10:00-11:00 | 84% | 1.44 | Solid |
| 11:00-12:00 | 85% | 1.27 | Decent |
| 12:00+ | 84% | 1.42 | OK runner%, but **11 of top 20 fakeouts are 15:00-15:50** |

Morning (9:30-10:00) big moves have 92% runner rate. Top fakeouts cluster in the last hour (15:00-15:50) — end-of-day reversals.

### Best Filter Stacking Combos

| Stack | n | Runner% | Fakeout% | MFE |
|-------|---|---------|----------|-----|
| **5min >0.05 + EMA + VWAP** | 1,411 | **93%** | **0%** | 1.75 |
| EMA + VWAP + bear + ADX≥20 + before 11 | 523 | 86% | 2% | 1.82 |
| EMA + VWAP + before 11 | 1,324 | 86% | 2% | 1.78 |
| EMA + VWAP + ADX≥20 + vol≥2x | 370 | 85% | 4% | 2.04 |

### Combined Actionable Recommendations (from both analyses)

| # | Change | Source | Impact | Priority |
|---|--------|--------|--------|----------|
| R1 | ~~**Lower/remove Body% filter**~~ | ✅ **IMPLEMENTED v2.7** — 50%→30% | ~~**HIGH**~~ |
| R2 | ~~**VWAP as signal level**~~ | ✅ **IMPLEMENTED v2.7** — VWAP zone ±0.1 ATR, 9th level type | ~~**HIGH**~~ |
| R3 | ~~**5-minute gate checkpoint**~~ | ✅ **IMPLEMENTED v2.7** — label update + alert after CONF | ~~**HIGH**~~ |
| R4 | ~~**Revise Runner Score vol factor**~~ | ✅ **IMPLEMENTED v2.7** (≥5x) + v2.8 tuned time 9:30-10, +TSM D-tier | ~~MEDIUM~~ |
| R5 | **HIGH-level dimming** | Signal analysis | ORB H 14% vs Yest L 30% CONF | MEDIUM |
| R6 | **GLD special handling** | Signal analysis | 6% CONF rate is extreme outlier | LOW |

### The Three Pillars of Trade Quality

From all analyses combined, trade quality depends on:

1. **Direction + Level** — bear breakout at LOW level (Yest L, PM L, ORB L) = ~2x CONF rate vs HIGH levels
2. **Location** — near VWAP (±0.1 ATR), not extended = best follow-through (1.98 vs 1.42 MFE)
3. **Momentum confirmation** — positive at 5 minutes + EMA aligned = 93% runner, 0% fakeout

What traditional TA emphasizes (body%, high volume at signal bar) is either noise or inverted for predicting follow-through.

---

### Multi-Symbol Big-Move Fingerprint (2x 5m-ATR, March 2026)

**Data:** 2,069 moves across 13 symbols, Dec 2025 – Mar 2026. Threshold: 5m bar range ≥ 2x ATR(14).
**Overall: 65% runner rate, 5% fakeout rate.** ~3 moves/day/symbol.

#### What GENERALIZES (validated across all/most symbols):

| # | Finding | Evidence | Symbols validated |
|---|---------|----------|-------------------|
| 1 | **5-min P&L positive = THE universal predictor** | Runners 60-67% positive at 5min, fakeouts 0% — every symbol | 12/12 (all with 5s data) |
| 2 | **Morning 9:30-10 = best time** | 70% runner rate vs 49% afternoon (+21% gap) | 11/13 (not GLD, SLV) |
| 3 | **Body% is INVERSE** | High body (63.5%) = MORE fakeouts vs runners (55.9%) = -7.6 gap | Universal |
| 4 | **Pre-vol ramp: U-shaped** | Drying (<0.5x) = 68% runner; Explosive (>5x) = 64% + best MFE 2.66; Moderate (1-2x) = worst 56% | Universal pattern |

#### What DOESN'T generalize (TSLA-specific or inconsistent):

| # | Finding | Reality | Action |
|---|---------|---------|--------|
| 5 | ~~ADX differentiates~~ | Only +1.9 gap multi-symbol. GLD/SLV inverse. | Keep ADX>20 filter (blocks worst), but don't weight in Runner Score |
| 6 | ~~Gap Down = more runners~~ | Only AMD/AMZN/QQQ/TSLA/TSM. GLD is -29% inverse! | Symbol-specific, not generalizable |
| 7 | ~~EMA/VWAP aligned~~ | -4% gap (slightly inverse at 2x ATR level) | Noise at big-move threshold — don't use for big-move filtering |
| 8 | ~~Pre-vol ramp = monotonic~~ | It's U-shaped: drying AND explosive both good, moderate worst | Revise assumption |

#### Symbol Tiers (2x ATR runner rate):

| Tier | Symbols | Runner% range |
|------|---------|---------------|
| A | QQQ (72%), META (71%), GOOGL (70%), AMD (69%), AMZN (69%) | 69-72% |
| B | MSFT (68%), SPY (67%), TSLA (66%), AAPL (63%), NVDA (63%) | 63-68% |
| C | GLD (61%), SLV (57%) | 57-61% |
| D | TSM (38%) | <40% — outlier |

#### Key Insight: The "Quiet Before Storm" Pattern
Pre-move volume DRYING (<0.5x ramp) + big 2x ATR bar = 68% runner, only 3% fakeout.
This is the classic consolidation-then-explosion setup. The big bar IS the breakout from the quiet.
Conversely, explosive pre-ramp (>5x) = slightly fewer runners (64%) but best MFE (2.66 ATR) when it works.
Moderate ramping (1-2x) = worst bucket: 56% runner, 7% fakeout. Already distributed.

**Data files:** `debug/multisym-bigmove-data.csv` (2069 rows), `debug/multisym-bigmove-fingerprint.md`, `debug/tsla-bigmove-data.csv` (6761 rows)
