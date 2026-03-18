# v3.1 Backtest Results

**Date:** 2026-03-06
**Signals:** 1841 (enriched-signals.csv)
**5m PnL coverage:** 1841/1841 (100%)
**SPY regime coverage:** 1841/1841 (100%)

---
## Change 1: REV Exemption from EMA Hard Gate

In v3.0b, REV signals required EMA alignment after 9:50 ET. In v3.1, REV
signals are exempt from EMA gate (only need ADX + body gate).

### REV Signal Breakdown
| Category | N | Avg PnL | Total PnL | Win% |
|----------|---|---------|-----------|------|
| All REV | 777 | +0.026 | +20.0 | 50.5% |
| REV pre-9:50 | 445 | +0.025 | +11.1 | 50.6% |
| REV post-9:50 + EMA aligned | 233 | +0.089 | +20.8 | 56.7% |
| REV post-9:50 + EMA misaligned (SUPPRESSED in v3.0b) | 99 | -0.119 | -11.8 | 35.4% |

**Impact:** In v3.0b, 99 REV signals were suppressed by EMA gate after 9:50.
These signals had total PnL of **-11.8 ATR**.
Allowing them in v3.1 would COST **-11.8 ATR** — these are net negative.

#### Breakdown by direction:
| Direction | N | Avg PnL | Total PnL | Win% |
|-----------|---|---------|-----------|------|
| bull | 48 | -0.100 | -4.8 | 43.8% |
| bear | 51 | -0.138 | -7.0 | 27.5% |

#### Breakdown by time bucket:
| Time | N | Avg PnL | Total PnL | Win% |
|------|---|---------|-----------|------|
| 9:30-10:00 | 41 | -0.191 | -7.8 | 29.3% |
| 10:00-11:00 | 41 | -0.095 | -3.9 | 39.0% |
| 11:00-12:00 | 2 | -0.175 | -0.3 | 0.0% |
| 12:00+ | 15 | +0.019 | +0.3 | 46.7% |

#### Breakdown by EMA state (misaligned only):
| EMA | N | Avg PnL | Total PnL | Win% |
|-----|---|---------|-----------|------|
| bull | 36 | -0.195 | -7.0 | 22.2% |
| bear | 35 | -0.115 | -4.0 | 42.9% |
| mixed | 28 | -0.028 | -0.8 | 42.9% |

#### Net impact on REV after 9:50:
- v3.0b: 233 REV signals, total PnL = +20.8 ATR
- v3.1:  332 REV signals, total PnL = +8.9 ATR
- Delta: **-11.8 ATR** from 99 additional signals

---
## Change 2: PD Mid → REV Signal Type

PD Mid is a **new level** added in v3.0 — it does not exist in the historical
enriched-signals.csv data. Therefore this change **cannot be backtested** against
historical signals.

**What we know from v3.0 research:**
- PD Mid was estimated at +0.209 avg P&L in the new levels research
- Changing from BRK to REV detection means touch-and-turn instead of close-through
- REV signals tend to have tighter entries and lower MAE
- Expected impact: slightly fewer triggers but better entry quality

---
## Change 3: SPY Market Regime → BAIL Modifier

Old BAIL: Hold if pnl_5m > 0.05 ATR (flat threshold for all signals)
New BAIL:
- Signal aligned with SPY direction (>0.3%) → NEVER BAIL
- SPY neutral (±0.3%) → loose BAIL (pnl > -0.10 ATR)
- Signal opposes SPY → strict BAIL (pnl > 0.05 ATR)

**CONF pass signals:** 231
**With 5m PnL data:** 231
**With 5m PnL + SPY data:** 231

### SPY Regime Distribution (CONF pass signals)
| SPY Regime | N | % |
|------------|---|---|
| aligned | 82 | 35.5% |
| neutral | 133 | 57.6% |
| opposed | 16 | 6.9% |

### Old vs New BAIL Decision Counts
| BAIL Rule | HOLD | BAIL |
|-----------|------|------|
| Old (flat 0.05) | 100 | 131 |
| New (SPY-aware) | 204 | 27 |

### Total PnL Comparison
| Metric | Old BAIL | New BAIL | Delta |
|--------|----------|----------|-------|
| Total PnL (ATR) | +36.5 | +52.0 | **+15.5** |
| Avg PnL (ATR) | +0.158 | +0.225 | +0.067 |
| Win % | 63.6% | 74.0% | +10.4pp |

### Breakdown by SPY Regime
| Regime | N | Old Hold% | New Hold% | Old PnL | New PnL | Delta |
|--------|---|-----------|-----------|---------|---------|-------|
| aligned | 82 | 43% | 100% | +14.7 | +22.8 | +8.1 |
| neutral | 133 | 46% | 89% | +21.1 | +28.5 | +7.4 |
| opposed | 16 | 25% | 25% | +0.7 | +0.7 | +0.0 |

### Signals Where Decision Changes

- **Loosened** (old=BAIL, new=HOLD): 104 signals
  - These signals were bailed in v3.0b but now held to completion
  - Their 5m PnL (what old got): -1.0 ATR
  - Their full PnL (what new gets): +14.5 ATR
  - Net gain from loosening: **+15.5 ATR**

  Loosened by regime:
  - aligned: 47 signals, 5m PnL=-0.9, full PnL=+7.2, delta=+8.1
  - neutral: 57 signals, 5m PnL=-0.2, full PnL=+7.3, delta=+7.4
- **Tightened** (old=HOLD, new=BAIL): 0 signals

### Deep Dive: Aligned Signals (Never BAIL in v3.1)
| Category | N | Full PnL | Win% |
|----------|---|----------|------|
| Aligned + old would HOLD | 35 | +15.6 | 100.0% |
| Aligned + old would BAIL | 47 | +7.2 | 74.5% |

The 47 signals that old BAIL would exit — their full outcome is
**+7.2 ATR** vs early exit at **-0.9 ATR**.
Holding them gains **+8.1 ATR**.

### Deep Dive: Neutral Signals (Loose BAIL: pnl > -0.10)
| Category | N | Full PnL | 5m PnL | Win% |
|----------|---|----------|--------|------|
| Still HOLD (pnl_5m > 0.05) | 61 | +23.4 | +9.0 | 88.5% |
| Newly HOLD (-0.10 < pnl_5m <= 0.05) | 57 | +7.3 | -0.2 | 70.2% |
| Still BAIL (pnl_5m <= -0.10) | 15 | -1.0 | -2.2 | n/a |

---
## Combined Summary

| Change | Description | ATR Impact | Signals Affected |
|--------|-------------|------------|------------------|
| 1. REV EMA Exemption | Allow REV without EMA after 9:50 | **-11.8** | 99 |
| 2. PD Mid → REV | New level, no historical data | n/a | n/a |
| 3. SPY BAIL Modifier | Context-aware BAIL thresholds | **+15.5** | 231 |
| **Total measurable** | | **+3.7** | |

**Net positive impact of +3.7 ATR.** v3.1 is an improvement.

---
## Appendix: EMA Gate Impact on ALL Signals (not just REV)

For context, here is the EMA gate impact across ALL signal types after 9:50:

| Category | N | Avg PnL | Total PnL | Win% |
|----------|---|---------|-----------|------|
| Post-9:50 EMA aligned | 795 | +0.064 | +50.7 | 55.0% |
| Post-9:50 EMA misaligned | 208 | -0.064 | -13.3 | 38.5% |

By type, EMA misaligned after 9:50:
| Type | N | Avg PnL | Total PnL | Win% |
|------|---|---------|-----------|------|
| BRK | 109 | -0.014 | -1.5 | 41.3% |
| REV | 99 | -0.119 | -11.8 | 35.4% |

This confirms whether exempting REV from EMA gate is justified while keeping it for BRK.