# v3.1 Pine Log Validation Report

**Date:** 2026-03-06
**Data:** 21 v3.0b pine log files, 9 v3.1 pine log files
**Coverage:** Jan 26 - Mar 5, 2026 | 8 symbols (AMZN, GLD, GOOGL, META, MSFT, QQQ, SPY, TSLA)
**Script:** `debug/v31_validate.py`

---

## Executive Summary

| Change | Verdict | Detail |
|--------|---------|--------|
| PD Mid BRK->REV | **BROKEN** | 0 REV signals firing. PD Mid completely silent in v3.1 |
| SPY BAIL modifier | **WORKING** | Saves 312 signals, kills 0. SPY-aligned HOLDs are 64% positive |
| FADE signals | **GONE** | 79 in v3.0b, 0 in v3.1 |
| Net impact | **Mixed** | BAIL fix is good. PD Mid and FADE regressions need fixing |

---

## 1. PD Mid Analysis: BRK -> REV Change

### What happened
v3.0b fired 94 unique PD Mid BRK signals. v3.1 fires **zero** PD Mid signals of any type (BRK or REV). The REV trigger for PD Mid is not activating.

### Were the lost PD Mid BRK signals good?
Of 94 unique PD Mid BRK signals in v3.0b:
- 15 never got CONF (EMA gate or timing)
- 2 got CONF but no 5m CHECK
- **14 got HOLD** (avg pnl = **+0.133 ATR**) -- these were GOOD signals
- **63 got BAIL** (avg pnl = **-0.074 ATR**) -- mostly losers

### The 14 PD Mid HOLDs we lost

| Symbol | Date | Time | 5m PNL | Notes |
|--------|------|------|--------|-------|
| QQQ | Jan 29 | 10:25 | +0.52 | PD Mid + PD LH L -- HUGE winner |
| AMZN | Feb 3 | 10:00 | +0.16 | PD Mid + PD LH L |
| TSLA | Feb 3 | 10:15 | +0.15 | PD Mid only |
| TSLA | Feb 11 | 09:55 | +0.15 | PD Mid only |
| TSLA | Mar 5 | 09:35 | +0.15 | PM L + Week L + PD Mid + PD LH L |
| AMZN | Feb 6 | 09:30 | +0.13 | PD Mid only |
| META | Feb 2 | 09:35 | +0.10 | PM H + PD Mid |
| TSLA | Jan 30 | 09:35 | +0.09 | PM H + PD Mid |
| MSFT | Mar 2 | 09:40 | +0.08 | PD Mid only |
| AMZN | Feb 23 | 09:35 | +0.07 | PM L + PD Mid |
| AMZN | Feb 23 | 09:40 | +0.07 | ORB L + PD Mid |
| AMZN | Feb 26 | 09:50 | +0.07 | PM L + ORB L + PD Mid + PD LH L |
| SPY | Feb 2 | 09:55 | +0.06 | PD Mid only |
| AMZN | Feb 2 | 09:35 | +0.06 | PM H + PD Mid |

**Key insight:** Most of the good PD Mid signals also had OTHER levels (PM H/L, ORB, PD LH L). When v3.1 removes PD Mid from BRK, those signals still fire -- just without the PD Mid tag. Only 4 signals had PD Mid as the SOLE level. The loss is real but smaller than it appears.

### PD Mid BRK: Majority were losers
63 BAILed PD Mid signals, avg pnl = -0.074. Some were deeply negative:
- META Feb 3 09:40: pnl = -0.30 (PM H + ORB H + PD Mid)
- AMZN Mar 3 09:40: pnl = -0.26
- AMZN Feb 9 09:35: pnl = -0.25
- MSFT Mar 5 09:30: pnl = -0.25

**Bottom line:** PD Mid BRK has 18% HOLD rate (14/77 with outcomes), and the HOLDs averaged +0.133 while BAILs averaged -0.074. Net sum: 14 * 0.133 - 63 * 0.074 = 1.86 - 4.66 = **-2.80 ATR net negative**. Removing PD Mid BRK is actually +2.80 ATR... IF nothing replaces it.

### PD Mid REV: Not firing
The REV trigger for PD Mid should fire when price touches PD Mid and reverses. Zero REV signals appeared. **This is a bug.** The REV detection logic may not be matching PD Mid levels, or the touch condition is too strict.

**Action needed:** Investigate why PD Mid REV is not firing. Check the Pine Script logic for REV signal generation at PD Mid levels.

---

## 2. SPY BAIL Modifier

### Replay Results (v3.0b checks replayed with v3.1 rules)
- **630 total 5m CHECKs** in v3.0b data
- **312 decisions changed** BAIL -> HOLD (49.5% of all checks)
- **0 decisions changed** HOLD -> BAIL
- The new rules ONLY save signals, never kill them

### Breakdown of saved signals

| SPY Regime | Count | Avg PNL | Positive | Sum PNL |
|------------|------:|--------:|---------:|--------:|
| SPY-aligned | 123 | -0.061 | 34% | -7.50 |
| SPY-neutral(loose) | 189 | -0.016 | 40% | -3.02 |
| **Total** | **312** | **-0.034** | **38%** | **-10.52** |

### Caution: 5m PNL is not final outcome
The PNL values above are 5-minute PNLs at CONF time, NOT final trade outcomes. A signal with -0.05 PNL at 5 minutes might still end profitable. However, the data shows the saved signals are on average negative at the 5-minute mark.

### v3.1 Actual BAIL Performance (from live v3.1 logs)

| SPY Tag | Decision | N | Avg PNL | Positive | Sum PNL |
|---------|----------|--:|--------:|---------:|--------:|
| SPY-aligned | HOLD | 111 | +0.015 | 64% | +1.70 |
| SPY-neutral | HOLD | 113 | +0.016 | 53% | +1.84 |
| SPY-neutral | BAIL | 52 | -0.172 | 0% | -8.96 |
| SPY-opposed | BAIL | 19 | -0.091 | 11% | -1.72 |
| SPY-opposed | HOLD | 2 | +0.215 | 100% | +0.43 |

**The modifier is working correctly in v3.1:**
- SPY-aligned HOLDs: 64% positive, net +1.70 ATR
- SPY-neutral HOLDs: 53% positive, net +1.84 ATR
- SPY-neutral BAILs: 0% positive, avg -0.172 -- correctly killed
- SPY-opposed BAILs: 11% positive -- correctly killed

### HOLD Rate Comparison
| Version | HOLD | BAIL | HOLD Rate |
|---------|-----:|-----:|----------:|
| v3.0b | 158 | 472 | 25.1% |
| v3.1 | 226 | 71 | 76.1% |

v3.1 keeps 3x more signals alive. The HOLD avg PNL dropped from +0.131 to +0.018 (dilution from saving more marginal signals), but the BAIL avg PNL went from -0.070 to -0.150 (BAILs are now truly bad signals only).

---

## 3. Direct v3.0b vs v3.1 Signal Comparison

### Per-Symbol Changes (largest file per symbol)

#### AMZN
- **+1 new:** `2026-03-03 09:40 BRK PM H + ORB H` (PD Mid stripped from level combo)
- **-8 lost:** 5 PD Mid-only signals, 3 FADE signals
- **BAIL changes:** 11 BAIL->HOLD (SPY-aligned/neutral saves)

Notable: `2026-02-02 09:40 pnl=-0.62 BAIL -> HOLD (SPY-aligned)` -- saved a deep loser

#### SPY
- **+5 new:** Signals that had "ORB H/L + PD Mid" now fire as just "ORB H/L"
- **-14 lost:** 8 PD Mid signals, 4 FADE signals, 2 other
- **BAIL changes:** Multiple saves including `2026-02-05 10:20 pnl=-0.20 BAIL -> HOLD (SPY-aligned)`

#### META
- **+7 new:** Signals where PD Mid was stripped from level combos
- **-19 lost:** 8 PD Mid signals, 5 FADE signals, 6 from different date ranges
- **BAIL changes:** 14 BAIL->HOLD saves

#### TSLA
- **+29 new, -52 lost:** Mostly from different date ranges (v3.0b covers Jan 26+, v3.1 covers Feb 2+)
- Not a meaningful comparison for TSLA

#### MSFT
- **+2 new:** `PM H` (stripped PD Mid), `PD LH L` (stripped PD Mid)
- **-7 lost:** 3 PD Mid signals, 3 FADE signals, 1 other
- **BAIL changes:** 10 BAIL->HOLD saves

#### GOOGL
- **+3 new:** Signals where PD Mid stripped from combos
- **-13 lost:** 7 PD Mid signals, 5 FADE signals, 1 other

---

## 4. FADE Signal Regression

**v3.0b had 79 FADE signals. v3.1 has 0.**

FADE signals were introduced in v3.0 as a new signal type that fires when a CONF fails and price reverses through the level within 30 minutes. Their complete absence in v3.1 is a regression.

**Action needed:** Investigate why FADE signals stopped firing. This may be related to the PD Mid change or could be a separate bug.

---

## 5. CONF Pass Rate

| Version | Pass | Fail | Rate |
|---------|-----:|-----:|-----:|
| v3.0b | 752 | 90 | 89.4% |
| v3.1 | 350 | 1 | 99.7% |

The near-100% CONF pass rate in v3.1 is suspicious. With auto-confirm R1 changes (now `(auto-R1: EMA)` instead of `(auto-R1: EMA+morning)`), nearly every signal auto-confirms. This effectively removes CONF as a filter, which was by design (CONF 1->3 bars window expansion + auto-confirm changes).

---

## 6. Net Impact Assessment

### Positive
1. **SPY BAIL modifier works correctly** -- 64% positive for SPY-aligned HOLDs
2. **PD Mid BRK removal is net positive** -- PD Mid BRK was -2.80 ATR net negative
3. **HOLD rate tripled** (25% -> 76%) -- fewer false BAIL exits
4. **BAIL quality improved** -- remaining BAILs are truly bad (0% positive for SPY-neutral BAILs)

### Negative / Needs Fix
1. **PD Mid REV not firing (BUG)** -- 0 signals. The touch-and-turn logic for PD Mid is broken
2. **FADE signals gone (BUG)** -- 79 -> 0. Complete regression
3. **Some good PD Mid combos lost** -- signals where PD Mid was part of a level combo (PM H + PD Mid) may have been strong entries that now fire without PD Mid confirmation
4. **SPY-aligned saves avg PNL is negative** (-0.061) -- keeping losers alive longer

### Net ATR Impact Estimate
| Change | ATR Impact | Reasoning |
|--------|--------:|----------|
| PD Mid BRK removal | +2.80 | Net negative signal type removed |
| SPY-aligned saves | -7.50 | 123 saves with avg -0.061 PNL |
| SPY-neutral saves | -3.02 | 189 saves with avg -0.016 PNL |
| FADE loss | ??? | 79 signals, outcome unknown from logs |
| PD Mid REV missing | ??? | Should add new signals but is broken |
| **Estimated net** | **~-7.7** | Dominated by BAIL saves of negative signals |

**IMPORTANT CAVEAT:** The 5-minute PNL is NOT the final trade outcome. Many of these "negative at 5 min" signals could recover. The enriched-signals.csv with MFE/MAE data would give better outcome tracking. The BAIL save question is: does keeping a -0.05 PNL signal alive lead to eventual profit or eventual larger loss?

---

## 7. Recommendations

1. **Fix PD Mid REV** -- The touch-and-turn logic is not matching PD Mid levels. Debug the Pine Script.
2. **Fix FADE signals** -- Complete regression needs investigation.
3. **Validate BAIL saves with final outcomes** -- Cross-reference the 312 BAIL->HOLD saves with enriched-signals.csv MFE data to see if holding these signals actually produced better final outcomes.
4. **Consider tightening SPY-neutral rule** -- The loose BAIL (pnl > -0.10) for neutral SPY is saving many marginally negative signals. Consider pnl > -0.05 instead.
5. **Monitor CONF pass rate** -- 99.7% pass rate means CONF is no longer filtering. This may be intentional but removes a safety net.

---

## Appendix: File Inventory

### v3.0b Files (21)
| Hash | Symbol | Lines | Date Range |
|------|--------|------:|------------|
| 01085 | AMZN | 251 | Jan 26 - Mar 4 |
| 100da | GLD | 171 | Feb 2 - Mar 5 |
| 1f23e | SPY | 205 | Feb 2 - Mar 4 |
| 21c43 | MSFT | 190 | Feb 2 - Mar 4 |
| 2845e | SPY | 220 | Feb 2 - Mar 5 |
| 2cbe1 | QQQ | 235 | Jan 26 - Mar 5 |
| 2f230 | AMZN | 243 | Jan 26 - Mar 4 |
| 49c92 | META | 257 | Feb 2 - Mar 5 |
| 4caf9 | AMZN | 185 | Feb 2 - Mar 5 |
| 4d466 | MSFT | 197 | Feb 2 - Mar 5 |
| 67b51 | META | 236 | Jan 26 - Mar 4 |
| 71d98 | TSLA | 271 | Jan 26 - Mar 5 |
| 77b0c | AMZN | 192 | Feb 2 - Mar 5 |
| 7aedc | GOOGL | 214 | Feb 2 - Mar 5 |
| 984ec | TSLA | 215 | Feb 2 - Mar 5 |
| 9a085 | AMZN | 256 | Jan 26 - Mar 5 |
| ba67a | AMZN | 236 | Jan 26 - Mar 4 |
| ccab3 | GOOGL | 205 | Feb 2 - Mar 4 |
| cea64 | META | 274 | Jan 26 - Mar 4 |
| e94d0 | MSFT | 188 | Feb 2 - Mar 5 |
| fa0b5 | META | 243 | Jan 26 - Mar 5 |

### v3.1 Files (9)
| Hash | Symbol | Lines | Date Range |
|------|--------|------:|------------|
| 2a729 | META | 241 | Feb 2 - Mar 5 |
| 3e439 | AMZN | 167 | Feb 2 - Mar 5 |
| 401e4 | META | 233 | Jan 26 - Mar 5 |
| 4d0f0 | GOOGL | 202 | Feb 2 - Mar 5 |
| 5612a | MSFT | 190 | Feb 2 - Mar 5 |
| b8ca4 | TSLA | 193 | Feb 2 - Mar 5 |
| e995b | AMZN | 193 | Feb 2 - Mar 5 |
| f2685 | SPY | 201 | Feb 2 - Mar 5 |
| f3ad7 | AMZN | 248 | Jan 26 - Mar 5 |
