# v3.1 Design: SPY Market Regime + PD Mid REV

**Goal:** Two changes that address the biggest PnL drags identified in v3.0b research.

**Architecture:** All changes within existing Pine Script v6 indicator. Zero new `request.security()` calls. SPY data already available. BAIL modifier is the core PnL lever.

**Data backing:**
- BAIL investigation: current BAIL costs -10.6 ATR (debug/v30b-bail-investigation.md)
- PD Mid research: BRK = 100% BAIL, FADE = +0.396/touch (debug/v30b-new-levels-deep-research.md)
- Move scanner: cross-symbol triggers = context not signal (debug/v30b-move-scanner-research.md)
- v3.1 backtest: +15.5 ATR from BAIL modifier alone (debug/v31-backtest-results.md)

---

## ~~Change 1: REV Exemption from EMA Hard Gate~~ — REVERTED

**Backtest result:** -11.8 ATR. 99 counter-EMA REVs had 35.4% win rate.
EMA gate STAYS on all REV signals. Data > intuition.
See: debug/v31-backtest-results.md

## Change 2: PD Mid → Reversal Signal

**Lines 750-751:** `bullBreak(pdMid)` → `bullRev(pdMid, pdMidBody)`, same for bear.
**Filtered signals:** Moved from BRK section to REV section (no EMA gate — new signal type, magnet level).
**Text/counts:** Moved from BRK to REV sections with `~ PD Mid` prefix.

**Rationale:** PD Mid = magnet level. BRK at magnets = wrong signal type. REV = right type.

## Change 3: SPY Market Regime → BAIL Modifier

**Detection:** `spyChg` already computed. Add threshold: >+0.3% = BULL, <-0.3% = BEAR, else NEUTRAL.

**BAIL modifier (line 1537):**
- Signal matches SPY regime → no BAIL (hold = true)
- SPY neutral → loose BAIL (pnl > -0.10)
- Signal opposes SPY → current strict BAIL (pnl > 0.05)

**Runner Score:** Add SPY-aligned as 6th factor.

**Backtest result:** +15.5 ATR. 104 signals change from BAIL→HOLD. Win rate 63.6%→74.0%.

## What Does NOT Change

- EMA Hard Gate for BRK AND REV signals (validated +20.47 ATR for BRK, +11.8 ATR for REV)
- FADE, RNG signal logic
- Once-per-session guards
- All existing alerts
- No new request.security() calls
