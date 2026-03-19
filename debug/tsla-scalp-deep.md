# TSLA Open-Scalp Deep Research — Phase 2
*Generated: 2026-03-14 20:21*

8 focused modules extending the prior 14-module research loop (tsla-scalp-research.md).

**Modules:**
- D01: ORB direction × 5m rule agreement (all 4 combos)
- D02: ORB width × ORB direction
- D03: Puts-path simulation on 5s bars (bar-by-bar, SL checked before TP)
- D04: Fix R05 SPY divergence
- D05: Fix R06 multi-day trend
- D06: Deep dip reversal × ORB confirmation
- D07: VWAP cross timing as hold/bail modifier
- D08: ORB direction × gap size

---

## D01: ORB Direction × 5m Rule Agreement

Tests all 4 combos of ORB first-break direction and 5m-close vs open.
This shows whether the two signals are independent or redundant,
and which combination is most actionable.

| Combo | Days | Day Above % | Avg Day Close | Avg Day High | Avg Day Low |
|-------|------|-------------|---------------|--------------|-------------|
| ORB Bull + 5m Above (double bull) | 108 | 70% | $4.12 | $10.56 | $-4.50 |
| ORB Bull + 5m Below (conflict) | 34 | 71% | $3.52 | $9.28 | $-6.84 |
| ORB Bear + 5m Above (conflict) | 37 | 32% | $-3.95 | $6.25 | $-9.58 |
| ORB Bear + 5m Below (double bear) | 99 | 27% | $-4.52 | $3.80 | $-11.13 |
| ALL days (baseline) | 278 | 50% | $-0.10 | $7.42 | $-7.83 |

**Conflict days** (ORB vs 5m disagree): 71 days = 26% of all days
- Day above open: 51%
- Avg close vs open: $-0.37

*n=278 total trading days*

## D02: ORB Width × ORB Direction

Narrow ORB alone showed 40% bull days. But does ORB direction override?
Split by width quartile AND ORB break direction.

| ORB Width | Break Direction | Days | Day Above % | Avg Day Close | Avg Day High |
|-----------|-----------------|------|-------------|---------------|--------------|
| Narrow ORB (≤$3.73) | Bull break first | 38 | 55% | $1.82 | $8.31 |
| Narrow ORB (≤$3.73) | Bear break first | 32 | 22% | $-3.09 | $3.39 |
| Mid ORB ($3.73-$4.63) | Bull break first | 37 | 73% | $3.83 | $8.77 |
| Mid ORB ($3.73-$4.63) | Bear break first | 32 | 31% | $-2.64 | $4.28 |
| Wide ORB (>$4.63) | Bull break first | 67 | 78% | $5.28 | $12.18 |
| Wide ORB (>$4.63) | Bear break first | 72 | 31% | $-5.69 | $5.03 |

**Narrow ORB focus** (≤$3.73, n=70):
- Narrow + bull break: 38 days → 55% day above, avg close $1.82
- Narrow + bear break: 32 days → 22% day above, avg close $-3.09

## D03: Puts-Path Simulation (5s Bars, Bar-by-Bar)

Signal: 5m close ≤ open−$2. Enter short at 9:35. TP=open−$3, SL=open+$1.50.
Bar-by-bar on 5s data: SL is checked before TP on each bar (conservative).

Signal days (5m close ≤ open−$2): **69** of 278

**Simulated 18 trades** (may be fewer than signal days if 5s data missing):
- TP hit (open−$3): 16 (89%) ← actual path-verified
- SL hit (open+$1.50): 2 (11%)
- No exit (held to EOD): 0 (0%)

**P&L (stock price, short):**
- Avg P&L: $-0.52
- Median P&L: $-0.83
- Avg time to exit: 0 min

| Outcome | Trades | Avg P&L | Avg Min to Exit |
|---------|--------|---------|-----------------|
| TP | 16 | $-1.13 | 0m |
| SL | 2 | $4.37 | 0m |

**Comparison with R14 proxy (day L/H only, no path):**
- R14 proxy TP hits: 69/69 = 100%
- D03 actual TP hits: 16/18 = 89%
- **Verdict:** Path check reduced win rate

## D04: TSLA vs SPY Day Direction (R05 Fixed)

Both TSLA and SPY daily summaries are built with the same build_daily().
Join on date and cross-tabulate day direction (up/down).

Days with both TSLA + SPY data: 278

| Scenario | Days | TSLA 5m Above | Avg TSLA Close | Avg TSLA High |
|----------|------|---------------|----------------|---------------|
| TSLA Up / SPY Up | 94 | 65% | $8.21 | $11.59 |
| TSLA Up / SPY Down | 45 | 60% | $6.78 | $11.86 |
| TSLA Down / SPY Up | 47 | 36% | $-5.23 | $3.13 |
| TSLA Down / SPY Down | 92 | 43% | $-9.34 | $3.19 |

### 5m Divergence (at 9:35) — n=278 days

| 5m Scenario | Days | TSLA Day Above | Avg TSLA Close | Avg TSLA High |
|-------------|------|----------------|----------------|---------------|
| TSLA↑ SPY↑ (agree bull) | 81 | 63% | $2.74 | $9.59 |
| TSLA↑ SPY↓ (TSLA leads) | 64 | 58% | $1.20 | $9.30 |
| TSLA↓ SPY↑ (TSLA lags) | 68 | 38% | $-1.51 | $5.90 |
| TSLA↓ SPY↓ (agree bear) | 65 | 38% | $-3.46 | $4.46 |

## D05: Multi-Day Prior Trend as Predictor (R06 Fixed)

Does prior 3-day direction predict today's open behavior?
Fix: use numpy .values to avoid index misalignment in boolean shifts.

| Prior 3 Days | Days | 5m Above | Day Above | Avg Day Close | Avg Day High |
|--------------|------|----------|-----------|---------------|--------------|
| 3 bull days prior | 25 | 56% | 40% | $-2.80 | $5.58 |
| 2 bull + 1 bear (prev3 bear) | 40 | 45% | 38% | $-1.73 | $5.72 |
| 1 bull + 2 bear (prev2-3 bear) | 29 | 28% | 48% | $1.01 | $7.70 |
| 3 bear days prior | 35 | 40% | 43% | $-1.71 | $8.00 |
| Prev day bull (any) | 138 | 44% | 47% | $-1.02 | $6.46 |
| Prev day bear (any) | 137 | 61% | 53% | $0.80 | $8.44 |
| ALL days (baseline) | 275 | 52% | 50% | $-0.11 | $7.45 |

### Streak analysis (prior 5 days)
*ERROR in D05: Multi-Day Trend (fixed): 0*

## D06: Deep Dip Reversal × ORB Confirmation

R11: reversal day (1m red → 5m green) = 70% bull. Does ORB direction improve that? Or contradict it?

Reversal days (1m red → 5m green): **53** of 278

### Reversal days × ORB direction
| Sub-group | Days | Day Above | Avg Day Close | Avg Day High |
|-----------|------|-----------|---------------|--------------|
| Rev + ORB Bull (double confirmation) | 39 | 69% | $4.50 | $9.20 |
| Rev + ORB Bear (contradiction) | 14 | 36% | $-4.86 | $6.21 |
| Rev ALL (baseline) | 53 | 60% | $2.03 | $8.41 |
| Non-reversal + ORB Bull | 103 | 71% | $3.78 | $10.65 |
| Non-reversal ALL (baseline) | 225 | 48% | $-0.60 | $7.19 |

### Deep dip reversal (>$3) × ORB direction
Deep dip reversal days (dip >$3 + 1m red → 5m green): **10**
  - Deep rev + ORB Bull: n=7, day_above=86%, avg close=$7.06
  - Deep rev + ORB Bear: n=3, day_above=33%, avg close=$-3.71
  - Deep rev ALL: n=10, day_above=70%, avg close=$3.83

## D07: VWAP Cross Timing as Exit Signal (for 5m-Above Days)

On HOLD days (5m above open), when TSLA crosses VWAP affects outcome.
Early VWAP reclaim = strong. Late = exit signal.

Hold days (5m above open): **145** of 278

| VWAP Timing (Hold Days) | Days | Day Above | Avg Day Close | Avg Day High |
|-------------------------|------|-----------|---------------|--------------|
| Early VWAP reclaim (<30m) | 143 | 62% | $2.24 | $9.55 |
| Late VWAP reclaim (>90m) | 1 | 0% | $-0.78 | $4.91 |
| Never above VWAP after 9:35 | 1 | 0% | $-21.19 | $1.37 |
| ALL hold days (baseline) | 145 | 61% | $2.06 | $9.46 |

**Late VWAP cross (1 days):** day above=0%, avg close=$-0.78
If exited at VWAP cross (stock ≈ open), would have avoided negative days.

### Bail days (5m below open): VWAP as reversal signal
Bail days with early VWAP cross above (<30m): potential reversal?
- Bail + early VWAP reclaim: 103 days → day above=45%, avg close=$-0.66
- Bail + never crosses VWAP: 4 days → day above=0%, avg close=$-19.85

## D08: ORB Direction × Gap Size

Does gap direction reinforce or contradict ORB direction signal?
Gap up + ORB bull = momentum? Gap up + ORB bear = gap fade?

| Gap × ORB | Days | Day Above | Avg Day Close | Avg Day High | Avg Day Low |
|-----------|------|-----------|---------------|--------------|-------------|
| Gap Flat + ORB Bull | 119 | 71% | $4.03 | $10.75 | $-5.51 |
| Gap Flat + ORB Bear | 115 | 30% | $-4.55 | $4.64 | $-11.15 |
| ALL days | 234 | 51% | $-0.18 | $7.75 | $-8.28 |


---

## Summary

Completed: 7/8 modules

### Errors
- **D05: Multi-Day Trend (fixed)**: 0

### Action items
1. D01: If double-bull (ORB bull + 5m above) is ≥75% → use as primary entry filter
2. D01: If conflict combos are still 50/50 → ignore either signal when they disagree
3. D02: If narrow ORB + bull break is strong → add width filter to entry rules
4. D03: If actual path TP% < R14 proxy → R14 was overfit; re-size TP/SL targets
5. D06: If deep-dip + ORB bull ≥80% → strongest bull signal in dataset
6. D07: If late VWAP cross on hold days = negative day → use as hard exit rule
7. D08: If gap + ORB agreement > 80% → combined signal for opening momentum
