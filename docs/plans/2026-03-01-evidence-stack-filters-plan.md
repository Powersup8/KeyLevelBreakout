# Evidence Stack Filters (v2.5) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add 4 toggleable filters (5m EMA alignment, RS vs SPY, ADX trend strength, candle body quality) to KeyLevelBreakout.pine that reduce BAD signals by ~40% while maintaining GOOD follow-through rate.

**Architecture:** All filters are computed after the signal-TF data is loaded but before signal generation. Each filter produces a per-direction boolean (bull/bear). In Suppress mode, failing signals are not generated. In Dim mode, they appear as gray labels with `?` suffix. Three new `request.security()` calls fetch 5m EMA/ADX data and SPY data. Total security calls increase from 5 to 8 (of 40 max).

**Tech Stack:** Pine Script v6, TradingView indicator

**Reference:** Design doc at `docs/plans/2026-03-01-evidence-stack-filters-design.md`

---

### Task 1: Add Filter Input Controls

**Files:**
- Modify: `KeyLevelBreakout.pine:43-44` (after VWAP filter input, in "Filters" group)

**Step 1: Add the 5 new inputs after the VWAP filter input (line 43)**

Insert after `i_vwapFilter` (line 43), before `i_useZones` (line 45):

```pine
i_fEMA    = input.bool(true, "5m EMA Alignment Filter",     tooltip="Suppress signals against the 5m EMA(20)/EMA(50) trend", group="Filters")
i_fRS     = input.bool(true, "RS vs SPY Filter",            tooltip="Suppress long signals underperforming SPY (and vice versa)", group="Filters")
i_fADX    = input.bool(true, "ADX Trend Strength Filter",   tooltip="Suppress signals when 5m ADX < 20 (chop/no trend)", group="Filters")
i_fCandle = input.bool(true, "Candle Body Quality Filter",  tooltip="Suppress wick-heavy breakout candles (body < 50% or close in wrong zone)", group="Filters")
i_fMode   = input.string("Suppress", "Filter Mode", options=["Suppress", "Dim"], tooltip="Suppress: hide signals entirely. Dim: show as gray with ? suffix", group="Filters")
```

**Step 2: Verify the indicator compiles**

Open TradingView, load the indicator. Check that 5 new inputs appear in the "Filters" group in Settings.

**Step 3: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "feat(v2.5): add evidence stack filter input controls"
```

---

### Task 2: Add request.security() Calls for Filter Data

**Files:**
- Modify: `KeyLevelBreakout.pine:84-85` (daily OHLC tuple — add `todayOpen`)
- Modify: `KeyLevelBreakout.pine` after line 93 (add 3 new security calls)

**Step 1: Add `todayOpen` to the existing daily security call**

The current code at line 84-85:
```pine
[yestHigh, yestLow, yestOpen, yestClose] = request.security(syminfo.tickerid, "D",
     [high[1], low[1], open[1], close[1]], lookahead = barmerge.lookahead_on)
```

Change to (add `todayOpen` — today's `open` without `[1]` is non-repainting with lookahead):
```pine
[yestHigh, yestLow, yestOpen, yestClose, todayOpen] = request.security(syminfo.tickerid, "D",
     [high[1], low[1], open[1], close[1], open], lookahead = barmerge.lookahead_on)
```

**Step 2: Add a helper function for 5m ADX extraction**

Insert just before the existing daily security calls (before line 83, after the PM high/low computation):

```pine
// ─── Filter Helpers ──────────────────────────────────────
// ADX extraction for request.security (ta.dmi returns tuple)
f_adx() =>
    [_, _, adx] = ta.dmi(14, 14)
    adx
```

**Step 3: Add 3 new security calls after line 93 (after `dailyVolSma`)**

Insert after `dailyVolSma` line:

```pine
// ─── Evidence Stack Filter Data (v2.5) ───────────────────
// 5m EMA(20), EMA(50), ADX — single call, non-repainting
[ema20_5m, ema50_5m, adx_5m] = request.security(syminfo.tickerid, "5",
     [ta.ema(close, 20)[1], ta.ema(close, 50)[1], f_adx()[1]], lookahead = barmerge.lookahead_on)
// SPY intraday data for relative strength
spyClose   = request.security("SPY", i_signalTF, close[1], lookahead = barmerge.lookahead_on)
spyDayOpen = request.security("SPY", "D", open, lookahead = barmerge.lookahead_on)
```

**Step 4: Verify the indicator compiles**

Open TradingView, reload. No visible change expected — data is fetched but not used yet. Check for compilation errors in the Pine editor.

**Step 5: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "feat(v2.5): add security calls for EMA, ADX, and SPY RS data"
```

---

### Task 3: Compute Filter Boolean Flags

**Files:**
- Modify: `KeyLevelBreakout.pine` after line 309 (after `rearmBuf` computation, in Filter Computations section)

**Step 1: Add filter flag computations**

Insert after `rearmBuf = ...` (line 309), before `retestBuf` (line 310):

```pine
// ─── Evidence Stack Filter Flags (v2.5) ──────────────────
// Filter 1: 5m EMA alignment (trend direction)
fEMA_bull = ema20_5m > ema50_5m
fEMA_bear = ema20_5m < ema50_5m

// Filter 2: Intraday RS vs SPY
// SPY/QQQ/GLD/SLV: skip RS filter (always pass)
bool rsSkip = syminfo.ticker == "SPY" or syminfo.ticker == "QQQ" or syminfo.ticker == "GLD" or syminfo.ticker == "SLV"
stockChg = not na(todayOpen) and todayOpen > 0 ? (sigC - todayOpen) / todayOpen : 0.0
spyChg   = not na(spyDayOpen) and spyDayOpen > 0 ? (spyClose - spyDayOpen) / spyDayOpen : 0.0
rsVsSpy  = stockChg - spyChg
fRS_bull = rsSkip or rsVsSpy > 0
fRS_bear = rsSkip or rsVsSpy < 0

// Filter 3: ADX trend strength (5m)
fADX = not na(adx_5m) ? adx_5m > 20 : true

// Filter 4: Candle body quality
candleRange = sigH - sigL
bodyRatio   = candleRange > 0 ? math.abs(sigC - sigO) / candleRange : 0.0
closeLoc_bull = candleRange > 0 ? (sigC - sigL) / candleRange : 0.0
closeLoc_bear = candleRange > 0 ? (sigH - sigC) / candleRange : 0.0
fCandle_bull = bodyRatio > 0.5 and closeLoc_bull > 0.6
fCandle_bear = bodyRatio > 0.5 and closeLoc_bear > 0.6

// Combined evidence stack pass (per direction)
evStackBull = (not i_fEMA or fEMA_bull) and (not i_fRS or fRS_bull) and (not i_fADX or fADX) and (not i_fCandle or fCandle_bull)
evStackBear = (not i_fEMA or fEMA_bear) and (not i_fRS or fRS_bear) and (not i_fADX or fADX) and (not i_fCandle or fCandle_bear)

// Suppress gate: blocks signal generation entirely when filter fails
fGateBull = i_fMode == "Suppress" ? evStackBull : true
fGateBear = i_fMode == "Suppress" ? evStackBear : true
```

**Step 2: Verify the indicator compiles**

Reload in TradingView. No visible change yet — flags are computed but not applied.

**Step 3: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "feat(v2.5): compute evidence stack filter flags with SPY/ETF bypass"
```

---

### Task 4: Apply Filters to Signal Generation

**Files:**
- Modify: `KeyLevelBreakout.pine:504-511` (filtered breakout signals)
- Modify: `KeyLevelBreakout.pine:544-552` (filtered reversal signals)

**Step 1: Add filter gate to breakout signals**

Current breakout filter lines (504-511):
```pine
sigBullPMH = rBullPMH and (not i_firstOnly or not xPMH)
sigBearPML = rBearPML and (not i_firstOnly or not xPML)
sigBullYH  = rBullYH  and (not i_firstOnly or not xYH)
sigBearYL  = rBearYL  and (not i_firstOnly or not xYL)
sigBullWH  = rBullWH  and (not i_firstOnly or not xWH)
sigBearWL  = rBearWL  and (not i_firstOnly or not xWL)
sigBullOH  = rBullOH  and (not i_firstOnly or not xOH)
sigBearOL  = rBearOL  and (not i_firstOnly or not xOL)
```

Change to (append `and fGateBull`/`fGateBear`):
```pine
sigBullPMH = rBullPMH and (not i_firstOnly or not xPMH) and fGateBull
sigBearPML = rBearPML and (not i_firstOnly or not xPML) and fGateBear
sigBullYH  = rBullYH  and (not i_firstOnly or not xYH)  and fGateBull
sigBearYL  = rBearYL  and (not i_firstOnly or not xYL)  and fGateBear
sigBullWH  = rBullWH  and (not i_firstOnly or not xWH)  and fGateBull
sigBearWL  = rBearWL  and (not i_firstOnly or not xWL)  and fGateBear
sigBullOH  = rBullOH  and (not i_firstOnly or not xOH)  and fGateBull
sigBearOL  = rBearOL  and (not i_firstOnly or not xOL)  and fGateBear
```

**Step 2: Add filter gate to reversal signals**

Current reversal filter lines (544-552):
```pine
sigRevBullPML = rRevBullPML and (not i_firstOnly or not rPML)
sigRevBullYL  = rRevBullYL  and (not i_firstOnly or not rYL)
sigRevBullWL  = rRevBullWL  and (not i_firstOnly or not rWL)
sigRevBullOL  = rRevBullOL  and (not i_firstOnly or not rOL)

sigRevBearPMH = rRevBearPMH and (not i_firstOnly or not rPMH)
sigRevBearYH  = rRevBearYH  and (not i_firstOnly or not rYH)
sigRevBearWH  = rRevBearWH  and (not i_firstOnly or not rWH)
sigRevBearOH  = rRevBearOH  and (not i_firstOnly or not rOH)
```

Change to:
```pine
sigRevBullPML = rRevBullPML and (not i_firstOnly or not rPML) and fGateBull
sigRevBullYL  = rRevBullYL  and (not i_firstOnly or not rYL)  and fGateBull
sigRevBullWL  = rRevBullWL  and (not i_firstOnly or not rWL)  and fGateBull
sigRevBullOL  = rRevBullOL  and (not i_firstOnly or not rOL)  and fGateBull

sigRevBearPMH = rRevBearPMH and (not i_firstOnly or not rPMH) and fGateBear
sigRevBearYH  = rRevBearYH  and (not i_firstOnly or not rYH)  and fGateBear
sigRevBearWH  = rRevBearWH  and (not i_firstOnly or not rWH)  and fGateBear
sigRevBearOH  = rRevBearOH  and (not i_firstOnly or not rOH)  and fGateBear
```

**Step 3: Verify Suppress mode works**

In TradingView: enable all 4 filters with "Suppress" mode. Compare signal count vs. baseline (should be ~30% of original). Toggle each filter individually to verify independent operation.

**Step 4: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "feat(v2.5): apply evidence stack filters to breakout + reversal signals"
```

---

### Task 5: Add Dim Mode Visual Styling

**Files:**
- Modify: `KeyLevelBreakout.pine` — bull label styling (~line 708-712)
- Modify: `KeyLevelBreakout.pine` — bear label styling (~line 835-839)
- Modify: `KeyLevelBreakout.pine` — bull combined text (~line 702-703)
- Modify: `KeyLevelBreakout.pine` — bear combined text (~line 828-830)

**Step 1: Add Dim mode flag and `?` suffix to bull labels**

In the bull label section, after `combinedBullText += bullQualLine ...` (around line 703), add:

```pine
    // Evidence stack dim mode: append ? suffix when filter fails
    bool isDimBull = i_fMode == "Dim" and not evStackBull
    if isDimBull
        combinedBullText += "\n?"
```

Then in the bull label styling section (around line 708-712), modify the color/size logic. Find:
```pine
    bool isCooled = i_cooldownBars > 0 and (sigBarIdx - lastBullSigBar) <= i_cooldownBars
    bool isAftn   = i_dimAfternoon and isAfternoon and not isOld and not isCooled
    color finalColor = isCooled ? color.new(color.gray, 70) : isAftn ? color.new(lblColor, 60) : (isOld ? color.new(color.gray, 90) : lblColor)
    color finalText  = isCooled ? color.new(color.gray, 50) : isAftn ? color.new(color.gray, 30) : (isOld ? color.new(color.gray, 70) : color.black)
    string finalSize = isCooled ? size.tiny : isAftn ? size.tiny : (totalCount > 1 ? size.normal : size.small)
```

Change to (add `isDimBull` as highest-priority dim, before cooldown):
```pine
    bool isCooled = i_cooldownBars > 0 and (sigBarIdx - lastBullSigBar) <= i_cooldownBars
    bool isAftn   = i_dimAfternoon and isAfternoon and not isOld and not isCooled
    color finalColor = isDimBull ? color.new(color.gray, 70) : isCooled ? color.new(color.gray, 70) : isAftn ? color.new(lblColor, 60) : (isOld ? color.new(color.gray, 90) : lblColor)
    color finalText  = isDimBull ? color.new(color.gray, 50) : isCooled ? color.new(color.gray, 50) : isAftn ? color.new(color.gray, 30) : (isOld ? color.new(color.gray, 70) : color.black)
    string finalSize = isDimBull ? size.tiny : isCooled ? size.tiny : isAftn ? size.tiny : (totalCount > 1 ? size.normal : size.small)
```

**Step 2: Add Dim mode flag and `?` suffix to bear labels**

Same pattern in the bear label section. After `combinedBearText += bearQualLine ...` (around line 830), add:

```pine
    // Evidence stack dim mode: append ? suffix when filter fails
    bool isDimBear = i_fMode == "Dim" and not evStackBear
    if isDimBear
        combinedBearText += "\n?"
```

Then modify the bear label styling (around lines 835-839):
```pine
    bool isCooled = i_cooldownBars > 0 and (sigBarIdx - lastBearSigBar) <= i_cooldownBars
    bool isAftn   = i_dimAfternoon and isAfternoon and not isOld and not isCooled
    color finalColor = isDimBear ? color.new(color.gray, 70) : isCooled ? color.new(color.gray, 70) : isAftn ? color.new(lblColor, 60) : (isOld ? color.new(color.gray, 90) : lblColor)
    color finalText  = isDimBear ? color.new(color.gray, 50) : isCooled ? color.new(color.gray, 50) : isAftn ? color.new(color.gray, 30) : (isOld ? color.new(color.gray, 70) : color.black)
    string finalSize = isDimBear ? size.tiny : isCooled ? size.tiny : isAftn ? size.tiny : (totalCount > 1 ? size.normal : size.small)
```

**Step 3: Verify Dim mode works**

In TradingView: switch Filter Mode to "Dim". Verify that filtered-out signals appear as tiny gray labels with `?` suffix, while passing signals look normal.

**Step 4: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "feat(v2.5): add Dim mode visual styling for filtered signals"
```

---

### Task 6: Add Filter Status to Log Output

**Files:**
- Modify: `KeyLevelBreakout.pine` — inside `dbAppend()` function (around line 388)

**Step 1: Extend the log message with filter status fields**

Find the `msg` construction inside `dbAppend()` (line 388):
```pine
            string msg = "[KLB] " + fmtTime(time) + " " + dir + " " + typ + " " + levels + " vol=" + volStr + " pos=" + posStr + " vwap=" + vwapStr + " " + ohlc + " ATR=" + str.tostring(nz(dailyATR), "#.##") + " rawVol=" + str.tostring(nz(sigVol), "#") + " volSMA=" + str.tostring(nz(volBase), "#") + " buf=" + str.tostring(breakBuf, "#.###") + " prices=" + lvlPrices
```

Change to (append filter status fields):
```pine
            string emaStr = not na(ema20_5m) ? (ema20_5m > ema50_5m ? "bull" : "bear") : "na"
            string rsStr  = not na(rsVsSpy) ? str.tostring(rsVsSpy * 100, "+#.#;-#.#") + "%" : "na"
            string adxStr = not na(adx_5m) ? str.tostring(adx_5m, "#") : "na"
            string bodyStr = str.tostring(math.round(bodyRatio * 100)) + "%"
            string msg = "[KLB] " + fmtTime(time) + " " + dir + " " + typ + " " + levels + " vol=" + volStr + " pos=" + posStr + " vwap=" + vwapStr + " ema=" + emaStr + " rs=" + rsStr + " adx=" + adxStr + " body=" + bodyStr + " " + ohlc + " ATR=" + str.tostring(nz(dailyATR), "#.##") + " rawVol=" + str.tostring(nz(sigVol), "#") + " volSMA=" + str.tostring(nz(volBase), "#") + " buf=" + str.tostring(breakBuf, "#.###") + " prices=" + lvlPrices
```

**Step 2: Verify log output in Pine Logs**

In TradingView: enable Debug Log, open Pine Logs panel. Verify new fields appear: `ema=bull rs=+0.3% adx=28 body=72%`.

**Step 3: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "feat(v2.5): add filter status fields to pine log output"
```

---

### Task 7: ADX Filter Replaces CHOP? Label

**Files:**
- Modify: `KeyLevelBreakout.pine` — bull CONF fail chop warning (~line 965-969)
- Modify: `KeyLevelBreakout.pine` — bear CONF fail chop warning (~line 1011-1015)

**Step 1: Suppress CHOP? label when ADX filter is active**

The ADX filter already detects chop (ADX < 20). When it's enabled, the CHOP? label is redundant. Find the bull chop warning (around line 965):

```pine
        // Chop day warning
        if i_chopWarn and confFailStreak >= 3 and confPassCount == 0 and not chopWarned and not isOld
```

Change to:
```pine
        // Chop day warning (suppressed when ADX filter is active — it already detects chop)
        if i_chopWarn and not i_fADX and confFailStreak >= 3 and confPassCount == 0 and not chopWarned and not isOld
```

**Step 2: Same change for bear CONF fail section**

Find the bear chop warning (around line 1011):
```pine
        if i_chopWarn and confFailStreak >= 3 and confPassCount == 0 and not chopWarned and not isOld
```

Change to:
```pine
        if i_chopWarn and not i_fADX and confFailStreak >= 3 and confPassCount == 0 and not chopWarned and not isOld
```

**Step 3: Verify behavior**

In TradingView: with ADX filter ON, verify no CHOP? labels appear (ADX already prevents chop signals). With ADX filter OFF, CHOP? labels should appear as before.

**Step 4: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "feat(v2.5): suppress CHOP? label when ADX filter handles chop detection"
```

---

### Task 8: Update Documentation and Version

**Files:**
- Modify: `KeyLevelBreakout.pine:1-5` (version comment)
- Modify: `KeyLevelBreakout.md` (changelog)

**Step 1: Update indicator header comment**

Change line 2 from:
```pine
// Detects bullish/bearish 5m candle closes through key levels
```
To:
```pine
// Detects bullish/bearish 5m candle closes through key levels (v2.5)
```

**Step 2: Add v2.5 changelog entry to KeyLevelBreakout.md**

Add to the changelog section:

```markdown
### v2.5 — Evidence Stack Filters
- **5m EMA Alignment Filter:** Suppresses signals against the 5m EMA(20)/EMA(50) trend direction
- **RS vs SPY Filter:** Requires stock to outperform SPY for longs (underperform for shorts). Auto-bypasses SPY, QQQ, GLD, SLV.
- **ADX Trend Strength Filter:** Suppresses signals when 5m ADX < 20 (choppy/no-trend environment). Replaces CHOP? label when active.
- **Candle Body Quality Filter:** Requires body > 50% of range and close in favorable 60% zone
- **Filter Mode:** Choose Suppress (hide entirely) or Dim (gray + ? suffix) for filtered signals
- **Log output:** Added ema, rs, adx, body fields to Pine Log messages
- Backtest: All 4 filters combined keep ~30% of signals, improve GOOD:BAD from 3.0:1 to 3.8:1
```

**Step 3: Commit**

```bash
git add KeyLevelBreakout.pine KeyLevelBreakout.md
git commit -m "docs: update version to v2.5 with evidence stack filters changelog"
```

---

## Verification Checklist

After all tasks are complete, verify in TradingView:

1. **Suppress mode (all 4 filters ON):** Signal count drops ~70% vs baseline
2. **Dim mode:** Filtered signals appear as tiny gray labels with `?`
3. **Toggle each filter independently:** Each reduces signals when enabled
4. **SPY chart:** RS filter has no effect (auto-bypass)
5. **Pine Logs:** New fields `ema=`, `rs=`, `adx=`, `body=` appear in log output
6. **CHOP? label:** Suppressed when ADX filter is ON, appears when OFF
7. **No repainting:** Navigate to a historical bar, note signals, refresh — same signals appear

## Security Call Budget

| Call | Timeframe | Data | Status |
|------|-----------|------|--------|
| 1 | D | yestHigh, yestLow, yestOpen, yestClose, **todayOpen** | Modified |
| 2 | W | weekHigh, weekLow, weekOpen, weekClose | Existing |
| 3 | D | dailyATR | Existing |
| 4 | D | dailyVolSma | Existing |
| 5 | signal TF | sigC, sigO, sigH, sigL, sigPC, sigPC2, sigVol, sigVolPrev, sigVolSma | Existing |
| **6** | **5** | **ema20_5m, ema50_5m, adx_5m** | **New** |
| **7** | **signal TF** | **spyClose** | **New** |
| **8** | **D** | **spyDayOpen** | **New** |
| **Total** | | | **8 of 40** |
