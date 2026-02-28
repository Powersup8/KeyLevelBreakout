# Feb 27, 2026 Signal Analysis: AMZN, GOOGL, SLV

**Analyst:** Claude (automated)
**Date:** 2026-02-28
**Data sources:** Pine logs (KLB v2.2) + BATS 1m candle data, aggregated to 5m

> **Bar alignment note:** Pine Script signals fire at the OPEN of the bar AFTER the signal bar. So a signal timestamped "9:35" was triggered by the 9:30-9:34 bar. All OHLC values in the pine log match the PREVIOUS 5m bar (verified for all signals). FT is calculated from the signal bar's close.

---

## AMZN -- Grade: C+

**Key Levels:**
- ORB H: 207.49
- ORB L: 205.77
- PM H: 208.94
- Yest L: 205.35

**Session OHLC (candle-verified):** Open 206.83 | High 210.33 (15:57) | Low 205.21 (09:43) | Close 209.99 | Range 5.12pt | Net +3.16 (+1.53%)

**Day narrative:** AMZN gapped down and sold off further in the first 15 minutes, testing the ORB low at 205.21. A reversal from ORB L launched a steady recovery, breaking ORB H at 10:20 and grinding toward PM H (208.94). The PM H breakout at 12:10 failed badly with a -1.50 FT at 15m. Price chopped around 208.50-209.50 for hours before a massive 5.5x volume breakout at 15:55 sent AMZN surging to 210.33 into the close.

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT | Notes |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|-------|
| 1 | 9:35 | ▼ | ~ (Rev) | ORB H | 10.8x | v52 | NEUTRAL | +0.26 | +0.30 | +0.17 | First bar reversal at ORB H; FT slightly bearish but small |
| 2 | 9:50 | ▲ | ~ (Rev) | ORB L | 2.2x | ^67 | GOOD | +0.30 | +0.12 | +1.71 | Reversal off ORB L; slow start but excellent 30m FT |
| 3 | 10:20 | ▲ | BRK | ORB H | 1.6x | ^91 | NEUTRAL | +0.67 | +0.02 | +0.81 | Clean breakout but FT was choppy; continued higher eventually |
| 4 | 10:20 | ▲ | ~ (Rev) | Yest L | 1.6x | ^91 | NEUTRAL | +0.67 | +0.02 | +0.81 | Same bar as #3; Yest L far below, not actionable |
| 5 | 10:31 | ▲ | Retest ◆² | ORB H | - | - | NEUTRAL | -0.15 | +0.69 | +0.44 | Weak retest, low vol; mixed FT |
| 6 | 12:10 | ▲ | BRK | PM H | 1.8x | ^59 | BAD | -1.03 | -1.56 | -1.49 | PM H breakout failed immediately; auto-confirmed then failed 1 min later |
| 7 | 12:10 | ▲ | Retest ◆⁰ | PM H | - | - | BAD | -1.03 | -1.56 | -1.49 | Same bar retest, also failed |
| 8 | 15:05 | ▲ | BRK | PM H | 2.2x | ^47 | NEUTRAL | -0.10 | +0.51 | -0.12 | Second PM H attempt; mixed FT, eventually failed confirmation |
| 9 | 15:09 | ▲ | Retest ◆⁰ | PM H | - | - | NEUTRAL | -0.10 | +0.51 | -0.12 | Same window as #8 |
| 10 | 15:40 | ▼ | ~~ (Reclaim) | PM H | 1.8x | v96 | BAD | +0.04 | -1.16 | -1.45 | Bearish reclaim of PM H; immediately reversed by EOD surge |
| 11 | 15:55 | ▲ | BRK | PM H | 5.5x | ^92 | NEUTRAL | +0.23 | +0.29 | +0.32 | Final massive breakout into close; FT limited (EOD) but held |

**Confirmations:** 1/3 (33%)
- 12:10 BRK PM H: auto-confirmed then failed at 12:11 (1 bar hold) -- very fast fail
- 15:05 BRK PM H: failed at 15:38
- Note: the 15:55 breakout had no confirmation logged (probably EOD cutoff)

**Missed signals:**
- 10:15: ORB H (207.49) crossed UP -- this was actually the signal bar for signal #3 (10:20 timestamp = 10:15 bar). Not missed.
- 12:00: PM H (208.94) crossed UP -- first PM H cross; signal fired at 12:10 (12:05 bar). The 12:00 bar crossed PM H but closed at 209.13, which triggered the 12:05 bar signal. **Possible 1-bar delay.**
- 13:45-14:05: Multiple PM H crosses -- price chopped around 208.94 several times. No signals because of cooldown from the failed 12:10 breakout. **Design working as intended** (cooldown preventing whipsaw signals).
- 14:55: PM H crossed UP -- led to signal #8 at 15:05 (15:00 bar). Correctly captured.
- 15:35: PM H crossed DOWN -- this IS signal #10 (15:40 = 15:35 bar). Not missed.
- 15:50: PM H crossed UP -- this IS signal #11 (15:55 = 15:50 bar). Not missed.

**Key findings:**
1. **PM H was a grind level** -- price tested 208.94 repeatedly from 12:00-15:55 before finally breaking through convincingly. The indicator correctly identified most attempts.
2. **Instant confirmation failure at 12:10** is notable -- confirmed then failed in 1 minute. This suggests the auto-promote threshold may be too loose.
3. **Bearish reclaim at 15:40 was counter-trend** -- price was in an uptrend all day; reclaim signals in strong trends are risky.
4. **OHLC verification: PERFECT** -- all 11 signals' OHLC exactly matched our aggregated 5m bars after correcting for the 1-bar offset.

---

## GOOGL -- Grade: C

**Key Levels:**
- ORB H: 307.26
- ORB L: 303.80
- PM H: 308.60
- PM L: 303.79
- Yest L: 302.35

**Session OHLC (candle-verified):** Open 304.19 | High 312.40 (15:57) | Low 303.80 (09:30) | Close 311.55 | Range 8.60pt | Net +7.36 (+2.42%)

**Day narrative:** GOOGL gapped down to the PM low at 303.80, immediately bounced with a massive first-bar reversal (+2.61pt). By 9:45 it broke ORB H and PM H in rapid succession, surging to 309.83. The move was too fast -- PM H breakout at 9:50 reversed hard, giving back 1.5pt within 5 bars. Price then spent 4+ hours chopping between 306-309 (massive 307.26/308.60 range). A late session breakout at 15:55 with 6.5x volume launched GOOGL from 308.22 to 312.40 in 10 minutes.

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT | Notes |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|-------|
| 1 | 9:35 | ▲ | ~ (Rev) | PM L + ORB L | 10.2x | ^87 | GOOD | -0.21 | +2.80 | +1.81 | Dual-level reversal; excellent signal despite choppy 5m |
| 2 | 9:40 | ▼ | ~ (Rev) | ORB H | 5.8x | v49 | NEUTRAL | see note | see note | see note | Bearish reversal at ORB H on a massive up day; counter-trend |
| 3 | 9:45 | ▲ | BRK | ORB H | 4.1x | ^89 | NEUTRAL | +1.56 | +0.05 | -0.05 | Strong initial FT but gains evaporated by 15m |
| 4 | 9:45 | ▲ | ~ (Rev) | Yest L | 4.1x | ^89 | NEUTRAL | +1.56 | +0.05 | -0.05 | Same bar; Yest L at 302.35 was far below current price |
| 5 | 9:50 | ▲ | BRK | PM H | 4.9x | ^89 | BAD | -1.43 | -0.99 | -1.66 | PM H breakout immediately failed; chased the gap-fill move |
| 6 | 9:52 | ▲ | Retest ◆⁰ | PM H | - | - | BAD | -1.43 | -0.99 | -1.66 | Same-bar retest, also failed |
| 7 | 9:55 | ▼ | ~~ (Reclaim) | PM H | 2.4x | v98 | NEUTRAL | +0.08 | +0.09 | -0.50 | Bearish reclaim; small FT then price drifted back up |
| 8 | 10:05 | ▲ | BRK | PM H | 2.2x | ^53 | NEUTRAL | -0.53 | -0.67 | -0.32 | Second PM H attempt; weak close position, failed |
| 9 | 10:05 | ▲ | Retest ◆⁰ | PM H | - | - | NEUTRAL | -0.53 | -0.67 | -0.32 | Same-bar retest |
| 10 | 14:05 | ▲ | BRK | ORB H | 1.7x | ^98 | NEUTRAL | -0.18 | -0.17 | -0.86 | Afternoon ORB H break; great close position but no follow-through |
| 11 | 14:10 | ▼ | ~~ (Reclaim) | PM H | 1.7x | v84 | NEUTRAL | -0.66 | +0.65 | +0.81 | FT mixed: 5m against, 15m/30m positive. Choppy. |
| 12 | 14:21 | ▲ | Retest ◆³ | ORB H | - | - | NEUTRAL | -0.66 | -0.69 | -0.85 | Weak retest, pos=^0 (bearish close), bad FT |
| 13 | 14:45 | ▼ | ~~ (Reclaim) | ORB H | 1.6x | v33 | NEUTRAL | -0.09 | +0.00 | -1.01 | Reclaim of ORB H; pos=v33 is weak; 30m went strongly against |
| 14 | 15:15 | ▲ | BRK | ORB H | 1.6x | ^96 | NEUTRAL | +0.27 | +0.12 | -0.53 | Another ORB H break; great position but couldn't sustain |
| 15 | 15:37 | ▲ | Retest ◆⁴ | ORB H | - | - | GOOD | -0.41 | +0.47 | +3.46 | Retest before the massive EOD move; excellent 30m FT |
| 16 | 15:55 | ▲ | BRK | PM H | 6.5x | ^96 | NEUTRAL | +0.46 | -0.40 | -0.84 | Massive EOD breakout; FT measured into afterhours shows pullback |

**Note on signal #2 FT:** The bar matching found the correct 9:35 bar. FT calculation: 5m bar (9:40) close = 308.04, so bear FT = 306.59 - 308.04 = -1.45 (BAD). 15m bar (9:50) close = 308.17, FT = 306.59 - 308.17 = -1.58 (BAD). 30m bar (10:05) close = 308.08, FT = 306.59 - 308.08 = -1.49 (BAD). **Corrected rating: BAD.**

**Confirmations:** 2/5 (40%)
- 9:50 BRK PM H: auto-confirmed, then failed at 9:54 (2-bar hold)
- 10:05 BRK PM H: failed at 10:09
- 14:05 BRK ORB H: failed at 14:40
- 15:15 BRK ORB H: no fail logged (likely passed or EOD)
- 15:55 BRK PM H: auto-confirmed (held into close)

**Missed signals:**
- 10:00-11:35: PM H (308.60) crossed UP/DOWN approximately 12 times. Only 2 signals generated (10:05 BRK + retest). **Massive chop zone with cooldown suppression working correctly** -- generating signals for every cross would have been worse.
- 12:05: PM H crossed UP (bar high 309.36, close 309.09). No signal generated. This may have been suppressed by cooldown from the 10:05 breakout failure.
- 12:40: ORB H (307.26) crossed DOWN (close 307.13). No signal generated. Could be a missed reclaim.
- 14:00: ORB H crossed UP -- this is signal #10's bar (14:05 = 14:00 bar). Not missed.
- 15:10: ORB H crossed UP -- this is signal #14's bar (15:15 = 15:10 bar). Not missed.
- 15:50: PM H crossed UP -- this is signal #16's bar (15:55 = 15:50 bar). Not missed.

**Key findings:**
1. **PM H was a brutal chop level** -- GOOGL crossed 308.60 approximately 15 times during the session. The indicator wisely suppressed most signals via cooldown.
2. **Early momentum trap at 9:50** -- the PM H breakout fired with 4.9x volume and ^89 position but immediately reversed. This was a gap-fill momentum exhaustion.
3. **The massive EOD move (+3pt in 5 min)** was correctly captured by both the ORB H retest (#15) and PM H breakout (#16).
4. **Signal #2 (9:40 bearish reversal at ORB H) was a terrible signal** on a +2.4% up day -- counter-trend reversals in gap recovery are risky.
5. **Yest L reversal at 9:45** (signal #4) -- Yest L was at 302.35 but price was at 308 when the signal fired. This level was not relevant to the current price action.

---

## SLV -- Grade: B+

**Key Levels:**
- ORB H: 83.28
- ORB L: 82.58
- PM H: 83.99

**Session OHLC (candle-verified):** Open 83.25 | High 85.27 (11:18) | Low 82.36 (09:41) | Close 84.98 | Range 2.91pt | Net +1.73 (+2.07%)

**Day narrative:** SLV opened near PM H, immediately sold off to test ORB L area (82.36 low at 9:41). A strong reversal from ORB L led to a steady uptrend -- breaking ORB H at 10:10 and PM H at 10:45. SLV hit the day high of 85.27 at 11:18, then pulled back sharply to 83.64 in a midday selloff. After the PM H reclaim, price rebuilt slowly and closed near 84.98. Clean trend day with one sharp pullback.

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT | Notes |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|-------|
| 1 | 9:35 | ▼ | ~ (Rev) | ORB H | 4.7x | v87 | BAD | +0.01 | -0.29 | -0.54 | Bearish reversal on ORB H; price immediately bounced. Counter-trend. |
| 2 | 9:45 | ▲ | ~ (Rev) | ORB L | 2.7x | ^82 | GOOD | +0.19 | +0.24 | +0.88 | Clean reversal from ORB L; great FT at 30m. Key signal of the day. |
| 3 | 10:10 | ▲ | BRK | ORB H | 3.1x | ^55 | GOOD | +0.24 | +0.04 | +0.72 | ORB H breakout with 3.1x volume; 30m FT strong |
| 4 | 10:10 | ▲ | Retest ◆⁰ | ORB H | - | - | GOOD | +0.24 | +0.04 | +0.72 | Same-bar auto-retest confirmed the breakout |
| 5 | 10:45 | ▲ | BRK | PM H | 1.6x | ^52 | GOOD | +0.39 | +0.56 | +0.79 | PM H breakout; confirmed and held for 2.5 hours. Best signal. |
| 6 | 13:25 | ▼ | ~~ (Reclaim) | PM H | 2.0x | v85 | BAD | -0.35 | -0.15 | -0.57 | Bearish PM H reclaim; price recovered above PM H by 13:40. Failed. |

**Confirmations:** 1/2 (50%)
- 10:45 BRK PM H: auto-confirmed, held until 13:24 (2h 39m hold) -- strong confirmation
- 13:24: PM H BRK confirmation failed

**Missed signals:**
- 10:05: ORB H (83.28) crossed UP (bar close 83.41). This is signal #3's bar (10:10 = 10:05 bar). Not missed.
- 10:35: PM H (83.99) crossed UP (bar close 84.13). This is close to signal #5's bar but 2 bars earlier. The 10:35 bar had O=83.76, H=84.14, L=83.72, C=84.13. The signal fired at 10:45 (10:40 bar). **Possible 1-bar delay** -- the 10:35 bar crossed PM H but the signal triggered on the 10:40 bar.
- 13:20: PM H crossed DOWN (bar high 84.55, close 83.77). This is signal #6's bar (13:25 = 13:20 bar). Not missed.
- 13:30: PM H (83.99) crossed DOWN again (close 83.97 -- barely below). No signal (cooldown from #6). Correct.
- 13:40: PM H crossed UP (close 84.22). No breakout signal generated. **Potential miss** -- after the reclaim at 13:25, price recovered above PM H at 13:40 but no re-breakout signal was generated. This could be by design (cooldown) or a gap in coverage.

**Key findings:**
1. **Clean trend day** -- SLV had the most tradeable signals of the three symbols. 4 of 6 signals were GOOD.
2. **The PM H breakout at 10:45 was excellent** -- held confirmation for 2h 39m before failing, giving plenty of time to manage the trade.
3. **Counter-trend signals struggled** -- both BAD signals (#1 and #6) were against the prevailing trend.
4. **Possible 1-bar delay on PM H breakout** -- the 10:35 bar crossed PM H but the signal fired from the 10:40 bar. This may be due to the buffer zone (buf=0.294) requiring price to close above 83.99 + 0.294 = 84.28, which the 10:35 bar (C=84.13) didn't achieve. The 10:40 bar (C=84.19) also didn't reach 84.28, so the breakout threshold may use a different formula. Worth investigating.

---

## Cross-Symbol Summary

| Symbol | Grade | Signals | GOOD | BAD | NEUTRAL | Confirm Rate | Day Move |
|--------|-------|---------|------|-----|---------|-------------|----------|
| AMZN | C+ | 11 | 1 | 3 | 7 | 1/3 (33%) | +1.53% |
| GOOGL | C | 16 | 2 | 3* | 11 | 2/5 (40%) | +2.42% |
| SLV | B+ | 6 | 4 | 2 | 0 | 1/2 (50%) | +2.07% |

*GOOGL signal #2 corrected from NEUTRAL to BAD (bar matching issue in initial pass resolved).

**GOOGL corrected totals:** GOOD=2, BAD=3, NEUTRAL=11

### Key Patterns Across All Three Symbols

1. **End-of-day breakouts were consistent** -- All three symbols had massive volume breakouts in the final 5-10 minutes (15:55 AMZN 5.5x, 15:55 GOOGL 6.5x, N/A SLV). These were the strongest moves of the day.

2. **PM H was the key battle level** -- AMZN tested PM H 5+ times, GOOGL tested it ~15 times, SLV tested it 3 times. The level created the most signal noise.

3. **Counter-trend reversals were consistently BAD** -- Bearish reversals on bullish trend days (SLV #1, GOOGL #2) and bearish reclaims that fought the trend (AMZN #10, SLV #6) all had negative outcomes.

4. **Early session reversals from ORB extremes were GOOD** -- AMZN #2 (ORB L reversal), GOOGL #1 (PM L + ORB L reversal), SLV #2 (ORB L reversal) all produced meaningful follow-through.

5. **Auto-confirmation was unreliable** -- AMZN's 12:10 confirmation lasted only 1 minute. GOOGL's 9:50 confirmation lasted 2 bars. Only SLV's 10:45 confirmation held meaningfully.

### Design Issues / Bugs

1. **OHLC bar alignment is correct** -- All signal OHLC values perfectly match the previous 5m bar (one bar before the signal timestamp). This confirms the indicator is working as designed.

2. **Yest L signals far from price** -- GOOGL signal #4 flagged Yest L at 302.35 when price was at 308. While technically a reversal from being below this level, the practical value is zero for a signal 6pt above the level.

3. **Same-bar retests (◆⁰) are redundant** -- When a breakout and retest fire on the same bar (AMZN #6/#7, GOOGL #5/#6, #8/#9, SLV #3/#4), they produce identical FT and add noise without value.

4. **Counter-trend reclaims in strong trends** -- The indicator doesn't distinguish trend context. A bearish reclaim of PM H at 15:40 on AMZN (a +1.5% day) was almost guaranteed to fail. A simple trend filter (e.g., price > VWAP or > session open) could suppress these.

5. **Confirmation auto-promote then immediate fail** -- AMZN's 12:10 breakout was auto-confirmed and then failed 1 minute later. This suggests the auto-promote criteria may need tightening, or the confirmation window needs a minimum hold time.
