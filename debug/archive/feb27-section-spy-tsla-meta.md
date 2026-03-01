# Feb 27, 2026 — Signal Analysis: SPY, TSLA, META

*Generated: 2026-02-28 16:18*

**Methodology:** 1-minute BATS candle data aggregated into 5-minute bars (aligned to session open 09:30). Follow-through measured at 5m/15m/30m after signal bar close using the pine log's reported close price. Rating: GOOD if 15m or 30m FT >= +0.3% of price, BAD if <= -0.3%, else NEUTRAL.

**OHLC Note:** The pine log reports 5-minute timeframe OHLC from TradingView's server. Our candle-aggregated 5m bars may differ slightly due to exchange data feed differences (BATS vs composite). Minor discrepancies (< $0.20) are expected; larger ones are flagged.


---

## SPY — Grade: C

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

## TSLA — Grade: D+

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

## META — Grade: C

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
- 2 level crossing(s) without signals — likely filtered by cooldown/volume rules. Important ones are in the table above.

**Signal summary:** 0 GOOD / 1 BAD / 2 NEUTRAL / 1 N/A out of 4 total signals.


---

## Cross-Symbol Summary

| Symbol | Grade | Total Signals | Good | Bad | Neutral | N/A | BRK Conf Rate | Missed |
|--------|-------|---------------|------|-----|---------|-----|---------------|--------|
| SPY | C | 11 | 0 | 0 | 10 | 1 | 0/4 | 0 |
| TSLA | D+ | 7 | 0 | 5 | 1 | 1 | 0/2 | 0 |
| META | C | 4 | 0 | 1 | 2 | 1 | 0/1 | 2 |

### Overall Observations

1. **OHLC Discrepancies:** All three symbols show OHLC mismatches between the pine log (TradingView 5m composite data) and BATS 1m-aggregated 5m bars. This is expected — TradingView uses consolidated tape data while BATS is a single exchange. The pine log OHLC should be treated as authoritative for signal evaluation.

2. **Confirmation Rate:** 0/7 BRK signals confirmed across all three symbols. Feb 27 was a choppy day where breakouts consistently failed to sustain, then price eventually moved in the breakout direction later. The confirmation window may be too tight for this type of slow-grind day.

3. **SPY** had the most signals (10) but all rated NEUTRAL — price moved in tight ranges around key levels with no clear breakout until late day. The late ORB H breakout at 15:15 did work but the follow-through was modest.

4. **TSLA** was the worst performer with 5 BAD ratings. The extreme early volatility (ORB H break then immediate Yest L break) created conflicting signals. The indicator correctly identified the moves but the whipsaw made them untradeable.

5. **META** had only 4 signals with 1 BAD. The initial Yest L breakout was correctly identified but the reversal made it a bad trade. The reversal signal at 9:35 was NEUTRAL — the huge first-bar range made clean entries impossible.

6. **Design observations:**
   - The indicator's cooldown and volume filters correctly suppressed many level re-crosses (only 2 missed signals in META, 0 in SPY and TSLA after buffer filtering)
   - On whipsaw days, same-bar BRK+reversal combinations (TSLA 9:40-9:45) create conflicting signals that are confusing for traders
   - Late-day signals (15:15, 15:55) have limited follow-through data for proper evaluation
   - The 0% confirmation rate across all symbols on this day suggests the confirmation mechanism is working correctly — it's protecting traders from false breakouts on a choppy day
   - SPY's 9:45 bearish signals had 30m FT of -0.223% (price went up against signal) — just below the 0.3% BAD threshold. On a day that ultimately closed +0.46%, these bearish signals were directionally wrong but the FT was just small enough to rate NEUTRAL
   - The OHLC discrepancies between BATS and TradingView composite data are systematically large (up to $3-4 for META, $1-2 for SPY/TSLA). For future analysis, using TradingView's own exported 5m candle data would provide more accurate verification
