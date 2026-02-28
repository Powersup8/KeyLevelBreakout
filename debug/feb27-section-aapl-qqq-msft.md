# Feb 27, 2026 Signal Analysis: AAPL, QQQ, MSFT

## Executive Summary

| Symbol | Grade | Good | Bad | Neutral | Confirm Rate | Missed | Day Return |
|--------|-------|------|-----|---------|-------------|--------|------------|
| AAPL   | **B-** | 3   | 4   | 2       | 1/2 (50%)   | 13     | -3.19%     |
| QQQ    | **D+** | 0   | 4   | 6       | 0/3 (0%)    | 16     | +0.73%     |
| MSFT   | **D**  | 2   | 5   | 2       | 0/2 (0%)    | 40     | +0.45%     |

**Overall:** 28 signals, 5 Good (18%), 13 Bad (46%), 10 Neutral (36%). Confirmation rate 1/7 (14%). Heavy morning chop across all three symbols produced rapid-fire opposing signals. Afternoon sessions were quieter but signals still struggled. AAPL's directional trend (strong sell-off) was the only one where the indicator's bearish bias ultimately paid off, though short-term follow-through was disrupted by counter-bounces.

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

## Overall Assessment

- **Total signals:** 28 (5 Good / 18%, 13 Bad / 46%, 10 Neutral / 36%)
- **Overall confirm rate:** 1/7 (14%) -- extremely low
- **Total missed crossings:** 69 (mostly whipsaw at established levels)
- **Best signal of the day:** AAPL 10:00 ▼ BRK Yest L (GOOD, +2.14pt / +0.79% at 30m, confirmed)
- **Worst signal cluster:** QQQ 9:45 (3 simultaneous bearish signals, all BAD, -2.68 at 30m)
- **OHLC verification:** All signals with standard bars matched candle-aggregated OHLC perfectly (0 discrepancies)

## Design Issues & Bugs

### 1. BUG: Dual CONF at Same Timestamp (AAPL 10:00)
The AAPL 10:00 ▼ BRK Yest L shows two CONF entries at the same timestamp: one "auto-promote" (confirmed) and one "failed". The same breakout should not produce conflicting confirmation statuses. This appears to be a race condition between auto-promote and regular confirmation logic.

### 2. DESIGN: Signal Overload in Opening Minutes
All three symbols produced rapid-fire opposing signals in the first 20-30 minutes:
- AAPL: 6 signals in 16 minutes (9:35-9:51), 4 direction changes
- QQQ: 7 signals in 20 minutes (9:35-9:55), 3 direction changes
- MSFT: 2 early signals (9:30-9:35), then 3 signals at 10:10-10:20

**Recommendation:** Consider a "settling period" in the first 15 minutes after open where signal generation is suppressed or signals require higher confidence. Alternatively, require a minimum hold time before allowing opposing signals.

### 3. DESIGN: Closely-Spaced Levels Create Noise (MSFT)
MSFT's ORB H (394.23) and Week L (394.53) were only $0.30 apart (0.08% of price, 0.55x buffer). This created 40 missed crossings and multiple false signals as price oscillated in the zone. Similarly, PM L (389.86) and ORB L (389.90) were only $0.04 apart.

**Recommendation:** When two levels are within 1x buffer distance of each other, merge them into a single "zone" and only generate signals when price decisively clears both edges of the zone.

### 4. DESIGN: 0.3% FT Threshold May Not Suit ETFs
QQQ had 6 NEUTRAL signals despite several being directionally correct. On a $600+ ETF with relatively low volatility (ATR=10.08 = 1.67%), the 0.3% threshold ($1.81) may be too high for the typical 5-30 minute move. QQQ signal #8 (10:05 ▲ BRK ORB H) was the correct call that led to a $3+ move over 2 hours, but the 30m FT was only +$0.80 (0.13%).

**Recommendation:** Use ATR-proportional thresholds for FT evaluation rather than fixed percentages, or reduce the threshold for broad ETFs.

### 5. DESIGN: Confirmation Rate is Structurally Low (14%)
Only 1 of 7 breakouts confirmed across all three symbols. This suggests either:
- Confirmation criteria are too strict for the current market conditions
- The levels being used don't produce clean breaks (they're more like speed bumps than walls)
- Breakouts in choppy/ranging days inherently fail to confirm

### 6. DESIGN: 3 Signals at Same Bar (QQQ 9:45)
QQQ fired BRK Yest L + REV ORB H + RST Yest L all at 9:45. A breakout and a retest of the same level (Yest L) at the same bar is contradictory. The BRK fires because price broke below, and the RST fires because it's retesting from below -- but both at the same time suggests the retest logic should be suppressed when a fresh breakout just occurred.
