# TSLA Short Entry Optimization: Post-BAIL Strategies

**Date:** 2026-03-20
**Data:** 282 trading days (Feb 2025 - Mar 2026), 136 BAIL days (48.2%)
**5sec data:** Dec 2025 - Mar 2026 (29 BAIL days)

## The Core Problem

Shorting TSLA at 9:30 open on days where 9:34 close < 9:30 open (BAIL) gives outstanding results: 86.8% win, $2.54 avg, Sharpe 17.01 at 5-minute hold. But this requires knowing BAIL before it happens. By the time BAIL is confirmed at 9:34, the edge is gone: 50.7% win, -$0.03 avg, Sharpe -0.20.

The $2.54 average profit from the benchmark IS the 9:30-9:34 drop itself. Once you wait for confirmation, you've missed the entire move.

---

## Executive Summary

**No post-9:34 strategy produces tradeable edge.** Once BAIL is confirmed, every entry method tested -- bounce limits, green bar fading, new-low confirmation, time-window highs -- produces Sharpe below 1.0. The edge lives entirely in the 9:30-9:34 window.

**The only path to edge is early BAIL prediction.** Entering BEFORE 9:34 based on partial information is the only viable approach. The best tradeable signal: **bar1 red with drop >= 0.7% at 9:30 close** (Sharpe 4.67, 59% win, N=22, ALL days).

**Theoretical ceiling analysis (S5)** shows that even with perfect timing (shorting at the post-9:34 bounce high), the strategy is good but not as good as the benchmark. The 3-bar high (9:35-9:37) gives Sharpe 11.25 -- this is the theoretical max for any post-9:34 entry with a limit order.

---

## Strategy Rankings (5-minute hold)

| Rank | Strategy | N | Win% | Avg PnL | Sharpe | Tradeable? |
|------|----------|---|------|---------|--------|------------|
| 1 | S0: 9:30 open (benchmark) | 136 | 86.8% | $2.54 | 17.01 | No (requires future knowledge) |
| 2 | S5: 9:35-44 high (theoretical) | 136 | 80.1% | $2.17 | 15.01 | No (requires perfect timing) |
| 3 | S5: 9:35-39 high (theoretical) | 136 | 74.3% | $1.62 | 11.85 | No |
| 4 | S5: 9:35-37 high (theoretical) | 136 | 77.2% | $1.48 | 11.25 | No |
| 5 | S5: 9:35-36 high (theoretical) | 136 | 77.2% | $1.22 | 10.03 | No |
| 6 | S8: bar1_red drop>=1.0% ALL | 10 | 80.0% | $1.75 | 8.72 | Yes* (tiny N) |
| 7 | S5: 9:35 high (theoretical) | 136 | 71.3% | $0.97 | 7.28 | No |
| 8 | S7b: 5sec 1min high | 27 | 77.8% | $0.85 | 7.15 | No (requires perfect timing) |
| 9 | S8: bar1_red BAIL only | 93 | 63.4% | $0.98 | 6.58 | No (requires BAIL knowledge) |
| 10 | **S8: bar1_red drop>=0.7% ALL** | **22** | **59.1%** | **$0.89** | **4.67** | **Yes (best candidate)** |
| 11 | S8: bar1_red drop>=0.5% ALL | 47 | 55.3% | $0.34 | 1.96 | Marginal |
| 12 | S2: Limit at 9:34 close | 136 | 58.1% | $0.06 | 0.43 | Yes (no edge) |
| 13 | S1: First green bar | 136 | 52.2% | $0.00 | 0.02 | Yes (no edge) |
| 14 | S0b: 9:34 close | 136 | 50.7% | -$0.03 | -0.20 | Yes (no edge) |
| 15 | S6: New low after bounce | 109 | 52.3% | -$0.16 | -1.55 | Yes (no edge) |
| 16 | S3: Limit at 9:30 open | 47 | 44.7% | -$0.46 | -3.57 | Yes (negative edge) |

---

## Detailed Strategy Results

### S0: Benchmark — Short at 9:30 Open (known BAIL)

| Hold | N | Win% | Avg PnL | Sharpe | Avg MFE | Avg MAE |
|------|---|------|---------|--------|---------|---------|
| 3 | 136 | 89.7% | $2.33 | 17.79 | $3.46 | $0.29 |
| 5 | 136 | 86.8% | $2.54 | 17.01 | $4.04 | $0.49 |
| 10 | 136 | 79.4% | $2.60 | 13.04 | $4.74 | $0.88 |
| 20 | 136 | 77.9% | $2.52 | 10.12 | $5.56 | $1.33 |
| EOD | 136 | 61.8% | $2.48 | 3.82 | $9.94 | $4.78 |

### S0b: Short at 9:34 Close (confirmed BAIL, zero edge)

| Hold | N | Win% | Avg PnL | Sharpe | Avg MFE | Avg MAE |
|------|---|------|---------|--------|---------|---------|
| 3 | 136 | 50.0% | -$0.06 | -0.50 | $1.42 | $1.45 |
| 5 | 136 | 50.7% | -$0.03 | -0.20 | $1.65 | $1.68 |
| 10 | 136 | 53.7% | -$0.05 | -0.30 | $2.24 | $2.13 |
| 20 | 136 | 50.0% | -$0.01 | -0.04 | $3.01 | $2.86 |
| EOD | 136 | 52.2% | -$0.06 | -0.10 | $7.26 | $6.70 |

**Key finding:** MFE and MAE are nearly identical at every hold period. This is a coin flip. BAIL confirmation has zero predictive power for the NEXT move.

---

### S1: First Green Bar After BAIL

Short at the close of the first green (close > open) 1m bar after 9:34.

- **Fill rate:** 100% (always a green bar eventually)
- **Timing:** 49% at 9:35, 21% at 9:36, 19% at 9:37 (89% within 3 bars)

| Hold | N | Win% | Avg PnL | Sharpe | Avg MFE | Avg MAE |
|------|---|------|---------|--------|---------|---------|
| 3 | 136 | 50.7% | -$0.02 | -0.18 | $1.24 | $1.20 |
| 5 | 136 | 52.2% | $0.00 | 0.02 | $1.57 | $1.53 |
| 10 | 136 | 51.5% | $0.08 | 0.52 | $2.19 | $2.02 |
| 20 | 136 | 49.3% | $0.19 | 0.83 | $2.91 | $2.68 |
| EOD | 136 | 52.2% | -$0.04 | -0.06 | $7.17 | $6.56 |

**Verdict:** No edge. Waiting for a green bar does not improve entry.

---

### S2: Bounce to 9:34 Close (Limit Order)

Place limit order at 9:34 close price after BAIL confirmation.

- **Fill rate:** 100% within 5 minutes (price always returns to 9:34 close)

| Hold | N | Win% | Avg PnL | Sharpe | Avg MFE | Avg MAE |
|------|---|------|---------|--------|---------|---------|
| 3 | 136 | 55.9% | -$0.02 | -0.19 | $1.28 | $1.26 |
| 5 | 136 | 58.1% | $0.06 | 0.43 | $1.58 | $1.55 |
| 10 | 136 | 54.4% | $0.00 | 0.03 | $2.18 | $2.07 |
| 20 | 136 | 52.9% | $0.03 | 0.11 | $2.90 | $2.76 |
| EOD | 136 | 52.2% | -$0.06 | -0.10 | $7.19 | $6.62 |

Adding a buffer above 9:34 close does NOT help (tested +0.05% to +0.20%, all Sharpe near 0).

**Verdict:** Tiny edge at 5m (58% win) but Sharpe 0.43 is not tradeable.

---

### S3: Bounce to 9:30 Open (Limit Order at Full Retrace)

| Window | Fill Rate | 5m Win% | 5m PnL | 5m Sharpe |
|--------|-----------|---------|--------|-----------|
| 5 min | 34.6% | 44.7% | -$0.46 | -3.57 |
| 10 min | 39.7% | 44.4% | -$0.41 | -3.34 |
| 20 min | 50.0% | 44.1% | -$0.30 | -2.53 |
| 60 min | 58.8% | 41.2% | -$0.28 | -2.46 |

**Verdict:** Negative edge at all windows. When price fully retraces the BAIL drop, it tends to keep going UP. Selection bias: only the weakest BAIL days retrace fully.

---

### S4: Bounce Percentage of Drop

Entry = 9:34_close + (9:30_open - 9:34_close) * X%. Window: 20 minutes.

| Bounce % | Fill Rate | 5m Win% | 5m PnL | 5m Sharpe |
|----------|-----------|---------|--------|-----------|
| 25% | 80.9% | 50.9% | -$0.06 | -0.48 |
| 33% | 77.9% | 51.9% | -$0.13 | -0.95 |
| 50% | 67.6% | 47.8% | -$0.23 | -1.86 |
| 67% | 62.5% | 50.6% | -$0.20 | -1.70 |
| 75% | 59.6% | 46.9% | -$0.16 | -1.35 |
| 100% | 50.0% | 44.1% | -$0.30 | -2.53 |

**Verdict:** Every bounce level produces negative or zero edge. Larger bounces are worse (selection bias toward weaker BAIL days). This confirms: entering on the bounce is a losing proposition.

---

### S5: Time-Based Window Highs (Theoretical Maximum)

Short at the HIGH of post-9:34 time windows. This is NOT tradeable -- it represents the theoretical ceiling for any limit-order entry.

| Window | 3m Win% | 3m Sharpe | 5m Win% | 5m Sharpe | 10m Sharpe | 20m Sharpe |
|--------|---------|-----------|---------|-----------|------------|------------|
| 9:35 (1 bar) | 69.1% | 7.81 | 71.3% | 7.28 | 5.69 | 3.94 |
| 9:35-36 (2 bars) | 75.7% | 12.05 | 77.2% | 10.03 | 7.35 | 6.14 |
| 9:35-37 (3 bars) | 81.6% | 13.52 | 77.2% | 11.25 | 9.41 | 7.26 |
| 9:35-39 (5 bars) | 81.6% | 14.10 | 74.3% | 11.85 | 10.42 | 7.86 |
| 9:35-44 (10 bars) | 84.6% | 16.91 | 80.1% | 15.01 | 10.87 | 8.69 |

**Avg entry improvement over 9:34 close:**
- 1 bar: $0.91 (median $0.73)
- 3 bars: $1.45 (median $1.15)
- 5 bars: $1.68 (median $1.31)
- 10 bars: $2.13 (median $1.65)

**Key insight:** The 3-bar window high averages $1.45 above 9:34 close. This means the post-9:34 bounce is reliably $1-2. But you can only capture this with perfect timing. Any real limit order at a fixed price (S2, S4) gets filled at 9:34 close level, not at the actual local high.

**The gap between S5 (theoretical) and S2 (practical) is the entire story.** The bounce exists and is worth $1.45, but you can't predict WHEN it peaks. By the time you know it peaked, it's already reversing.

---

### S6: First New Low After Bounce

Wait for bounce above 9:34 close, then wait for close below 9:34 close (bear continuation signal).

- **Trades:** 109/136 (80% of BAIL days have bounce-then-continuation)
- **No bounce (straight down):** 11 days
- **No continuation (bounced and stayed up):** 16 days
- **Avg entry time:** 9:57

| Hold | N | Win% | Avg PnL | Sharpe | Avg MFE | Avg MAE |
|------|---|------|---------|--------|---------|---------|
| 3 | 109 | 45.0% | -$0.15 | -1.73 | $0.90 | $1.16 |
| 5 | 109 | 52.3% | -$0.16 | -1.55 | $1.21 | $1.43 |
| 10 | 109 | 46.8% | -$0.08 | -0.59 | $1.72 | $1.82 |
| 20 | 109 | 52.3% | $0.01 | 0.07 | $2.43 | $2.42 |
| EOD | 109 | 54.1% | $0.20 | 0.37 | $6.55 | $5.99 |

**Verdict:** No edge. "Confirmation of continuation" after a bounce does not predict further downside.

---

### S7: 5-Second Precision Entries (Dec 2025+)

| Strategy | N | 3m Win% | 3m Sharpe | 5m Win% | 5m Sharpe | EOD Sharpe |
|----------|---|---------|-----------|---------|-----------|------------|
| S7a: First micro-bounce | 27 | 63.0% | 2.23 | 59.3% | 0.82 | 4.18 |
| S7b: 1min local high | 27 | 74.1% | 9.88 | 77.8% | 7.15 | 5.70 |

**S7b is strong** but is the same concept as S5 -- shorting at the local high is great but requires perfect timing. N=27 is too small to be conclusive anyway.

---

### S8: Early BAIL Prediction (The Only Path Forward)

#### BAIL Probability by Early Signal

| Signal | Total | BAIL | P(BAIL) | Lift |
|--------|-------|------|---------|------|
| bar1 red (9:30 close < 9:30 open) | 146 | 93 | 63.7% | 1.32x |
| 9:31 close < 9:30 open | 144 | 108 | 75.0% | 1.56x |
| bar1 AND bar2 both red | 77 | 65 | 84.4% | 1.75x |
| 9:32 close < 9:30 open | 145 | 113 | 77.9% | 1.62x |
| bar1 red + drop > 0.5% | 47 | 41 | 87.2% | 1.81x |
| 9:33 close < 9:30 open | 137 | 122 | 89.1% | 1.85x |
| bar1+bar2+bar3 all red | 37 | 35 | 94.6% | 1.96x |

**The probability ramp is clear:**
- At 9:30: if bar1 red, 64% chance of BAIL
- At 9:31: if still below open, 75%
- At 9:32: 78%
- At 9:33: 89%
- At 9:33 with 3 consecutive red bars: 95%

#### Early Entry Performance (BAIL days only, entry at signal bar close)

**bar1_red (entry at 9:30 close, BAIL days only):**

| Hold | N | Win% | Avg PnL | Sharpe |
|------|---|------|---------|--------|
| 3 | 93 | 73.1% | $0.93 | 8.00 |
| 5 | 93 | 63.4% | $0.98 | 6.58 |
| 10 | 93 | 65.6% | $1.08 | 5.24 |
| 20 | 93 | 58.1% | $1.00 | 3.86 |

**But this requires BAIL knowledge!** On ALL days (including non-BAIL):

#### bar1_red with Drop-Size Filter (ALL days, the real tradeable signal)

| Filter | N | 5m Win% | 5m Avg | 5m Sharpe | Comment |
|--------|---|---------|--------|-----------|---------|
| Any red bar1 | 146 | 45.2% | -$0.21 | -1.20 | No edge |
| Drop >= 0.3% | 83 | 48.2% | -$0.00 | -0.02 | No edge |
| Drop >= 0.5% | 47 | 55.3% | $0.34 | 1.96 | Marginal |
| Drop >= 0.7% | 22 | 59.1% | $0.89 | 4.67 | **Interesting** |
| Drop >= 1.0% | 10 | 80.0% | $1.75 | 8.72 | Strong but N=10 |

**bar1_red + drop >= 0.7% full hold analysis (ALL days, N=22):**

| Hold | N | Win% | Avg PnL | Sharpe | MFE/MAE |
|------|---|------|---------|--------|---------|
| 1 | 22 | 72.7% | $0.67 | 10.29 | 1.90 |
| 3 | 22 | 68.2% | $1.00 | 6.95 | 2.12 |
| 5 | 22 | 59.1% | $0.89 | 4.67 | 1.83 |
| 10 | 22 | 59.1% | $0.36 | 1.33 | 1.49 |
| 20 | 22 | 45.5% | -$0.14 | -0.43 | 1.29 |
| EOD | 22 | 40.9% | -$2.01 | -3.46 | 0.85 |

**This is the best tradeable signal found.** At 1-3 minute holds, Sharpe 7-10 with N=22. Quick in, quick out. Edge decays fast -- by 10 minutes it's mostly gone.

#### S8c: Short at 9:33 Close on All Days

When 9:33 close < 9:30 open (89% BAIL prediction accuracy), N=137:

| Hold | N | Win% | Avg PnL | Sharpe |
|------|---|------|---------|--------|
| 3 | 137 | 51.8% | -$0.04 | -0.32 |
| 5 | 137 | 52.6% | -$0.11 | -0.71 |
| 10 | 137 | 54.7% | $0.14 | 0.73 |

**Verdict:** Despite 89% BAIL accuracy, the entry at 9:33 close has no edge because the drop already happened. You're entering 1 minute earlier than 9:34 close -- but you've already eaten 80% of the drop.

---

## Drop Size Analysis on BAIL Days

| Stat | $ | % of open |
|------|---|-----------|
| Mean | $2.54 | 0.70% |
| Median | $2.06 | 0.53% |
| P25 | $0.99 | - |
| P75 | $3.77 | - |
| Max | $9.16 | - |

## Bounce Analysis After 9:34 (% of drop recovered)

| Window | Mean | Median | P75 | P90 |
|--------|------|--------|-----|-----|
| 1 min | 209% | 35% | 90% | 224% |
| 2 min | 266% | 46% | 109% | 466% |
| 3 min | 305% | 47% | 148% | 526% |
| 5 min | 324% | 58% | 173% | 577% |
| 10 min | 405% | 75% | 197% | 770% |
| 20 min | 515% | 100% | 262% | 957% |

**The median bounce at 1 minute is only 35% of the drop, but the mean is 209%.** This extreme right skew means a minority of BAIL days bounce back violently (mean >>>>> median). This is why ALL bounce-based strategies fail -- the outlier bounces destroy the average.

---

## Key Insights

### 1. BAIL is a Lagging Indicator
BAIL confirmation at 9:34 tells you the drop already happened. The NEXT move after 9:34 is a coin flip. MFE and MAE are equal at every hold period. The market has already priced in the move.

### 2. The Bounce is Real But Unpredictable
Post-9:34, price reliably bounces $1-2 above the 9:34 close (median 35-47% retrace within 1-3 minutes). But the bounce magnitude varies wildly (mean 200-300% of drop). You can't set a fixed limit order that captures the peak -- any level you pick either (a) fills immediately with no edge or (b) doesn't fill on the best BAIL days.

### 3. Drop Size Predicts Continuation
When bar1 drops >= 0.7% from the open (N=22, ~8% of days), there is genuine short-term edge: 73% win at 1m, 68% at 3m. This works because a large first-bar drop signals momentum that has NOT been fully absorbed by 9:30 close.

### 4. Edge Decays Rapidly
Even the best signal (bar1 drop >= 0.7%) shows edge decaying from Sharpe 10 at 1 minute to Sharpe 1.3 at 10 minutes to negative at 20 minutes. This is a scalp, not a swing.

### 5. "Waiting for Confirmation" Destroys Edge
Every strategy that waits for post-9:34 confirmation (S1 green bar, S6 new low, S3/S4 bounce then short) produces zero edge. The confirmation itself is the problem -- by the time the setup is "confirmed," the opportunity is gone.

---

## Practical Recommendations

### Best Tradeable Strategy: bar1 Drop >= 0.7%

**Rules:**
1. At 9:30:59 (close of first 1-minute bar), check: is close < open AND (open - close) / open >= 0.7%?
2. If yes, short at 9:30 close (or market short at 9:31:00)
3. Hold 1-3 minutes maximum
4. Target: $0.67-1.00 per share (1-3 min avg)
5. Stop: above 9:30 open (natural stop, avg MAE at 3m is $1.18)

**Expected frequency:** ~22 trades per 282 days = about once per 2.5 weeks
**Expected edge:** Sharpe 7-10 at 1-3 minute holds
**Risk:** N=22 is small. Need more data to confirm robustness.

### What NOT to Do
- Do NOT wait for 9:34 BAIL confirmation to enter. Zero edge.
- Do NOT try to short on a bounce back to 9:34 close or 9:30 open. Negative edge.
- Do NOT use "first green bar" or "new low after bounce" as entry signals. No edge.
- Do NOT hold these trades beyond 5 minutes. Edge gone.

### Further Research
- Test bar1 drop >= 0.7% on other high-beta names (AMD, NVDA, META)
- Combine with premarket gap direction (gap down + bar1 drop >= 0.7% might be even stronger)
- Test if volume of bar1 adds signal (high volume drop = more conviction?)
- When more 5sec data accumulates, revisit S7b (1min local high) for sub-minute entries
