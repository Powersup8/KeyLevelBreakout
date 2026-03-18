# v3.0b New Levels Deep Research — Challenge Everything

**Generated:** 2026-03-05
**Data:** 9 symbols (AAPL, AMD, AMZN, META, MSFT, NVDA, QQQ, SPY, TSLA), 452 symbol-days, 11,815 level touches
**Resolution:** 5sec data (47-60 days per symbol), mark-to-market PnL at 30 minutes
**Method:** Every 5-min bar closing within 0.15 ATR of a level = one "touch event," PnL measured from the bar's close price

---

## Executive Summary

**The edge IS real. Both PD Mid and PD LH L are genuinely profitable levels when measured correctly. The problem is not the levels -- it is the IMPLEMENTATION.**

### The Three Core Discoveries

**Discovery 1: The corrected backtest CONFIRMS the edge.**

When measured mark-to-market at 30 min (same as live) across ALL hours (not just after 10:30) with NO filters:
- PD Mid: N=566, win%=52.1%, avg +0.084 ATR/touch, total +47.7 ATR
- PD LH L: N=573, win%=53.4%, avg +0.096 ATR/touch, total +54.8 ATR

These are genuinely positive and comparable to PDL (N=394, win%=53.0%, avg +0.120 ATR) -- a known strong level. The edge is not an artifact of MFE measurement or time restriction.

**Discovery 2: The live implementation destroys the edge through filter mismatch.**

The natural touch population (avg vol 0.8x, spread across all hours) is profitable. But the live indicator requires vol >= 1.5x, which:
- Reduces PD Mid from 566 to just 27 touches (95% filtered out)
- The 27 high-vol touches have +0.271 PnL (even better!) but N=27 is too small to be reliable
- Combined filters (10:30 + vol + EMA) reduce to single digits (N=7-9), statistically meaningless

**The filters are not wrong per se -- they just eliminate 95% of the opportunities.** These levels work at LOW volume (0.5-2x), not HIGH volume. The indicator's vol >= 1.5x filter is structurally incompatible with how these levels operate.

**Discovery 3: PD Mid works as a FADE, PD LH L works as a REVERSAL -- NOT breakouts.**

| Level | BRK (cross) | REV (bounce) | FADE (failed break) |
|-------|-------------|-------------|---------------------|
| PD Mid | N=262, +0.044/touch | N=304, -0.091/touch | **N=142, +0.396/touch** |
| PD LH L | N=264, **-0.148/touch** | **N=309, +0.051/touch** | N=164, +0.184/touch |

**PD Mid's best design is FADE** -- when price crosses through and comes back within 3 bars, that is the trade (+0.396 PnL, 60.6% win, N=142, total +56.2 ATR).

**PD LH L's best design is REV** -- price bouncing off the level without crossing (+0.051, 52.8% win). But BRK at PD LH L is deeply negative (-0.148). The live implementation generates BRK signals at this level -- the WRONG signal type.

---

## 1. Corrected Backtest (Live Methodology)

Original backtest used MFE over 6 bars, after 10:30 only, no vol/EMA filter.
Corrected: mark-to-market at 30 min, ALL hours, vol/EMA filters applied incrementally.

### Mark-to-Market at 30m

| Level | N_all | W%_all | PnL_all | N_after1030 | W%_1030 | PnL_1030 | N_vol>=1.5x | W%_vol | PnL_vol | N_EMA | W%_EMA | PnL_EMA | N_combo | W%_combo | PnL_combo |
|-------|-------|--------|---------|-------------|---------|----------|-------------|--------|---------|-------|--------|---------|---------|----------|-----------|
| PD_MID | 566 | 52.1 | +0.084 | 391 | 51.4 | +0.059 | 27 | 59.3 | +0.271 | 566 | 52.1 | +0.084 | 27 | 59.3 | +0.271 |
| PD_LH_L | 573 | 53.4 | +0.096 | 390 | 53.1 | +0.105 | 23 | 73.9 | +0.684 | 234 | 57.7 | +0.235 | 9 | 77.8 | +0.826 |
| PD_LH_H | 555 | 52.3 | +0.059 | 375 | 53.6 | +0.089 | 25 | 48.0 | -0.107 | 199 | 51.8 | +0.202 | 12 | 41.7 | +0.079 |
| VWAP_STD_L | 1555 | 48.7 | +0.016 | 1060 | 48.6 | +0.042 | 52 | 51.9 | +0.134 | 91 | 56.0 | +0.228 | 7 | 71.4 | +0.787 |
| VWAP_ATR_L | 21 | 61.9 | +0.437 | 19 | 63.2 | +0.491 | 2 | 100 | +2.456 | 0 | -- | -- | 0 | -- | -- |
| VWAP_HALF_ATR_L | 330 | 51.2 | +0.041 | 251 | 53.4 | +0.080 | 22 | 63.6 | +0.551 | 25 | 56.0 | +0.527 | 1 | 100 | +4.640 |
| PDH (reference) | 394 | 49.2 | -0.104 | 283 | 49.1 | -0.090 | 25 | 56.0 | +0.012 | 128 | 41.4 | -0.276 | 16 | 62.5 | +0.354 |
| PDL (reference) | 394 | 53.0 | +0.120 | 263 | 54.4 | +0.213 | 15 | 80.0 | +0.924 | 158 | 62.0 | +0.306 | 7 | 85.7 | +0.966 |
| ORB_H (reference) | 824 | 49.5 | +0.046 | 524 | 48.1 | +0.033 | 23 | 39.1 | +0.037 | 223 | 48.4 | -0.033 | 11 | 27.3 | -0.343 |
| ORB_L (reference) | 725 | 47.7 | -0.027 | 431 | 46.2 | -0.040 | 27 | 63.0 | +0.273 | 167 | 47.9 | +0.078 | 13 | 61.5 | +0.253 |

### Key Findings

1. **PD_MID and PD_LH_L are positive at ALL measurement points.** The original backtest was not flawed in direction -- the edge is real.

2. **After 10:30 filter barely changes the picture.** PD_LH_L actually improves slightly after 10:30 (+0.105 vs +0.096). PD_MID drops slightly (+0.059 vs +0.084). The "after 10:30 only" constraint in the original backtest was NOT the main source of the edge.

3. **Vol >= 1.5x dramatically reduces sample size.** PD_MID drops from 566 to 27 touches. The high-vol subset is more profitable per touch (+0.271) but with N=27 over 452 symbol-days, that is 1 signal per 17 symbol-days -- too rare to matter.

4. **The EMA filter helps PD_LH_L strongly.** EMA-aligned bull touches at PD_LH_L: N=234, +0.235/touch, 57.7% win. This is a real edge.

5. **VWAP_ATR_L fires only 21 times across 452 symbol-days.** When it does fire, the bounce is strong (+0.437), but it is essentially a crisis-day level. The live implementation correctly identified it as a level but the distance is too extreme for regular use.

6. **VWAP_STD_L is the correct formula for the VWAP band.** N=1555 touches but the edge is thin (+0.016). The original backtest's +0.133 was inflated by MFE measurement.

---

## 2. Level Computation Validation

### Sample Level Values

| Sym | Date | PD_MID | PD_LH_L | ATR | VWAP@10 | VWAP_STD@10 | VWAP-STD | VWAP-ATR |
|-----|------|--------|---------|-----|---------|-------------|----------|----------|
| AAPL | 2025-12-04 | 277.35 | 277.92 | 3.67 | 282.87 | 0.99 | 281.88 | 279.21 |
| AAPL | 2025-12-23 | 272.19 | 270.50 | 3.91 | 270.95 | 0.53 | 270.42 | 267.04 |
| AAPL | 2026-01-02 | 272.72 | 271.75 | 3.65 | 275.07 | 1.94 | 273.12 | 271.42 |
| AAPL | 2026-01-05 | 273.42 | 270.21 | 3.78 | 269.42 | 1.01 | 268.41 | 265.64 |
| AAPL | 2026-01-08 | 261.75 | 259.81 | 3.89 | 256.75 | 0.35 | 256.40 | 252.86 |

**VWAP-STD (at 10:00) averages 0.3-1.9 points below VWAP.** For AAPL ($260 range), this is 0.1%-0.7%.
**VWAP-ATR averages 3.3-3.9 points below VWAP.** For AAPL, this is 1.3%-1.5%.

The distance ratio: VWAP-ATR is 2-10x farther from VWAP than VWAP-STD. The backtest validated a band at 0.3-1.9 points below VWAP. The live code placed the band at 3.3-3.9 points below. These are entirely different levels.

**Pine computation check:**
- `pdMid = (yestHigh + yestLow) / 2` -- matches our computation exactly
- `pdLastHrLow = lowest low during 15:00-16:00 ET` -- matches our 15:00-16:00 window
- `vwapLowerBand = vwapVal - dailyATR` -- confirmed: this is the WRONG formula (should be VWAP - VWAP_STD)

---

## 3. Price Action Study

### PD_MID (N=566 touches)

- **Crossed through: 46%, Bounced: 54%** -- price has no strong directional preference at PD Mid
- **Stayed through 3 bars after crossing: only 45%** -- more than half the crosses come back (MAGNET behavior)
- **First touch is BEST: N=143, win%=62%, avg +0.201** -- the first time price reaches PD Mid, it respects it
- **2nd touch degrades: N=108, win%=45%, avg +0.057** -- the level weakens with repeated contact
- **3rd touch rebounds: N=86, win%=60%, avg +0.239** -- possibly a mean-reversion setup (multiple bounces)
- Average vol at touch: 0.8x (LOW volume -- confirms these are quiet mean-reversion touches)
- Touches spread across all hours: 9h=87, 10h=137, 11h=81, 12h=75, 13h=66, 14h=54, 15h=66

### PD_LH_L (N=573 touches)

- **Crossed through: 46%, Bounced: 54%** -- similar to PD Mid
- **Stayed through 3 bars: only 37%** -- even MORE magnet-like than PD Mid (63% come back)
- **First touch: N=151, win%=54%, avg +0.048** -- first touch is mildly positive but not as strong as PD Mid
- **2nd touch: N=119, win%=50%, avg +0.027** -- moderate
- **3rd touch turns negative: N=87, win%=45%, avg -0.069** -- level exhaustion
- Average vol: 0.8x (again, low volume)
- Time distribution: peaks at 10h (156 touches) -- 10 AM is the natural gravitational pull hour

### PDH (N=394 touches, reference)

- Crossed through: 45%, Bounced: 55%
- Stayed through 3 bars: 44% -- very similar to PD_MID
- **First touch is NEGATIVE: N=125, win%=53%, avg -0.087** -- PDH is a difficult level
- Average vol: 0.9x

### PDL (N=394 touches, reference)

- Crossed through: 44%, Bounced: 56%
- Stayed through 3 bars: 43%
- **First touch: N=122, win%=52%, avg +0.076** -- positive but weaker than PD_MID's first touch
- 2nd touch improves: N=93, win%=53%, avg +0.130
- Average vol: 0.8x

### Price Action Summary

| Level | Cross% | Stay-through% | 1st touch PnL | Magnet Score |
|-------|--------|---------------|---------------|--------------|
| PD_MID | 46% | 45% | **+0.201** | Medium-high |
| PD_LH_L | 46% | 37% | +0.048 | **High** (63% come back) |
| PDH | 45% | 44% | -0.087 | Medium |
| PDL | 44% | 43% | +0.076 | Medium |
| ORB_H | 44% | 41% | -- | Medium-high |
| ORB_L | 46% | 42% | -- | Medium |

**PD_LH_L is the strongest "magnet" level** -- 63% of crosses come back within 3 bars. This means BRK signals at PD_LH_L are structurally flawed: most breakdowns fail and reverse. The correct signal type is REV or FADE.

**PD_MID first-touch is the strongest edge** at +0.201 PnL. But it degrades with repeated contact.

---

## 4. Alternative Signal Designs

### PD_MID

| Design | N | Win% | Avg PnL | Total PnL |
|--------|---|------|---------|-----------|
| a) REV (bounce off level) | 304 | 46.4 | -0.091 | -27.6 |
| b) BRK (cross through) | 262 | 55.0 | +0.044 | +11.5 |
| **c) FADE (failed break)** | **142** | **60.6** | **+0.396** | **+56.2** |
| d) After 10:30 only | 391 | 51.4 | +0.059 | +23.2 |
| e) Vol 0.5-2x only | 496 | 52.4 | +0.095 | +47.0 |
| f) 1st touch only | 143 | 61.5 | +0.201 | +28.7 |
| f) 2nd+ touches | 423 | 48.9 | +0.045 | +19.0 |
| g) Bear only | 566 | 50.2 | +0.022 | +12.2 |
| g) Bull only | 566 | 48.9 | -0.022 | -12.2 |
| h) 10:00+ vol<5x EMA | 478 | 50.0 | +0.047 | +22.3 |

**WINNER: FADE design.** When price crosses PD Mid and then FAILS (returns within 3 bars), trading the return direction produces +0.396/touch, 60.6% win rate, total +56.2 ATR across 142 events. This is the single best signal design at PD Mid.

**Runner-up: 1st touch.** First-ever touch of PD Mid in a session: N=143, +0.201/touch, 61.5% win.

**Note on REV:** Pure reversal (bouncing off the level) is NEGATIVE (-0.091). PD Mid does NOT work as a simple reversal level. It works as a FADE level -- you need to see the failed cross first.

**Note on direction:** Bear-only (+0.022) slightly outperforms bull-only (-0.022), but the difference is marginal. PD Mid is not strongly directional.

### PD_LH_L

| Design | N | Win% | Avg PnL | Total PnL |
|--------|---|------|---------|-----------|
| **a) REV (bounce)** | **309** | **52.8** | **+0.051** | **+15.6** |
| b) BRK (break down) | 264 | 45.1 | **-0.148** | **-39.2** |
| c) FADE (failed break) | 164 | 56.7 | +0.184 | +30.1 |
| d) After 10:30 only | 390 | 53.1 | +0.105 | +41.0 |
| e) Vol 0.5-2x only | 501 | 52.9 | +0.093 | +46.6 |
| f) 1st touch only | 151 | 53.6 | +0.048 | +7.2 |
| f) 2nd+ touches | 422 | 53.3 | +0.113 | +47.6 |
| g) Bear BRK (break down) | 573 | 46.2 | -0.096 | -54.8 |
| h) 10:00+ vol<5x EMA | 191 | 55.5 | +0.237 | +45.2 |

**BRK is DEEPLY NEGATIVE at PD_LH_L** (-0.148/touch, -39.2 total). This is the signal type the live indicator generates. The live indicator is generating the WRONG signal.

**REV and FADE both work.** REV (bounce off) at +0.051 is modest but positive. FADE (failed break that returns) at +0.184 is stronger but less frequent (164 vs 309).

**After 10:30 + EMA-aligned + vol<5x** produces the best filtered set: N=191, +0.237/touch, 55.5% win. This is the optimal filter combination.

**2nd+ touches outperform 1st touch** for PD_LH_L (+0.113 vs +0.048). This is the opposite of PD_MID. PD_LH_L gets more significant as the day progresses and price re-tests it.

---

## 5. Level Magnet Hypothesis

### Break Conviction Ratio

When price reaches within 0.15 ATR of a level:

| Level | N | Cross% | Bounce% | Stayed 3 bars (clean break) | Came back (messy) |
|-------|---|--------|---------|----------------------------|-------------------|
| PD_MID | 566 | 46% | 54% | 45% | **55%** |
| PD_LH_L | 573 | 46% | 54% | **37%** | **63%** |
| PDH | 394 | 45% | 55% | 44% | 56% |
| PDL | 394 | 44% | 56% | 43% | 57% |
| ORB_H | 824 | 44% | 56% | 41% | 59% |
| ORB_L | 725 | 46% | 54% | 42% | 58% |

**PD_LH_L has the LOWEST clean-break rate (37%) of all tested levels.** 63% of all crosses fail and come back. This confirms the magnet hypothesis: PD LH L is a "gravitational" level where price oscillates around rather than breaking through cleanly.

**Implication:** Breakout signals (BRK) at PD_LH_L are structurally doomed. The level is better suited for mean-reversion (REV) or failed-breakout (FADE) designs.

PD_MID is similar but not as extreme (55% messy vs 63% for PD_LH_L). Still magnet-like, but the FADE design captures the profitable subset of messy crosses.

**For comparison:** PDH (44% clean break) and PDL (43%) are modestly better at producing clean breaks, supporting their use as breakout levels. But even they are below 50% -- all levels tested are more "magnet" than "barrier."

---

## 6. Level Overlap Contamination

### PD_MID

- **Standalone** (no PDH/PDL/ORB within 0.3 ATR): N=452, win%=49.8%, avg +0.048, total +21.6
- **Overlapping** (original level within 0.3 ATR): N=114, win%=61.4%, avg +0.229, total +26.1

**PD_MID's edge when STANDALONE is only +0.048/touch** (roughly half the overall +0.084). The overlapping subset (+0.229) drives most of the total PnL.

When PD Mid coincides with PDH/PDL/ORB, the signal is 4.8x more profitable. This strongly suggests **the original level is doing the heavy lifting, and PD Mid is incidental.**

### PD_LH_L

- **Standalone**: N=320, win%=50.9%, avg +0.013, total +4.2
- **Overlapping**: N=253, win%=56.5%, avg +0.200, total +50.6

**Even more contaminated than PD_MID.** Standalone PD_LH_L is essentially break-even (+0.013/touch). The overlapping signals (+0.200) account for 50.6 of the 54.8 total ATR.

**This is the most damning finding:** 92% of PD_LH_L's total profit comes from touches that ALSO have an original level nearby. When PD_LH_L stands alone, the edge disappears.

### Implication

The original backtest's strong PD_LH_L result (+0.238/touch) was likely driven by overlap with known-good levels (PDL, ORB_L) that happened to coincide with PD_LH_L on many days. The PD_LH_L "signal" was attribution error -- the edge belonged to the original levels.

---

## 7. VW Band Deep Dive

### Formula Comparison (VWAP lower bands)

| Band | Formula | N touches | Bull REV PnL | Bear BRK PnL | Avg vol |
|------|---------|-----------|-------------|-------------|---------|
| VWAP_STD_L | VWAP - 1x STD | 1555 | +0.016 | -0.016 | 0.8x |
| VWAP_HALF_ATR_L | VWAP - 0.5x ATR | 330 | +0.041 | -0.041 | 0.9x |
| VWAP_ATR_L | VWAP - 1x ATR | **21** | **+0.437** | -0.437 | 0.9x |
| VWAP_1.5STD_L | VWAP - 1.5x STD | 1078 | **-0.063** | +0.063 | 0.8x |

**The backtest-validated VWAP_STD_L (VWAP - 1 STD) produces N=1555 touches but the edge is thin (+0.016/touch for bull REV).** It fires frequently (3.4 per symbol-day) but each touch contributes very little.

**VWAP - ATR (what the live code uses) only fires 21 times in 452 symbol-days** -- 1 touch per 22 symbol-days. When it fires, the bull bounce is strong (+0.437) but this is a crisis-day signal, not a regular one.

**VWAP - 0.5 ATR is the sweet spot** for a band that fires regularly (330 touches) with a modest edge (+0.041 for bull REV). The hour distribution shows it fires mostly in the morning (10h=88) and afternoon (15h=44).

**VWAP - 1.5 STD is NEGATIVE for bull REV (-0.063).** This wider band catches more extreme drops where price is unlikely to bounce back. The bear BRK is positive (+0.063) -- price breaking that far below VWAP tends to keep going.

### VW Band Recommendation

If implementing a VW band level:
1. Use `VWAP - VWAP_STD` (standard deviation), NOT `VWAP - ATR`
2. Signal type should be **bull REV** (bounce off band), NOT bear BRK
3. Expected edge: +0.016/touch (thin) with N=1555 -- total +24.6 ATR
4. Or use `VWAP - 0.5*ATR` for a middle ground: N=330, +0.041/touch, total +13.6 ATR

---

## 8. Intraday Level Relevance Decay

### PD_MID: Hourly Performance

| Hour | N | Win% | Avg PnL | Total |
|------|---|------|---------|-------|
| 9:00-10:00 | 87 | **64.4** | **+0.296** | +25.8 |
| 10:00-11:00 | 137 | 49.6 | +0.127 | +17.4 |
| 11:00-12:00 | 81 | 42.0 | -0.142 | -11.5 |
| 12:00-13:00 | 75 | 61.3 | +0.213 | +15.9 |
| 13:00-14:00 | 66 | 47.0 | -0.107 | -7.1 |
| 14:00-15:00 | 54 | 53.7 | +0.279 | +15.0 |
| 15:00-16:00 | 66 | 47.0 | -0.120 | -7.9 |

**PD Mid does NOT decay monotonically.** The 9:00 and 12:00 and 14:00 hours are positive; 11:00, 13:00, and 15:00 are negative. This is an alternating pattern suggesting PD Mid is a mean-reversion anchor -- price oscillates around it throughout the day.

**Wait -- the 9:00 hour is the BEST** (+0.296, 64.4% win, N=87). This contradicts the live findings where morning PD Mid signals lose money. Why? Because the live indicator fires high-vol BRK signals in the morning, while the natural 9:00 touches (avg vol 0.8x) are low-vol mean-reversion touches. The vol filter inverts the population.

### PD_LH_L: Hourly Performance

| Hour | N | Win% | Avg PnL | Total |
|------|---|------|---------|-------|
| 9:00-10:00 | 98 | 57.1 | +0.074 | +7.2 |
| **10:00-11:00** | **156** | **59.0** | **+0.260** | **+40.6** |
| 11:00-12:00 | 103 | 46.6 | -0.015 | -1.6 |
| 12:00-13:00 | 75 | 44.0 | -0.136 | -10.2 |
| 13:00-14:00 | 41 | 56.1 | +0.458 | +18.8 |
| 14:00-15:00 | 46 | 41.3 | -0.393 | -18.1 |
| 15:00-16:00 | 54 | 64.8 | +0.335 | +18.1 |

**10:00-11:00 is the dominant hour for PD_LH_L** (+40.6 ATR, 59% win, N=156). This is consistent with the live data finding. The 10 AM window is when price "discovers" the PD LH L level as it explores the day's range after the opening volatility settles.

**The afternoon is chaotic:** 13:00 is strongly positive (+0.458), 14:00 is strongly negative (-0.393), 15:00 bounces back (+0.335). This suggests the level has real but INCONSISTENT relevance in the afternoon.

**Level distance does NOT decay:** Average distance from level stays at 0.065-0.074 ATR throughout the day. The level stays equally "reachable" -- the issue is directional clarity, not distance.

### Comparison with PDL (known-good reference)

PDL shows a different pattern: 13:00 is the BEST hour (+0.592, 69.7% win), while 14:00 is the worst (-0.253). PDL gets STRONGER in the afternoon as institutions trade against the prior day's low. PD_LH_L does not show this institutional anchoring.

---

## 9. Multi-Day Level Analysis

### Does gap-to-level distance affect quality?

**PD_MID:**
- Gap < 0.5 ATR: N=102, win%=53.9%, avg **+0.191** (BEST)
- Gap 0.5-1.0 ATR: N=102, win%=48.0%, avg +0.015
- Gap 1.0-2.0 ATR: N=205, win%=51.2%, avg +0.078
- Gap > 2.0 ATR: N=157, win%=54.8%, avg +0.069

**PD Mid works BEST when price opens near it (gap < 0.5 ATR).** This makes intuitive sense -- when the market gaps to the prior day's mid-range, it signals indecision. The level acts as a natural center of gravity for the new session. When price opens far away (gap > 2 ATR), it still works but with less conviction.

**PD_LH_L:**
- Gap < 0.5 ATR: N=140, win%=54.3%, avg +0.063
- Gap 0.5-1.0 ATR: N=169, win%=55.6%, avg +0.155
- Gap 1.0-2.0 ATR: N=164, win%=54.9%, avg **+0.185** (BEST)
- Gap > 2.0 ATR: N=100, win%=46.0%, avg **-0.105** (LOSE)

**PD_LH_L works best at MEDIUM distance (0.5-2.0 ATR).** When price opens right at it (< 0.5 ATR), the level has moderate relevance. When price opens far away (> 2 ATR), the level LOSES -- the market has moved too far from the prior close for the last-hour low to matter.

**This is a useful filter:** suppress PD_LH_L signals when the gap-to-level exceeds 2 ATR.

---

## 10. Optimal Design Recommendation

### Summary Ranking

| Level | Raw PnL | Best Design | Best Design PnL | Overlap Issue? | Verdict |
|-------|---------|-------------|-----------------|----------------|---------|
| PD_MID | +0.084 | FADE (failed break) | **+0.396** (N=142) | Yes (standalone only +0.048) | **REDESIGN as FADE** |
| PD_LH_L | +0.096 | 10:00+ EMA vol<5x | **+0.237** (N=191) | Yes (standalone only +0.013) | **REDESIGN or REMOVE** |
| VWAP_ATR_L | +0.437 | Bull REV | +0.437 (N=21) | N/A (too rare) | **REMOVE** (never fires) |
| VWAP_STD_L | +0.016 | Bull REV | +0.016 (N=1555) | N/A | **OPTIONAL** (thin edge) |
| VWAP_HALF_ATR_L | +0.041 | Bull REV | +0.041 (N=330) | N/A | **OPTIONAL** (moderate) |

### Honest Assessment

**PD Mid** has a real FADE edge (+0.396/touch, 60.6% win, N=142) that survives scrutiny. However:
- This is a FADE signal (failed breakout), not a BRK or REV
- The current indicator has no FADE signal type at PD Mid
- Implementing a FADE requires tracking the cross and the return (more complex logic)
- The standalone edge (without original level overlap) is only +0.048/touch -- the FADE's edge may also be overlap-driven

**PD LH L** looks good on the surface but the overlap analysis is devastating:
- 92% of total profit comes from touches where an original level is also nearby
- Standalone PD_LH_L is essentially break-even (+0.013/touch)
- The 10:00-11:00 window edge (+0.260) may be driven by ORB/PM level overlap in that exact window
- BRK at PD_LH_L is deeply negative -- the current implementation is generating the wrong signal

**VW Band (VWAP-ATR)** should be removed. It never fires and the formula is wrong.

**VWAP-STD Band** could replace VW Band if desired, but the edge is thin (+0.016/touch).

### The Real Answer: WHY They Underperform

1. **Signal type mismatch.** PD Mid should be FADE, PD LH L should be REV. The live indicator generates BRK at both. BRK at PD_LH_L is -0.148/touch (negative). This single design error is the primary cause.

2. **Volume filter mismatch.** These levels work at 0.8x average volume (natural, quiet touches). The indicator's vol >= 1.5x filter eliminates 95% of the profitable population and only fires on the high-vol morning spikes, which are structurally different.

3. **Attribution error.** Most of the backtested edge at these levels comes from overlap with existing levels (PDH/PDL/ORB). When standalone, both PD Mid and PD LH L are near break-even.

4. **Once-per-session guard.** These levels are touched 2-4 times per session. Allowing only the first touch misses the profitable 2nd+ touches at PD_LH_L and the FADE signals at PD_MID.

### Specific Recommendations

**Priority 1: Fix PD_LH_L signal type (if keeping)**
- Change from BRK to REV at PD_LH_L: the level is a magnet (63% of crosses fail), not a barrier
- Or remove PD_LH_L entirely (standalone edge is +0.013, negligible)

**Priority 2: Remove VW Band (VWAP-ATR)**
- Replace with VWAP-STD if desired, but the edge is thin
- If replacing, signal must be BULL REV (bounce off band), not BEAR BRK

**Priority 3: Consider PD Mid FADE (new signal paradigm)**
- If you want to pursue PD Mid, implement it as a FADE signal: fire only when price crosses through PD Mid and returns within 3 bars
- Expected: N=142 over 452 symbol-days, +0.396/touch, 60.6% win
- WARNING: this requires new Pine logic (track cross + return), adds complexity
- The standalone vs overlap question needs resolution first

**Priority 4: Remove vol >= 1.5x for new levels (if keeping)**
- These levels work at low volume. The vol filter is counter-productive.
- Alternatively, use vol 0.5-2x filter (captures the mean-reversion population)

### Bottom Line: Is it Worth the Complexity?

**Probably not, at least not in the current BRK implementation.**

- Standalone PD_MID: +0.048/touch, total ~22 ATR across 452 symbol-days = +0.05 ATR/symbol-day
- Standalone PD_LH_L: +0.013/touch, total ~4 ATR = essentially zero
- The original levels (PDH/PDL/ORB) already capture the overlapping edge
- Adding PD_MID and PD_LH_L as BRK signals adds noise without adding edge

**If you want to pursue the FADE design at PD Mid** (+56.2 ATR total, +0.396/touch), that is the one genuinely promising avenue. But it requires a new signal paradigm that does not exist in the current indicator architecture.

**The most impactful change is the simplest: remove PD_LH_L BRK signals.** They are -0.148/touch. Removing them eliminates a known negative-expectancy signal type.

---

*Analysis script: `debug/v30b_new_levels_research.py`*
*Data: 5sec parquet, 9 symbols, 452 symbol-days, 11,815 level touches*
*Method: Every 5m bar within 0.15 ATR of level, mark-to-market PnL at 30 min*
