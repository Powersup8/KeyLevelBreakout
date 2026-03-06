to investigate:
investigate each why we didnt fetch it, how far it went, so we can see what we lost. And what is the pattern, the big picture before, in and after. Think and investigate how to fetch it, get creative and go smart ways. use the cache candle data you need to use.
get only the new ones, we didn't investigate before. make a detail report and a summary. compare to our other findings. And if we could use other findings we have but didnt use or in other circumstances.
I put some pine logs into the folder.
after that: investigate each signal on the past if we fetch it right, how far it went, so we can see what we got. was it right
  or false.  And what is the pattern, the big picture before, in and after. Think and investigate how to fetch it,
  get creative and go smart ways. use the cache candle data you need to use.
  do this to all data(signals) avaible. make a detail report and a summary. compare to our other findings. And if we
  could use other findings we have but didnt use or in other circumstances.


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
1. ⚠ IMPLEMENT: Exempt REV signals from EMA Hard Gate (TSLA 10:16 miss = documented false negative)
2. ⚠ IMPLEMENT: PD Mid → FADE signal instead of BRK (4/4 BRK BAIL + new-levels research: FADE = +0.396/touch)
3. INVESTIGATE: BAIL too aggressive on trending days? (91.7% BAIL rate on March 5)
4. INVESTIGATE: TSM total suppression — is the filter combination too restrictive?
5. CONSIDER: Afternoon full suppression after 11:30 (would save ~38 ATR/5 days)
6. CONSIDER: Cross-symbol market regime (SPY direction → alert correlated symbols)
7. DATA: Need v3.0b pine logs for GOOGL, GLD, SLV (add TradingView charts)
8. DATA: BATS vs IB price offset — update analysis scripts to handle correctly

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