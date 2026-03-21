to investigate:
investigate each why we didnt fetch it, how far it went, so we can see what we lost. And what is the pattern, the big picture before, in and after. Think and investigate how to fetch it, get creative and go smart ways. use the cache candle data you need to use.
get only the new ones, we didn't investigate before. make a detail report and a summary. compare to our other findings. And if we could use other findings we have but didnt use or in other circumstances.
I put some pine logs into the folder.
after that: investigate each signal on the past if we fetch it right, how far it went, so we can see what we got. was it right
  or false.  And what is the pattern, the big picture before, in and after. Think and investigate how to fetch it,
  get creative and go smart ways. use the cache candle data you need to use.
  do this to all data(signals) avaible. make a detail report and a summary. compare to our other findings. And if we
  could use other findings we have but didnt use or in other circumstances.


3/20/26 TSLA Scalp Indicator — INVESTIGATED
why MED after 4m baerish down 2.5$?

ANSWER: conf scored 3/5 (checks: PM pos ✓ 0.433, PM accel ✗ -1.95, VIX ✓ 24.1, align ✗ T↓S↓Q↓, no gap ✓).
The 3 passing checks are STRUCTURAL (position in PM range, VIX level, gap size) — not DIRECTIONAL.
The 2 failing checks (accel, alignment) ARE directional — both screaming bear. But 3/5 = MED threshold.

The problem: pm_acc=-1.95 is the most negative in the entire 22-day dataset, pm_trend=-1.36 (falling hard),
align=T↓S↓Q↓ (everything down), p9_30s=DN. EVERY directional signal was bearish.

1s data shows the crash: open $379.60, by 9:30:06 already $377.01 (-$2.59 in 6 seconds!), SL breached at 9:31:42,
day low $373.34 at 9:36:37. The -$2.50 in 4m was actually -$6.26 in 6.5 minutes.

RESULT: CALL direction was WRONG. Dip-buy entry at $377.18, SL hit 1 minute later at $376.21 (loss -$0.97).
ORB BEAR confirmed at 9:35 (pnl -$3.00).

IF PUT: Entry $379.60 at open → exit at 9:32 close $375.57 → PUT PnL = +$4.03. The $2 PT ($377.60) was hit
at 9:30:06 (6 seconds!). This was a textbook PUT day that the v1.4 system would have caught IF conf had been <=2.

ROOT CAUSE: conf system weights structural checks equally with directional checks. A day can score 3/5 with
zero directional confirmation. The fix: either add a directional meta-check ("if ALL directional signals bear,
cap conf at 2 regardless of structural score") or weight PM accel/alignment higher.

PROPOSED FIX: Add a "directional override" — if pm_accel < -1.0 AND pm_trend < -1.0 AND align all down,
force tier to LOW regardless of conf score. This catches 3/20-type days where structure says MED but
direction says strong bear. Needs backtesting before implementing.

V1.4 PERFORMANCE SUMMARY (22 days, Feb 17 — Mar 20):
  PUT days (14): 9 wins (64%), total +$14.33, avg +$1.02/trade
  CALL days (8): 6 wins (75%), total +$24.54, avg +$3.07/trade (includes runners)
  COMBINED: +$38.87 over 22 days (+$1.77/day avg)
  3/20 was the only CALL day that should have been PUT. Cost: -$0.97 CALL loss + $4.03 missed PUT = -$5.00 total.

---

3/19/26 — INVESTIGATED → this conversation + debug/tsla-put-backtest-findings.md
TSLA what did the big red labels mean and if it would be an entry, how it would worked out the next 3/5/10/20/60m?
did they even fire in the right direction?

ANSWER: The "big red labels" were SL HIT — EXIT ($380.65 at 9:36). This was on a LOW (2/5) day — the indicator
said "WATCHING" (not entered), so the SL HIT label was confusing noise. There was no position to exit.

v1.4 fixes this: SL HIT and ORB BEAR labels are now suppressed on PUT days. Instead, v1.4 shows:
  9:30: PUT ZONE — short $387.23 (orange label)
  9:30: BAR1 RED — ADD PUT (bar1 red, range $5.19, chaotic)
  9:32: PUT EXIT 2m — $+4.77

The open ($387.27) was literally the day high. Price never went above it.
Full IB 1m data: long from $387.23 → MFE only +$0.04 (never went up), MAE -$7.51.
Short from $387.27 (gap fade) → MFE +$7.55, MAE $0.00 (zero adverse excursion).

3/19 was a textbook PUT day: LOW tier, bar1 RED+chaotic, immediate selloff.

ALL SYMBOLS 3/19: Most symbols were BULL (SPY +$2.77, QQQ +$3.48, AMD +$10.14). TSLA was the outlier —
gapped up and faded while market rallied. META also gap-faded (-$5.45). TSLA was decoupled from market.



3/9/26 — INVESTIGATED → debug/investigation-2026-03-09.md + debug/deep_investigation_20260309.md
V-shaped bull recovery day. SPY ATR=$9.45. All 11 major moves were bull. KLB caught late BRK cluster (15:15+).

TSLA 9:30 bull vs 9:35 bear → CORRECT behavior. RNG fires on bar close. 5-min rule resolves: 9:35 close < open → cancel bull RNG. v3.7 note: VWAP reclaim at 10:45 (+0.21 ATR) is the real TSLA entry.
TSLA uptrend after 10:12 → Level desert + EMA bear all morning. VWAP reclaim at 10:45 (v3.7 would catch). Full move = 1.38 ATR but uncatchable from open.
SPY 9:36-9:53 downtrend late → Only -0.35 ATR total. Sub-threshold. RNG was correct response.
SPY/QQQ 9:54-10:04 upmove → +0.31 ATR bounce. Not a quality signal.
SPY/QQQ 10:05-10:13 "massive" down → Only -0.38 ATR (SPY ATR=$9.45). No level broken. Correct: no signal.
SPY/QQQ 10:14 long uptrend → v3.7 VWAP Reclaim at 10:20 (SPY entry 665.29, MFE=0.46 ATR). IMPLEMENTED.
NVDA 9:33-10:44 "down missed, signaled up" → WRONG framing. NVDA went DOWN only -0.42 ATR at open, then held above VWAP all morning. VR fired at 09:55 (MFE=0.386 ATR). Was leader, not laggard.
NVDA 9:46 uptrend missed → See above. 09:55 VR would catch it in v3.7.
META signals false → NOT false. All caught the real -0.43 ATR bear leg. Day reversed after. v3.7 adds bull VR at 10:00/10:20 for the recovery.
No HQ signals → Real quality trade was 15:15-15:40 BRK cluster (5 symbols, all CONF✓). V-days are KLB's blind spot.

Key findings:
- v3.7 VWAP Reclaim catches 4/18 missed moves (SPY 10:20, AMZN 10:15, META 10:00, NVDA 09:55)
- 47 total VR signals on this day (31 bull, 16 bear), 17 HQ (MFE>0.30 ATR)
- SPY ATR mismatch: $3.54/7min = 0.38 ATR (ATR=$9.45 — high-volatility period)
- DST: US DST started 3/8/26. ET=UTC-4, Berlin=UTC+1, offset=5h until EU DST (~3/29)
→ RESOLVED: v3.7 implements VWAP Reclaim + SPY reclaim DIM + large-candle bypass



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
NVDA 9:45-10:30 down → INVESTIGATED 2026-03-09 [WRONG FRAME — actual move was 11:05-12:50]
  Price: 184.06 → 177.88 = 6.18 pts = 0.99 ATR (day high to day low)
  Root cause: The "9:45-10:30" window was NOT a real downmove (-0.05 pts net, 0.01 ATR chop).
    The real sustained downmove: 11:05 high (184.06) → 12:50 low (177.88) = 0.99 ATR over 105 min.
    Split into two phases:
      Phase 1 (11:05–12:28): 184.06 → 181.07 = 2.99 pts grind (0.48 ATR, 75 min, LOW VOLUME)
      Phase 2 (12:29–12:50): 181.07 → 177.88 = 3.19 pts flush (0.51 ATR, 22 min, VOLUME SPIKE 1M+/bar)
  KLB signals in window (11:05–12:40):
    11:35 ▲ ~~ VWAP (DIM bull — EMA flipped bull during 9:45-10:50 rally, vol=0.8x)
    12:40 ▼ BRK Yest L → FIRED + CONF ✓ + HOLD (caught Phase 2 late)
    NOTHING between 11:05 and 12:40 — 95-min signal desert
  Why no signal 11:05–12:29 (Phase 1):
    1. EMA GATE: EMA flipped BULL during the 9:45–10:50 rally to 182.80.
       All bear BRK signals require ema=bear — still bull at 11:05-12:29.
       Confirmed: 11:35 log shows ema=bull; 12:40 log shows ema=bear (EMA crossed back).
    2. LEVEL DESERT: Price drifted through 8 levels (PD Last Hr High, PD Close, ORB High,
       PD Mid, PD Last Hr Low, Today Open, ORB Low, PD Low) but all generated DIM or no signal.
       The only clean non-dim BRK was "Yest L" (~179.50 on TV) which price only reached at 12:29.
    3. GRADUAL GRIND: Phase 1 was 75-min slow bleed with low volume (vol ~0.8-1.5x) —
       volume gate + slow approach = multiple dim signals instead of clean BRKs.
  Nearest level at move start: PD Last Hr High (183.86) — 0.034 ATR from 184.06.
    This generated a DIM bull REV at 10:55 (ema=bull, correct direction but already falling).
  Recoverable ATR:
    If BRK PD Low (~12:30, entry ~180.00): MFE to low = 2.12 pts = 0.34 ATR
    If earlier ORB High BRK (~10:25, entry ~182.00): MFE to 177.88 = 4.12 pts = 0.66 ATR
    Actual catch (12:40 Yest L): 1.62 pts = 0.26 ATR (but was a HOLD signal)
  Verdict: NOT a KLB miss — correct behavior given EMA state.
    Phase 1 was unactionable (EMA bull, low-vol grind).
    Phase 2 was caught correctly at Yest L (12:40).
    The "9:45-10:30" framing was misleading — that period was actually a RALLY (+1.7 pts to ORB H).
  Improvement opportunity: PD Low BRK at 12:30 (vol 1M+ spike, ema=bear by then) was not fired
    because "Yest L" fired instead just 10 bars later. PD Low = 180.06 vs Yest L = ~179.50 (TV).
    Gap = BATS vs IB price discrepancy (~0.5 pts). Not a real miss.

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
   RESEARCHED 2026-03-09: VALIDATED. Signal quality at 0.03–0.05 ATR is EQUAL to exact-touch.
   - great%=42.7%, noise%=8.0%, mfe/mae=4.24x vs touching: 45.3%, 6.7%, 4.22x
   - False alarm rate flat at 40% across ALL distance buckets (inherent property of HIGH levels)
   - TSLA 9:57 confirmed: dist=0.029 ATR, mfe=0.319 in move catalog
   - Expected gain: +5.6–10 ATR/symbol/year (N=1,517 over 2yr, 15 symbols)
   - IMPLEMENT: bear REV at HIGH levels fires when price within 0.03 ATR of level
   → RECOMMENDED: Start conservative at 0.03 ATR; can expand to 0.05 ATR after validation
→ ACTION 2 (LOW, was MEDIUM): Opening-bar level re-arm timer — if opening bar rangeATR > 3.0, re-arm
   consumed levels after 30 min. Would restore v2.8a's 10:25 BRK ORB_H signal in v3.4.
   RESEARCHED 2026-03-09: LOW PRIORITY — do not implement yet.
   - Big-open threshold >4.0 fires 24% of days (too common); >3.0 = 47% of days (meaningless)
   - TSLA 3/4 10:30 downmove was 0.34 ATR from ORB High — re-arm would NOT have caught it
   - Expected gain: ~1.6 ATR/symbol/year (4–6x less than proximity tolerance)
   - High implementation complexity: per-level consumed-state tracking + re-arm timer
   - Big-open days actually have BETTER move quality after 10am (great=43.9% vs 38.8% normal)
   → DEFER: Proximity tolerance addresses the motivating case; re-arm doesn't
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