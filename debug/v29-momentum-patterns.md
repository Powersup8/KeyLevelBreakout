# v29 Momentum Patterns Analysis (After 9:50 ET)

Data: 11461 signals, 17244 follow-through rows
Actionable signals after 9:50: 3647
30-min follow-through after 9:50: 3573

## 1. After-9:50 Big Bars (range_atr >= 1.5)

Total big bars after 9:50: **1482**
With 30-min follow-through: 1408

### By signal type:
  BRK: n=492, MFE avg=0.867 med=0.543, MAE avg=0.771 med=0.479, pos=90%, runners(≥1.0)=30%

  REV: n=732, MFE avg=0.865 med=0.580, MAE avg=0.779 med=0.471, pos=93%, runners(≥1.0)=32%

  VWAP: n=184, MFE avg=0.728 med=0.515, MAE avg=0.808 med=0.602, pos=93%, runners(≥1.0)=26%

### By direction:
  bull: n=649, MFE avg=0.767 med=0.547, MAE avg=0.850 med=0.537, pos=92%, runners(≥1.0)=28%

  bear: n=759, MFE avg=0.917 med=0.571, MAE avg=0.719 med=0.447, pos=91%, runners(≥1.0)=32%

### By time bucket:
  9:00-9:59: n=255, MFE avg=0.975 med=0.705, MAE avg=0.808 med=0.487, pos=91%, runners(≥1.0)=38%

  10:00-10:59: n=722, MFE avg=0.837 med=0.549, MAE avg=0.800 med=0.579, pos=92%, runners(≥1.0)=29%

  11:00-11:59: n=108, MFE avg=1.064 med=0.823, MAE avg=0.526 med=0.374, pos=95%, runners(≥1.0)=43%

  12:00-12:59: n=50, MFE avg=0.791 med=0.640, MAE avg=0.610 med=0.412, pos=96%, runners(≥1.0)=24%

  13:00-13:59: n=68, MFE avg=0.681 med=0.447, MAE avg=0.628 med=0.436, pos=85%, runners(≥1.0)=28%

  14:00-14:59: n=61, MFE avg=0.623 med=0.495, MAE avg=0.529 med=0.253, pos=92%, runners(≥1.0)=23%

  15:00-15:59: n=144, MFE avg=0.708 med=0.372, MAE avg=1.055 med=0.450, pos=90%, runners(≥1.0)=22%

### Range ATR distribution:
  1.5-2.0: n=843, MFE avg=0.921 med=0.606, MAE avg=0.827 med=0.547, pos=94%, runners(≥1.0)=33%

  2.0-3.0: n=496, MFE avg=0.740 med=0.500, MAE avg=0.744 med=0.471, pos=89%, runners(≥1.0)=27%

  3.0+: n=69, MFE avg=0.727 med=0.419, MAE avg=0.454 med=0.281, pos=88%, runners(≥1.0)=29%


## 2. Volume Surge After 9:50 (vol >= 5.0)

Total vol surge signals after 9:50: **50**
With 30-min follow-through: 48

### Overall:
  vol>=5x: n=48, MFE avg=0.738 med=0.547, MAE avg=0.928 med=0.622, pos=94%, runners(≥1.0)=27%

### By volume bucket:
  5-10x: n=48, MFE avg=0.738 med=0.547, MAE avg=0.928 med=0.622, pos=94%, runners(≥1.0)=27%

  10-20x: n=0

  20x+: n=0

### By signal type:
  BRK: n=25, MFE avg=0.554 med=0.462, MAE avg=0.896 med=0.604, pos=92%, runners(≥1.0)=16%

  REV: n=12, MFE avg=1.159 med=0.803, MAE avg=1.055 med=0.357, pos=100%, runners(≥1.0)=42%

  VWAP: n=11, MFE avg=0.698 med=0.764, MAE avg=0.862 med=0.808, pos=91%, runners(≥1.0)=36%

### Combined: vol>=5x AND range_atr>=1.5:
  vol>=5x + big bar: n=47, MFE avg=0.750 med=0.578, MAE avg=0.925 med=0.604, pos=94%, runners(≥1.0)=28%


## 3. Consecutive Directional Bars (same symbol, same day, same direction)

Consecutive directional signals (2nd+ in streak): **4242**
After 9:50: 2393
With 30-min FT: 2364

### By streak position:
  position 2: n=834, MFE avg=1.093 med=0.658, MAE avg=1.031 med=0.687, pos=93%, runners(≥1.0)=36%

  position 3: n=610, MFE avg=1.084 med=0.691, MAE avg=1.023 med=0.727, pos=93%, runners(≥1.0)=38%

  position 4: n=422, MFE avg=1.073 med=0.739, MAE avg=1.007 med=0.700, pos=93%, runners(≥1.0)=38%

  position 5: n=255, MFE avg=0.933 med=0.578, MAE avg=1.071 med=0.714, pos=91%, runners(≥1.0)=31%

  position 6: n=127, MFE avg=1.158 med=0.756, MAE avg=0.999 med=0.746, pos=91%, runners(≥1.0)=38%

  position 7: n=56, MFE avg=1.299 med=0.792, MAE avg=0.886 med=0.693, pos=96%, runners(≥1.0)=43%

  position 8: n=28, MFE avg=1.258 med=0.673, MAE avg=5.013 med=0.996, pos=89%, runners(≥1.0)=39%

  position 9: n=15, MFE avg=1.099 med=0.608, MAE avg=1.105 med=0.622, pos=87%, runners(≥1.0)=27%

  position 10: n=5, MFE avg=0.528 med=0.533, MAE avg=1.161 med=1.100, pos=100%, runners(≥1.0)=0%

  position 11: n=4, MFE avg=0.320 med=0.233, MAE avg=1.780 med=1.817, pos=75%, runners(≥1.0)=0%

  position 12: n=4, MFE avg=0.758 med=0.403, MAE avg=1.389 med=1.118, pos=100%, runners(≥1.0)=25%

  position 13: n=2, MFE avg=0.313 med=0.313, MAE avg=0.384 med=0.384, pos=100%, runners(≥1.0)=0%

  position 14: n=2, MFE avg=0.037 med=0.037, MAE avg=0.880 med=0.880, pos=50%, runners(≥1.0)=0%

### Consecutive vs Non-consecutive (all after 9:50, 30-min):
  ALL after 9:50: n=3573, MFE avg=1.062 med=0.667, MAE avg=1.027 med=0.669, pos=93%, runners(≥1.0)=36%

  CONSECUTIVE only: n=2364, MFE avg=1.076 med=0.683, MAE avg=1.073 med=0.710, pos=93%, runners(≥1.0)=37%

  NON-CONSECUTIVE: n=1139, MFE avg=1.037 med=0.631, MAE avg=0.951 med=0.587, pos=93%, runners(≥1.0)=35%


## 4. VWAP Cross Momentum

VWAP cross signals (vwap flips between consecutive signals): **1631**
After 9:50: 1103
With 30-min FT: 1073

### Overall VWAP cross:
  VWAP cross: n=1073, MFE avg=1.033 med=0.633, MAE avg=0.959 med=0.586, pos=93%, runners(≥1.0)=35%

### By cross direction:
  below→above: n=561, MFE avg=0.986 med=0.625, MAE avg=1.064 med=0.608, pos=93%, runners(≥1.0)=32%

  above→below: n=512, MFE avg=1.084 med=0.656, MAE avg=0.843 med=0.577, pos=93%, runners(≥1.0)=37%

### VWAP cross aligned with signal direction:
  ALIGNED (bull+above / bear+below): n=1072, MFE avg=1.033 med=0.635, MAE avg=0.959 med=0.586, pos=93%, runners(≥1.0)=35%

  MISALIGNED (bull+below / bear+above): n=1, MFE avg=0.388 med=0.388, MAE avg=0.131 med=0.131, pos=100%, runners(≥1.0)=0%


## 5. Best Intraday Momentum Fingerprint (30-min MFE >= 1.0 ATR after 9:50)

Runners (MFE >= 1.0): **1290** (36.1%)
Non-runners: 2283

### Runner profile vs Non-runner:

  vol         : runner avg=1.6 med=1.5 | non-runner avg=1.8 med=1.5 | gap=-0.1
  adx         : runner avg=29.4 med=27.0 | non-runner avg=29.1 med=27.0 | gap=+0.3
  body        : runner avg=66.2 med=68.0 | non-runner avg=68.1 med=70.0 | gap=-1.9
  ramp        : runner avg=1.0 med=0.9 | non-runner avg=1.1 med=1.0 | gap=-0.1
  range_atr   : runner avg=1.3 med=1.2 | non-runner avg=1.5 med=1.4 | gap=-0.2

  **direction** distribution:
    bear        : runner=53% | non-runner=50% | gap=+3%
    bull        : runner=47% | non-runner=50% | gap=-3%

  **ema** distribution:
    bear        : runner=50% | non-runner=53% | gap=-3%
    bull        : runner=50% | non-runner=47% | gap=+3%

  **vwap** distribution:
    above       : runner=47% | non-runner=50% | gap=-3%
    below       : runner=53% | non-runner=50% | gap=+3%

  **type** distribution:
    BRK         : runner=22% | non-runner=23% | gap=-0%
    REV         : runner=64% | non-runner=64% | gap=+1%
    VWAP        : runner=13% | non-runner=14% | gap=-1%

  is_bigmove      : runner=11% | non-runner=16% | gap=-5%
  is_bodywarn     : runner=26% | non-runner=31% | gap=-4%

  **Time distribution:**
    10:00-10:59: runner=44% | non-runner=43% | gap=+1%
    11:00-11:59: runner=19% | non-runner=16% | gap=+3%
    12:00-12:59: runner=8% | non-runner=8% | gap=+0%
    13:00-13:59: runner=6% | non-runner=7% | gap=-1%
    14:00-14:59: runner=5% | non-runner=8% | gap=-3%
    15:00-15:59: runner=8% | non-runner=10% | gap=-1%

  **Symbol runner rate** (signals with MFE >= 1.0):
    TSLA  : 65% (238/365)
    META  : 57% (211/373)
    AMD   : 40% (143/358)
    MSFT  : 39% (108/274)
    QQQ   : 38% (125/329)
    GOOGL : 35% (124/356)
    SPY   : 31% (129/413)
    AAPL  : 20% (71/348)
    NVDA  : 20% (75/370)
    AMZN  : 17% (66/387)

## 6. Worst vs Best Comparison (Top 20% vs Bottom 20% MFE after 9:50)

Bottom 20% (worst): n=714, MFE range [-1.242, 0.210]
Top 20% (best): n=714, MFE range [1.644, 13.500]

### Feature comparison:

Feature          |       Best (top 20%) |   Worst (bottom 20%) |        Gap
-----------------+----------------------+----------------------+-----------
vol              |                 1.62 |                 1.84 |      -0.22
adx              |                29.47 |                29.35 |      +0.12
body             |                64.73 |                67.64 |      -2.91
ramp             |                 1.01 |                 1.14 |      -0.13
range_atr        |                 1.24 |                 1.52 |      -0.28

### Categorical differences:

**direction:**
  bear        : best=56% | worst=51% | gap=+4%
  bull        : best=44% | worst=49% | gap=-4%

**ema:**
  bear        : best=51% | worst=54% | gap=-3%
  bull        : best=49% | worst=46% | gap=+3%

**vwap:**
  above       : best=44% | worst=48% | gap=-4%
  below       : best=56% | worst=52% | gap=+4%

**type:**
  BRK         : best=23% | worst=26% | gap=-3%
  REV         : best=65% | worst=58% | gap=+7%
  VWAP        : best=11% | worst=15% | gap=-4%

is_bigmove      : best=9% | worst=20% | gap=-11%
is_bodywarn     : best=22% | worst=28% | gap=-6%

**Time distribution:**
  10:00-10:59: best=46% | worst=42% | gap=+4%
  11:00-11:59: best=18% | worst=12% | gap=+6%
  12:00-12:59: best=7% | worst=7% | gap=+0%
  13:00-13:59: best=6% | worst=9% | gap=-4%
  14:00-14:59: best=4% | worst=8% | gap=-4%
  15:00-15:59: best=9% | worst=11% | gap=-2%

**Symbol distribution:**
  AAPL  : best=4% | worst=13% | gap=-9%
  AMD   : best=11% | worst=9% | gap=+2%
  AMZN  : best=4% | worst=17% | gap=-13%
  GOOGL : best=10% | worst=10% | gap=+1%
  META  : best=19% | worst=7% | gap=+12%
  MSFT  : best=8% | worst=8% | gap=-1%
  NVDA  : best=4% | worst=12% | gap=-8%
  QQQ   : best=9% | worst=9% | gap=+0%
  SPY   : best=8% | worst=10% | gap=-1%
  TSLA  : best=23% | worst=6% | gap=+17%

## 7. Key Takeaways

**Top numeric differentiators (runner vs non-runner, % difference):**
  - range_atr: -11%
  - ramp: -6%
  - vol: -6%
  - body: -3%
  - adx: +1%

**Runner rate by hour (after 9:50):**
  10:00-10:59: 36% runner rate (n=1557, avg MFE=1.088)
  11:00-11:59: 41% runner rate (n=609, avg MFE=1.231)
  12:00-12:59: 37% runner rate (n=284, avg MFE=1.065)
  13:00-13:59: 32% runner rate (n=244, avg MFE=0.889)
  14:00-14:59: 26% runner rate (n=238, avg MFE=0.716)
  15:00-15:59: 33% runner rate (n=330, avg MFE=1.041)

**Combo filters (after 9:50, 30-min):**
  vol>=5 + range_atr>=1.5: n=47, runner=28%, MFE=0.750, MAE=0.925
  vol>=5 + ema aligned: n=41, runner=24%, MFE=0.687, MAE=0.897
  range_atr>=1.5 + ema aligned: n=909, runner=31%, MFE=0.866, MAE=0.786
  vol>=5 + range_atr>=1.5 + ema aligned: n=40, runner=25%, MFE=0.700, MAE=0.894
  big bar + ema + vwap aligned: n=903, runner=31%, MFE=0.867, MAE=0.788

---

## 8. Interpretation and Actionable Findings

### Surprise #1: After 9:50, the "momentum" filters DON'T help
Volume surges (>=5x) after 9:50 are RARE (only 50 signals out of 3647) and actually UNDERPERFORM the baseline (27% runner rate vs 36% overall). Big bars (range_atr>=1.5) also underperform at 30% runner rate. Combo filters (vol+big bar+EMA) are even worse at 25%. **After 9:50, extreme momentum signals are likely exhaustion moves, not continuation.**

### Surprise #2: 11:00 AM is the hidden sweet spot
The 11:00-11:59 hour has the HIGHEST runner rate (41%) and best avg MFE (1.231 ATR) of any hour after 9:50. For big bars specifically, 11:00 hour hits 43% runner rate with 1.064 avg MFE. This is midday when most traders expect "chop" -- but the data shows big bars at this hour are the most reliable continuation signals of the day.

### Surprise #3: Smaller bars run MORE than big bars
Runners have LOWER range_atr (1.3 avg) than non-runners (1.5 avg). The 1.5-2.0 ATR bucket has 33% runner rate while 3.0+ has only 29%. **The biggest bars after 9:50 are exhaustion, not initiation.** The sweet spot is moderate-sized bars (1.2-1.5 ATR).

### Surprise #4: Consecutive streaks barely help
Consecutive same-direction signals (37% runner) vs non-consecutive (35%) is only a +2% edge -- statistically negligible. Streak position 2-4 averages 37% but position 5+ degrades to 31%. **Chasing momentum streaks after 9:50 adds risk (MAE 1.07 vs 0.95) without proportional reward.**

### Surprise #5: VWAP crosses = no edge
VWAP cross signals (35% runner) match the overall baseline exactly. Even "aligned" crosses (bull + crossing above) show no advantage. **VWAP crosses after 9:50 are noise, not signal.**

### Surprise #6: Symbol selection is the #1 differentiator
TSLA (65% runner) and META (57%) are 3-4x more likely to produce runners after 9:50 than AMZN (17%) or AAPL/NVDA (20%). Top 20% MFE signals are 23% TSLA vs 6% in the bottom 20%. **Symbol matters more than any filter.**

### Surprise #7: is_bigmove is a NEGATIVE signal
Big-move bars (range >= 2x ATR) are 11% of runners but 16% of non-runners, and 9% of best vs 20% of worst. **The bigmove flag predicts exhaustion, not continuation, after 9:50.**

### Surprise #8: REV type outperforms
REV signals are 65% of the best outcomes vs 58% of worst -- the largest type gap (+7%). Reversals after 9:50 have better follow-through than breakouts. For high-vol signals specifically, REV has 42% runner rate vs BRK at 16%.

### Summary for v29 design:
- **Don't chase big bars or volume after 9:50** -- they predict exhaustion
- **11 AM big bars are the exception** -- highest runner rate of the day
- **Symbol filter is king** -- TSLA/META >> AAPL/AMZN/NVDA after 9:50
- **Moderate bars (1.2-1.5 ATR) with bear direction** produce the best runners
- **REV signals outperform BRK after 9:50** -- favor reversals over breakouts
