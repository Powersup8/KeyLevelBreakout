to investigate:
investigate each why we didnt fetch it, how far it went, so we can see what we lost. And what is the pattern, the big picture before, in and after. Think and investigate how to fetch it, get creative and go smart ways. use the cache candle data you need to use.
get only the new ones, we didn't investigate before. make a detail report and a summary. compare to our other findings. And if we could use other findings we have but didnt use or in other circumstances.
I put some pine logs into the folder.
after that: investigate each signal on the past if we fetch it right, how far it went, so we can see what we got. was it right
  or false.  And what is the pattern, the big picture before, in and after. Think and investigate how to fetch it,
  get creative and go smart ways. use the cache candle data you need to use.
  do this to all data(signals) avaible. make a detail report and a summary. compare to our other findings. And if we
  could use other findings we have but didnt use or in other circumstances.


3/6/26 — INVESTIGATED → debug/investigation-2026-03-06.md
NVDA 15:50 alert "RNG up Range+Vol" but no label → INVESTIGATED: NOT a code bug. FIFO label eviction.
AMD 12:05 down → 0.24 ATR. Midday desert + EMA gate. No action needed.
TSLA 11:05 down → 0.05 ATR. Noise, not a real move.
TSLA 12:40 up → 0.32 ATR. EMA gate + midday. Correct suppression.
TSLA 13:15 bull → 0.06 ATR. Move was exhausted by signal time.
NVDA 9:30 up → 0.29 ATR. Signal fired 9:35 but no CONF (EMA bear). Volume 11.1x — consider vol-override research.
NVDA 12:00 down → 0.27 ATR. EMA gate + midday. Correct suppression.
META 9:30 bear → FALSE MISS. Auto-R1 CONF was there. User didn't see it on chart → CONF visibility issue.
META 9:35 up → 0.34 ATR. Intra-bar reversal inside massive bear candle. Uncatchable.
META 10:30 bear → No signal needed. META was going UP at that time.

Summary: 1.12 ATR real misses. Midday desert (#1 gap). EMA gate correct. 3/9 were false alarms.
→ ACTION: Forward-test v3.2 midday levels. Investigate CONF label visibility. Low-pri: vol-override auto-confirm.


3/5/26 — INVESTIGATED → debug/investigation-2026-03-05.md + debug/v30b-move-scanner-research.md
TSLA signal 9:29 PD Mid → ✅ BRK ▼ PD Mid, CONF ✓ auto-R1, BAIL at 9:35 (pnl=-0.25 ATR). Wrong direction — price went UP.
TSLA signal 9:34 RNG up → ✅ 3 RNG ▲ fired (vol 3.9x-13.5x). Suppressed as BRK by EMA Gate (bull sig, bear EMA)
TSLA upmove 9:30 → RNG caught it. BRK missed (fakeout bear at PD Mid)
TSLA downmove 10:01-10:31 → ❌ NO SIGNALS. No key level broken during this move.
TSLA 10:16 not fired → ❌ CONFIRMED: EMA Hard Gate killed the bearish REV at Yest H.
  EMA flipped to bull after 7pt rally (401→408). Bear REV = counter-EMA → suppressed at signal generation level.
  v2.8/2.9 would have caught it (no EMA gate). CODE VERIFIED: line 831 emaGateBear=false + isPre950=false = signal killed.
  ⚠ DESIGN FLAW: Reversals are counter-trend BY NATURE. EMA gate on REVs = logically contradictory.
  → ACTION NEEDED: Exempt REV signals from EMA Hard Gate.
TSLA upmove 10:32 → ❌ NO SIGNALS. System silent on TSLA from 9:35-15:55.
TSLA downmove 12:06 → ❌ NO SIGNALS for TSLA.
SPY/QQQ/AMD/NVDA downmove 12:06 → Continuation of morning weakness. SPY broke ORB L at 10:25.
  NVDA caught it at 12:40 (BRK Yest L), AMD at 12:50 (BRK PM L + ORB L). 30-40 min lag.
  QQQ had dim REV at ORB H 12:10. Cross-symbol trigger detectable but midday dead zone.
NVDA 9:40 down → ✅ CORRECTLY SUPPRESSED — NOT a real miss (investigated 2026-03-09)
  Signal DID fire: `9:40 ▼ ~ x~ ORB H` — but killed by TWO independent filters:
  1. vol=7.1x → exhaustion dim (>5x threshold, v3.3 logic)
  2. body=23% → below body filter (pin bar / shooting star, no directional commitment)
  Move: 182.46 → 180.90 = 1.56 pts = 0.25 ATR over 9 minutes. Immediately fully recovered.
  Real best exit: only 0.095 ATR MFE by 10:32 — well below 0.3 ATR threshold for quality trade.
  The "real" NVDA bear signal that day: 12:40 BRK Yest L → KLB caught it correctly.
  v3.5: identical — same 6 signals, same suppression. No change needed.


Key findings 3/5:
- BAIL epidemic: 11/12 signals BAILed (91.7%). Only 1 HOLD (SPY 10:05 BRK PD LH L).
  Trending bear day, correct-direction signals kept getting cut. 5m check may be too tight for trending days.
- 27 suppressions vs 18 signals = over-filtering (60% more suppressed than allowed)
- TSM: 0 tradeable signals despite touching 6 different levels (PM H, Yest H, ORB H, VWAP, Yest L, PM L)
- CONF rate 87.5% (Auto-R1 all-day working well)
- PD Mid BRK = ALL BAIL (4/4). Confirms magnet-not-barrier finding.
- Symbol identification: TradingView BATS prices differ from IB by 0.5-2.5 pts
- GOOGL, GLD, SLV NOT in v3.0b pine logs (need to add charts)

5-day backtest findings (debug/v30b-move-scanner-research.md):
- 1,054 significant moves in 5 days. v3.0b catches 4.2% (by design — key-level system).
- EMA Hard Gate VALIDATED: saved +20.47 ATR (18 suppressed, 94% losers)
- Afternoon signals = -38.34 ATR (43 signals, 22% win). Should suppress entirely after 11:30.
- Cross-symbol triggers: 259 instances of 4+ symbols moving together.
  Morning bear 9:40-10:15 = best edge (+1.058 ATR, 63% win, N=17)
  5-symbol > 10-symbol (exhaustion when all move). Individual stocks lead, NOT SPY/QQQ.
- NOT over-optimized. EMA gate works. Afternoon is the biggest PnL drag.

---
🔴 NEXT ACTIONS:
1. ✅ DONE (v3.1): REV EMA exemption — TESTED & REVERTED. -11.8 ATR, 35% win. Data > intuition. EMA gate stays.
   → OPEN: Investigate alternate trigger for high-quality extended reversals (TSLA 10:16 type). Agent running.
2. ✅ DONE (v3.1): PD Mid → REV signal (touch-and-turn, no EMA gate). Magnet level, BRK was wrong type.
3. ✅ DONE (v3.1): BAIL fixed via SPY Market Regime. +15.5 ATR. Aligned=never BAIL, neutral=loose, opposed=strict.
4. INVESTIGATE: TSM total suppression — is the filter combination too restrictive?
5. ~~CONSIDER: Afternoon full suppression~~ — DROPPED. Problem is signal TYPE not TIME. Fix signal types first.
6. ✅ DONE (v3.1): SPY regime implemented as BAIL modifier + Runner Score factor.
7. ✅ DONE: GOOGL/GLD/SLV charts added to TradingView.
8. LOW PRIORITY: BATS vs IB price offset — calibration fix for analysis scripts only.

---
3/4/26 — INVESTIGATED → debug/investigation-2026-03-04.md
AMZN upmove 9:45 on didnt fire
TSLA upmove 9:58 & 11:20
TSLA downmove 10:30-11:14
SPY/QQQ upmove 9:46
NVDA upmove 9:43-9:48 & 10:04-10:30
NVDA downmove 9:35-42 & 9:49-9:58 & 10:31
NVDA 9:30 5m candle fires bullish but goes down then
SPY upmove 9:46-11:03
AMZN upmove 9:46-10:27
Key findings: Gap-and-Pullback CONF Failure (5/5 symbols), Level Desert Grind, 32% capture rate (1.75/5.46 ATR)

TSLA 3/4/26 — DEEP INVESTIGATION (v3.4/v3.5 validated 2026-03-09)
Root cause: Enormous opening bar (rangeATR=5.9, L=394.55 H=403.47) consumed ALL nearby levels in 5 minutes.
Left v3.4 with 4 signals at 9:30–9:35 and ZERO signals the rest of the day despite 2 meaningful moves.

TSLA upmove 9:57–10:28 (+0.76 ATR) — WHY MISSED:
  → 9:35 VWAP REV (bull) fired but no CONF — opening bar too wild, CONF never formed
  → Actual bounce at $396.72 (9:57) was 0.026 ATR above Yest H ($396.34) — came within $0.38 but didn't TOUCH
  → Level desert: bounce happened between Yest H and ORB_L with no level hit
  → Root cause: proximity tolerance. 0.026 ATR is economically a Yest H reversal. Signal needs ~0.05 ATR buffer.
  → Magnitude: $11.14 = 0.76 ATR over 31 min. Fully recoverable miss.

TSLA downmove 10:30–11:14 (-0.42 ATR) — WHY MISSED:
  → ORB_H ($403.47) was consumed by 9:35 RNG opening bar — level "used up", no re-arm
  → Price above ORB_H all the way to 10:30 peak ($407.79) — no resistance level overhead
  → Failed BRK: 9:35 bar broke ORB_H but never confirmed (no CONF ✓). Re-crossed below ORB_H at 11:10.
  → No "failed BRK reversal" signal type in system. v2.8a fired BRK ORB_H at 10:25; v3.4 does not.
  → Root cause 1: Opening bar level consumption (no re-arm after 30min).
  → Root cause 2: No "failed breakout" reverse signal type.
  → Magnitude: $6.17 = 0.42 ATR over 44 min. Partially recoverable.

TSLA upmove 11:14–11:30 (+0.21 ATR) — ACCEPTABLE MISS:
  → Bounce from $401.62, PM_H ($402.04) only $0.42 overhead — no clean level support below
  → 0.21 ATR, below threshold. Afternoon context. No action needed.

v3.5 comparison: Identical to v3.4 on this day. Changes in v3.5 (adaptive SL, afternoon suppress) don't affect opening-bar level consumption or proximity tolerance. Still 4 signals, all at 9:30–9:35.

Pattern: v3.4/v3.5 catches moves cleanly when direction aligns with trend + price breaks a defined level.
Struggles when: (1) opening bar swallows all levels, (2) bounce near but not AT a level, (3) failed BRK re-crosses.

TOTAL RECOVERABLE MISSED: ~1.18 ATR (0.76 + 0.42)

→ ACTION 1 (HIGH): Near-level proximity tolerance for REV signals — 0.03–0.05 ATR buffer.
   The 9:57 Yest H reversal was 0.026 ATR away. Tier S fingerprint avg level distance = 0.065 ATR.
   Risk: noise from levels that don't hold. Needs research validation before implementing.
→ ACTION 2 (MEDIUM): Opening-bar level re-arm timer — if opening bar rangeATR > 3.0, re-arm
   consumed levels after 30 min. Would restore v2.8a's 10:25 BRK ORB_H signal in v3.4.
→ ACTION 3 (LOW): Failed BRK reverse signal — when no-CONF BRK bar is followed 30+ min later
   by re-cross in opposite direction → fire reverse signal. Complex, needs research.

---
🔴 NEXT MEETING: Open Call Management — Research Complete, Ready for Trading Setup

**The 5-Minute Rule (271 days TSLA, validated on NVDA/AMZN/SPY):**
- At 9:35: price above open → HOLD calls (67% bull, +$3.22 avg)
- At 9:35: price below open → BAIL (32% bull, -$3.64 avg) — $6.87 EV gap
- Best signal: 1m down → 5m up (reversal) = 72% bull, +$3.67
- Not recovered by 5m → 82% losing day, avg -$7.71

**Level Bounce (4 symbols, 476 days):**
- $1-2 dips at 5d+ level = +12-21pp edge (NVDA/AMZN/SPY)
- HIGH-turned-support > LOW levels across all symbols
- AMZN opens bearish 57% — persistent, not regime-dependent

**TODO: Design into tradeable setup**
1. Pre-market checklist: identify 5d+ levels within $1-2 of expected open
2. Define entry/exit: buy dip at level, hold if 5m up, bail if 5m down
3. KLB integration: pre-market level proximity alert?
4. Can the 5-min rule improve KLB CONF exits? (hold ✓ if 5m up, bail if down)

**Full findings:** `debug/open-scalp-learnings.md` (Parts A-F)