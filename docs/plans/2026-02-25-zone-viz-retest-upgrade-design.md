# KeyLevelBreakout v1.8 — Zone Visualization + Retest Upgrade

**Date:** 2026-02-25
**Status:** Approved
**Inspiration:**
- Tom Vorwald: wick-to-body zones carry rejection strength info, levels are zones not lines
- First Candle 5m Scalping Strategy: retest is the entry, not the breakout

---

## Feature A: Zone Band Visualization

**What:**
When `i_showLines` is ON, draw shaded bands between wick and body edge for each level.

**How:**
- 8 new `plot()` calls for body edge lines
- 8 `fill()` calls between wick plot and body-edge plot
- Colors: same per-level color at ~85 transparency
  - PM: orange
  - Yest: blue
  - Week: purple
  - ORB: teal

**Band width behavior:**
- D/W: varies per candle (real wick-to-body) — wide = strong rejection
- PM/ORB: uniform (ATR-derived) — no single candle to reference

**Inputs:** None new. Gated by existing `i_showLines` + `i_useZones`.

---

## Feature B: Per-Level Retest Tracking

**What:**
Track retest state independently for each of the 8 levels, replacing the current
single-tracker-per-direction system.

**State per level (8 levels × 3 vars = 24 vars, replacing old 12):**
- `retestState` — 0=none, 1=monitoring, 2=retested, 3=time-confirmed, -1=failed
- `retestBar` — bar_index when breakout fired (for bar count)
- `retestLbl` — reference to the breakout label (for text updates)

**Retest detection (per level, each chart bar):**
- **Retested:** price dips back to within `rearmBuf` of level AND closes on breakout side
- **Time-confirmed:** survived `i_confirmBars` bars without failing
- **Failed:** price closes back through level beyond `rearmBuf`

**Smart summarization:**
Retests append as new lines on the breakout label:

```
ORB H + Yest H
1.8x ^82
⟳³ ORB H 2.1x ^85
⟳⁷ Yest H 1.4x ^71
```

- Each retest gets its own line with superscript bar count
- Same-bar retests merge: `⟳³ ORB H + Yest H 2.1x ^85`
- Failed: `✗` appended, label grayed out

---

## Feature C: PA Quality on Retest Candle

**What:**
Assess price action quality of the retest candle specifically.

**Metrics:**
- Close position %: same computation as breakout candle, applied to retest bar
  - Bull: `^85` = close at 85% toward high = strong
  - Bear: `v90` = close at 90% toward low = strong
- Volume multiple: retest candle volume vs baseline

**Display:**
On the retest line: `⟳³ ORB H 2.1x ^85`

---

## Feature D: Retest-Only Toggle

**Input:**
```
i_retestOnly = input.bool(false, "Retest-Only Mode", group="Signals")
```

**When OFF (default):**
- Breakout label fires as today (with line-break formatting)
- Retest info appended as suffix lines on breakout label
- Both breakout and retest alerts fire

**When ON:**
- Breakout detection runs internally (unchanged)
- Breakout label suppressed → small gray dot at breakout bar
- Retest fires its own label at the retest bar:
  ```
  ⟳³ ORB H
  2.1x ^85
  ```
- Only retest alerts fire, breakout alerts suppressed

**Unchanged regardless of toggle:**
- All internal logic (flags, re-arm, reversal/reclaim)
- Zone band visualization
- Reversal/reclaim labels

---

## Label Format (all modes)

Line breaks separate concerns:

```
Line 1: Level name(s)
Line 2: Volume + PA quality
Line 3+: Retest lines (one per retest, grows as they come in)
```

---

## Scope

### Changes
| File | What |
|------|------|
| `KeyLevelBreakout.pine` | Features A-D, label format |
| `KeyLevelBreakout.md` | Document new features |
| `KeyLevelBreakout_Improvements.md` | Update status |

### No changes
- Breakout detection logic
- Reversal / reclaim logic and labels
- Flag management and re-arm
- Zone bounds computation
- KeyLevelScanner.pine (separate scope, later)

### New inputs: 1
- `i_retestOnly` (default OFF)

### New vars: ~24 (replacing 12)
### New plots: 8 body-edge + 8 fills
