# v3.0b Deep Analysis — FADE/RNG Fixes Validated

**Date:** 2026-03-05
**Data:** 8 v3.0b pine logs (8 symbols, 27 days), 10sec IB parquet for follow-through
**Symbols:** AAPL, AMD, AMZN, META, NVDA, QQQ, SPY, TSLA

---

## Executive Summary

v3.0b fixes are **working**. FADE went from 1 signal to 26 (70% win). RNG morning-only filter correctly suppresses afternoon noise (100% before 11:00). The system is now **net positive** across all timeframes (+14.6 ATR at 30m, +23.6 at 60m over 27 days). **New levels remain the drag** — all three are negative and cost ~3.8 ATR. The best tradeable set is CONF ✓ + HOLD at 83% win.

---

## v3.0b Fix Validation

### FADE — Fixed (was 1 signal, now 26)

| Metric | v3.0 | v3.0b | Change |
|--------|------|-------|--------|
| Total signals | 1 | 26 | +2500% |
| With follow-through | 0 | 10 | — |
| 15m Win% | N/A | **70%** | Best signal type |
| 15m PnL/signal | N/A | **+0.059** | Strong |
| 30m PnL/signal | N/A | **+0.080** | Growing |

Fixes that worked:
- Removed EMA gate (was blocking 97% — FADE is contrarian)
- Widened window 30→60 min (fades develop slower)
- Dropped breakBuf (unnecessary strictness)

### RNG — Morning-Only Working

| Metric | v3.0 | v3.0a | v3.0b | Change |
|--------|------|-------|-------|--------|
| Total signals | 0 | 262 | 213 | Fixed + filtered |
| Morning (<11) | — | 85% | **100%** | Filter working |
| After 11 | — | 15% | **0%** | Suppressed |
| 15m PnL | — | -0.079 | **+0.034** | Now positive |
| 30m PnL | — | +0.273 | **+0.068** | Positive |
| 60m PnL | — | +0.439 | **+0.113** | Strong at 65% win |

RNG profile: Starts slow (5m: -0.005), builds momentum (60m: +0.113, 65% win). Classic range-breakout signature.

---

## Overall System Performance (N=521 with FT)

| Window | MFE | MAE | PnL | Win% | Total ATR |
|--------|-----|-----|-----|------|-----------|
| 5m | 0.095 | 0.099 | -0.007 | 49.5% | -3.4 |
| 15m | 0.149 | 0.151 | **+0.007** | 51.1% | **+3.9** |
| 30m | 0.206 | 0.188 | **+0.028** | 53.2% | **+14.6** |
| 60m | 0.278 | 0.232 | **+0.045** | 56.2% | **+23.6** |

**4.9 signals/day/symbol, 38.9 total/day across 8 symbols.**

---

## Quality Tiers

| Tier | Filter | N | 15m Win% | 15m PnL | 30m Win% | 30m Total |
|------|--------|---|----------|---------|----------|-----------|
| **1** | **CONF ✓ + HOLD** | **35** | **83%** | **+0.119** | **77%** | **+3.9** |
| 1a | Tier 1 + orig levels | 31 | **87%** | +0.138 | 81% | +3.8 |
| 2 | CONF ✓ only | 241 | 48% | +0.004 | 52% | +7.4 |
| 3 | HOLD only | 35 | 83% | +0.119 | 77% | +3.9 |
| — | All signals | 521 | 51% | +0.007 | 53% | +14.6 |

**Key insight:** HOLD is the real alpha filter. CONF ✓ alone is near-random, but CONF ✓ + HOLD = 83% win.

### Tier 1 Daily Stats (CONF ✓ + HOLD)
- 2.5 signals/day (14 trading days with signals)
- +0.275 ATR/day average
- Win days: 10/14 (71%)

---

## What's Profitable

| Filter | N | 30m PnL | 30m Win% | Total |
|--------|---|---------|----------|-------|
| **ETFs (SPY+QQQ)** | **59** | **+0.101** | **73%** | **+6.0** |
| **FADE + RNG (new types)** | **104** | **+0.069** | **60%** | **+7.2** |
| **Yesterday levels** | **97** | **+0.048** | **64%** | **+4.6** |
| 10-11 AM + CONF✓ | 58 | +0.048 | 59% | +2.8 |
| Yesterday + CONF✓ + HOLD | 14 | +0.072 | 71% | +1.0 |

---

## What's Not Profitable

| Filter | N | 15m PnL | 15m Win% | Total |
|--------|---|---------|----------|-------|
| **PD Last Hr Low** | **40** | **-0.043** | **42.5%** | **-1.7** |
| **PD Mid** | **36** | **-0.047** | **38.9%** | **-1.7** |
| Volume 3-5x | 74 | -0.050 | 39% | -3.7 |
| VWAP zone | 83 | -0.019 | 49% | -1.6 |
| AMD | 120 | -0.015 | 47% | -1.8 |

### Impact of New Levels
- New levels (standard signals only): N=148, **-3.8 ATR at 15m**
- Without new levels (keep FADE+RNG): N=373, **+7.6 ATR at 15m**
- Dropping new levels nearly doubles 15m profitability (+3.9 → +7.6)

---

## Feature Status

| Feature | Status | Notes |
|---------|--------|-------|
| EMA Hard Gate | ✅ Clean | 0 leaks after 9:50 for standard signals |
| Auto-Confirm R1 | ✅ Working | 286/334 CONFs (86%) |
| FADE | ✅ **Fixed** | 26 signals, 70% win, best type |
| RNG morning-only | ✅ **Working** | 100% before 11:00, positive all TFs |
| CONF 3-bar window | ✅ Working | Standard CONF: 40% pass (19/48) |
| 5m HOLD/BAIL | ✅ Working | HOLD: 77% win 30m vs BAIL: 51% |
| New levels (PD Mid) | ⚠️ Negative | -0.047/signal, 38.9% win |
| New levels (PD LH L) | ⚠️ Negative | -0.043/signal, 42.5% win |
| New levels (VWAP) | ⚠️ Marginal | -0.019/signal, 49.4% win |
| ✓★ auto-promote | ⚠️ 0 signals | May need investigation |

---

## Recommendations

### Keep As-Is
1. **FADE** — 70% win, excellent contrarian signal
2. **RNG morning-only** — positive at all timeframes, 65% win at 60m
3. **EMA gate + Auto-R1** — both working as designed
4. **5m HOLD/BAIL filter** — strongest real-time filter (83% vs 51% win)

### Consider Changing
5. **New levels → DIM or disable** — all three net negative. PD Mid and PD LH L are worst (-0.043 to -0.047). These are costing ~3.8 ATR.
6. **Volume 3-5x → DIM** — consistently worst volume bucket (-0.050, 39% win)
7. **✓★ investigation** — 0 auto-promotes seems low

### Trading Guidance
8. **Best setup:** CONF ✓ + HOLD signals on original levels (87% win, +0.138/signal)
9. **Best symbols:** SPY (79%), QQQ (60%), AAPL (51%)
10. **Best time:** 10-11 AM (59% win), avoid 12-1 PM
11. **New types (FADE+RNG):** 60% win at 30m, +7.2 ATR — keep trading

---

## Data Limitations
- 521/1050 signals have follow-through (10sec coverage)
- 5 of 8 symbols only have 5 trading days of 10sec data (Feb 26 - Mar 4)
- AAPL, AMD, AMZN have 25 days of 10sec (most reliable)
- Missing: GOOGL, GLD, SLV, TSM, MSFT (no pine logs yet)
