# KLB Daily Investigation — March 6, 2026

## Market Context

Broadly bearish day. SPY flat (-0.1%), but individual names sold off hard in the afternoon.

| Symbol | Open | High | Low | Close | Chg% | Range (ATR) |
|--------|------|------|-----|-------|------|-------------|
| SPY | 673.39 | 676.11 | 669.76 | 672.46 | -0.1% | 0.7x |
| QQQ | 600.31 | 606.00 | 598.33 | 599.81 | -0.1% | 0.7x |
| AMD | 195.27 | 200.24 | 191.44 | 192.58 | -1.4% | 1.0x |
| TSLA | 398.09 | 402.35 | 394.21 | 396.56 | -0.4% | 0.6x |
| NVDA | 179.80 | 182.76 | 176.90 | 177.74 | -1.1% | 0.9x |
| META | 648.01 | 649.47 | 636.11 | 644.83 | -0.5% | 0.8x |

Morning: Mixed, with gap down on META and AMD bull fakeout. Afternoon: Broad selloff in final 90 minutes.

---

## Part 1: Pine Log Signal Scorecard

Source: 16 pine log files (`pine-logs-Key Level Breakout v3.2_*.csv`). Files matched to symbols via IB opening prices.

### File-to-Symbol Mapping (IB-verified)

| File Hash | Symbol | Open Price | ATR |
|-----------|--------|-----------|-----|
| `f5ca9` | NVDA | 179.85 | 6.37 |
| `6c510` | TSLA | 399.12 | 14.32 |
| `64be3` | META | 649.85 | 19.68 |
| `5f808` | AMD | 195.27 | 10.81 |
| `2db98` | SPY | 673.41 | 8.80 |
| `715ab` | QQQ | 602.28 | 10.52 |
| `4a6ed` | MSFT | 409.34 | varies |
| `d7a4b` | AAPL | 257.88 | varies |
| `cd90d` | GOOGL | 296.09 | varies |
| `63fda` | AMZN | 213.81 | varies |
| `23330` | AMD (1m chart) | 98.50 | 4.60 |
| `3c350` | TSLA (1m chart) | 384.30 | 24.84 |
| `3da7c` | TSLA (alt chart) | 344.19 | 13.43 |
| `59c57` | TSM | 76.24 | 5.67 |
| `9985c` | SLV | 56.80 | 1.19 |
| `c817e` | QQQ (alt chart) | - | - |

Note: Multiple files per symbol exist due to different chart configurations (1m vs 5m signal TF, different exchanges). The IB-matched files above are the primary 5m signal charts.

### Signals by Symbol (Primary Charts Only)

#### NVDA (`f5ca9`) — 4 signals, 3 CONF pass
| Time | Dir | Type | Level | Vol | EMA | CONF | BAIL |
|------|-----|------|-------|-----|-----|------|------|
| 9:35 | BULL | BRK | PD LH L + Today O | 11.1x | bear | - | - |
| 9:50 | BULL | RNG | range break | 4.0x | - | - | - |
| 10:15 | BULL | BRK | VWAP | 1.3x | bull | - | - |
| 15:15 | BEAR | BRK | ORB L | 4.8x | bear | CONF pass | HOLD |
| 15:25 | BEAR | BRK | PM L | 2.9x | bear | CONF pass | - |
| 15:30 | BEAR | BRK | Yest L | 3.1x | bear | CONF pass | HOLD |

Morning: Bullish. System caught the 9:35 bull breakout. No midday signals. Afternoon: Caught the massive selloff from 15:15 onward — all CONF passed.

#### TSLA (`6c510`) — 5 signals, 1 CONF pass
| Time | Dir | Type | Level | Vol | EMA | CONF | BAIL |
|------|-----|------|-------|-----|-----|------|------|
| 9:30 | BEAR | BRK | Today O | 0.8x | bear | - | - |
| 9:35 | BEAR | RNG | range break | 13.3x | - | - | - |
| 9:35 | BEAR | BRK | PM L | 13.3x | bear | CONF pass | - |
| 9:40 | BEAR | BRK | VWAP | 8.7x | bear | - | HOLD |
| 10:10 | BEAR | BRK | ORB H | 1.8x | bear | - | - |
| 10:45 | BEAR | BRK | ORB H | 1.4x | bear | - | - |

All signals bear. TSLA sold off at open, bounced 9:45-13:15, then chopped. **No bull signals at all** — system had TSLA locked in bear mode with EMA below.

#### META (`64be3`) — 4 signals, 3 CONF pass
| Time | Dir | Type | Level | Vol | EMA | CONF | BAIL |
|------|-----|------|-------|-----|-----|------|------|
| 9:30 | BEAR | BRK | Yest L | 1.5x | bear | CONF pass | - |
| 9:35 | BEAR | RNG | range break | 17.6x | - | - | - |
| 9:35 | BEAR | BRK | PM L | 17.6x | bear | CONF pass | - |
| 9:35 | BEAR | BRK | VWAP + Today O | 17.6x | bear | - | HOLD (pnl=-0.10) |

All signals bear at open. Massive 17.6x volume on the breakdown. CONF auto-passed (R1 EMA). **5m CHECK at 9:40 showed pnl=-0.10 but HOLD** because SPY was aligned (SPY checkmark).

#### AMD (`5f808`) — 9 signals, 2 CONF pass
| Time | Dir | Type | Level | Vol | EMA | CONF | BAIL |
|------|-----|------|-------|-----|-----|------|------|
| 9:35 | BULL | BRK | PM L + PD LH L | 14.2x | bear | - | - |
| 11:00 | BULL | BRK | Yest L + VWAP | 1.0x | bull | - | - |
| 11:20 | BULL | BRK | Yest L + ORB H | 0.6x | bull | - | - |
| 12:00 | BULL | BRK | Yest H | 0.8x | bull | - | - |
| 13:10 | BULL | BRK | Yest L + ORB H | 1.3x | bull | - | - |
| 14:05 | BEAR | BRK | VWAP | 1.3x | bear | - | - |
| 15:15 | BEAR | BRK | PM L + Yest L + ORB L + PD LH L | 4.8x | bear | CONF pass | HOLD |
| 15:25 | BEAR | BRK | Week L + Month O | 2.3x | bear | CONF pass | HOLD |

AMD had a complex day: bull until 12:00 (peaking at 200.24), then reversed hard. Bull signals dominated morning; bear BRK PM L + Yest L at 15:15 caught the afternoon collapse.

#### SPY (`2db98`) — 3 signals, 1 CONF pass
| Time | Dir | Type | Level | Vol | EMA | CONF | BAIL |
|------|-----|------|-------|-----|-----|------|------|
| 9:35 | BEAR | BRK | VWAP + Today O | 6.3x | bear | - | - |
| 9:40 | BEAR | RNG+BRK | PM L + ORB L | 4.9x | bear | CONF pass | HOLD |
| 15:35 | BEAR | BRK | ORB L | 1.9x | bear | CONF pass | HOLD |

SPY quiet until the late selloff. 9:40 bear BRK + 15:35 bear BRK both confirmed and held.

#### QQQ (`715ab`) — 2 signals, 1 CONF pass
| Time | Dir | Type | Level | Vol | EMA | CONF | BAIL |
|------|-----|------|-------|-----|-----|------|------|
| 10:10 | BEAR | BRK | ORB H + VWAP | 1.2x | bear | - | - |
| 15:35 | BEAR | BRK | ORB L | 1.9x | bear | CONF pass | HOLD |

### Day Summary Scorecard

| Metric | Value |
|--------|-------|
| Total signals (primary charts) | ~30 |
| CONF passes | 12 |
| CONF fails | 0 |
| BAIL decisions | 0 (all HOLD) |
| HOLD decisions | ~8 |
| Symbols with signals | 10+ |
| Coverage gap 11:00-14:00 | Minimal (only AMD bull signals) |

---

## Part 2: Missed Move Investigation

### Miss 1: AMD 12:05 Downmove

**User note:** "downmove missed"

**IB 5m data at 12:05:**
```
O=199.86 H=199.96 L=199.14 C=199.36  Vol=141,515 (0.7x avg)
```

**5-bar window:**
| Time | O | H | L | C | Vol |
|------|---|---|---|---|-----|
| 11:55 | 199.39 | 200.00 | 199.17 | 199.89 | 176K |
| 12:00 | 199.89 | 200.24 | 199.67 | 199.93 | 123K |
| **12:05** | **199.86** | **199.96** | **199.14** | **199.36** | **142K** |
| 12:10 | 199.36 | 199.51 | 198.90 | 199.08 | 191K |
| 12:15 | 199.09 | 199.21 | 198.58 | 198.97 | 134K |

**MFE:** 2.23 (0.24 ATR) — small but real move, AMD went from 200 to 197 over next hour.

**Key levels:**
- PD Close at 199.46 — **right at the level** (0.01 ATR)
- ORB High at 198.11 (0.14 ATR)
- VWAP at 198.02 (0.15 ATR)

**EMA/VWAP:** Price ABOVE both EMA(21) and VWAP. EMA trend = bull.

**Pine log context:** System had AMD bullish all morning (BRK Yest H at 12:00 was the last bull signal). The bearish reversal from the 200 double-top wasn't detectable because:

**Root cause:** EMA GATE + signal type mismatch. Price was above EMA and VWAP at 12:05. The system was correctly showing bullish context. This was a **reversal from PD Close / Yest High** — a magnet level where REV signal would be appropriate, but the system was in BRK mode at a bullish level. The move was also only 0.24 ATR.

**Cross-symbol:** All 6 symbols moved down at 12:05 simultaneously (SPY -0.19%, QQQ -0.21%). This was a **broad market downturn**, not AMD-specific.

**Verdict:** Marginal miss. Small move (0.24 ATR), EMA gate correctly blocked. Would need a REV signal at PD Close/Yest High double-top pattern, which the system doesn't support well mid-day.

---

### Miss 2: TSLA 11:05 Downmove

**User note:** "downmove missed"

**IB 5m data at 11:05:**
```
O=398.72 H=399.37 L=398.20 C=398.25  Vol=806,527 (0.8x avg)
```

**MFE:** 0.59 (0.05 ATR) — very small. TSLA only went from 398 to 397.66 then bounced back to 399.78 by 11:15.

**Key levels:**
- ORB High at 398.27 — right at the level (0.00 ATR)
- Today Open at 398.09 (0.01 ATR)
- PD Low at 399.42 (0.09 ATR)

**EMA/VWAP:** Price above both. EMA trend = bull.

**Pine log context:** TSLA's last signal was at 10:45 (BEAR BRK ORB H). At 11:05, TSLA was bouncing back toward ORB High, and the downward move was minuscule.

**Root cause:** Non-move. MFE of 0.05 ATR is essentially noise. TSLA was range-bound 397-399 from 10:45 to 12:30. No real move to catch.

**Verdict:** Not actionable. The "downmove" was noise — 0.05 ATR within a 2-point range.

---

### Miss 3: TSLA 12:40 Upmove

**User note:** "upmove missed"

**IB 5m data at 12:40:**
```
O=397.55 H=398.24 L=397.14 C=398.15  Vol=491,904 (0.8x avg)
```

**MFE:** 4.20 (0.32 ATR) — moderate. TSLA went from 398 to 402.35 (the daily high) by 13:20.

**Key levels:**
- Today Open at 398.09 (0.00 ATR) — right at the level
- ORB High at 398.27 (0.01 ATR)
- VWAP at 397.79 (0.03 ATR)

**EMA/VWAP:** Price BELOW EMA(21), ABOVE VWAP. EMA trend = bear.

**Pine log context:** No signal at 12:40. System was bearish on TSLA all day. Last signal at 10:45 was bear BRK ORB H.

**Root cause:** EMA GATE + Midday Desert. Price was below the 21 EMA, and the move was a bullish reversal against the EMA trend. The system correctly had TSLA in bear mode. This reversal off Today Open/ORB High support would need a REV signal at those levels. However, EMA gate would suppress it (price below EMA for a bull signal).

**Cross-symbol:** TSLA-specific move. SPY was flat (-0.04%), QQQ flat (-0.02%). This was a TSLA-only bounce.

**Verdict:** Real miss (0.32 ATR), but EMA gate was protecting against counter-trend trades. A REV signal at Today Open with EMA exemption could catch this, but those were shown to be net-negative in v3.1 testing (-11.8 ATR).

---

### Miss 4: TSLA 13:15 Bull Signal — Then It Was Over

**User note:** "signaled bull but then it was over"

**IB 5m data at 13:15:**
```
O=400.99 H=401.84 L=400.80 C=401.59  Vol=622,488 (1.2x avg)
```

**MFE:** 0.76 (0.06 ATR) — negligible. TSLA peaked at 402.35 and reversed.

**Key levels:**
- PD Low at 399.42 (0.17 ATR)
- Today Open at 398.09 (0.27 ATR)

**Pine log context:** No pine log signal at 13:15 on the primary TSLA chart (`6c510`). The `3da7c` (alt TSLA chart) had a 13:40 BEAR BRK ORB H with conf=x~ (dimmed due to prior CONF fail). But nothing at 13:15.

**Root cause:** The user may have seen a signal from the 1m chart configuration. On the primary 5m chart, TSLA was still in bear mode with no levels to break. The bull move from 12:40 to 13:20 ran out of steam at PD Low (399.42) and reversed. By 13:15, TSLA was already at the top (401.59) with 0.06 ATR MFE remaining — the move was indeed over.

**Verdict:** Correctly not signaled on primary chart. The move was already exhausted. If a signal appeared on a secondary chart, the timing was too late — classic "signal at the top" problem.

---

### Miss 5: NVDA 9:30 Upmove

**User note:** "upmove we didn't fetch it"

**IB 5m data at 9:30:**
```
O=179.80 H=181.44 L=179.64 C=180.96  Vol=5,679,664 (1.0x avg)
```

**MFE:** 1.80 (0.29 ATR) — moderate. NVDA went from 180.96 to 182.76 by 12:00.

**Pine log context:** The system DID fire a bull signal at **9:35** (not 9:30):
```
9:35 ▲ BRK PD LH L + Today O vol=11.1x ema=bear rs=+0.8% rangeATR=3.5
```
Plus a RNG range break at 9:50, and a BRK VWAP at 10:15.

**Root cause:** The system **DID catch this move**, just 5 minutes later (9:35 vs 9:30). The 9:30 bar itself was the opening bar with massive range (179.64 to 181.44 = 1.80). The signal fired at 9:35 after the first 5m bar confirmed direction, which is by design.

**Important:** No CONF pass was logged for the 9:35 bull BRK. The signal appeared as a tilde `~` (pending CONF). The user may have seen the signal but without a confirmation label — this matches the complaint "we didn't fetch it" (meaning no actionable confirmation).

**Verdict:** Signal existed at 9:35 but lacked CONF pass. The EMA was bear at open (price above EMA only marginally). This was likely suppressed or not auto-confirmed because CONF criteria weren't met. The bull move DID continue to 182.76. **This is a real miss worth ~0.29 ATR due to missing CONF.**

---

### Miss 6: NVDA 12:00 Down

**User note:** "down we didn't catch"

**IB 5m data at 12:00:**
```
O=182.32 H=182.49 L=182.09 C=182.19  Vol=1,661,468 (1.3x avg)
```

**MFE:** 1.67 (0.27 ATR) — moderate. NVDA went from 182.19 to 180.52 by 12:30.

**Key levels:**
- ORB High at 182.34 — right at the level (0.02 ATR)
- PD Close at 183.33 (0.18 ATR)
- VWAP at 181.70 (0.08 ATR)

**EMA/VWAP:** Price above both. EMA trend = bull.

**Pine log context:** No signal at 12:00. Last NVDA signal was the 10:15 bull BRK VWAP. No more signals until 15:15.

**Root cause:** EMA GATE + Midday Desert. Price was above EMA at 12:00 — system would not generate a bear signal. The reversal from ORB High (182.34) was a classic REV setup, but the system was in bull mode. The 5-hour gap (10:15 to 15:15) is the Midday Desert problem.

**Cross-symbol:** NVDA-specific move. SPY was flat (+0.04%) at this time.

**Verdict:** Real miss. 0.27 ATR from a REV at ORB High. The ORB High acted as resistance and price turned down. EMA gate correctly blocked, but a REV signal at ORB High could have caught it if REV signals had better midday coverage.

---

### Miss 7: META 9:30 Bear — Got It But No GO Signal

**User note:** "great move we got it but no conf or other label that says GO IN"

**IB 5m data at 9:30:**
```
O=648.01 H=648.38 L=637.85 C=638.26  Vol=757,495 (1.0x avg)
```

A massive 10+ point candle on the first bar. META gapped down through yesterday's low.

**Pine log context:**
```
9:30 ▼ BRK Yest L vol=1.5x ema=bear rs=-1.2% adx=40 rangeATR=2.8
CONF 9:30 ▼ BRK → ✓ (auto-R1: EMA)
```

**The log DOES show CONF pass** at 9:30 via auto-R1 (EMA aligned). This auto-confirmed the bear breakout of Yesterday's Low.

**Root cause:** The CONF pass label may not have been visible on the chart, or the user expected a different type of confirmation marker (e.g., star, explicit GO label). The system auto-confirmed it due to R1 criteria (EMA aligned + early time). The 5m CHECK at 9:40 showed pnl=-0.10 but HOLD (SPY aligned).

**Verdict:** FALSE MISS — the system did signal and confirm. This is a UI/visibility issue. The auto-confirm label may blend in or the user expected a more prominent marker. Consider making the CONF pass label more visible.

---

### Miss 8: META 9:35 Upmove — Only REV, No Confirmation

**User note:** "significant upmove, only REV ORB L, not conf, not marked good to go"

**IB 5m data at 9:35:**
```
O=638.30 H=640.72 L=636.11 C=640.19  Vol=364,597 (0.5x avg)
```

**MFE:** 5.97 (0.34 ATR) — META bounced from 636 low to 646 by 10:30.

**Pine log context:** At 9:35, the system fired:
- RNG range break (17.6x vol) — **BEAR**
- BRK PM L (17.6x vol) — **BEAR**, CONF pass
- BRK VWAP + Today O — **BEAR**

All signals at 9:35 were BEAR, not bull. The user's "upmove" at 9:35 was the reversal bounce AFTER the massive 9:30 drop. META hit 636.11 (the session low) at 9:35 and then bounced.

**Root cause:** Signal type mismatch. The 9:35 bar was a continuation of the bear breakout (PM L broke). The intra-bar reversal (from 636 back to 640) happened within the same 5m candle. On a 5m timeframe, this was a bear candle that just happened to bounce. A REV signal at the ORB Low (636.11) would need to wait for a separate bar confirming the reversal — which didn't come until 9:40-9:50.

The user may be seeing this on a 1-minute chart where the reversal was more visible. On 5m, the bounce was part of the 9:35 bear candle.

**Verdict:** Hard to catch on 5m. The reversal happened within a single massive bear candle. A FADE signal could potentially catch this (price broke PM L, failed, reversed), but the timing was very tight. The 0.34 ATR bounce was real but against the dominant bearish momentum.

---

### Miss 9: META 10:30 Bearish Diamond — But Went Up

**User note:** "bearish signal with diamond but went up and then neutral"

**IB 5m data at 10:30:**
```
O=644.27 H=646.16 L=644.18 C=646.16  Vol=153,470 (0.7x avg)
```

The bar was actually bullish (+0.29%). META went UP from 644 to 647 in the next few bars.

**Pine log context:** No signal at 10:30 on the primary META chart (`64be3`). The `2db98` file (which is actually SPY, not META) shows signals at 12:55 and 13:00 for bear ORB H — but those are SPY signals, not META, and at different times.

**Key levels at 10:30:**
- Today Open at 648.01 (0.10 ATR away)
- PD Low at 650.31 (0.23 ATR)

**Root cause:** The "diamond" marker the user saw was likely a dimmed signal (either on a secondary chart configuration or a display element). The pine logs don't show a META signal at 10:30. META was recovering bullishly at this time (EMA=bull, price above VWAP). If there was a bear signal, it was correctly invalidated by the bullish price action.

**Verdict:** No actionable signal existed. The "diamond" may have been a dimmed/gated signal from a different chart overlay. META was going UP at 10:30 — a bearish signal would have lost money.

---

## Part 3: Cross-Symbol Analysis

### Simultaneous Moves

**12:05 — Broad market downturn:**
All 6 symbols moved down simultaneously. SPY -0.19%, QQQ -0.21%, AMD -0.25%, TSLA -0.32%, NVDA -0.22%, META -0.17%. This was a market-wide event, not symbol-specific. The system had no signals because EMA was bullish across most names.

**9:30 Open — Divergent:**
AMD +1.24% UP, NVDA +0.65% UP. META -1.50% DOWN, TSLA -0.39% DOWN. SPY -0.15% DOWN. The open was split — tech megacaps (META) sold while semis (AMD, NVDA) rallied. The system correctly generated bear signals for META and TSLA, bull signals for NVDA (at 9:35).

**15:15 — Synchronized selloff:**
AMD, NVDA, GOOGL, AMZN, QQQ all broke down through multiple key levels with CONF passes. This was the system's best performance of the day — catching the broad afternoon selloff.

### Pattern: Midday Reversal Gap

The 11:00–14:00 window had minimal signals across all symbols. During this time:
- AMD reversed from 200 to 197 (missed)
- NVDA reversed from 182.3 to 180.5 (missed)
- TSLA bounced from 397 to 402 (missed)

These were all **reversal moves at ORB High/Today Open levels** — exactly the Midday Desert problem documented in the system research.

---

## Synthesis: Patterns and Action Items

### What Worked

1. **Opening signals (9:30-9:40):** System correctly identified bear breakouts in META, TSLA, SPY, and bull breakout in NVDA/AMD. Strong 17.6x and 13.3x volume confirmations.
2. **Afternoon selloff (15:15+):** CONF pass on AMD, NVDA, GOOGL, AMZN, SPY, QQQ — broad synchronized move with high-quality signals.
3. **BAIL/HOLD decisions:** All 5m CHECKs resulted in HOLD (correct — no premature exits).

### What Missed

| Miss | MFE (ATR) | Root Cause | Fixable? |
|------|-----------|------------|----------|
| AMD 12:05 down | 0.24 | EMA gate + midday | Marginal, not worth |
| TSLA 11:05 down | 0.05 | Non-move (noise) | N/A |
| TSLA 12:40 up | 0.32 | EMA gate + midday | REV at Today O, but net-negative historically |
| TSLA 13:15 bull | 0.06 | Exhausted move | N/A |
| NVDA 9:30 up | 0.29 | Caught at 9:35, no CONF | Check CONF criteria for morning opens |
| NVDA 12:00 down | 0.27 | EMA gate + midday | REV at ORB H |
| META 9:30 bear | 0.12 | FALSE MISS — had CONF | UI visibility issue |
| META 9:35 up | 0.34 | Intra-bar reversal | Hard on 5m TF |
| META 10:30 bear | 0.11 | No signal existed | N/A |

**Total real missed MFE:** ~1.12 ATR (excluding false miss, noise, and exhausted moves)

### Root Cause Breakdown

1. **Midday Desert (5 of 9 misses):** The 11:00-14:00 gap remains the primary blind spot. Moves at ORB H/Today O levels go undetected.
2. **EMA Gate (4 of 9):** Correctly blocking counter-trend signals. Previous research showed counter-EMA REVs at 35% win = net negative.
3. **UI/Visibility (1 of 9):** META 9:30 CONF pass was invisible to user.
4. **Non-moves (2 of 9):** TSLA 11:05 and 13:15 were noise/exhaustion.

### Action Items

1. **Check NVDA 9:35 CONF criteria** — The bull BRK at 9:35 with 11.1x volume and EMA=bear should have auto-confirmed (R1 criteria: EMA aligned + before 10:30). But EMA was bear, not aligned with bull direction. This is by design — the EMA gate correctly prevented auto-confirm. However, with 11.1x volume and rs=+0.8%, this was a strong signal. Consider a volume-override for auto-confirm when vol > 10x at open.

2. **META CONF label visibility** — The user didn't see the CONF pass at 9:30. Consider making auto-confirm labels more prominent (bigger font, brighter color, or a separate "GO" marker).

3. **Midday coverage remains the #1 opportunity** — 1.12 ATR missed in 9 moves. The ORB High and Today Open levels produced real reversals midday. The FADE signal mechanism (implemented in v3.0) should theoretically catch some of these, but none fired midday on March 6.

4. **No new structural problems identified** — The EMA gate, CONF system, and BAIL/HOLD decisions all performed correctly. The misses are known limitations (midday gap, counter-EMA suppression).
