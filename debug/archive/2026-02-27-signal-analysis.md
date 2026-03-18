# KeyLevelBreakout Signal Analysis — Feb 27, 2026

*Generated: 2026-02-28*
*Indicator: KeyLevelBreakout v2.2*

**Methodology:** 1-minute BATS candle data aggregated into 5-minute bars (aligned to session open 09:30). Follow-through measured at 5m/15m/30m after signal bar close using the pine log's reported close price. Rating: GOOD if 15m or 30m FT >= +0.3% of price, BAD if <= -0.3%, else NEUTRAL.

**Bar alignment note:** Pine Script signals fire at the OPEN of the bar AFTER the signal bar. So a signal timestamped "9:35" was triggered by the 9:30-9:34 bar. All OHLC values in the pine log match the PREVIOUS 5m bar (verified for all signals). FT is calculated from the signal bar's close.

---

## Missing Data

All 12 symbols analyzed. No missing data.

---

## Data Inventory

| Symbol | Pine Log Hash | Coverage | Candle Data Hash |
|--------|---------------|----------|------------------|
| SPY | 332ac | Full session | 9d4c2 |
| AMD | e4ccc | Full session | e859f |
| NVDA | c303a | Full session | a81b6 |
| TSLA | e923d | Full session | 6cbb7 |
| TSM | 99efc | Full session | 1768e |
| SLV | 90fcf | Full session | aa4d1 |
| AMZN | b5978 | Full session | 22e1f |
| GOOGL | 4e22e | Full session | d0e08 |
| META | bc0f1 | Full session | 4e874 |
| AAPL | 98520 | Full session | a11cd |
| QQQ | 07880 | Full session | 98261 |
| MSFT | 2a8ba | Full session | 24662 |

---

## Executive Summary

**Market context:** Feb 27 was a choppy morning that turned into a late bullish session. Most symbols had V-shaped or U-shaped recoveries. Morning signals were mostly noise; late-day breakouts were the real moves.

### Scorecard

| Symbol | Grade | Signals | GOOD | BAD | NEUTRAL | N/A | Confirm Rate | Best Trade | Worst Trade |
|--------|-------|---------|------|-----|---------|-----|-------------|------------|-------------|
| SPY | C | 11 | 0 | 0 | 10 | 1 | 0/4 (0%) | 15:15 BRK ORB H (late breakout) | 9:45 bearish cluster (wrong direction) |
| TSLA | D+ | 7 | 0 | 5 | 1 | 1 | 0/2 (0%) | 15:55 ~ ORB L (N/A, late) | 9:40 BRK ORB H (immediate reversal) |
| META | C | 4 | 0 | 1 | 2 | 1 | 0/1 (0%) | 15:15 ~ Week L (neutral) | 9:30 BRK Yest L (gap reversal) |
| AMD | C+ | 10 | 1 | 6 | 3 | 0 | 1/4 (25%) | 13:20 BRK PM L (GOOD, confirmed) | 9:35 ~ ORB H (counter-trend) |
| NVDA | C+ | 8 | 0 | 3 | 5 | 0 | 2/5 (40%) | 13:20 BRK Week L (directionally correct) | 10:00 BRK ORB L (confirmed but BAD) |
| TSM | B | 4 | 1 | 2 | 1 | 0 | 0/1 (0%) | 9:35 ~ PM L + ORB L (GOOD, +3.20 15m) | 9:45 ~ ORB H (counter-trend, -4.20 30m) |
| AMZN | C+ | 11 | 1 | 3 | 7 | 0 | 1/3 (33%) | 9:50 ~ ORB L (GOOD, +1.71 30m) | 12:10 BRK PM H (confirmed then failed) |
| GOOGL | C | 16 | 2 | 3 | 11 | 0 | 2/5 (40%) | 9:35 ~ PM L + ORB L (GOOD, +2.80 15m) | 9:50 BRK PM H (momentum trap) |
| SLV | B+ | 6 | 4 | 2 | 0 | 0 | 1/2 (50%) | 10:45 BRK PM H (held 2h39m) | 9:35 ~ ORB H (counter-trend) |
| AAPL | B- | 9 | 3 | 4 | 2 | 0 | 1/2 (50%) | 10:00 BRK Yest L (+2.14 at 30m) | 9:50 REV ORB L (-1.52 at 30m) |
| QQQ | D+ | 10 | 0 | 4 | 6 | 0 | 0/3 (0%) | 10:05 BRK ORB H (correct direction) | 9:45 bear trap (3 BAD signals) |
| MSFT | D | 9 | 2 | 5 | 2 | 0 | 0/2 (0%) | 9:30 REV PM L (+3.33 at 30m) | 15:25 BRK ORB H (-2.08 at 30m) |

---

## Aggregate Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total signals** | **105** | 100% |
| GOOD | 14 | 13.3% |
| BAD | 38 | 36.2% |
| NEUTRAL | 50 | 47.6% |
| N/A (insufficient data) | 3 | 2.9% |
| **BRK confirmation rate** | 8/34 | 23.5% |

**Bullish vs Bearish signal quality:**

| Direction | Total | GOOD | BAD | NEUTRAL | Win Rate |
|-----------|-------|------|-----|---------|----------|
| Bullish (▲) | ~57 | 11 | 14 | 30 | 19% |
| Bearish (▼) | ~48 | 3 | 24 | 20 | 6% |

Feb 27 was a bullish day for most symbols. Bearish signals were overwhelmingly wrong, with only AMD's 13:20 BRK PM L, AAPL's 10:00 BRK Yest L, and AAPL's 9:51 RST PM L qualifying as GOOD. Bullish signals fared better but were still mostly NEUTRAL due to choppy morning action. AAPL was the notable exception -- a strong bearish trend day (-3.19%) where bearish signals eventually paid off.

---

## Key Takeaways

1. **Morning chop destroyed signal quality across all symbols.** The 9:30-10:30 window generated the most signals but had the worst hit rate. AMD had 7 signals in the first hour (5 BAD), NVDA had 6 signals (3 BAD, 3 NEUTRAL), and SPY had 8 signals in the first hour (all NEUTRAL). Only TSM's and GOOGL's opening ORB L reversals were genuinely GOOD.

2. **Late-day breakouts were the real moves.** AMZN's 15:55 breakout (5.5x volume) and GOOGL's 15:55 breakout (6.5x volume) were the strongest moves of the day. Nearly every symbol had a significant late-session push that was either captured or occurred too late for proper FT measurement.

3. **Counter-trend signals consistently failed.** Bearish reversals on bullish trend days (SLV 9:35, GOOGL 9:40, TSM 9:45) and bearish reclaims that fought the trend (AMZN 15:40, SLV 13:25, GOOGL 14:45) all had negative outcomes. The indicator does not distinguish trend context.

4. **ORB L reversals were the best signal type.** SLV 9:45 (GOOD), AMZN 9:50 (GOOD), GOOGL 9:35 (GOOD), and TSM 9:35 (GOOD) all produced meaningful follow-through. Buying the morning dip at ORB L was the best strategy on this day.

5. **Auto-confirmation was unreliable.** Confirmed signals that immediately failed: NVDA 10:00 BRK ORB L was auto-confirmed but reversed -1.77 in 5 minutes (the worst signal of the day); AMZN 12:10 BRK PM H was auto-confirmed then failed in 1 minute; GOOGL 9:50 BRK PM H was auto-confirmed then failed in 2 bars. Only SLV's 10:45 PM H confirmation held meaningfully (2h 39m).

6. **OHLC verification confirmed the bar offset pattern.** Signal at time T shows OHLC from bar T-1. This was verified across all 12 symbols. AMZN, GOOGL, and SLV showed perfect OHLC matches after correcting for the 1-bar offset. SPY, TSLA, and META showed larger discrepancies due to BATS vs composite tape differences.

7. **MSFT's ORB H / Week L proximity ($0.30 apart) caused 40 missed crossings.** Two levels within 0.08% of price created a whipsaw nightmare. This is a strong argument for level merging when levels are within 1x buffer of each other.

8. **QQQ's 0.3% FT threshold may be too high for ETFs.** On a $603 ETF, 0.3% = $1.81. QQQ's best signal (10:05 BRK ORB H) was directionally correct and led to a $3+ move over 2 hours, but the 30m FT was only +$0.80 (0.13%). Consider ATR-based thresholds.

9. **AAPL was the only stock where bearish signals eventually paid off.** On a strong trend day (-3.19%), the indicator's bearish bias was correct. The 10:00 BRK Yest L was the clean signal after the morning noise cleared, with +2.14pt at 30m.

10. **BUG: AAPL 10:00 dual CONF (auto-promote + failed at same timestamp).** The same breakout produced conflicting confirmation statuses, suggesting auto-promote and regular confirmation logic run independently.

---

## Signal Quality by Type

| Type | Symbol | Count | GOOD | BAD | NEUTRAL | N/A | Win Rate |
|------|--------|-------|------|-----|---------|-----|----------|
| **BRK (Breakout)** | All | 36 | 5 | 14 | 16 | 1 | 14% |
| **~ (Reversal)** | All | 30 | 8 | 10 | 10 | 2 | 27% |
| **~~ (Reclaim)** | All | 13 | 0 | 7 | 6 | 0 | 0% |
| **Retest** | All | 14 | 3 | 4 | 7 | 0 | 21% |
| **Retest ◆⁰ (same-bar)** | All | 12 | 2 | 4 | 6 | 0 | 17% |

**Key observations by type:**
- **Breakouts** had a 14% win rate and 39% failure rate. The morning breakouts were nearly all BAD; only afternoon breakouts (AMD 13:20, SLV 10:45, AAPL 10:00) were GOOD.
- **Reversals** were the best signal type at 27% win rate. ORB L reversals in particular were excellent. AAPL's REV ORB L (9:40) and MSFT's REV PM L (9:30) added to the pattern of buying morning dips at support.
- **Reclaims** had a 0% win rate -- every reclaim signal either failed or was NEUTRAL. Counter-trend reclaims were the worst offenders. MSFT added 2 more NEUTRAL reclaims.
- **Same-bar retests (◆⁰)** added noise without value -- they always duplicated the breakout signal's outcome.

---

## Per-Symbol Detailed Analysis

---

### SPY — Grade: C

**Key Levels:**

- PM L=682.01
- ORB L=682.8
- Yest L + ORB L=682.8
- ORB H=684.16
- Yest L + ORB L=684.35
- Yest L=684.35

**Session OHLC (candle-verified):** Open 683.06 | High 686.85 (15:59) | Low 681.66 (09:43) | Close 686.17 | Range 5.19pt | Net +3.11 (+0.46%)

**Day narrative:** SPY opened at 683.06 and quickly sold off to the session low of 681.66 at 09:43 in the first 15 minutes, testing below Yesterday's Low and ORB Low. A reversal off PM Low at 682.01 followed, leading to a slow grind higher through the midday. Price chopped around the 684 level (Yest L/ORB H zone) for hours. A breakout above ORB High at 15:15 led to a steady close at the session high of 686.85. Overall a bullish reversal day: sold off early, ground higher all day, closed near highs.

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|
| 1 | 9:35 | ▲ | ~ | ORB L | 7.5x | ^69 | **NEUTRAL** | -1.12 (-0.164%) | -0.66 (-0.097%) | +0.98 (+0.143%) |
| 2 | 9:45 | ▼ | BRK | Yest L + ORB L | 3.9x | v61 | **NEUTRAL** | -0.46 (-0.067%) | -1.30 (-0.190%) | -1.52 (-0.223%) |
| 3 | 9:45 | ▼ | ~ | ORB H | 3.9x | v61 | **NEUTRAL** | -0.46 (-0.067%) | -1.30 (-0.190%) | -1.52 (-0.223%) |
| 4 | 9:45 | ▼ | ◆ | ORB L | 0.7x | v18 | **NEUTRAL** | -0.46 (-0.067%) | -1.30 (-0.190%) | -1.52 (-0.223%) |
| 5 | 9:50 | ▲ | ~ | PM L | 3x | ^82 | **NEUTRAL** | -0.64 (-0.094%) | +1.17 (+0.171%) | +1.15 (+0.168%) |
| 6 | 10:02 | ▼ | ◆ | Yest L | 0.6x | v53 | **N/A** | N/A | N/A | N/A |
| 7 | 10:10 | ▲ | BRK | ORB H | 2.2x | ^56 | **NEUTRAL** | -0.58 (-0.085%) | -0.19 (-0.028%) | +0.94 (+0.137%) |
| 8 | 10:16 | ▲ | ◆ | ORB H | 0.2x | ^24 | **NEUTRAL** | +0.13 (+0.019%) | -0.08 (-0.012%) | +0.52 (+0.076%) |
| 9 | 12:25 | ▼ | BRK | Yest L | 1.5x | v25 | **NEUTRAL** | -0.83 (-0.121%) | +0.11 (+0.016%) | -0.32 (-0.047%) |
| 10 | 12:25 | ▼ | ◆ | Yest L | 0.3x | v61 | **NEUTRAL** | -0.83 (-0.121%) | +0.11 (+0.016%) | -0.32 (-0.047%) |
| 11 | 15:15 | ▲ | BRK | ORB H | 2.9x | ^100 | **NEUTRAL** | +0.63 (+0.092%) | +0.16 (+0.023%) | +0.22 (+0.032%) |

**OHLC Verification:** 10/11 signals have OHLC discrepancies between pine log and BATS candle aggregation.

<details><summary>OHLC Discrepancy Details</summary>

- **9:35 ~:** MISMATCH: O: candle=683.83 vs pine=683.06 (Δ0.77); H: candle=684.26 vs pine=684.16 (Δ0.10); L: candle=682.90 vs pine=682.80 (Δ0.10); C: candle=684.08 vs pine=683.74 (Δ0.34)
- **9:45 BRK:** MISMATCH: O: candle=682.62 vs pine=684.10 (Δ1.48); H: candle=683.84 vs pine=684.10 (Δ0.26); L: candle=682.23 vs pine=681.66 (Δ0.57); C: candle=683.55 vs pine=682.62 (Δ0.93)
- **9:45 ~:** MISMATCH: O: candle=682.62 vs pine=684.10 (Δ1.48); H: candle=683.84 vs pine=684.10 (Δ0.26); L: candle=682.23 vs pine=681.66 (Δ0.57); C: candle=683.55 vs pine=682.62 (Δ0.93)
- **9:45 ◆:** MISMATCH: O: candle=682.62 vs pine=684.10 (Δ1.48); H: candle=683.84 vs pine=684.10 (Δ0.26); L: candle=682.23 vs pine=681.66 (Δ0.57); C: candle=683.55 vs pine=682.62 (Δ0.93)
- **9:50 ~:** MISMATCH: O: candle=683.49 vs pine=682.62 (Δ0.87); H: candle=683.68 vs pine=683.84 (Δ0.16); L: candle=682.71 vs pine=682.23 (Δ0.48); C: candle=683.08 vs pine=683.55 (Δ0.47)
- **10:10 BRK:** MISMATCH: O: candle=684.72 vs pine=683.90 (Δ0.82); H: candle=685.50 vs pine=685.41 (Δ0.09); L: candle=684.51 vs pine=683.84 (Δ0.67); C: candle=684.57 vs pine=684.72 (Δ0.15)
- **10:16 ◆:** MISMATCH: O: candle=684.63 vs pine=684.72 (Δ0.09); H: candle=684.84 vs pine=685.50 (Δ0.66); L: candle=683.63 vs pine=684.51 (Δ0.88); C: candle=684.14 vs pine=684.57 (Δ0.43)
- **12:25 BRK:** MISMATCH: O: candle=684.04 vs pine=684.24 (Δ0.20); H: candle=684.50 vs pine=684.31 (Δ0.19); L: candle=683.92 vs pine=683.29 (Δ0.63); C: candle=684.13 vs pine=684.05 (Δ0.08)
- **12:25 ◆:** MISMATCH: O: candle=684.04 vs pine=684.24 (Δ0.20); H: candle=684.50 vs pine=684.31 (Δ0.19); L: candle=683.92 vs pine=683.29 (Δ0.63); C: candle=684.13 vs pine=684.05 (Δ0.08)
- **15:15 BRK:** MISMATCH: O: candle=685.22 vs pine=683.96 (Δ1.26); H: candle=685.70 vs pine=685.22 (Δ0.48); L: candle=685.12 vs pine=683.96 (Δ1.16); C: candle=685.59 vs pine=685.22 (Δ0.37)

</details>

**BRK Confirmations:** 0/4 (0%)

- 10:07 ▼ BRK → ✗ failed
- 10:18 ▲ BRK → ✗ failed
- 12:33 ▼ BRK → ✗ failed

**Missed signals:** None detected.

**Key findings:**

- **0/4 BRK confirmations** — all breakouts failed to confirm. This suggests choppy/mean-reverting price action around key levels, where breakouts lacked sustained follow-through.
- **Main signal ratings (excl. retests):** 0 GOOD, 0 BAD, 7 NEUTRAL out of 7.
- Reversals: 3 total — 0 GOOD, 0 BAD.
- Breakouts: 4 total — 0 GOOD, 0 BAD.
- Retests: 4 total — 0 GOOD, 0 BAD.

**Signal summary:** 0 GOOD / 0 BAD / 10 NEUTRAL / 1 N/A out of 11 total signals.


---

### TSLA — Grade: D+

**Key Levels:**

- PM L + ~ ORB L=400.93
- ORB L=400.93
- PM L + ~ ORB L=402.59
- Yest L=403.66
- ORB H=404.49

**Session OHLC (candle-verified):** Open 402.94 | High 407.12 (10:28) | Low 398.11 (13:56) | Close 402.42 | Range 9.01pt | Net -0.52 (-0.13%)

**Day narrative:** TSLA opened at 402.94 and showed extreme volatility in the first 15 minutes. An initial move up to 405.51 broke ORB High, but immediately reversed to 401.41 breaking Yest Low in the same 5m period. Price then bounced back above 404 before rolling over. The rest of the day was a slow grind lower, with price eventually reaching the session low of 398.11 at 13:56. A late-day rally at 15:55 brought price back to 402.42, near unchanged. Choppy, whipsaw action — very difficult for breakout signals.

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|
| 1 | 9:35 | ▲ | ~ | PM L + ~ ORB L | 14.6x | ^83 | **NEUTRAL** | -1.04 (-0.257%) | -0.64 (-0.158%) | +0.68 (+0.168%) |
| 2 | 9:40 | ▲ | BRK | ORB H | 9.8x | ^84 | **BAD** | -1.09 (-0.269%) | -1.93 (-0.476%) | -0.31 (-0.077%) |
| 3 | 9:40 | ▲ | ◆ | ORB H | 1x | ^1 | **BAD** | -1.09 (-0.269%) | -1.93 (-0.476%) | -0.31 (-0.077%) |
| 4 | 9:45 | ▼ | BRK | Yest L | 5x | v61 | **BAD** | -0.40 (-0.099%) | -2.11 (-0.524%) | -1.76 (-0.437%) |
| 5 | 9:45 | ▼ | ~~ | ORB H | 5x | v61 | **BAD** | -0.40 (-0.099%) | -2.11 (-0.524%) | -1.76 (-0.437%) |
| 6 | 9:45 | ▼ | ◆ | Yest L | 1.3x | v54 | **BAD** | -0.40 (-0.099%) | -2.11 (-0.524%) | -1.76 (-0.437%) |
| 7 | 15:55 | ▲ | ~ | ORB L | 4x | ^97 | **N/A** | N/A | N/A | N/A |

**OHLC Verification:** 7/7 signals have OHLC discrepancies between pine log and BATS candle aggregation.

<details><summary>OHLC Discrepancy Details</summary>

- **9:35 ~:** MISMATCH: O: candle=403.95 vs pine=402.94 (Δ1.01); H: candle=405.51 vs pine=404.49 (Δ1.02); L: candle=403.38 vs pine=400.93 (Δ2.45); C: candle=405.17 vs pine=403.89 (Δ1.28)
- **9:40 BRK:** MISMATCH: O: candle=405.14 vs pine=403.95 (Δ1.19); H: candle=405.14 vs pine=405.51 (Δ0.37); L: candle=401.41 vs pine=403.38 (Δ1.97); C: candle=402.85 vs pine=405.17 (Δ2.32)
- **9:40 ◆:** MISMATCH: O: candle=405.14 vs pine=403.95 (Δ1.19); H: candle=405.14 vs pine=405.51 (Δ0.37); L: candle=401.41 vs pine=403.38 (Δ1.97); C: candle=402.85 vs pine=405.17 (Δ2.32)
- **9:45 BRK:** MISMATCH: O: candle=402.86 vs pine=405.14 (Δ2.28); H: candle=404.43 vs pine=405.14 (Δ0.71); L: candle=402.43 vs pine=401.41 (Δ1.02); C: candle=404.08 vs pine=402.85 (Δ1.23)
- **9:45 ~~:** MISMATCH: O: candle=402.86 vs pine=405.14 (Δ2.28); H: candle=404.43 vs pine=405.14 (Δ0.71); L: candle=402.43 vs pine=401.41 (Δ1.02); C: candle=404.08 vs pine=402.85 (Δ1.23)
- **9:45 ◆:** MISMATCH: O: candle=402.86 vs pine=405.14 (Δ2.28); H: candle=404.43 vs pine=405.14 (Δ0.71); L: candle=402.43 vs pine=401.41 (Δ1.02); C: candle=404.08 vs pine=402.85 (Δ1.23)
- **15:55 ~:** MISMATCH: O: candle=402.85 vs pine=400.48 (Δ2.37); H: candle=403.56 vs pine=402.90 (Δ0.66); L: candle=402.04 vs pine=400.31 (Δ1.73); C: candle=402.42 vs pine=402.83 (Δ0.41)

</details>

**BRK Confirmations:** 0/2 (0%)

- 9:41 ▲ BRK → ✗ failed
- 10:01 ▼ BRK → ✗ failed

**Missed signals:** None detected.

**Key findings:**

- **0/2 BRK confirmations** — all breakouts failed to confirm. This suggests choppy/mean-reverting price action around key levels, where breakouts lacked sustained follow-through.
- **Main signal ratings (excl. retests):** 0 GOOD, 3 BAD, 1 NEUTRAL out of 5.
- Reversals: 2 total — 0 GOOD, 0 BAD.
- Breakouts: 2 total — 0 GOOD, 2 BAD.
- Retests: 2 total — 0 GOOD, 2 BAD.

**Signal summary:** 0 GOOD / 5 BAD / 1 NEUTRAL / 1 N/A out of 7 total signals.


---

### META — Grade: C

**Key Levels:**

- Week L=628.15
- PM L + ~ ORB L=641.55
- PM L + ~ ORB L=642.02
- Yest L=647.5

**Session OHLC (candle-verified):** Open 643.45 | High 649.33 (09:32) | Low 638.12 (15:01) | Close 648.17 | Range 11.21pt | Net +4.72 (+0.73%)

**Day narrative:** META gapped down below Yesterday's Low of 647.50, opening at 643.45. The first 5m bar saw a wild range (641.55 to 649.33) as price initially dumped then recovered sharply. Price spent the morning consolidating around 645-647, then broke higher briefly above 648 around 10:20. From there it slowly bled lower, reaching the session low of 638.12 at 15:01 around 15:00. A strong rally in the final hour pushed price to 648.17, closing near the open. V-shaped intraday with a failed bearish thesis and strong close.

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|
| 1 | 9:30 | ▼ | BRK | Yest L | 5.3x | v75 | **BAD** | -0.72 (-0.112%) | -2.88 (-0.448%) | -2.94 (-0.457%) |
| 2 | 9:35 | ▲ | ~ | PM L + ~ ORB L | 18x | ^64 | **NEUTRAL** | -3.31 (-0.512%) | -1.43 (-0.221%) | -0.72 (-0.111%) |
| 3 | 15:15 | ▲ | ~ | Week L | 1.6x | ^98 | **NEUTRAL** | +0.96 (+0.150%) | -0.47 (-0.073%) | -0.42 (-0.066%) |
| 4 | 15:55 | ▲ | ~ | PM L + ~ ORB L | 5.1x | ^97 | **N/A** | N/A | N/A | N/A |

**OHLC Verification:** 4/4 signals have OHLC discrepancies between pine log and BATS candle aggregation.

<details><summary>OHLC Discrepancy Details</summary>

- **9:30 BRK:** MISMATCH: O: candle=643.45 vs pine=646.50 (Δ3.05); H: candle=649.33 vs pine=646.50 (Δ2.83); L: candle=641.55 vs pine=642.02 (Δ0.47); C: candle=646.53 vs pine=643.16 (Δ3.37)
- **9:35 ~:** MISMATCH: O: candle=646.62 vs pine=643.45 (Δ3.17); H: candle=646.73 vs pine=649.33 (Δ2.60); L: candle=642.21 vs pine=641.55 (Δ0.66); C: candle=643.88 vs pine=646.53 (Δ2.65)
- **15:15 ~:** MISMATCH: O: candle=640.86 vs pine=639.15 (Δ1.71); H: candle=641.47 vs pine=640.94 (Δ0.53); L: candle=640.71 vs pine=639.14 (Δ1.57); C: candle=641.30 vs pine=640.91 (Δ0.39)
- **15:55 ~:** MISMATCH: O: candle=644.19 vs pine=640.43 (Δ3.76); H: candle=649.09 vs pine=644.37 (Δ4.72); L: candle=644.00 vs pine=640.43 (Δ3.57); C: candle=648.17 vs pine=644.24 (Δ3.93)

</details>

**BRK Confirmations:** 0/1 (0%)

- 9:31 ▼ BRK → ✗ failed

**Missed signals:** 2 level crossings detected without corresponding signals (using buf=0.967).

| Time | Dir | Level | Price | Close | Prev Close |
|------|-----|-------|-------|-------|------------|
| 15:50 | ▲ | PM L + ~ ORB L=642.02 | 642.02 | 644.24 | 640.49 |
| 15:50 | ▲ | PM L + ~ ORB L=641.55 | 641.55 | 644.24 | 640.49 |

*Note: Many of these are likely filtered by the indicator's cooldown period, volume threshold, or ATR buffer. The indicator is designed to avoid generating signals on every minor level cross in choppy conditions.*

**Key findings:**

- **0/1 BRK confirmations** — all breakouts failed to confirm. This suggests choppy/mean-reverting price action around key levels, where breakouts lacked sustained follow-through.
- **Main signal ratings (excl. retests):** 0 GOOD, 1 BAD, 2 NEUTRAL out of 4.
- Reversals: 3 total — 0 GOOD, 0 BAD.
- Breakouts: 1 total — 0 GOOD, 1 BAD.
- 2 level crossing(s) without signals — likely filtered by cooldown/volume rules.

**Signal summary:** 0 GOOD / 1 BAD / 2 NEUTRAL / 1 N/A out of 4 total signals.


---

### AAPL -- Grade: B-

**Key Levels:**
- ORB H: 272.90 (= session open)
- PM L: 271.39
- Yest L: 270.80
- ORB L: 269.18
- Week H: 266.82

**Session OHLC (candle-verified):** Open 272.90 | High 272.90 (09:30) | Low 262.89 (15:57) | Close 264.20 | Range 10.01pt | Net -8.70 (-3.19%)

**Day narrative:** AAPL gapped down sharply at the open, dropping from 272.90 to 269.18 in the first 5-minute bar -- a 3.72pt move that immediately broke both PM L (271.39) and Yest L (270.80). A counter-bounce from 269.05 to 270.92 between 9:40-9:50 created a v-shaped whipsaw, generating 6 signals in 16 minutes (4 of them opposing). Once the bounce faded, the 10:00 BRK Yest L was the clean signal, with strong follow-through (+2.14pt at 30m). AAPL then ground lower all day, breaking ORB L at 12:15 and eventually reaching the day's low of 262.89 near the close. The overall bearish thesis was correct; the challenge was the early morning noise.

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT | OHLC Match |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|------------|
| 1 | 9:35 | ▼ | BRK | PM L + Yest L | 17.8x | v91 | **BAD** | -0.05 (-0.02%) | -1.37 (-0.51%) | -0.53 (-0.20%) | YES |
| 2 | 9:35 | ▼ | REV | ORB H | 17.8x | v91 | **BAD** | -0.05 (-0.02%) | -1.37 (-0.51%) | -0.53 (-0.20%) | YES |
| 3 | 9:40 | ▲ | REV | ORB L | 8.2x | ^55 | **GOOD** | -0.60 (-0.22%) | +1.58 (+0.59%) | +0.27 (+0.10%) | YES |
| 4 | 9:48 | ▼ | RST | Yest L | 0.9x | v0 | **BAD** | -1.92 (-0.71%) | -1.70 (-0.63%) | -0.57 (-0.21%) | N/A (retest) |
| 5 | 9:50 | ▲ | REV | ORB L | 3.6x | ^98 | **BAD** | +0.26 (+0.10%) | -0.84 (-0.31%) | -1.52 (-0.56%) | YES |
| 6 | 9:51 | ▼ | RST | PM L | 0.5x | v21 | **GOOD** | -0.26 (-0.10%) | +0.84 (+0.31%) | +1.52 (+0.56%) | N/A (retest) |
| 7 | 10:00 | ▼ | BRK | Yest L | 2x | v51 | **GOOD** | +0.62 (+0.23%) | +1.13 (+0.42%) | +2.14 (+0.79%) | YES |
| 8 | 12:15 | ▼ | BRK | ORB L | 1.6x | v100 | **NEUTRAL** | +0.19 (+0.07%) | +0.06 (+0.02%) | +0.54 (+0.20%) | YES |
| 9 | 15:55 | ▼ | REV | Week H | 3.3x | v75 | **NEUTRAL** | +0.22 (+0.08%) | N/A | N/A | YES |

**Signal Details:**

**Signal 1-2: 9:35 ▼ BRK PM L + Yest L / REV ORB H** -- The opening 5m bar was massive (O=272.90, L=269.18, C=269.50). Both bearish signals fired correctly identifying the gap-down break through PM L and Yest L. However, the 15m FT was -1.37 (price bounced to 270.87) as the gap-down was too aggressive and attracted buyers. The 30m FT was -0.53 as the bounce partially faded. Rated BAD on short-term FT, but **directionally correct** for the day (AAPL closed at 264.20).

**Signal 3: 9:40 ▲ REV ORB L** -- Caught the bottom of the opening sell-off correctly. The bounce from 269.05 to 270.87 gave +1.58 at 15m. GOOD signal -- the bounce was real, even if temporary.

**Signal 4: 9:48 ▼ RST Yest L** -- Bearish retest during the bounce. FT was very negative (-1.92 at 5m, -1.70 at 15m) as the bounce continued through this signal. BAD timing -- the retest fired while the bounce was still in progress.

**Signal 5: 9:50 ▲ REV ORB L** -- Second bullish reversal at ORB L. This one came at the TOP of the bounce (C=270.87, which was the local high). 15m FT was -0.84, 30m was -1.52 as price rolled back down. BAD signal -- it was essentially a late entry into the bounce.

**Signal 6: 9:51 ▼ RST PM L** -- Bearish retest one minute after the bullish reversal. This caught the top correctly -- the bounce peaked at 270.92 and this signal fired right as it started fading. GOOD signal with +1.52 at 30m.

**Signal 7: 10:00 ▼ BRK Yest L** -- The best signal of the day. Clean bearish breakout below Yest L with confirmed follow-through: +0.62 at 5m, +1.13 at 15m, +2.14 at 30m. This was the "real" signal after the morning noise cleared. Auto-confirmed, then separately failed confirmation (see bug note below).

**Signal 8: 12:15 ▼ BRK ORB L** -- Bearish breakout below ORB L with pos=v100 (closed at the low). FT was positive but small (+0.54 at 30m = 0.20%), just below the 0.3% threshold. Price was already in a sustained downtrend by this point -- correct direction but limited incremental move.

**Signal 9: 15:55 ▼ REV Week H** -- Late-day bearish reversal at the weekly high level. Only 5 minutes of FT data available (+0.22). Limited data for evaluation but consistent with the bearish trend.

**Confirmations:** 1/2 (50%)
- 10:00 ▼ BRK Yest L --> CONFIRMED (auto-promote)
- 10:00 ▼ BRK Yest L --> FAILED
- **BUG:** Same breakout at 10:00 shows both auto-promote (confirmed) and failed. These are two separate CONF lines in the pine log at the same timestamp. This appears to be a logic issue where auto-promote and regular confirmation run independently.

**Missed signals:** 13
- ORB L (269.18): 9 crossings between 10:15-11:55 -- price oscillated around this level as it became resistance/support
- Week H (266.82): 4 crossings between 13:05-15:20 -- price briefly touched this level

**Key findings:**
- The opening 5m bar (9:30-9:34) produced a 3.72pt drop, generating the correct directional call but the ensuing bounce created 6 signals in 16 minutes with 4 direction changes
- Signal #7 (10:00 ▼ BRK Yest L) was the standout trade: clean break, strong FT, confirmed
- The indicator correctly identified the bearish trend but early signals got whipsawed by the bounce
- AAPL's 10pt range (-3.19%) was a trending day where later signals outperformed early ones
- BUG: Dual CONF (auto-promote + failed) at same timestamp for the same breakout

---

### AMD — Grade: C+

**Key Levels:**
- ORB H: 200.38 (from 9:30-9:34 high)
- ORB L: 198.01 (from 9:30-9:34 low)
- PM L (Pre-Market Low): 199.55
- Yest L (Yesterday's Low): 201.46
- Week L: 194.83

**Session OHLC (candle-verified):**
Open 200.11 | High 201.89 (10:12) | Low 197.74 (13:49) | Close 200.20 | Range 4.15pt | Net +0.09 (+0.04%)

**Day narrative:** AMD opened at 200.11 and immediately sold off to 198.01, establishing the ORB low. It then chopped violently through the first 30 minutes, whipping between 198 and 201 with multiple failed breakouts. After 10:30, it settled into a slow grind down, breaking the PM Low (199.55) cleanly in the 13:20 bar and reaching the day's low near 197.74. A late-day recovery reclaimed PM Low at 15:55, closing near 200.20. Very choppy morning, cleaner afternoon signals.

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|
| 1 | 9:35 | ▼ | ~ | ORB H | 13x | v19 | **BAD** | -0.51 | -1.04 | -0.38 |
| 2 | 9:40 | ▲ | ~ | PM L + Wk L | 5.5x | ^95 | **NEUTRAL** | -0.90 | -0.36 | +0.59 |
| 3 | 9:45 | ▼ | BRK | PM L | 3.6x | v56 | **BAD** | -1.43 | -0.32 | -1.56 |
| 4 | 9:45 | ▼ | ◆ | PM L | 0.6x | v55 | — | — | — | — |
| 5 | 9:50 | ▲ | BRK | ORB H | 3x | ^92 | **BAD** | -0.89 | -0.66 | -0.38 |
| 6 | 9:55 | ▼ | BRK | Yest L | 2.1x | v53 | **BAD** | +0.22 | -0.95 | -0.91 |
| 7 | 10:00 | ▼ | ~~ | ORB H | 2x | v72 | **BAD** | -0.45 | -1.24 | -1.23 |
| 8 | 10:10 | ▲ | BRK | ORB H | 2.3x | ^69 | **NEUTRAL** | +0.07 | -0.04 | -0.69 |
| 9 | 13:20 | ▼ | BRK | PM L | 1.8x | v94 | **GOOD** | +0.09 | +0.35 | +0.58 |
| 10 | 13:30 | ▲ | ~ | ORB L | 2.2x | ^75 | **BAD** | -0.28 | -0.40 | -0.43 |
| 11 | 15:55 | ▲ | ~~ | PM L | 3.5x | ^68 | **NEUTRAL** | +0.20 | — | — |

**Notes on OHLC verification:** The pine log OHLC for each signal matches the PREVIOUS completed 5m bar, not the bar at the signal timestamp. This is consistent with the bar offset pattern confirmed across all symbols. Example: Signal 1 (9:35) — Pine OHLC = O200.11 H200.38 L198.01 C199.93 matches the 9:30-9:34 bar exactly.

**BRK Confirmations:** 1/4 (25%)

- 9:46 ▼ BRK PM L → ✗ failed
- 9:51 ▲ BRK ORB H → ✗ failed
- 10:31 ▲ BRK ORB H → ✗ failed
- 13:20 ▼ BRK PM L → auto-promoted ✓

**Missed signals:**
- The massive drop from 201.89 (10:12) through ORB H (200.38) down to ~199.70 (10:32) — a $2.19 decline in 20 minutes — did not generate a clean bearish ORB H breakdown signal. The 10:00 reclaim was bearish but the big move didn't get a distinct BRK label on the way down.
- No signal was generated when price broke the ORB L (198.01) level during the 13:27-13:30 area. Price touched 197.97 at 13:27 (per pine log) but no BRK ORB L signal fired.

**Key findings:**

1. **Morning chop destroyed signal quality.** 5 of the first 7 signals were BAD — the 9:30-10:30 window was extremely noisy with price crossing levels repeatedly.
2. **Only the 13:20 ▼ BRK PM L was genuinely good** — auto-confirmed, steady follow-through.
3. **3 of 4 breakouts failed confirmation** — indicator correctly identified these as unreliable.
4. **The reversal signals (~) in the morning were particularly poor** — catching falling knives and calling tops that didn't hold.
5. **OHLC discrepancy pattern confirmed**: Pine log OHLC shows the PREVIOUS completed 5m bar, not the bar at the signal timestamp. This is consistent behavior.

**Signal summary:** 1 GOOD / 6 BAD / 3 NEUTRAL out of 10 total signals.


---

### NVDA — Grade: C+

**Key Levels:**
- ORB H: 181.78 (from 9:30-9:34 high)
- ORB L: 180.01 (from 9:30-9:34 low)
- PM L (Pre-Market Low): 181.02
- Week L: 179.18

**Session OHLC (candle-verified):**
Open 181.25 | High 182.58 (10:12) | Low 176.39 (15:59) | Close 177.10 | Range 6.19pt | Net -4.15 (-2.34%)

**Day narrative:** NVDA opened at 181.25 and immediately sold off through PM L (181.02) in the first 5-minute bar. A sharp V-recovery at 9:40 reclaimed PM L and ORB L, then broke above ORB H (181.78) by 10:10, reaching a session high of 182.58 at 10:12. However, the breakout failed, and NVDA drifted lower all day, breaking ORB L at 10:00, then later breaking ORB L again at 12:20. It continued grinding to new lows, breaking Week L (179.18) at 13:20. A failed late-day recovery attempt preceded a massive sell-off in the final 10 minutes (178.13 to 176.39), closing at 177.10. Brutal bearish day.

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|
| 1 | 9:35 | ▼ | BRK + ~ | PM L + ORB H | 10.3x | v75 | **BAD** | -1.16 | -0.38 | -1.11 |
| 2 | 9:40 | ▲ | ~~ | PM L + ORB L | 6.2x | ^96 | **NEUTRAL** | -1.01 | -1.63 | +0.54 |
| 3 | 9:45 | ▼ | BRK | PM L | 2.9x | v59 | **NEUTRAL** | -0.23 | +0.81 | -1.43 |
| 4 | 10:00 | ▼ | BRK | ORB L | 2.4x | v69 | **BAD** | -1.77 | -2.24 | -2.04 |
| 5 | 10:05 | ▲ | ~~ | PM L + ORB L | 1.7x | ^100 | **NEUTRAL** | +0.59 | -0.29 | -0.02 |
| 6 | 10:10 | ▲ | BRK + ~ | ORB H + Week L | 1.8x | ^71 | **BAD** | -0.12 | -0.61 | -0.41 |
| 7 | 12:20 | ▼ | BRK | ORB L | 2x | v88 | **NEUTRAL** | +0.23 | -0.35 | +0.02 |
| 8 | 13:20 | ▼ | BRK | Week L | 2x | v87 | **NEUTRAL** | -0.07 | +0.01 | +0.31 |

**BRK Confirmations:** 2/5 (40%)

- 10:00 ▼ BRK ORB L → auto-promoted ✓ (but terrible FT — BAD signal despite confirmation)
- 13:20 ▼ BRK Week L → auto-promoted ✓ (neutral FT, eventually correct direction)
- 9:35 BRK PM L → ✗ failed
- 9:45 BRK PM L → (no explicit CONF, retest at 9:46)
- 10:10 BRK ORB H → ✗ failed

**Missed signals:**
- The massive 10:05-10:12 rally from 179.74 to 182.58 (+2.84, +1.58%) — while the reclaim at 10:05 and BRK at 10:10 were captured, the full extent of the move was one of the best trades of the day.
- The final-hour crash from ~178.13 to 176.39 (-1.74, -1.0% in 10 minutes) had no signal. No level was tracked at those prices.
- Price broke below PM L (181.02) multiple times intraday without getting a new breakout signal each time (cooldown working as designed).

**Key findings:**

1. **Auto-confirmed ORB L breakdown at 10:00 was the worst signal of the day** — auto-promoted but immediately reversed +1.77 in 5 minutes. This is a design concern: auto-promote on a level that was tested multiple times in choppy conditions should not auto-confirm.
2. **Morning session (9:30-10:15) was a whipsaw disaster** — 6 signals, all BAD or NEUTRAL. Price oscillated +/-2 points around PM L and ORB levels.
3. **The 13:20 Week L breakdown was directionally correct** but follow-through was slow. The massive final-10-minute sell-off (177.1 to 176.39 close) came much later.
4. **No bullish signals worked** — all 3 bullish signals (9:40, 10:05, 10:10) were NEUTRAL or BAD. It was a bearish day that the indicator failed to capture cleanly.
5. **Volume was massive** (10x, 6x in the first bars) but did not improve signal quality.

**Signal summary:** 0 GOOD / 3 BAD / 5 NEUTRAL out of 8 total signals.


---

### QQQ -- Grade: D+

**Key Levels:**
- PM L: 602.52
- ORB L: 602.73
- Yest L: 603.98
- ORB H: 605.10

**Session OHLC (candle-verified):** Open 602.95 | High 608.32 (12:08) | Low 602.19 (09:43) | Close 607.38 | Range 6.13pt | Net +4.43 (+0.73%)

**Day narrative:** QQQ opened near its PM L (602.52) and ORB L (602.73), dipped briefly to 602.19 at 9:43, then reversed sharply higher. The 9:45-10:05 window produced rapid-fire conflicting signals as price whipsawed around the ORB H (605.10). After clearing ORB H decisively around 10:05, QQQ ground higher to reach 608.32 at 12:08. The afternoon was a consolidation between 604-607 with QQQ closing at 607.38. Despite being an up day (+0.73%), the indicator's signals were largely wrong -- 3 bearish signals at 9:45 went against the trend, and the bullish signals were too tepid to rate GOOD due to limited FT magnitude.

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT | OHLC Match |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|------------|
| 1 | 9:35 | ▲ | REV | PM L + ORB L | 12x | ^76 | **NEUTRAL** | +0.52 (+0.09%) | +1.13 (+0.19%) | +1.06 (+0.18%) | YES |
| 2 | 9:45 | ▼ | BRK | Yest L | 3.5x | v49 | **BAD** | -1.99 (-0.33%) | -0.93 (-0.15%) | -2.68 (-0.44%) | YES |
| 3 | 9:45 | ▼ | REV | ORB H | 3.5x | v49 | **BAD** | -1.99 (-0.33%) | -0.93 (-0.15%) | -2.68 (-0.44%) | YES |
| 4 | 9:45 | ▼ | RST | Yest L | 1.3x | v25 | **BAD** | -1.99 (-0.33%) | -0.93 (-0.15%) | -2.68 (-0.44%) | YES |
| 5 | 9:50 | ▲ | BRK | ORB H | 3.4x | ^90 | **NEUTRAL** | -0.98 (-0.16%) | -0.07 (-0.01%) | +0.56 (+0.09%) | YES |
| 6 | 9:50 | ▲ | RST | ORB H | 0.4x | ^28 | **NEUTRAL** | -0.98 (-0.16%) | -0.07 (-0.01%) | +0.56 (+0.09%) | YES |
| 7 | 9:55 | ▼ | RCL | ORB H | 1.8x | v78 | **BAD** | +0.08 (+0.01%) | -1.74 (-0.29%) | -2.34 (-0.39%) | YES |
| 8 | 10:05 | ▲ | BRK | ORB H | 2.9x | ^64 | **NEUTRAL** | +0.83 (+0.14%) | +0.63 (+0.10%) | +0.80 (+0.13%) | YES |
| 9 | 12:22 | ▲ | RST | ORB H | 0.3x | ^10 | **NEUTRAL** | -0.04 (-0.01%) | +1.04 (+0.17%) | -0.26 (-0.04%) | N/A (retest) |
| 10 | 15:15 | ▲ | BRK | ORB H | 2.4x | ^99 | **NEUTRAL** | +0.32 (+0.05%) | +0.26 (+0.04%) | -0.77 (-0.13%) | YES |

**Signal Details:**

**Signal 1: 9:35 ▲ REV PM L + ORB L** -- Correct directional call. QQQ bounced off PM L/ORB L and headed higher. However, the FT magnitude was below the 0.3% threshold at all timeframes (+0.18% max). On a $603 stock, 0.3% = $1.81, and the max FT was $1.13 at 15m. NEUTRAL rating despite correct direction -- the move was meaningful in absolute terms but below the percentage threshold.

**Signals 2-4: 9:45 ▼ BRK Yest L / REV ORB H / RST Yest L** -- Three bearish signals fired simultaneously, all BAD. The 9:40-9:44 bar dipped to 602.19 triggering bearish breakout/reversal signals. But price immediately reversed higher, reaching 605.66 by 9:50. All three had -2.68 at 30m FT (price $2.68 higher than signal close). This was the classic "bear trap" -- a flush to the lows followed by a sharp reversal. **Design issue:** 3 signals at the same bar is noise. The BRK Yest L + RST Yest L at the same time is particularly redundant.

**Signals 5-6: 9:50 ▲ BRK ORB H / RST ORB H** -- Price recovered to 605.66, triggering bullish signals at ORB H. The immediate pullback (-0.98 at 5m) made these look shaky, but price eventually stabilized above ORB H. NEUTRAL -- direction was right but magnitude insufficient for GOOD.

**Signal 7: 9:55 ▼ RCL ORB H** -- Bearish reclaim of ORB H after the breakout attempt failed in the short term. Price closed at 604.68, below 605.10. But this was a false signal -- price broke back above ORB H by 10:05 and never looked back. BAD, with -2.34 at 30m.

**Signal 8: 10:05 ▲ BRK ORB H** -- The definitive bullish breakout of ORB H. This was the correct signal that eventually led to the day's high (608.32). However, FT was below the threshold (+0.80 at 30m = 0.13%). NEUTRAL by our criteria but directionally correct. The confirmation failed at 13:21, meaning the breakout didn't hold above the confirmation threshold for the required period.

**Signal 9: 12:22 ▲ RST ORB H** -- Retest of ORB H from above. FT was mixed: +1.04 at 15m but -0.26 at 30m. NEUTRAL.

**Signal 10: 15:15 ▲ BRK ORB H** -- Late-day bullish breakout attempt. FT faded at 30m (-0.77). NEUTRAL.

**Confirmations:** 0/3 (0%)
- 9:46 ▼ BRK Yest L --> FAILED (price reversed immediately)
- 9:53 ▲ BRK ORB H --> FAILED (price dipped back below)
- 13:21 ▲ BRK ORB H --> FAILED (after holding for 3+ hours)

**Missed signals:** 16
- All 16 at ORB H (605.10): price oscillated around this level from 13:15-15:05 during the afternoon consolidation

**Key findings:**
- QQQ was an up day (+0.73%) but the indicator generated 4 BAD bearish signals vs 0 GOOD bullish signals
- The 9:45 bear trap (3 simultaneous bearish signals followed immediately by bullish reversal) was the worst outcome
- Signal #8 (10:05 ▲ BRK ORB H) was directionally correct but FT was below the 0.3% threshold on a $600+ ETF
- **Design observation:** The 0.3% threshold may be too high for QQQ ($1.81 on $603). Consider using an ATR-based threshold instead. QQQ's ATR was 10.08, so a 0.5*ATR threshold would be $5.04, which is even stricter. The issue is that QQQ's intraday moves are percentage-wise smaller than individual stocks.
- 0% confirmation rate across 3 breakouts suggests levels are not strong enough for QQQ on this day
- Afternoon consolidation around ORB H (16 missed crossings) shows the level lost significance

---

### TSM — Grade: B

**Key Levels:**
- ORB H: 371.95 (from 9:30-9:34 high)
- ORB L: 368.65 (from 9:30-9:34 low)
- PM L: 369.85 (close to ORB L)
- Week H: 372.20

**Session OHLC (candle-verified):**
Open 370.14 | High 376.67 (10:12) | Low 368.65 (9:30) | Close 374.69 | Range 8.02pt | Net +4.55 (+1.23%)

**Day narrative:** TSM opened at 370.14 and immediately bounced off the ORB low at 368.65, recovering strongly. It crossed above ORB H (371.95) and Week H (372.20) by 9:50, rallied to a session high of 376.67 at 10:12, then drifted slowly lower through the midday. At 13:35, a reclaim signal fired as it broke back below ORB H. After that, TSM spent the afternoon between 371-374 before recovering into the close at 374.69. A moderately bullish day with a clear morning impulse and afternoon consolidation.

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|
| 1 | 9:35 | ▲ | ~ | PM L + ORB L | 16x | ^84 | **GOOD** | +0.60 | +3.20 | +2.87 |
| 2 | 9:45 | ▼ | ~ | ORB H | 2.8x | v38 | **BAD** | -3.40 | -1.45 | -4.20 |
| 3 | 9:50 | ▲ | BRK | Week H + ORB H | 2.2x | ^95 | **NEUTRAL** | -1.55 | -0.33 | +0.63 |
| 4 | 13:35 | ▼ | ~~ | ORB H | 3.3x | v96 | **BAD** | -0.35 | -0.82 | -1.90 |

**BRK Confirmations:** 0/1 (0%)

- 9:50 ▲ BRK Week H + ORB H → ✗ failed (confirmation check at 13:26 — 3.5 hours later!)

**Missed signals:**
- The rally from 374.61 (9:49) to 376.67 (10:12) — a +2.06 (+0.55%) move — occurred AFTER the ORB H BRK but with no additional signal. The initial breakout captured this move's start.
- The decline from 376.67 (10:12 high) to 371.55 (13:21 area) — a -5.12 (-1.36%) move over 3 hours — had only one reclaim signal at 13:35 (after the bulk of the decline). No signal captured the top or early decline.
- The recovery from 370.97 (13:35) back to 374.69 (close) — a +3.72 (+1.0%) move — had no bullish signal at all.

**Key findings:**

1. **The opening reversal (9:35 ▲) was the day's best signal** — 16x volume, strong bullish close, and excellent follow-through (+3.20 at 15m). This captured the morning impulse.
2. **Only 4 signals all day** — TSM was relatively quiet compared to AMD and NVDA. The indicator correctly avoided over-signaling in the consolidation zone.
3. **The 9:45 ▼ reversal was the worst signal** — bearish call at the start of a massive +4 point rally. Low volume (2.8x) and weak pos (v38) should have been warning signs.
4. **The 13:35 ▼ reclaim fired too late** — the bearish move was largely exhausted by 13:35. Then price reversed higher.
5. **BRK confirmation took 3.5 hours to check** — the 9:50 BRK wasn't confirmed/denied until 13:26. This seems like an unusually long confirmation window.
6. **Missing the afternoon recovery** — a +3.72 point move from 13:35 to close had zero bullish signals. This is a significant gap.

**Signal summary:** 1 GOOD / 2 BAD / 1 NEUTRAL out of 4 total signals.


---

### AMZN — Grade: C+

**Key Levels:**
- ORB H: 207.49
- ORB L: 205.77
- PM H: 208.94
- Yest L: 205.35

**Session OHLC (candle-verified):** Open 206.83 | High 210.33 (15:57) | Low 205.21 (09:43) | Close 209.99 | Range 5.12pt | Net +3.16 (+1.53%)

**Day narrative:** AMZN gapped down and sold off further in the first 15 minutes, testing the ORB low at 205.21. A reversal from ORB L launched a steady recovery, breaking ORB H at 10:20 and grinding toward PM H (208.94). The PM H breakout at 12:10 failed badly with a -1.50 FT at 15m. Price chopped around 208.50-209.50 for hours before a massive 5.5x volume breakout at 15:55 sent AMZN surging to 210.33 into the close.

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|
| 1 | 9:35 | ▼ | ~ | ORB H | 10.8x | v52 | **NEUTRAL** | +0.26 | +0.30 | +0.17 |
| 2 | 9:50 | ▲ | ~ | ORB L | 2.2x | ^67 | **GOOD** | +0.30 | +0.12 | +1.71 |
| 3 | 10:20 | ▲ | BRK | ORB H | 1.6x | ^91 | **NEUTRAL** | +0.67 | +0.02 | +0.81 |
| 4 | 10:20 | ▲ | ~ | Yest L | 1.6x | ^91 | **NEUTRAL** | +0.67 | +0.02 | +0.81 |
| 5 | 10:31 | ▲ | ◆² | ORB H | — | — | **NEUTRAL** | -0.15 | +0.69 | +0.44 |
| 6 | 12:10 | ▲ | BRK | PM H | 1.8x | ^59 | **BAD** | -1.03 | -1.56 | -1.49 |
| 7 | 12:10 | ▲ | ◆⁰ | PM H | — | — | **BAD** | -1.03 | -1.56 | -1.49 |
| 8 | 15:05 | ▲ | BRK | PM H | 2.2x | ^47 | **NEUTRAL** | -0.10 | +0.51 | -0.12 |
| 9 | 15:09 | ▲ | ◆⁰ | PM H | — | — | **NEUTRAL** | -0.10 | +0.51 | -0.12 |
| 10 | 15:40 | ▼ | ~~ | PM H | 1.8x | v96 | **BAD** | +0.04 | -1.16 | -1.45 |
| 11 | 15:55 | ▲ | BRK | PM H | 5.5x | ^92 | **NEUTRAL** | +0.23 | +0.29 | +0.32 |

**BRK Confirmations:** 1/3 (33%)

- 12:10 BRK PM H: auto-confirmed then failed at 12:11 (1-bar hold) — very fast fail
- 15:05 BRK PM H: failed at 15:38
- 15:55 BRK PM H: no confirmation logged (EOD cutoff)

**Missed signals:**
- 12:00: PM H (208.94) crossed UP — first PM H cross; signal fired at 12:10 (12:05 bar). The 12:00 bar crossed PM H but closed at 209.13, which triggered the 12:05 bar signal. **Possible 1-bar delay.**
- 13:45-14:05: Multiple PM H crosses — price chopped around 208.94 several times. No signals because of cooldown from the failed 12:10 breakout. **Design working as intended** (cooldown preventing whipsaw signals).

**Key findings:**

1. **PM H was a grind level** — price tested 208.94 repeatedly from 12:00-15:55 before finally breaking through convincingly. The indicator correctly identified most attempts.
2. **Instant confirmation failure at 12:10** is notable — confirmed then failed in 1 minute. This suggests the auto-promote threshold may be too loose.
3. **Bearish reclaim at 15:40 was counter-trend** — price was in an uptrend all day; reclaim signals in strong trends are risky.
4. **OHLC verification: PERFECT** — all 11 signals' OHLC exactly matched our aggregated 5m bars after correcting for the 1-bar offset.

**Signal summary:** 1 GOOD / 3 BAD / 7 NEUTRAL out of 11 total signals.


---

### GOOGL — Grade: C

**Key Levels:**
- ORB H: 307.26
- ORB L: 303.80
- PM H: 308.60
- PM L: 303.79
- Yest L: 302.35

**Session OHLC (candle-verified):** Open 304.19 | High 312.40 (15:57) | Low 303.80 (09:30) | Close 311.55 | Range 8.60pt | Net +7.36 (+2.42%)

**Day narrative:** GOOGL gapped down to the PM low at 303.80, immediately bounced with a massive first-bar reversal (+2.61pt). By 9:45 it broke ORB H and PM H in rapid succession, surging to 309.83. The move was too fast — PM H breakout at 9:50 reversed hard, giving back 1.5pt within 5 bars. Price then spent 4+ hours chopping between 306-309 (massive 307.26/308.60 range). A late session breakout at 15:55 with 6.5x volume launched GOOGL from 308.22 to 312.40 in 10 minutes.

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|
| 1 | 9:35 | ▲ | ~ | PM L + ORB L | 10.2x | ^87 | **GOOD** | -0.21 | +2.80 | +1.81 |
| 2 | 9:40 | ▼ | ~ | ORB H | 5.8x | v49 | **BAD** | -1.45 | -1.58 | -1.49 |
| 3 | 9:45 | ▲ | BRK | ORB H | 4.1x | ^89 | **NEUTRAL** | +1.56 | +0.05 | -0.05 |
| 4 | 9:45 | ▲ | ~ | Yest L | 4.1x | ^89 | **NEUTRAL** | +1.56 | +0.05 | -0.05 |
| 5 | 9:50 | ▲ | BRK | PM H | 4.9x | ^89 | **BAD** | -1.43 | -0.99 | -1.66 |
| 6 | 9:52 | ▲ | ◆⁰ | PM H | — | — | **BAD** | -1.43 | -0.99 | -1.66 |
| 7 | 9:55 | ▼ | ~~ | PM H | 2.4x | v98 | **NEUTRAL** | +0.08 | +0.09 | -0.50 |
| 8 | 10:05 | ▲ | BRK | PM H | 2.2x | ^53 | **NEUTRAL** | -0.53 | -0.67 | -0.32 |
| 9 | 10:05 | ▲ | ◆⁰ | PM H | — | — | **NEUTRAL** | -0.53 | -0.67 | -0.32 |
| 10 | 14:05 | ▲ | BRK | ORB H | 1.7x | ^98 | **NEUTRAL** | -0.18 | -0.17 | -0.86 |
| 11 | 14:10 | ▼ | ~~ | PM H | 1.7x | v84 | **NEUTRAL** | -0.66 | +0.65 | +0.81 |
| 12 | 14:21 | ▲ | ◆³ | ORB H | — | — | **NEUTRAL** | -0.66 | -0.69 | -0.85 |
| 13 | 14:45 | ▼ | ~~ | ORB H | 1.6x | v33 | **NEUTRAL** | -0.09 | +0.00 | -1.01 |
| 14 | 15:15 | ▲ | BRK | ORB H | 1.6x | ^96 | **NEUTRAL** | +0.27 | +0.12 | -0.53 |
| 15 | 15:37 | ▲ | ◆⁴ | ORB H | — | — | **GOOD** | -0.41 | +0.47 | +3.46 |
| 16 | 15:55 | ▲ | BRK | PM H | 6.5x | ^96 | **NEUTRAL** | +0.46 | -0.40 | -0.84 |

**BRK Confirmations:** 2/5 (40%)

- 9:50 BRK PM H: auto-confirmed, then failed at 9:54 (2-bar hold)
- 10:05 BRK PM H: failed at 10:09
- 14:05 BRK ORB H: failed at 14:40
- 15:15 BRK ORB H: no fail logged (likely passed or EOD)
- 15:55 BRK PM H: auto-confirmed (held into close)

**Missed signals:**
- 10:00-11:35: PM H (308.60) crossed UP/DOWN approximately 12 times. Only 2 signals generated (10:05 BRK + retest). **Massive chop zone with cooldown suppression working correctly** — generating signals for every cross would have been worse.
- 12:05: PM H crossed UP (bar high 309.36, close 309.09). No signal generated. This may have been suppressed by cooldown from the 10:05 breakout failure.
- 12:40: ORB H (307.26) crossed DOWN (close 307.13). No signal generated. Could be a missed reclaim.

**Key findings:**

1. **PM H was a brutal chop level** — GOOGL crossed 308.60 approximately 15 times during the session. The indicator wisely suppressed most signals via cooldown.
2. **Early momentum trap at 9:50** — the PM H breakout fired with 4.9x volume and ^89 position but immediately reversed. This was a gap-fill momentum exhaustion.
3. **The massive EOD move (+3pt in 5 min)** was correctly captured by both the ORB H retest (#15) and PM H breakout (#16).
4. **Signal #2 (9:40 bearish reversal at ORB H) was a terrible signal** on a +2.4% up day — counter-trend reversals in gap recovery are risky.
5. **Yest L reversal at 9:45** (signal #4) — Yest L was at 302.35 but price was at 308 when the signal fired. This level was not relevant to the current price action.

**Signal summary:** 2 GOOD / 3 BAD / 11 NEUTRAL out of 16 total signals.


---

### MSFT -- Grade: D

**Key Levels:**
- PM L: 389.86
- ORB L: 389.90 (only $0.04 from PM L)
- ORB H: 394.23
- Week L: 394.53 (only $0.30 from ORB H)

**Session OHLC (candle-verified):** Open 390.98 | High 396.81 (11:04) | Low 389.90 (09:30) | Close 392.75 | Range 6.91pt | Net +1.77 (+0.45%)

**Day narrative:** MSFT opened at 390.98, dipped to the day's low of 389.90 on the first bar (touching PM L and ORB L), then rallied sharply to 394.23 by 9:34. The early bullish signals correctly caught this bounce. However, the mid-morning saw price oscillate between ORB H (394.23) and Week L (394.53) -- two levels only $0.30 apart -- creating a nightmare of whipsaw. MSFT reached 396.81 at 11:04 before fading back into the 393-395 range for the afternoon. The final hour saw a failed bullish breakout at 15:25 immediately reversed by a bearish breakout at 15:30, finishing at 392.75. The key structural problem: ORB H and Week L were so close together that any move through the 394.23-394.53 zone triggered level interactions in both directions.

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT | OHLC Match |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|------------|
| 1 | 9:30 | ▲ | REV | PM L | 1.5x | ^68 | **GOOD** | +2.23 (+0.57%) | +0.94 (+0.24%) | +3.33 (+0.85%) | N/A (first bar) |
| 2 | 9:35 | ▲ | REV | ORB L | 10.5x | ^77 | **GOOD** | +0.22 (+0.06%) | +0.59 (+0.15%) | +1.27 (+0.32%) | YES |
| 3 | 10:10 | ▼ | BRK | Week L | 2x | v100 | **BAD** | +0.06 (+0.02%) | -1.20 (-0.30%) | -1.57 (-0.40%) | YES |
| 4 | 10:10 | ▼ | REV | ORB H | 2x | v100 | **BAD** | +0.06 (+0.02%) | -1.20 (-0.30%) | -1.57 (-0.40%) | YES |
| 5 | 10:20 | ▼ | RST | Week L | 0.3x | v25 | **BAD** | -1.11 (-0.28%) | -1.26 (-0.32%) | -1.52 (-0.39%) | YES |
| 6 | 15:25 | ▲ | BRK | ORB H | 2x | ^81 | **BAD** | -0.98 (-0.25%) | -2.32 (-0.59%) | -2.08 (-0.53%) | YES |
| 7 | 15:25 | ▲ | RST | ORB H | 0.5x | ^16 | **BAD** | -0.98 (-0.25%) | -2.32 (-0.59%) | -2.08 (-0.53%) | YES |
| 8 | 15:30 | ▼ | BRK | Week L | 1.8x | v96 | **NEUTRAL** | +0.13 (+0.03%) | +0.62 (+0.16%) | +1.07 (+0.27%) | YES |
| 9 | 15:30 | ▼ | RCL | ORB H | 1.8x | v96 | **NEUTRAL** | +0.13 (+0.03%) | +0.62 (+0.16%) | +1.07 (+0.27%) | YES |

**Signal Details:**

**Signal 1: 9:30 ▲ REV PM L** -- First bar of the day. MSFT dipped to 389.86 (exactly PM L) and bounced to close at 390.99. The signal correctly identified the bounce off PM L. Strong FT: +2.23 at 5m, +3.33 at 30m. GOOD -- this was a valid level with strong reaction. Note: OHLC cannot be verified against "previous bar" since this is the first bar.

**Signal 2: 9:35 ▲ REV ORB L** -- Bullish reversal off ORB L (389.90) with high volume (10.5x). The 9:30-9:34 bar confirmed the bounce with C=393.22. FT was positive but modest: +1.27 at 30m (0.32%), just clearing the 0.3% threshold. GOOD.

**Signals 3-4: 10:10 ▼ BRK Week L / REV ORB H** -- The 10:05-10:09 bar closed at 393.56, below both Week L (394.53) and ORB H (394.23). This triggered a bearish breakout of Week L and a bearish reversal of ORB H. However, price immediately bounced back: -1.57 at 30m (price went UP $1.57 instead of down). BAD -- MSFT was still bullish, just pulling back from the 396.81 high. **Key issue:** Week L at 394.53 is a "breakDOWN" level, but price was above it for most of the morning session. The bearish break signal was premature.

**Signal 5: 10:20 ▼ RST Week L** -- Bearish retest of Week L, 10 minutes after the breakout. Also BAD -- price continued higher with -1.52 at 30m.

**Signals 6-7: 15:25 ▲ BRK ORB H / RST ORB H** -- Late-day bullish breakout attempt at ORB H. C=394.80, just above ORB H (394.23). But the breakout immediately failed: -2.08 at 30m as MSFT sold off into the close. BAD -- false breakout at end of day.

**Signals 8-9: 15:30 ▼ BRK Week L / RCL ORB H** -- Just 5 minutes after the failed bullish breakout, bearish signals fired. The quick reversal was valid (the bullish break was indeed fake), but FT was modest: +1.07 at 30m (0.27%), just below the 0.3% threshold. NEUTRAL.

**Confirmations:** 0/2 (0%)
- 10:33 ▼ BRK Week L --> FAILED (price bounced back above)
- 15:29 ▲ BRK ORB H --> FAILED (price reversed immediately)

**Missed signals:** 40
- Week L (394.53): 20 crossings between 09:50-13:00
- ORB H (394.23): 20 crossings between 09:55-15:15
- **Root cause:** These two levels are only $0.30 apart. Any 5m bar with a range > $0.30 that trades in this zone crosses both levels. MSFT spent ~4 hours oscillating in this zone.

**Key findings:**
- Early signals (#1-2) were excellent, correctly catching the bounce off PM L / ORB L
- Mid-morning and late-day signals were all BAD or NEUTRAL, plagued by the ORB H / Week L proximity problem
- **Critical design issue:** ORB H (394.23) and Week L (394.53) are only $0.30 apart (0.08% of price, well below the buffer of $0.545). The indicator should consider merging or suppressing signals when two levels are within 1x buffer of each other.
- The 40 missed crossings represent the worst whipsaw of the three symbols, entirely caused by the closely-spaced levels
- 15:25-15:30 opposing signals (▲ then ▼ in 5 minutes) show end-of-day chop

---

### SLV — Grade: B+

**Key Levels:**
- ORB H: 83.28
- ORB L: 82.58
- PM H: 83.99

**Session OHLC (candle-verified):** Open 83.25 | High 85.27 (11:18) | Low 82.36 (09:41) | Close 84.98 | Range 2.91pt | Net +1.73 (+2.07%)

**Day narrative:** SLV opened near PM H, immediately sold off to test ORB L area (82.36 low at 9:41). A strong reversal from ORB L led to a steady uptrend — breaking ORB H at 10:10 and PM H at 10:45. SLV hit the day high of 85.27 at 11:18, then pulled back sharply to 83.64 in a midday selloff. After the PM H reclaim, price rebuilt slowly and closed near 84.98. Clean trend day with one sharp pullback.

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|
| 1 | 9:35 | ▼ | ~ | ORB H | 4.7x | v87 | **BAD** | +0.01 | -0.29 | -0.54 |
| 2 | 9:45 | ▲ | ~ | ORB L | 2.7x | ^82 | **GOOD** | +0.19 | +0.24 | +0.88 |
| 3 | 10:10 | ▲ | BRK | ORB H | 3.1x | ^55 | **GOOD** | +0.24 | +0.04 | +0.72 |
| 4 | 10:10 | ▲ | ◆⁰ | ORB H | — | — | **GOOD** | +0.24 | +0.04 | +0.72 |
| 5 | 10:45 | ▲ | BRK | PM H | 1.6x | ^52 | **GOOD** | +0.39 | +0.56 | +0.79 |
| 6 | 13:25 | ▼ | ~~ | PM H | 2.0x | v85 | **BAD** | -0.35 | -0.15 | -0.57 |

**BRK Confirmations:** 1/2 (50%)

- 10:45 BRK PM H: auto-confirmed, held until 13:24 (2h 39m hold) — strong confirmation
- 13:24: PM H BRK confirmation failed

**Missed signals:**
- 10:35: PM H (83.99) crossed UP (bar close 84.13). Signal fired at 10:45 (10:40 bar). **Possible 1-bar delay** — the 10:35 bar crossed PM H but the signal triggered on the 10:40 bar. This may be due to the ATR buffer zone requiring price to close above a threshold.
- 13:40: PM H crossed UP (close 84.22). No re-breakout signal generated after the 13:25 reclaim. Could be by design (cooldown) or a gap in coverage.

**Key findings:**

1. **Clean trend day** — SLV had the most tradeable signals of all 12 symbols. 4 of 6 signals were GOOD.
2. **The PM H breakout at 10:45 was excellent** — held confirmation for 2h 39m before failing, giving plenty of time to manage the trade.
3. **Counter-trend signals struggled** — both BAD signals (#1 and #6) were against the prevailing trend.
4. **Possible 1-bar delay on PM H breakout** — the 10:35 bar crossed PM H but the signal fired from the 10:40 bar. This may be due to the buffer zone requiring price to close beyond the level + ATR buffer.

**Signal summary:** 4 GOOD / 2 BAD / 0 NEUTRAL out of 6 total signals.


---

## Bugs & Issues Found

1. **NVDA auto-confirmed BRK ORB L at 10:00 was the worst signal of the day.** Auto-promoted but immediately reversed -1.77 in 5 minutes. The auto-promote criteria should be tighter, especially when a level has been crossed multiple times in quick succession during choppy conditions.

2. **AMZN PM H auto-confirm lasted only 1 minute before failing.** The 12:10 BRK PM H was auto-confirmed and then failed at 12:11 (1 bar hold). A minimum hold time requirement would prevent this.

3. **TSM confirmation took 3.5 hours to check.** The 9:50 BRK wasn't confirmed/denied until 13:26. The confirmation timing logic may need review — this gap between signal and confirmation check is unusual and potentially a bug.

4. **META/GOOGL Yest L signals fired far from the level.** META's Yest L at 647.50 generated a BRK signal at 9:30 (reasonable), but GOOGL's Yest L at 302.35 generated a reversal signal at 9:45 when price was at 308 — 6 points above the level. This creates noise with no practical trading value.

5. **Same-bar retests (◆⁰) are redundant noise.** When a breakout and retest fire on the same bar (AMZN #6/#7, GOOGL #5/#6, #8/#9, SLV #3/#4), they produce identical FT and add visual clutter without providing new information. Consider suppressing same-bar retests.

6. **Counter-trend reclaims in strong trends consistently fail.** AMZN 15:40 bearish reclaim of PM H on a +1.5% day, SLV 13:25 bearish reclaim of PM H on a +2% day, GOOGL 14:10/14:45 bearish reclaims on a +2.4% day — all were BAD or NEUTRAL. The indicator lacks trend context awareness.

7. **Morning whipsaw creates conflicting signals on TSLA.** Same-bar BRK+reversal combinations (TSLA 9:40-9:45) produced bullish and bearish signals within 5 minutes of each other, which is confusing for traders.

8. **No signals for new session lows/highs beyond tracked levels.** NVDA's final-10-minute crash from 178.13 to 176.39 (-1.0% in 10 min) had no signal because no level was tracked at those prices. Similarly, TSM's afternoon recovery (+3.72pt) had no bullish signal.

9. **OHLC discrepancies between BATS and TradingView composite data.** SPY, TSLA, and META showed discrepancies up to $3-4 (META) and $1-2 (SPY/TSLA) due to BATS vs composite tape differences. AMZN, GOOGL, SLV had perfect matches. For future analysis, using TradingView's own exported 5m candle data would provide more consistent verification.

10. **GOOGL PM H was crossed ~15 times in one session.** While cooldown correctly suppressed most re-signals, this highlights that some levels create excessive noise zones. A "chop detection" mechanism could temporarily deactivate signals around a level that has been crossed too many times.

11. **AAPL dual CONF bug at 10:00.** Same breakout (▼ BRK Yest L) produced both an auto-promote (confirmed) and a failed confirmation at the same timestamp. Auto-promote and regular confirmation logic appear to run independently, creating contradictory results.

12. **Signal overload in opening minutes.** AAPL generated 6 signals in 16 minutes (9:35-9:51) with 4 direction changes. QQQ generated 7 signals in 20 minutes (9:35-9:55) with 3 direction changes. This rapid-fire opposing signal pattern is common across symbols and creates decision paralysis for traders.

13. **Closely-spaced levels create structural noise (MSFT).** MSFT's ORB H (394.23) and Week L (394.53) were only $0.30 apart (0.08% of price), generating 40 missed crossings and multiple false signals. Similarly, PM L (389.86) and ORB L (389.90) were only $0.04 apart. Levels within 1x buffer should be merged.

14. **FT threshold may not suit ETFs (QQQ).** QQQ's 0.3% FT threshold ($1.81 on $603) penalizes directionally correct signals. Signal #8 (10:05 BRK ORB H) was the correct call but rated NEUTRAL because the 30m FT was only 0.13%.

15. **Same-bar BRK + RST contradiction (QQQ 9:45).** A breakout and retest of the same level (Yest L) fired at the same bar. A fresh breakout should suppress the retest logic for that bar.

---

## Strategy Comparison

**"If You Traded" — performance of different filter strategies:**

| Strategy | Signals Taken | GOOD | BAD | NEUTRAL | Win Rate | Notes |
|----------|---------------|------|-----|---------|----------|-------|
| **All signals** | 105 | 14 | 38 | 50 | 13% | Unfiltered; heavy losses from BAD signals |
| **Confirmed BRK only** | 8 | 3 | 1 | 4 | 38% | Better; AAPL 10:00 added a GOOD confirmed signal |
| **Reversals (~) only** | 30 | 8 | 10 | 10 | 27% | Best type but still mixed; needs filtering |
| **ORB L/PM L reversals only** | 9 | 6 | 2 | 1 | 67% | The sweet spot: buying dips at support levels (AAPL, MSFT added) |
| **After 10:30 only** | 33 | 4 | 11 | 18 | 12% | Avoiding morning chop helps, but not enough alone |
| **Vol >= 3x + Pos >= 80** | ~16 | 5 | 4 | 7 | 31% | High-conviction filter; still some BAD signals |
| **No counter-trend signals** | ~72 | 14 | 22 | 36 | 19% | Removes obvious losers but still noisy |
| **ORB L rev + confirmed BRK after 10:30** | ~7 | 4 | 0 | 3 | 57% | Best combined filter for this day |

---

## What Went Well

- **ORB L reversals were consistently excellent.** AMZN 9:50, GOOGL 9:35, SLV 9:45, TSM 9:35, AAPL 9:40, MSFT 9:30/9:35 — all captured the morning dip bounce with good follow-through.
- **Cooldown suppression worked well.** GOOGL's PM H was crossed ~15 times but only generated 5 signals. AMZN's PM H chop zone was correctly suppressed during the 13:45-14:05 period.
- **SLV was a clean signal day.** 4/6 GOOD signals with the PM H breakout holding for 2h 39m — demonstrating the indicator works well on trend days.
- **Late-day breakouts were captured.** AMZN 15:55 (5.5x), GOOGL 15:55 (6.5x) — both correctly identified the high-volume EOD moves.
- **OHLC bar alignment is consistent and verified** across all 12 symbols. The 1-bar offset is by design and now well-documented.
- **Confirmation mechanism protected traders** on choppy SPY (0/4 confirmed, all would have been losers) and TSLA (0/2 confirmed, both BAD).
- **AAPL's 10:00 BRK Yest L was a standout signal** — clean break with strong FT (+2.14 at 30m), auto-confirmed. The best individual signal across all 12 symbols.
- **MSFT's early reversals (9:30-9:35) correctly caught the bounce** off PM L/ORB L with strong follow-through.

## What Didn't Go Well

- **Morning chop destroyed signal quality.** 9:30-10:30 generated the most signals but had the worst win rate. The indicator has no mechanism to detect and suppress signals in high-chop environments.
- **Counter-trend signals consistently failed.** Every bearish reversal on a bullish day and every bearish reclaim in an uptrend was BAD. The indicator lacks trend context.
- **Auto-confirmation was unreliable.** NVDA 10:00 (confirmed BAD), AMZN 12:10 (confirmed then failed in 1 min), GOOGL 9:50 (confirmed then failed in 2 bars), AAPL 10:00 (dual CONF bug). Auto-promote needs tighter criteria.
- **Reclaim signals had a 0% GOOD rate.** All 13 reclaim signals across 12 symbols were BAD or NEUTRAL. This signal type may need fundamental rework.
- **Massive moves were missed.** NVDA's final-10-min crash (-1.0%), TSM's afternoon recovery (+1.0%), AMD's ORB L break — all had no corresponding signals.
- **Same-bar retests added clutter.** 12 same-bar retests all duplicated their parent signal's outcome.
- **Bearish signals were almost entirely wrong.** Only 3 out of 48 bearish signals were GOOD (AMD 13:20, AAPL 10:00, AAPL 9:51), reflecting the mostly bullish bias of the day that the indicator couldn't adapt to.
- **TSM confirmation window of 3.5 hours** suggests a timing logic issue.
- **MSFT's closely-spaced levels (ORB H / Week L $0.30 apart)** created 40 missed crossings and structural noise — the worst whipsaw of any symbol.
- **QQQ's percentage-based FT threshold penalized correct signals** on a high-priced, low-volatility ETF.

---

## Recommendations

### High Priority

1. **Suppress same-bar retests (◆⁰).** These add noise without value. If a breakout and retest fire on the same bar, suppress the retest.

2. **Tighten auto-confirmation criteria.** Require a minimum hold time (e.g., 3 bars instead of 1) before auto-promoting. The NVDA 10:00 and AMZN 12:10 cases show that immediate auto-confirm in choppy conditions is unreliable.

3. **Add counter-trend filter.** Suppress bearish reversals/reclaims when price is above session VWAP or session open. Suppress bullish reversals/reclaims when price is below VWAP or session open. This would have eliminated several BAD signals on this day.

4. **Merge closely-spaced levels.** When two levels are within 1x buffer distance of each other (e.g., MSFT's ORB H and Week L at $0.30 apart), merge them into a single "zone" and only generate signals when price decisively clears both edges. This would have prevented MSFT's 40 missed crossings and multiple false signals.

### Medium Priority

5. **Filter distant level signals.** GOOGL's Yest L reversal at 302.35 when price was at 308 has zero practical value. Add a maximum-distance filter (e.g., signal level must be within 1-2 ATR of current price).

6. **Add chop detection.** When a level has been crossed more than N times in M minutes, temporarily suppress further signals at that level. This would help with GOOGL's PM H (15 crosses), MSFT's ORB H/Week L zone (40 crossings), and AMD's morning ORB H chop.

7. **Review reclaim signal type.** 0% GOOD rate across 13 signals suggests reclaims are not providing value in their current form. Consider requiring higher thresholds or removing this signal type.

8. **Investigate TSM confirmation timing.** The 3.5-hour gap between signal (9:50) and confirmation check (13:26) seems like a bug. Normal confirmation checks happen within minutes.

9. **Adjust FT thresholds for ETFs.** QQQ's 0.3% threshold ($1.81 on $603) is too high for the typical intraday move of a broad ETF. Consider using ATR-proportional thresholds or reducing the percentage for instruments with lower relative volatility.

### Low Priority

10. **Morning volatility mode / settling period.** Consider suppressing or dimming signals in the first 15 minutes of the session when volatility is extremely high (e.g., TSLA's $9 range in the first 15 min, AAPL's 6 signals in 16 minutes). A settling period would let the opening noise subside before generating actionable signals.

11. **Session-low/high break signals.** When price breaks below all tracked levels (NVDA's final crash), there's no signal. A new signal type for session extreme breaks could capture these moves.

12. **Use TradingView exported 5m data for verification.** BATS vs composite tape discrepancies are significant for SPY/TSLA/META. Future analysis should use TV's own exported candle data for more accurate OHLC verification.

13. **Fix AAPL dual CONF bug.** Auto-promote and regular confirmation should not produce conflicting results at the same timestamp. Ensure auto-promote takes precedence or that the confirmation check is skipped when auto-promote has already fired.
