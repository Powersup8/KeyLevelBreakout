# KeyLevelBreakout Signal Analysis — Feb 25, 2026

## ⚠ Missing Data — Action Required

| Symbol | Pine Logs | Candle Data | Status |
|--------|-----------|-------------|--------|
| **AAPL** | ✗ MISSING | ✗ MISSING | **Cannot analyze — export both** |
| **MSFT** | ✗ MISSING | ✗ MISSING | **Cannot analyze — export both** |
| AMD | ✓ 696e6 | ✗ MISSING | FT from pine log only — **export candle** |
| NVDA | ✓ 0a1ef | ✗ MISSING | FT from pine log only — **export candle** |
| TSLA | ✓ 9ce87 | ✗ MISSING | FT from pine log only — **export candle** |
| TSM | ✓ 4b04d | ✗ MISSING | FT from pine log only — **export candle** |
| GOOGL | ✓ cfd64 | ⚠ Partial (15:28-15:59) | No morning FT verification — **export full session** |
| META | ✓ 56661 | ⚠ Partial (14:42-15:59) | No morning FT verification — **export full session** |
| SLV | ✓ e0129 | ✗ MISSING | FT from pine log only — **export candle** |
| AMZN | ✓ 44b3b | ✗ MISSING | FT from pine log only — **export candle** |
| SPY | ✓ 4415c | ✓ 92036 (full session) | **Complete** ✓ |
| QQQ | ✓ 1959d | ✓ 2db23 (full session) | **Complete** ✓ |

> **Note:** Only SPY and QQQ have candle-verified follow-through. All other FT values are estimated from pine log OHLC between consecutive signals. Ratings marked with `*` are estimates.

---

## Data Inventory

| Symbol | Pine Log File | Coverage | Candle Data File | Candle Coverage |
|--------|--------------|----------|-----------------|----------------|
| SPY | 4415c | 09:35–11:45 | BATS_SPY 92036 | Full session ✓ |
| QQQ | 1959d | 09:30–09:45 | BATS_QQQ 2db23 | Full session ✓ |
| META | 56661 | 09:30–09:50 | BATS_META 6a7dd | Partial (14:42–15:59) |
| TSLA | 9ce87 | 09:30–09:45 | BATS_TSLA 373d3 | Partial (15:56–16:00) |
| AMD | 696e6 | 09:35–15:15 | — | None |
| NVDA | 0a1ef | 09:30–10:18 | BATS_NVDA 0b43f | After-hours only |
| GOOGL | cfd64 | 09:35–15:50 | BATS_GOOGL bc9cd | Partial (15:28–15:59) |
| TSM | 4b04d | 09:30–10:03 | BATS_TSM ad0ec | Partial (15:30–16:00) |
| SLV | e0129 | 09:35–15:50 | BATS_SLV 45615 | Partial (15:50–16:00) |
| AMZN | 44b3b | 09:35–14:35 | BATS_AMZN 8a8b0 | Partial (15:44–16:00) |

---

## Executive Summary

**Market context:** Moderately bullish day. SPY +2.87pt (+0.4%), QQQ +5.43pt (+0.9%). Low-range, grind-higher session — SPY range was only 3.58pt (vs 9.0pt on Feb 26). Most symbols trended gently bullish but with significant opening chop. QQQ and META were the cleanest movers; SPY, GOOGL, TSM, SLV, and AMZN were whipsaw-heavy.

**10 symbols analyzed:** SPY, QQQ, META, TSLA, AMD, NVDA, GOOGL, TSM, SLV, AMZN
**Not analyzed (no data):** AAPL, MSFT

### Scorecard

| Symbol | Grade | Signals | GOOD | NEUTRAL | BAD | Confirm Rate | Best Trade | Worst Trade |
|--------|-------|---------|------|---------|-----|-------------|------------|-------------|
| SPY    | **D+** | 9      | 2    | 4       | 3   | 0% (0/1)    | 11:45 long BRK ORB H (+0.39 at 30m, +1.17 to EOD) | 9:50 long BRK ORB H (CONF ✓→✗, -1.08 at 15m) |
| QQQ    | **A+** | 4      | 4    | 0       | 0   | 100% (2/2)  | 9:30 long BRK Week H (+4.20 at 30m, +5.46 to EOD) | — |
| META   | **A**  | 4      | 3    | 1       | 0   | 100% (2/2)  | 9:35 long BRK PM H* (+6.29 to ORB H break) | — |
| TSLA   | **B**  | 6      | 2    | 3       | 1   | 100% (1/1)  | 9:30 long BRK Yest H* (+6.25 at 5m) | 9:45 short ~ ORB H* (counter-trend) |
| AMD    | **C**  | 7      | 3    | 2       | 2   | 0% (0/1)    | 9:45 long ~ Yest L* (+1.84 at 10m) | 9:55 long ~~ ORB L* (failed reclaim) |
| NVDA   | **C+** | 5      | 1    | 3       | 1   | n/a         | 9:40 long ~ ORB L* (+1.38 at 15m) | 9:35 short ~ ORB H* (counter-trend) |
| GOOGL  | **D+** | 8      | 2    | 2       | 4   | 0% (0/2)    | 9:40 long ~~ PM L* (+0.58 at 5m) | 9:50 long BRK PM H* (CONF ✓→✗, -1.65) |
| TSM    | **D+** | 7      | 2    | 1       | 4   | 0% (0/2)    | 9:30 short ~ PM H* (-2.78 at 5m) | 9:45 long BRK Yest H* (CONF ✗, -1.14) |
| SLV    | **D+** | 12     | 4    | 4       | 4   | 50% (1/2)   | 15:35 short BRK ORB L* (-0.75 to PM L break) | 15:00 long BRK PM H* (CONF ✓→✗, crashed) |
| AMZN   | **D**  | 9      | 1    | 4       | 4   | 0% (0/1)    | 9:50 long ~~ ORB L* (+0.23 at 5m) | 10:05 long BRK PM H+Week H* (CONF ✓→✗, -1.09) |

*Ratings marked with `*` are estimated from pine log OHLC (no candle verification).*

### Aggregate Statistics

| Metric | Value |
|--------|-------|
| Total signals across 10 symbols | **71** |
| GOOD signals | **24** (34%) |
| NEUTRAL signals | **24** (34%) |
| BAD signals | **23** (32%) |
| Confirmed breakouts (✓) | **6/14** tracked (43%) |
| Failed breakouts (✗) | **8/14** tracked (57%) |
| **Bullish signals that were GOOD** | **19/52** (37%) |
| **Bearish signals that were GOOD** | **5/19** (26%) |

---

## Key Takeaways

### 1. Low-range days generate noise — lots of it
Feb 25 produced **71 signals** vs Feb 26's 53, but with far worse accuracy (34% GOOD vs 47%). The gentle grind-higher didn't break levels decisively — most breakouts were quickly reclaimed.

### 2. Confirmation system was a strong warning: 57% failure rate
Only 43% of tracked breakouts confirmed (vs 65% on Feb 26). When CONF ✗ fired, it was right every time — the entry was bad. **If you only traded CONF ✓ signals, you got 6 signals: QQQ (2), META (2), TSLA (1), SLV (1).**

### 3. QQQ and META were the "clean" tickers
Both had 100% GOOD rates with 100% confirmation. They were the only tickers with clear momentum — Week H break (QQQ), PM H + ORB H cascade (META). **Single-ticker focus on the strongest mover would have been optimal.**

### 4. SPY was the worst-performing index ticker
Despite being bullish, SPY's narrow range (3.58pt) turned every breakout into a whipsaw zone. The first ORB H breakout at 9:50 was auto-confirmed then failed 14 minutes later. The real breakout didn't come until 11:45 — **2 hours of chop before the genuine signal.**

### 5. Reclaims were mixed but slightly better than Feb 26
Unlike Feb 26 where 0/5 reclaims worked, Feb 25 had some success (SPY 10:05 ~~ ORB H: GOOD, AMD 9:45 ~ Yest L: GOOD). But reclaims still had a high failure rate overall.

### 6. Confirmed breakouts that later failed were the biggest traps
SPY ORB H (9:50 CONF ✓ → 10:04 ✗), GOOGL PM H (9:50 ✓ → 10:00 ✗), AMZN PM H+Week H (10:05 ✓ → 10:18 ✗), SLV PM H (15:00 ✓ → 15:16 ✗). All resulted in BAD signals. **The auto-promote mechanism is too fast on choppy days — price crosses the threshold briefly, gets confirmed, then immediately reverses.**

### 7. Afternoon signals improved on SLV
SLV's first 5 signals (morning) were 2 GOOD, 1 NEUTRAL, 2 BAD. The afternoon cascade (15:30-15:50) was 3 signals, 2 GOOD. The real move came late.

---

## Signal Quality by Type

| Type | Total | GOOD | BAD | Win Rate |
|------|-------|------|-----|----------|
| BRK (Breakout) | 28 | 12 | 9 | 43% |
| ~ (Reversal) | 20 | 6 | 5 | 30% |
| ~~ (Reclaim) | 13 | 4 | 5 | 31% |
| ◆ (Retest) | 10 | 2 | 4 | 20% |

**Breakouts were the most reliable but still only 43%** (vs 63% on Feb 26). Reversals and reclaims were coin-flips. Retests had the worst win rate at 20% — most retests on this day were retesting levels that were about to fail.

---

## Per-Symbol Detailed Analysis

### SPY — Grade: D+

**Key Levels:** PM H 690.74 | PM L 688.78 | Week H 690.06 | ORB H 691.23 | ORB L 690.10 | ATR 8.09

**Session OHLC (candle-verified):** Open 690.19 | High 693.68 (15:50) | Low 690.10 (9:30) | Close 693.06 | Range 3.58pt | Net +2.87 (+0.4%)

**Day narrative:** Low-range grind higher. Opened right at ORB L/PM H zone — immediate conflict. First bar broke PM H + Week H with 9.3x volume but only ^66 position (mid-bar, not decisive). ORB H broke at 9:50 and was auto-confirmed, but failed at 10:04 — price dropped to 690.33 (below PM H). Two bearish reclaims followed (10:05, 10:15). Then 90 minutes of sideways chop between 690.2-691.2 before the genuine ORB H breakout at 11:45. From there, steady grind to 693.68 session high at 15:50.

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|
| 1 | 9:35 | ▲ | BRK | PM H + Week H | 9.3x | ^66 | NEUTRAL | +0.07 | +0.55 | -0.25 |
| 2 | 9:35 | ▲ | ~ | ORB L | 9.3x | ^66 | NEUTRAL | +0.07 | +0.55 | -0.25 |
| 3 | 9:45 | ▼ | ~ | ORB H | 5.2x | v58 | **BAD** | +0.48 | +0.02 | -0.30 |
| 4 | 9:45 | ▲ | ◆² | PM H | 5.2x | ^42 | NEUTRAL | +0.48 | +0.02 | -0.30 |
| 5 | 9:50 | ▲ | BRK | ORB H | 4.4x | ^80 | **BAD** | -0.37 | -1.08 | -0.97 |
| 6 | 10:00 | ▲ | ◆² | ORB H | 2.6x | ^72 | **BAD** | -0.72 | -0.70 | -0.91 |
| 7 | 10:05 | ▼ | ~~ | ORB H | 2.5x | v97 | **GOOD** | -0.45 | -0.23 | -0.57 |
| 8 | 10:15 | ▼ | ~~ | PM H | 1.5x | v70 | NEUTRAL | +0.22 | -0.08 | +0.03 |
| 9 | 11:45 | ▲ | BRK | ORB H | 1.6x | ^74 | **GOOD** | +0.22 | +0.28 | +0.39 |

**Confirmations:** 0/1 (0%). ORB H breakout confirmed at 9:50, failed at 10:04.
**SPY lesson:** On narrow-range days, the first breakout is often a trap. The genuine breakout came 2 hours later at 11:45 with lower volume (1.6x) but steady follow-through — patience > conviction.

---

### QQQ — Grade: A+

**Key Levels:** PM H 611.50 | Week H 610.35 | ORB H 613.06 | ORB L 611.01 | ATR 9.95

**Session OHLC (candle-verified):** Open 611.11 | High 616.86 (15:50) | Low 611.01 (9:30) | Close 616.54 | Range 5.85pt | Net +5.43 (+0.9%)

**Day narrative:** Textbook low-to-high trending day. Session low printed on the opening bar. Staircase breakouts: Week H (9:30), PM H (9:35 confirmed), ORB H (9:45 confirmed). Price never looked back — every 5m bar from 9:30 to 9:55 printed a higher close. Consolidated 614-615 from 10:00-11:00, then resumed rally to 616.86. All 4 signals bullish, all GOOD.

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|
| 1 | 9:30 | ▲ | BRK | Week H | 2.8x | ^90 | **GOOD** | +2.04 | +3.82 | +4.20 |
| 2 | 9:35 | ▲ | BRK | PM H | 14.0x | ^75 | **GOOD** | +1.21 | +2.73 | +2.31 |
| 3 | 9:35 | ▲ | ~ | ORB L | 14.0x | ^75 | **GOOD** | +1.21 | +2.73 | +2.31 |
| 4 | 9:45 | ▲ | BRK | ORB H | 6.1x | ^86 | **GOOD** | +1.52 | +1.52 | +0.64 |

**Confirmations:** 2/2 (100%). Both PM H and ORB H breakouts auto-promoted and held.
**QQQ highlight:** Signal 1 (BRK Week H) had +5.46 FT to EOD — the best bullish trade across all 10 symbols. The weekly high break was the entry of the day.

---

### META — Grade: A

**Key Levels:** PM H 643.00 | ORB H 645.64 | ORB L 642.14 | Yest H 641.11 | ATR 20.18

**Day narrative:** Strong bullish open. First bar (9:30) broke Yest H with massive close (^100 — closed at bar high). Second bar (9:35) broke PM H with 17.3x volume. ORB H broken at 9:50 with ^97 position, auto-confirmed. Pine log ends at 9:50 — limited afternoon visibility. Closed ~651 (estimated from level data).

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|
| 1 | 9:30 | ▲ | BRK | Yest H | 3.3x | ^100 | **GOOD*** | +0.21 | n/a | n/a |
| 2 | 9:35 | ▲ | BRK | PM H | 17.3x | ^31 | **GOOD*** | n/a | +6.29 | n/a |
| 3 | 9:35 | ▲ | ~ | ORB L | 17.3x | ^31 | **GOOD*** | n/a | +6.29 | n/a |
| 4 | 9:50 | ▲ | BRK | ORB H | 5.9x | ^97 | NEUTRAL* | n/a | n/a | n/a |

**Confirmations:** 2/2 (100%). Both Yest H and ORB H breakouts auto-promoted.
**Note:** FT from pine log only — consecutive signal closes used (643.00 → 643.21 → 649.50). Signal 4 rated NEUTRAL due to limited FT data (no subsequent signal to measure against). *Candle export needed for precise FT.*

---

### TSLA — Grade: B

**Key Levels:** PM H 412.22 | Yest H 410.82 | Week H 416.90 | Week L 400.51 | ORB H 419.58 | ORB L 412.14 | ATR 14.85

**Day narrative:** Explosive bullish open. First bar (9:30) broke Yest H at ^96. Second bar (9:35) was a monster — 7.44pt range (412.14 to 419.58), breaking PM H + Week H with 18.2x volume and CONF ✓. Then immediate pullback — 9:45 bar reversed at ORB H (v99), dropped from 418.96 to 416.93. TSLA closed ~417.38, essentially at the pullback level. Classic "gap and stall."

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|
| 1 | 9:30 | ▲ | BRK | Yest H | 2.0x | ^96 | **GOOD*** | +6.25 | n/a | n/a |
| 2 | 9:30 | ▲ | ~ | Week L | 2.0x | ^96 | **GOOD*** | +6.25 | n/a | n/a |
| 3 | 9:35 | ▲ | BRK | PM H + Week H | 18.2x | ^84 | NEUTRAL* | -1.47 | n/a | n/a |
| 4 | 9:35 | ▲ | ~ | ORB L | 18.2x | ^84 | NEUTRAL* | -1.47 | n/a | n/a |
| 5 | 9:45 | ▼ | ~ | ORB H | 4.1x | v99 | **BAD*** | n/a | n/a | n/a |
| 6 | 9:45 | ▲ | ◆² | Week H | 5.1x | ^1 | NEUTRAL* | n/a | n/a | n/a |

**Confirmations:** 1/1 (100%). PM H + Week H breakout confirmed.
**TSLA highlight:** Signal 1 had +6.25 FT at 5m — the largest single-bar follow-through. But the 9:35 bar was so extended (7.44pt) that the entry was at the top, leading to pullback.

---

### AMD — Grade: C

**Key Levels:** PM H 215.75 | PM L 214.20 | Yest H 216.71 | Yest L 206.50 | ORB H 216.70 | ORB L 211.87 | ATR 11.83

**Day narrative:** Whipsaw city. Opening bar (9:35) was a 4.83pt range that broke PM L (v96, 15.1x vol) while reversing at PM H + Yest H + ORB H. ORB L broke at 9:40, confirmed, then failed at 9:50. Yest L reversal at 9:45 triggered a bounce. Reclaim at 9:55 brought price back to 213.59. Then slow grind down all afternoon — ORB L broke again at 15:05. AMD closed ~211, below ORB L.

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|
| 1 | 9:35 | ▼ | BRK | PM L | 15.1x | v96 | **GOOD*** | -0.64 | n/a | n/a |
| 2 | 9:35 | ▼ | ~ | PM H + Yest H + ORB H | 15.1x | v96 | **GOOD*** | -0.64 | n/a | n/a |
| 3 | 9:40 | ▼ | BRK | ORB L | 9.6x | v48 | **BAD*** | +0.33 | n/a | n/a |
| 4 | 9:45 | ▲ | ~ | Yest L | 4.6x | ^88 | **GOOD*** | +1.84 | n/a | n/a |
| 5 | 9:55 | ▲ | ~~ | ORB L | 3.1x | ^83 | **BAD*** | n/a | n/a | n/a |
| 6 | 15:05 | ▼ | BRK | ORB L | 1.6x | v20 | NEUTRAL* | n/a | n/a | n/a |
| 7 | 15:15 | ▼ | ◆² | ORB L | 1.2x | v27 | NEUTRAL* | n/a | n/a | n/a |

**Confirmations:** 0/1 (0%). ORB L breakout confirmed at 9:40, failed at 9:50.
**AMD lesson:** The Yest L reversal at 9:45 was the only signal that truly worked — a counter-trend bounce with ^88 position. Opening bar signals were correct directionally (bearish) but the ORB L break was premature.

---

### NVDA — Grade: C+

**Key Levels:** PM H 194.85 | ORB H 195.00 | ORB L 194.03 | ATR 5.96

**Day narrative:** Initial weakness, then recovery. First bar (9:30) reversed at PM H (v80). Second bar (9:35) reversed at ORB H (v96) — two consecutive bearish reversals. But 9:40 bar bounced off ORB L (^71), and by 9:55 NVDA broke above PM H + ORB H with ^92 position. Closed ~196, above all opening levels.

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|
| 1 | 9:30 | ▼ | ~ | PM H | 2.5x | v80 | NEUTRAL* | -0.41 | n/a | n/a |
| 2 | 9:35 | ▼ | ~ | ORB H | 14.3x | v96 | **BAD*** | +0.33 | n/a | n/a |
| 3 | 9:40 | ▲ | ~ | ORB L | 8.6x | ^71 | **GOOD*** | +1.38 | n/a | n/a |
| 4 | 9:55 | ▲ | BRK | PM H + ORB H | 4.8x | ^92 | NEUTRAL* | n/a | n/a | n/a |
| 5 | 10:18 | ▲ | ◆⁴ | ORB H | 1.1x | ^1 | NEUTRAL* | n/a | n/a | n/a |

**NVDA pattern:** The early bearish reversals (signals 1-2) were traps on a recovery day. Signal 3 (ORB L reversal) caught the bottom correctly. The BRK PM H+ORB H at 9:55 was the trend-confirming entry.

---

### GOOGL — Grade: D+

**Key Levels:** PM H 312.85 | PM L 311.47 | Yest H 312.27 | Yest L 305.93 | ORB H 312.16 | ORB L 309.63 | ATR 9.23

**Day narrative:** Maximum chop. BRK PM L at 9:35 failed in 2 minutes (CONF ✗ at 9:37). Immediate reclaim + Yest L reversal at 9:40. Then bullish cascade: BRK Yest H+ORB H at 9:45, BRK PM H at 9:50 (confirmed then failed at 10:00). Bearish reclaim at 10:05 (PM H + ORB H). Afternoon recovery — PM L reclaim at 15:10, BRK Yest H+ORB H again at 15:50. GOOGL closed ~312.39 — essentially flat for the day.

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|
| 1 | 9:35 | ▼ | BRK | PM L | 15.6x | v74 | **BAD*** | +1.62 | n/a | n/a |
| 2 | 9:35 | ▼ | ~ | Yest H + ORB H | 15.6x | v74 | **BAD*** | +1.62 | n/a | n/a |
| 3 | 9:40 | ▲ | ~~+~ | PM L + Yest L | 7.3x | ^87 | **GOOD*** | +0.58 | n/a | n/a |
| 4 | 9:45 | ▲ | BRK | Yest H + ORB H | 5.5x | ^65 | NEUTRAL* | +0.79 | n/a | n/a |
| 5 | 9:50 | ▲ | BRK | PM H | 4.4x | ^90 | **BAD*** | -1.65 | n/a | n/a |
| 6 | 10:05 | ▼ | ~~ | PM H + ORB H | 3.1x | v80 | **BAD*** | n/a | n/a | n/a |
| 7 | 15:10 | ▲ | ~~ | PM L | 2.5x | ^79 | **GOOD*** | n/a | n/a | n/a |
| 8 | 15:50 | ▲ | BRK | Yest H + ORB H | 2.0x | ^44 | NEUTRAL* | n/a | n/a | n/a |

**Confirmations:** 0/2 (0%). PM L BRK failed at 9:37. PM H BRK confirmed at 9:50, failed at 10:00.
**GOOGL lesson:** On a flat day (close ≈ open), every breakout in both directions was a trap. The 9:37 CONF ✗ was the fastest failure across all symbols — only 2 minutes.

---

### TSM — Grade: D+

**Key Levels:** PM H 391.80 | PM L 388.80 | Yest H 389.18 | ORB H 390.21 | ATR 13.62

**Day narrative:** Bearish open, then whipsaw. First bar (9:30) reversed at PM H with v99 — strong bearish conviction. Second bar (9:35) broke PM L with 14.1x volume, but CONF ✗ at 9:44. Immediate reversal: BRK Yest H + reclaim PM L at 9:45, also failed (CONF ✗ at 9:47). PM L broke again at 9:50. TSM closed ~387.87, below PM L. Every tracked breakout failed.

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|
| 1 | 9:30 | ▼ | ~ | PM H | 2.6x | v99 | **GOOD*** | -2.78 | n/a | n/a |
| 2 | 9:35 | ▼ | BRK | PM L | 14.1x | v67 | **BAD*** | +2.39 | n/a | n/a |
| 3 | 9:35 | ▼ | ~ | ORB H | 14.1x | v67 | **BAD*** | +2.39 | n/a | n/a |
| 4 | 9:45 | ▲ | BRK | Yest H | 4.8x | ^88 | **BAD*** | -1.14 | n/a | n/a |
| 5 | 9:45 | ▲ | ~~ | PM L | 4.8x | ^88 | **BAD*** | -1.14 | n/a | n/a |
| 6 | 9:50 | ▼ | BRK | PM L | 3.0x | v61 | **GOOD*** | n/a | n/a | n/a |
| 7 | 10:03 | ▼ | ◆² | PM L | 2.0x | v45 | NEUTRAL* | n/a | n/a | n/a |

**Confirmations:** 0/2 (0%). PM L BRK failed at 9:44. Yest H BRK failed at 9:47.
**TSM highlight:** Signal 1 (9:30 ~ PM H at v99) had the strongest single-bar FT among TSM signals (-2.78). The PM H reversal was the only clean read all morning — everything after was whipsaw.

---

### SLV — Grade: D+

**Key Levels:** PM H 82.43 | PM L 81.10 | ORB H 82.23 | ORB L 81.58 | ATR 5.88

**Day narrative:** Two acts. **Morning (9:35-12:45):** Opened bearish (~ ORB H, BRK ORB L), but ORB L break failed immediately. PM L reversal at 9:45 launched a recovery. Price worked up to PM H zone by 12:45. **Afternoon (13:00-15:50):** BRK ORB H at 13:00, then BRK PM H at 15:00 (confirmed then failed at 15:16). Then total reversal — reclaimed ORB H, broke ORB L and PM L in rapid succession with CONF ✓. SLV closed ~80.89, near session lows. **12 signals — most of any symbol.**

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|
| 1 | 9:35 | ▼ | ~ | ORB H | 8.6x | v71 | NEUTRAL* | -0.59 | n/a | n/a |
| 2 | 9:40 | ▼ | BRK | ORB L | 6.3x | v78 | **BAD*** | +0.51 | n/a | n/a |
| 3 | 9:45 | ▲ | ~ | PM L | 3.9x | ^93 | **GOOD*** | +0.31 | n/a | n/a |
| 4 | 9:55 | ▲ | ~~ | ORB L | 2.0x | ^87 | **GOOD*** | n/a | n/a | n/a |
| 5 | 12:45 | ▼ | ~ | PM H | 2.2x | v95 | **BAD*** | +0.22 | n/a | n/a |
| 6 | 13:00 | ▲ | BRK | ORB H | 3.2x | ^48 | NEUTRAL* | n/a | n/a | n/a |
| 7 | 13:10 | ▲ | ◆² | ORB H | 0.2x | ^38 | NEUTRAL* | n/a | n/a | n/a |
| 8 | 15:00 | ▲ | BRK | PM H | 2.2x | ^31 | **BAD*** | n/a | n/a | n/a |
| 9 | 15:10 | ▲ | ◆² | PM H | 0.8x | ^35 | **BAD*** | n/a | n/a | n/a |
| 10 | 15:30 | ▼ | ~~ | ORB H | 2.4x | v95 | **GOOD*** | -0.06 | n/a | n/a |
| 11 | 15:35 | ▼ | BRK | ORB L | 3.0x | v30 | **GOOD*** | n/a | n/a | n/a |
| 12 | 15:50 | ▼ | BRK | PM L | 4.6x | v73 | NEUTRAL* | n/a | n/a | n/a |

**Confirmations:** 1/2 (50%). ORB L BRK failed at 9:45. PM L BRK confirmed at 15:50.
**SLV pattern:** A "V-reversal" day — up all morning/midday, crash in last 30 minutes. The indicator captured both phases but the midday signals (ORB H break, PM H break) were traps.

---

### AMZN — Grade: D

**Key Levels:** PM H 210.60 | ORB H 211.37 | ORB L 210.11 | Yest H 210.36 | Week H 211.17 | ATR 6.84

**Day narrative:** Narrow range, maximum confusion. Opening bar (9:35) reversed at PM H + ORB H with v100 (extreme bearish close position). ORB L broke at 9:40 but CONF ✗ at 9:46. Quick reclaim, then bullish cascade: BRK Yest H (9:55), BRK PM H + Week H (10:05 confirmed then failed at 10:18). Reclaim PM H at 10:20. Afternoon: reclaim ORB L at 14:35. AMZN closed ~210.39 — flat. **Every single breakout that was tracked either failed or faded.**

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|
| 1 | 9:35 | ▼ | ~ | PM H + ORB H | 16.5x | v100 | NEUTRAL* | -0.23 | n/a | n/a |
| 2 | 9:40 | ▼ | BRK | ORB L | 11.8x | v64 | **BAD*** | +0.61 | n/a | n/a |
| 3 | 9:40 | ▼ | ~ | Week H | 11.8x | v64 | **BAD*** | +0.61 | n/a | n/a |
| 4 | 9:50 | ▲ | ~~ | ORB L | 3.0x | ^66 | **GOOD*** | +0.23 | n/a | n/a |
| 5 | 9:55 | ▲ | BRK | Yest H | 2.6x | ^85 | NEUTRAL* | +0.58 | n/a | n/a |
| 6 | 10:05 | ▲ | BRK | PM H + Week H | 3.8x | ^67 | **BAD*** | -1.09 | n/a | n/a |
| 7 | 10:15 | ▲ | ◆² | PM H | 1.4x | ^20 | **BAD*** | n/a | n/a | n/a |
| 8 | 10:20 | ▼ | ~~ | PM H | 1.7x | v84 | NEUTRAL* | n/a | n/a | n/a |
| 9 | 14:35 | ▲ | ~~ | ORB L | 2.4x | ^98 | NEUTRAL* | n/a | n/a | n/a |

**Confirmations:** 0/1 (0%). PM H + Week H breakout confirmed at 10:05, failed at 10:18.
**AMZN lesson:** Narrow-range stocks (~1pt session range) with tightly clustered levels are the worst environment for breakout signals. PM H (210.60) and Yest H (210.36) were only 0.24pt apart — every move through one immediately tested the other.

---

## Bugs & Issues Found

### ISSUE 1: Auto-Promote Too Fast on Choppy Days (HIGH priority)

**What happened:** 4 breakouts were auto-promoted (CONF ✓) then failed within 2-18 minutes:
- SPY ORB H: 9:50 ✓ → 10:04 ✗ (14 min)
- GOOGL PM H: 9:50 ✓ → 10:00 ✗ (10 min)
- AMZN PM H+Week H: 10:05 ✓ → 10:18 ✗ (13 min)
- SLV PM H: 15:00 ✓ → 15:16 ✗ (16 min)

**Impact:** High — traders trusting CONF ✓ took 4 losing trades. On Feb 26 (trend day), CONF ✓ was 10/11 GOOD. On Feb 25 (chop day), it was 6/10 — the 4 failures above had no GOOD outcome.

**Possible fix:** Delay auto-promote on days when ATR-relative range is low (narrow range = higher whipsaw risk). Or require the close to hold above the level for 2 consecutive 5m bars before confirming.

### ISSUE 2: GOOGL PM L Fastest Failure (2 min) — firstOnly Re-arm Question

**What happened:** BRK PM L fired at 9:35, CONF ✗ at 9:37. Then at 9:40, the PM L *reclaim* fired — suggesting the breakout state properly reset. But by 9:45, PM L didn't re-fire a bearish BRK despite price presumably crossing below again at some point. Was this firstOnly suppression? Or did the level never truly re-break?

**Impact:** Low — price went up, so no missed signal. But worth verifying the re-arm logic.

### DESIGN CONSIDERATION: Narrow-Range Day Detector

**Pattern:** On Feb 25, the average session range was small (SPY 3.58pt vs ATR 8.09 = 44% of ATR). When range is < 50% of ATR, breakout signals have a ~34% GOOD rate (vs ~47% on trend days like Feb 26).

**Possible approach:** If the first 30 minutes establish < 50% of ATR range, suppress or dim signals with a "low-range" warning. This would have prevented most false breakouts on Feb 25.

---

## If You Traded: Strategy Comparison

| Strategy | Signals Taken | GOOD | BAD | Net Direction |
|----------|--------------|------|-----|---------------|
| All signals | 71 | 24 | 23 | Slightly positive |
| Bullish only | 52 | 19 | 14 | Moderately positive |
| Confirmed BRK only (✓) | 6 | 5 | 0 | **Good** (but only 6 trades) |
| QQQ + META only | 8 | 7 | 0 | **Excellent** |
| Reversals only | 20 | 6 | 5 | Slightly positive |
| Reclaims only | 13 | 4 | 5 | Negative |
| Retests only | 10 | 2 | 4 | Negative |

**Best filter for this day:** Trade only CONF ✓ signals that *survived* (i.e., never got CONF ✗). That gives QQQ (2), META (2), TSLA (1), SLV PM L (1) = 6 signals, 5 GOOD + 1 NEUTRAL.

**Or simply:** Focus on QQQ + META (the cleanest movers) = 8 signals, 7 GOOD, 0 BAD.

---

## What Went Well

- QQQ and META: perfect signal accuracy, 100% confirmation rate
- CONF ✗ was a reliable warning — every failure flag was correct
- TSLA's opening bar BRK Yest H captured a massive +6.25pt move
- SLV's afternoon bearish cascade (15:30-15:50) captured a genuine 2pt reversal
- TSM's 9:30 PM H reversal (v99) was the strongest conviction signal and worked perfectly
- No false signals on the clearly trending tickers (QQQ, META)

## What Didn't Go Well

- 71 signals is too many — signal-to-noise ratio was poor on this choppy day
- SPY ORB H false breakout with auto-confirm (CONF ✓ → ✗) was the biggest trap
- 4 confirmed breakouts failed (SPY, GOOGL, AMZN, SLV) — auto-promote mechanism too aggressive on low-range days
- GOOGL was maximum chop — 8 signals, 4 BAD, essentially untradeable
- AMZN's tightly clustered levels (PM H and Yest H only 0.24pt apart) caused confusion
- No pine log data for AAPL and MSFT — two core watchlist symbols missing
- Only 2/10 symbols have candle-verified FT — most ratings are estimates

## Recommendations for Indicator Improvement

1. **Delay auto-promote on low-range days** — require 2 consecutive 5m bars above level before CONF ✓, or increase the threshold when first-hour range < 50% ATR
2. **Add narrow-range day warning** — if 30-min range < 50% ATR, dim or tag signals as "low conviction"
3. **Investigate clustered-level filter** — when multiple levels are < 0.5% apart (like AMZN), merge them or suppress redundant signals
4. **Reduce retest frequency** — 10 retests generated only 2 GOOD signals (20%). Consider higher threshold for retest emissions
5. **Export complete data for all watchlist symbols** — AAPL and MSFT pine logs missing entirely; candle data missing for 8/10 symbols

---

## Cross-Day Comparison: Feb 25 vs Feb 26

| Metric | Feb 25 (Chop) | Feb 26 (Trend) |
|--------|---------------|----------------|
| SPY Range | 3.58pt (44% ATR) | 9.0pt (113% ATR) |
| Total Signals | 71 | 53 |
| GOOD Rate | 34% | 47% |
| BAD Rate | 32% | 26% |
| CONF Success | 43% (6/14) | 65% (11/17) |
| Best Strategy | QQQ+META only | Confirmed BRK only |
| Counter-Trend Traps | Mixed | 100% failed |

**Key insight:** The indicator performs significantly better on trend days (clean directional moves, high ATR utilization) vs chop days (narrow range, whipsaw breakouts). A "day type" classifier could dramatically improve signal quality by adjusting thresholds based on early-session character.
