# Feb 27, 2026 Signal Analysis: AMD, NVDA, TSM

---

## AMD — Grade: C+

**Key Levels:**
- ORB H: 200.38 (from 9:30-9:34 high)
- ORB L: 198.01 (from 9:30-9:34 low)
- PM L (Pre-Market Low): 199.55
- Yest L (Yesterday's Low): 201.46
- Week L: 194.83

**Session OHLC (candle-verified):**
Open 200.11 | High 201.89 (10:12) | Low 197.74 (13:49) | Close 200.20 | Range 4.15pt | Net +0.09 (+0.04%)

**Day narrative:** AMD opened at 200.11 and immediately sold off to 198.01, establishing the ORB low. It then chopped violently through the first 30 minutes, whipping between 198 and 201 with multiple failed breakouts. After 10:30, it settled into a slow grind down, breaking the PM Low (199.55) cleanly in the 13:20 bar and reaching the day's low near 197.74. A late-day recovery reclaimed PM Low at 15:55, closing near 200.20. Very choppy morning, cleaner afternoon signals.

### Signal Table

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|
| 1 | 9:35 | ▼ | ~ (rev) | ORB H | 13x | v19 | BAD | +0.50 | -0.91 | -0.65 |
| 2 | 9:40 | ▲ | ~ (rev) | PM L + Week L | 5.5x | ^95 | BAD | -0.90 | -0.41 | -0.13 |
| 3 | 9:45 | ▼ | BRK | PM L | 3.6x | v56 | BAD | -0.43 | -0.49 | -0.36 |
| 4 | 9:45 | ▼ | ◆ retest | PM L | 0.6x | v55 | — | — | — | — |
| 5 | 9:50 | ▲ | BRK | ORB H | 3x | ^92 | BAD | -0.89 | -0.94 | +0.06 |
| 6 | 9:55 | ▼ | BRK | Yest L | 2.1x | v53 | BAD | +0.22 | +0.97 | +0.83 |
| 7 | 10:00 | ▼ | ~~ (rclm) | ORB H | 2x | v72 | BAD | +1.17 | +0.89 | +0.51 |
| 8 | 10:10 | ▲ | BRK | ORB H | 2.3x | ^69 | NEUTRAL | +0.67 | -0.14 | -0.63 |
| 9 | 13:20 | ▼ | BRK | PM L | 1.8x | v94 | GOOD | -0.11 | -0.44 | -0.54 |
| 10 | 13:30 | ▲ | ~ (rev) | ORB L | 2.2x | ^75 | BAD | -0.36 | -0.46 | -0.31 |
| 11 | 15:55 | ▲ | ~~ (rclm) | PM L | 3.5x | ^68 | NEUTRAL | +0.20 | — | — |

**Notes on calculations:**

Signal 1 (9:35 ▼ ~ ORB H): Pine OHLC = O200.11 H200.38 L198.01 C199.93. This is a 5m bar (9:35-9:39). Candle-verified 5m aggregation: 9:35-9:39 → O199.89, H200.50, L199.17, C200.44. **DISCREPANCY**: The pine log shows C199.93 but 1m candles show the bar closing at 200.44. The pine OHLC appears to be the first 5m bar of the session (9:30-9:34), not 9:35. The signal at 9:35 likely references the 9:30-9:34 bar's properties.

*Actually, on re-examination:* The pine log timestamps represent the 5m bar start time. So signal at 9:35 = bar covering 9:35-9:39. But the OHLC values O200.11 H200.38 L198.01 C199.93 don't match the 9:35-9:39 candles (O199.89 H200.50 L199.17 C200.44). These values match the 9:30-9:34 bar (O200.11, H200.38, L198.01 verified from candles). **This is a known pattern**: the signal fires on the bar where the level was established/crossed, and the OHLC shown is from that bar's data which was calculated at bar close.

**Revised interpretation**: The 5m bar time shown IS the signal bar. The OHLC in the pine log is the aggregated 5m bar for that time window. Let me re-verify:

- Signal 9:35: Candle 5m 9:35-9:39 = O199.89 H200.50 L199.17 C200.44 (pine says O200.11 H200.38 L198.01 C199.93)

The OHLC in pine doesn't match. This suggests the pine log OHLC is from the PREVIOUS completed 5m bar (9:30-9:34). The 9:30-9:34 1m candles: O200.11, H max(200.21, 198.77, 199.38, 199.77, 200.38)=200.38, L min(198.2, 198.01, 198.43, 198.92, 199.28)=198.01, C(9:34)=199.93. **Yes, confirmed**: Pine OHLC = 9:30-9:34 bar. The signal fires at the start of the 9:35 bar but references the just-completed 9:30-9:34 bar's OHLC.

**This means signal bar close = the close shown in OHLC field, and follow-through starts from the NEXT 5m bar.**

With this understanding, let me recalculate FT properly:

**Signal 1 (9:35 ▼ ~ ORB H, close=199.93):**
- Signal bar closed at 199.93 (end of 9:30-9:34 bar)
- 5m FT: close of 9:35-9:39 bar = 200.44 → FT = 199.93 - 200.44 = -0.51 (wrong direction) → BAD
- 15m FT: close of 9:45-9:49 bar. 9:45-9:49 1m: C9:49=200.97. → FT = 199.93 - 200.97 = -1.04 → BAD
- 30m FT: close of 10:00-10:04 bar. C10:04=200.31 → FT = 199.93 - 200.31 = -0.38 → BAD
- Rating: BAD (15m FT = -1.04, -0.52% against)

**Signal 2 (9:40 ▲ ~ PM L + Week L, close=200.44):**
- 5m bar 9:35-9:39, close 200.44
- 5m FT: close of 9:40-9:44 bar. C9:44=199.54 → FT = 199.54 - 200.44 = -0.90 → BAD
- 15m FT: close of 9:50-9:54 bar. C9:54=200.08 → FT = 200.08 - 200.44 = -0.36 → NEUTRAL
- 30m FT: close of 10:05-10:09 bar. C10:09=201.03 → FT = 201.03 - 200.44 = +0.59 → GOOD at 30m
- Rating: NEUTRAL (mixed; 5m bad, 30m good, but net move small vs. chop)

**Signal 3 (9:45 ▼ BRK PM L, close=199.54):**
- 5m bar 9:40-9:44, close 199.54
- 5m FT: close of 9:45-9:49 bar. C9:49=200.97 → FT = 199.54 - 200.97 = -1.43 → BAD
- 15m FT: close of 9:55-9:59 bar. C9:59=199.86 → FT = 199.54 - 199.86 = -0.32 → NEUTRAL
- 30m FT: close of 10:10-10:14 bar. C10:14=201.10 → FT = 199.54 - 201.10 = -1.56 → BAD
- Rating: BAD (5m FT = -1.43, -0.72% against)
- CONF: 9:46 → failed ✗

**Signal 5 (9:50 ▲ BRK ORB H, close=200.97):**
- 5m bar 9:45-9:49, close 200.97
- Wait, pine says O199.51 H201.12 L199.25 C200.97. Let me verify 9:45-9:49: O(9:45)=199.51, H=max(199.67,200.16,199.88,200.90,201.12)=201.12, L=min(199.25,199.43,199.50,199.71,200.61)=199.25, C(9:49)=200.97. ✓ Matches.
- 5m FT: close of 9:50-9:54 bar. C9:54=200.08 → FT = 200.08 - 200.97 = -0.89 → BAD
- 15m FT: close of 10:00-10:04 bar. C10:04=200.31 → FT = 200.31 - 200.97 = -0.66 → BAD
- 30m FT: close of 10:15-10:19 bar. C10:19=200.59 → FT = 200.59 - 200.97 = -0.38 → NEUTRAL
- Rating: BAD (5m = -0.89, -0.44% against)
- CONF: 9:51 → failed ✗

**Signal 6 (9:55 ▼ BRK Yest L, close=200.08):**
- Pine OHLC: O200.93 H201.01 L199.25 C200.08. This should be the 9:50-9:54 bar.
- Verify: O(9:50)=200.93 ✓, C(9:54)=200.08 ✓
- prices=201.46 (Yest L level). But wait — close 200.08 is below 201.46, so this is saying price broke below Yest L. That makes sense.
- 5m FT: close of 9:55-9:59 bar. C9:59=199.86 → FT = 200.08 - 199.86 = +0.22 → NEUTRAL (bearish direction confirmed but small)
- 15m FT: close of 10:05-10:09 bar. C10:09=201.03 → FT = 200.08 - 201.03 = -0.95 → BAD
- 30m FT: close of 10:20-10:24 bar. C10:24=200.99 → FT = 200.08 - 200.99 = -0.91 → BAD
- Rating: BAD (15m = -0.95, -0.47% against)

**Signal 7 (10:00 ▼ ~~ reclm ORB H, close=199.86):**
- Pine OHLC: O200.01 H200.26 L199.71 C199.86. This is 9:55-9:59 bar.
- Verify: O(9:55)=200.01 ✓, C(9:59)=199.86 ✓
- 5m FT: close of 10:00-10:04. C10:04=200.31 → FT = 199.86 - 200.31 = -0.45 → BAD
- 15m FT: close of 10:10-10:14. C10:14=201.10 → FT = 199.86 - 201.10 = -1.24 → BAD
- 30m FT: close of 10:25-10:29. C10:29=201.09 → FT = 199.86 - 201.09 = -1.23 → BAD
- Rating: BAD (15m = -1.24, -0.62% against)

**Signal 8 (10:10 ▲ BRK ORB H, close=201.03):**
- Pine OHLC: O200.34 H201.38 L200.25 C201.03. This is 10:05-10:09 bar.
- Verify: O(10:05)=200.34 ✓, H=max(200.81,201.10,201.23,201.38,201.36)=201.38 ✓, C(10:09)=201.03 ✓
- 5m FT: close of 10:10-10:14. C10:14=201.10 → FT = 201.10 - 201.03 = +0.07 → NEUTRAL
- 15m FT: close of 10:20-10:24. C10:24=200.99 → FT = 200.99 - 201.03 = -0.04 → NEUTRAL
- 30m FT: close of 10:35-10:39. C10:39=200.34 → FT = 200.34 - 201.03 = -0.69 → BAD
- Rating: NEUTRAL (5m/15m flat, 30m turned against but gradual drift, not decisive)
- CONF: 10:31 → failed ✗

**Signal 9 (13:20 ▼ BRK PM L, close=198.43):**
- Pine OHLC: O198.81 H198.87 L198.40 C198.43. This is 13:15-13:19 bar.
- Verify: O(13:15)=198.81 ✓, L=min(198.66,198.68,198.59,198.60,198.40)=198.40 ✓, C(13:19)=198.43 ✓
- CONF: 13:20 → auto-promoted ✓
- 5m FT: close of 13:20-13:24. C13:24=198.34 → FT = 198.43 - 198.34 = +0.09 → NEUTRAL
- 15m FT: close of 13:30-13:34. C13:34=198.08 → FT = 198.43 - 198.08 = +0.35 → NEUTRAL (0.18%)
- 30m FT: close of 13:45-13:49. C13:49=197.85 → FT = 198.43 - 197.85 = +0.58 → GOOD (0.29%)
- Rating: GOOD (consistent follow-through, 30m = +0.58, 0.29% — borderline but directionally clean)

**Signal 10 (13:30 ▲ ~ rev ORB L, close=198.36):**
- Pine OHLC: O198.32 H198.48 L197.97 C198.36. This is 13:25-13:29 bar.
- Verify: O(13:25)=198.32 ✓, L=min(198.07,198.03,197.97,198.05,198.26)=197.97 ✓, C(13:29)=198.355. Close rounds approximately. ✓
- 5m FT: close of 13:30-13:34. C13:34=198.08 → FT = 198.08 - 198.36 = -0.28 → NEUTRAL
- 15m FT: close of 13:40-13:44. C13:44=197.96 → FT = 197.96 - 198.36 = -0.40 → BAD (bearish = against bullish signal)
- 30m FT: close of 13:55-13:59. C13:59=197.93 → FT = 197.93 - 198.36 = -0.43 → BAD
- Rating: BAD (15m = -0.40, -0.20%; 30m = -0.43, -0.22% — just under threshold but consistently wrong)

**Signal 11 (15:55 ▲ ~~ reclm PM L, close=200.00):**
- Pine OHLC: O199.77 H200.23 L199.49 C200. This is 15:50-15:54 bar.
- Verify: O(15:50)=199.77 ✓, H=max(199.99,199.78,199.84,200.16,200.23)=200.23 ✓, C(15:54)=199.995. ✓ (~200)
- 5m FT: close of 15:55-15:59. C15:59=200.20 → FT = 200.20 - 200.00 = +0.20 → NEUTRAL
- 15m/30m: Session ends at 16:00 — insufficient data
- Rating: NEUTRAL (limited FT data; small positive move into close)

### Revised Signal Table

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|
| 1 | 9:35 | ▼ | ~ rev | ORB H | 13x | v19 | **BAD** | -0.51 | -1.04 | -0.38 |
| 2 | 9:40 | ▲ | ~ rev | PM L + Wk L | 5.5x | ^95 | **NEUTRAL** | -0.90 | -0.36 | +0.59 |
| 3 | 9:45 | ▼ | BRK | PM L | 3.6x | v56 | **BAD** | -1.43 | -0.32 | -1.56 |
| 4 | 9:50 | ▲ | BRK | ORB H | 3x | ^92 | **BAD** | -0.89 | -0.66 | -0.38 |
| 5 | 9:55 | ▼ | BRK | Yest L | 2.1x | v53 | **BAD** | +0.22 | -0.95 | -0.91 |
| 6 | 10:00 | ▼ | ~~ rclm | ORB H | 2x | v72 | **BAD** | -0.45 | -1.24 | -1.23 |
| 7 | 10:10 | ▲ | BRK | ORB H | 2.3x | ^69 | **NEUTRAL** | +0.07 | -0.04 | -0.69 |
| 8 | 13:20 | ▼ | BRK | PM L | 1.8x | v94 | **GOOD** | +0.09 | +0.35 | +0.58 |
| 9 | 13:30 | ▲ | ~ rev | ORB L | 2.2x | ^75 | **BAD** | -0.28 | -0.40 | -0.43 |
| 10 | 15:55 | ▲ | ~~ rclm | PM L | 3.5x | ^68 | **NEUTRAL** | +0.20 | — | — |

*(Retests and CONF lines excluded from rating — they are supplementary)*

**Confirmations:** 1/4 BRK confirmed (25%) — only the 13:20 PM L BRK was auto-promoted. The 9:45, 9:50, 10:10 BRKs all failed confirmation.

**Missed signals:**
- The massive drop from 201.89 (10:12) through ORB H (200.38) down to ~199.70 (10:32) — a $2.19 decline in 20 minutes — did not generate a clean bearish ORB H breakdown signal. The 10:00 reclaim was bearish but the big move didn't get a distinct BRK label on the way down.
- No signal was generated when price broke the ORB L (198.01) level during the 13:27-13:30 area. Price touched 197.97 at 13:27 (per pine log) but no BRK ORB L signal fired.

**Key findings:**
1. **Morning chop destroyed signal quality.** 5 of the first 7 signals were BAD — the 9:30-10:30 window was extremely noisy with price crossing levels repeatedly.
2. **Only the 13:20 ▼ BRK PM L was genuinely good** — auto-confirmed, steady follow-through.
3. **3 of 4 breakouts failed confirmation** — indicator correctly identified these as unreliable.
4. **The reversal signals (~) in the morning were particularly poor** — catching falling knives and calling tops that didn't hold.
5. **OHLC discrepancy pattern confirmed**: Pine log OHLC shows the PREVIOUS completed 5m bar, not the bar at the signal timestamp. This is consistent behavior.

---

## NVDA — Grade: C+

**Key Levels:**
- ORB H: 181.78 (from 9:30-9:34 high)
- ORB L: 180.01 (from 9:30-9:34 low)
- PM L (Pre-Market Low): 181.02
- Week L: 179.18

**Session OHLC (candle-verified):**
Open 181.25 | High 182.58 (10:12) | Low 176.39 (15:59) | Close 177.10 | Range 6.19pt | Net -4.15 (-2.34%)

**Day narrative:** NVDA opened at 181.25 and immediately sold off through PM L (181.02) in the first 5-minute bar. A sharp V-recovery at 9:40 reclaimed PM L and ORB L, then broke above ORB H (181.78) by 10:10, reaching a session high of 182.58 at 10:12. However, the breakout failed, and NVDA drifted lower all day, breaking ORB L at 10:00, then later breaking ORB L again at 12:20. It continued grinding to new lows, breaking Week L (179.18) at 13:20. A failed late-day recovery attempt preceded a massive sell-off in the final 10 minutes (178.13 to 176.39), closing at 177.10. Brutal bearish day.

### Signal Table

**Signal 1 (9:35 ▼ BRK PM L, close=180.45):**
- Pine OHLC: O181.25 H181.78 L180.01 C180.45. This is the 9:30-9:34 bar.
- Verify: O(9:30)=181.25 ✓, H=181.78 ✓, L=180.01 ✓, C(9:34)=180.45 ✓
- 5m FT: close of 9:35-9:39 bar. C(9:39)=181.61 → FT = 180.45 - 181.61 = -1.16 → BAD
- 15m FT: close of 9:45-9:49. C(9:49)=180.83 → FT = 180.45 - 180.83 = -0.38 → BAD
- 30m FT: close of 10:00-10:04. C(10:04)=181.56 → FT = 180.45 - 181.56 = -1.11 → BAD
- Rating: **BAD** (immediate V-reversal)
- CONF: 9:39 → failed ✗

**Signal 1b (9:35 ▼ ~ rev ORB H, close=180.45):**
- Same bar, same OHLC. Reversal off ORB H high.
- Same FT as above → **BAD**

**Signal 2 (9:40 ▲ ~~ rclm PM L + ~~ ORB L, close=181.61):**
- Pine OHLC: O180.46 H181.69 L179.73 C181.61. This is the 9:35-9:39 bar.
- Verify: O(9:35)=180.455 ≈ 180.46, H=max(180.71,180.34,180.27,181.03,181.685)=181.685≈181.69 ✓, L=min(179.80,179.73,179.88,179.95,180.68)=179.73 ✓, C(9:39)=181.61 ✓
- 5m FT: close of 9:40-9:44. C(9:44)=180.60 → FT = 180.60 - 181.61 = -1.01 → BAD
- 15m FT: close of 9:50-9:54. C(9:54)=179.98 → FT = 179.98 - 181.61 = -1.63 → BAD
- 30m FT: close of 10:05-10:09. C(10:09)=182.15 → FT = 182.15 - 181.61 = +0.54 → GOOD
- Rating: **NEUTRAL** (5m/15m bad, 30m good — inconsistent; overall the move eventually worked but took a 30-min detour)

**Signal 3 (9:45 ▼ BRK PM L, close=180.60):**
- Pine OHLC: O181.59 H181.65 L179.86 C180.60. This is 9:40-9:44 bar.
- Verify: O(9:40)=181.59 ✓, H=181.65 ✓, L=min(180.94,180.51,180.05,179.86,180.04)=179.86 ✓, C(9:44)=180.60 ✓
- 5m FT: close of 9:45-9:49. C(9:49)=180.83 → FT = 180.60 - 180.83 = -0.23 → NEUTRAL
- 15m FT: close of 9:55-9:59. C(9:59)=179.79 → FT = 180.60 - 179.79 = +0.81 → GOOD
- 30m FT: close of 10:10-10:14. C(10:14)=182.03 → FT = 180.60 - 182.03 = -1.43 → BAD
- Rating: **NEUTRAL** (whipsaw — 15m good then completely reversed at 30m)

**Signal 4 (10:00 ▼ BRK ORB L, close=179.79):**
- Pine OHLC: O179.97 H180.28 L179.57 C179.79. This is 9:55-9:59 bar.
- Verify: O(9:55)=179.97 ✓, H=max(180.01,179.92,180.28,179.99,179.89)=180.28 ✓, L=min(179.66,179.625,179.89,179.57,179.575)=179.57 ✓, C(9:59)=179.79 ✓
- CONF: 10:00 → auto-promoted ✓
- 5m FT: close of 10:00-10:04. C(10:04)=181.56 → FT = 179.79 - 181.56 = -1.77 → BAD
- 15m FT: close of 10:10-10:14. C(10:14)=182.03 → FT = 179.79 - 182.03 = -2.24 → BAD
- 30m FT: close of 10:25-10:29. C(10:29)=181.83 → FT = 179.79 - 181.83 = -2.04 → BAD
- Rating: **BAD** (auto-confirmed but immediately reversed dramatically — terrible signal)
- CONF: 10:01 → failed ✗ (second confirmation check)

**Signal 5 (10:05 ▲ ~~ rclm PM L + ~~ ORB L, close=181.56):**
- Pine OHLC: O179.79 H181.56 L179.74 C181.56. This is 10:00-10:04 bar.
- Verify: O(10:00)=179.79 ✓, H=max(180.145,180.82,181.13,181.17,181.56)=181.56 ✓, L=min(179.735,180.14,180.65,180.85,180.98)=179.735≈179.74 ✓, C(10:04)=181.56 ✓
- 5m FT: close of 10:05-10:09. C(10:09)=182.15 → FT = 182.15 - 181.56 = +0.59 → GOOD
- 15m FT: close of 10:15-10:19. C(10:19)=181.27 → FT = 181.27 - 181.56 = -0.29 → NEUTRAL
- 30m FT: close of 10:30-10:34. C(10:34)=181.54 → FT = 181.54 - 181.56 = -0.02 → NEUTRAL
- Rating: **NEUTRAL** (5m follow-through good, but 15m/30m gave it all back)

**Signal 6 (10:10 ▲ BRK ORB H, close=182.15):**
- Pine OHLC: O181.57 H182.43 L181.48 C182.15. This is 10:05-10:09 bar.
- Verify: O(10:05)=181.57 ✓, H=max(181.87,182.09,182.36,182.40,182.43)=182.43 ✓, C(10:09)=182.15 ✓
- 5m FT: close of 10:10-10:14. C(10:14)=182.03 → FT = 182.03 - 182.15 = -0.12 → NEUTRAL
- 15m FT: close of 10:20-10:24. C(10:24)=181.54 → FT = 181.54 - 182.15 = -0.61 → BAD
- 30m FT: close of 10:35-10:39. C(10:39)=181.745 → FT = 181.745 - 182.15 = -0.41 → BAD
- Rating: **BAD** (breakout failed, immediate drift down; -0.34% at 15m)
- CONF: 10:16 → failed ✗

**Signal 6b (10:10 ▲ ~ rev Week L, close=182.15):**
- Same bar. Reversal off Week L at 179.18. This is a stretch — current price 182.15 is far above 179.18.
- Same FT → **BAD**

**Signal 7 (12:20 ▼ BRK ORB L, close=179.72):**
- Pine OHLC: O179.95 H179.97 L179.69 C179.72. This is 12:15-12:19 bar.
- Verify: O(12:15)=179.95 ✓, H=max(179.97,179.94,179.86,179.81,179.78)=179.97 ✓, L=min(179.88,179.79,179.72,179.69,179.685)=179.685≈179.69 ✓, C(12:19)=179.72 ✓
- 5m FT: close of 12:20-12:24. C(12:24)=179.49 → FT = 179.72 - 179.49 = +0.23 → NEUTRAL
- 15m FT: close of 12:30-12:34. C(12:34)=180.07 → FT = 179.72 - 180.07 = -0.35 → BAD
- 30m FT: close of 12:45-12:49. C(12:49)=179.70 → FT = 179.72 - 179.70 = +0.02 → NEUTRAL
- Rating: **NEUTRAL** (5m weak follow-through, then bounced, then returned to entry — flat overall at 30m)

**Signal 8 (13:20 ▼ BRK Week L, close=178.87):**
- Pine OHLC: O179.28 H179.31 L178.80 C178.87. This is 13:15-13:19 bar.
- Verify: O(13:15)=179.28 ✓, H=max(179.31,179.235,179.19,179.11,179.08)=179.31 ✓, L=min(179.125,179.10,179.08,179.01,178.80)=178.80 ✓, C(13:19)=178.865≈178.87 ✓
- CONF: 13:20 → auto-promoted ✓
- 5m FT: close of 13:20-13:24. C(13:24)=178.94 → FT = 178.87 - 178.94 = -0.07 → NEUTRAL
- 15m FT: close of 13:30-13:34. C(13:34)=178.86 → FT = 178.87 - 178.86 = +0.01 → NEUTRAL
- 30m FT: close of 13:45-13:49. C(13:49)=178.56 → FT = 178.87 - 178.56 = +0.31 → NEUTRAL (0.17%)
- Rating: **NEUTRAL** (auto-confirmed, direction correct but very slow follow-through; price meandered near 178.8-179.0 for a long time before eventually collapsing further in the final minutes)
- CONF: 14:56 → BRK failed ✗ (late secondary check failed?)

### Revised Signal Table

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|
| 1 | 9:35 | ▼ | BRK + ~ rev | PM L + ORB H | 10.3x | v75 | **BAD** | -1.16 | -0.38 | -1.11 |
| 2 | 9:40 | ▲ | ~~ rclm | PM L + ORB L | 6.2x | ^96 | **NEUTRAL** | -1.01 | -1.63 | +0.54 |
| 3 | 9:45 | ▼ | BRK | PM L | 2.9x | v59 | **NEUTRAL** | -0.23 | +0.81 | -1.43 |
| 4 | 10:00 | ▼ | BRK | ORB L | 2.4x | v69 | **BAD** | -1.77 | -2.24 | -2.04 |
| 5 | 10:05 | ▲ | ~~ rclm | PM L + ORB L | 1.7x | ^100 | **NEUTRAL** | +0.59 | -0.29 | -0.02 |
| 6 | 10:10 | ▲ | BRK + ~ rev | ORB H + Week L | 1.8x | ^71 | **BAD** | -0.12 | -0.61 | -0.41 |
| 7 | 12:20 | ▼ | BRK | ORB L | 2x | v88 | **NEUTRAL** | +0.23 | -0.35 | +0.02 |
| 8 | 13:20 | ▼ | BRK | Week L | 2x | v87 | **NEUTRAL** | -0.07 | +0.01 | +0.31 |

*(Retests and CONF lines excluded from main rating)*

**Confirmations:** 2/5 BRK confirmed (40%):
- 10:00 ▼ BRK ORB L → auto-promoted ✓ (but terrible FT — BAD signal despite confirmation)
- 13:20 ▼ BRK Week L → auto-promoted ✓ (neutral FT, eventually correct direction)
- 9:35 BRK PM L → failed ✗
- 9:45 BRK PM L → (no explicit CONF line, but retest at 9:46)
- 10:10 BRK ORB H → failed ✗

**Missed signals:**
- The massive 10:05-10:12 rally from 179.74 to 182.58 (+2.84, +1.58%) — while the reclaim at 10:05 and BRK at 10:10 were captured, the full extent of the move was one of the best trades of the day.
- The final-hour crash from ~178.13 to 176.39 (-1.74, -1.0% in 10 minutes) had no signal. No level was tracked at those prices.
- Price broke below PM L (181.02) multiple times intraday without getting a new breakout signal each time (cooldown working as designed).

**Key findings:**
1. **Auto-confirmed ORB L breakdown at 10:00 was the worst signal of the day** — auto-promoted but immediately reversed +1.77 in 5 minutes. This is a design concern: auto-promote on a level that was tested multiple times in choppy conditions should not auto-confirm.
2. **Morning session (9:30-10:15) was a whipsaw disaster** — 6 signals, all BAD or NEUTRAL. Price oscillated ±2 points around PM L and ORB levels.
3. **The 13:20 Week L breakdown was directionally correct** but follow-through was slow. The massive final-10-minute sell-off (177.1 → 176.39 close) came much later.
4. **No bullish signals worked** — all 3 bullish signals (9:40, 10:05, 10:10) were NEUTRAL or BAD. It was a bearish day that the indicator failed to capture cleanly.
5. **Volume was massive** (10x, 6x in the first bars) but did not improve signal quality.

---

## TSM — Grade: B

**Key Levels:**
- ORB H: 371.95 (from 9:30-9:34 high)
- ORB L: 368.65 (from 9:30-9:34 low)
- PM L: 369.85 (close to ORB L)
- Week H: 372.20

**Session OHLC (candle-verified):**
Open 370.14 | High 376.67 (10:12) | Low 368.65 (9:30) | Close 374.69 | Range 8.02pt | Net +4.55 (+1.23%)

**Day narrative:** TSM opened at 370.14 and immediately bounced off the ORB low at 368.65, recovering strongly. It crossed above ORB H (371.95) and Week H (372.20) by 9:50, rallied to a session high of 376.67 at 10:12, then drifted slowly lower through the midday. At 13:35, a reclaim signal fired as it broke back below ORB H. After that, TSM spent the afternoon between 371-374 before recovering into the close at 374.69. A moderately bullish day with a clear morning impulse and afternoon consolidation.

### Signal Table

**Signal 1 (9:35 ▲ ~ rev PM L + ~ ORB L, close=371.41):**
- Pine OHLC: O370.14 H371.95 L368.65 C371.41. This is the 9:30-9:34 bar.
- Verify: O(9:30)=370.14 ✓, H=max(370.14,369.58,370.47,371.66,371.945)=371.945≈371.95 ✓, L=min(368.65,368.70,369.00,370.53,370.99)=368.65 ✓, C(9:34)=371.41 ✓
- 5m FT: close of 9:35-9:39. C(9:39)=372.01 → FT = 372.01 - 371.41 = +0.60 → NEUTRAL (0.16%)
- 15m FT: close of 9:45-9:49. C(9:49)=374.61 → FT = 374.61 - 371.41 = +3.20 → GOOD (0.86%)
- 30m FT: close of 10:00-10:04. C(10:04)=374.28 → FT = 374.28 - 371.41 = +2.87 → GOOD (0.77%)
- Rating: **GOOD** (strong bullish follow-through, 15m = +3.20, 0.86%)

**Signal 2 (9:45 ▼ ~ rev ORB H, close=371.21):**
- Pine OHLC: O372.07 H372.17 L369.62 C371.21. This is 9:40-9:44 bar.
- Verify: O(9:40)=372.07 ✓, H=max(372.17,371.49,371.17,370.61,371.48)=372.17 ✓, L=min(371.07,370.68,369.87,369.62,370.42)=369.62 ✓, C(9:44)=371.21 ✓
- 5m FT: close of 9:45-9:49. C(9:49)=374.61 → FT = 371.21 - 374.61 = -3.40 → BAD
- 15m FT: close of 9:55-9:59. C(9:59)=372.655 → FT = 371.21 - 372.655 = -1.445 → BAD
- 30m FT: close of 10:10-10:14. C(10:14)=375.41 → FT = 371.21 - 375.41 = -4.20 → BAD
- Rating: **BAD** (massive move against; -0.92% at 15m, -1.13% at 30m)

**Signal 3 (9:50 ▲ BRK Week H + ORB H, close=374.61):**
- Pine OHLC: O371.10 H374.80 L370.79 C374.61. This is 9:45-9:49 bar.
- Verify: O(9:45)=371.10 ≈, H: looking at 9:45-9:49 candles: H=max(372.00, 373.19, 373.00, 374.52, 374.80)=374.80 ✓, L=min(370.79, 371.76, 372.525, 372.90, 374.15)=370.79 ✓, C(9:49)=374.61 ✓
- 5m FT: close of 9:50-9:54. C(9:54)=373.06 → FT = 373.06 - 374.61 = -1.55 → BAD
- 15m FT: close of 10:00-10:04. C(10:04)=374.28 → FT = 374.28 - 374.61 = -0.33 → NEUTRAL
- 30m FT: close of 10:15-10:19. C(10:19)=375.24 → FT = 375.24 - 374.61 = +0.63 → NEUTRAL (0.17%)
- Rating: **NEUTRAL** (5m bad pullback but recovered; 30m slightly above entry — marginal)
- CONF: 13:26 → failed ✗ (very late confirmation check — failed after 3.5 hours!)

**Signal 4 (13:35 ▼ ~~ rclm ORB H, close=370.97):**
- Pine OHLC: O371.50 H371.72 L370.94 C370.97. This is 13:30-13:34 bar.
- Verify: O(13:30)=371.50 ✓, H=max(371.72, 371.58, 371.40, 371.17, 371.22)=371.72 ✓, L=min(371.46, 371.40, 370.96, 370.94, 370.97)=370.94 ✓, C(13:34)=370.97 ✓
- 5m FT: close of 13:35-13:39. C(13:39)=371.32 → FT = 370.97 - 371.32 = -0.35 → NEUTRAL
- 15m FT: close of 13:45-13:49. C(13:49)=371.79 → FT = 370.97 - 371.79 = -0.82 → BAD
- 30m FT: close of 14:00-14:04. C(14:04)=372.87 → FT = 370.97 - 372.87 = -1.90 → BAD
- Rating: **BAD** (reclaim signal was bearish but price immediately bounced back above; -0.51% at 30m)

### Revised Signal Table

| # | Time | Dir | Type | Levels | Vol | Pos | Rating | 5m FT | 15m FT | 30m FT |
|---|------|-----|------|--------|-----|-----|--------|-------|--------|--------|
| 1 | 9:35 | ▲ | ~ rev | PM L + ORB L | 16x | ^84 | **GOOD** | +0.60 | +3.20 | +2.87 |
| 2 | 9:45 | ▼ | ~ rev | ORB H | 2.8x | v38 | **BAD** | -3.40 | -1.45 | -4.20 |
| 3 | 9:50 | ▲ | BRK | Week H + ORB H | 2.2x | ^95 | **NEUTRAL** | -1.55 | -0.33 | +0.63 |
| 4 | 13:35 | ▼ | ~~ rclm | ORB H | 3.3x | v96 | **BAD** | -0.35 | -0.82 | -1.90 |

*(Retests excluded from main rating)*

**Confirmations:** 0/1 BRK confirmed (0%):
- 9:50 ▲ BRK Week H + ORB H → failed ✗ (confirmation check at 13:26 — 3.5 hours later!)

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

---

## Cross-Symbol Summary

### Overall Grades
| Symbol | Grade | Good | Bad | Neutral | Total Signals |
|--------|-------|------|-----|---------|---------------|
| AMD | C+ | 1 | 6 | 3 | 10 |
| NVDA | C+ | 0 | 3 | 5 | 8 |
| TSM | B | 1 | 2 | 1 | 4 |

### Common Patterns

1. **Morning chop (9:30-10:30) destroyed signal quality across all three stocks.** AMD had 7 signals in the first hour (5 BAD), NVDA had 6 signals (3 BAD, 3 NEUTRAL). Only TSM's opening reversal was genuinely good.

2. **Auto-confirmation doesn't guarantee good signals.** NVDA's 10:00 ▼ BRK ORB L was auto-confirmed but immediately reversed -1.77 in 5 minutes — the worst signal of the day.

3. **Reversal signals (~) are particularly unreliable in choppy conditions.** AMD's 9:35 and 9:40 reversals, NVDA's 9:35 reversal, and TSM's 9:45 reversal were all BAD.

4. **Afternoon signals were generally better than morning signals.** AMD's 13:20 ▼ BRK was GOOD; NVDA's 13:20 ▼ BRK was directionally correct (NEUTRAL). Less noise in midday.

5. **The indicator missed major moves:**
   - NVDA's final-10-minute crash (-1.74) had no signal
   - TSM's afternoon recovery (+3.72) had no signal
   - AMD's drift from 201.89 to 197.74 was only partially captured

6. **Confirmation windows are inconsistent.** TSM's BRK took 3.5 hours to check confirmation (and failed). Earlier signals got checked within 1-20 minutes. The confirmation timing logic may need review.

### Design Issues Identified

1. **Reversal signals in high-chop environments:** Consider requiring higher volume thresholds or stronger position scores for reversal signals in the first 15 minutes of the session.

2. **Auto-confirmation reliability:** The NVDA 10:00 auto-confirm BAD signal suggests auto-promote criteria should be tighter, especially when a level has been crossed multiple times in quick succession.

3. **Late confirmation checks:** TSM's 3.5-hour gap between signal and confirmation check is unusual and may indicate a logic issue with how confirmation timing is tracked.

4. **Missing breakdown signals for new lows:** When NVDA made new session lows in the final 10 minutes (breaking well below any tracked level), no signal fired. Consider adding a session-low-break signal type.
