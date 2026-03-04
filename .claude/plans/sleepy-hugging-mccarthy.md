# v2.4 Implementation Plan — Visual Quality Tiers + Logging + Cleanup

## Context

6-week analysis (3,753 signals, 13 symbols) revealed that CONF ✓ signals have 53% GOOD / 0% BAD rate, yet look identical to unconfirmed breakouts. Afternoon signals (after 11:00) have near-zero follow-through but equal visual weight. Window expiry code never fires. VWAP filter can't be validated because VWAP position isn't logged.

**File:** `KeyLevelBreakout.pine` (~1122 lines). All changes in this one file.

---

## Changes (in implementation order)

### 1. Store vol/pos for CONF tracking (A+E prerequisite)

**Where:** After CONF tracking setup — line ~773 (bull), line ~890 (bear)

Add 4 new `var` declarations near line 180:
```pine
var float bRTVolRatio = na
var int   bRTClosePos = na
var float sRTVolRatio = na
var int   sRTClosePos = na
```

Store values when CONF tracking starts:
- Bull (~line 773): `bRTVolRatio := volRatioBull`, `bRTClosePos := bullClosePos`
- Bear (~line 890): `sRTVolRatio := volRatioBear`, `sRTClosePos := bearClosePos`

---

### 2. CONF ✓ visual boost + high-conviction tier (A+E)

**Where:** Auto-promote code — lines 749 (bull), 864 (bear)

After `label.set_text(bRTLbl, bRTBase + "\n✓")`, add:
```pine
// Visual boost for CONF ✓
bool highConv = not na(bRTVolRatio) and bRTVolRatio >= 5.0 and not na(bRTClosePos) and bRTClosePos >= 80
if highConv
    label.set_text(bRTLbl, bRTBase + "\n✓★")
    label.set_color(bRTLbl, color.new(#FFD700, 0))  // gold
    label.set_size(bRTLbl, size.normal)
else
    label.set_color(bRTLbl, color.new(#32CD32, 0))  // lime green
```

Mirror for bear at line ~864 (use `sRTVolRatio`, `sRTClosePos`).

---

### 3. Add VWAP to log output (B)

**Where:** `dbAppend()` log.info() call — line ~368

Append to the log message string: `+ " vwap=" + (not na(vwapVal) ? (sigC > vwapVal ? "above" : "below") : "na")`

No new arrays needed — log-only change.

---

### 4. Afternoon dimming (C)

**Where:** Label creation — lines ~689-691 (bull), ~800-802 (bear)

New input near line 16:
```pine
i_dimAfternoon = input.bool(true, "Dim Afternoon Signals", group="Visuals")
```

New time check near line 66:
```pine
isAfternoon = isRegular and hour(time, TZ) >= 11
```

In label color logic (lines ~689-691), add afternoon dimming alongside cooldown:
```pine
bool isAftn = i_dimAfternoon and isAfternoon and not isOld
// Existing cooldown + old check, then add:
color finalColor = isCooled ? ... : isAftn ? color.new(lblColor, 60) : (isOld ? ... : lblColor)
color finalText  = isCooled ? ... : isAftn ? color.new(color.gray, 30) : (isOld ? ... : color.black)
string finalSize = isCooled ? size.tiny : isAftn ? size.tiny : (totalCount > 1 ? size.normal : size.small)
```

Mirror for bear label block.

---

### 5. Chop day warning (D)

**Where:** New `var` counter + display in CONF state transitions

New input near line 33:
```pine
i_chopWarn = input.bool(true, "Chop Day Warning", group="Signals")
```

New vars near line 180:
```pine
var int confFailStreak = 0
var int confPassCount  = 0
```

Reset at session start (near existing `newRegular` logic):
```pine
if newRegular
    confFailStreak := 0
    confPassCount  := 0
```

Increment on CONF outcomes — at auto-promote (lines 749, 864):
```pine
confPassCount += 1
confFailStreak := 0
```

At CONF ✗ (lines 911, 956):
```pine
confFailStreak += 1
```

Display: Small label when `confFailStreak >= 3 and confPassCount == 0`:
```pine
if i_chopWarn and confFailStreak >= 3 and confPassCount == 0
    label.new(bar_index, high + dailyATR * 0.3, "CHOP?",
         yloc=yloc.price, style=label.style_label_down,
         color=color.new(color.orange, 20), textcolor=color.black, size=size.small)
```

Only fires once (add `var bool chopWarned = false` guard, reset on `newRegular`).

---

### 6. Widen volume alpha range (F)

**Where:** Lines 307-308

Change:
```pine
bullVolAlpha = ... math.max(0, math.round(35 - volRatioBull * 10)) ...
bearVolAlpha = ... math.max(0, math.round(35 - volRatioBear * 10)) ...
```
To:
```pine
bullVolAlpha = ... math.max(0, math.round(60 - volRatioBull * 10)) ...
bearVolAlpha = ... math.max(0, math.round(60 - volRatioBear * 10)) ...
```

This makes <1x volume labels 50% transparent, 3x labels 30% transparent, 6x+ fully opaque. **Needs visual testing** — if too aggressive, try 50 instead of 60.

---

### 7. Dead code cleanup (G)

**Where:** Lines 945-950 (bull), 990-995 (bear)

Remove the window expiry promotion blocks:
```pine
// DELETE these lines (bull):
if elapsed >= retestMaxElapsed and bRTState == 1
    if dbConfBullIdx >= 0 ...
        array.set(dbConf, dbConfBullIdx, "✓")
        if i_debugLog and barstate.isconfirmed
            log.info("[KLB] CONF {0} ▲ BRK → ✓ (window)", fmtTime(time))
    bRTState := 0

// DELETE mirror lines (bear)
```

**Keep** `retestMaxElapsed` variable — it's used by the retest tracking system.

---

## Verification

1. **Visual check on SPY 1m chart:** Load indicator, verify:
   - CONF ✓ labels show lime green (regular) or gold (high-conviction with ✓★)
   - CONF ✗ labels still show gray
   - Afternoon labels are dimmer/smaller
   - Low-volume labels are more transparent than before
   - CHOP? label appears after 3 consecutive CONF fails at open

2. **Pine Logs check:** Enable debug logging, verify `vwap=above/below` appears in log output

3. **Regression:** Toggle all new inputs OFF → behavior should match v2.3 exactly (except dead code removal and VWAP logging which are unconditional)

4. **Alpha readability (F):** Visually confirm that 1.5x-2x volume labels are still readable. If too faint, adjust 60 down to 50.
