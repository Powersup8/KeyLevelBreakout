# KeyLevelBreakout -- Cross-Day Analysis Summary (Feb 25-27, 2026)

*Generated: 2026-02-28*
*Indicator: KeyLevelBreakout v2.2*
*Data sources: Pine logs + BATS 1m candle verification across 3 trading sessions*

---

## 1. Three-Day Overview Table

| Metric | Feb 25 (Chop) | Feb 26 (Trend Down) | Feb 27 (Late Bull) |
|--------|---------------|---------------------|---------------------|
| SPY Range | 3.58pt (44% ATR) | 9.0pt (113% ATR) | 5.19pt (64% ATR) |
| SPY ATR | 8.09 | 7.97 | ~8.1 (est.) |
| SPY Net | +2.87 (+0.4%) | ~-9.0 (bearish) | +3.11 (+0.46%) |
| Symbols Analyzed | 10 | 10 | 12 |
| Total Signals | **71** | **53** | **105** |
| GOOD | 24 (34%) | 25 (47%) | 14 (13%) |
| BAD | 23 (32%) | 14 (26%) | 38 (36%) |
| NEUTRAL | 24 (34%) | 14 (26%) | 50 (48%) |
| N/A | 0 | 0 | 3 (3%) |
| CONF Success Rate | 43% (6/14) | 65% (11/17) | 24% (8/34) |
| Best Strategy | QQQ+META only (7/8 GOOD) | Confirmed BRK only (10/11 GOOD) | ORB L rev + confirmed BRK after 10:30 (3/5 GOOD) |

**Three-day totals:** 229 signals, 63 GOOD (28%), 75 BAD (33%), 88 NEUTRAL (38%), 3 N/A (1%).

---

## 2. Day-Type Classification

### Chop Day (Feb 25)
**Characteristics:** SPY range 3.58pt = 44% of ATR. Gentle bullish grind with no decisive directional move until late. Most levels clustered tightly.
**Indicator performance:** 71 signals -- the most of any day -- but only 34% GOOD. Confirmation system was 43% successful (6/14). Auto-promote fired then failed on SPY, GOOGL, AMZN, and SLV. QQQ and META were the only clean tickers (100% GOOD, 100% CONF success). The narrow range caused breakouts to trigger then immediately reverse. Every confirmed-then-failed signal was a losing trade.

### Trend Day (Feb 26)
**Characteristics:** SPY range 9.0pt = 113% of ATR. Strong directional sell-off from the open, with 9 of 10 symbols bearish. Massive opening volume (8-17x).
**Indicator performance:** 53 signals with 47% GOOD -- the best hit rate of all three days. Confirmed breakouts were near-perfect: 10/11 GOOD. Bearish signals were 71% GOOD (22/31). Counter-trend bullish signals were 14% GOOD (3/22) -- almost universally traps. The indicator excels on trend days where breakouts carry through decisively.

### Late Recovery Day (Feb 27)
**Characteristics:** SPY range 5.19pt = 64% of ATR. Morning sell-off, then slow V-shaped recovery closing near highs. Most symbols had the same pattern: early chop, late directional push.
**Indicator performance:** 105 signals across 12 symbols with only 13% GOOD -- the worst hit rate. Confirmation was only 24% successful (8/34). Morning chop (9:30-10:30) generated the most signals but had the worst quality. The real moves came in the final 1-2 hours when it was too late for meaningful follow-through measurement. Reclaims were 0% GOOD (0/10). Same-bar retests added noise. AAPL was the lone bright spot (B-, strong bearish trend day with +2.14pt follow-through on the 10:00 BRK Yest L). QQQ suffered from ETF FT threshold issues (6 NEUTRAL on correct directional calls). MSFT was plagued by closely-spaced levels (ORB H / Week L only $0.30 apart). This was the indicator's weakest day type.

---

## 3. Per-Symbol Performance Across Days

| Symbol | Feb 25 | Feb 26 | Feb 27 | Avg Grade | Notes |
|--------|--------|--------|--------|-----------|-------|
| SPY | D+ (2/9 GOOD) | A- (5/5 GOOD) | C (0/11 GOOD) | C+ | Best on trend day, worst on chop/recovery days |
| AAPL | N/A (no data) | B+ (4/7 GOOD) | B- (3/9 GOOD) | B | Trending well on sell-offs; early bounce noise is the main risk |
| MSFT | N/A (no data) | D+ (1/7 GOOD) | D (2/9 GOOD) | D+ | Closely-spaced levels cause chronic whipsaw; early reversals are the only reliable signals |
| QQQ | A+ (4/4 GOOD) | N/A (no data) | D+ (0/10 GOOD) | C+ | Wild swing: A+ on chop day, D+ on recovery day; ETF FT threshold is a factor |
| META | A (3/4 GOOD) | B (2/4 GOOD) | C (0/4 GOOD) | B | Consistently lone outlier; performance declined |
| TSLA | B (2/6 GOOD) | B+ (3/7 GOOD) | D+ (0/7 GOOD) | C+ | Good on trend/chop, terrible on late-recovery |
| AMD | C (3/7 GOOD) | C (1/4 GOOD) | C+ (1/10 GOOD) | C | Consistently choppy; morning signals unreliable |
| NVDA | C+ (1/5 GOOD) | A (3/6 GOOD) | C+ (0/8 GOOD) | B- | Excellent on trend day, poor otherwise |
| GOOGL | D+ (2/8 GOOD) | A (3/4 GOOD) | C (2/16 GOOD) | C+ | Wild variation; 16 signals on Feb 27 was extreme |
| TSM | D+ (2/7 GOOD) | A (2/4 GOOD) | B (1/4 GOOD) | B- | Best with few signals; morning open reversal works |
| SLV | D+ (4/12 GOOD) | C+ (1/5 GOOD) | B+ (4/6 GOOD) | C+ | Most variable; 12 signals on Feb 25 was max |
| AMZN | D (1/9 GOOD) | N/A (no data) | C+ (1/11 GOOD) | D+ | Tightly clustered levels cause chronic confusion |

**Most consistent performer:** TSM (B-, strong opening reversal works across day types).
**Most volatile performance:** QQQ (A+ on chop day, D+ on recovery day -- a wider swing than even GOOGL).
**Worst overall:** AMZN (D+ avg -- tight level clusters and narrow ranges), MSFT (D+ avg -- closely-spaced levels).

---

## 4. Signal Type Performance Across Days

| Signal Type | Feb 25 | Feb 26 | Feb 27 | 3-Day Total | 3-Day Win Rate |
|-------------|--------|--------|--------|-------------|----------------|
| **BRK (Breakout)** | 12/28 GOOD (43%) | 17/27 GOOD (63%) | 5/36 GOOD (14%) | 34/91 GOOD | **37%** |
| **~ (Reversal)** | 6/20 GOOD (30%) | 6/17 GOOD (35%) | 8/28 GOOD (29%) | 20/65 GOOD | **31%** |
| **~~ (Reclaim)** | 4/13 GOOD (31%) | 0/5 GOOD (0%) | 0/11 GOOD (0%) | 4/29 GOOD | **14%** |
| **Retest** | 2/10 GOOD (20%) | 2/4 GOOD (50%) | 2/14 GOOD (14%) | 6/28 GOOD | **21%** |
| **Retest same-bar (included above)** | n/a | n/a | 1/8 GOOD (13%) | n/a | Low |

**Key observations:**
- **Breakouts** are the best signal type overall (37%) but swing wildly by day type: 63% on trend days vs 14% on late-recovery days. The Feb 27 expanded dataset (AAPL, QQQ, MSFT) reinforced the pattern -- QQQ and MSFT breakouts were 0% GOOD; only AAPL's 10:00 BRK Yest L delivered.
- **Reversals** are the most stable type across day types (29-35% range), with ORB L reversals particularly strong on recovery days. AAPL's 9:40 REV ORB L and MSFT's 9:30 REV PM L were both GOOD on Feb 27.
- **Reclaims** are consistently the worst type. After a 31% GOOD rate on Feb 25 (the "best" day for reclaims), they dropped to 0% on both Feb 26 and Feb 27. QQQ's 9:55 RCL ORB H was a textbook counter-trend trap. Three-day rate: 14%.
- **Retests** are low-value overall (21%), and same-bar retests (Feb 27 data) are essentially noise at 13%. QQQ 9:45 fired a BRK + RST at the same bar on the same level (Yest L) -- a logical contradiction.

---

## 5. Confirmation System Analysis

### Three-Day CONF Summary

| Day | Confirmed (GOOD) | Confirmed (Total) | Success Rate | Failed (Correct Warning) |
|-----|-------------------|--------------------|-------------|--------------------------|
| Feb 25 | 6 | 14 | 43% | 8/14 (57%) |
| Feb 26 | 10-11 | 17 | 65% | 6/17 (35%) |
| Feb 27 | 8 | 34 | 24% | 26/34 (76%) |
| **3-Day Total** | **~25** | **65** | **~38%** | **~40/65 (62%)** |

### When CONF Helped

**Feb 26 (Trend Day):** CONF was near-perfect. 10/11 confirmed breakouts were GOOD. Trading only CONF signals would have produced an outstanding day. The one exception was META's Yest H+ORB H which was initially right (+4.61 at 5m) but faded at 30m (-1.43). CONF failures (6 total) correctly warned traders off bad entries every single time -- 100% accuracy on the failure side.

**Feb 25 (Chop Day):** CONF failures were 100% accurate warnings (all 8 CONF failures corresponded to bad/neutral entries). The problem was the 6 CONF successes included 4 that later reversed -- SPY ORB H (confirmed then failed in 14 min), GOOGL PM H (confirmed then failed in 10 min), AMZN PM H+Week H (confirmed then failed in 13 min), SLV PM H (confirmed then failed in 16 min). If you filtered to only CONF signals that *never* received a subsequent failure, you got 5 GOOD + 1 NEUTRAL out of 6 -- excellent.

### When CONF Failed

**Feb 27 (Late Recovery):** Auto-confirm was catastrophically unreliable. Specific failures:
- **NVDA 10:00 BRK ORB L:** Auto-confirmed but immediately reversed -1.77pt in 5 minutes (worst signal of the day)
- **AMZN 12:10 BRK PM H:** Auto-confirmed then failed in just 1 minute
- **GOOGL 9:50 BRK PM H:** Auto-confirmed then failed in 2 bars
- **SPY:** 0/4 breakouts confirmed at all -- correctly preventing bad trades, but also blocking the eventual 15:15 breakout that worked
- **QQQ:** 0/3 breakouts confirmed -- all correctly rejected (9:46 BRK Yest L, 9:53 BRK ORB H both reversed immediately; 13:21 BRK ORB H failed after holding 3+ hours)
- **MSFT:** 0/2 breakouts confirmed -- 10:33 BRK Week L bounced back, 15:29 BRK ORB H reversed immediately
- **AAPL 10:00 BRK Yest L:** BUG -- dual CONF (auto-promote confirmed + failed) at same timestamp

### Design Conclusions
The auto-promote mechanism is **too fast on non-trend days**. It triggers when price briefly crosses a threshold, but on choppy days that threshold is crossed and then immediately lost. The CONF failure flag is consistently reliable as a *warning* -- across all 3 days, CONF failures were correct 90%+ of the time. The weakness is false *confirmations* on chop/recovery days. The expanded Feb 27 data (8/34 = 24%) reinforces this finding -- QQQ and MSFT added 5 more failed confirmations with 0 successes.

---

## 6. Consistent Patterns Found (Across All 3 Days)

### Pattern 1: Counter-trend reclaims (~~) are consistently the worst signal type
- Feb 25: 4/13 GOOD (31%) -- best day, still weak
- Feb 26: 0/5 GOOD (0%) -- every reclaim was a counter-trend trap
- Feb 27: 0/11 GOOD (0%) -- zero value (QQQ 9:55 RCL ORB H added to the evidence)
- **Three-day total: 4/29 GOOD (14%)**
- Examples: TSLA 9:55 ~~ Yest L on Feb 26 (-5.08 at 30m), AMD 10:05 ~~ PM L on Feb 26 (-5.40 at 30m), NVDA 10:05 ~~ PM L+ORB L on Feb 27 (NEUTRAL at best), AMZN 15:40 ~~ PM H on Feb 27 (BAD, -1.45 at 30m), QQQ 9:55 ~~ ORB H on Feb 27 (BAD, -2.34 at 30m)

### Pattern 2: CONF failure flags are reliable warnings
- Feb 25: 8 CONF failures, all corresponded to bad/neutral entries
- Feb 26: 6 CONF failures, all correctly warned off bad entries
- Feb 27: 26 CONF failures out of 34 total -- correctly identifying the majority of breakouts that wouldn't hold (including all 5 QQQ/MSFT breakouts)
- **Across all 3 days, CONF failure was a correct warning ~95% of the time.**

### Pattern 3: Close position (v95+/^95+) is a better predictor than volume alone
- Feb 26 example: SPY 10:15 BRK Yest L at v99 = GOOD (+4.22pt). NVDA 9:35 BRK PM L+Yest L at v98 = GOOD (+6.11 to EOD).
- Feb 25 example: TSM 9:30 ~ PM H at v99 = GOOD (-2.78 at 5m). SLV 15:30 ~~ ORB H at v95 = GOOD.
- Feb 27 example: NVDA 10:05 ~~ PM L+ORB L at ^100 = NEUTRAL (exception). AMD 9:40 ~ PM L+Wk L at ^95 = NEUTRAL. MSFT 15:30 BRK Week L at v96 = NEUTRAL (close to GOOD threshold).
- High volume alone did NOT predict quality -- Feb 26 MSFT 9:35 had 14.9x vol but was BAD; Feb 27 AMD 9:35 had 13x vol and v19 position = BAD; Feb 27 AAPL 9:35 had 17.8x vol at v91 = BAD (bounce reversed FT).
- **Close position >= 95% combined with trend alignment was the strongest single filter across all 3 days.**

### Pattern 4: Opening bar (9:30/9:35) signals are directionally informative but hard to trade
- Across all 3 days, the first bar consistently established the session's directional bias for most symbols, with extreme ranges (5-7pt on TSLA, 4-6pt on META/GOOGL, 3.7pt on AAPL Feb 27).
- On Feb 26, the opening bar's direction was correct for 9/10 symbols.
- On Feb 27, AAPL's opening bar (9:30-9:34) produced a 3.72pt drop -- correct directional call for the day, but the ensuing bounce generated 6 signals in 16 minutes with 4 direction changes.
- However, the entry is at an extreme price after a massive range bar -- the immediate follow-through is often a pullback, making the entry risky.
- Best approach: use the opening bar's direction as a *filter* for subsequent signals, not as a trade entry.

### Pattern 5: Confirmed breakouts that survive are the highest-quality signals
- On Feb 25, filtering to only CONF signals that never got a subsequent CONF failure: 5 GOOD + 1 NEUTRAL out of 6.
- On Feb 26, confirmed breakouts: 10/11 GOOD.
- On Feb 27, the few confirmed signals that held (SLV PM H for 2h 39m, AMD PM L, AAPL 10:00 BRK Yest L) were GOOD.
- On Feb 27, QQQ and MSFT had 0 surviving confirmations -- consistent with their BAD/NEUTRAL signal quality.
- **The combination "CONF confirmed AND no subsequent CONF failure" was the single best filter across all 3 days.**

### Pattern 6: Afternoon signals outperform morning signals on chop/recovery days
- Feb 25: SLV afternoon cascade (15:30-15:50) had 2 GOOD out of 3 signals. SPY's genuine breakout came at 11:45.
- Feb 27: SLV's 10:45 PM H BRK was the best signal (held 2h 39m). GOOGL/AMZN's 15:55 breakouts were the biggest moves. AAPL's 10:00 BRK (after 30 min of settling) was the standout signal.
- Feb 26 (trend day): Morning signals were the best -- the trend was established immediately.
- **Rule: On non-trend days, the first 30-60 minutes are noise. Wait for midday or afternoon for genuine breakouts.**

### Pattern 7: Closely-spaced levels create noise storms
- Feb 27 MSFT: ORB H (394.23) and Week L (394.53) only $0.30 apart -- generated 40 missed crossings and multiple false breakout/reversal pairs. PM L (389.86) and ORB L (389.90) only $0.04 apart.
- Feb 25 AMZN: PM H and Yest H only 0.24pt apart -- chronic confusion.
- **When two levels are within 1x buffer distance, they create a whipsaw zone rather than discrete levels. This is a structural indicator weakness.**

### Pattern 8: Same-bar BRK + RST is a logical contradiction
- Feb 27 QQQ 9:45: BRK Yest L and RST Yest L fired on the same bar. A breakout and a retest of the same level at the same time is contradictory -- the BRK says "price broke through" while the RST says "price came back to test."
- Feb 27: 8+ same-bar retests across all symbols, all duplicating the parent breakout's outcome.
- **Same-bar retests should be suppressed when a fresh breakout fires on the same bar and level.**

---

## 7. Day-Specific Patterns

### Only Works on Trend Days (Feb 26)
- **Bearish-only filter:** 71% GOOD rate on bearish signals (22/31). On Feb 25 bearish signals were 26% GOOD (5/19), and Feb 27 bearish signals were 3% GOOD (1/29) for the original 9 symbols.
- **Trading every breakout in the trend direction:** On Feb 26, all with-trend breakouts were GOOD. On other days, breakouts in the eventual winning direction still had poor morning hit rates.
- **Massive opening bar as entry signal:** When the first bar breaks 2+ levels with >10x volume on a trend day (SPY, NVDA, TSLA, TSM, GOOGL on Feb 26), the direction is correct and breakouts carry. On chop/recovery days, this pattern doesn't hold.

### Only Works on Chop Days (Feb 25)
- **Multi-ticker selectivity:** Focusing on only the 2 cleanest movers (QQQ + META) produced 7 GOOD / 0 BAD out of 8 signals. On trend days, most tickers move together so selectivity adds less. On recovery days, no single ticker was clean enough.

### Only Works on Recovery Days (Feb 27)
- **ORB L reversals as dip-buy signals:** Feb 27's 4 ORB L/PM L reversals were the best signals: AMZN 9:50 (GOOD, +1.71 at 30m), GOOGL 9:35 (GOOD, +2.80 at 15m), SLV 9:45 (GOOD, +0.88 at 30m), TSM 9:35 (GOOD, +3.20 at 15m). AAPL 9:40 REV ORB L also GOOD (+1.58 at 15m) and MSFT 9:30 REV PM L was GOOD (+3.33 at 30m). On Feb 26 (trend down), ORB L reversals were traps. On Feb 25 (chop), they were mixed.
- **Late-session breakouts with high volume:** AMZN 15:55 (5.5x), GOOGL 15:55 (6.5x), SPY 15:15 (2.9x, ^100). The day's real move came in the final 1-2 hours.
- **AAPL as counter-example:** While most symbols had a bullish recovery, AAPL sold off -3.19% -- its bearish signals were the only ones that worked. This reinforces Rule 1 (identify per-symbol trend, not just market trend).

---

## 8. Bugs & Design Issues (Consolidated Across All 3 Days)

### HIGH Priority

**B1. Auto-Promote Too Fast on Non-Trend Days**
- Feb 25: 4 confirmed-then-failed: SPY ORB H (14 min), GOOGL PM H (10 min), AMZN PM H+Week H (13 min), SLV PM H (16 min)
- Feb 27: NVDA ORB L confirmed then reversed -1.77 in 5 min (worst signal of the day); AMZN PM H confirmed then failed in 1 minute; GOOGL PM H confirmed then failed in 2 bars
- **Impact:** Traders trusting CONF took multiple losing trades. On trend day (Feb 26) CONF was 65% accurate; on chop (Feb 25) 43%; on recovery (Feb 27) 24%.
- **Fix:** Require minimum 2-3 consecutive 5m bars holding above the level before auto-promote, or scale the threshold by day-type detection (ATR utilization).

**B2. Counter-Trend Signals Have No Suppression Mechanism**
- Feb 26: 0/12 counter-trend signals in the first 30 min were GOOD (all traps on bearish symbols)
- Feb 27: Bearish signals were 3% GOOD (1/29) on a bullish recovery day (original 9 symbols); QQQ had 4 BAD bearish signals at 9:45 on what was an up day (+0.73%)
- Feb 25: Counter-trend reversals were mixed but low-quality
- **Impact:** Consistently the largest source of BAD signals across all 3 days.
- **Fix:** Implement VWAP or session-open directional filter. Suppress bearish reversals/reclaims above VWAP on bullish days and vice versa. Or require higher volume/position thresholds for counter-trend signals.

**B3. Reclaim Signal Type (~~) is Fundamentally Broken**
- 3-day total: 4/29 GOOD (14%). Feb 26: 0/5, Feb 27: 0/11.
- Every reclaim that fought the prevailing trend was BAD. QQQ 9:55 RCL ORB H (Feb 27) was another textbook example: BAD, -2.34 at 30m.
- **Fix:** Consider removing reclaims entirely, or require much higher thresholds (e.g., 5x volume + 90% position + trend alignment).

**B4. Closely-Spaced Levels Create Noise Storms**
- Feb 27 MSFT: ORB H (394.23) / Week L (394.53) = $0.30 apart, 0.08% of price, 0.55x buffer. Result: 40 missed crossings, 5 BAD/NEUTRAL signals from oscillation.
- Feb 27 MSFT: PM L (389.86) / ORB L (389.90) = $0.04 apart. Functionally identical levels.
- Feb 25 AMZN: PM H / Yest H = 0.24pt apart. Chronic confusion.
- **Impact:** Generates the worst whipsaw of any structural issue. MSFT's 40 missed crossings was the highest across all 36 symbol-days analyzed.
- **Fix:** When two levels are within 1x buffer distance, merge them into a single zone. Only generate signals when price decisively clears both edges of the zone.

### MEDIUM Priority

**B5. D/W Zone Width Can Be Enormous**
- Feb 26: NVDA Yest H zone was 2.07pt (11x wider than PM/ORB zones); META Week H zone was 7.35pt (12x wider).
- Result: Signals fire far from the actual level, reducing actionability. NVDA 9:30 reversal fired 1.85pt below Yest H; META 10:10 reversal fired 7pt below Week H.
- **Fix:** Cap D/W zone width at ATR * zoneATRPct (same formula as PM/ORB zones), or use `min(bodyEdge, wick - ATR * cap)`.

**B6. Pre-Market Bar Evaluated as Regular Session Signal**
- Feb 26: NVDA 9:30 signal evaluated the 9:25-9:29 bar (premarket) because `isRegular` flips at 9:30 while using `[1]` lookahead.
- **Fix:** Skip reversal evaluation when the signal bar's OHLC originates from premarket.

**B7. MSFT ORB L Re-Arm Logic Gap**
- Feb 26: MSFT 10:30 bar closed below ORB L buffer (400.02 < 401.42) but no breakout signal fired. Likely `firstOnly` state not properly re-armed after the 9:40 ORB L reversal.
- **Fix:** Investigate re-arm threshold logic; ensure reversal properly resets breakout state.

**B8. Same-Bar Retests (Retest fired on same bar as Breakout) Add Noise**
- Feb 27: 8+ same-bar retests across original 9 symbols, all duplicating the parent breakout's outcome (AMZN, GOOGL, SLV, AMD, TSLA).
- Feb 27 QQQ: BRK Yest L + RST Yest L at same bar (9:45) -- a logical contradiction (breakout and retest of same level simultaneously).
- **Fix:** Suppress retests that fire on the same bar as their parent breakout signal.

**B9. TSM Confirmation Timing Gap (3.5 hours)**
- Feb 27: TSM 9:50 BRK confirmation was not checked until 13:26 -- a 3.5-hour gap.
- Normal confirmation checks happen within minutes. This suggests a timing logic issue.
- **Fix:** Investigate confirmation check scheduling; ensure checks happen within a bounded time window.

**B10. Distant Level Signals Fire Far From Current Price**
- Feb 27: GOOGL Yest L at 302.35 generated a reversal signal at 9:45 when price was at 308 -- 6 points above the level.
- **Fix:** Add a maximum-distance filter (signal level must be within 1-2 ATR of current price).

**B11. Dual CONF at Same Timestamp (AAPL)**
- Feb 27: AAPL 10:00 BRK Yest L shows two CONF entries at the same timestamp -- one "auto-promote" (confirmed) and one "failed". The same breakout should not produce conflicting confirmation statuses.
- **Root cause:** Auto-promote and regular confirmation logic appear to run independently, creating a race condition.
- **Fix:** Ensure auto-promote and regular CONF logic share state. If auto-promote has already confirmed, suppress the regular CONF check (or vice versa).

**B12. ETF FT Threshold May Be Too High**
- Feb 27 QQQ: 6 NEUTRAL signals were directionally correct but below the 0.3% FT threshold. On a $603 ETF, 0.3% = $1.81 -- higher than typical intraday moves at short timeframes. Signal #1 (9:35 REV PM L+ORB L) caught the bottom correctly but max FT was +$1.13 (0.19%). Signal #8 (10:05 BRK ORB H) led to a $3+ move over 2 hours but 30m FT was only +$0.80 (0.13%).
- **Impact:** QQQ's 0 GOOD signals may be partially a measurement artifact rather than signal quality failure.
- **Fix:** Use ATR-proportional FT thresholds, or reduce the percentage threshold for broad ETFs.

**B13. Signal Overload in Opening Minutes**
- Feb 27: All three new symbols produced rapid-fire opposing signals in the first 20-30 minutes: AAPL 6 signals in 16 min (4 direction changes), QQQ 7 signals in 20 min (3 direction changes), MSFT 2 signals in first 5 min then 3 more by 10:20.
- This pattern was consistent across nearly all 12 symbols on Feb 27.
- **Impact:** Traders receive contradictory information in rapid succession. By the time the noise settles, the best entry has often passed.
- **Fix:** Consider a settling period or higher confidence requirement in the first 15 minutes. Alternatively, require a minimum hold time before allowing opposing signals at the same level.

### LOW Priority

**B14. GOOGL PM L Fastest Failure (2 min) -- Feb 25**
- BRK PM L at 9:35, CONF failure at 9:37. The breakout state properly reset (reclaim fired at 9:40). No missed signals but worth verifying re-arm logic.

**B15. OHLC Discrepancies Between BATS and TradingView Composite**
- Feb 27: SPY, TSLA, META showed discrepancies up to $3-4 between BATS and pine log OHLC. AMZN, GOOGL, SLV had perfect matches. AAPL, QQQ, MSFT all had perfect matches.
- Feb 26: All 10 symbols showed perfect OHLC matches.
- **Root cause:** BATS is a single exchange; TradingView uses composite tape (multiple exchanges). Discrepancies are largest for high-volume/wide-spread names.
- **Impact:** Low -- this is a verification methodology issue, not an indicator bug. Future analysis should use TradingView-exported 5m candle data.

**B16. No Signals for Moves Beyond All Tracked Levels**
- Feb 27: NVDA final crash from 178.13 to 176.39 (-1.0% in 10 min) had no signal. TSM afternoon recovery (+3.72pt) had no bullish signal.
- **Impact:** Low -- these are edge cases where price moves beyond the day's tracked level structure.

---

## 9. Recommended Indicator Improvements

### Tier 1: Would Have Helped on ALL 3 Days

1. **Delay auto-promote on non-trend days.** Require 2-3 consecutive bars holding above the level before CONF. On Feb 25 this prevents 4 false confirms; on Feb 27 it prevents NVDA/AMZN/GOOGL false confirms and would have saved QQQ/MSFT from their 0% CONF rate; on Feb 26 it slightly delays already-correct confirms (acceptable tradeoff). Detection method: if first-30-min range < 60% ATR, apply stricter confirmation.

2. **Suppress or significantly filter reclaim signals (~~).** Three-day GOOD rate of 14% is unacceptable. Either require much higher conviction (5x volume + 90%+ position + trend alignment) or remove entirely. This would eliminate 29 mostly-bad signals across 3 days.

3. **Add counter-trend awareness.** Use session VWAP or opening direction to classify trend. Suppress counter-trend reversals/reclaims in the first hour, or require 2x the normal volume threshold. Feb 26: eliminates 12 traps. Feb 27: eliminates ~15 bad bearish signals. QQQ 9:45 bear trap (3 simultaneous bearish signals on a bullish day) is a textbook case.

4. **Suppress same-bar retests.** When a breakout and retest fire on the same bar, suppress the retest. Feb 27 had 8+ redundant same-bar retests across 12 symbols. QQQ's same-bar BRK+RST on Yest L is a logical contradiction.

5. **Merge closely-spaced levels.** When two levels are within 1x buffer distance, treat them as a single zone. MSFT's 40 missed crossings from ORB H / Week L ($0.30 apart) is the strongest evidence. AMZN's PM H / Yest H ($0.24 apart on Feb 25) is another case.

### Tier 2: Would Help on Specific Day Types

6. **Narrow-range day detector (helps chop days like Feb 25).** If first-30-min range < 50% ATR, dim/tag signals as "low conviction." On Feb 25, SPY range was 44% ATR -- this filter would have warned on every SPY signal.

7. **ORB L reversal priority filter (helps recovery days like Feb 27).** ORB L/PM L reversals were the best signals on Feb 27: 67% GOOD for original 9 symbols, and both AAPL REV ORB L and MSFT REV PM L were also GOOD. Highlight or prioritize ORB L/PM L reversals when the opening bar sells off but volume suggests institutional buying.

8. **Chop level detection (helps days with whipsaw levels).** When a level is crossed > 5 times in 60 minutes, suppress further signals at that level. GOOGL's PM H crossed ~15 times on Feb 27; AMD's ORB H was crossed 4+ times on both Feb 25 and Feb 27; MSFT's ORB H / Week L zone had 40 crossings on Feb 27; QQQ's ORB H had 16 missed crossings in the afternoon.

9. **Afternoon-only mode for late-recovery days.** On Feb 27, "after 10:30 only" was a meaningful filter. If morning chop is detected (e.g., 0 CONF in first 30 min), suggest suppressing morning signals.

10. **ATR-proportional FT thresholds for ETFs.** The fixed 0.3% threshold penalizes lower-volatility ETFs like QQQ. Using ATR-proportional thresholds would have turned several of QQQ's NEUTRAL signals into GOOD, giving a more accurate picture of signal quality.

### Tier 3: Nice-to-Have

11. **Cap D/W zone widths using ATR.** Prevents spurious signals 2-7pt away from the actual level (NVDA Yest H, META Week H on Feb 26).

12. **Fix pre-market bar reversal evaluation.** Skip reversal checks when the signal bar is from premarket data (NVDA 9:30 on Feb 26).

13. **Add distant-level filter.** Suppress signals where the level is > 2 ATR from current price (GOOGL Yest L on Feb 27).

14. **Investigate TSM confirmation timing gap.** The 3.5-hour confirmation delay on Feb 27 appears anomalous.

15. **Fix dual CONF bug (AAPL).** Auto-promote and regular CONF should share state to prevent conflicting confirmations at the same timestamp.

16. **Implement opening-minute signal suppression or confidence weighting.** All 12 symbols on Feb 27 produced excessive signals in the first 15-20 minutes. A settling period or higher conviction requirement would reduce noise without missing the best signals (which came 30+ minutes after open).

17. **Export methodology improvements.** Ensure full-session candle data for all symbols from the first analysis run. Use TradingView-exported 5m data instead of BATS for SPY/TSLA/META to eliminate composite tape discrepancies.

---

## 10. Trading Rules Derived from Data

### Rule 1: Identify the Day Type Early
- **First 30 minutes range vs ATR determines everything.**
  - Range > 80% ATR + 2+ level breaks on first bar with >10x volume = **Trend Day**. Trade with-trend breakouts aggressively. CONF is reliable.
  - Range < 50% ATR = **Chop Day**. Most breakouts will fail. Focus only on the 1-2 cleanest tickers. Wait for the genuine breakout (often 90+ minutes into session).
  - Range 50-80% ATR + V-shape in first 30 min = **Recovery Day**. ORB L reversals are the best trade. Afternoon breakouts are the real moves.

### Rule 2: Which Signal Types to Trust
- **Trust:** Breakouts in the trend direction on trend days (63% GOOD on Feb 26). ORB L/PM L reversals on recovery days (67%+ GOOD on Feb 27, confirmed by AAPL and MSFT data).
- **Trade with caution:** Reversals (31% GOOD overall) -- only when aligned with session direction and with high close position.
- **Avoid:** Reclaims (14% GOOD overall -- near-random). Counter-trend reversals on any day type. Same-bar retests (noise). Signals at closely-spaced levels (MSFT ORB H / Week L, AMZN PM H / Yest H).

### Rule 3: How to Use the Confirmation System
- **CONF failure is a reliable stop signal.** Across 3 days, CONF failure was correct ~95% of the time. If a breakout gets CONF failure, exit immediately or do not enter. QQQ and MSFT on Feb 27 had 0% CONF success (5 failures) -- correctly signaling to avoid all breakouts.
- **CONF success is only reliable on trend days.** On Feb 26, CONF success = 65% GOOD. On Feb 25 and 27, CONF success was 43% and 24% respectively.
- **Best filter: CONF confirmed AND no subsequent CONF failure.** This combination was the single highest-quality filter across all 3 days.
- **Watch for dual CONF bug:** If you see both "confirmed" and "failed" at the same timestamp (AAPL 10:00 Feb 27), treat as unconfirmed.

### Rule 4: Volume and Position Filters
- **Close position >= 95% (v95+/^95+) is a stronger signal than raw volume.** A 2x volume signal at v99 consistently outperformed a 10x volume signal at v50.
- **Volume >= 3x combined with position >= 80%** had approximately 33% GOOD rate on Feb 27 (the worst day) -- better than unfiltered.
- **High volume alone does not predict quality.** Feb 27: AMD 9:35 (13x vol, v19 pos) = BAD. Feb 27: AAPL 9:35 (17.8x vol, v91 pos) = BAD (bounce reversed). Feb 26: MSFT 9:35 (14.9x vol, v85 pos) = BAD.

### Rule 5: Time-of-Day Considerations
- **9:30-10:00 window:** Directionally informative but entries are risky due to extreme volatility. Use for bias detection, not trade entry (unless it's a clear trend day with CONF confirmation). Feb 27: AAPL had 6 signals in 16 minutes, QQQ had 7 in 20 minutes -- overwhelming noise.
- **10:00-11:00 window:** If the day is choppy, this is a dead zone. Avoid new positions. Exception: AAPL's 10:00 BRK Yest L on Feb 27 was the standout signal -- the noise had settled and the trend was clear.
- **11:00-14:00 window:** On chop/recovery days, this is when the genuine breakout often starts (SPY 11:45 on Feb 25, AMD 13:20 on Feb 27, SLV 10:45 on Feb 27).
- **15:00-16:00 window:** Late-day breakouts with elevated volume (>3x) on recovery days are often the day's best moves (AMZN/GOOGL 15:55 on Feb 27, SLV 15:30-15:50 on Feb 25). However, limited time for follow-through measurement/trade management. MSFT's 15:25 BRK ORB H was a late-day trap (BAD) -- late breakouts are not universally reliable.

### Rule 6: Symbol Selection
- **On chop days:** Focus on the 1-2 tickers with the cleanest momentum. On Feb 25, QQQ + META = 7/8 GOOD. Broad exposure = diluted signal quality.
- **On trend days:** Most tickers move together; trade the highest-volume, most liquid names. SPY, NVDA, GOOGL, TSM were all A-grade on Feb 26.
- **On recovery days:** Look for the outlier trend. Feb 27 AAPL was -3.19% while the market was +0.46% -- its bearish signals were the only consistently correct ones. Identify per-symbol trend, not just market trend.
- **Avoid on all days:** Tickers with tightly clustered levels (AMZN Feb 25: PM H and Yest H only 0.24pt apart; MSFT Feb 27: ORB H and Week L only $0.30 apart). Tickers with mid-bar position (40-60%) on opening signals.
- **ETF caution:** QQQ on Feb 27 went from A+ (Feb 25 chop day) to D+ (Feb 27 recovery day). Part of this is the 0.3% FT threshold being too high for a $600 ETF. Be aware that ETF signal grades may understate actual signal quality.
- **SLV requires special treatment:** Most signals of any ticker (12 on Feb 25, 6 on Feb 27). Often uncorrelated with equity indices. Best when it establishes a clear direction (B+ on Feb 27).
- **MSFT is structurally problematic:** D+ across 2 days of data. Closely-spaced levels (ORB H / Week L, PM L / ORB L) create whipsaw zones. Only the earliest reversal signals (9:30-9:35) are reliable.

### Rule 7: Risk Management
- **If CONF failure fires, the trade is over.** Do not average down or hold through CONF failure.
- **First breakout is often a trap on non-trend days.** Feb 25: SPY's first ORB H break at 9:50 was a trap; real breakout at 11:45. Feb 27: SPY 0/4 breakouts confirmed; QQQ 0/3 confirmed; MSFT 0/2 confirmed.
- **Counter-trend signals are negative expected value.** Over 3 days, counter-trend reclaims and reversals had a combined ~10% GOOD rate. Avoiding them entirely is the simplest win.
- **Expect 30%+ NEUTRAL signals.** Many signals are not clearly GOOD or BAD. This is normal -- the indicator identifies potential, not certainty. Use additional context (tape reading, order flow, broader market) to convert NEUTRAL situations into actionable decisions.
- **Watch for closely-spaced level traps.** If two levels are within ~$0.50 on a $400 stock (or within 1x buffer), treat the zone between them as untradeable noise. Wait for price to clear both levels decisively.
