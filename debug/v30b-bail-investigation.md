# v3.0b BAIL Investigation — Is the 5-Minute Check Too Aggressive?

**Date:** 2026-03-06
**Data:** 231 confirmed signals matched to IB 1m data (from 1841 total)
**Period:** 2026-01-20 to 2026-02-27

## Executive Summary

The current BAIL threshold (**pnl > 0.05 ATR at 5m**) exits **149/231** (65%) of confirmed signals.
Of those BAILed signals, **82/129** (64%) would have been profitable at 30 minutes.

| Metric | Value |
|--------|-------|
| Net PnL with current BAIL | **13.1 ATR** |
| Net PnL without any BAIL | **23.7 ATR** |
| BAIL value-add | **-10.6 ATR** |
| Best threshold found | **-0.10 ATR** → 22.4 ATR |

**Verdict:** BAIL is net negative — it cuts too many winners. The threshold needs adjustment.

## 1. Current BAIL Mechanics (Pine Code)

```
Threshold: pnl > 0.05 ATR
Timing: 1 signal bar after CONF pass (~5 min on 5m TF)
PnL calc: (close - entry) / dailyATR for bulls, inverse for bears
HOLD: pnl > 0.05 → add '5m✓' to label
BAIL: pnl <= 0.05 → add '5m✗' to label
```

## 2. HOLD vs BAIL Performance

### HOLD Signals
- **N = 80**, avg PnL at 30m: **0.209 ATR**
- Total PnL: **16.7 ATR**
- Win rate (30m): **88.8%**
- Avg MFE (30m): **0.347 ATR**

### BAIL Signals (Counterfactual)
- **N = 129**
- PnL at exit (5m): avg **-0.026 ATR**, total **-3.6 ATR**
- If held to 30m: avg **0.054 ATR**, total **7.0 ATR**
- Would have won at 30m: **82/129 (63.6%)**
- Would have won at 60m: **87/118 (73.7%)**
- MFE rest-of-day: avg **0.435 ATR** (the move was there)

## 3. Threshold Optimization

| Threshold | HOLD% | BAIL% | Net PnL | No-BAIL PnL | Value Add | BAIL→Win% |
|-----------|-------|-------|---------|-------------|-----------|-----------|
|  **-0.10** | 88% | 12% | 22.4 | 23.7 | -1.3 | 44% |
| -0.05 | 78% | 22% | 21.6 | 23.7 | -2.1 | 46% |
| 0.00 | 63% | 37% | 19.4 | 23.7 | -4.3 | 54% |
| 0.02 | 54% | 46% | 16.4 | 23.7 | -7.3 | 61% |
| 0.05 ← current | 35% | 65% | 13.1 | 23.7 | -10.6 | 64% |
| 0.08 | 26% | 74% | 12.2 | 23.7 | -11.6 | 66% |
| 0.10 | 19% | 81% | 11.2 | 23.7 | -12.5 | 67% |
| 0.15 | 11% | 89% | 8.8 | 23.7 | -14.9 | 70% |
| 0.20 | 7% | 93% | 8.8 | 23.7 | -15.0 | 71% |

## 4. Trending vs Choppy Days

### Trending Up (N=71)
- BAIL rate: **59%** (42/71)
- Net PnL with BAIL: **4.8 ATR**
- BAILed → would win at 30m: **16/35 (46%)**
- BAILed counterfactual PnL: **0.6 ATR**
- **With-trend signals:** 49, BAIL rate 51%
  - BAILed with-trend → would win: **12/24 (50%)**
  - Counterfactual avg: **0.068 ATR**

### Trending Down (N=65)
- BAIL rate: **66%** (43/65)
- Net PnL with BAIL: **4.8 ATR**
- BAILed → would win at 30m: **24/37 (65%)**
- BAILed counterfactual PnL: **2.6 ATR**
- **With-trend signals:** 63, BAIL rate 68%
  - BAILed with-trend → would win: **24/37 (65%)**
  - Counterfactual avg: **0.072 ATR**

### Choppy (N=41)
- BAIL rate: **71%** (29/41)
- Net PnL with BAIL: **0.2 ATR**
- BAILed → would win at 30m: **15/24 (62%)**
- BAILed counterfactual PnL: **-0.4 ATR**

### Mixed (N=54)
- BAIL rate: **65%** (35/54)
- Net PnL with BAIL: **3.4 ATR**
- BAILed → would win at 30m: **27/33 (82%)**
- BAILed counterfactual PnL: **4.2 ATR**

## 5. Direction-Aware BAIL Scenarios

| Scenario | HOLD | BAIL | Net PnL | Trending PnL | Choppy PnL |
|----------|------|------|---------|--------------|------------|
| Current (0.05 all) | 82 | 149 | **13.1** | 9.6 | 0.2 |
| Dir-aware (0.00/0.05) | 136 | 95 | **19.6** | 13.4 | 0.4 |
| Dir-aware (-0.05/0.05) | 165 | 66 | **21.6** | 13.8 | 1.0 |
| Trend-day (-0.05/0.05) | 140 | 91 | **17.3** | 13.8 | 0.2 |

## 6. Time-of-Day Analysis

| Time Bucket | N | BAIL% | Net PnL | BAIL→Win% |
|-------------|---|-------|---------|-----------|
| 9:30-10:00 | 112 | 59% | 8.0 | 62% |
| 11:00-12:00 | 10 | 60% | 1.5 | 83% |

## 7. EMA Alignment and BAIL

### EMA Aligned (N=209)
- BAIL rate: **63%**
- Net PnL: **13.5 ATR**
- BAILed → would win: **72 (64%)**

### Not EMA Aligned (N=22)
- BAIL rate: **82%**
- Net PnL: **-0.4 ATR**
- BAILed → would win: **10 (59%)**

## 8. Alternative Check Timing

| Check At | HOLD | BAIL | HOLD% | Net PnL | BAIL→Win% |
|----------|------|------|-------|---------|-----------|
| 5m check | 82 | 149 | 35% | **13.1** | 64% |
| 10m check | 106 | 125 | 46% | **18.6** | 52% |
| 15m check | 124 | 107 | 54% | **20.7** | 45% |

## Recommendations

### 1. Adjust Threshold to -0.10 ATR
- Improvement: **+9.3 ATR** over current threshold
- HOLD rate goes from 35% to 88%

### 2. Direction-Aware BAIL: Dir-aware (-0.05/0.05)
- Net PnL: **21.6 ATR** vs current 13.1 ATR
- Improvement: **+8.5 ATR**

### 3. Check at 15m check instead of 5m
- Net PnL: **20.7 ATR** vs current 13.1 ATR

### Bottom Line

The BAIL system is **net negative by -10.6 ATR** — it cuts too many winners. The March 5 observation was NOT an anomaly; it is the systemic pattern.

**Root cause:** The 0.05 ATR threshold is too tight for 5-minute checks. After CONF pass, 64% of signals show a temporary pullback before continuing in the correct direction. The BAIL check catches these pullbacks and exits prematurely.

**Key numbers:**
- 64% of BAILed signals would have been profitable at 30 minutes
- 74% would have been profitable at 60 minutes
- Average rest-of-day MFE for BAILed signals: 0.435 ATR (the move WAS there)

**Ranked recommendations (pick ONE):**

| Rank | Change | Net PnL | Gain vs Current | Complexity |
|------|--------|---------|-----------------|------------|
| 1 | **Kill BAIL entirely** | 23.7 ATR | +10.6 ATR | Simplest — delete ~30 lines |
| 2 | **Lower to -0.10 ATR** | 22.4 ATR | +9.3 ATR | Just change threshold |
| 3 | **Dir-aware -0.05/0.05** | 21.6 ATR | +8.5 ATR | Moderate — needs trend detection |
| 4 | **Check at 15m instead** | 20.7 ATR | +7.6 ATR | Change checkpoint timing |

**Recommendation: Kill the BAIL system.** It was designed for a world where CONF pass signals could still be garbage. But with v3.0's EMA Hard Gate + Auto-Confirm R1, CONF pass signals are already high quality (89% win rate when HOLDing). The 5m check is second-guessing what is already a strong filter stack.

If removing BAIL entirely feels too aggressive, option 2 (threshold = -0.10 ATR) captures 95% of the benefit while still providing a safety net for the worst cases.
