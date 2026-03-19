# TSLA Open-Scalp Deep Research
*Generated: 2026-03-14*

Extends prior open-scalp-learnings.md (Parts A-F). Investigates 14 new hypotheses.

## R01: Opening Range Breakout (ORB)

ORB defined as first 5m candle H/L (9:30-9:34). After 9:35, price breaks above ORB High or below ORB Low.

| ORB Break | Days | Day Above Open | Avg Day Close | Avg Day High |
|-----------|------|----------------|---------------|--------------|
| Bull (ORB High first) | 142 | 70% | $3.98 | $10.25 |
| Bear (ORB Low first) | 136 | 29% | $-4.36 | $4.47 |

*n=278 days total*

### ORB Bull break timing
- Bull break: 205 days break ORB High. Median at 8m. 25th pct=5m, 75th=30m
- Bear break: 209 days break ORB Low. Median at 10m. 25th pct=5m, 75th=25m

## R02: First 1m Bar Size as Momentum Predictor

Hypothesis: a large opening bar (high range) signals a momentum day.

| Bar Size | Days | 5m Above Open | Day Above | Avg Day Close | Avg Day High |
|----------|------|---------------|-----------|---------------|--------------|
| Q1 tiny (≤$2.06) | 71 | 56% | 39% | $-1.63 | $6.38 |
| Q2 small ($2.06-$2.62) | 68 | 51% | 51% | $0.15 | $7.51 |
| Q3 medium ($2.62-$3.32) | 69 | 51% | 61% | $2.68 | $8.69 |
| Q4 large (>$3.32) | 70 | 50% | 49% | $-1.54 | $7.14 |

### Green vs Red First Bar
| 1st Bar | Days | 5m Above | Day Above | Avg Day Close |
|---------|------|----------|-----------|---------------|
| Green (close≥open) | 134 | 69% | 57% | $1.08 |
| Red (close<open) | 144 | 37% | 44% | $-1.21 |

## R03: Overnight Gap Size Tiers

Prior: gap up adds +6pp edge (weak). Test extreme gaps (>$3, >$5, >$10).

| Gap Tier | Days | 5m Above | Day Above | Avg Day Close | Avg Day High |
|----------|------|----------|-----------|---------------|--------------|
| Gap Up $0-2 | 94 | 51% | 43% | $-1.77 | $7.06 |
| Flat (±$0) | 234 | 51% | 51% | $-0.18 | $7.75 |
| Gap Dn $0-2 | 98 | 48% | 55% | $-0.13 | $7.63 |

## R04: Pre-Market Level Proximity at Open

Hypothesis: opening near PM High → fade/reversal. Near PM Low → bounce.

| Open Position | Days | 5m Above | Day Above | Avg Day Close | Avg Day High |
|---------------|------|----------|-----------|---------------|--------------|
| Open above PM High (gap up beyond PM) | 2 | 100% | 100% | $12.14 | $16.68 |
| Open near PM High (within 15% PM range) | 33 | 42% | 67% | $2.65 | $8.42 |
| Open at PM mid | 55 | 47% | 60% | $-0.47 | $8.63 |
| Open near PM Low (within 15% PM range) | 51 | 49% | 35% | $-0.80 | $6.47 |
| Open below PM Low (gap down beyond PM) | 1 | 100% | 0% | $-6.14 | $4.62 |

## R05: TSLA vs SPY Divergence at 5m

Hypothesis: when TSLA and SPY diverge at 5m, TSLA reverts toward SPY.

| Scenario | Days | TSLA Day Above | Avg TSLA Day Close | Avg TSLA Day High |
|----------|------|----------------|--------------------|-------------------|
*Error in R05: SPY Divergence: 'day_high_above_open'*

## R06: Multi-Day Prior Trend as Predictor

Does TSLA being up/down for 3-5 consecutive days predict opening direction?

*Error in R06: Multi-Day Trend: "None of [Index([-2, -1, -1, -1, -2, -2, -1, -1, -2, -1,\n       ...\n       -1, -2, -1, -2, -2, -1, -2, -1, -2, -1],\n      dtype='object', length=275)] are in the [columns]"*

## R07: Opening Volume Signature

High opening volume = momentum confirmation or exhaustion?

| Volume Tier | Days | 5m Above | Day Above | Avg Day Close | Avg Day High |
|-------------|------|----------|-----------|---------------|--------------|
| Very high vol (>1.1x avg) | 67 | 45% | 54% | $0.29 | $8.87 |
| High vol (0.9-1.1x) | 67 | 54% | 45% | $-1.80 | $6.72 |
| Normal vol (0.7-0.9x) | 67 | 61% | 61% | $2.08 | $8.17 |
| Low vol (<0.7x) | 67 | 49% | 42% | $-0.72 | $5.98 |

## R08: ORB Range Width → Day Character

Narrow ORB (tight first 5m) often precedes large breakout moves.

| ORB Width | Days | Day Above | Avg Day Close | Avg Day Range | Avg Range Expansion |
|-----------|------|-----------|---------------|---------------|---------------------|
| Narrow ORB (≤$3.73) | 70 | 40% | $-0.42 | $12.95 | 4.3x |
| Small ORB ($3.73-$4.63) | 69 | 54% | $0.83 | $13.38 | 3.2x |
| Wide ORB ($4.63-$5.92) | 69 | 49% | $-0.82 | $17.26 | 3.3x |
| Very wide ORB (>$5.92) | 70 | 57% | $0.01 | $17.39 | 2.4x |

## R09: Second-Chance Entry (Return to Open After 15m)

After 5m above open (hold signal), price sometimes pulls back to open price. Is that a buying opportunity?

Of 144 days with 5m above open:
- **98 days (68%)** returned to within $0.50 of open after 9:45
- **46 days (32%)** held above open all day

When price returns to open after 9:45 (n=98):
- Recovered to +$1 within 30m: True (1%)
- Day close vs open: avg=$-0.67, med=$-0.02
- Day above open: 49%

Return timing: median 20m after open, range 15-382m

## R10: Combined Strategy Simulation (5m Rule + Level Touch)

Simulate call buying: enter at 9:35 when 5m above open. TP=$3/$5, SL=$1/$2. Raw stock-side P&L (no spread).

Signal: 5m above open = 145 days (52% of days)

| Config | Trades | Win% (TP hit) | Avg Raw P&L | Notes |
|--------|--------|---------------|-------------|-------|
| TP=$1.0 SL=$0.5 | 145 | 100% | $1.00 | raw, ignores path |
| TP=$2.0 SL=$1.0 | 145 | 94% | $1.81 | raw, ignores path |
| TP=$3.0 SL=$1.5 | 145 | 86% | $2.38 | raw, ignores path |
| TP=$5.0 SL=$2.0 | 145 | 72% | $3.02 | raw, ignores path |
| TP=$3.0 SL=$1.0 | 145 | 86% | $2.45 | raw, ignores path |
| TP=$5.0 SL=$1.0 | 145 | 72% | $3.30 | raw, ignores path |

### Enhanced: 5m above + $2 above open (stronger signal)
Signal: 5m close ≥ open+$2 = 72 days
| TP=$3.0 SL=$1.5 | 72 | 100% | $3.00 | |
| TP=$5.0 SL=$2.0 | 72 | 90% | $4.32 | |
| TP=$5.0 SL=$1.0 | 72 | 90% | $4.42 | |

## R11: Reversal Pattern Deep-Dive (1m Down → 5m Up)

Part F found: '1m DOWN → 5m UP = 72% bull, +$3.67 avg' (n=32). Find optimal entry timing for this reversal.

Reversal days (1m red → 5m green): **53 days**

- Day above open: 60%
- Avg day close vs open: $2.03
- Avg day high above open: $8.41
- Median max dip below open: $2.08

### Reclaim bar distribution
  - Reclaim at 9:31: 27 days (51%)
  - Reclaim at 9:32: 10 days (19%)
  - Reclaim at 9:33: 13 days (25%)
  - Reclaim at 9:34: 3 days (6%)

### Dip depth split
  - Shallow dip (≤$1): n=4, day_above=75%, avg_close=$6.33
  - Medium dip ($1-3): n=39, day_above=56%, avg_close=$1.13
  - Deep dip (>$3): n=10, day_above=70%, avg_close=$3.83

## R12: VWAP Cross Timing

Compute intraday VWAP and find when price first crosses it. Early VWAP reclaim (before 10am) = strong day signal?

Days with VWAP cross above (after 9:35): 273 of 278

| VWAP Cross Timing | Days | Day Above | Avg Day Close | Avg Day High |
|-------------------|------|-----------|---------------|--------------|
| Early cross (before 10am, <30m) | 246 | 54% | $1.03 | $8.04 |
| Mid cross (10-11am, 30-90m) | 18 | 28% | $-5.54 | $3.28 |
| Late cross (after 11am, >90m) | 9 | 0% | $-8.97 | $2.11 |
| Never above VWAP (after 9:35) | 5 | 0% | $-20.12 | $1.32 |

## R13: Time-to-First-$3/$5 Move

n=278 days

**$3 move:**
- Hits +$3 up: 198 days (71%), median 5m after open
- Hits -$3 down: 207 days (74%), median 6m after open

**$5 move:**
- Hits +$5 up: 151 days (54%), median 18m after open
- Hits -$5 down: 159 days (57%), median 20m after open

| Early Move (<30m) | Days | Day Above | Avg Day Close |
|-------------------|------|-----------|---------------|
| Bull $3 within 30m | 127 | 68% | $2.90 |
| Bear $3 within 30m | 126 | 35% | $-3.08 |

## R14: Puts-Only with 5m Direction Filter (Full 271-Day Simulation)

Prior research only tested puts on 47-day downtrend window. Now: puts on any day where 5m close < open (the BAIL signal). Entry at 9:35, using day_low as SL proxy and day_high as TP obstacle.

Signal days (5m below open): 133 of 278 (48%)

- Day ends below open (put wins raw): 62%
- Avg raw put P&L (open - day_close): $2.46
- Median raw put P&L: $3.16

| Config | Trades | Win% (TP hit) | Avg Raw P&L |
|--------|--------|---------------|-------------|
| TP=$1.0 SL=$0.5 | 133 | 100% | $1.00 |
| TP=$2.0 SL=$1.0 | 133 | 98% | $1.93 |
| TP=$3.0 SL=$1.5 | 133 | 92% | $2.63 |
| TP=$5.0 SL=$2.0 | 133 | 78% | $3.47 |

### Enhanced: 5m close ≤ open-$2 (strong bear)
Strong signal days: 69
- Day ends below open: 71%
  TP=$3.0/SL=$1.5: win=100%, avg P&L=$3.00
  TP=$5.0/SL=$2.0: win=88%, avg P&L=$4.19

---

## Summary: Key Findings

*(Auto-generated placeholder — review the module outputs above for specific findings)*

### Questions for next session
1. Which modules showed strongest edges? Should we simulate those with actual options P&L (spread costs)?
2. R05 SPY divergence: if TSLA lags SPY at 5m, is that a buy or a warning?
3. R11 reversal: is the reclaim timing (9:31 vs 9:34) predictive of day strength?
4. R14 puts-only: is there a structural TSLA bearish bias at open worth exploiting?
