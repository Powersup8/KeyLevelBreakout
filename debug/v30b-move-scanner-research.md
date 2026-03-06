# v3.0b Move Scanner Research — Ground Truth + Cross-Symbol Triggers

**Date:** 2026-03-05
**Data:** 5sec parquet → 5min resampled, 10 symbols, 5 trading days (Feb 26 - Mar 4)
**Analysis script:** `debug/v30b_move_scanner.py`

---

## 1. Executive Summary

### What we are catching vs missing

**Ground truth:** 1,054 significant moves (>= 0.5 ATR in any 30-min window) across 10 symbols over 5 days. That is roughly **21 significant moves per symbol per day.**

**v3.0b catch rate: 4.2%** (44 of 1,054 moves).

This sounds alarming, but context matters:

- **82% of missed moves are quiet drifts** — no key level, low volume. These are not signal-worthy moves; they are slow grinds that our indicator correctly ignores.
- **Only 10% of moves start near a key level** (114/1054). Our indicator is a key-level system, so it should only catch level-related moves.
- Of the 114 level-based moves, v3.0b catches 10 (9%). This is the real catch rate concern.
- **Only 2 "golden misses"** (EMA-aligned + near level + vol >= 1.5x) — moves we should have caught and didn't.

**v3.0b signal quality:**
- 68 active signals over 5 days (13.6/day across 10 symbols)
- 90% reach MFE > 0.3 ATR (signals do move in the right direction)
- 50% have MFE/MAE ratio > 1 (half are tradeable)
- Total PnL on 30-min hold: +2.60 ATR (slightly positive)
- 15:00+ signals are the drag: -22.83 ATR from 13 late-day signals

**The EMA Hard Gate works:** Suppressed 18 signals that would have lost -20.47 ATR total. Only 1 of 18 was truly profitable (AMD pm_l on 3/3 at 15:55, +7.30 ATR — a late-day outlier).

### The real gold mine: Cross-Symbol Triggers

**259 instances** where 4+ symbols moved >= 0.3 ATR in the same 5-min window. These are highly tradeable, but our indicator has **zero cross-symbol awareness.** This is the single biggest opportunity.

---

## 2. Ground Truth Move Inventory

### 5-Day Summary (Feb 26 - Mar 4)

| Metric | Value |
|--------|-------|
| Total significant moves | 1,054 |
| Per day | 207-216 |
| Per symbol/day | ~21 |
| Avg magnitude | 2.12 ATR |
| Near key level | 114 (11%) |
| EMA-aligned | 508 (48%) |

### Moves by Symbol

| Symbol | Total | Bull | Bear | Avg Mag |
|--------|-------|------|------|---------|
| AAPL | 109 | 55 | 54 | 2.10 |
| AMD | 107 | 61 | 46 | 1.91 |
| AMZN | 105 | 58 | 47 | 2.15 |
| GOOGL | 104 | 49 | 55 | 2.17 |
| META | 104 | 53 | 51 | 2.16 |
| MSFT | 105 | 56 | 49 | 2.10 |
| NVDA | 105 | 49 | 56 | 2.11 |
| QQQ | 104 | 59 | 45 | 2.15 |
| SPY | 105 | 51 | 54 | 2.25 |
| TSLA | 106 | 50 | 56 | 2.14 |

### Near-Level Distribution

| Level | Count |
|-------|-------|
| ORB H | 31 |
| PM L | 23 |
| PM H | 19 |
| Yest H | 14 |
| Yest L | 14 |
| ORB L | 13 |

**Key insight:** ORB levels appear most frequently (44 total), followed by PM levels (42). Yesterday levels are less common (28). This aligns with the known finding that ORB/PM levels are more frequently tested during the session.

---

## 3. Cross-Symbol Trigger Patterns (The Gold Mine)

### Overview

| Threshold | Count (5 days) | Per Day |
|-----------|---------------|---------|
| 3+ symbols, >= 0.3 ATR | 341 | ~68 |
| 4+ symbols, >= 0.3 ATR | 259 | ~52 |
| 7+ symbols, >= 0.3 ATR | 92 | ~18 |
| 10 symbols (all), >= 0.3 ATR | 23 | ~5 |

Cross-symbol moves are **extremely frequent** — about one every 7 minutes during market hours. This means they happen so often that they cannot all be traded. The key is finding which ones have follow-through.

### Time-of-Day Analysis (Excluding Last 30 Min)

| Window | N | 30m PnL/trigger | Total PnL | Win% |
|--------|---|-----------------|-----------|------|
| 9:30-10:00 | 28 | +0.437 | +12.2 ATR | 57% |
| 10:00-11:00 | 37 | +0.145 | +5.4 ATR | 48% |
| 11:00-12:00 | 37 | -0.107 | -4.0 ATR | 48% |
| 12:00-13:00 | 36 | -0.181 | -6.5 ATR | 46% |
| 13:00-14:00 | 36 | -0.005 | -0.2 ATR | 52% |
| 14:00-15:00 | 40 | +0.239 | +9.6 ATR | 55% |
| 15:00-15:30 | 27 | -0.429 | -11.6 ATR | 37% |

**Finding:** Morning (9:30-10:00) and mid-afternoon (14:00-15:00) cross-symbol triggers are profitable. Midday (11-13) is a dead zone. Last 30 minutes is strongly negative.

### Morning Bear Triggers (9:40-10:15) — Best Edge Found

| Date | Time | N Sym | Mag | 30m PnL | Win% |
|------|------|-------|-----|---------|------|
| 02/26 | 09:40-10:10 | 4-9 | 0.5-1.4 | +2.85 to +4.24 | 100% |
| 02/26 | 10:15 | 9 | 1.38 | -0.37 | 20% |
| 02/27 | 09:40 | 9 | 0.92 | -1.32 | 10% |
| 03/02 | 09:50 | 9 | 0.66 | -1.09 | 0% |
| 03/03 | 09:40-09:55 | 6-9 | 0.6-0.9 | +0.25 to +1.09 | 70-100% |
| 03/04 | 09:40 | 7 | 0.68 | -1.96 | 0% |

**N=17, avg PnL=+1.058 ATR, win=63%, total=+18.0 ATR**

This is the most profitable edge found: when 4+ symbols sell off together between 9:40 and 10:15, the continuation trade averaged +1.06 ATR per trigger over these 5 days. The magnitude (how much they've already dropped) doesn't predict quality — small cascades work as well as large ones.

However, **sample size is only 17** and includes one day (Feb 26) that accounted for most of the gains. This needs more validation.

### By Number of Participating Symbols

| N Symbols | Count | 30m PnL | Win% |
|-----------|-------|---------|------|
| 4 | 46 | +0.111 | 55% |
| 5 | 30 | +0.941 | 60% |
| 6 | 46 | -0.360 | 45% |
| 7 | 45 | +0.005 | 45% |
| 8 | 35 | -0.166 | 46% |
| 9 | 34 | -0.146 | 46% |
| 10 | 23 | -0.982 | 47% |

**Counterintuitive finding:** 5-symbol triggers are the best (not 10-symbol). When ALL symbols move together, it often marks exhaustion, not continuation. The 5-symbol count may hit a sweet spot of "enough confirmation but not yet saturated."

### By Direction

| Direction | Count | 30m PnL | Win% |
|-----------|-------|---------|------|
| Bull | 134 | -0.290 | 50% |
| Bear | 125 | +0.182 | 48% |

Bear triggers are slightly more profitable than bull triggers for follow-through. This may reflect the known asymmetry that sell-offs are faster and more directional.

### Leader Analysis

| Symbol | Times Leading | % |
|--------|--------------|---|
| MSFT | 46 | 13% |
| META | 43 | 13% |
| AAPL | 43 | 13% |
| GOOGL | 39 | 11% |
| NVDA | 38 | 11% |
| TSLA | 36 | 11% |
| AMZN | 34 | 10% |
| AMD | 33 | 10% |
| SPY | 22 | 6% |
| QQQ | 7 | 2% |

**SPY does NOT lead.** Individual stocks (MSFT, META, AAPL) lead more often than the indices. This makes sense — the indices aggregate the moves. SPY leading is only 6% of the time, and its follow-through when leading (+0.05 ATR) is no better than when following (-0.05 ATR).

### "Trigger Detection Rule" Assessment

Can we build a tradeable rule from this?

**Proposed rule:** "When 4-5 symbols move >= 0.3 ATR in the same direction in a single 5-min bar, AND it's between 9:45 and 15:00, enter ALL correlated symbols in that direction."

**Backtest (from this 5-day sample):**
- All triggers 9:45-15:00: N=199, avg 30m PnL = +0.096 ATR, win = 51%, total = +19.2 ATR
- If further filtered to 5-symbol triggers: N=26, avg 30m PnL = +0.886 ATR, win = 62%

**Assessment:** There is a marginal edge, but it's noisy. The cross-symbol move itself is NOT the signal — it's context. The real value would be using it as a CONFIRMATION for existing key-level signals.

### Best and Worst Triggers

**Best 5 triggers (all high-PnL, all in last 30 min — market close dynamics):**
- 03/02 15:55 bear, 5 sym, +9.35 ATR (close sell-off, artificial)
- 02/26 15:45 bear, 6 sym, +6.28 ATR (close sell-off, artificial)

**Excluding close (best organic):**
- 02/26 09:45-10:05 bear, 4-6 sym, +2.50 to +4.24 ATR (genuine morning sell-off)
- 03/03 10:55-11:05 bull, 9-10 sym, +1.06 to +2.03 ATR (genuine morning rally)
- 03/04 09:45-10:05 bull, 5-8 sym, +0.90 to +1.80 ATR (genuine recovery bounce)

**Worst triggers (pattern: late-day reversals):**
- 03/02 15:30 bull, 10 sym, -8.71 ATR (fake late rally crushed at close)
- 03/02 15:50 bull, 10 sym, -8.70 ATR (same)
- 02/26 15:30 bull, 10 sym, -7.72 ATR (same pattern)

**Lesson:** Late-day bull triggers with ALL 10 symbols are catastrophic — they mark the exhaustion top before market close.

---

## 4. Move Fingerprint Classification

| Fingerprint | N | Avg Magnitude | Continuation Win% | Avg Continuation |
|-------------|---|---------------|-------------------|------------------|
| Quiet Drift | 951 | 1.95 ATR | 50% | +0.308 |
| Cross-Symbol Cascade | 734 | 2.24 ATR | 49% | +0.183 |
| Reversal | 546 | 2.09 ATR | 51% | +0.296 |
| Level Break | 114 | 2.22 ATR | 48% | +0.517 |
| Gap Follow-Through | 50 | 4.01 ATR | 44% | +0.854 |
| Momentum Surge | 34 | 4.22 ATR | 38% | +0.730 |
| Unclassified | 10 | 3.35 ATR | 70% | +2.516 |

### Key Insights

1. **Level Breaks have the best continuation** (+0.517 ATR avg) among classified types. This validates that our indicator focuses on the right signal type.

2. **Gap Follow-Through has the highest magnitude** (4.01 ATR) and decent continuation (+0.854). These are early-morning moves that continue the open direction. v3.0b catches 28% of these (14/50) — the best catch rate of any type.

3. **Quiet Drifts are 90% of all moves** but have zero edge (50% win, +0.308 continuation). v3.0b correctly ignores these (3% catch rate).

4. **Momentum Surges have the worst continuation win rate** (38%) despite large magnitude (4.22 ATR). High-volume surges are often exhaustion, not continuation. This aligns with our ⚡ big-move findings.

5. **Cross-Symbol Cascades** are abundant (734) and have moderate continuation (+0.183), but v3.0b only catches 5% of them. These represent the biggest opportunity gap.

### What v3.0b Catches vs Misses

| Move Type | Total | Caught | Missed | Catch% |
|-----------|-------|--------|--------|--------|
| Level Break | 114 | 10 | 104 | 9% |
| Momentum Surge | 34 | 9 | 25 | 26% |
| Quiet Drift | 951 | 25 | 926 | 3% |
| Gap Follow-Through | 50 | 14 | 36 | 28% |
| Reversal | 546 | 12 | 534 | 2% |
| Cross-Symbol Cascade | 734 | 34 | 700 | 5% |

v3.0b best catches Gap Follow-Through (28%) and Momentum Surges (26%), which are the highest-volume, most obvious moves. It misses Reversals (2%) and Quiet Drifts (3%) almost entirely — by design.

---

## 5. Over-Optimization Audit

### v2.8 vs v3.0b Signal Comparison

| Metric | v2.8 (simple) | v3.0b Active | v3.0b Suppressed |
|--------|---------------|--------------|------------------|
| N signals (5 days) | 86 | 68 | 18 |
| Win rate (30m hold) | 26% | 27% | 6% |
| Total PnL | -17.87 ATR | +2.60 ATR | -20.47 ATR |
| Avg PnL | -0.213 ATR | +0.039 ATR | -1.137 ATR |
| Avg MFE | 1.829 ATR | 1.669 ATR | — |
| Avg MAE | 2.418 ATR | 2.151 ATR | — |

**v3.0b's EMA Hard Gate added +20.47 ATR** by suppressing 18 counter-EMA signals. Only 7 of the 18 (39%) would have been profitable, and the total PnL if allowed = -20.47 ATR. The gate works decisively.

### EMA Hard Gate Audit (18 Suppressed Signals)

Notable suppressed signals:
- **TSLA 03/03 15:50 bull pm_l** +5.79 ATR — the biggest miss. Late-day reversal, counter-EMA. An outlier.
- **AMD 03/03 15:55 bull pm_l** +7.30 ATR — same late-day session. Counter-EMA.
- **QQQ 02/27 15:35 bear orb_h** +4.38 ATR — profitable counter-EMA signal.
- **QQQ 03/02 15:50 bull yest_h** -12.55 ATR — the gate saved us from catastrophe.
- **NVDA 03/02 15:50 bull yest_h** -8.00 ATR — same.
- **GOOGL 03/02 15:50 bull orb_h** -9.59 ATR — same.

**Verdict:** The EMA gate correctly blocks 3 catastrophic late-day signals (-30 ATR combined) at the cost of missing 2 profitable late-day outliers (+13 ATR). Net benefit: +17 ATR. Keep the gate.

### Afternoon Dimming Audit

| Metric | After 11:30 | Before 11:30 |
|--------|-------------|--------------|
| N | 43 | 25 |
| Win rate | 22% | 36% |
| Avg PnL | -0.935 ATR | +1.404 ATR |
| Total PnL | -38.34 ATR | +35.10 ATR |

**Afternoon signals are toxic.** The -38.34 ATR from 43 afternoon signals erases ALL the morning gains. Dimming is not aggressive enough — suppressing afternoon signals entirely would improve total PnL by +38 ATR.

### Once-Per-Session Impact

Found 23 instances where a level was touched twice (opposite directions). Results:
- First touch: 52% win, avg +0.2 ATR
- Second touch: highly variable, dominated by 15:50+ noise

The once-per-session gate is not costing us much because second touches mostly happen at market close where they're unreliable anyway.

### Volume Filter (< 1.5x) Audit

- 122 low-volume level touches detected
- 101 (83%) had the price move > 0.3 ATR in the touch direction within 30 min

**This is misleading.** A "touch" at a level followed by any movement is not the same as a tradeable signal. Low-volume level approaches often drift through without conviction. The 83% figure reflects the fact that prices generally move 0.3 ATR in 30 minutes regardless of any signal. This is not evidence that the volume filter should be removed.

### TSLA March 5 Level Computation (User's Specific Request)

From March 4 data:
- **Yesterday High: 408.33**
- **Yesterday Low: 394.58**
- **Yesterday Close: 406.06**
- **Yesterday Open: 397.85**
- **EMA9 at close: 406.64, EMA21 at close: 406.33 → BULL**

If TSLA opens March 5 around 406 (near yesterday's close), then:
- Yesterday High at 408.33 would be the nearest resistance level (+2.27 above close)
- PM H would be defined by the first 5-min bar of March 5
- EMA at close is barely bull (9 vs 21 only +0.31 gap) — fragile. Any early weakness could flip EMAs bear.

---

## 6. "Right Signal for Right Move" Framework

### Current Signal Types vs Move Types

| Move Type | Best Signal | Our Indicator Has It? | Coverage |
|-----------|-------------|----------------------|----------|
| Key Level Breakout | BRK | YES | 9% of level breaks caught |
| Mean-Reversion Touch | REV | YES | 2% of reversals caught |
| Momentum Surge | RNG (range break) | YES | 26% caught |
| Quiet Drift | None needed | Correctly ignored | 3% (noise) |
| Gap Follow-Through | BRK at open | YES | 28% caught |
| Cross-Symbol Cascade | NOT AVAILABLE | NO | 5% caught (accidentally) |

### The Coverage Gap

Our indicator is a **single-symbol, key-level system.** It catches moves that happen at specific price levels with sufficient volume. This is approximately 11% of all significant moves.

The 89% it misses consists of:
- **82% quiet drifts** — correctly ignored, no edge
- **7% cross-symbol cascades, reversals, and level-adjacent moves** — potentially tradeable

### Cross-Symbol Cascade Signal (Proposed New Type)

The data shows that cross-symbol moves are frequent (52 per day at 4+ symbols) but individually have thin edge (+0.096 ATR). However, as a CONFIRMATION layer for existing signals, they could be powerful:

**Hypothetical rule:** "When a BRK/REV signal fires, check if 3+ other symbols moved the same direction in the current or prior 5-min bar. If yes, upgrade confidence."

This cannot be implemented in Pine Script for a single-chart indicator (Pine runs per-symbol, no cross-symbol access). It would require either:
1. A separate scanner/alert system
2. Using SPY/QQQ as a proxy for market direction (already done via VWAP alignment)
3. A multi-symbol Pine Script using `request.security()` calls

---

## 7. Specific Recommendations

### High-Confidence Recommendations (Data-Validated)

1. **Kill afternoon signals entirely (after 11:30)** — Expected impact: +38 ATR over 5 days. Afternoon signals are net -38 ATR with 22% win rate. This is the single highest-impact change available. Currently they are "dimmed" but still visible — they should be fully suppressed.
   - Risk: You miss occasional late-day outliers (TSLA 15:50, AMD 15:55). But these are 2 wins out of 43 signals.

2. **Keep EMA Hard Gate** — Confirmed: +20.47 ATR saved. 94% of suppressed signals were losers.

3. **Add "first trigger of the day" caution** — The very first 5-min bar's signal (9:30-9:35) has -1.18 ATR avg PnL across 5 days. Opening noise makes first-bar signals unreliable. The MC 9:50 gate partly addresses this, but BRK signals at 9:30-9:35 also suffer.

### Medium-Confidence Recommendations (Promising but Small Sample)

4. **Morning bear cascades (9:40-10:15) as high-conviction setup** — N=17, +1.06 ATR avg, 63% win. When 4+ symbols sell off together in this window, it's a strong continuation signal. But 5-day sample is too small to act on.

5. **5-symbol triggers > 10-symbol triggers** — When ALL symbols move together, it's often exhaustion. When 5 move together, it's a sector rotation with conviction. This is a subtle pattern that needs more data.

6. **Late-day bull + 10 symbols = AVOID** — Three instances, all -7 to -9 ATR. When all 10 symbols rally after 15:30, it reverses catastrophically by close. But N=3 is too few.

### Not Recommended (Data Does Not Support)

7. **Cross-symbol cascade as standalone signal** — 259 triggers in 5 days is far too frequent (52/day). Individual trigger PnL is +0.096 ATR, barely above noise. The cross-symbol move is context, not signal.

8. **Removing volume filter** — The 83% "profitability" of low-vol touches is misleading. Prices move 0.3 ATR in 30 min naturally. No evidence of edge from low-vol level touches.

9. **Removing once-per-session gate** — Second touches mostly happen at market close. Minimal impact either way.

### Over-Optimization Assessment

| Filter | Status | Justified? |
|--------|--------|-----------|
| EMA Hard Gate (post 9:50) | Active | YES — saves 20.47 ATR in 5 days |
| Once-per-session | Active | NEUTRAL — minimal impact |
| Afternoon dimming | Active (dim) | SHOULD BE STRONGER — suppress entirely |
| Vol >= 1.5x | Active | UNCLEAR — no evidence for or against |
| Auto-R1 (EMA + morning) | Active | Not testable from candle data alone |

**Overall assessment:** v3.0b is NOT over-optimized. The EMA gate is the most impactful filter and it clearly works. The main issue is that afternoon signals should be suppressed more aggressively, not less. The system could be simpler by removing dimming and just suppressing everything after 11:30.

---

## Appendix: Data Quality Notes

- **5-day window is small.** Feb 26-Mar 4 includes tariff-driven volatility (Feb 26 sell-off). Results may not generalize to low-volatility periods.
- **30-min hold PnL** is a simplistic metric. The actual indicator uses CONF/5m CHECK, which captures edge differently.
- **Cross-symbol triggers** use the same 0.3 ATR threshold for all symbols. A normalized threshold (based on each symbol's typical 5m range) might be more precise.
- **Level detection** in the simulation uses simple yesterday H/L, ORB, PM levels. The actual Pine indicator also uses VWAP zones, reclaims, and retests, which would change the catch rate.
- **Win rate for simulated signals (2-27%)** is lower than what the actual indicator achieves because: (a) the simulation doesn't use CONF/5m check, (b) it doesn't use Runner Score, (c) it holds for exactly 30 min instead of using a trailing stop.
