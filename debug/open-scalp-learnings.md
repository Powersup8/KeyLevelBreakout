# TSLA Open — Complete Research Findings

**Dates:** 2026-03-03 to 2026-03-05
**Data:** 5s (47 days), 1m (271 days), 5m (525 days) — IB candles
**Multi-symbol:** TSLA, NVDA, AMZN, SPY (1m + 5m)

---

## Part A: Open Scalp Strategy — DEAD END (47 days, 5s data)

Buy ATM call or put within 120s of open, TP/SL management, hard exit 9:35.
Entry: wait 30s, compare bar close to 9:30 open. Close ≥ open → Call, Close < open → Put.

### Best configs

| Config | Trades | Win% | Total P&L | Sharpe |
|--------|--------|------|-----------|--------|
| **Puts only** (TP=$2, SL=$1) | **30** | **53%** | **+$515** | **3.6** |
| Both directions (TP=$2, SL=$1) | 44 | 48% | +$355 | 1.7 |
| Calls only (best) | 14 | 43% | -$85 | -3.8 |

### What we tested and ruled out

1. **13 entry triggers** → `wait_30s` best. 15s/20s = too noisy, 60s = move already done.
2. **Tight stops** get clipped by 5s noise. Only TP≥$1.50 / SL≥$0.75 works.
3. **Trailing stops** → best +$17. Fixed TP beats trailing at the open.
4. **Indicator exits** (EMA9/20, VWAP, reversal, stall) → all worse than TP/SL.
5. **Buy-the-dip** (always long, enter on 35% recovery) → all negative (-$100 to -$1312).
6. **1m close as direction** → catastrophically worse. Wait_60s: -$582 vs wait_30s: +$454.
7. **Always-call with dip recovery** → only TP=$1.00/SL=$0.25 positive (+$172, 50% win). Not tradeable.

**Verdict:** The puts-only edge was regime-dependent (47-day TSLA downtrend). Over 271+ days direction is 50/50. Real spreads wipe all profit.

---

## Part B: Direction Study (271 days 1m, 525 days 5m)

### Opening direction is a coin flip (except AMZN)

| Symbol | TF | Days | 30s Below | 1m Below | 5m Below | Day Close |
|--------|-----|------|-----------|----------|----------|-----------|
| TSLA | 1m | 221 | 49% | 52% | 51% | 50/50 |
| TSLA | 5m | 476 | 49% | 49% | 50% | 49/50 |
| NVDA | 5m | 476 | 53% | 53% | 49% | 51/48 |
| **AMZN** | **5m** | **476** | **57%** | **57%** | **55%** | **49/49** |
| SPY | 5m | 476 | 47% | 47% | 44% | 52/46 |

AMZN has a persistent bearish opening bias (55-57% below open). SPY has mild bullish bias.

### All symbols trade above open during the day

| Symbol | Day High Above Open | Avg Day High |
|--------|--------------------|----|
| TSLA | 99% | +$7.45 |
| NVDA | 96-97% | +$2.25 |
| AMZN | 97-98% | +$2.20 |
| SPY | 97-99% | +$2.97 |

---

## Part C: Day High Timing (271 days 1m)

### U-shaped distribution

| Time Window | TSLA (1m) | TSLA (5m) |
|---|---|---|
| 9:30-10:00 | **41%** | **42%** |
| 10:00-11:00 | 15% | 16% |
| 11:00-15:00 | 26% | 25% |
| 15:00-16:00 | **17%** | **15%** |

### Bull vs bear days — completely different profiles

| Metric | Bull Days (136) | Bear Days (135) |
|---|---|---|
| High in first 5m | 2% | 52% |
| High in first 30m | 10% | 73% |
| High in last hour | 36% | 0% |
| Median high time | 12:57 | 9:34 |

Descriptive, not predictive — you only know which type of day it is after the fact.

---

## Part D: Bull/Bear Day Prediction (271 days, 1m)

### What DOESN'T predict direction
- 1st bar range, volume, day range — identical for bull/bear
- Overnight gap — useless (+6pp for gap up, -0pp for gap down)
- Day of week — zero signal

### Prediction accuracy scales linearly with time

| Signal | → Bull% | n | Edge |
|---|---|---|---|
| 1st bar green | 56% | 131 | +13pp |
| 5m above open | 60% | 138 | +21pp |
| 15m above open | 72% | 128 | +42pp |
| 30m above open | 77% | 127 | +51pp |

No early shortcut. Best combos: "30m up + 5m up" = 76% bull (n=89), "30m up >$2 + gap up" = 85% (n=47).

---

## Part E: Level Bounce Study (271-476 days, 4 symbols)

When the opening dip (first 5m) touches a known key level (prev day, 2d-50d lookback), does it bounce better?

### Cross-symbol summary

| Symbol | TF | Days | Level% | Lvl 5m Win% | No-Lvl 5m Win% | Edge |
|--------|----|----- |--------|-------------|----------------|------|
| TSLA | 1m | 221 | 30% | 84% | 81% | +3pp |
| NVDA | 1m | 221 | 67% | 82% | 75% | +7pp |
| AMZN | 1m | 322 | 69% | 85% | 83% | +2pp |
| SPY | 1m | 221 | 63% | 90% | 83% | +7pp |

### The real edge: $1-2 dips + level touch

| Symbol | $1-2 Dip + Level Win% | $1-2 No-Level Win% | Edge |
|--------|-----------------------|---------------------|------|
| NVDA | 83% | 62% | **+21pp** |
| AMZN | 78% | 67% | **+12pp** |
| SPY | 90% | 71% | **+19pp** |
| TSLA | 85% | 90% | -5pp |

$1-2 dip Goldilocks zone: big enough to reach a level, small enough to bounce reliably.

### 5-day+ lookback = sweet spot

| Depth | TSLA 5m Win% | NVDA | SPY |
|-------|-------------|------|-----|
| prev_day | 79% | 83% | 90% |
| **5d level** | **100%** | **95%** | **91%** |
| 50d level | 100% (n=2) | 100% (n=12) | 94% (n=32) |

### HIGH levels > LOW levels (consistent across symbols)

| Symbol | HIGH 5m Win% | LOW 5m Win% |
|--------|-------------|-------------|
| TSLA | 94% | 87% |
| NVDA | 86% | 79% |
| AMZN | 88% | 81% |
| SPY | 90% | 88% |

Touching a previous high (now support) = bullish structure. Touching a previous low = bearish extending.

---

## Part F: HOLD or BAIL — Call Holder's Playbook (271 days, 1m)

**Setup:** You hold TSLA calls at market open. What tells you to hold or sell?

### Baseline

- Avg day high above open: **$7.45** (median $5.68)
- Avg day close: **$-0.09** (coin flip)
- 89% of days reach ≥$1 above open, 55% reach ≥$5

### The 5-Minute Rule

| 5m Signal | Days | % Bull Close | Avg Day Close | Avg Day High | 30m MFE |
|-----------|------|-------------|---------------|-------------|---------|
| **Above open** | 134 | **67%** | **+$3.22** | $9.99 | $6.24 |
| **Below open** | 133 | **32%** | **-$3.64** | $4.83 | $2.13 |

**$6.87 expected value gap.** This is the single most powerful signal.

### The Decision Matrix (best combos)

| Signal | Days | % Bull | Avg Day Close | Action |
|--------|------|--------|---------------|--------|
| **5m > +$2** | **76** | **75%** | **+$4.71** | **HOLD** |
| **5m UP + big dip recovered** | **73** | **67%** | **+$3.32** | **HOLD** |
| **1m DOWN → 5m UP (reversal)** | **32** | **72%** | **+$3.67** | **HOLD** (strongest!) |
| 5m DOWN + small dip (<$1) | 9 | 11% | -$7.70 | **BAIL FAST** |
| 5m DOWN + not recovered | 97 | 29% | -$4.34 | **BAIL** |
| 1m UP → 5m DOWN (fakeout) | 30 | 30% | -$3.11 | **BAIL** |

### Recovery speed matters

| Recovery After Dip | Days | % Bull | Avg Day Close |
|--------------------|------|--------|---------------|
| 1-2 minutes | 87 | 55% | +$1.78 |
| 2-5 minutes | 51 | **67%** | **+$2.54** |
| Never recovered | 62 | **18%** | **-$7.71** |

**If not recovered by 5m → 82% chance of losing day. BAIL.**

### Bear day escape window

Even on bear days, 77% reach ≥$1 above open — but avg bear day high is at **0:29 after open**.
- By 5m: only 32% still above open
- By 30m: only 21% above open

On a bad day you have **seconds, not minutes** to exit near breakeven.

### When to take profit (bull days)

- Avg bull day high: **$11.73**
- Avg time of high: **3:36 after open** (median 3:34)
- At 30m: 73% still above open, avg +$2.96

Bull days trend all day. No rush to sell in the first hour.

---

## The Three Rules

1. **Wait until 9:35.** Price above open = HOLD (67% bull, +$3.22 avg). Below = BAIL (32% bull, -$3.64 avg).

2. **Dip-then-recovery is the STRONGEST hold signal.** 1m down → 5m up = 72% bull, +$3.67 avg. Recovery proves buying pressure.

3. **No recovery by 5m = exit.** 82% chance of losing day, avg -$7.71. Don't hope.

---

## Files

| File | Description |
|---|---|
| `open_scalp_analysis.py` | Main scalp sim (triggers, TP/SL grid, trailing, direction filter) |
| `open_scalp_exits.py` | Indicator-based exit comparison |
| `open_scalp_dip_buy.py` | Buy-the-dip strategy (always long) |
| `open_scalp_1m_direction.py` | 30s vs 1m direction + wait time comparison |
| `open_scalp_call30s.py` | Always-call strategy, dip recovery + hold/momentum/TP-SL |
| `open_direction_study.py` | Above/below open at 30s intervals, 3 timeframes |
| `day_high_timing.py` | Day high timing analysis, bull/bear split |
| `open_level_bounce.py` | Level bounce study (TSLA, extended lookbacks) |
| `open_level_multi.py` | Multi-symbol level bounce + direction (TSLA/NVDA/AMZN/SPY) |
| `open_hold_or_bail.py` | Call holder HOLD/BAIL decision framework |
| `open-scalp-results.md` | Full scalp numerical results |
| `open-scalp-exits.md` | Indicator exit results |
| `open-scalp-dip-buy.md` | Dip-buy results |
| `open-scalp-1m-direction.md` | 30s vs 1m direction results |
| `open-scalp-call30s.md` | Always-call results |
| `open-direction-study.md` | Direction study results |
| `open-level-bounce.md` | TSLA level bounce results |
| `open-level-multi.md` | Multi-symbol level bounce + direction |
| `open-hold-or-bail.md` | Call holder HOLD/BAIL results |
| `day-high-timing.md` | Day high timing results |
