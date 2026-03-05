# Investigation Report: March 4, 2026 — Missed Moves & Anomalies

**Date:** 2026-03-04 | **Indicator:** KLB v2.8a | **Data:** Pine logs (5m signal TF) + 1m IB candles

## Symbol Identification

| File | Symbol | Open Price | ATR | Key Levels |
|------|--------|-----------|-----|------------|
| 0edc9 | TSLA | $397.85 | 14.62 | PM H $402.04, ORB H $403.47 |
| 4d99b | NVDA | $180.58 | 6.52 | Yest H $180.90, ORB H $182.25 |
| 97001 | AMZN | $210.51 | 6.44 | PM H $210.60, Week H $211.59, ORB H $212.32 |
| d308b | SPY | $681.64 | 8.80 | Yest H $682.61, PM H $683.33, ORB H $683.49 |
| 6fb8f | QQQ | $604.16 | 10.46 | PM H $605.88, Yest H $603.96, ORB L $603.73, ORB H $606.88 |

**Context:** March 4 was a strong broad-market up day. All 5 symbols gapped up and continued higher. Every symbol's first signal (9:35) was a bullish breakout that failed CONF — the classic "gap-and-pullback" pattern before the real move resumed.

---

## 1. AMZN Upmove 9:45 (Didn't Fire) / 9:46-10:27

### What happened?
AMZN pulled back from its opening spike ($212.32 high at 9:30) to $210.59 at 9:40, then resumed upward. The real move started at 9:46 (O=$211.47) and ran to $217.54 by 10:27.

- **Move magnitude:** $211.05 (9:45 open) to $217.54 (10:27 high) = **$6.49 = 1.01 ATR**
- **From 9:46 entry:** $211.47 to $217.54 = **$6.07 = 0.94 ATR**
- **Duration:** 42 minutes of steady uptrend

### What signals fired?
1. **9:35 ▲ BRK PM H + Week H** — vol=16.2x, ema=bull, vwap=above, adx=32, rangeATR=4.3 ⚡ 🔊 → **CONF ✗ (9:40)**
2. **9:50 ▲ BRK Week H + ORB H** — vol=6.6x, ema=bull, vwap=above, adx=38, rangeATR=3.3 ⚡ → **No CONF line in log** (log may have been exported before CONF eval; or it's the last entry)

### What didn't fire?
- **No signal between 9:40-9:50.** The move started at 9:46 with a sharp bar ($211.47 to $212.28, +$0.81 in 1 minute). There was no 5m bar close during this window that generated a new signal.
- The 9:45-9:50 5m bar (which closes at 9:50 in Pine) captured the move start. The 9:50 BRK Week H + ORB H signal IS the move being caught — but it comes 4 minutes late.

### WHY was it missed at 9:45?
- **Timing gap between 5m bars.** The move started mid-bar (at 9:46 on the 1m chart). The 9:40-9:45 5m bar closed at 9:45 and showed: O=211.09, C=210.67 — it was actually a DOWN bar. The bullish impulse started in the last 2 minutes of that 5m bar.
- **The 9:35 signal CONF failed** because the 9:35-9:40 5m bar pulled back (C=210.67 from H=212.32). This is the "gap-and-pullback" false CONF failure — the indicator correctly fired the signal at 9:35 but the immediate pullback killed confirmation.
- **No level was broken at 9:45-9:46 on the 5m timeframe.** The signal-TF bar at 9:45 was red. The breakout re-occurred on the 9:50 bar.

### How big was the miss?
If we count from 9:46 open to 10:27 high: **0.94 ATR missed.**
But note: the 9:50 BRK fired and had strong indicators (vol=6.6x, adx=38, ema=bull). If a trader took this signal at 9:50, they'd enter at ~$212.69 and ride to $217.54 = $4.85 = **0.75 ATR captured.**

### What could catch it?
- **The 9:35 signal WAS correct** — it was a legitimate BRK of PM H + Week H with perfect conditions. The problem is CONF failed because the immediate next bar pulled back. This is the classic "first bar confirms direction, second bar pulls back, then it runs."
- **Auto-CONF with a lookahead** (e.g., 2-bar CONF instead of 1-bar) would have kept this alive. At 9:45 (2 bars after signal), price was still near the breakout level.
- **Re-trigger mechanism:** If a signal fires, CONF fails, but price then re-breaks the same level, the indicator should re-fire. Currently once CONF fails, the level is "used up" for that session. The 9:50 signal is basically this re-trigger — it works, but it means missing the 9:46-9:50 window.

---

## 2. TSLA Upmove 9:58

### What happened?
TSLA pulled back from its 9:35 spike (H=$403.47) to a low of $396.72 at 9:57, then bounced. From the 9:58 low, it grinded up to $407.86 by 10:28.

- **Move magnitude:** $396.74 (9:58 low) to $407.86 (10:28 high) = **$11.12 = 0.76 ATR**
- **Duration:** 30 minutes, gradual grind with no single explosive bar

### What signals fired?
1. **9:35 ▲ BRK PM H** — vol=14.7x ⚡ 🔊 → **CONF ✗ (9:40)**
2. Next signal: **10:25 ▲ BRK ORB H** — vol=2.1x, body=94% ⚠ → **CONF ✗ (11:12)**

### What didn't fire?
- **No signal between 9:40 and 10:25.** That's a **45-minute signal desert** covering the entire 0.76 ATR upmove.
- The bounce from 9:57-9:58 ($396.72) was not near any key level. PM H was at $402.04 (above). ORB H at $403.47 (way above). No Yest L/H, PM L, or ORB L was nearby.

### WHY was it missed?
- **Level desert.** At the 9:58 bounce point ($396.72), the price was BETWEEN levels. PM H was $5.32 above, and the open range low hadn't formed yet as a reference.
- **Gradual grind.** No single 5m bar had a clean breakout. The 5m bars from 9:55-10:25 were all small (rangeATR ~0.5-0.8), none breaking a key level.
- **VWAP could have helped.** If VWAP was near $399-400 at the time, the cross back above VWAP around 10:00 could have generated a VWAP signal. The 9:35 log shows vwap=above, so VWAP was likely around $400 — but we don't see a VWAP reversal signal at 10:00 because the move was gradual and didn't have a clean VWAP touch/reversal pattern.

### How big was the miss?
**0.76 ATR total.** But the 10:25 BRK ORB H (entry at ~$405.82) would have captured $405.82 to $407.86 = $2.04 = 0.14 ATR. So the **net miss is about 0.62 ATR.**

### What could catch it?
- **VWAP cross signal:** A signal when price crosses above VWAP after being below (around 10:00, price crossed from ~$398 to $400+). This would need a different trigger than the current VWAP reversal.
- **EMA reclaim/cross signal:** If EMAs were bearish during the pullback and flipped bullish around 10:00-10:05, an EMA cross signal could catch this.
- **"Grind detector":** 5 consecutive higher closes on 5m bars without breaking a level — this is a new signal type concept for trending moves away from levels.

---

## 3. TSLA Upmove 11:20

### What happened?
After the 10:30 peak ($407.79), TSLA sold off to $401.62 at 11:14, then bounced from $402.40 at 11:20 to $404.32 at 11:27.

- **Move magnitude:** $402.11 (11:20 low) to $404.67 (11:30 high) = **$2.56 = 0.18 ATR** (extended to ~$405.47 if we include 11:40)
- **Total: 0.23 ATR**
- **Duration:** 10-20 minutes

### What signals fired?
- **11:15 ▼ ~~ ORB H reclaim** — a BEARISH signal at ORB H ($403.47). This fired because price broke back BELOW ORB H. The reclaim was dimmed (vol=0.6x, body=83% ⚠).

### What didn't fire?
- **No bullish signal at 11:20.** No reversal, no reclaim, no BRK upward.

### WHY was it missed?
- **Small move (0.23 ATR).** This is below the threshold where the indicator typically generates meaningful signals.
- **Late in the session.** By 11:20, the indicator naturally dims signals (afternoon dimming starts).
- **No clear level nearby for a bullish trigger.** The ORB H at $403.47 was above ($402.40), and price bounced from a "no man's land" area.

### How big was the miss?
**0.23 ATR** — marginal. Not a significant miss. The risk/reward at 11:20 was poor (0.23 ATR potential vs. the ongoing downtrend).

### What could catch it?
- This is below the indicator's designed signal threshold. Chasing 0.23 ATR moves after 11:00 is not productive based on the validated data (afternoon GOOD = 0%).
- **Verdict: Acceptable miss.** Not worth optimizing for.

---

## 4. TSLA Downmove 10:30-11:14

### What happened?
TSLA peaked at $407.79 (10:30 high) and sold off to $401.62 (11:14 low).

- **Move magnitude:** $407.79 to $401.62 = **$6.17 = 0.42 ATR**
- **Duration:** 44 minutes, gradual selloff

### What signals fired?
- **10:52 ▲ retest ORB H** — a bullish retest signal at ORB H (wrong direction for this move)
- **11:15 ▼ ~~ ORB H reclaim** — bearish reclaim. This IS the correct signal, but it fired at the END of the move (11:15, when the low was at 11:14).

### What didn't fire?
- **No bearish signal between 10:30-11:14.** The selloff was gradual with no single 5m bar breaking below a key level until very late.

### WHY was it missed?
- **Gradual grind without level breaks.** The 5m bars from 10:30-11:14 were mostly small (0.2-0.5 ATR range), grinding lower without breaking ORB H cleanly on the downside until 11:12-11:15.
- **ORB H at $403.47** — price didn't break below this until 11:12 ($402.16 close). The first 40 minutes of the selloff (10:30-11:10) stayed above ORB H.
- **No bearish reversal at the top.** At 10:30, price was at $407.79 — there was no level above to reverse from (no Yest H, Week H, or PM H above $407).

### How big was the miss?
**0.42 ATR.** The 11:15 bearish reclaim came right at the end, with only 0.03 ATR remaining.

### What could catch it?
- **A "failed breakout" signal**: When price breaks ORB H (at 10:25), gets CONF ✗, and then starts grinding back below — this pattern is a reliable short signal.
- **Runner Score inversion:** When a bullish BRK fails CONF and price stays below the breakout level for 3+ 5m bars, fire a "fade" or "failed breakout" signal.
- **EMA cross bearish:** If the fast EMA crosses below slow EMA during this grind, that could be a standalone signal.

---

## 5. SPY/QQQ Upmove 9:46

### What happened?
Both SPY and QQQ made their session lows around 9:45 (SPY: $679.62, QQQ: $603.43) and then rallied:

**SPY:** $679.62 (9:45 low) to $686.64 (11:03 high) = **$7.02 = 0.80 ATR**, 77 minutes
**QQQ:** $603.43 (9:45 low) to $611.45 (11:02 high) = **$8.02 = 0.77 ATR**, 77 minutes

### What signals fired?

**SPY:**
1. **9:35 ▲ BRK Yest H** — vol=8.9x ⚡ 🔊 → **CONF ✗ (9:40)**
2. **10:20 ▲ BRK PM H + ORB H** — vol=2.6x, body=91% ⚠ → No CONF line in log
3. **10:55 ▲ ~ VWAP reversal** — vol=1.1x

**QQQ:**
1. **9:35 ▲ BRK PM H + Yest H** — vol=11.6x ⚡ ⚠ 🔊 → **CONF ✗ (9:40)**
2. **9:50 ▲ ~ ORB L reversal** — vol=3.4x, rangeATR=2.3 ⚡
3. **10:10 ▲ BRK PM H + ORB H** — vol=2.3x, body=83% ⚠ → No CONF line in log

### What didn't fire?
- **SPY: No signal between 9:40-10:20** — a 40-minute gap during which the upmove started
- **QQQ: Had a 9:50 reversal at ORB L** — this is actually a catch! The ORB L reversal at 9:50 with vol=3.4x and rangeATR=2.3 ⚡ is the indicator catching the bounce. But it's a REVERSAL (~), not a BRK, so it gets lower priority.

### WHY was the SPY 9:46 start missed?
- **Same pattern as AMZN.** The 9:35 BRK fired correctly but CONF failed due to immediate pullback. Then a signal desert until 10:20 (34 minutes) during the key move.
- **SPY had no level between 9:40-10:20.** Yest H was broken at 9:35, PM H and ORB H were higher. Price was in a level desert.
- **QQQ performed slightly better** — the 9:50 ORB L reversal caught the bounce. This is because QQQ had ORB L at $603.73, right at the 9:45 low ($603.43). SPY's equivalent level wasn't as close.

### How big was the miss?
**SPY: 0.80 ATR.** The 10:20 BRK enters at ~$684.47, which leaves only $686.64 - $684.47 = $2.17 = 0.25 ATR. So **0.55 ATR net missed.**
**QQQ: 0.77 ATR.** The 9:50 reversal catches it at ~$605.11, giving $611.45 - $605.11 = $6.34 = 0.61 ATR captured. **Only 0.16 ATR missed** (the 9:45-9:50 window).

### What could catch it?
- **For SPY:** A VWAP reclaim signal around 10:00 when price crossed back through VWAP area, or an ORB L reversal (if SPY had one). The fundamental issue is SPY was in a level desert.
- **Re-trigger mechanism** (same as AMZN item #1) — the 9:35 signal was correct, CONF failure was premature.
- **QQQ's ORB L reversal at 9:50 is actually a success case** — the indicator DID catch this move via the reversal at the ORB low.

---

## 6. NVDA Upmove 9:43-9:48

### What happened?
NVDA bounced from $180.86 (9:43 low) to $182.77 (9:47 high).

- **Move magnitude:** $180.86 to $182.77 = **$1.91 = 0.29 ATR**
- **Duration:** 5 minutes

### What signals fired?
- No new signal fired between 9:40 and 9:50. The 9:40 bearish ORB H reversal was the last signal before, and the 9:50 bullish BRK ORB H was the next.

### WHY was it missed?
- **Short duration (5 min) and small size (0.29 ATR).** This is a single 5m bar move. The indicator would need to catch this within the same bar it occurs on, which isn't possible on 5m signal TF.
- **Within-bar move.** On the 5m chart, 9:40-9:45 was a down bar (the reversal signal) and 9:45-9:50 was the up bar (which became the BRK ORB H at 9:50).

### How big was the miss?
**0.29 ATR** — but the 9:50 BRK ORB H (CONF ✓) caught the continuation. This 9:43-9:48 sub-move is just the early part of the larger 9:43-10:30 uptrend.

### Verdict: Not a true miss. The 9:50 signal captured the continuation.

---

## 7. NVDA Upmove 10:04-10:30

### What happened?
After pulling back from $182.96 (9:49 high) to $180.58 (9:59 low), NVDA grinded up again from $181.01 (10:04) to $183.64 (10:30 high).

- **Move magnitude:** $180.95 (10:04 low) to $183.64 (10:30 high) = **$2.69 = 0.41 ATR**
- **Duration:** 26 minutes

### What signals fired?
- **None in this window.** The last signal was 9:50 BRK ORB H (CONF ✓ then ✗ at 9:55). The next signal isn't until after 10:30 (if any — the log ends without one).

### WHY was it missed?
- **Level desert after CONF failure.** The 9:50 BRK ORB H confirmed then failed (5m CHECK pnl=-0.11 → BAIL, then CONF ✗ at 9:55). After that, the ORB H level is "used up."
- **Gradual grind.** The move from 10:04-10:30 was a slow, steady climb — no single 5m bar broke a new level.
- **No higher level to break.** ORB H ($182.25) was re-broken around 10:12, but since the level was already triggered (used) at 9:50, it doesn't re-fire.

### How big was the miss?
**0.41 ATR** — meaningful.

### What could catch it?
- **Level re-arm after CONF failure.** If a BRK fires at a level, CONF fails, and price drops below the level then breaks above it AGAIN, the level should re-arm. This happened here: BRK ORB H at 9:50 → CONF ✗ → price dropped below $182.25 → re-broke above at ~10:12.
- **VWAP cross signal** if VWAP was near $181-182 area.

---

## 8. NVDA Downmoves: 9:35-9:42, 9:49-9:58, 10:31 onward

### 8a. NVDA 9:35-9:42 Downmove
- **$182.33 to $180.78 = $1.55 = 0.24 ATR**, 7 minutes
- **Signal fired:** 9:40 ▼ ~ ORB H reversal (vol=5.6x, body=83% ⚠ 🔊). This IS the indicator catching the downmove via a bearish reversal at ORB H.
- **Verdict: CAUGHT** by the 9:40 ORB H reversal. Not a miss.

### 8b. NVDA 9:49-9:58 Downmove
- **$182.96 to $180.87 = $2.09 = 0.32 ATR**, 9 minutes
- **No bearish signal fired.** The 9:50 bullish BRK ORB H was the signal (wrong direction!), which then CONF failed.
- **WHY:** The 9:49 bar went high ($182.96) then reversed. The 9:50 5m bar showed price above ORB H triggering a bullish BRK — but price was already reversing.
- **This is a failed breakout.** The BRK fired bullish, price briefly went above, then collapsed.
- **What could catch it:** A "failed BRK" detection — if CONF ✗ and price drops 0.15 ATR below the breakout level within 2 bars, fire a bearish "faded breakout" signal.

### 8c. NVDA 10:31 Onward Downmove
- **$183.64 (10:30 high) to $181.80 (11:14 low) = $1.84 = 0.28 ATR**, 44 minutes
- **No bearish signal fired.** The log shows no more NVDA signals after 9:55.
- **WHY:** Gradual grind, no level break downward. Same pattern as TSLA 10:30-11:14 — a slow selloff with no clean trigger.
- **What could catch it:** Same as TSLA item #4 — "failed breakout reversal" or EMA cross signal.

---

## 9. SPECIAL: NVDA 9:30 5m Candle — Fires Bullish, Then Goes Down

### What happened?
The 9:30-9:34 5m candle on NVDA: O=$180.41 H=$182.25 L=$180.06 C=$182.19. This is a strong bullish bar (+$1.78, 27% body).

The KLB indicator fired at 9:35 (bar close):
- **▲ BRK Yest H** — vol=12.8x, pos=^97, vwap=above, ema=bull, rs=+0.8%, adx=21, body=74%, ramp=29.3x, rangeATR=3.9 ⚡ 🔊
- Plus VWAP reversal signal (same bar)

Then price immediately reversed downward:
- 9:35: O=$182.19, C=$181.86 (down)
- 9:36: C=$181.58
- 9:37: C=$181.84
- 9:38: C=$181.50
- 9:39: C=$181.23
- 9:40: C=$181.05 (1m low at 9:40 = $180.93)
- 9:41: C=$181.00
- 9:42: C=$180.87 (near session low)

### MAE Analysis
- **Entry at signal close:** $182.19
- **Worst point:** $180.78 (9:42 low) → **MAE = -$1.41 = -0.22 ATR**
- **Recovery:** Price then bounced back through $182.25 at 9:47 and hit $182.96 at 9:49

### Why did the signal fail?
1. **The 5m bar had a huge range** (rangeATR=3.9, i.e., ~$8.91 range on a 5m bar with ATR=$6.52). The bar went from $180.06 low to $182.25 high — a massive opening drive that exhausted itself.
2. **ADX was low (21)** — trend strength was weak.
3. **Volume was extreme (12.8x)** — but this is opening bar volume, always inflated. The ramp=29.3x confirms this was opening-driven volume, not organic breakout volume.
4. **The breakout level (Yest H = $180.90)** was very close to the open ($180.41). Price gapped through it — this isn't a "breakout" in the traditional sense, it's a gap-through.

### Would filters have caught this?
- **EMA gate:** ema=bull at 9:35 — would NOT have filtered it.
- **VWAP:** vwap=above — would NOT have filtered it.
- **ADX:** adx=21 — right at the threshold (ADX>20 is the current filter). If raised to 25, this would be filtered.
- **"First bar filter":** A rule that ignores signals on the very first 5m bar (9:30-9:35) would have avoided this. Opening bars are notoriously unreliable due to gap fills.
- **Body warning:** body=74% — no ⚠ warning. But the real issue isn't body%, it's the gap-through on the opening bar.
- **rangeATR>3 + first bar = unreliable.** Bars this wide on the open are often gap exhaustion moves.

### Key insight
This is the **"opening bar gap-through" failure mode.** Price gapped past a level, the first 5m bar confirmed the breakout, but it was actually an exhaustion move. The subsequent pullback (MAE = -0.22 ATR) killed the signal before it could recover.

**Interesting:** Price DID eventually recover (hitting $182.96 at 9:49, $183.64 at 10:30) — the direction was ultimately correct, but the entry timing was terrible. An entry 5-7 minutes later (at the 9:42 pullback low) would have been ideal.

### Recommendation
- **Delay or reduce confidence on first-bar (9:30-9:35) breakout signals** when rangeATR > 3. These gap-through bars have a "breathe first, then go" pattern. The CONF mechanism partially handles this (it failed), but the signal itself causes confusion.
- **Opening bar filter (optional):** Skip or auto-dim signals on the 9:30-9:35 bar. This is a common pattern — validated by our data showing 9:30-10:00 as best MFE window, but the FIRST bar within that window is the exception.

---

## Summary

### Total ATR Missed

| # | Item | Symbol | ATR Missed | Signal Fired? | Category |
|---|------|--------|-----------|---------------|----------|
| 1 | AMZN upmove 9:46-10:27 | AMZN | 0.94 (0.75 caught at 9:50) | Yes, 9:35 BRK (CONF ✗), 9:50 re-BRK | CONF failure + re-trigger delay |
| 2 | TSLA upmove 9:58 | TSLA | 0.76 (0.14 caught at 10:25) | Late BRK at 10:25 | Level desert / grind |
| 3 | TSLA upmove 11:20 | TSLA | 0.23 | No | Small / afternoon → acceptable miss |
| 4 | TSLA downmove 10:30-11:14 | TSLA | 0.42 | Reclaim at 11:15 (too late) | Gradual grind / no level break |
| 5a | SPY upmove 9:46-11:03 | SPY | 0.80 (0.25 caught at 10:20) | Late BRK at 10:20 | Level desert / CONF failure |
| 5b | QQQ upmove 9:46-11:03 | QQQ | 0.77 (0.61 caught at 9:50) | 9:50 ORB L reversal | Mostly caught |
| 6 | NVDA upmove 9:43-9:48 | NVDA | 0.29 (caught at 9:50) | 9:50 BRK ORB H | Caught (within-bar) |
| 7 | NVDA upmove 10:04-10:30 | NVDA | 0.41 | None | Level re-arm / grind |
| 8a | NVDA down 9:35-9:42 | NVDA | 0.24 | 9:40 ORB H reversal | CAUGHT |
| 8b | NVDA down 9:49-9:58 | NVDA | 0.32 | 9:50 BRK bull (wrong dir!) | Failed BRK, no fade signal |
| 8c | NVDA down 10:31+ | NVDA | 0.28 | None | Gradual grind |
| 9 | NVDA 9:30 bullish→fail | NVDA | -0.22 MAE | BRK at 9:35 | Opening bar gap-through |

**Total ATR across all items: ~5.46 ATR**
**ATR actually caught by existing signals: ~1.75 ATR**
**Net missed: ~3.71 ATR** (across 5 symbols, 1 session)

### Common Patterns

**Pattern 1: "Gap-and-Pullback CONF Failure" (Items 1, 5a, 5b, 9)**
All 5 symbols fired bullish BRK at 9:35 with strong conditions (vol 8-16x, ema=bull, vwap=above). ALL had CONF ✗ at 9:40 because the second 5m bar pulled back. But the overall direction was correct — every single one continued higher after the pullback.

This is the #1 systemic issue: **On gap-up days, the first bar fires correctly but CONF fails due to natural pullback.** The indicator is "right but too early."

**Frequency:** 5/5 symbols (100%) on March 4. This pattern likely occurs on every strong gap day.

**Pattern 2: "Level Desert Grind" (Items 2, 4, 7, 8c)**
After the opening breakout signals, price enters a zone between levels where no new signals fire. The move is gradual (0.3-0.8 ATR over 20-45 min) with no single bar breaking a new level. The indicator goes silent during meaningful moves.

**Pattern 3: "Failed Breakout Without Fade Signal" (Item 8b)**
NVDA 9:50 BRK ORB H confirmed then immediately reversed. The indicator fires BRK, CONF fails, but has no mechanism to fire a signal in the OPPOSITE direction after the failure.

### Comparison to Existing Research

| Finding | Matches? | Details |
|---------|----------|---------|
| "Morning 9:30-10 best MFE" | YES | All major moves started in this window |
| "CONF ≠ follow-through" | YES | 5/5 opening BRKs had CONF ✗ but direction was correct |
| "Afternoon = 0% GOOD" | YES | TSLA 11:20 upmove was only 0.23 ATR, not worth chasing |
| "EMA alignment = strongest filter" | PARTIAL | ema=bull was correct for direction, but didn't prevent false signals |
| "5-min gate strongest predictor" | YES | The 5m CHECK BAIL signals accurately flagged the immediate pullback |
| "Vol >=5x = best" | MIXED | High vol on first bar (12-16x) predicted direction but not timing |

### Actionable Improvements

**High Impact:**
1. **CONF lookahead extension** — Instead of 1-bar CONF (immediately after signal), allow 2-3 bar CONF window. If price holds above breakout level within 3 bars, confirm. This would have saved 4/5 of the opening BRK signals.
2. **Level re-arm after CONF failure** — If a signal fires at a level, CONF fails, price drops below the level, then re-breaks it, the level should re-fire. This catches the "second attempt" breakout (AMZN 9:50, NVDA 10:12 re-break of ORB H).
3. **Opening bar caution** — Either dim or delay signals on the 9:30-9:35 bar when rangeATR > 3. These gap-through bars have exhaustion risk.

**Medium Impact:**
4. **Failed breakout fade signal** — When BRK fires, CONF fails, and price drops 0.15+ ATR below the breakout level within 2 bars, fire a reverse signal. This catches items like NVDA 8b.
5. **VWAP cross signal** — A bullish/bearish signal when price crosses VWAP from the opposite side during a trend (not at a level). This catches the "grind through VWAP" moves in level deserts.

**Low Impact (not worth the complexity):**
6. "Grind detector" for consecutive higher/lower closes — over-engineering risk.
7. EMA cross as standalone signal — needs backtesting, may produce too many false signals.

### Key Takeaway

March 4 was a classic "gap-up with pullback" day. The indicator's direction detection was **100% correct** — every first signal was bullish and the market went up. The problem was exclusively **timing and confirmation**:

- CONF failed on all 5 symbols because of the natural pullback after the opening gap
- After CONF failure, the indicator went quiet during the main move due to level deserts
- The signals that DID fire later (AMZN 9:50, QQQ 9:50, SPY 10:20, TSLA 10:25) caught portions of the moves

**Estimated capture rate: 32% of total ATR opportunity.** With CONF lookahead extension and level re-arm, this could rise to ~65-70%.
