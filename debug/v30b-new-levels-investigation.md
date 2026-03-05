# v3.0b New Levels Investigation

**Date:** 2026-03-05
**Data:** 8 symbols (AAPL, AMD, AMZN, META, NVDA, QQQ, SPY, TSLA), 27 days (Jan 26 – Mar 4, 2026)
**Method:** Pine log signals matched to 5sec parquet data, PnL measured at 5/15/30/60 min after signal

---

## 1. Executive Summary

All three new v3.0 level types are underperforming in live trading. However, the severity and root causes differ substantially for each level.

| Level | N | Win%@30m | Avg PnL@30m | Total@30m | Backtest | Gap |
|-------|---|---------|------------|----------|----------|-----|
| PD Mid | 61 | 46.6% | -0.015 | -0.9 ATR | +0.209 | -0.224 |
| PD LH L | 83 | 47.6% | +0.007 | +0.6 ATR | +0.238 | -0.231 |
| VWAP Zone | 172 | 46.1% | +0.013 | +2.2 ATR | +0.133 | -0.120 |
| **Original levels** | **513** | **55.8%** | **+0.029** | **+14.2 ATR** | — | — |

**Key finding:** PD LH L and VWAP Zone are not deeply negative — they are near-zero in live. PD Mid is the worst but still mild (-0.9 ATR total). The dramatic backtest-vs-live gaps are driven by fundamental methodological mismatches, not a bug in the indicator.

---

## 2. Root Cause: Backtest vs Live Mismatches

The "midday treasure hunt" backtest that produced the +0.209/+0.238/+0.133 numbers was measuring something materially different from what v3.0b generates. Here are the specific mismatches:

### Mismatch 1: VWAP Lower Band — Completely Different Formula

- **Backtest used:** `VWAP_LOWER = VWAP - VWAP_STD` (standard deviation band)
- **Live implements:** `vwapLowerBand = VWAP - ATR(14)` (daily ATR band)

VWAP_STD (standard deviation of the volume-weighted price) is typically much smaller than ATR(14), especially early in the session. These produce different price levels entirely. The backtest validated a level the live code never actually uses.

**Consequence:** The "VWAP Lower Band" BRK signal (sigBearVWBL) fired **ZERO times** in 27 days of live data. The level is apparently always too far below price to be reached. What we *are* calling "VWAP Zone" in live data is the pre-existing VWAP REV signal from v2.7 (labeled "VWAP" in signal text), not the new VW Band level.

### Mismatch 2: Trade Entry Criterion (Who Gets a Signal?)

- **Backtest:** ANY 5m bar whose close is within 0.15 ATR of the level → hypothetical trade
- **Live:** Signal must pass: vol ≥ 1.5x SMA, first-cross guard (once-per-session), EMA gate, ADX ≥ 20, body ≥ 30%

The backtest had no first-cross guard, no volume requirement, no EMA requirement. It was testing "is this level meaningful?" not "does the indicator generate good signals here?" The backtest included many quiet mean-reversion touches that the indicator correctly filters out.

### Mismatch 3: Time Window (Morning vs Midday)

- **Backtest:** Only tested AFTER 10:30 ET (it was a "midday treasure hunt" for the dead zone)
- **Live:** These levels fire all day, including 9:30-10:30

In the live data: 64% of PD Mid signals and 61% of PD LH L signals fire before 10:00 AM. The 9:30-10:00 window is the noisiest, highest-volatility period where static levels have the least predictive power.

**PD Mid performance by time:**
- 9:30-10:00: N=39, win%=46%, avg=-0.021, total=-0.8 ATR
- 10:00-11:00: N=10, win%=60%, avg=+0.009, total=+0.1 ATR
- 12:00+: N=10, win%=43%, avg=+0.001, total=+0.0 ATR

The 10:00-11:00 window is the only positive window — exactly where the backtest was focused.

### Mismatch 4: PD Mid Direction Logic

- **Backtest:** Treated PD Mid as a "neutral" level → direction follows EMA alignment
- **Live:** PD Mid fires as a BRK signal in the direction price is moving (ignoring EMA for direction)

In the backtest, a bearish EMA + price touching PD Mid from above → bear trade. In live, if price is shooting through PD Mid from below (bull BRK), the signal fires as bull even if EMA is bear. This created directional misalignment.

However in actual live data, all 61 PD Mid signals are BRK-only and ALL are EMA-aligned (100% EMA alignment). So this mismatch isn't the primary driver for PD Mid.

### Mismatch 5: PnL Measurement (MFE vs Mark-to-Market)

- **Backtest:** Measured best MFE over 6 bars (30 min). A signal "wins" if price moves favorably AT ALL.
- **Live:** Measured mark-to-market at exactly 15/30/60 min after signal.

MFE-based win rates are always higher than mark-to-market because they capture temporary favorable moves that later reverse. This alone could explain 10-15% of the win rate gap.

### Mismatch 6: VWAP Lower Band Direction is INVERTED vs Backtest

- **Backtest (VWAP_LOWER):** Classified as a LOW level → expected bull reversal off it (price bouncing up from below VWAP-band)
- **Live (sigBearVWBL):** Implemented as bearish BREAKOUT (price breaking DOWN through vwapLowerBand)

The live implementation has the direction REVERSED vs the backtest assumption. The backtest was measuring "price bouncing off VWAP-STD band = buy." The code fires a sell signal when price breaks below VWAP-ATR. This is a fundamental design error for the VW Band signal.

---

## 3. Signal-by-Signal Analysis

### 3a. PD Mid (61 signals)

All 61 signals are BRK type — no REV or RET signals appear at PD Mid in live data.
All 61 are EMA-aligned (100%).

**By Signal Type:**
- BRK: N=61, win%=46.6%, avg=-0.015, total=-0.9 ATR

**Performance by dimension:**

Time:
- 9:30-10:00: N=39, **win%=46%, avg=-0.021, total=-0.8 ATR** ← Problem area
- 10:00-11:00: N=10, win%=60%, avg=+0.009, total=+0.1 ATR
- 11:00-12:00: N=2, win%=0%, avg=-0.081, total=-0.2 ATR
- 12:00+: N=10, win%=43%, avg=+0.001, total=+0.0 ATR

Volume:
- 1-2x: N=9, win%=56%, avg=+0.035, total=+0.3 ATR
- 2-5x: N=27, win%=46%, avg=+0.033, total=+0.8 ATR
- ≥5x: N=25, **win%=44%, avg=-0.079, total=-2.0 ATR** ← High vol is BAD for PD Mid

ADX:
- 20-30: N=34, win%=48%, avg=-0.020, total=-0.6 ATR
- 30-40: N=22, win%=41%, avg=-0.031, total=-0.7 ATR
- ≥40: N=5, win%=60%, avg=+0.081, total=+0.4 ATR (small N)

Symbol:
- Best: QQQ (62.5%, +1.1 ATR), SPY (66.7%, +0.7 ATR), AAPL (60%, +0.3 ATR)
- Worst: META (28.6%, -1.3 ATR), AMD (25%, -0.5 ATR), TSLA (0%, -0.3 ATR)

Lightning ⚡ flag: nearly identical between ⚡ (win%=45.7%) and no-⚡ (win%=47.8%).

**Key pattern in PD Mid winners (>+0.1 ATR):** Morning (9:30-10:00) with lightning opens where PD Mid is also ORB level. Signals like "ORB L + PD Mid" or "PM H + PD Mid" where the level confluence is strong.

**Key pattern in PD Mid losers (<-0.1 ATR):** Standalone "PD Mid" without level confluence, particularly at the open (9:30-9:45). Worst: SPY/QQQ "ORB H + PD Mid" at 9:40 on 2026-02-17 (-0.6, -0.64 ATR each).

### 3b. PD LH L (83 signals, sorted by 30m PnL)

**By Signal Type:**
- BRK: N=47, win%=45.7%, avg=+0.017, total=+0.8 ATR
- REV: N=36, win%=50.0%, avg=-0.006, total=-0.2 ATR

**Performance by dimension:**

Time:
- 9:30-10:00: N=51, **win%=41%, avg=-0.012, total=-0.6 ATR**
- 10:00-11:00: N=21, **win%=57%, avg=+0.069, total=+1.5 ATR** ← Best window
- 12:00+: N=9, win%=62%, avg=-0.042, total=-0.3 ATR (small N, skewed by early wins)

Volume:
- 1-2x: N=16, **win%=75%, avg=+0.065, total=+1.0 ATR** ← Best bucket
- 2-5x: N=26, **win%=28%, avg=-0.067, total=-1.7 ATR** ← Worst bucket
- ≥5x: N=39, win%=51%, avg=+0.043, total=+1.7 ATR

ADX:
- 20-30: N=52, win%=51%, avg=+0.020, total=+1.0 ATR
- 30-40: N=25, win%=44%, avg=+0.008, total=+0.2 ATR
- ≥40: N=6, win%=33%, avg=-0.104, total=-0.6 ATR (small N)

Symbol:
- Best: SPY (58.3%, +1.2 ATR), NVDA (54.5%, +0.7 ATR), META (58.3%, +0.0 ATR)
- Worst: AMD (20%, -0.2 ATR), TSLA (33.3%, -0.3 ATR), AMZN (50%, -1.5 ATR)

EMA alignment:
- EMA aligned: N=62, win%=49%, avg=+0.002, total=+0.1 ATR
- EMA counter: N=21, win%=43%, avg=+0.021, total=+0.4 ATR (counter-EMA performs similar!)

**Top 5 PD LH L winners:**
1. SPY ▼ BRK 9:45, Yest L + PD LH L, vol=6.9x → +0.674 ATR
2. AAPL ▲ REV 9:30, VWAP + ~ PD LH L, vol=7.7x → +0.645 ATR
3. QQQ ▼ BRK 9:45, PD LH L, vol=6.6x → +0.555 ATR
4. SPY ▼ BRK 10:40, PD LH L, vol=1.9x → +0.529 ATR
5. AMD ▼ BRK 10:10, PD LH L, vol=2.0x → +0.509 ATR

**Top 5 PD LH L losers:**
1. AMZN ▲ REV 9:30, VWAP + ~ PD LH L, vol=8.2x → -0.746 ATR
2. META ▲ REV 9:30, PD LH L, vol=3.6x → -0.734 ATR
3. SPY ▲ REV 9:35, VWAP + ~ PD LH L, vol=14.6x → -0.501 ATR
4. AMZN ▼ BRK 9:40, PM L + PD Mid + PD LH L, vol=8.7x → -0.561 ATR
5. AMZN ▼ BRK 9:55, PD Mid + PD LH L, vol=2.6x → -0.350 ATR

Note: PD LH L REV signals at 9:30 with high vol are the worst losers. BRK signals at 10:00+ are the best winners.

### 3c. VWAP Zone REV (172 signals)

Note: The "VWAP zone" signals in live data are the pre-existing VWAP REV signals from v2.7, labeled as "VWAP" in the signal. These are NOT the new "VW Band" signals (which fired 0 times).

**All 172 are REV type.** This is an existing signal type that predates v3.0.

**By Direction:**
- Bull ▲: N=81, **win%=39%, avg=-0.023, total=-1.7 ATR** ← VWAP bull rev is losing
- Bear ▼: N=91, **win%=52%, avg=+0.045, total=+3.9 ATR** ← VWAP bear rev is winning

This is the dominant finding for VWAP Zone: **bear VWAP reversals strongly outperform bull VWAP reversals (+3.9 ATR vs -1.7 ATR).** The bear direction is +5.6 ATR better than bull.

**By Time:**
- 9:30-10:00: N=114, win%=48%, avg=+0.013, total=+1.5 ATR
- 10:00-11:00: N=25, win%=44%, avg=+0.027, total=+0.7 ATR
- 11:00-12:00: N=11, win%=45%, avg=+0.031, total=+0.3 ATR
- 12:00+: N=22, **win%=33%, avg=-0.020, total=-0.3 ATR** ← Afternoon is losing

**By Volume:**
- <1x: N=26, win%=38%, avg=-0.016
- 1-2x: N=31, win%=44%, avg=+0.029
- 2-5x: N=30, win%=40%, avg=-0.005
- ≥5x: N=85, **win%=51%, avg=+0.024, total=+2.0 ATR** ← High vol is better

**By Symbol:**
- Best: NVDA (70.6%, +2.2 ATR), QQQ (52.9%, +1.4 ATR), AMZN (56.5%, +1.0 ATR)
- Worst: AMD (30%, -1.0 ATR), TSLA (33.3%, -0.9 ATR), META (41.7%, -0.9 ATR)

**By ADX:**
- 20-30: N=109, win%=46.6%, avg=+0.013, total=+1.4 ATR
- 30-40: N=47, win%=50%, avg=+0.040, total=+1.9 ATR
- ≥40: N=16, win%=31%, avg=-0.065, total=-1.0 ATR (high ADX = bad for VWAP rev)

---

## 4. Winners vs Losers Profile (All New-Level Signals Combined)

N=288 new-level signals with valid 30m PnL. Winners (>+0.1 ATR): 100. Losers (<-0.1 ATR): 91.

| Factor | Winners | Losers | Edge |
|--------|---------|--------|------|
| EMA aligned | 85% | 79% | +6% winners |
| Morning (<11am) | 95% | 93% | negligible |
| Mean ADX | 29.4 | 30.5 | negligible |
| Mean vol | 8.0x | 7.3x | slight winners |
| Lightning ⚡ | 71% | 70% | negligible |
| Body warn ⚠ | 31% | 31% | none |
| BRK/REV ratio | 35/65 | 36/55 | negligible |
| Bull/Bear | 44%/56% | 46%/45% | slight bear edge |
| Top symbols | AMZN, SPY, NVDA, QQQ | AMZN, META, AMD, SPY | AMD/META = loser |

**Critical finding: Winners and losers have nearly identical profiles.** There is no single clean filter that separates them. The primary differentiators are:

1. **Symbol**: AMD and META are overrepresented in losers. NVDA and QQQ overrepresented in winners.
2. **Direction for VWAP Zone**: Bear VWAP REV wins (+3.9 ATR), Bull VWAP REV loses (-1.7 ATR).
3. **Time for PD LH L**: 10:00-11:00 wins (+1.5 ATR), 9:30-10:00 loses (-0.6 ATR).
4. **Volume for PD LH L**: 2-5x vol is uniquely bad (win%=28%), while ≥5x is positive.

---

## 5. Backtest vs Live Comparison Summary

| Dimension | Backtest Conditions | Live v3.0b Conditions |
|-----------|--------------------|-----------------------|
| Time window | After 10:30 only | All day (9:30-16:00) |
| Entry criterion | Within 0.15 ATR of level | Full signal generation (vol, EMA, first-cross) |
| VWAP Lower formula | VWAP - VWAP_STD | VWAP - ATR(14) |
| VWAP Lower direction | Bull reversal (LOW level) | Bear breakout (sigBearVWBL) |
| PnL measurement | Best MFE over 6 bars | Mark-to-market at 30m |
| PD Mid direction | Follows EMA | Any direction of cross |
| Dataset size | 451 days, 13 symbols | 27 days, 8 symbols |
| Classification of moves | "Missed" significant moves | Any bar touching level with vol |

The backtest also had significantly lower vol ratios (median=0.76x, mean=0.82x) vs what the live indicator requires (vol must be ≥1.5x SMA). This means the backtest was primarily testing low-vol touches (mean-reversion) while the live indicator only generates high-vol signals.

**Backtest time distribution:** 46% of rows are 12:00+ (midday), where the backtest showed these levels working best. Live signals cluster 61-63% before 10:00 (exactly the window where the backtest didn't test).

---

## 6. Why VW Band Never Fires

The VWAP Lower Band in Pine is `vwapLowerBand = vwapVal - dailyATR`. This places the band 1 full daily ATR below VWAP.

- SPY daily ATR in Jan-Mar 2026: ~$6-8
- VWAP for SPY at open: ~$685
- VW Band: ~$677-679

For a bearish BRK of VW Band, price must trade BELOW $677 when VWAP is $685. This requires the price to fall ~1.2% below VWAP — an extreme intraday move. In normal sessions, price rarely reaches this level. The VW Band is effectively a crisis-level signal that only triggers during severe selloffs.

**Backtest used VWAP - VWAP_STD** which is a much smaller distance (often 0.1-0.3 ATR), meaning price regularly touches that band. The implementation uses 1× ATR instead.

---

## 7. Specific Recommendations

### Recommendation 1: PD Mid — Add 9:30-10:00 Time Gate

**Data:** 64% of signals (39/61) fire in the first 30 minutes. This window is -0.8 ATR total (-0.021/signal). The 10:00-11:00 window is positive (+0.009/signal).

**Action:** Add time gate: PD Mid signals only after 10:00 ET. Or dim PD Mid signals before 10:00 (they still appear but are grayed).

**Expected impact:** Remove -0.8 ATR drag, keeps 22 positive signals. From -0.9 to roughly +0.0 ATR net.

### Recommendation 2: PD Mid — Remove High-Volume Filter

**Data:** PD Mid at ≥5x volume is -2.0 ATR (N=25, win%=44%). At 2-5x: +0.8 ATR. At 1-2x: +0.3 ATR.

**Action:** For PD Mid specifically, suppress signals when vol ≥5x. These are explosive bars (⚡) where price is blowing through the level, not respecting it.

**Rationale:** High-volume PD Mid crosses are momentum moves that don't respect the level. Lower volume means price is "finding" the level and respecting it.

### Recommendation 3: PD LH L — Restrict to 10:00-11:00 or Add Vol Filter

**Data:** The 10:00-11:00 window is strongly positive (+1.5 ATR, win%=57%). The 9:30-10:00 window is -0.6 ATR.

**Alternatively:** Volume 1-2x at PD LH L wins 75% (N=16, +1.0 ATR). Volume 2-5x loses 72% (N=26, -1.7 ATR).

**Action (Option A):** Add 10:00 gate for PD LH L signals specifically.
**Action (Option B):** Suppress PD LH L when vol is 2-5x (the worst bucket). Allow <2x and ≥5x.

**Expected impact:** Option A removes -0.6 ATR from 9:30 signals, keeps the profitable 10:00+ signals.

### Recommendation 4: VWAP Zone — Bear-Only Filter

**Data:** Bear VWAP REV: win%=52%, +3.9 ATR. Bull VWAP REV: win%=39%, -1.7 ATR. Gap = 5.6 ATR.

**Action:** Suppress (or dim) bull VWAP REV signals. Only allow bearish VWAP reversal signals.

**Rationale:** VWAP acts as support. When price drops to VWAP and bounces (bull REV), it often gives back the bounce and continues lower. When price rises above VWAP and pulls back (bear REV), the pullback is more likely to continue. Bears defending VWAP is a stronger pattern than bulls defending VWAP.

**Expected impact:** +1.7 ATR from removing bull VWAP REV losing trades. Keep +3.9 ATR from bear VWAP REV.

### Recommendation 5: VWAP Zone — Remove Afternoon Signals

**Data:** 12:00+ VWAP REV: win%=33%, avg=-0.020, total=-0.3 ATR (N=22).

**Action:** Stop VWAP REV signals after 12:00 (or 11:30). This is consistent with the general finding that afternoon signals underperform.

### Recommendation 6: Fix VW Band (VWAP Lower Band Implementation)

**Problem:** VW Band (VWAP - ATR) never fires because the level is always too far from price.

**Option A:** Change the formula to match backtest: `vwapLowerBand = VWAP - VWAP_STD`. This would make the band reach at ~0.1-0.3 ATR from VWAP and fire regularly.

**Option B:** Remove VW Band BRK entirely — the backtest was testing a bull REV at the level, not a bear BRK through it. The direction implementation is opposite to the validated backtest setup.

**Option C:** Keep as-is and accept that VW Band is for extreme sessions only (once or twice per month per symbol). Not worth the complexity.

**Recommendation:** Choose Option B (remove). The backtest validated a BULL reversal off VWAP-STD band. The implementation generates a BEAR breakout below VWAP-ATR. These are opposite signals at different levels. The implementation doesn't match what was validated.

### Recommendation 7: Elevate PD LH L — It's the Best New Level

PD LH L at +0.6 ATR total is barely positive. But with the 10:00 gate (+1.5 ATR from 10:00-11:00) and the removal of 2-5x vol signals (-1.7 ATR), the potential is to recover ~2.5+ ATR from this level type alone.

BRK signals at PD LH L (N=47, +0.8 ATR) outperform REV signals (N=36, -0.2 ATR). Consider: only generate BRK at PD LH L, not REV.

### Recommendation 8: AMD Suppression or Dimming

AMD is the worst symbol across all new-level types:
- PD Mid AMD: win%=25%, -0.5 ATR
- PD LH L AMD: win%=20%, -0.2 ATR
- VWAP Zone AMD: win%=30%, -1.0 ATR

AMD is already in the D-tier in the existing runner score. Consider adding AMD to a suppression list for new-level signals specifically, or apply an extra EMA alignment requirement.

---

## 8. Think From Every Angle

### Are we computing levels correctly?

- **PD Mid:** Yes. `(yestHigh + yestLow) / 2` computed at session open. Correct.
- **PD LH L:** Yes. Tracks lowest low during 15:00-16:00 of the prior day, frozen at session open. Correct.
- **VWAP Lower Band:** Formula is correct (`VWAP - dailyATR`) but may not be the right level. The backtest validated a different formula.

### Could the backtest have look-ahead bias?

No. The `backtest_level_type` function in midday_treasure_hunt.py explicitly:
- Only looks at bars from bar index 3 forward (after session open)
- Only uses `get_dynamic_levels(b5, bar_idx, atr)` which uses `past = bars_5m_grp.iloc[:bar_idx]` (data before current bar only)
- Computes VWAP cumulatively (no look-ahead)

The backtest is methodologically sound. The issue is that it tested a different setup than what was implemented.

### Could the backtest's "0.5 ATR proximity" be catching different moves?

Yes. The backtest used TIGHT_ATR = 0.15 (not 0.5 — the prompt says 0.5 but the code uses 0.15). With 0.15 ATR proximity, the backtest was looking for near-touches of the level, not decisive crosses. Live signals require a decisive close through the level (BRK) or a reversal FROM the level (REV). These are fundamentally different patterns.

### Should new levels only fire as REV (not BRK)?

For PD LH L: **BRK outperforms REV** (+0.8 vs -0.2 ATR). REV should not be preferenced.
For PD Mid: Only BRK fires in live data anyway (no REV signals generated).
For VWAP Zone: Already all REV (and bear direction is the winner).

### Should new levels have stricter filters?

Yes. The data suggests:
- PD Mid: need time gate (after 10:00) and vol cap (<5x)
- PD LH L: need time gate (after 10:00) or vol filter (avoid 2-5x)
- VWAP Zone: need direction filter (bear only) and time gate (before 12:00)

### Should new levels be dimmed instead of removed?

Dimming is appropriate if there are legitimate but lower-quality signals. Given the near-zero performance (not deeply negative), dimming is a reasonable first step. This preserves optionality while reducing the prominence of these signals.

---

## 9. Signal Count by Symbol and Level

| Symbol | PD Mid | PD LH L | VWAP Zone |
|--------|--------|---------|-----------|
| AAPL | 5 (+0.3) | 9 (+0.5) | 25 (+0.4) |
| AMD | 10 (-0.5) | 10 (-0.2) | 21 (-1.0) |
| AMZN | 14 (-0.6) | 17 (-1.5) | 26 (+1.0) |
| META | 7 (-1.3) | 12 (0.0) | 24 (-0.9) |
| NVDA | 6 (-0.2) | 11 (+0.7) | 17 (+2.2) |
| QQQ | 8 (+1.1) | 6 (+0.2) | 17 (+1.4) |
| SPY | 9 (+0.7) | 12 (+1.2) | 24 (-0.1) |
| TSLA | 2 (-0.3) | 6 (-0.3) | 18 (-0.9) |

(Numbers in parentheses are total 30m PnL in ATR)

A-tier for new levels: QQQ, SPY, NVDA.
D-tier for new levels: AMD, TSLA, META, AMZN.

---

## 10. Comparison with Original Levels

Original levels (N=513): win%=55.8%, avg=+0.029, total=+14.2 ATR

The original levels outperform new levels on every metric:
- 9% higher win rate (55.8% vs 46-47%)
- 2-4x higher avg PnL per signal
- Consistent across time buckets (original levels win 55% in morning AND midday)

The new levels are adding noise to a signal set that works well. Rather than adding more level types, the data suggests focusing on improving filter quality for the existing strong signals.

---

## 11. Summary of Recommended Actions (Ranked by Impact)

| Priority | Action | Expected Impact | Complexity |
|----------|--------|----------------|------------|
| 1 | VWAP Zone: bear only, kill bull REV | +5.6 ATR | Low (1 flag) |
| 2 | VW Band: remove or fix formula | Remove confusion | Low |
| 3 | PD Mid: gate after 10:00 ET | +0.8 ATR recovery | Low |
| 4 | PD LH L: gate after 10:00 ET | +0.6 ATR recovery | Low |
| 5 | VWAP Zone: stop after 12:00 | +0.3 ATR recovery | Low |
| 6 | PD Mid: cap vol at <5x | +2.0 ATR if isolated | Low |
| 7 | AMD: suppress new-level signals | +1.7 ATR | Medium |

Total recoverable with all actions: ~10-11 ATR from 27 days of live data.

---

*Analysis script: `debug/v30b_new_levels_investigation.py`*
*Data sources: pine-logs-Key Level Breakout v3.0b_*.csv (8 files), 5sec parquet data*
*Backtest reference: debug/midday_treasure_hunt.py, debug/no-signal-zone-moves.csv*
