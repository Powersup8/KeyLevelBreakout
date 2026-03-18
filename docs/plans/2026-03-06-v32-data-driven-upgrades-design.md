# v3.2 Data-Driven Upgrades — Design Document

**Date:** 2026-03-06
**Version:** v3.1a → v3.2
**Based on:** 4 research reports (EXREV, FADE, Signal Type Matching, Midday Desert)
**Estimated impact:** +24.6 ATR minimum (before HIGH→REV reassignment)

---

## Overview

5 changes implemented in risk order (safest first), each with regression check per the Validation Protocol in KLB_GUIDELINES.md.

---

## Change 1: ORB L Bull REV Suppress

**Risk:** Minimal (removal only)
**ATR impact:** +12.5 (143 signals removed, 27% win, all net negative)
**Source:** `debug/signal-type-matching-research.md`

**What:** Suppress bull REV signals at ORB L. This is the single biggest ATR drain in the system.

**How:** Add `and not (levels contain ORB L and direction is bull)` condition to `sigRevBullOL`, or simplest: hardcode `sigRevBullOL = false`.

**Regression risk:** None — only removes losing signals.

---

## Change 2: 4 New Midday Levels

**Risk:** Low (additive — no existing logic touched)
**ATR impact:** Incremental midday coverage
**Source:** `debug/midday-desert-research.md`

### New Levels

| Level | Type | Signal | Calculation | MFE | EMA% |
|-------|------|--------|-------------|-----|------|
| Today's Open | Magnet | REV | `request.security(syminfo.tickerid, "D", open)` | 1.43 | 66.5% |
| PD Close | Magnet | REV | Previous day close | 1.38 | 72.3% |
| Week Open | Barrier | BRK | Monday's open | 1.48 | — |
| Month Open | Barrier | BRK | 1st trading day open | 1.65 | — |

### Per Level Implementation
Each level needs:
1. **Input toggle** in Level Toggles group (default: true)
2. **Level calculation** (~2 lines)
3. **Plot line** (~1 line, dashed style, distinct color)
4. **Raw signal detection** — REV for magnets (Today Open, PD Close), BRK for barriers (Week Open, Month Open)
5. **Filtered signal** — through evidence stack + EMA gate
6. **Label text** — added to bull/bear text sections
7. **Count** — added to bull/bear count expressions
8. **Log** — included in signal log output

**Lines:** ~12 per level × 4 = ~50 lines total

---

## Change 3: EXREV Bypass

**Risk:** Low-Medium (surgical addition)
**ATR impact:** +4.3 (N=31, 45.2% win)
**Source:** `debug/v31-extended-reversal-research.md`

### Critical Finding
The candle quality filter (`fCandle_bear = bodyRatio > 0.3`) kills EXREV candidates BEFORE the EMA gate. The bypass must skip BOTH gates.

### Implementation
1. **Input toggle:** `i_exrevGate` (default: true, group: Filters)
2. **Bypass variable:** `exrevBypass = i_exrevGate and bodyRatio < 0.30 and candleRange > 0`
3. **Detection variable:** `isExrevSignal = exrevBypass and not emaGateBear and not isPre950`
4. **5 bear REV filter lines:** Add `(fGateBear_rev or exrevBypass)` AND `(emaGateBear or isPre950 or exrevBypass)`
5. **Label prefix:** `x~ ` for EXREV signals
6. **Label color:** `#FF6600` (darker orange) with same alpha logic
7. **Log marker:** `x~` type in log output

**Bull EXREV:** NOT implemented (40% win, negative P&L — not validated).
**PD Mid:** Already exempt from EMA gate — no change needed.

**Lines:** ~16 (4 new + 12 modified)

---

## Change 4: FADE Resurrection

**Risk:** Medium (new signal type definition, state tracking)
**ATR impact:** +7.8 (N=327, 52.9% win for EMA-aligned FADEs)
**Source:** `debug/fade-resurrection-research.md`

### New FADE Definition
Decoupled from CONF failures. Works with auto-confirm.

**Trigger conditions:**
1. Any signal fires (BRK or REV, any CONF status)
2. Original signal was **counter-EMA** (bull signal when EMA = bear, or vice versa)
3. Price closes back through the signal's level within 6 bars (30 min on 5m)
4. FADE fires in **opposite direction** (= with EMA trend)

### State Tracking
Need persistent variables per-signal to track:
- `fadeWatchActive` (bool) — are we watching for a crossback?
- `fadeWatchDir` (int) — original signal direction (1=bull, -1=bear)
- `fadeWatchLevel` (float) — the level price to watch
- `fadeWatchExpiry` (int) — bar_index when the 6-bar window expires
- `fadeWatchEma` (string) — EMA state at original signal time

On each bar after signal:
- If `bar_index > fadeWatchExpiry` → cancel watch
- If price crosses back through `fadeWatchLevel` in opposite direction → fire FADE

### Label & Alert
- Purple label (same as v3.0b FADE): `#9C27B0`
- Text: `FADE ▲/▼` + level name
- Alert: `"FADE ▲/▼ at {level}"` with `alert.freq_once_per_bar`
- Log: `[KLB] FADE` prefix

### One-at-a-time constraint
Only track one pending FADE at a time (latest signal overwrites). Multiple simultaneous watches add complexity without proportional benefit.

**Lines:** ~60

---

## Change 5: HIGH→REV Reassignment

**Risk:** High (structural — changes signal types at 4 levels)
**ATR impact:** Large (all 5 HIGH levels underperform as BRK vs REV)
**Source:** `debug/signal-type-matching-research.md`

### Levels Affected
PM H, Yest H, ORB H, Week H — move from BRK detection to REV detection.

### How It Works
Currently these levels fire BRK signals (price breaks above resistance → continuation expected). Data shows price more often bounces back (magnet behavior). Converting to REV means:
- Signal fires when price **touches and reverses** at the level (not breaks through)
- Uses `bullRev`/`bearRev` helper or inline detection
- Goes through REV evidence stack + EMA gate

### EMA Gate Interaction
REV signals have EMA gate (validated at -11.8 ATR without it). For HIGH-level REVs:
- **Bear REV at HIGH level** = price hit resistance and reversed down. If EMA = bear, this is WITH trend → passes EMA gate. If EMA = bull, this is counter-trend → blocked (unless EXREV bypass applies).
- **Bull REV at HIGH level** = price hit resistance and bounced up. Unusual pattern. May be rare.

The EXREV bypass (Change 3) handles the counter-EMA case at HIGH levels naturally.

### Implementation
1. Remove PM H, Yest H, ORB H, Week H from BRK raw detection section
2. Add them to REV raw detection section (using inline detection like PD Mid, or existing `bullRev`/`bearRev` helpers)
3. Move from `anyBull`/`anyBear` to `anyRevBull`/`anyRevBear`
4. Move text from BRK text section to REV text section (with `~ ` prefix)
5. Update BRK and REV count expressions
6. Keep LOW levels (PM L, Yest L, ORB L, Week L) as BRK — these are true barriers

**Lines:** ~40

---

## Implementation Order & Validation

| Step | Change | After: Regression Check |
|------|--------|------------------------|
| 1 | ORB L bull REV suppress | Signal count, win rate per type |
| 2 | 4 midday levels | New signals fire correctly, existing unchanged |
| 3 | EXREV bypass | Bear REV count increases, bull unchanged |
| 4 | FADE resurrection | FADE signals appear, existing unchanged |
| 5 | HIGH→REV reassignment | Full regression: all signal types, levels, directions |
| Final | Bump to v3.2 | Full backtest vs enriched-signals.csv |

### Validation Protocol (from KLB_GUIDELINES.md)
Each change must pass:
1. Backtest — net positive ATR
2. Regression — existing signals not degraded
3. Cross-symbol — works across multiple symbols
4. Side-effect scan — cascade through EMA gate, candle filter, CONF, BAIL
5. Document the result

---

## Files Affected

| File | Changes |
|------|---------|
| `KeyLevelBreakout.pine` | All 5 changes (~170 lines) |
| `KLB_Reference.md` | New levels, EXREV, FADE, HIGH→REV |
| `KLB_PLAYBOOK.md` | Updated signal catalog, level rankings |
| `KLB_DESIGN-JOURNAL.md` | v3.2 section |
| `debug/_toinvestigate.md` | Mark items done |
| `MEMORY.md` | v3.2 features |

---

## Dead Ends (from research — do NOT implement)

- Cross-symbol momentum filter (0.11 ATR follow-through)
- Ungating RNG time filter (vol compression too rare midday)
- Trend continuation signals (0% hit rate)
- Multi-day highs/lows (too rare, overlap existing)
- Bull EXREV (40% win, negative P&L)
