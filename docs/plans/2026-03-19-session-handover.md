# Session Handover — 2026-03-19

## What Was Done

### 1. 15s Premarket Research (Module P at high resolution)
- **251 days** of TSLA 15s PM data (4:00–9:30), zero gaps in 9:16–9:30 window
- Script: `debug/tsla_pm_15s_research.py` → `debug/tsla-pm-15s-findings.md`

**Key findings:**
- **2m accel window (9:27→9:29) beats original 4m (9:25→9:29):** +3pp win, -4pp worst, Sharpe 8→11 in combined filter
- **90s window (9:28→9:29) has highest raw correlation** (0.136 vs 0.067 for 2m) but 2m cuts more losers (5% worst vs 11%)
- **PM position timestamp:** 9:29 is fine, no meaningful gain from 9:29:30/9:29:45
- **Path efficiency sweet spot:** Q2 (0.10–0.20) = 81% win, $6.76 avg, 3% worst on HOLD days. "Steady drift with normal wiggles" beats both choppy and straight-line PM
- **1m proxy for path efficiency:** close-to-close efficiency correlates 0.903 with 15s ground truth. Reproduces 80% win in Q2 vs 56% in Q4
- **PM volume mid-range best on HOLD:** upper-mid (82k–128k) = 81% win, 6% worst. Low (<53k) and very high (>129k) both bad

### 2. SL Optimization Research
- Script: `debug/tsla_sl_research.py`

**Key findings:**
- **ORB low beats fixed $2.00 SL dramatically:** Net SL value $175 vs $9
  - ORB low kills 35 losers (saved $283) and only 21 winners (cost $107)
  - Fixed $2 kills 33 losers (saved $251) but also 31 winners (cost $242)
- **Drawdown timing:** 36% of max drawdowns happen during ORB build (9:30–9:34), 51% after 10:30
- **P50 max drawdown in first 10m = $1.29** → fallback SL set to $1.50

### 3. Fakeout Deep Research
- Script: `debug/tsla_fakeout_deep_research.py` → `debug/tsla-fakeout-deep-research.md`
- Used 15s RTH data (137 days with 30s-resolution opening bars)

**Key findings:**
- **Fakeout redefined:** UP→DOWN alone is 42% win (+$0.16 avg) — not catastrophic
- **The real discriminant: bar2 breaks bar1 low**
  - Bar2 held above bar1 low: 48% win, +$1.21, 24% worst — normal pullback
  - Bar2 broke below bar1 low: **27% win, -$2.21, 64% worst** — real trap
- **Volume confirms:** selling dries up = 50% win / +$2.38 vs selling intensifies = 33% / -$2.05
- **ORB is the real decision:** UP→DN + HOLD + Bull break = 67% win, +$5.20
- Today (Mar 18): bar1 low=$399.01, bar2 low=$400.55 → held above → NOT a real fakeout (correctly verified with TV 5s data)

### 4. TSLA Open Scalper v1.2c Built
All changes implemented in `TSLA_OpenScalper.pine`:

| Change | Detail |
|---|---|
| Accel window 4m → 2m | `open_927` → `close_929` (3 bars) |
| P9 hard kill: real 30s accel | `request.security_lower_tf("15S")` on 9:29 bar |
| Fakeout: real 30s patterns | `request.security_lower_tf("30S")` × 4 (OHLC) |
| Fakeout redefined | Only fires if bar2 low < bar1 low (real trap) |
| Fakeout visual downgraded | Orange "FAKEOUT — watch ORB" instead of red "EXIT" |
| Dynamic SL | Fallback $1.50 during ORB build → ORB low after freeze |
| SL line drawn from 9:34 | No stale fallback SL line; fresh line at ORB freeze |
| SL price label updates | Shows "SL 398.06 (ORB)" after freeze |
| SL skip on ORB freeze bar | Prevents self-trigger (orb_low = bar's own low) |
| Min ORB width filter | Skip breakout if ORB range < $1.00 |
| PM volume hard kill | **DISABLED** (default=0) — TV volume ≠ IB volume, needs calibration |
| `request.security_lower_tf` confirmed | Works on user's Premium plan |

**Version history:** v1.2 → v1.2a (SL fix + vol kill disable) → v1.2b (fakeout visual + SL label) → v1.2c (fakeout redefined: bar2 must break bar1 low)

**`request.security` budget:** 3 existing + 5 new = 8 of 40 total

### 5. Full Optimization Sweep
- Script: `debug/tsla_scalp_supervisor.py` + `debug/tsla_scalp_backtest.py`
- 61 experiments, 117 minutes, 9 phases
- Results: `debug/tsla_scalp_results.tsv` + `debug/tsla-scalp-optimization-report.md`

**Key findings:**
- **Fallback SL is the #1 lever:** 54% of trades get stopped during ORB build at $1.50. The 25 trades that survive to HOLD_10 exit are 100% winners at +$4.95 avg
- **Fallback $3.00 has best score (30.3)** — lets more trades survive to ORB
- **Fallback $1.00 has best Sharpe (2.19)** — tighter losses when stopped
- **Hold=3 bars is best** by score (23.7) and Sharpe (1.73) — fast scalp
- **Hold 25+ bars all identical** — after 25 bars, either stopped or done
- **ORB low SL confirmed best** post-ORB (score 16.4 vs fixed $2 at 14.4)
- **Path efficiency (wide) helps slightly:** Sharpe 1.57 vs 1.21
- **ORB width filter:** no effect up to $2 (all TSLA ORBs are wider)

## Open Questions for Next Session

### Priority 1: Fallback SL Decision
The $1.50 fallback kills 54% of trades. Options:
1. **Widen to $3.00** — more winners survive, but larger individual losses
2. **Remove pre-ORB SL entirely** — rely only on ORB low after freeze
3. **Use the 9:30 bar low as SL** — adaptive to opening bar size
4. **Don't enter until ORB freeze** — wait for 9:34, skip the risky first 4 bars

This is the #1 decision that determines system performance.

### Priority 2: Hold Time
Research says 3 bars (3 min after breakout) is optimal. Current default is 10. Should we shorten? Or is 3 bars too fast for options execution?

### Priority 3: PM Volume Calibration
TV premarket volume is ~10-50× lower than IB (TV shows 2k-14k vs IB's 53k+ threshold). Need to collect TV volume data for a few days and find the right threshold. The log already prints `pm_vol=` for this purpose.

### Priority 4: Path Efficiency Implementation
Deferred from v1.2. The 1m proxy works (0.903 corr). Would add as 6th confidence check. Needs bar-by-bar accumulation during 9:20–9:29.

## Branch & Commits
- **Branch:** `autoklb/v38-realdata` (not yet committed — all changes are local)
- Key files changed: `TSLA_OpenScalper.pine` (v1.2c)
- New research scripts in `debug/`:
  - `tsla_pm_15s_research.py` + `tsla-pm-15s-findings.md`
  - `tsla_sl_research.py`
  - `tsla_pm_proxy_test.py`
  - `tsla_fakeout_deep_research.py` + `tsla-fakeout-deep-research.md`
  - `tsla_scalp_backtest.py` + `tsla_scalp_supervisor.py`
  - `tsla_scalp_results.tsv` + `tsla-scalp-optimization-report.md`

## Pine Script Gotchas Found This Session
- `request.security_lower_tf` works on Premium (not just Premium+)
- 15s sub-bars on premarket bars return 4 elements per 1m bar (9:29:00, 9:29:15, 9:29:30, 9:29:45)
- SL at ORB low self-triggers on the freeze bar (bar's low = ORB low by definition) → must skip `is0934`
- `between_time('04:00', '09:29')` excludes 9:29:15+ — use `'09:29:59'` for full coverage
- TV premarket volume is dramatically lower than IB data — don't use IB-calibrated thresholds
- `replace_all` on version strings can damage `//` comment prefixes if the search string appears in them
