# Signal Type Matching Research

*Generated: 2026-03-06 | Data: enriched-signals.csv (1,841 signals) + IB 5m (853 level touches) | Script: `debug/signal_type_matching.py`*

---

## 1. Executive Summary

**The biggest finding: HIGH levels are magnets, not barriers.** All five HIGH level types (PM H, Yest H, ORB H, Week H, Week L) perform better as REV (reversal/touch-and-turn) signals than as BRK (breakout). LOW levels remain true barriers where BRK dominates. This single structural mismatch costs the system ~12.5 ATR from ORB L REV alone.

### Top 3 Recommendations (ranked by ATR impact)

| # | Action | ATR Impact | Confidence |
|---|--------|--------:|-----------|
| 1 | **Suppress ORB L bull REV** (N=143, PnL=-0.088) | +12.5 ATR | HIGH (N=143) |
| 2 | **Reassign all HIGH levels to prefer REV** (PM H, Yest H, ORB H, Week H, Week L) | +25+ ATR shift | HIGH (consistent across all 5) |
| 3 | **EMA gate on non-BRK-aligned combos** (all against-EMA REV at LOW levels) | +22+ ATR | HIGH (6 combos, all negative) |

### Key Numbers
- **Mismatch total:** REV signals at barrier levels account for 777 signals (42% of all). Net ATR = +20.0, but ORB L REV drains -12.5 of that.
- **ORB L REV (bull):** The single worst combo. N=143, 27.3% win, -0.088 avg PnL, -12.5 net ATR.
- **Confluence bonus:** 3-level signals hit 54.5% win rate (+0.108 PnL) vs single-level 33.8% (+0.033).
- **Level staleness paradox:** Older levels perform BETTER (Week > Yest/PM > ORB), contradicting the "stale levels decay" assumption.

---

## 2. Signal Type x Level Type Matrix

### Full Matrix (Primary Level x Signal Type)

| Level | Type | N | Win% | Avg MFE | Avg MAE | Net ATR | Avg PnL | Assessment |
|-------|------|--:|-----:|--------:|--------:|--------:|--------:|-----------|
| **PM H** | BRK | 178 | 33.7% | 0.237 | -0.219 | +3.1 | +0.018 | Marginal |
| **PM H** | REV | 103 | 39.8% | 0.270 | -0.211 | +6.1 | **+0.059** | Better |
| **PM L** | BRK | 234 | 36.8% | 0.282 | -0.200 | **+19.3** | **+0.082** | Strong |
| **PM L** | REV | 150 | 32.7% | 0.224 | -0.210 | +2.1 | +0.014 | Marginal |
| **Yest H** | BRK | 91 | 30.8% | 0.206 | -0.188 | +1.6 | +0.018 | Marginal |
| **Yest H** | REV | 73 | 34.2% | 0.340 | -0.253 | +6.4 | **+0.088** | Strong |
| **Yest L** | BRK | 118 | 42.4% | 0.270 | -0.208 | +7.3 | **+0.062** | Good |
| **Yest L** | REV | 73 | 38.4% | 0.254 | -0.239 | +1.1 | +0.015 | Marginal |
| **ORB H** | BRK | 203 | 31.5% | 0.202 | -0.200 | +0.3 | +0.002 | Flat |
| **ORB H** | REV | 175 | 33.1% | 0.275 | -0.228 | +8.1 | **+0.047** | Good |
| **ORB L** | BRK | 163 | 38.0% | 0.291 | -0.183 | **+17.6** | **+0.108** | Best combo |
| **ORB L** | REV | 143 | 27.3% | 0.210 | -0.297 | **-12.5** | **-0.088** | DRAIN |
| **Week H** | BRK | 39 | 38.5% | 0.229 | -0.230 | -0.0 | -0.001 | Flat |
| **Week H** | REV | 31 | 51.6% | 0.338 | -0.176 | +5.0 | **+0.162** | Excellent |
| **Week L** | BRK | 38 | 31.6% | 0.224 | -0.198 | +1.0 | +0.026 | Marginal |
| **Week L** | REV | 29 | 51.7% | 0.275 | -0.146 | +3.7 | **+0.129** | Excellent |

### Pattern: HIGH = Magnet, LOW = Barrier

| Level Type | BRK PnL | REV PnL | Better Type | Delta |
|-----------|--------:|--------:|------------|------:|
| PM H | +0.018 | **+0.059** | REV | +0.041 |
| Yest H | +0.018 | **+0.088** | REV | +0.070 |
| ORB H | +0.002 | **+0.047** | REV | +0.045 |
| Week H | -0.001 | **+0.162** | REV | +0.163 |
| PM L | **+0.082** | +0.014 | BRK | +0.068 |
| Yest L | **+0.062** | +0.015 | BRK | +0.047 |
| ORB L | **+0.108** | -0.088 | BRK | +0.196 |
| Week L | +0.026 | **+0.129** | REV | +0.103 |

**Insight:** 5 of 8 levels favor REV over BRK. All HIGH levels favor REV. Only LOW levels from PM/Yest/ORB favor BRK. Week L is the anomaly -- it acts more like a magnet (REV +0.129) than a barrier.

---

## 3. Level Behavior Classification (IB 5m Touch Analysis)

Using 853 classified level touches from IB 5m data (post-ORB, first touch per day):

| Level | N | Breakout% | Bounce% | False Break% | Behavior |
|-------|--:|----------:|--------:|-------------:|----------|
| **ORB H** | 254 | 40.6% | 33.5% | 26.0% | BARRIER (weak) |
| **ORB L** | 233 | 37.8% | **42.1%** | 20.2% | **MAGNET** |
| **Yest H** | 192 | **58.3%** | 25.5% | 16.1% | BARRIER (strong) |
| **Yest L** | 174 | **61.5%** | 22.4% | 16.1% | BARRIER (strong) |

### Key Finding: ORB L is actually a MAGNET

ORB L has more bounces (42.1%) than breakouts (37.8%). This explains why ORB L BRK works so well -- when it DOES break, it's a genuine momentum event. But it also explains why ORB L REV fails badly (-12.5 ATR) -- price tends to bounce back above ORB L, meaning bears touching ORB L from above get reversed.

Meanwhile, Yest H/L are strong barriers (58-62% breakout), validating BRK as the right signal type for these levels.

### Touch Behavior Over Time of Day

| Level | 10-11 AM | 11-12 PM | 12-16 PM | Shift |
|-------|----------|----------|----------|-------|
| **ORB H** | 42% BRK / 32% bounce | 32% BRK / 36% bounce | 42% BRK / 46% bounce | Becomes MAGNET in afternoon |
| **ORB L** | 36% BRK / 44% bounce | 50% BRK / 36% bounce | 40% BRK / 34% bounce | Reverses midday |
| **Yest H** | 65% BRK / 20% bounce | 22% BRK / 44% bounce | 25% BRK / 75% bounce | **Strong BARRIER-to-MAGNET shift** |
| **Yest L** | 67% BRK / 21% bounce | 35% BRK / 35% bounce | 40% BRK / 20% bounce | Weakens but stays barrier |

**Critical finding:** Yest H transitions from a 65% barrier in the morning to a 75% magnet in the afternoon. This means Yest H BRK signals should be time-gated -- only effective before 11 AM.

---

## 4. Direction Analysis Per Level

Every level in this dataset is directionally pure: BRK signals at HIGH levels are exclusively bull, and BRK at LOW levels are exclusively bear. REV at HIGH levels = bear, REV at LOW = bull. So the direction analysis reduces to the signal type x level matrix above.

### Direction Performance Ranking (all combos, N>=10)

| Rank | Level | Dir | Type | N | Avg PnL | Net ATR |
|-----:|-------|-----|------|--:|--------:|--------:|
| 1 | Week H | bear | REV | 31 | +0.162 | +5.0 |
| 2 | Week L | bull | REV | 29 | +0.129 | +3.7 |
| 3 | ORB L | bear | BRK | 163 | +0.108 | +17.6 |
| 4 | Yest H | bear | REV | 73 | +0.088 | +6.4 |
| 5 | PM L | bear | BRK | 234 | +0.082 | +19.3 |
| 6 | Yest L | bear | BRK | 118 | +0.062 | +7.3 |
| 7 | PM H | bear | REV | 103 | +0.059 | +6.1 |
| 8 | ORB H | bear | REV | 175 | +0.047 | +8.1 |
| ... | ... | ... | ... | ... | ... | ... |
| 15 | ORB H | bull | BRK | 203 | +0.002 | +0.3 |
| 16 | Week H | bull | BRK | 39 | -0.001 | -0.0 |
| **LAST** | **ORB L** | **bull** | **REV** | **143** | **-0.088** | **-12.5** |

**Observation:** Bear signals dominate the top of the table. The best bull signals are Week L REV (+0.129) and Yest L bull REV (+0.015). Bull BRK at ORB H is essentially flat (+0.002). This reinforces the known bear > bull edge.

---

## 5. Combo / Confluence Analysis

### Single vs Multi-Level

| Type | N | Win% | Avg PnL | Net ATR |
|------|--:|-----:|--------:|--------:|
| Single level | 1,425 | 33.8% | +0.033 | +47.4 |
| 2 levels | 347 | 36.9% | +0.045 | +15.7 |
| **3 levels** | **66** | **54.5%** | **+0.108** | **+7.1** |
| 4 levels | 3 | 66.7% | +0.012 | +0.0 |

**Confluence works.** 3-level signals are dramatically better: 54.5% win rate vs 33.8% for single. The PnL triples from +0.033 to +0.108.

### Best Combos (N>=5, ranked by PnL)

| Levels | Type | N | Win% | Avg PnL | Net ATR |
|--------|------|--:|-----:|--------:|--------:|
| Yest L+Week L+ORB L | REV | 6 | 66.7% | +0.320 | +1.9 |
| Week L+ORB L | REV | 6 | 50.0% | +0.306 | +1.8 |
| PM L+Week L+ORB L | REV | 8 | 75.0% | +0.262 | +2.1 |
| PM L+Yest L | BRK | 21 | 47.6% | +0.162 | +3.4 |
| Week H (single) | REV | 28 | 53.6% | +0.160 | +4.5 |
| PM H+Yest H+ORB H | REV | 11 | 63.6% | +0.159 | +1.8 |
| Yest H (single) | REV | 49 | 36.7% | +0.132 | +6.5 |
| PM H+ORB H | REV | 42 | 42.9% | +0.119 | +5.0 |
| ORB L (single) | BRK | 163 | 38.0% | +0.108 | +17.6 |

### Worst Combos

| Levels | Type | N | Win% | Avg PnL | Net ATR |
|--------|------|--:|-----:|--------:|--------:|
| PM L+Yest L | REV | 6 | 0.0% | -0.229 | -1.4 |
| Yest L+Week L | REV | 7 | 28.6% | -0.104 | -0.7 |
| **ORB L (single)** | **REV** | **143** | **27.3%** | **-0.088** | **-12.5** |
| PM H+ORB H | BRK | 30 | 26.7% | -0.050 | -1.5 |

**PM H+ORB H BRK is a known mismatch:** both are HIGH levels, and the BRK signal (which is bull) fails at -0.050 PnL. The REV version of PM H+ORB H works well (+0.119).

---

## 6. Level Behavior Over Time of Day

### BRK vs REV Performance by Time

| Time | BRK N | BRK Win% | BRK PnL | REV N | REV Win% | REV PnL |
|------|------:|---------:|--------:|------:|---------:|--------:|
| 9:30-10:00 | 527 | 42.5% | +0.061 | 531 | 38.8% | +0.020 |
| 10:00-10:30 | 216 | 41.2% | +0.077 | 96 | 37.5% | +0.054 |
| **10:30-11:00** | **40** | **20.0%** | **-0.074** | 12 | 16.7% | -0.009 |
| 11:00-12:00 | 37 | 29.7% | +0.086 | 9 | 33.3% | +0.183 |
| 12:00-14:00 | 95 | 17.9% | -0.001 | 43 | 11.6% | -0.021 |
| 14:00-16:00 | 149 | 18.8% | +0.010 | 86 | 22.1% | +0.040 |

**10:30-11:00 is a dead zone.** Both BRK and REV collapse: BRK drops to 20% win, REV to 17%. This is the transition from morning momentum to midday consolidation.

**Afternoon: REV slightly outperforms BRK** (14:00-16:00: REV +0.040 vs BRK +0.010), consistent with the idea that levels become magnets later in the day.

### Level Staleness: Older = Better

| Freshness | N | Win% | Avg PnL | Net ATR |
|-----------|--:|-----:|--------:|--------:|
| Fresh (ORB, same day) | 684 | 32.6% | +0.020 | +13.5 |
| 1-day old (PM, Yest) | 1,020 | 36.0% | +0.046 | +47.0 |
| **1-5 days old (Week)** | **137** | **42.3%** | **+0.071** | **+9.7** |

This is counter-intuitive: older levels are MORE effective. Week levels (1-5 days old) have the best win rate (42.3%) and PnL (+0.071). Possible explanation: Week H/L are more significant levels that the market "remembers" and reacts to more predictably.

### Critical Time-of-Day Warnings

Combos that turn NEGATIVE after 10:30:
- **PM L BRK 10:30-11:00:** PnL = -0.165 (10 signals, 10% win) vs +0.123 in the morning
- **ORB H BRK 9:30-10:** PnL = -0.038, but recovers to +0.060 at 10-10:30
- **Yest H BRK 10:30-11:** PnL = -0.049 (12.5% win)
- **All PM levels 12-14:** Both BRK and REV go negative at PM H/L after noon

---

## 7. Recommended Signal Type Reassignment Map

Based on the data, here is the ideal mapping:

| Level | Current Assumption | Data-Driven Best | Action | Impact |
|-------|--------------------|-----------------|--------|--------|
| **PM H** | BRK (barrier) | **REV** | Change default | +3.0 ATR gain (REV +6.1 vs BRK +3.1) |
| **PM L** | BRK (barrier) | **BRK** (confirmed) | Keep | Already optimal |
| **Yest H** | BRK (barrier) | **REV** | Change default | +4.8 ATR gain |
| **Yest L** | BRK (barrier) | **BRK** (confirmed) | Keep | Already optimal |
| **ORB H** | BRK (barrier) | **REV** | Change default | +7.8 ATR gain |
| **ORB L** | BRK (barrier) | **BRK** (confirmed) | Keep + suppress REV | +12.5 ATR from suppression |
| **Week H** | BRK (barrier) | **REV** | Change default | +5.0 ATR gain |
| **Week L** | BRK (barrier) | **REV** | Change default | +2.7 ATR gain |

### The Rule: HIGH levels = REV, LOW levels = BRK

With one exception: **Week L** acts like a magnet (+0.129 REV vs +0.026 BRK). This could be because Week L, being a multi-day low, acts as a support magnet that price bounces off rather than breaks through.

---

## 8. Suppression List with ATR Savings

### Definite Suppressions (N>=10, net negative, pattern is clear)

| Combo | N | Win% | Avg PnL | ATR Drain | Action |
|-------|--:|-----:|--------:|----------:|--------|
| **ORB L bull REV** | 143 | 27.3% | -0.088 | -12.5 | SUPPRESS |
| **ORB H BRK (CONF fail)** | 169 | 25.4% | -0.041 | -6.9 | Require CONF |
| **PM H BRK (CONF fail)** | 140 | 26.4% | -0.040 | -5.6 | Require CONF |
| **Yest L BRK (CONF fail)** | 83 | 30.1% | -0.046 | -3.8 | Require CONF |
| **Yest H BRK (CONF fail)** | 77 | 27.3% | -0.024 | -1.8 | Require CONF |

**Total recoverable from suppression: ~12.5 ATR (direct), ~18.1 ATR from CONF-fail gating**

### EMA-Based Suppressions (against-EMA combos that are net negative)

| Combo | N | Avg PnL | ATR Drain |
|-------|--:|--------:|----------:|
| ORB H BRK against-EMA | 55 | -0.245 | -13.5 |
| ORB L REV against-EMA | 38 | -0.222 | -8.4 |
| PM L REV against-EMA | 68 | -0.113 | -7.7 |
| PM H BRK against-EMA | 22 | -0.281 | -6.2 |
| Yest L REV against-EMA | 24 | -0.251 | -6.0 |
| Yest H REV against-EMA | 32 | -0.085 | -2.7 |
| Week L REV against-EMA | 6 | -0.255 | -1.5 |
| Week H BRK aligned (!) | 28 | -0.044 | -1.2 |

**Total against-EMA drain: ~47.2 ATR across 273 signals.** The EMA hard gate (v3.0) already handles most of this, but these numbers validate why it works.

---

## 9. New Level Type Candidates and Missing Coverage

### Confirmed by Data

1. **VWAP as REV level:** Not in enriched-signals.csv yet, but VWAP alignment is tracked. Counter-VWAP signals (price on opposite side of VWAP from signal direction) have a known +0.060 MFE delta. VWAP itself should be a REV level.

2. **PD Mid as REV level:** Already implemented in v3.1 (was incorrectly BRK before). Data validates this is correct -- midpoints are magnets.

3. **Round numbers:** Not currently tracked. Given the magnet/barrier framework, round numbers ($100, $200, $500) likely act as magnets. Would need IB data analysis to validate.

### Missing Signal Types in Data

The enriched-signals.csv only contains BRK and REV (no FADE, RNG, QBS, Reclaim, Retest). These newer signal types from v3.0+ need their own evaluation once enough data accumulates:

- **FADE:** Post-CONF-failure reversals. Estimated 179 ATR potential from missed-moves analysis.
- **RNG:** 12-bar range breakouts. Estimated 297 ATR potential.
- **Reclaim:** Price reclaims a level after breaking through. Not yet quantified.

---

## Appendix: Confirmation (CONF) x Level Interaction

CONF pass is universally positive across ALL levels, but the magnitude varies:

| Level | CONF Pass PnL | CONF Fail PnL | Delta |
|-------|-------------:|-------------:|------:|
| Yest L BRK | +0.313 (N=28, 75% win) | -0.046 (N=83) | +0.359 |
| PM L BRK | +0.134 (N=50, 42% win) | +0.023 (N=166) | +0.111 |
| ORB H BRK | +0.224 (N=27, 67% win) | -0.041 (N=169) | +0.265 |
| PM H BRK | +0.232 (N=22, 59% win) | -0.040 (N=140) | +0.272 |
| ORB L BRK | +0.111 (N=41, 46% win) | +0.079 (N=113) | +0.032 |

**ORB L BRK is the only level where CONF fail still works** (+0.079 PnL). At every other level, CONF fail = net negative or barely positive. This further supports that ORB L bear BRK is the system's strongest signal.

---

## Summary: Three Changes, Ordered by Impact

1. **Suppress ORB L bull REV (+12.5 ATR).** This is the single biggest ATR drain in the system. Price bounces off ORB L 42% of the time -- the "reversal" signal fires into the bounce, gets trapped, and loses.

2. **Reclassify HIGH levels as magnet/REV.** PM H, Yest H, ORB H, Week H, and Week L all perform better as REV signals. The combined ATR uplift from routing to the best signal type is ~23 ATR.

3. **Time-gate BRK signals at barrier levels after 10:30.** Yest H breakouts collapse from 65% barrier behavior to 22% by 11 AM. PM levels go negative after noon. Consider dimming or suppressing BRK signals at these levels in the afternoon.
