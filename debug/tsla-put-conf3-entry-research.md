# TSLA PUT Strategy Research: Weak Premarket (conf<=3) Days

**Date:** 2026-03-20
**Data:** TSLA 5sec bars (67 days, Dec 2025-Mar 2026) + 1m bars (282 days, Feb 2025-Mar 2026)
**Hypothesis:** On days where premarket confidence is low (conf<=3), short TSLA early or after a dip-bounce-turnaround pattern.

---

## Executive Summary

**VERDICT: NO VIABLE PUT STRATEGY FOUND.**

Across all 6 tests, every short entry method on conf<=3 days produces negative or near-zero expected value. The fundamental problem: TSLA has a **strong long bias at the open** (+$0.14 avg first bar, 62% up days) that overwhelms any conf-based filter. The best results seen (bar1_red + 30s hold: +$0.09 avg, 71% win on 28 days) evaporate within 60 seconds and do not replicate on the larger 282-day 1m dataset (35% win, -$0.09 avg).

---

## Proxy Validation

Since pine log conf scores only cover 23 days (Feb 17 - Mar 19, 2026), a proxy was built using:
1. Bar1 direction (green = bullish PM position proxy)
2. VIX in 18-25 sweet spot
3. Triple alignment (TSLA + SPY + QQQ bar1 all green)
4. Gap < 2% of price
5. PM acceleration skipped (no premarket data in IB files)

**Validation: 78% category match** (18/23 days correctly classified as <=3 or >=4).

| Day | Actual conf | Proxy score | Match? |
|-----|------------|-------------|--------|
| 2026-02-17 | 3 | 3 | OK |
| 2026-02-18 | 2 | 2 | OK |
| 2026-02-19 | 2 | 4 | MISS |
| 2026-02-20 | 2 | 2 | OK |
| 2026-02-24 | 4 | 4 | OK |
| 2026-02-25 | 4 | 2 | MISS |
| 2026-03-03 | 4 | 2 | MISS |
| 2026-03-11 | 4 | 4 | OK |
| 2026-03-12 | 2 | 4 | MISS |
| 2026-03-18 | 4 | 3 | MISS |

**Issue:** The proxy is heavily skewed -- 263 of 282 days classify as conf<=3 (93%). This is because without premarket data, 2 of 5 checks are structurally hard to pass (PM acceleration always=0, triple alignment requires all 3 bar1s green). The proxy catches the bearish cluster but lacks precision.

**Universe sizes:**
- conf<=3 proxy: 263 days (1m) / 63 days (5sec)
- conf>=4 proxy: 19 days (1m) / 4 days (5sec)

---

## Test 1: 10-Second Entry SHORT

Short at 9:30:10 bar close, measure PnL at various hold times.

| Group | N | 30s avg | 60s avg | 2m avg | 3m avg | 5m avg | 5m MFE | 5m MAE |
|-------|---|---------|---------|--------|--------|--------|--------|--------|
| conf<=3 | 63 | -$0.02 | -$0.03 | -$0.10 | -$0.06 | -$0.00 | $0.43 | $0.49 |
| conf>=4 | 4 | -$0.34 | -$0.14 | -$0.20 | -$0.34 | -$0.34 | $0.14 | $0.62 |
| ALL | 67 | -$0.04 | -$0.04 | -$0.11 | -$0.07 | -$0.02 | $0.41 | $0.50 |

**Result:** Negative expectancy at all horizons. conf<=3 is slightly less bad than all days, but still losing. Win rates 35-51% (below breakeven). MAE exceeds MFE.

---

## Test 2: Multiple Entry Times on conf<=3 Days

| Entry | 30s | 60s | 2m | 3m | 5m |
|-------|-----|-----|----|----|-----|
| 9:30:05 | $-0.01 (48%) | $+0.02 (48%) | $-0.09 (32%) | $-0.04 (41%) | $+0.04 (46%) |
| 9:30:10 | $-0.02 (51%) | $-0.03 (49%) | $-0.10 (35%) | $-0.06 (43%) | $-0.00 (44%) |
| 9:30:15 | $-0.01 (49%) | $-0.01 (44%) | $-0.08 (41%) | $-0.03 (41%) | $+0.02 (46%) |
| 9:30:20 | $+0.03 (46%) | $+0.03 (46%) | $-0.04 (43%) | $+0.01 (41%) | $+0.06 (51%) |
| 9:30:30 | $+0.02 (48%) | $-0.04 (37%) | $-0.06 (43%) | $-0.01 (40%) | $+0.04 (51%) |
| 9:30:45 | $-0.00 (37%) | $-0.05 (37%) | $-0.02 (49%) | $-0.05 (44%) | $+0.05 (49%) |
| 9:31:00 | $-0.06 (33%) | $-0.09 (37%) | $-0.05 (44%) | $-0.05 (44%) | $+0.02 (48%) |

**Result:** 9:30:20 is the "least bad" entry time, but still produces avg PnL of +$0.03 to +$0.06 with sub-50% win rates. No entry time produces a tradeable edge.

---

## Test 3: Dip-Bounce-Turnaround Entry

After open, wait for: (1) a dip from open, (2) a bounce back up by X% of the dip, (3) turnaround confirmation (bar closes below bounce bar's low). Entry = turnaround bar close. Window: first 5 minutes.

| Bounce % | N | 30s | 60s | 3m | 5m | MFE | MAE | Avg Delay |
|----------|---|-----|-----|----|----|-----|-----|-----------|
| 10% | 33 | +$0.05 (42%) | -$0.00 (27%) | +$0.03 (48%) | +$0.08 (55%) | $0.41 | $0.36 | 105s |
| 15% | 33 | +$0.02 (39%) | -$0.02 (27%) | +$0.00 (48%) | +$0.06 (52%) | $0.40 | $0.39 | 111s |
| 20% | 34 | +$0.02 (38%) | -$0.01 (29%) | +$0.05 (50%) | +$0.08 (53%) | $0.41 | $0.39 | 118s |
| 25% | 33 | +$0.00 (33%) | -$0.02 (30%) | +$0.05 (52%) | +$0.09 (52%) | $0.41 | $0.38 | 101s |
| 33% | 32 | -$0.03 (28%) | -$0.04 (25%) | -$0.00 (50%) | +$0.01 (50%) | $0.32 | $0.37 | 109s |
| **50%** | **29** | -$0.00 (38%) | -$0.02 (31%) | **+$0.11 (62%)** | **+$0.12 (62%)** | $0.39 | $0.30 | 116s |

**Best: 50% bounce, 3-5m hold** (+$0.11-$0.12, 62% win). But:
- N=29 is thin
- Average PnL of $0.12 on a $400 stock is 0.03% -- well below transaction costs
- MFE $0.39 with MAE $0.30 gives a 1.3x ratio -- not enough edge to trade
- Stop distance is only $0.15 (the bounce bar is tiny), making stops unreliable

---

## Test 4: Signal Optimization

Using 60s hold after 9:30:10 entry on conf<=3 days. Splitting by various signals:

| Signal | YES avg | YES win% | NO avg | NO win% | Verdict |
|--------|---------|----------|--------|---------|---------|
| High volume first 10s | -$0.08 (50%) | | +$0.02 (48%) | | Worse with vol |
| Wide bar1 range | -$0.09 (47%) | | +$0.04 (52%) | | Worse with wide |
| Gap DOWN | -$0.04 (57%) | | -$0.03 (43%) | | ~Same |
| VIX > 20 | **-$0.17 (29%)** | | +$0.02 (57%) | | **Shorts much worse with high VIX** |
| **Bar1 RED** | **+$0.05 (64%)** | | -$0.10 (37%) | | **Only positive filter** |
| First 5sec RED | -$0.03 (48%) | | -$0.03 (50%) | | No signal |

**Bar1 RED is the only filter that produces positive short PnL.** But validation on full 1m dataset (106 days) shows -$0.09 avg, 35% win rate. The 5sec result does not hold.

**Surprising: VIX>20 is terrible for shorts** (-$0.17, 29% win). High VIX means wider ranges, and TSLA's long bias overwhelms at open.

### Bar1 RED Subgroup Deep Dive (5sec)

| Horizon | conf<=3 + bar1 RED (N=28) | conf<=3 + bar1 GREEN (N=35) |
|---------|--------------------------|----------------------------|
| 30s | +$0.09 (71%) | -$0.11 (34%) |
| 60s | +$0.05 (64%) | -$0.10 (37%) |
| 2m | -$0.04 (36%) | -$0.14 (34%) |
| 3m | -$0.06 (39%) | -$0.05 (46%) |
| 5m | -$0.04 (29%) | +$0.03 (57%) |

The bar1_red edge exists ONLY in the first 30-60 seconds, then reverses. This is consistent with a mean-reversion pattern: the red bar1 overshoots, bounces back, but then continues lower... except it doesn't -- the 2m/3m/5m numbers go negative.

### 1m Validation (282 days)

| Group | hold=1m | hold=2m | hold=3m | hold=5m |
|-------|---------|---------|---------|---------|
| conf<=3 + RED (106d) | -$0.09 (35%) | -$0.20 (35%) | -$0.27 (34%) | -$0.21 (37%) |
| conf<=3 + GRN (157d) | -$0.10 (45%) | -$0.07 (52%) | -$0.10 (42%) | +$0.02 (45%) |

**On the full dataset, bar1_red shorts are the WORST group**, losing the most at every horizon. The 5sec sample was misleading.

---

## Test 5: Stop Loss and Profit Target Optimization

Fixed SL x TP grid on conf<=3 days, 9:30:10 entry, 5min max hold:

| SL \ TP | $0.50 | $1.00 | $1.50 | $2.00 | $3.00 |
|---------|-------|-------|-------|-------|-------|
| $1.00 | -$0.05 (48%) | -$0.05 (43%) | -$0.03 (43%) | -$0.03 (43%) | -$0.04 (43%) |
| $1.50 | -$0.01 (49%) | -$0.01 (44%) | **+$0.02 (44%)** | +$0.01 (44%) | -$0.00 (44%) |
| $2.00 | -$0.01 (49%) | -$0.01 (44%) | +$0.02 (44%) | +$0.01 (44%) | -$0.00 (44%) |
| $3.00 | -$0.01 (49%) | -$0.01 (44%) | +$0.02 (44%) | +$0.01 (44%) | -$0.00 (44%) |

**Best: SL=$1.50 TP=$1.50** with avg +$0.02, total +$1.50 over 63 days. But:
- 44% win rate, $0.02 avg PnL
- Total profit of $1.50 over 63 trades = noise
- SL>=$2 never gets hit in 5 minutes (same results as $1.50)

**Dynamic stops (bar1_high, open price):** All negative.

**Trailing stops:** All near zero or negative.

---

## Test 6: Side-by-Side Comparison

| Metric | CALL (pine log, 23 days) | PUT @9:30:10 (63 days) |
|--------|--------------------------|------------------------|
| N trades | 37 | 63 |
| Win % | 41% | 49% |
| Avg PnL | -$0.41 | -$0.03 |
| Total PnL | -$15.34 | -$1.93 |
| Std Dev | $3.60 | $0.36 |
| MFE (5m) | n/a | $0.43 |
| MAE (5m) | n/a | $0.49 |

Note: The CALL strategy pine log includes SL hits and ORB bear breaks, reflecting the current indicator's imperfect performance in the logged period. The PUT strategy has smaller magnitudes because it's a 60-second hold vs the CALL's multi-minute trades.

---

## Structural Analysis: Why Shorting TSLA at Open Fails

**TSLA's open has a persistent long bias:**
- First bar: +$0.14 avg, 62% up days (282 days)
- First 5 minutes: +$0.25 avg, 58% up days

This isn't unique to high-conf days. Even on conf<=3 days (our "bearish" universe), the long bias persists because:

1. **The proxy is too broad** -- 93% of days classify as conf<=3, so it barely filters
2. **TSLA attracts dip buyers** -- institutional algos buy the open on TSLA regardless of premarket sentiment
3. **The conf system identifies CALL weakness, not SHORT opportunity** -- low conf means "don't go long" not "go short." These are different statements
4. **Mean reversion dominates in the first minutes** -- any initial dip gets bought back within 1-2 minutes

---

## Practical Recommendation

**Do not implement a PUT strategy based on conf<=3 days.**

The data across 282 days (1m) and 67 days (5sec) shows no tradeable short edge:

1. **No entry timing works** -- all tested offsets (5s to 60s) produce negative or zero PnL
2. **The dip-bounce-turnaround pattern is marginal** -- best case +$0.12 avg on N=29 (0.03% of price)
3. **Signal filters don't help enough** -- bar1_red gives a fleeting 30-second edge that reverses and doesn't replicate on the larger dataset
4. **SL/TP optimization can't fix a non-edge** -- the best combo produces +$0.02 avg ($1.50 total over 63 trades)
5. **VIX>20 actually hurts shorts** -- contrary to intuition, high-vol environments amplify TSLA's long bias at open

**If you want to trade weak premarket days, the better approach is:**
- Use conf<=3 as a STAND-ASIDE signal (the current behavior)
- Wait for ORB bear break (which the indicator already detects)
- The ORB bear break has actual structure and confirmation, unlike raw open shorts

**The conf system is working correctly as a filter, not as a directional signal.**
