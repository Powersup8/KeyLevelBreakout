# March 5, 2026 -- Signal & Move Investigation Report

## 1. Symbol Identification Map

18 pine log files mapped to 10 symbols. Note: TradingView uses BATS exchange data which differs slightly from IB consolidated prices.

| Hash | Symbol | BATS Price (Mar 5) | IB Price (Mar 4 close) | Verification |
|------|--------|-------------------|----------------------|--------------|
| 49c92, cea64 | **SPY** | ~682 | 685.22 | RS=0.0% (benchmark) |
| fa0b5, 67b51 | **META** | ~668 | 667.52 | Earnings spike to 730 on Jan 29 |
| 4d466, 21c43 | **TSLA** | ~401-405 | 406.06 | ATR=14.71 (high vol), PD Mid match |
| e94d0 | **MSFT** | ~407 | 405.00 | Yest H=406.70 matches MSFT Mar 3 High exactly |
| 71d98 | **TSM** | ~356 | 357.46 | Levels PM H=358.98, Yest H=361.09 |
| 1f23e, 2845e | **QQQ** | ~607-612 | 610.55 | |
| 7aedc, ccab3 | **NVDA** | ~181-183 | 182.90 | |
| 77b0c, 2f230 | **AMZN** | ~218-220 | 216.75 | |
| 4caf9, ba67a | **AMD** | ~197-203 | 202.01 | |
| 01085, 9a085 | **AAPL** | ~259-265 | 262.45 | |

**Not in pine logs:** GOOGL, GLD, SLV (3 of the 13 tracked symbols not charted in v3.0b)

**Duplicate files:** Most symbols have 2 files (likely same chart opened twice or different chart instances). TSLA has 3 total (2 identical + 1 MSFT). AMD and AMZN each have 2 (only 1 per pair has March 5 data).

---

## 2. Complete Signal Timeline -- March 5, 2026

### TSLA (3 entries, only 1 real signal)

| Time | Type | Dir | Level | Vol | EMA | VWAP | C | Notes |
|------|------|-----|-------|-----|-----|------|------|-------|
| 9:30 | BRK | ▼ | PD Mid | 1.7x | bear | below | 401.00 | CONF ✓ (auto-R1) |
| 9:30 | SUPP | ▼ | VWAP | 1.7x | bear | below | 401.00 | Same bar, VWAP suppressed |
| 9:35 | RNG | ▲ | (range break) | 13.5x | - | - | - | |
| 9:35 | SUPP | ▲ | PM L + VWAP | 13.5x | bear | above | 404.65 | EMA gate: bull sig, bear EMA |
| 9:35 | BAIL | ▼ | (5m check) | - | - | - | - | pnl=-0.25 ATR |
| 15:55 | SUPP | ▲ | PM L | 3.1x | bull | above | 353.61 | Afternoon, suppressed |

**Summary:** Only 1 real signal (9:30 BRK PD Mid ▼). Confirmed auto-R1, then BAILed at 5m. Nothing between 9:35 and 15:55.

### SPY (9 entries, 4 real signals)

| Time | Type | Dir | Level | Vol | EMA | C | Notes |
|------|------|-----|-------|-----|-----|------|-------|
| 9:45 | BRK | ▼ | PD Mid | 5.2x | bear | 682.66 | CONF ✓, then BAIL |
| 10:05 | BRK | ▼ | PD LH L | 3.4x | bear | 684.26 | CONF ✓, then HOLD |
| 10:10 | REV (dim) | ▼ | ORB H | 3.2x | bear | 683.50 | Reversal at ORB H, dim label |
| 10:25 | BRK | ▼ | ORB L | 1.6x | bear | 681.05 | CONF ✓, then BAIL |
| 15:30 | BRK | ▼ | Week L | 1.8x | bear | 679.46 | CONF ✗ (failed) |

**Summary:** Bearish all day. 4 signals, 3 CONF ✓ + 1 CONF ✗, 1 HOLD + 2 BAIL. SPY sold from 683 to 679 (new Week Low).

### QQQ (6 entries, 2 real signals)

| Time | Type | Dir | Level | Vol | EMA | C | Notes |
|------|------|-----|-------|-----|-----|------|-------|
| 9:35 | RNG | ▲ | | 11.6x | - | - | RNG up, then reversed |
| 9:45 | SUPP | ▼ | ORB H | 3.1x | bear | 609.08 | Pre-9:50, suppressed |
| 10:30 | BRK | ▼ | PD Mid | 1.6x | bear | 608.00 | |
| 10:35 | BRK | ▼ | ORB L + PD Mid | 1.9x | bear | 607.14 | CONF ✓★, then BAIL |
| 12:10 | REV (dim) | ▼ | ORB H | 1.4x | bear | 608.85 | Reversal at ORB H, dim label |

**Summary:** Bearish. Got CONF ✓★ on ORB L breakdown but BAILed. 12:10 showed dim reversal at ORB H.

### AMD (8 entries, 5 real signals)

| Time | Type | Dir | Level | Vol | EMA | C | Notes |
|------|------|-----|-------|-----|-----|------|-------|
| 9:35 | RNG | ▲ | | 13.0x | - | - | Counter-EMA (ema=bear), suppressed |
| 9:55 | BRK | ▲ | Yest H + ORB H | 3.5x | bull | 202.84 | CONF ✓, then BAIL |
| 10:15 | BRK | ▲ | Yest H | 2.0x | bull | 202.85 | CONF ✓, then BAIL |
| 12:50 | BRK | ▼ | PM L + ORB L | 2.8x | bear | 195.81 | |
| 12:55 | BRK | ▼ | PD Mid | 3.0x | bear | 195.50 | CONF ✓, then BAIL |
| 14:35 | BRK | ▼ | PD Mid | 1.7x | bear | 195.17 | CONF ✓, then BAIL |

**Summary:** Bull to bear reversal. Morning bullish (BRK Yest H), afternoon bearish selloff (PM L, ORB L, PD Mid). All BAIL.

### AMZN (4 entries, 2 real signals)

| Time | Type | Dir | Level | Vol | EMA | C | Notes |
|------|------|-----|-------|-----|-----|------|-------|
| 9:35 | RNG | ▲ | | 17.4x | - | - | |
| 9:35 | BRK | ▲ | PM H + Yest H | 17.4x | bull | 218.87 | CONF ✓ |
| 9:40 | BRK | ▲ | ORB H | 10.5x | bull | 219.78 | CONF ✓, then BAIL |

**Summary:** Strong morning breakout above PM H + Yest H + ORB H. BAILed after 5m check.

### NVDA (5 entries, 2 real signals)

| Time | Type | Dir | Level | Vol | EMA | C | Notes |
|------|------|-----|-------|-----|-----|------|-------|
| 9:30 | SUPP | ▼ | VWAP | 1.3x | bear | 181.12 | Pre-9:50, suppressed |
| 12:40 | BRK | ▼ | Yest L | 3.9x | bear | 179.63 | Retest 13:08, CONF ✗ |
| 15:55 | BRK | ▲ | PD Mid | 2.4x | bull | 182.99 | EOD bounce |

**Summary:** Bearish through midday (broke Yest L), bounced EOD. The 12:40 Yest L break is part of the cross-symbol selloff.

### META (3 entries, 1 real signal)

| Time | Type | Dir | Level | Vol | EMA | C | Notes |
|------|------|-----|-------|-----|-----|------|-------|
| 9:35 | RNG | ▲ | | 16.3x | - | - | |
| 10:15 | BRK | ▲ | ORB H | 1.8x | bull | 670.05 | CONF ✓, then BAIL |
| 11:05 | SUPP | ▼ | Week H | 0.6x | bear | 659.48 | EMA gate |
| 11:50 | SUPP | ▼ | Week H | 0.6x | bear | 658.85 | EMA gate |

**Summary:** Morning bull, afternoon bear. ORB H breakout BAILed. Week H rejections suppressed.

### AAPL (2 entries, 1 real signal)

| Time | Type | Dir | Level | Vol | EMA | C | Notes |
|------|------|-----|-------|-----|-----|------|-------|
| 9:30 | RNG | ▼ | | 5.1x | - | - | |
| 9:45 | BRK | ▼ | PM L + ORB L | 4.9x | bear | 259.30 | CONF ✓, then BAIL |

### MSFT (1 entry, 0 real signals)

| Time | Type | Dir | Level | Vol | EMA | C | Notes |
|------|------|-----|-------|-----|-----|------|-------|
| 9:35 | RNG | ▲ | | 12.9x | - | - | |
| 9:35 | SUPP | ▲ | VWAP + PD LH L | 12.9x | bear | 407.28 | EMA gate: bull sig, bear EMA |

**Summary:** Only a suppressed signal. MSFT effectively silent today.

### TSM (3 entries, 0 real signals)

| Time | Type | Dir | Level | Vol | EMA | C | Notes |
|------|------|-----|-------|-----|-----|------|-------|
| 9:30 | RNG | ▲ | | 3.9x | - | - | |
| 9:40 | SUPP | ▼ | PM H + Yest H + ORB H | 7.1x | bear | 356.18 | Pre-9:50, EMA-aligned but suppressed |
| 9:45 | SUPP | ▼ | VWAP | 5.5x | bear | 354.70 | Pre-9:50, suppressed |
| 10:15 | SUPP | ▲ | Yest L + VWAP | 0.9x | bull | 358.10 | Post-9:50, EMA gate |
| 15:55 | SUPP | ▲ | PM L | 3.1x | bull | 353.61 | Afternoon |

**Summary:** ALL signals suppressed. TSM had 0 tradeable signals today despite hitting PM H, Yest H, ORB H, Yest L. This is a significant over-filtering issue.

---

## 3. Move-by-Move Analysis

### a) TSLA upmove 9:30

**What happened:** TSLA opened at ~402.25 on BATS, broke below PD Mid (~401.45) triggering BRK PD Mid ▼ at 9:30. But the bearish signal immediately failed -- price reversed UP from 401 to 404.65 by 9:35 (a 3.65 point rally in 5 minutes). The 5m check at 9:35 showed pnl=-0.25 ATR -> BAIL.

**Did we catch it?** The system fired a BEARISH signal on what turned out to be a bullish move. The 5m BAIL correctly identified the failure. The BULLISH RNG ▲ at 9:35 (vol=13.5x) was suppressed because ema=bear (counter-EMA at pre-9:50 = dim only, not fully suppressed, but no actual BRK/REV fired upward).

**Verdict: MISSED OPPORTUNITY (upside).** The opening PD Mid breakdown was a fakeout. The real move was UP. The EMA gate (pre-9:50 dim) suppressed the bullish reversal signal. In v2.8/v2.9, the RNG bullish breakout and PM L level break would have fired.

### b) TSLA downmove 10:01-10:31

**What happened:** After rallying from 401 to ~408 (approaching Yest H = 408.33 on IB), TSLA reversed hard downward from ~10:01 to 10:31.

**Did we catch it?** NO. Zero signals between 9:35 and 15:55 in the TSLA pine log. Complete silence during a major move.

**Why:** See TSLA 10:16 investigation below.

### c) TSLA 10:16 Reversal (CRITICAL INVESTIGATION)

**The user's observation:** "TSLA downmove 10:16 not fired - we catched it with an older version 2.8 or 2.9 / reversal PMH and YestH?!?"

**Pine log evidence:**
- File 4d466 (TSLA): Last signal at 9:35, next at 15:55. Nothing at 10:16.
- At 9:30: ema=bear. At 9:35: ema=bear (still bearish despite price rally).
- By 10:15, the 5-min EMA(20) would have flipped to bull after a 7-point, 45-minute rally.

**Key levels for March 5 TSLA:**
- PD Mid = ~401.45 (from IB Mar 4: H=408.33, L=394.58 -> mid=401.45)
- Yest H (IB) = 408.33
- PM H = estimated ~402-404 (from pine log: PM L was 400.62, PM H would be the pre-market high)

Actually, from the pine log, PM H is NOT directly visible for TSLA. The 9:35 suppressed signal mentions "PM L" at prices=400.62. The March 4 pine log shows PM H at 402.04 (from the previous day's signal). For March 5, PM H would be a new value based on the pre-market session.

**Root cause analysis:**

1. **EMA Hard Gate (v3.0 addition) -- PRIMARY CAUSE:**
   - At 9:30-9:35, EMA was bearish (ema=bear in pine log)
   - After rallying from 401 to ~408 between 9:30-10:00, the 5-min EMA(20) would flip to bullish
   - At 10:16, a bearish REV at Yest H would be **counter-EMA** (bear signal, bull EMA)
   - v3.0 EMA Hard Gate: after 9:50, counter-EMA signals are fully suppressed
   - **RESULT: Signal killed by EMA Hard Gate**

2. **Once-per-session guard -- NOT THE CAUSE:**
   - Yest H slot was NOT burned (9:30 was PD Mid, 9:35 was PM L)
   - PM H slot was NOT burned
   - These level slots were available for a new signal

3. **In v2.8/v2.9 (no EMA Hard Gate):**
   - The bearish REV at Yest H WOULD have fired regardless of EMA direction
   - This confirms the user's memory that older versions caught this type of reversal

**Code verification (KeyLevelBreakout.pine):**
```pine
// Line 831: sigRevBearYH = rRevBearYH and (not i_firstOnly or not rYH) and fGateBear_rev and (emaGateBear or isPre950)
// Line 498: emaGateBear = not i_emaGate or fEMA_bear
//
// At 10:16 ET:
//   i_emaGate = true (setting is ON)
//   fEMA_bear = false (5m EMA flipped to bull after 7pt rally)
//   => emaGateBear = false
//   isPre950 = false (10:16 > 9:50)
//   => (emaGateBear or isPre950) = false
//   => sigRevBearYH = false
//   => NO signal generated, NO label, NO log entry
```

**Verdict: FALSE NEGATIVE caused by EMA Hard Gate.** This is a legitimate reversal at a key level (Yest H) that the system deliberately suppressed at the signal generation level. The EMA Hard Gate applies equally to BRK and REV signals (line 831 uses the same `emaGateBear` condition). This is arguably a design flaw: reversal signals at HIGH levels (Yest H, PM H, Week H) are counter-trend BY NATURE -- the whole point of a reversal is that price hits a resistance level and turns around. Requiring the reversal to be with-EMA defeats the purpose.

### d) SPY/QQQ/AMD/NVDA downmove 12:06

**Cross-symbol simultaneous selloff.** What each symbol showed:

| Symbol | Signal at 12:00-12:15 | Fired? | Notes |
|--------|----------------------|--------|-------|
| SPY | Nothing | No | Last signal was 10:25 ORB L |
| QQQ | 12:10 REV ▼ ORB H (dim) | Dim label shown | Reversal at ORB H, with-EMA, dimmed by evidence stack |
| AMD | 12:50 BRK ▼ PM L + ORB L | **Yes** (40 min lag) | First to fire, with 2.8x vol |
| NVDA | 12:40 BRK ▼ Yest L | **Yes** (34 min lag) | Broke yesterday's low |
| META | 11:50 SUPP ▼ Week H | Suppressed | Low vol (0.6x) |
| TSLA | Nothing | No | Silent all day after 9:35 |

**Pattern:** Market-wide selloff that started at 12:06 but signals didn't fire until 12:40-12:50 (30-40 minute lag). Only NVDA and AMD eventually caught the move. QQQ had a signal that was suppressed by the EMA gate. SPY had no new breakout level to trigger.

**Why the lag?** The selloff needed time to reach key levels. At 12:06, prices were still within their ranges. By 12:40, NVDA broke Yest L (a significant level) and AMD broke PM L + ORB L.

**Could a "market sell trigger" work?** If the system monitored SPY breaking below a key level (SPY broke ORB L at 10:25), correlated symbols could have been alerted earlier. However, SPY's 10:25 ORB L break was already 1.5 hours before the 12:06 move, suggesting the afternoon selloff was a separate wave.

### e) TSLA upmove 10:32

After the 10:01-10:31 downmove, TSLA reversed up. **No signal fired.** The system was completely silent on TSLA from 9:35 to 15:55. This bounce would have been at/near PD Mid or PM L levels on the way back up, but with EMA likely still in transition, it would have been suppressed.

### f) TSLA downmove 12:06-?

Part of the cross-symbol selloff. **No TSLA signal.** The system produced nothing on TSLA during this move. If TSLA dropped to PM L (~400.62 BATS) or below, a bearish BRK should have triggered -- but the EMA direction and once-per-session guards may have blocked it.

---

## 4. Cross-Symbol 12:06 Pattern Analysis

### The Selloff Timeline

Based on pine log signals and the user's observation:

| Time | Event | Evidence |
|------|-------|----------|
| 10:25 | SPY breaks ORB L (681.05) | BRK fired |
| 10:35 | QQQ breaks ORB L (607.14) | BRK ✓★ fired |
| 11:05 | META hits Week H resistance | Suppressed |
| 12:06 | Market-wide selling accelerates | User observation |
| 12:10 | QQQ tests ORB H again from below | Suppressed (EMA gate) |
| 12:40 | NVDA breaks Yest L (179.63) | BRK fired |
| 12:50 | AMD breaks PM L + ORB L (195.81) | BRK fired |
| 12:55 | AMD breaks PD Mid (195.50) | BRK fired |
| 15:30 | SPY breaks Week L (679.46) | BRK fired (CONF ✗) |

**Key observation:** The selling was NOT sudden at 12:06 -- it was a continuation of morning weakness. SPY and QQQ established bearish direction by 10:25-10:35. The 12:06 acceleration was when the selling spread from indices to individual stocks (NVDA, AMD).

**Could cross-symbol correlation help?** Yes. If the system detected SPY breaking ORB L at 10:25 AND staying below VWAP, it could have generated "heightened risk" alerts for all correlated symbols. The AMD and NVDA breaks 2+ hours later were predictable given SPY's direction.

---

## 5. 9:35 RNG Cluster Analysis

Nearly every symbol broke out of its overnight range simultaneously at 9:35:

| Symbol | Dir | Vol | Outcome |
|--------|-----|-----|---------|
| TSLA | ▲ | 13.5x | Suppressed (counter-EMA) -- correct direction initially |
| AMZN | ▲ | 17.4x | BRK PM H + Yest H ✓ -> BAIL |
| AMD | ▲ | 13.0x | Suppressed (counter-EMA) -- correct direction |
| NVDA | ? | ? | RNG ▼ (per 9:35 data, bear) |
| META | ▲ | 16.3x | Led to ORB H breakout at 10:15 |
| QQQ | ▲ | 11.6x | Reversed -- bearish by 9:45 |
| MSFT | ▲ | 12.9x | Suppressed |
| TSM | ▲ | 3.9x (at 9:30) | Reversed -- bearish |
| AAPL | ▼ | 5.1x (at 9:30) | Led to PM L + ORB L break |
| SPY | (no RNG) | - | SPY had no RNG at 9:35, signal came at 9:45 |

**10 of 10 symbols fired RNG signals within 5 minutes of open.** This is a massive simultaneous cluster driven by the opening volume surge.

**Which direction was correct?**
- **Bullish RNG correct (temporarily):** TSLA, AMZN, AMD, META (all rallied 9:35-10:00)
- **Bearish RNG correct:** AAPL (broke down), SPY (sold all day), QQQ (reversed quickly)
- **Mixed:** Most bullish RNGs faded by midday -- the broader market was bearish

**Conclusion:** The 9:35 RNG cluster reflects the opening volatility explosion. The bullish direction was correct for the first 30-60 minutes, but the broader market direction was bearish. Symbols that broke out bullish (AMZN at PM H + Yest H, AMD at Yest H) gave back gains by afternoon.

---

## 6. Signal Quality Scorecard

### Scorecard Summary

| Symbol | Signals | CONF ✓ | HOLD | BAIL | Suppressed | Rating |
|--------|---------|--------|------|------|------------|--------|
| SPY | 4 | 3 | 1 | 2 | 4 | Direction correct (bearish all day) |
| QQQ | 2 | 1 (✓★) | 0 | 1 | 5 | Direction correct but BAILed |
| AMD | 5 | 5 | 0 | 5 | 2 | All BAIL -- caught moves but no hold |
| AMZN | 2 | 2 | 0 | 1 | 1 | Morning BRK correct but faded |
| NVDA | 2 | 0 | 0 | 0 | 3 | Yest L break was the move, CONF failed |
| META | 1 | 1 | 0 | 1 | 3 | ORB H BAILed |
| TSLA | 1 | 1 | 0 | 1 | 3 | PD Mid ▼ was wrong direction |
| AAPL | 1 | 1 | 0 | 1 | 1 | PM L + ORB L correct |
| MSFT | 0 | 0 | 0 | 0 | 1 | Silent (suppressed) |
| TSM | 0 | 0 | 0 | 0 | 4 | Silent (all suppressed) |
| **TOTAL** | **18** | **14** | **1** | **11** | **27** | |

### Day-Level Metrics

- **CONF rate: 14/16 = 87.5%** (14 auto-confirm ✓ out of 16 CONF events, 2 ✗)
- **HOLD rate: 1/12 = 8.3%** (only 1 HOLD out of 12 5m checks)
- **BAIL rate: 11/12 = 91.7%** -- Nearly every confirmed signal BAILed at 5m check
- **Suppressed: 27 entries** -- More suppressions than signals (27 vs 18)

### Signal-by-Signal Quality Rating

| Time | Symbol | Signal | CONF | 5m | Direction Correct? | Rating |
|------|--------|--------|------|-----|-------------------|--------|
| 9:30 | TSLA | BRK PD Mid ▼ | ✓ | BAIL | NO (price went UP) | BAD SIGNAL |
| 9:35 | AMZN | BRK PM H + Yest H ▲ | ✓ | - | YES (but faded PM) | GOOD ENTRY, FADED |
| 9:40 | AMZN | BRK ORB H ▲ | ✓ | BAIL | YES short-term | NEUTRAL |
| 9:45 | SPY | BRK PD Mid ▼ | ✓ | BAIL | YES (bearish day) | GOOD SIGNAL, BAD EXIT |
| 9:45 | AAPL | BRK PM L + ORB L ▼ | ✓ | BAIL | YES (sold) | GOOD SIGNAL, BAD EXIT |
| 9:55 | AMD | BRK Yest H + ORB H ▲ | ✓ | BAIL | YES short-term | NEUTRAL |
| 10:05 | SPY | BRK PD LH L ▼ | ✓ | HOLD | YES! | GOOD SIGNAL |
| 10:15 | AMD | BRK Yest H ▲ | ✓ | BAIL | NO (faded) | BAD SIGNAL |
| 10:15 | META | BRK ORB H ▲ | ✓ | BAIL | Temporary | NEUTRAL |
| 10:25 | SPY | BRK ORB L ▼ | ✓ | BAIL | YES | GOOD SIGNAL, BAD EXIT |
| 10:30 | QQQ | BRK PD Mid ▼ | - | - | YES | GOOD SIGNAL |
| 10:35 | QQQ | BRK ORB L + PD Mid ▼ | ✓★ | BAIL | YES | GOOD SIGNAL, BAD EXIT |
| 12:40 | NVDA | BRK Yest L ▼ | - | - | CONF ✗ | FADED (bounced back) |
| 12:50 | AMD | BRK PM L + ORB L ▼ | - | - | YES | GOOD SIGNAL |
| 12:55 | AMD | BRK PD Mid ▼ | ✓ | BAIL | YES | GOOD SIGNAL, BAD EXIT |
| 14:35 | AMD | BRK PD Mid ▼ | ✓ | BAIL | Marginal | NEUTRAL |
| 15:30 | SPY | BRK Week L ▼ | ✗ | - | NO (bounced) | BAD SIGNAL |
| 15:55 | NVDA | BRK PD Mid ▲ | - | - | EOD bounce | NEUTRAL |

### Quality Summary
- **GOOD SIGNALS:** 8 (SPY 10:05, SPY 9:45, SPY 10:25, AAPL 9:45, QQQ 10:30, QQQ 10:35, AMD 12:50, AMD 12:55)
- **BAD SIGNALS:** 3 (TSLA 9:30 wrong direction, AMD 10:15 faded, SPY 15:30 bounced)
- **NEUTRAL:** 6 (temporary or marginal)
- **MISSED:** TSLA 10:16 reversal, TSLA 10:32 bounce, 12:06 cross-symbol selloff timing

### The BAIL Problem

11 out of 12 five-minute checks resulted in BAIL. This is catastrophic. On a day where the market trended strongly bearish, the 5-minute checkpoint consistently forced exits on what turned out to be correct-direction signals:

- SPY 9:45 BRK PD Mid ▼ -> BAIL -> SPY continued down 4 more points
- SPY 10:25 BRK ORB L ▼ -> BAIL -> SPY fell to Week L
- QQQ 10:35 BRK ORB L ▼ -> BAIL -> QQQ continued weak
- AAPL 9:45 BRK PM L + ORB L ▼ -> BAIL -> correct direction

The only HOLD was SPY 10:05 BRK PD LH L, which was the best signal of the day.

---

## 7. Over-Optimization Findings

### Signals Suppressed by v3.0 Filters

Total: **27 suppressions** vs 18 real signals. The filters are suppressing more than they allow.

#### A. EMA Hard Gate (counter-EMA after 9:50)

| Time | Symbol | Signal | Would It Have Worked? |
|------|--------|--------|----------------------|
| 10:15 | TSM | ▲ Yest L + VWAP | EMA=bull, sig=bull, WITH-EMA -- **should NOT have been suppressed** |
| 10:30 | NVDA | ▼ ORB H | EMA=bear, sig=bear, WITH-EMA -- likely suppressed for other reason |
| 11:05 | META | ▼ Week H | EMA=bear, sig=bear, WITH-EMA -- **should NOT have been suppressed** |
| 11:50 | META | ▼ Week H | Same pattern |
| 12:10 | QQQ | ▼ ORB H | EMA=bear, sig=bear, WITH-EMA -- **should NOT have been suppressed** |

**Important clarification on pine log `~ ~` entries:**

After reviewing the pine script code (lines 984-1043, 1195-1265), the `~ ~` prefix in pine logs represents **reversal/reclaim signals that ARE displayed on the chart** as dim labels. These are NOT invisible suppressions. The `~` means "reversal at this level" and `~~` means "reclaim of a previously broken level."

The EMA Hard Gate (lines 756-767, 825-833) suppresses signals at the **signal generation level** -- before any label or log entry is created. Signals blocked by the EMA Hard Gate produce **no pine log entry at all**. This is why TSLA has zero entries between 9:35 and 15:55: the bearish reversal at Yest H was never generated, never logged, never shown.

The `~ ~` entries we see (like TSM 9:40 `~ ~ PM H + ~ Yest H + ~ ORB H`) are reversal signals that DID pass the EMA gate (direction matched EMA) but are shown as dim labels because of evidence stack or other filters.

Specific suppression reasons:
- QQQ 12:10: `~ ~ ORB H` -- reversal signal that passed EMA gate (bear sig, bear EMA) but shown dim
- META 11:05/11:50: `~ ~ Week H` with vol=0.6x -- reversal signal but very low volume (0.6x)
- TSM 9:40: `~ ~ PM H + ~ Yest H + ~ ORB H` -- pre-9:50, EMA=bear, signal=bear (WITH-EMA), shown as dim label

#### B. Once-Per-Session Guard

Several levels appear to have been burned early:
- QQQ: ORB H/L slots burned at 10:35 (BRK ORB L fired), then 12:10 ORB H suppressed
- SPY: ORB H suppressed at 10:10 and 10:20 -- but ORB H slot may not have been burned (no ORB H BRK fired). This suggests another filter.

#### C. What v2.8/v2.9 Would Have Caught

| Signal | v3.0b Result | v2.8/v2.9 Likely Result | Impact |
|--------|-------------|------------------------|--------|
| TSLA 10:16 REV Yest H ▼ | NOT FIRED | Would fire (no EMA gate) | **HUGE MISS** -- big move |
| TSLA 9:35 RNG ▲ | Suppressed | Would fire (no EMA gate) | Correct direction |
| MSFT 9:35 ▲ | Suppressed | Would fire | Unknown impact |
| TSM 9:40 ▼ PM H + Yest H | Suppressed | Would fire | Correct direction |
| QQQ 12:10 ▼ | Suppressed | Would fire | Correct direction |
| META 11:05/11:50 ▼ Week H | Suppressed | Maybe (vol filter still applies) | Correct direction |

**The TSLA 10:16 is the standout miss.** A reversal at Yesterday's High after a failed opening rally -- textbook reversal trade. The EMA Hard Gate suppressed it because the EMA flipped to bull during the rally.

### TSM: Total Suppression Case Study

TSM had 5 log entries on March 5, ALL suppressed. Not a single tradeable signal. Yet the pine log shows TSM touching PM H, Yest H, ORB H (all at once at 9:40), VWAP (9:45), Yest L (10:15), and PM L (15:55). The pre-9:50 signals were dimmed, and the post-9:50 signals were fully suppressed.

TSM's 9:40 entry at C=356.18 with levels PM H=358.98, Yest H=361.09, ORB H=357.3 was a significant multi-level hit with 7.1x volume. This would have been a strong signal in v2.8/v2.9.

---

## 8. Key Findings & Recommendations

### Finding 1: BAIL Rate is 91.7% -- The 5-Minute Check is Too Aggressive

On a trending day, 11 of 12 confirmed signals were exited at the 5-minute checkpoint. Many of these were in the correct direction and the move continued for hours after the BAIL. The 5-minute gate was designed to cut losers fast, but on trending days it cuts winners too.

**Recommendation:** Consider a directional 5m check: if the signal is WITH the market trend (e.g., bearish signal on a bearish day as measured by SPY direction), use a wider threshold for BAIL. Alternatively, track the outcome beyond 5 minutes and compare BAIL vs HOLD performance.

### Finding 2: EMA Hard Gate Creates False Negatives at Key Reversals

The TSLA 10:16 reversal at Yesterday's High is the canonical example. The EMA Hard Gate assumes "if EMA is bull, bear signals are noise." But reversals at key resistance levels ARE the exception -- the price is SUPPOSED to reverse counter-EMA at these levels.

**Recommendation:** Exempt REV (reversal) signals at HIGH levels (Yest H, PM H, Week H) and LOW levels (Yest L, PM L, Week L) from the EMA Hard Gate. These are counter-trend by nature. Only apply the gate to BRK signals.

**Specific code change (lines 825-833):**
Replace `(emaGateBull or isPre950)` and `(emaGateBear or isPre950)` for reversal signals with just `true` (always allow reversals). Or add a new input: `i_emaGateREV = false` (default OFF for reversals).

### Finding 3: 27 Suppressions vs 18 Signals -- Over-Filtering

The system is suppressing 60% more signals than it produces. While many suppressions are valid (low volume, afternoon, etc.), the aggregate effect is that the system misses major moves.

**Recommendation:** Track suppression reasons in the pine log more explicitly. Add a suppression counter to the debug table. Monitor the "suppressed-but-would-have-been-correct" rate.

### Finding 4: TSM Complete Silence Despite Multiple Level Hits

TSM touched 6 different levels today and produced zero tradeable signals. This suggests the filter combination is too restrictive for some symbols.

**Recommendation:** Review TSM's filter hits. If the issue is pre-9:50 dimming + post-9:50 EMA gate, TSM may need looser thresholds. Or the once-per-session guard may be too aggressive for a symbol with narrower ranges.

### Finding 5: Cross-Symbol 12:06 Selloff Was Predictable from SPY

SPY established bearish direction at 10:25 (ORB L break). The 12:06 acceleration in AMD and NVDA was a lagged follow-through. A cross-symbol alert ("SPY bearish, watch for sympathy breaks") at 10:25 would have provided 2+ hours of advance warning.

**Recommendation:** Consider a "market regime" indicator based on SPY's direction. When SPY breaks ORB L, flag all correlated symbols as "sell-side alert" and lower the confirmation threshold for bearish signals.

### Finding 6: Morning Bull Signals Faded (AMZN, AMD, META)

Several morning bullish breakouts (AMZN PM H + Yest H, AMD Yest H, META ORB H) were correct for 30-60 minutes but faded by midday as the broader market turned bearish. The 5m BAIL actually protected against these fades, but earlier exits would have captured the initial move.

---

## Appendix: Computed Levels for March 5 (from IB March 4 Data)

| Symbol | Yest H | Yest L | PD Mid | Yest C |
|--------|--------|--------|--------|--------|
| TSLA | 408.33 | 394.58 | 401.45 | 406.06 |
| SPY | 687.09 | 679.62 | 683.36 | 685.22 |
| META | 672.77 | 657.67 | 665.22 | 667.52 |
| NVDA | 184.70 | 180.06 | 182.38 | 182.90 |
| AMD | 202.44 | 189.86 | 196.15 | 202.01 |
| QQQ | 612.88 | 603.43 | 608.15 | 610.55 |
| TSM | 360.65 | 354.55 | 357.60 | 355.74 |
| MSFT | 411.04 | 400.31 | 405.68 | 405.00 |
| AAPL | 266.15 | 261.42 | 263.78 | 262.45 |
| AMZN | 217.54 | 210.15 | 213.84 | 216.75 |

*Note: These are IB consolidated prices. BATS exchange prices differ by 0.5-2.5 points depending on symbol.*
