# Session Handover — 2026-03-18

## What Was Done

### 1. TSLA Research Extensions
- **VIX 1d extension** (254 days): Confirmed VIX moderate (18–25) = best regime (+$2.66, 12% worst). Corrected: VIX ≤15 is the real danger (44% worst), not >25. Fear regime is neutral.
- **SPY/QQQ PM trend** (234 days): Mostly noise for TSLA. One signal: **Triple PM alignment × 5m HOLD = 80% win, 8% worst**.
- Updated `debug/tsla-open-scalp-findings-2026-03-17.md` with both extensions.
- Scripts: `debug/tsla_vix1d_extension.py`, `debug/tsla_pm_spy_qqq.py`

### 2. TSLA Open Scalper Indicator (NEW)
Built a complete Pine Script v6 indicator: `TSLA_OpenScalper.pine` (v1.1k)

**State machine (8 states):**
- 0 SLEEP → 1 PRE-SCAN (9:20–9:29) → 2 OPENING (9:30) → 3 FAKEOUT → 4 ORB BUILD (9:31–9:33) → 5 ORB WATCH (9:34+) → 6 BREAKOUT → 7 DONE

**Key features:**
- Pre-open confidence scoring (5 checks + 3 hard kills → HIGH/MED/LOW/NO-GO tier)
- ORB-based breakout (v1.1 replaced the fixed-time 5m BAIL that exited at worst moments)
- Dip buy entry: shakeout bars use bar_low + 15% as entry, SL below turning point
- 5m rule demoted to table info only (ORB breakout is the primary signal)
- Fakeout/shakeout/chaotic detection from 1m bar patterns (30s not available)
- Corner table (top-right, visible through RTH)
- Background colors (green/yellow/red per state)
- Alerts (`alert()` with dynamic messages)
- Pine Logs (`[SCALP] TSLA 9:29 PRE-SCAN tier=MED conf=3/5 checks=11010 ...`)
- SL hit detection during ORB build/watch

**Files created:**
- `TSLA_OpenScalper.pine` — the indicator
- `TSLA_OpenScalper.md` — reference doc
- `TSLA_OpenScalper_TV.md` — TradingView publish description
- `docs/plans/2026-03-18-tsla-open-scalper-design.md` — spec
- `docs/plans/2026-03-18-tsla-open-scalper-plan.md` — implementation plan

### 3. Data Inventory Update
TSLA 15s data is much richer than initially reported:
- **251 days** (Mar 2025–Mar 2026), **540,992 bars**
- **Full 4:00–16:00 coverage** — 2,880 bars/day, 240/hour, zero gaps
- Complete premarket 4:00–9:29 at 15s resolution for the ENTIRE period
- This was previously incorrectly reported as "30 days, 9:00–9:29 only"

## Branch & Commits
- **Branch:** `autoklb/v38-realdata` (pushed to GitHub)
- Key commits:
  - `20af633` v1.1k — comprehensive Pine Logs
  - `958e8aa` v1.1h — correct 5m timing at 9:34
  - `9cafbe8` v1.1 — ORB-based breakout
  - `2136f4c` research extensions + design docs

## What's Next

### Immediate (v1.2)
1. **Smarter SL** — use ORB low as dynamic SL instead of fixed $2.00. Research optimal SL using 15s data (251 days available).
2. **Minimum ORB width filter** — skip trade if ORB range too narrow (noise breakouts).
3. **15s PM analysis** — run the full Module P research at 15s resolution now that 251 days are available.

### Later
4. **ATR-normalized thresholds** for multi-ticker support (v2.0)
5. **Put signal** on bear breakout (research R14: 62% win)
6. **Options P&L estimation** panel

## Pine Script Gotchas Found This Session
- `time()` session string `"0930-0930"` wraps to 24h — use `hour()`/`minute()` instead
- `request.security_lower_tf` not available on all plans (30s data)
- `isPremarket` session `"0400-0929"` excludes the 9:29 bar — use `hm <= 929`
- Tables show state of LAST processed bar — don't `table.clear()` after active window
- Labels on same bar at `low` overlap — merge into one combined label
- `var` declarations inside `if` blocks don't persist — declare at top level

## Version History
v1.0 → v1.0a (time fix) → v1.0b (shakeout) → v1.0c (session fix) → v1.0d (line colors) → v1.1 (ORB rework) → v1.1a-k (refinements, logging)
