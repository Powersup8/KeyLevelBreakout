# Debug Signal Table Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a togglable debug table (chart overlay) and Pine Logs output to KeyLevelBreakout.pine for post-session signal analysis.

**Architecture:** Parallel `var` arrays store signal data as it fires. Chart table renders once on `barstate.islast` from the last N entries. `log.info()` fires immediately at each signal for full-data export. Confirmation state tracked via saved array indices, updated on state transitions.

**Tech Stack:** Pine Script v6, `table.new()`, `log.info()`

---

## Context for the Implementer

**File:** `KeyLevelBreakout.pine` (~896 lines) — a TradingView indicator that detects breakouts, reversals, reclaims, and retests at key intraday levels.

**Key variables available at signal time:**
- `sigC`, `sigO`, `sigH`, `sigL` — signal-TF bar OHLC (line 222)
- `volRatioBull`, `volRatioBear` — volume ratio vs baseline (lines 257-258)
- `bullClosePos`, `bearClosePos` — close position 0-100% (lines 266-267)
- `dailyATR` — ATR(14) (line 81)
- `sigVol`, `sigVolSma` — raw volume + SMA (line 222)
- `breakBuf`, `rearmBuf` — ATR buffer values (lines 242-243)
- `pmHigh`, `pmLow`, `yestHigh`, `yestLow`, `weekHigh`, `weekLow`, `orbHigh`, `orbLow` — level prices (lines 63-93)

**Signal fire locations (where to append):**
1. Bull combined label block — line 572 (`if combinedBullText != ""`)
2. Bear combined label block — line 670 (`if combinedBearText != ""`)
3. Bull retest detection — line 781 (`if anyNew` inside bull retest monitoring)
4. Bear retest detection — line 815 (`if anyNew` inside bear retest monitoring)

**Confirmation state transitions (where to update `dbConf`):**
- Bull failure: line 766 (`bRTState := -1`)
- Bear failure: line 800 (`sRTState := -1`)
- Bull window expiry: line 794 (`bRTState := 0`)
- Bear window expiry: line 828 (`sRTState := 0`)
- Auto-promote bull: line 625 (`if bRTState == 1` before new breakout setup)
- Auto-promote bear: line 723 (`if sRTState == 1` before new breakout setup)

**Session reset:** line 172 (`if newRegular`)

**Design doc:** `docs/plans/2026-02-26-debug-table-design.md`

**No test framework exists.** Testing = paste into TradingView, add to chart, verify table renders and log output matches expectations. Use SPY 1m chart on Feb 25, 2026 data for verification (known signals from previous analysis).

---

### Task 1: Add Debug Inputs + Array Declarations

**Files:**
- Modify: `KeyLevelBreakout.pine:41-49` (after Reversal/Reclaim Toggles, before Session Detection)
- Modify: `KeyLevelBreakout.pine:150-170` (after last `var` block, before `if newRegular`)

**Step 1: Add debug inputs after line 49 (after `i_revORB`)**

Insert this block after line 49 (`i_revORB = input.bool(...)`) and before line 51 (`// ─── Session Detection`):

```pine
// ─── Debug Inputs ─────────────────────────────────────
i_debugTable = input.bool(false, "Show Signal Table",        group="Debug")
i_debugLog   = input.bool(false, "Log Signals (Pine Logs)",  group="Debug")
i_debugPos   = input.string("bottom_right", "Table Position",
    options=["top_left","top_center","top_right",
             "bottom_left","bottom_center","bottom_right"], group="Debug")
i_debugRows  = input.int(20, "Max Table Rows", minval=5, maxval=50, group="Debug")
```

**Step 2: Add array declarations after line 170 (after `var int sRTPrev = 0`)**

Insert this block after line 170 and before line 172 (`if newRegular`):

```pine
// ─── Debug Signal Log Arrays ─────────────────────────
var array<int>    dbTime       = array.new<int>()
var array<string> dbDir        = array.new<string>()
var array<string> dbType       = array.new<string>()
var array<string> dbLevels     = array.new<string>()
var array<float>  dbVol        = array.new<float>()
var array<int>    dbClsPos     = array.new<int>()
var array<string> dbConf       = array.new<string>()
var array<string> dbOHLC       = array.new<string>()
// Log-only extended data
var array<float>  dbATR        = array.new<float>()
var array<float>  dbVolRaw     = array.new<float>()
var array<float>  dbVolSMA     = array.new<float>()
var array<float>  dbBuffer     = array.new<float>()
var array<string> dbLvlPrices  = array.new<string>()
// Confirmation tracking indices
var int dbConfBullIdx = -1
var int dbConfBearIdx = -1
```

**Step 3: Add session reset for debug arrays inside the `if newRegular` block**

After line 218 (`sRTPrev := 0`), before line 220 (`// ─── Signal Timeframe Data`), add:

```pine
    // Reset debug arrays at session open
    if i_debugTable or i_debugLog
        array.clear(dbTime)
        array.clear(dbDir)
        array.clear(dbType)
        array.clear(dbLevels)
        array.clear(dbVol)
        array.clear(dbClsPos)
        array.clear(dbConf)
        array.clear(dbOHLC)
        array.clear(dbATR)
        array.clear(dbVolRaw)
        array.clear(dbVolSMA)
        array.clear(dbBuffer)
        array.clear(dbLvlPrices)
        dbConfBullIdx := -1
        dbConfBearIdx := -1
```

**Step 4: Verify in TradingView**

- Add indicator to SPY 1m chart
- Open Settings → Debug group should appear with 4 inputs
- Both toggles OFF → chart unchanged, no table, no log output
- No compilation errors

**Step 5: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "feat(debug): add debug inputs and signal log array declarations"
```

---

### Task 2: Add Append + Log Helper Functions

**Files:**
- Modify: `KeyLevelBreakout.pine` — insert after the `sigQual()` helper (after line 284), before level name arrays (line 286)

**Step 1: Add the `dbAppend()` helper function**

Insert after line 284 (`vol + (vol != "" and pa != "" ? " " : "") + pa`) and before line 286 (`// Level name arrays`):

```pine
// ─── Debug: append signal to arrays + optional log ───
dbAppend(string dir, string typ, string levels, float vol, int clsPos, string conf, string lvlPrices) =>
    if i_debugTable or i_debugLog
        array.push(dbTime, time)
        array.push(dbDir, dir)
        array.push(dbType, typ)
        array.push(dbLevels, levels)
        array.push(dbVol, vol)
        array.push(dbClsPos, clsPos)
        array.push(dbConf, conf)
        string ohlc = "O" + str.tostring(sigO, "#.##") + " H" + str.tostring(sigH, "#.##") + " L" + str.tostring(sigL, "#.##") + " C" + str.tostring(sigC, "#.##")
        array.push(dbOHLC, ohlc)
        array.push(dbATR, nz(dailyATR))
        array.push(dbVolRaw, nz(sigVol))
        array.push(dbVolSMA, nz(volBase))
        array.push(dbBuffer, breakBuf)
        array.push(dbLvlPrices, lvlPrices)
        if i_debugLog
            string posStr = not na(clsPos) ? (dir == "▲" ? "^" : "v") + str.tostring(clsPos) : ""
            string volStr = not na(vol) ? str.tostring(vol, "#.#") + "x" : ""
            log.info("[KLB] {0} {1} {2} {3} vol={4} pos={5} {6} ATR={7} rawVol={8} volSMA={9} buf={10} prices={11}",
                 str.format_time(time, "HH:mm", "America/New_York"), dir, typ, levels,
                 volStr, posStr, ohlc,
                 str.tostring(nz(dailyATR), "#.##"),
                 str.tostring(nz(sigVol), "#"),
                 str.tostring(nz(volBase), "#"),
                 str.tostring(breakBuf, "#.###"),
                 lvlPrices)
    array.size(dbTime) - 1  // return index for confirmation tracking
```

**Important Pine v6 note:** `log.info()` uses `{0}`, `{1}`, etc. as positional placeholders. Verify that `str.format_time()` is available in Pine v6 — if not, fall back to manual hour/minute extraction from `time`.

**Step 2: Add a helper to build level prices string**

Insert right after `dbAppend`:

```pine
// ─── Debug: build level prices string for a signal ───
dbLvlPriceStr(bool isPMH, bool isPML, bool isYH, bool isYL, bool isWH, bool isWL, bool isOH, bool isOL) =>
    string s = ""
    if isPMH and not na(pmHigh)
        s += (s != "" ? "/" : "") + str.tostring(pmHigh, "#.##")
    if isPML and not na(pmLow)
        s += (s != "" ? "/" : "") + str.tostring(pmLow, "#.##")
    if isYH and not na(yestHigh)
        s += (s != "" ? "/" : "") + str.tostring(yestHigh, "#.##")
    if isYL and not na(yestLow)
        s += (s != "" ? "/" : "") + str.tostring(yestLow, "#.##")
    if isWH and not na(weekHigh)
        s += (s != "" ? "/" : "") + str.tostring(weekHigh, "#.##")
    if isWL and not na(weekLow)
        s += (s != "" ? "/" : "") + str.tostring(weekLow, "#.##")
    if isOH and not na(orbHigh)
        s += (s != "" ? "/" : "") + str.tostring(orbHigh, "#.##")
    if isOL and not na(orbLow)
        s += (s != "" ? "/" : "") + str.tostring(orbLow, "#.##")
    s
```

**Step 3: Verify in TradingView**

- Compile check — no errors (functions are defined but not yet called)
- No visible change on chart

**Step 4: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "feat(debug): add dbAppend and dbLvlPriceStr helper functions"
```

---

### Task 3: Wire Append Calls into Signal Fire Points

**Files:**
- Modify: `KeyLevelBreakout.pine` — 4 locations where signals fire

**Step 1: Add bull breakout/reversal append**

Inside the bull combined label block, after the label is created and before the cooldown tracker update. Find the block starting at `if combinedBullText != ""` (line 572). After the `if not isOld` lastBullLblBar update (line 620), add:

```pine
    // Debug append — bull breakout and/or reversal
    if (i_debugTable or i_debugLog) and not isOld
        if bullText != ""
            string prices = dbLvlPriceStr(sigBullPMH, false, sigBullYH, false, sigBullWH, false, sigBullOH, false)
            int idx = dbAppend("▲", "BRK", bullText, volRatioBull, bullClosePos, "…", prices)
            if i_confirm
                dbConfBullIdx := idx
        if revBullText != ""
            string revType = revBullHasReclaim ? "~~" : "~"
            string prices = dbLvlPriceStr(false, sigRevBullPML, false, sigRevBullYL, false, sigRevBullWL, false, sigRevBullOL)
            dbAppend("▲", revType, revBullText, volRatioBull, bullClosePos, "—", prices)
```

**Step 2: Add bear breakout/reversal append**

Same pattern for the bear combined label block. After the bear `lastBearLblBar` update (line 718), add:

```pine
    // Debug append — bear breakout and/or reversal
    if (i_debugTable or i_debugLog) and not isOld
        if bearText != ""
            string prices = dbLvlPriceStr(false, sigBearPML, false, sigBearYL, false, sigBearWL, false, sigBearOL)
            int idx = dbAppend("▼", "BRK", bearText, volRatioBear, bearClosePos, "…", prices)
            if i_confirm
                dbConfBearIdx := idx
        if revBearText != ""
            string revType = revBearHasReclaim ? "~~" : "~"
            string prices = dbLvlPriceStr(sigRevBearPMH, false, sigRevBearYH, false, sigRevBearWH, false, sigRevBearOH)
            dbAppend("▼", revType, revBearText, volRatioBear, bearClosePos, "—", prices)
```

**Step 3: Add bull retest append**

Inside the bull retest `if anyNew` block (line 781), after the alert line (line 789), add:

```pine
                // Debug: log each new retest
                if i_debugTable or i_debugLog
                    dbAppend("▲", "◆", rtText, volRatioBull, bullClosePos, "—", "")
```

**Step 4: Add bear retest append**

Inside the bear retest `if anyNew` block (line 815), after the alert line (line 823), add:

```pine
                // Debug: log each new retest
                if i_debugTable or i_debugLog
                    dbAppend("▼", "◆", rtText, volRatioBear, bearClosePos, "—", "")
```

**Step 5: Verify in TradingView**

- Toggle `Log Signals` ON in settings
- Open Pine Logs panel (bottom panel → Pine Logs tab)
- Navigate to SPY 1m chart with Feb 25 data
- Should see `[KLB]` entries for each signal
- Toggle both OFF → no log output, chart unchanged

**Step 6: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "feat(debug): wire dbAppend calls into all 4 signal fire points"
```

---

### Task 4: Add Confirmation State Updates

**Files:**
- Modify: `KeyLevelBreakout.pine` — 6 locations where confirmation state changes

**Step 1: Update dbConf on bull auto-promote**

At line 625 (inside bull confirmation setup, `if bRTState == 1`), after `label.set_text(...)`, add:

```pine
            if dbConfBullIdx >= 0 and dbConfBullIdx < array.size(dbConf)
                array.set(dbConf, dbConfBullIdx, "✓")
                if i_debugLog
                    log.info("[KLB] CONF {0} ▲ BRK → ✓ (auto-promote)", str.format_time(time, "HH:mm", "America/New_York"))
```

**Step 2: Update dbConf on bear auto-promote**

At line 723 (inside bear confirmation setup, `if sRTState == 1`), after `label.set_text(...)`, add:

```pine
            if dbConfBearIdx >= 0 and dbConfBearIdx < array.size(dbConf)
                array.set(dbConf, dbConfBearIdx, "✓")
                if i_debugLog
                    log.info("[KLB] CONF {0} ▼ BRK → ✓ (auto-promote)", str.format_time(time, "HH:mm", "America/New_York"))
```

**Step 3: Update dbConf on bull failure**

At line 766 (`bRTState := -1` inside bull retest monitoring), after the label color changes, add:

```pine
        if dbConfBullIdx >= 0 and dbConfBullIdx < array.size(dbConf)
            array.set(dbConf, dbConfBullIdx, "✗")
            if i_debugLog
                log.info("[KLB] CONF {0} ▲ BRK → ✗ (failed)", str.format_time(time, "HH:mm", "America/New_York"))
```

**Step 4: Update dbConf on bear failure**

At line 800 (`sRTState := -1` inside bear retest monitoring), after the label color changes, add:

```pine
        if dbConfBearIdx >= 0 and dbConfBearIdx < array.size(dbConf)
            array.set(dbConf, dbConfBearIdx, "✗")
            if i_debugLog
                log.info("[KLB] CONF {0} ▼ BRK → ✗ (failed)", str.format_time(time, "HH:mm", "America/New_York"))
```

**Step 5: Update dbConf on bull window expiry**

At line 794 (`bRTState := 0` when elapsed >= retestMaxElapsed), add just before:

```pine
        if dbConfBullIdx >= 0 and dbConfBullIdx < array.size(dbConf) and array.get(dbConf, dbConfBullIdx) == "…"
            array.set(dbConf, dbConfBullIdx, "✓")
            if i_debugLog
                log.info("[KLB] CONF {0} ▲ BRK → ✓ (window)", str.format_time(time, "HH:mm", "America/New_York"))
```

**Step 6: Update dbConf on bear window expiry**

At line 828 (`sRTState := 0` when elapsed >= retestMaxElapsed), add just before:

```pine
        if dbConfBearIdx >= 0 and dbConfBearIdx < array.size(dbConf) and array.get(dbConf, dbConfBearIdx) == "…"
            array.set(dbConf, dbConfBearIdx, "✓")
            if i_debugLog
                log.info("[KLB] CONF {0} ▼ BRK → ✓ (window)", str.format_time(time, "HH:mm", "America/New_York"))
```

**Step 7: Verify in TradingView**

- Log Signals ON → check Pine Logs for `[KLB] CONF` entries
- Breakout labels that show ✓ on chart should have matching `→ ✓` log lines
- Breakout labels that show ✗ on chart should have matching `→ ✗` log lines

**Step 8: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "feat(debug): add confirmation state tracking to debug arrays"
```

---

### Task 5: Add Chart Table Rendering

**Files:**
- Modify: `KeyLevelBreakout.pine` — insert before the `// ─── Level Lines` section (before line 842)

**Step 1: Add the table render block**

Insert before `// ─── Level Lines (optional, off by default)` (line 842):

```pine
// ─── Debug Signal Table ──────────────────────────────
if i_debugTable and barstate.islast
    posMap = i_debugPos == "top_left" ? position.top_left :
             i_debugPos == "top_center" ? position.top_center :
             i_debugPos == "top_right" ? position.top_right :
             i_debugPos == "bottom_left" ? position.bottom_left :
             i_debugPos == "bottom_center" ? position.bottom_center :
             position.bottom_right

    int totalRows = array.size(dbTime)
    int startIdx  = math.max(0, totalRows - i_debugRows)
    int showRows  = totalRows - startIdx

    var table dbTbl = table.new(posMap, 8, showRows + 1,
         bgcolor=color.new(color.black, 80), border_width=1,
         border_color=color.new(color.gray, 60))

    // Header row
    table.cell(dbTbl, 0, 0, "Time",  text_color=color.white, text_size=size.tiny, bgcolor=color.new(color.gray, 30))
    table.cell(dbTbl, 1, 0, "Dir",   text_color=color.white, text_size=size.tiny, bgcolor=color.new(color.gray, 30))
    table.cell(dbTbl, 2, 0, "Type",  text_color=color.white, text_size=size.tiny, bgcolor=color.new(color.gray, 30))
    table.cell(dbTbl, 3, 0, "Levels",text_color=color.white, text_size=size.tiny, bgcolor=color.new(color.gray, 30))
    table.cell(dbTbl, 4, 0, "Vol",   text_color=color.white, text_size=size.tiny, bgcolor=color.new(color.gray, 30))
    table.cell(dbTbl, 5, 0, "Pos",   text_color=color.white, text_size=size.tiny, bgcolor=color.new(color.gray, 30))
    table.cell(dbTbl, 6, 0, "Conf",  text_color=color.white, text_size=size.tiny, bgcolor=color.new(color.gray, 30))
    table.cell(dbTbl, 7, 0, "OHLC",  text_color=color.white, text_size=size.tiny, bgcolor=color.new(color.gray, 30))

    // Data rows
    for i = startIdx to totalRows - 1
        int row = i - startIdx + 1
        string dir  = array.get(dbDir, i)
        string typ  = array.get(dbType, i)
        string conf = array.get(dbConf, i)
        bool isBull = dir == "▲"
        bool isFailed = conf == "✗"

        // Row background color
        color rowBg = isFailed ? color.new(color.gray, 85) :
             typ == "BRK" ? (isBull ? color.new(color.green, 88) : color.new(color.red, 88)) :
             typ == "~" or typ == "~~" ? (isBull ? color.new(color.aqua, 88) : color.new(color.orange, 88)) :
             color.new(color.black, 88)
        color rowTxt = isFailed ? color.new(color.gray, 40) : color.white

        string timeStr = str.format_time(array.get(dbTime, i), "HH:mm", "America/New_York")
        float vol = array.get(dbVol, i)
        string volStr = not na(vol) ? str.tostring(vol, "#.#") + "x" : "—"
        int pos = array.get(dbClsPos, i)
        string posStr = not na(pos) ? (isBull ? "^" : "v") + str.tostring(pos) : "—"

        table.cell(dbTbl, 0, row, timeStr,                    text_color=rowTxt, text_size=size.tiny, bgcolor=rowBg)
        table.cell(dbTbl, 1, row, dir,                         text_color=isBull ? color.green : color.red, text_size=size.tiny, bgcolor=rowBg)
        table.cell(dbTbl, 2, row, typ,                         text_color=rowTxt, text_size=size.tiny, bgcolor=rowBg)
        table.cell(dbTbl, 3, row, array.get(dbLevels, i),     text_color=rowTxt, text_size=size.tiny, bgcolor=rowBg, text_halign=text.align_left)
        table.cell(dbTbl, 4, row, volStr,                      text_color=rowTxt, text_size=size.tiny, bgcolor=rowBg)
        table.cell(dbTbl, 5, row, posStr,                      text_color=rowTxt, text_size=size.tiny, bgcolor=rowBg)
        table.cell(dbTbl, 6, row, conf,                        text_color=conf == "✓" ? color.lime : conf == "✗" ? color.red : color.gray, text_size=size.tiny, bgcolor=rowBg)
        table.cell(dbTbl, 7, row, array.get(dbOHLC, i),       text_color=rowTxt, text_size=size.tiny, bgcolor=rowBg, text_halign=text.align_left)

```

**Pine v6 note on `table.new` with `var`:** The `var` keyword ensures the table object persists. But since row count changes, we use `table.new()` inside the `if barstate.islast` block (non-var) — Pine rebuilds it on the last bar. If TradingView flickers, try `var table dbTbl = na` at declaration, then assign inside the block.

**Step 2: Verify in TradingView**

- Toggle `Show Signal Table` ON
- Table should appear in bottom-right corner
- Should show all signals from the session with correct data
- Check column alignment and readability
- Try different positions via dropdown
- Try adjusting Max Table Rows (5, 10, 20, 50)
- Toggle OFF → table disappears

**Step 3: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "feat(debug): add chart table rendering on barstate.islast"
```

---

### Task 6: Documentation + Final Cleanup

**Files:**
- Modify: `KeyLevelBreakout.md`
- Modify: `KeyLevelBreakout_Improvements.md`

**Step 1: Update KeyLevelBreakout.md**

Add a new section before the Changelog section:

```markdown
### Debug Signal Table

Toggle `Show Signal Table` (Debug group) to display a chart overlay table listing all signals from the current session:

| Column | Content |
|--------|---------|
| Time | Signal time (HH:MM ET) |
| Dir | ▲ (bull) / ▼ (bear) |
| Type | BRK / ~ / ~~ / ◆ |
| Levels | Level names (e.g., "PM H + Week H") |
| Vol | Volume ratio vs baseline |
| Pos | Close position % |
| Conf | ✓ confirmed / ✗ failed / … monitoring / — N/A |
| OHLC | Signal-TF bar OHLC |

Toggle `Log Signals` to output full signal data to TradingView's Pine Logs panel (`[KLB]` prefix). Log includes all table columns plus: ATR, raw volume, volume SMA, ATR buffer, level prices. Confirmation state changes logged as separate `[KLB] CONF` entries.

Both toggles are independent and OFF by default. Table position and max rows are configurable.
```

Add to the Inputs table in the Settings section:

```markdown
| Show Signal Table | Debug | OFF | Display signal summary table on chart |
| Log Signals | Debug | OFF | Output signal data to Pine Logs |
| Table Position | Debug | bottom_right | Chart corner for debug table |
| Max Table Rows | Debug | 20 | Maximum signals shown in table |
```

**Step 2: Update KeyLevelBreakout_Improvements.md**

Change line 222 from:
```
### 11. Debug Label Table — think later
```
to:
```
### 11. Debug Label Table (MEDIUM impact) ✅ IMPLEMENTED v2.1
```

**Step 3: Add v2.1 changelog entry to KeyLevelBreakout.md**

```markdown
**v2.1** — Debug Signal Table
- Chart table (togglable): 8-column signal summary, color-coded by type, configurable position/rows
- Pine Logs output (togglable): full signal data with `[KLB]` prefix, CSV-like format
- Confirmation state tracking: breakout entries update with ✓/✗ as confirmation resolves
- Both outputs independent, zero overhead when OFF
```

**Step 4: Commit**

```bash
git add KeyLevelBreakout.pine KeyLevelBreakout.md KeyLevelBreakout_Improvements.md
git commit -m "docs: add debug signal table documentation, mark improvement #11 done"
```

---

## Verification Checklist

After all tasks are complete, verify on TradingView:

- [ ] Both toggles OFF → chart identical to v2.0, no table, no log output
- [ ] Table ON → renders in chosen position with correct data
- [ ] Log ON → `[KLB]` entries appear in Pine Logs for each signal
- [ ] Both ON → table + log both work simultaneously
- [ ] Table rows match label count on chart
- [ ] Breakout rows show `✓` or `✗` matching label confirmation symbols
- [ ] Reversal/reclaim/retest rows show `—` in Conf column
- [ ] Color coding: green/red for BRK, aqua/orange for ~/~~, gray for failed
- [ ] Max Table Rows = 5 → only last 5 signals shown
- [ ] Position dropdown → table moves correctly to all 6 positions
- [ ] Session change → arrays clear, table shows only current session signals
- [ ] No compilation errors, no `request.security` limit warnings
