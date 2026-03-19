# TSLA Fakeout Deep Research — Opening Pattern Analysis
*Date: 2026-03-18 | 137 days with sub-30s data, 281 total*

## 1. A6 Pattern Baseline (30s bars)

| Pattern | n | Day Win% | Avg P&L | ORB Bull% | Worst% |
|---|---|---|---|---|---|
| UP_UP | 30 | 67% | $1.60 | 57% | 13% |
| UP_DN | 36 | 42% | $0.16 | 53% | 36% |
| DN_UP | 35 | 54% | $0.72 | 49% | 23% |
| DN_DN | 36 | 44% | $-2.50 | 42% | 39% |

## 2. UP→DOWN Deep Dive — Winner vs Loser Anatomy

UP→DOWN days: 36 total, 15 winners, 21 losers

| Metric | Winners avg | Losers avg | Spread | Discriminant? |
|---|---|---|---|---|
| Bar1 move ($) | 1.427 | 1.272 | +0.155 | maybe |
| Bar2 move ($) | -0.722 | -1.043 | +0.321 | YES |
| Bar1 range ($) | 2.625 | 2.524 | +0.102 |  |
| Giveback (bar2/bar1) | 5.187 | 1.622 | +3.565 | YES |
| Giveback absolute ($) | 0.722 | 1.043 | -0.321 | YES |
| Peak to bar2 close ($) | 1.464 | 1.662 | -0.198 | maybe |
| Peak to bar2 close (% of bar1 range) | 0.592 | 0.678 | -0.086 | maybe |
| Bar2 made new low | 0.067 | 0.048 | +0.019 | maybe |
| Volume shift (bar2/bar1) | 0.324 | 0.382 | -0.058 | maybe |
| Time to peak (0=start, 1=end) | 0.333 | 0.250 | +0.083 | maybe |
| Momentum decay (t3-t1) | -0.490 | -0.477 | -0.013 |  |
| First 60s max drawdown ($) | 2.437 | 2.688 | -0.251 |  |
| Recovery from low ($) | 1.236 | 0.968 | +0.268 | maybe |
| 1m bar body % of range | 0.321 | 0.276 | +0.045 | maybe |

## 3. Giveback Threshold — Does Severity Matter?

| Giveback % | n | Day Win% | Avg P&L | ORB Bull% | Worst% | Verdict |
|---|---|---|---|---|---|---|
| <20% (mild pullback) | 9 | 56% | $2.65 | 56% | 22% | OK |
| 20-40% | 4 | 25% | $-6.24 | 50% | 50% | DANGER |
| 40-60% | 4 | 75% | $11.28 | 75% | 0% | OK |
| 60-80% | 3 | 67% | $3.29 | 67% | 33% | OK |
| >80% (hard reversal) | 16 | 25% | $-3.00 | 44% | 50% | DANGER |

## 4. Other Factors Within UP→DOWN

### Bar2 breaks bar1 low?
- Yes — new low: n=11, Win=27%, Avg=$-2.21, Worst=64%
- No — held above: n=25, Win=48%, Avg=$1.21, Worst=24%

### Volume acceleration (bar2 vol / bar1 vol)
- Low vol shift (selling dries up): n=18, Win=50%, Avg=$2.38
- High vol shift (selling intensifies): n=18, Win=33%, Avg=$-2.05

### Time to peak within first 60s
- Early peak (<30%): n=22, Win=36%, Avg=$0.04
- Mid peak (30-60%): n=12, Win=50%, Avg=$1.28
- Late peak (>60%): n=2, Win=50%, Avg=$-5.13

### Momentum decay (3rd third move - 1st third move)
- Accelerating (recovering): n=16, Win=38%, Avg=$0.12, Worst=44%
- Decelerating (fading): n=20, Win=45%, Avg=$0.20, Worst=30%

## 5. UP→DOWN × 5m Rule × ORB Outcome

| Pattern | 5m | ORB | n | Win% | Avg P&L | Worst% |
|---|---|---|---|---|---|---|
| UP_DN | HOLD | Bull break | 15 | 67% | $5.20 | 13% |
| UP_DN | BAIL | Bull break | 4 | 50% | $6.39 | 25% |
| UP_DN | BAIL | Bear/None | 15 | 20% | $-5.64 | 60% |

## 6. All Patterns — Giveback as Universal Metric

Does giveback % matter even for non-UP→DOWN patterns?


### UP_UP
- Low giveback: n=15, Win=67%, Avg=$0.60
- High giveback: n=15, Win=67%, Avg=$2.61

### UP_DN
- Low giveback: n=18, Win=56%, Avg=$2.96
- High giveback: n=18, Win=28%, Avg=$-2.63

### DN_UP
- Low giveback: n=18, Win=56%, Avg=$0.49
- High giveback: n=17, Win=53%, Avg=$0.97

### DN_DN
- Low giveback: n=18, Win=28%, Avg=$-4.61
- High giveback: n=18, Win=61%, Avg=$-0.39

---
## 7. Recommendations

*(Filled after reviewing results)*
