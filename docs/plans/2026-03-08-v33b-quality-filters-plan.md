# v3.3b Quality Filters — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add 3 remaining fingerprint-driven quality filters to KLB: midday flat-EMA dim override, broad coil dim override, and quiet coil EMA hard gate bypass.

**Architecture:** All 3 changes are in `KeyLevelBreakout.pine`. Changes 1-2 add booleans near existing conditions (~line 596) and wire them into isDimBull/isDimBear (~lines 1412, 1585). Change 3 refactors the EMA gate into a single variable and replaces all 30+ references.

**Tech Stack:** Pine Script v6, TradingView

---

## Task 1: Add Midday Flat-EMA Dim Override

**Files:**
- Modify: `KeyLevelBreakout.pine:596-599` (add boolean after isMidday)
- Modify: `KeyLevelBreakout.pine:~1412` (isDimBull)
- Modify: `KeyLevelBreakout.pine:~1585` (isDimBear)

**Step 1: Add isMiddayFlat boolean**

After line 596 (`bool isMidday = ...`), add:

```pine
// v3.3b: Midday + flat EMA boost — 31.1% great (1.55x), 2.2% noise, N=541
bool isMiddayFlat = isMidday and not na(ema20_5m) and not na(dailyATR) and dailyATR > 0 and math.abs(ema20_5m - nz(ema20_5m[6])) / dailyATR < 0.02
```

**Step 2: Wire into isDimBull**

Find the `isDimBull` line (currently ends with `and not isQuietCoil`). Change to:
```pine
    bool isDimBull = ((i_fMode == "Dim" and not (bullText != "" ? evStackBull : evStackBull_rev)) or isVolModerate or emaGateBull_dim or isRegimeDimBull or isVolExhaustBull or isExhausted or isFreshDimBull) and not isQuietCoil and not isMiddayFlat and not isBroadCoil
```

Note: We add BOTH `isMiddayFlat` and `isBroadCoil` here (isBroadCoil from Task 2). If doing Task 1 first, just add `isMiddayFlat`; Task 2 will add `isBroadCoil`.

**Step 3: Wire into isDimBear**

Same pattern on the `isDimBear` line:
```pine
    bool isDimBear = ((i_fMode == "Dim" and not (bearText != "" ? evStackBear : evStackBear_rev)) or isVolModerate or emaGateBear_dim or isRegimeDimBear or isVolExhaustBear or isExhausted or isFreshDimBear) and not isQuietCoil and not isMiddayFlat and not isBroadCoil
```

**Verify:** In TradingView, check a midday signal (11:00-14:00) when EMA21 is flat. It should show at full brightness even if other dim conditions fire. Check that morning/afternoon signals are unaffected.

---

## Task 2: Add Broad Coil Dim Override

**Files:**
- Modify: `KeyLevelBreakout.pine:~587` (add boolean after isQuietCoil)
- Modify: `KeyLevelBreakout.pine:~1412` (isDimBull — if not already added in Task 1)
- Modify: `KeyLevelBreakout.pine:~1585` (isDimBear — if not already added in Task 1)

**Step 1: Add isBroadCoil boolean**

After the `isQuietCoil` line (~587), add:

```pine
// v3.3b: Broad Coil — small trigger + SPY moving = whole market is going (32.1% great, 1.6x, 1.0% noise)
bool isBroadCoil = sigRangeATR < 0.5 and math.abs(spyChg) > 0.003
```

**Step 2: Wire into isDimBull and isDimBear**

If Task 1 already added the full dim override chain, this is already done. If not, add `and not isBroadCoil` to both isDimBull and isDimBear (same pattern as isQuietCoil and isMiddayFlat).

**Verify:** In TradingView, find a signal where SPY has moved > 0.3% and the signal bar range is small (< 0.5 ATR). It should show full brightness.

---

## Task 3: Refactor EMA Gate into Unified Variable + Quiet Coil Bypass

**Files:**
- Modify: `KeyLevelBreakout.pine:~840-855` (BRK signal definitions)
- Modify: `KeyLevelBreakout.pine:~924-945` (REV signal definitions)
- Modify: `KeyLevelBreakout.pine:~998-999` (QBS signal definitions)

This is the aggressive change. We refactor the repeated `(emaGateBull or isPre950)` pattern into a single variable that includes the quiet coil bypass.

**Step 1: Define unified EMA pass variables**

Add these right before the signal definitions block (around line 838, before the first `sigBullPMH` line):

```pine
// v3.3b: Unified EMA pass — includes pre-9:50 bypass AND quiet coil bypass (aggressive)
// Quiet coil (drying vol + small range) bypasses EMA gate — catches Tier S monsters (40% EMA-misaligned)
bool emaPassBull = emaGateBull or isPre950 or isQuietCoil
bool emaPassBear = emaGateBear or isPre950 or isQuietCoil
```

**Step 2: Replace all `(emaGateBull or isPre950)` with `emaPassBull`**

Use replace-all. There are 17 instances on the bull side:
- Lines 842, 844, 846, 848, 852, 854 (BRK signals)
- Lines 924, 925, 926, 935, 936, 937, 938, 941, 944, 945 (REV signals)
- Line 998 (QBS signal)

Replace: `(emaGateBull or isPre950)` → `emaPassBull`

**Step 3: Replace all `(emaGateBear or isPre950)` with `emaPassBear`**

There are 10 instances on the bear side:
- Lines 843, 845, 847, 849, 850, 851, 853, 855 (BRK signals)
- Line 942 (REV VWAP)
- Line 999 (QBS signal)

Replace: `(emaGateBear or isPre950)` → `emaPassBear`

**Step 4: Handle EXREV signals (DO NOT CHANGE)**

Lines 929-932 use `(emaGateBear or isPre950 or exrevBypass)` — these already have their own bypass and should NOT be changed. They use a 3-way OR, not the 2-way pattern. Verify these lines are untouched after the replace-all.

**Verify:**
1. EXREV lines 929-932 still have `(emaGateBear or isPre950 or exrevBypass)` — not replaced
2. All other signal lines now use `emaPassBull` or `emaPassBear`
3. In TradingView: find a bar where EMA is against (e.g., EMA21 < EMA50 for bull) but volume is drying and range is small. A signal should now fire that wouldn't have fired before.
4. Check that pre-9:50 signals still work (isPre950 path unchanged)

---

## Task 4: Bump Version Comment + Commit

**Step 1: Update version comment**

The header comment already says v3.3 and indicator title says v3.3 (updated earlier). No version bump needed — these are part of the same v3.3 release.

**Step 2: Commit all changes**

```
git add KeyLevelBreakout.pine docs/plans/2026-03-08-v33b-quality-filters-design.md docs/plans/2026-03-08-v33b-quality-filters-plan.md
git commit -m "v3.3b: midday flat-EMA boost, broad coil boost, quiet coil EMA bypass"
```

---

## Summary of All Edits

| Location | What Changes |
|----------|-------------|
| ~Line 587 | Add `isBroadCoil` boolean |
| ~Line 597 | Add `isMiddayFlat` boolean |
| ~Line 838 | Add `emaPassBull`, `emaPassBear` variables |
| Lines 842-855 | Replace `(emaGateBull or isPre950)` → `emaPassBull` (6 lines) |
| Lines 843-855 | Replace `(emaGateBear or isPre950)` → `emaPassBear` (8 lines) |
| Lines 924-945 | Replace bull EMA gates → `emaPassBull` (11 lines) |
| Line 942 | Replace bear VWAP EMA gate → `emaPassBear` (1 line) |
| Lines 998-999 | Replace QBS EMA gates (2 lines) |
| ~Line 1412 | isDimBull: add `and not isMiddayFlat and not isBroadCoil` |
| ~Line 1585 | isDimBear: add `and not isMiddayFlat and not isBroadCoil` |
| Lines 929-932 | **DO NOT CHANGE** (EXREV has own bypass) |

Total: ~35 line modifications, 3 new lines.
