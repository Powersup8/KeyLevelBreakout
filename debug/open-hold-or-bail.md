# TSLA Calls: HOLD or BAIL?

**Data:** 271 trading days, 1-minute candles
**Setup:** You hold TSLA calls at market open. What early signals tell you to HOLD or BAIL?

## Baseline: Average Day Holding Calls

- Days: 271
- Day high above open: avg **$7.45**, median $5.68
- Day close vs open: avg **$-0.09**
- Day low below open: avg $-7.89
- % days close above open: **50%**
- % days high ≥ $1 above open: **89%**
- % days high ≥ $3 above open: **71%**
- % days high ≥ $5 above open: **55%**

### MFE by Hold Duration (from open)

| Hold | Avg MFE | Median MFE | ≥$1 | ≥$3 | ≥$5 |
|------|---------|------------|-----|-----|-----|
| 30m | $4.18 | $3.47 | 84% | 55% | 32% |
| 1h | $5.12 | $4.12 | 85% | 62% | 42% |
| 2h | $5.87 | $4.65 | 87% | 66% | 46% |
| eod | $7.45 | $5.68 | 89% | 71% | 55% |

---
## Signal 1: Price vs Open at Checkpoint

If price is above/below open at time T, what happens to your calls?

### At 30s

| Metric | Above open (125) | Below open (135) | Edge |
|--------|------------------------|-------------------------|------|
| Avg day high | $8.90 | $6.25 | $+2.64 |
| Avg day close | $+1.30 | $-1.09 | $+2.39 |
| % close above open | 58% | 44% | +13pp |
| Avg high time | 2:07 after open | 2:03 after open | |
| 30m MFE | $5.49 | $3.02 | $+2.47 |

### At 1m

| Metric | Above open (128) | Below open (138) | Edge |
|--------|------------------------|-------------------------|------|
| Avg day high | $9.31 | $5.58 | $+3.73 |
| Avg day close | $+1.42 | $-1.78 | $+3.21 |
| % close above open | 56% | 43% | +13pp |
| Avg high time | 2:06 after open | 1:58 after open | |
| 30m MFE | $5.96 | $2.45 | $+3.51 |

### At 2m

| Metric | Above open (125) | Below open (138) | Edge |
|--------|------------------------|-------------------------|------|
| Avg day high | $9.21 | $6.06 | $+3.15 |
| Avg day close | $+2.06 | $-1.77 | $+3.84 |
| % close above open | 60% | 41% | +19pp |
| Avg high time | 2:18 after open | 1:53 after open | |
| 30m MFE | $5.93 | $2.65 | $+3.28 |

### At 5m

| Metric | Above open (134) | Below open (133) | Edge |
|--------|------------------------|-------------------------|------|
| Avg day high | $9.99 | $4.83 | $+5.16 |
| Avg day close | $+3.22 | $-3.64 | $+6.87 |
| % close above open | 67% | 32% | +36pp |
| Avg high time | 2:29 after open | 1:39 after open | |
| 30m MFE | $6.24 | $2.13 | $+4.11 |

### At 10m

| Metric | Above open (126) | Below open (138) | Edge |
|--------|------------------------|-------------------------|------|
| Avg day high | $10.86 | $4.43 | $+6.43 |
| Avg day close | $+4.51 | $-4.17 | $+8.68 |
| % close above open | 70% | 31% | +39pp |
| Avg high time | 2:34 after open | 1:40 after open | |
| 30m MFE | $6.68 | $1.96 | $+4.72 |

### At 15m

| Metric | Above open (131) | Below open (132) | Edge |
|--------|------------------------|-------------------------|------|
| Avg day high | $10.61 | $4.47 | $+6.14 |
| Avg day close | $+3.53 | $-3.55 | $+7.08 |
| % close above open | 66% | 34% | +32pp |
| Avg high time | 2:32 after open | 1:40 after open | |
| 30m MFE | $6.48 | $1.95 | $+4.53 |

### At 30m

| Metric | Above open (129) | Below open (138) | Edge |
|--------|------------------------|-------------------------|------|
| Avg day high | $11.66 | $3.47 | $+8.19 |
| Avg day close | $+5.59 | $-5.51 | $+11.10 |
| % close above open | 77% | 23% | +54pp |
| Avg high time | 2:50 after open | 1:19 after open | |
| 30m MFE | $6.40 | $2.13 | $+4.27 |


---
## Signal 2: Opening Dip Size

How far does TSLA drop below open in the first 5 minutes → call fate?

| Dip | Days | Avg Day High | Avg Day Close | % Bull | 30m MFE | Day High Time |
|-----|------|-------------|---------------|--------|---------|---------------|
| No dip (≥$0) | 1 | $16.52 | $+15.48 | 100% | $7.62 | 4:32 |
| $0 to -$0.50 | 36 | $9.74 | $+2.61 | 67% | $7.64 | 1:56 |
| -$0.50 to -$1 | 33 | $10.22 | $+0.34 | 52% | $5.87 | 2:22 |
| -$1 to -$2 | 58 | $7.11 | $+1.11 | 50% | $4.21 | 2:16 |
| -$2 to -$3 | 57 | $7.09 | $+0.68 | 54% | $3.47 | 2:17 |
| -$3+ | 86 | $5.79 | $-2.89 | 38% | $2.48 | 1:42 |

---
## Signal 3: Recovery Speed

After dipping below open, how fast does TSLA recover? → call fate?

Days with ≥$0.50 dip: 234

| Recovery Time | Days | Avg Day High | Avg Day Close | % Bull | Avg Dip |
|---------------|------|-------------|---------------|--------|---------|
| 1-2 min | 87 | $9.40 | $+1.78 | 55% | $-1.54 |
| 2-5 min | 51 | $8.50 | $+2.54 | 67% | $-2.58 |
| 5-15 min | 20 | $7.88 | $+0.47 | 35% | $-3.57 |
| 15-30 min | 14 | $8.22 | $+3.61 | 71% | $-3.58 |
| Never (session) | 62 | $2.07 | $-7.71 | 18% | $-4.63 |

---
## Signal 4: Combined Signals — The Decision Matrix

Combining early checkpoint + dip size for HOLD/BAIL decision.

| Signal | Days | Day High | Day Close | % Bull | 30m MFE | 1h MFE | Action |
|--------|------|----------|-----------|--------|---------|--------|--------|
| 5m UP + small dip (<$1) | 61 | $10.94 | $+3.11 | 67% | $7.40 | $8.24 | **HOLD** ✓ |
| 5m UP + big dip (≥$1) | 73 | $9.19 | $+3.32 | 67% | $5.26 | $6.64 | **HOLD** ✓ |
| 5m DOWN + small dip (<$1) | 9 | $4.08 | $-7.70 | 11% | $2.74 | $3.39 | **BAIL** ✗ |
| 5m DOWN + big dip (≥$1) | 124 | $4.88 | $-3.35 | 33% | $2.08 | $2.81 | **BAIL** ✗ |
| 5m UP + recovered <2m | 105 | $10.27 | $+3.07 | 66% | $6.72 | $7.78 | **HOLD** ✓ |
| 5m UP + NOT recovered <2m | 29 | $8.97 | $+3.77 | 72% | $4.51 | $5.88 | **HOLD** ✓ |
| 5m DOWN + NOT recovered | 97 | $4.16 | $-4.34 | 29% | $1.75 | $2.22 | **BAIL** ✗ |
| 5m UP + gap up | 72 | $10.88 | $+3.86 | 67% | $6.53 | $7.96 | **HOLD** ✓ |
| 5m UP + gap down | 59 | $8.96 | $+2.24 | 66% | $5.89 | $6.65 | **HOLD** ✓ |
| 5m DOWN + gap up | 71 | $4.39 | $-4.08 | 28% | $2.02 | $2.46 | **BAIL** ✗ |
| 5m DOWN + gap down | 60 | $5.28 | $-3.33 | 35% | $2.28 | $3.27 | **BAIL** ✗ |
| 1m UP + 5m UP | 97 | $10.31 | $+2.84 | 65% | $6.76 | $7.77 | LEAN HOLD |
| 1m DOWN + 5m UP (reversal) | 32 | $8.79 | $+3.67 | 72% | $4.67 | $6.00 | **HOLD** ✓ |
| 1m UP + 5m DOWN (fakeout) | 30 | $6.22 | $-3.11 | 30% | $3.47 | $4.51 | **BAIL** ✗ |
| 1m DOWN + 5m DOWN | 103 | $4.43 | $-3.80 | 32% | $1.74 | $2.37 | **BAIL** ✗ |
| 5m > +$1 | 108 | $10.51 | $+3.61 | 69% | $6.83 | $7.85 | **HOLD** ✓ |
| 5m > +$2 | 76 | $11.79 | $+4.71 | 75% | $7.95 | $9.01 | **HOLD** ✓ |
| 5m < -$1 | 106 | $4.77 | $-3.67 | 32% | $1.93 | $2.66 | **BAIL** ✗ |
| 5m < -$2 | 71 | $4.74 | $-4.19 | 31% | $1.68 | $2.24 | **BAIL** ✗ |
| 15m UP | 131 | $10.61 | $+3.53 | 66% | $6.48 | $7.73 | **HOLD** ✓ |
| 15m DOWN | 132 | $4.47 | $-3.55 | 34% | $1.95 | $2.60 | **BAIL** ✗ |
| 30m UP | 129 | $11.66 | $+5.59 | 77% | $6.40 | $8.18 | **HOLD** ✓ |
| 30m DOWN | 138 | $3.47 | $-5.51 | 23% | $2.13 | $2.32 | **BAIL** ✗ |

---
## When to Take Profit (Call Holders)

If you decide to HOLD, when is the best time to sell?

### Bull days (135 days)

| Checkpoint | Avg Price vs Open | % Still Above Open | Avg MFE to Here |
|------------|-------------------|-------------------|-----------------|
| 5m | $+1.25 | 67% | — |
| 10m | $+1.50 | 65% | — |
| 15m | $+1.82 | 64% | — |
| 30m | $+2.96 | 73% | — |

- Avg day high: **$11.73**
- Avg time of day high: **3:36** after open
- Median time of day high: **3:34** after open

### Bear days (133 days) — when to get out

| Checkpoint | Avg Price vs Open | % Above Open | Window Closing |
|------------|-------------------|-------------|----------------|
| 1m | $-0.63 | 41% | |
| 2m | $-0.77 | 38% | |
| 3m | $-0.84 | 39% | |
| 5m | $-1.19 | 32% | |
| 10m | $-1.91 | 27% | |
| 15m | $-2.04 | 31% | |
| 30m | $-3.13 | 21% | |

- Even on bear days, avg day high above open: **$3.15**
- Avg time of day high (bear): **0:29** after open
- Bear day high ≥$1: **77%**
