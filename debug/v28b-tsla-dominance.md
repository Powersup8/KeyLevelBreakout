# TSLA Dominance Analysis: Structural Edge vs Regime Overfitting

Dataset: 2025-09-29 to 2026-03-03 | 870 trades | 10 symbols


## 1. Monthly P&L by Symbol (ATR units)

```
month   2025-09  2025-10  2025-11  2025-12  2026-01  2026-02  2026-03  TOTAL
symbol                                                                      
AAPL      -0.01    -0.68    -1.82    -1.54    -1.79     0.75     0.00  -5.09
AMD       -0.45     3.03    -2.55    -1.19     3.32     3.42     0.79   6.36
AMZN      -0.40    -1.20    -0.29    -1.41    -1.09     0.59    -0.15  -3.95
GOOGL     -0.09    -1.01     1.43    -0.49     4.04    -0.55     0.00   3.33
META      -0.30     1.30    -1.13     1.32     3.37     2.91     0.55   8.03
MSFT      -0.12    -0.91     0.04    -0.43    -0.96     4.10    -0.30   1.41
NVDA       1.53    -1.32     1.29    -0.93    -1.09     1.03    -0.30   0.21
QQQ        0.00    -1.87     0.45    -0.29     1.38    -1.15    -0.25  -1.73
SPY        0.00    -1.28     0.57    -0.45     0.28    -2.86     0.57  -3.18
TSLA      -0.04     1.85    10.21     1.11     7.70    -0.12    -0.60  20.11
ALL        0.12    -2.09     8.20    -4.30    15.15     8.12     0.30  25.51
```

**TSLA monthly detail:**
```
         trades  pnl_atr  wins  avg_pnl    wr
month                                        
2025-09       1   -0.036     0   -0.036   0.0
2025-10      20    1.852     5    0.093  25.0
2025-11      21   10.206    14    0.486  66.7
2025-12      24    1.110    10    0.046  41.7
2026-01      19    7.702    11    0.405  57.9
2026-02      18   -0.122     7   -0.007  38.9
2026-03       4   -0.600     0   -0.150   0.0
```

TSLA profitable months: 4/7

## 2. TSLA P&L by Direction

**BULL:** 56 trades | P&L: 8.45 ATR | Win rate: 26/56 (46.4%) | Avg: 0.151 ATR
**BEAR:** 51 trades | P&L: 11.66 ATR | Win rate: 21/51 (41.2%) | Avg: 0.229 ATR

**TSLA P&L by direction and month:**
```
month      2025-09  2025-10  2025-11  2025-12  2026-01  2026-02  2026-03  TOTAL
direction                                                                      
bear          0.00     0.61     7.69    -0.76     4.31     0.41     -0.6  11.66
bull         -0.04     1.24     2.52     1.87     3.39    -0.54      0.0   8.45
```

## 3. TSLA vs Other Symbols: Signal Characteristics

```
       trades  pnl_atr  avg_pnl  win_rate  avg_mfe  avg_atr  avg_vol
AAPL     81.0   -5.089   -0.063    22.222    0.162    2.219    5.094
AMD      91.0    6.362    0.070    35.165    0.303    1.926    3.967
AMZN     90.0   -3.949   -0.044    26.667    0.186    2.023    4.336
GOOGL    83.0    3.329    0.040    40.964    0.274    2.205    4.818
META     88.0    8.026    0.091    38.636    0.371    2.067    4.247
MSFT     77.0    1.411    0.018    31.169    0.238    2.321    5.318
NVDA     96.0    0.213    0.002    38.542    0.220    2.216    4.744
QQQ      79.0   -1.732   -0.022    32.911    0.197    1.997    3.996
SPY      78.0   -3.177   -0.041    30.769    0.215    1.681    3.272
TSLA    107.0   20.113    0.188    43.925    0.464    2.169    3.794
_REST   763.0    5.394    0.007    33.159    0.242    2.074    4.421
```

**Key comparisons:**
- TSLA win rate: 43.9% vs REST: 33.2%
- TSLA avg P&L/trade: 0.188 ATR vs REST: 0.007 ATR
- TSLA avg MFE: 0.464 ATR vs REST: 0.242 ATR
- TSLA avg vol mult: 3.8x vs REST: 4.4x
- TSLA avg ATR ($): 2.17 vs REST: 2.07

## 4. System Performance WITHOUT TSLA

Total trades (ex-TSLA): 763
Total P&L: 5.39 ATR
Win rate: 33.2%
Avg P&L/trade: 0.007 ATR
Profit factor: 1.08
Max drawdown: -14.09 ATR
Peak P&L: 6.09 ATR

**Monthly P&L (ex-TSLA):**
```
month
2025-09    0.16
2025-10   -3.94
2025-11   -2.01
2025-12   -5.41
2026-01    7.45
2026-02    8.25
2026-03    0.90
Freq: M
```
Profitable months: 4/7

**With vs Without TSLA:**
- Full system: 25.51 ATR
- TSLA only:   20.11 ATR (78.9%)
- Ex-TSLA:     5.39 ATR (21.1%)

## 5. Per-Symbol Monthly Consistency

```
        months_active  months_profitable consistency  total_pnl  best_month  worst_month  monthly_std  concentration
symbol                                                                                                              
AAPL                6                  1         1/6      -5.09        0.75        -1.82         1.06            NaN
AMD                 7                  4         4/7       6.36        3.42        -2.55         2.41          53.76
AMZN                7                  1         1/7      -3.95        0.59        -1.41         0.71            NaN
GOOGL               6                  2         2/6       3.33        4.04        -1.01         1.90         121.24
META                7                  5         5/7       8.03        3.37        -1.13         1.62          41.99
MSFT                7                  2         2/7       1.41        4.10        -0.96         1.76         290.69
NVDA                7                  3         3/7       0.21        1.53        -1.32         1.22         716.26
QQQ                 6                  2         2/6      -1.73        1.38        -1.87         1.15            NaN
SPY                 6                  3         3/6      -3.18        0.57        -2.86         1.35            NaN
TSLA                7                  4         4/7      20.11       10.21        -0.60         4.30          50.74
```

**Interpretation:**
- `concentration` = best month as % of total P&L (100% = all profit from one month = very fragile)
- Consistent edge: multiple profitable months, low concentration, low std

## 6. TSLA ATR/Volatility: Is the Edge Just More Movement?

P&L is already ATR-normalized, so pnl_atr controls for move size.
If TSLA's edge were just volatility, its avg pnl_atr would be similar to others.

**Dollar ATR by symbol:**
```
symbol
MSFT     2.32
AAPL     2.22
NVDA     2.22
GOOGL    2.20
TSLA     2.17
META     2.07
AMZN     2.02
QQQ      2.00
AMD      1.93
SPY      1.68
```

**ATR-normalized P&L distribution:**
```
         mean    std   25%    50%    75%
symbol                                  
AAPL   -0.063  0.184 -0.15 -0.150 -0.025
AMD     0.070  0.349 -0.15 -0.150  0.239
AMZN   -0.044  0.175 -0.15 -0.150  0.025
GOOGL   0.040  0.249 -0.15 -0.023  0.171
META    0.091  0.413 -0.15 -0.150  0.196
MSFT    0.018  0.283 -0.15 -0.150  0.144
NVDA    0.002  0.195 -0.15 -0.106  0.128
QQQ    -0.022  0.206 -0.15 -0.150  0.050
SPY    -0.041  0.172 -0.15 -0.150  0.083
TSLA    0.188  0.561 -0.15 -0.150  0.261
```

**Follow-through MFE (30-bar window) by symbol:**
```
        signals  avg_mfe  avg_mae  avg_ratio
symbol                                      
AAPL        590    0.501    0.562      8.694
AMD         609    0.964    1.175      9.727
AMZN        607    0.494    0.602      7.133
GOOGL       562    0.840    0.810     11.970
META        594    1.513    1.661     10.860
MSFT        498    0.876    1.105      9.928
NVDA        621    0.546    0.520     11.545
QQQ         505    0.925    0.863     15.351
SPY         581    0.806    0.750     11.720
TSLA        581    1.575    1.284     11.799
```

## 7. Verdict: Structural Edge or Regime Overfitting?

**Evidence AGAINST pure regime dependency:**
- Direction split is 58/42 bear/bull -- not extreme. Both sides profitable.
- Bull trades are profitable in 4 of 6 months (Oct, Nov, Dec, Jan).
- Bear trades are profitable in 4 of 6 months (Oct, Nov, Jan, Feb).
- TSLA's edge is NOT just its downtrend. The system captures moves in both directions.

**Evidence FOR concentration risk:**
- Nov 2025 alone = 10.21 ATR = 51% of TSLA's total P&L. Remove Nov and TSLA drops to +9.9 ATR.
- Jan 2026 = 7.70 ATR = 38%. Two months account for 89% of TSLA's total.
- TSLA's monthly std (4.30) is 2-3x higher than any other symbol -- the variance is enormous.
- Recent fade: Feb -0.12, Mar -0.60. TSLA may already be losing its edge as the trend stabilizes.

**The real structural difference (not volatility):**
- TSLA's dollar ATR ($2.17) is middle-of-pack, NOT higher than peers.
- But TSLA's ATR-normalized MFE (0.464) is nearly 2x the REST average (0.242).
- TSLA's follow-through MFE (1.575) is top-tier, AND its MFE/MAE ratio (1.23) is the best of all symbols -- moves carry further in TSLA's favor.
- TSLA's win rate (43.9%) is the highest. Not just bigger winners, but more of them.
- This suggests TSLA genuinely responds better to key-level breakout signals. Whether this persists in a different regime is unknown.

**Ex-TSLA system health:**
- +5.39 ATR over 763 trades = barely profitable (0.007 ATR/trade, PF 1.08).
- First 4 months were underwater (-11.20 ATR). Rescued by Jan-Feb 2026 (+15.70 ATR).
- Max drawdown of -14.09 ATR means the ex-TSLA system would have been psychologically brutal to trade.
- Only META (5/7 months profitable, +8.03 ATR) shows genuine consistency among non-TSLA symbols.
- AMD (+6.36) and GOOGL (+3.33) are positive but erratic. AAPL, AMZN, SPY, QQQ are net losers.

**Bottom line:**
TSLA's dominance is PARTIALLY structural (genuine signal quality -- higher MFE, better MFE/MAE ratio, higher win rate even after ATR normalization) and PARTIALLY concentration risk (51% from one month, fading in recent data). It is NOT simply a downtrend artifact -- bull trades are also profitable.

**Recommendations:**
1. Use ex-TSLA P&L (+5.39 ATR, PF 1.08) as the conservative floor. The system works without TSLA, but barely.
2. TSLA is the best symbol for this strategy, but do not size positions as if +20 ATR/quarter is the norm. The Nov spike is unlikely to repeat.
3. Monitor TSLA monthly -- Feb/Mar fade may signal regime shift. If 3+ consecutive months are flat/negative, reassess.
4. Consider capping per-symbol concentration at ~40% of total P&L in position sizing to reduce single-name risk.
5. Focus improvement efforts on the 4 net-losing symbols (AAPL, AMZN, SPY, QQQ) -- if their signal quality can be improved or their signals filtered out, ex-TSLA PF improves significantly.