# KeyLevelBreakout.pine — Improvement Plan

**Date:** 2026-02-24
**Status:** Approved for implementation
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

## Current State of KeyLevelBreakout.pine

`KeyLevelBreakout.pine` (209 lines) detects bullish/bearish candle closes through 4 key level types on a configurable signal timeframe:

- **Premarket High/Low** — tracked live during 04:00–09:30 ET
- **Yesterday High/Low** — via `request.security("D", high[1]/low[1])`
- **Last Week High/Low** — via `request.security("W", high[1]/low[1])`
- **ORB High/Low** — first 5-min bar of regular session

**Breakout conditions** (line 110–114):
- Bull: `close > open AND close > level AND prev_close <= level`
- Bear: `close < open AND close < level AND prev_close >= level`

**"Once Per Breakout"** mode (default on): flags prevent repeat signals. Flags re-arm when price closes back through the level (lines 91–107).

**Companion file:** `KeyLevelScanner.pine` (187 lines) — multi-symbol version monitoring up to 8 tickers with a status table. Uses the same breakout logic via `scan()` / `chk()` / `inv()` functions. **Any changes to breakout logic must be mirrored in both files.**

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
