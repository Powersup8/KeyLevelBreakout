# FADE Resurrection Research

**Date:** 2026-03-06
**Source:** 1841 signals from enriched-signals.csv (Jan 20 - Feb 27 2026, 13 symbols, 28 days)
**Method:** For each signal, check if price closes back through the level within 6 bars (30 min on 5m). If yes, a FADE fires in the opposite direction.
**Outcome measurement:** MFE/MAE in ATR multiples over 30 min and 60 min after FADE fires.

## Executive Summary

**Unfiltered FADE is a coin flip.** 1284 of 1841 signals (70%) had price cross back through the level within 30 min, but the raw FADE signal is net zero (-0.001 ATR/signal). This makes sense -- most levels are contested and price oscillates around them.

**EMA-aligned FADE has a real edge.** When the FADE direction aligns with the EMA (i.e., the original signal was counter-EMA and got rejected), the FADE is net positive: +0.024 ATR/signal, 52.9% win rate, +7.8 total ATR, positive in 9/13 symbols.

**The strongest filter is CONF failure + EMA-aligned FADE:** +0.064 ATR/signal, N=120, positive in 10/13 symbols. But this filter is destroyed by v3.1's auto-confirm (which makes CONF failures rare).

**The new definition preserving the edge without CONF dependency is: FADE fires when a counter-EMA original signal gets rejected (price crosses back within 6 bars).** This works in v3.1 because it only requires knowing the original signal's EMA alignment, not its CONF outcome.

---

## 1. Raw FADE: All Crossbacks Within 30 Min

| Metric | Value |
|--------|-------|
| Total signals | 1841 |
| Signals with crossback ≤ 6 bars | 1284 (70%) |
| Mean MFE (30m) | 0.173 ATR |
| Mean MAE (30m) | -0.174 ATR |
| **Net (30m)** | **-0.001 ATR** |
| Win rate (30m) | 49.1% |
| Total ATR | -1.3 |

**Verdict:** Essentially random. Not tradeable without filters.

## 2. The Key Split: Original Signal EMA Alignment

The critical insight: when the ORIGINAL signal was counter-EMA, it was fighting the trend. The crossback means the trend reasserted itself -- the FADE captures this reversion.

| Original EMA | FADEs | FADE Net 30m | FADE Win% | Total ATR | Interpretation |
|-------------|-------|-------------|-----------|-----------|----------------|
| Counter-EMA (FADE = with EMA) | 327 | **+0.024** | **52.9%** | **+7.8** | Trend reasserts -- TRADEABLE |
| With-EMA (FADE = counter EMA) | 872 | -0.010 | 47.4% | -9.0 | Fading the trend -- LOSERS |
| Mixed EMA | 85 | -0.025 | 48.2% | -2.1 | Noise |

**This is the entire edge.** Fading counter-EMA signals = going with the EMA trend after a fake breakout.

## 3. EMA-Aligned FADE by Symbol

| Symbol | FADEs | Net 30m | Win% | Total ATR |
|--------|-------|---------|------|-----------|
| AAPL | 22 | -0.100 | 36% | -2.2 |
| AMD | 26 | +0.034 | 50% | +0.9 |
| AMZN | 22 | -0.029 | 55% | -0.6 |
| GLD | 28 | **+0.110** | **82%** | +3.1 |
| GOOGL | 23 | +0.045 | 43% | +1.0 |
| META | 27 | +0.084 | 63% | +2.3 |
| MSFT | 19 | +0.092 | 63% | +1.7 |
| NVDA | 27 | -0.039 | 48% | -1.1 |
| QQQ | 27 | +0.086 | 59% | +2.3 |
| SLV | 27 | +0.040 | 52% | +1.1 |
| SPY | 30 | +0.020 | 47% | +0.6 |
| TSLA | 18 | +0.083 | 50% | +1.5 |
| TSM | 31 | -0.090 | 39% | -2.8 |

**Positive: 9/13 symbols** (AAPL, AMZN, NVDA, TSM are negative)
**GLD is standout:** 82% win rate, +0.110 ATR/signal

## 4. Old FADE (CONF ✗) vs New FADE

| Definition | N | Net 30m | Win% | Total ATR | v3.1 compatible? |
|-----------|---|---------|------|-----------|-----------------|
| Old: CONF ✗ only | 563 | +0.010 | 49.9% | +5.8 | NO (auto-confirm kills it) |
| Old + EMA aligned | 120 | +0.064 | 57.8% | +7.7 | NO |
| **New: Counter-EMA crossback** | **327** | **+0.024** | **52.9%** | **+7.8** | **YES** |
| New + crossback ≤2 bars | 297 | +0.024 | 53.2% | +7.0 | YES |

**The new definition captures MORE total ATR (+7.8 vs +5.8) while being v3.1 compatible.**

## 5. Crossback Speed

| Crossback Bars | Count | Net 30m | Win% |
|----------------|-------|---------|------|
| 1 (immediate) | 793 | -0.002 | 50.3% |
| 2 (10 min) | 147 | +0.028 | 49.7% |
| 3 (15 min) | 70 | -0.029 | 42.9% |
| 4 (20 min) | 46 | -0.040 | 34.8% |
| 5 (25 min) | 43 | +0.036 | 53.5% |
| 6 (30 min) | 30 | -0.046 | 43.3% |

Bar 1-2 crossbacks dominate (940/1284 = 73%). The fastest rejections are slightly better but not dramatically so. Restricting to ≤2 bars doesn't meaningfully improve the filter beyond EMA alignment.

## 6. Time of Day

| Time Bucket | EMA-Aligned FADEs | Net 30m | Win% |
|-------------|-------------------|---------|------|
| Morning (9:30-10:30) | 314 | +0.022 | 52.5% |
| Midday (11:00-13:00) | 2 | -0.025 | 50.0% |
| Afternoon (13:00-16:00) | 11 | +0.079 | 63.6% |

Nearly all EMA-aligned FADEs fire in the morning (96%). This makes sense: most KLB signals fire in the morning, so most FADEs do too.

## 7. By FADE Direction

| FADE Dir | Count | MFE 30m | MAE 30m | Net 30m | Win% | MFE 60m | Net 60m |
|----------|-------|---------|---------|---------|------|---------|---------|
| Bull FADE | 580 | 0.162 | -0.180 | -0.018 | 49.1% | 0.216 | -0.024 |
| Bear FADE | 549 | 0.184 | -0.167 | +0.016 | 49.0% | 0.246 | +0.030 |

Bear FADEs have a slight edge overall (consistent with the known bear > bull finding in KLB).

## 8. By Level Type

| Level | FADEs | Net 30m | Win% |
|-------|-------|---------|------|
| ORB H | 229 | +0.004 | 49.8% |
| ORB L | 199 | +0.020 | 50.8% |
| PM L | 135 | -0.006 | 45.9% |
| PM H | 99 | -0.012 | 53.5% |
| Yest L | 81 | +0.004 | 53.1% |
| PM H+ORB H | 47 | +0.018 | 57.4% |
| Week H | 37 | -0.042 | 40.5% |
| Week L | 39 | -0.030 | 43.6% |

ORB levels and PM H+ORB H (multi-level) are the best for FADEs. Weekly levels are the worst (wider ranges, less likely to revert).

## 9. By Original Signal Type

| Orig Type | FADEs | Net 30m | Win% |
|-----------|-------|---------|------|
| BRK | 677 | -0.001 | 47.6% |
| REV | 452 | -0.001 | 51.3% |

No difference between BRK and REV originals for raw FADE. Both are zero.

## 10. Filter Combinations (Ranked)

| Filter | N | Net 30m | Win% | Total ATR | Multi-Symbol? |
|--------|---|---------|------|-----------|--------------|
| CONF ✗ + EMA aligned | 120 | +0.064 | 57.8% | +7.7 | 10/13 pos |
| BRK + EMA aligned | 136 | +0.047 | 56.6% | +6.4 | 10/13 pos |
| Crossback ≤2 + EMA | 297 | +0.024 | 53.2% | +7.0 | 9/13 pos |
| **EMA aligned (all)** | **327** | **+0.024** | **52.9%** | **+7.8** | **9/13 pos** |
| Morning only | 857 | +0.008 | 50.1% | +6.9 | - |
| All FADEs | 1284 | -0.001 | 49.1% | -1.3 | 7/13 pos |

## 11. Original Signals That Became FADEs

Signals that trigger FADEs are genuinely weak originals:

| Metric | FADE Originals | All Signals |
|--------|---------------|-------------|
| MFE | 0.154 ATR | 0.253 ATR |
| MAE | -0.275 ATR | -0.215 ATR |
| Net | **-0.120 ATR** | +0.038 ATR |

FADE originals have 39% less favorable excursion and 28% more adverse excursion. They are demonstrably failed signals.

## 12. Key Conclusions

### Is the new FADE definition net positive?
**Yes, with the EMA filter.** Counter-EMA crossback FADE: +0.024 ATR/signal, +7.8 total ATR, 52.9% win rate.

### How many signals vs old 79?
- **327 EMA-aligned FADEs** (4x the old 79 from v3.0b)
- **~12 per symbol over 28 days** (~0.4 per symbol per day)

### Does it work across symbols?
**Yes: 9/13 positive.** The 4 negative symbols (AAPL, AMZN, NVDA, TSM) are individually small losses. No single symbol dominates the edge.

### Best time window?
**Immediate crossback (1-2 bars)** is most common. No strong signal from crossback speed after EMA filtering.

### Should FADE only fire at specific level types?
**ORB levels are slightly better**, but the EMA filter matters more than level type. Multi-levels (PM H+ORB H) at 57.4% win rate are promising but N is small.

## 13. Recommended Implementation

**FADE Definition for v3.1:**
1. Any signal fires (BRK or REV, any CONF status)
2. The original signal was **counter-EMA** (bull signal when EMA=bear, or bear when EMA=bull)
3. Price closes back through the level within 6 bars (30 min on 5m)
4. FADE fires in the **opposite direction** of the original signal (= with the EMA trend)

**This captures 327 signals over 28 days = ~12/day across 13 symbols, net +7.8 ATR.**

**No dependency on CONF status** -- works identically under v3.1's auto-confirm.

### Comparison to v3.0b FADE
| Aspect | v3.0b FADE | New FADE |
|--------|-----------|----------|
| Trigger | CONF ✗ required | Counter-EMA crossback |
| v3.1 compatible | NO | YES |
| Total signals (28d) | 79 | 327 |
| Per-signal edge | ~0.064 ATR | +0.024 ATR |
| Total edge | ~5 ATR | +7.8 ATR |
| Multi-symbol | unknown | 9/13 positive |

The new definition has lower per-signal edge but 4x more signals, yielding 56% more total ATR.
