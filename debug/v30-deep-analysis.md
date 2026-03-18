# v3.0 Deep Analysis — Pine Log Cross-Check

**Date:** 2026-03-05
**Data:** 8 v3.0 pine log exports (8 symbols, 27 days), 10sec IB parquet for follow-through
**Symbols with FT data:** AAPL, AMD, AMZN (Jan 28+), MSFT, NVDA, QQQ, SPY, TSLA (Feb 26+)

---

## Executive Summary

v3.0 signals are **near breakeven** at 15m (+0.0 ATR, 50.5% win, N=414). EMA gate and Auto-Confirm R1 work correctly. **One critical bug found: RNG signals can never fire** due to an off-by-one in the range computation. FADE fires very rarely (1 of 26 opportunities). New levels fire but show slightly negative P&L (small N).

---

## Bug Report

### BUG #1: RNG IMPOSSIBLE — NEVER FIRES (Critical)

**Impact:** Zero RNG signals. Expected ~1.5/day/symbol based on BATS data analysis.

**Root cause:** The 12-bar range INCLUDES the signal bar:
```pine
[rngH12, rngL12] = request.security(..., [ta.highest(high, 13)[1], ta.lowest(low, 13)[1]], ...)
```
- `rngH12 = ta.highest(high, 13)[1]` = highest high of bars [1..13]
- `sigC = close[1]` = close of bar [1]
- Since `high[1] >= close[1]` always, and `rngH12 >= high[1]`: **sigC > rngH12 is mathematically impossible**

**Fix:**
```pine
[rngH12, rngL12] = request.security(syminfo.tickerid, i_signalTF,
     [ta.highest(high, 12)[2], ta.lowest(low, 12)[2]], lookahead = barmerge.lookahead_on)
```
This gives the 12-bar range of bars [2..13] — PRIOR to the signal bar.

### BUG #2: FADE Fires Rarely (Minor)

1 FADE from 26 CONF failures (3.8% rate). AAPL 2026-02-11 15:05.

**Root cause:** Not a code bug — conditions are legitimately strict:
- Price must cross BACK through level + breakBuf within 30 min of failure
- Most failures are afternoon → market doesn't reverse strongly
- EMA gate further restricts

**Consider:** Widening window from 30 min to 60 min, or dropping breakBuf for FADE.

---

## Feature Verification

| Feature | Status | Notes |
|---------|--------|-------|
| EMA Hard Gate | ✅ Working | 0 non-EMA signals after 9:50. 96 pre-9:50 dimmed correctly |
| Auto-Confirm R1 | ✅ Working | 284/325 CONFs (87%). All ✓. |
| New Levels (PD Mid) | ✅ Firing | 58 signals |
| New Levels (PD LH L) | ✅ Firing | 80 signals |
| New Levels (VWAP zone) | ✅ Firing | 168 signals |
| FADE | ⚠️ Rare | 1 signal total. Working but strict conditions. |
| RNG | ❌ Bug | 0 signals. Impossible condition. |
| ✓★ | ✅ Working | 1 auto-promote ✓★. Rare because Auto-R1 handles 87% |
| Regime Score R0/R1/R2 | ✅ Working | R2=352, R1=62 in FT data |
| Kill MC | ✅ Clean | Zero MC references in logs |

---

## Performance (N=414 signals with 10sec follow-through)

### Overall
| Window | MFE | MAE | PnL | Win% | Total ATR |
|--------|-----|-----|-----|------|-----------|
| 5m | 0.087 | 0.094 | -0.009 | 50.2% | -3.7 |
| 15m | 0.139 | 0.147 | -0.000 | 50.5% | -0.2 |
| 30m | 0.195 | 0.186 | +0.019 | 51.2% | +7.9 |
| 60m | 0.260 | 0.227 | +0.033 | 54.1% | +13.8 |

### By Signal Type
| Type | N | 15m PnL | Win% | Total |
|------|---|---------|------|-------|
| BRK | 171 | +0.011 | 50.3% | +1.8 |
| REV | 242 | -0.008 | 50.8% | -1.9 |
| RCL | 1 | -0.025 | 0% | -0.0 |

### By Level (Original vs New)
| Level | N | 15m PnL | Win% | Total |
|-------|---|---------|------|-------|
| Yesterday | 98 | **+0.049** | **64.3%** | +4.8 |
| Week | 48 | -0.001 | 52.1% | -0.0 |
| Premarket | 97 | -0.007 | 45.4% | -0.7 |
| ORB | 117 | -0.013 | 47.0% | -1.5 |
| **PD Mid** | 35 | **-0.036** | 42.9% | -1.2 |
| **PD Last Hr Low** | 39 | **-0.056** | 41.0% | -2.2 |
| **VWAP zone** | 83 | -0.017 | 48.2% | -1.4 |

### By Time
| Bucket | N | 15m PnL | Win% | Total |
|--------|---|---------|------|-------|
| 9:30-10 | 234 | -0.014 | 47.0% | -3.2 |
| **10-11** | **75** | **+0.027** | **61.3%** | **+2.1** |
| 11-12 | 21 | -0.002 | 42.9% | -0.0 |
| 12+ | 84 | +0.013 | 52.4% | +1.1 |

### By Symbol
| Symbol | N | 15m PnL | Win% | Total |
|--------|---|---------|------|-------|
| **SPY** | **24** | **+0.061** | **79.2%** | **+1.5** |
| QQQ | 25 | +0.035 | 56.0% | +0.9 |
| AAPL | 105 | +0.011 | 50.5% | +1.1 |
| NVDA | 21 | +0.002 | 52.4% | +0.0 |
| MSFT | 17 | -0.006 | 47.1% | -0.1 |
| AMZN | 102 | -0.010 | 46.1% | -1.0 |
| TSLA | 23 | -0.016 | 56.5% | -0.4 |
| AMD | 97 | -0.023 | 45.4% | -2.2 |

### By Volume
| Bucket | N | 15m PnL | Win% |
|--------|---|---------|------|
| **1.5-3x** | **121** | **+0.019** | **58.7%** |
| 10x+ | 64 | +0.032 | 54.7% |
| <1.5x | 81 | +0.006 | 51.9% |
| 5-10x | 73 | -0.014 | 43.8% |
| 3-5x | 75 | -0.053 | 38.7% |

### Key Filters
| Filter | N | 15m PnL | Win% |
|--------|---|---------|------|
| EMA-Aligned | 358 | +0.001 | 50.8% |
| EMA-Misaligned | 56 | -0.012 | 48.2% |
| Regime R2 | 352 | -0.002 | 50.3% |
| Regime R1 | 62 | +0.008 | 51.6% |
| R1 Bull | 36 | +0.001 | 50.0% |
| R1 Bear | 26 | +0.018 | 53.8% |
| ADX 40+ | 53 | **+0.041** | **60.4%** |
| ADX 20-30 | 234 | -0.008 | 47.0% |

### 5-Minute Check Validation
| Check | N | 30m PnL | 30m Win% |
|-------|---|---------|----------|
| **HOLD** | **148** | **+0.121** | **70.9%** |
| BAIL | 321 | +0.009 | 48.9% |

### CONF Analysis
- Total: 325 CONFs
- Auto-R1: 284 (87%) — all ✓
- Standard: 41 → 15 ✓ (37%), 26 ✗ (63%)
- Auto-R1 follow-through: N=167, +0.012/sig, 50.9% win

---

## Key Observations

### What's Working
1. **5m HOLD/BAIL filter** — 70.9% vs 48.9% win. This is the strongest real-time filter.
2. **EMA gate** — Clean suppression, no leaks
3. **Yesterday levels** — Best level type (64.3% win, +0.049)
4. **10-11 AM window** — Best time (61.3% win)
5. **ADX 40+** — Best trend strength (60.4% win)
6. **SPY** — Best symbol (79.2% win, though N=24)

### What's Not Working
1. **RNG** — Zero signals (bug)
2. **FADE** — 1 signal (too strict)
3. **New levels** — All net negative (PD Mid -0.036, PD LH -0.056, VWAP -0.017)
4. **Overall P&L** — Near zero at 15m. System is not generating alpha.
5. **Volume 3-5x** — Worst bucket (-0.053, 38.7% win)
6. **Morning 9:30-10** — Slightly negative (-0.014, 47%)

### Surprises
- **R1 is not strongly negative** (unlike the 1841-signal backtest). R1 Bull +0.001 (was -0.176 in backtest). Small sample may explain.
- **10x+ volume positive** (+0.032) — contradicts "exhaustion" narrative
- **12:00+ slightly positive** (+0.013, 52.4%) — afternoon isn't dead with new levels

---

## Recommended Changes

### Immediate Fixes
1. **Fix RNG bug** — `[ta.highest(high, 12)[2], ta.lowest(low, 12)[2]]`
2. **Re-export pine logs** after fix to validate RNG signals

### Tuning Candidates (need more data)
3. **FADE window** — 30 min → 60 min (or drop breakBuf for FADE)
4. **Volume 3-5x** — Consider dimming (worst bucket)
5. **New levels** — Monitor with larger sample before removing. PD Last Hr Low is worst (-0.056).

### Data Limitations
- Only 414/801 signals have follow-through (10sec data coverage)
- 5 of 8 symbols only have 5 trading days of 10sec data (Feb 26 - Mar 4)
- Missing: GOOGL, META, GLD, SLV, TSM (no pine logs yet)
- Need more pine log exports across all 13 symbols for robust conclusions
