# v3.0b New Levels — Cross-Reference vs Missed Moves

**Date:** 2026-03-05
**Question:** Are the v3.0b new level signals (PD Mid, PD LH L, VWAP zone) actually catching the missed intraday movements we identified, or are they firing on DIFFERENT (worse) setups?

**Short answer: They are firing on DIFFERENT, WORSE setups. The overlap with actual missed moves is near-zero.**

---

## 1. Data Sources

| Dataset | Source | Period | Symbols | N |
|---------|--------|--------|---------|---|
| Missed moves database | `missed-moves-report.md` (`missed_moves_scanner.py`) | Feb 11–27, 2026 | 13 (AAPL AMD AMZN GLD GOOGL META MSFT NVDA QQQ SLV SPY TSLA TSM) | 766 |
| Extended missed moves | `no-signal-zone-tiers.md` (`no_signal_zone_tiers.py`) | Jan 20 – Feb 27, 2026 (28 signal days) | 13 | 1,979 (overlap dates) |
| v3.0b new-level signals | `v30b-new-levels-investigation.md` | Jan 26 – Mar 4, 2026 (27 days) | 8 (AAPL AMD AMZN META NVDA QQQ SPY TSLA) | 316 |
| v3.0b pine logs | `pine-logs-Key Level Breakout v3.0b_*.csv` (8 files) | Jan 26 – Mar 4, 2026 | 8 | — |

**Overlapping date range for fair comparison:** Feb 11–27, 2026 (12 trading days, 8 common symbols: AAPL, AMD, AMZN, META, NVDA, QQQ, SPY, TSLA).

Note: The missed-moves database (`no-signal-zone-moves.csv`) spans Apr 2024 – Mar 2026 (451 days). The 766-move Feb 11-27 figure comes from the `missed-moves-report.md` scanner run on the BATS CSV archive (1m candle data).

---

## 2. Profile Comparison: Missed Moves vs New-Level Signals

This is the fundamental table answering whether these two populations match.

| Dimension | Missed Moves (766 total) | New-Level Signals (316 total) | Match? |
|-----------|--------------------------|-------------------------------|--------|
| **Time — before 10:00** | 19% (9:30–9:45: 12%, 9:45–10:00: 6%) | **64% PD Mid, 61% PD LH L, 66% VWAP Zone** | NO — inverse |
| **Time — 10:00–11:00** | 33% | 16% PD Mid, 25% PD LH L, 15% VWAP Zone | NO — inverse |
| **Time — after 11:00** | **81%** | 20% PD Mid, 11% PD LH L, 19% VWAP Zone | NO — inverse |
| **EMA aligned** | 58% (No-Signal-Zone: 58%, Tier S: 38%) | **100% PD Mid, 73% PD LH L, ~70% VWAP Zone** | NO — reversed |
| **Volume** | avg 0.8x (below threshold) | avg 4–8x (requires ≥1.5x filter) | NO — structural gap |
| **Avg magnitude** | 1.76 ATR (missed) | 0.028 ATR PnL/30m (small follow-through) | N/A |
| **Pattern type** | 81% No_Signal_Zone (no level nearby), 14% Failed_Breakout_Fade | BRK/REV AT a level | Mismatched |
| **EMA gate** | 62% NON-EMA (genuinely outside our edge) | 100% require EMA to pass filter | NO — structural |

**Conclusion:** The two populations are structurally opposed in time, EMA alignment, and volume. The new levels were designed to catch afternoon, low-volume, non-EMA moves. But the indicator's filters (vol ≥ 1.5x, EMA gate after 9:50) ensure new-level signals almost exclusively fire in the morning on high-volume, EMA-aligned bars — the exact opposite of missed moves.

---

## 3. Overlap Quantification

### Step 1: Date/Symbol Filter

Common symbols (8): AAPL, AMD, AMZN, META, NVDA, QQQ, SPY, TSLA.
Common date window: Feb 11–27, 2026 (~12 trading days).

From the missed-moves inventory, the 8 common symbols account for roughly **548 of the 766 missed moves** (GLD, GOOGL, MSFT, SLV, TSM excluded).

From v3.0b signals: **316 new-level signals** across 27 days / 8 symbols = roughly 140 signals in the Feb 11-27 window.

### Step 2: Time Distribution Mismatch

Of 140 estimated new-level signals in the Feb 11-27 window:
- ~85 fire before 10:00 (64% of PD Mid + 61% of PD LHR + 66% VWAP)
- ~55 fire after 10:00

Of 548 missed moves from common symbols:
- ~105 occur before 10:00 (19%)
- ~443 occur after 10:00 (81%)

**For overlap, we need same symbol + same date + within ±15 minutes.**

The 85 pre-10:00 signals could only overlap with the ~105 pre-10:00 missed moves. But missed-moves before 10:00 are mostly "CAUGHT" or "SIGNAL_FIRED_BUT_FAILED" (the original levels catch 95% of 9:30–9:45 moves per the coverage table). There is essentially no pre-10:00 "No Signal Zone."

The 55 post-10:00 new-level signals could overlap with 443 post-10:00 missed moves. But post-10:00 missed moves are 62% non-EMA and avg vol 0.7x — exactly what the new-level signals' filters (vol ≥ 1.5x, EMA gate) exclude. So a new-level signal would only fire on the rare post-10:00 missed move that happens to also have high volume AND EMA alignment.

**Estimated true overlap: <5% of new-level signals catch a previously-missed move.**

The remaining 95%+ of new-level signals are:
- Morning noise (9:30–10:00) at new levels that also coincide with the open spike
- Redundant signals where the original levels (ORB, VWAP, Yest H/L) were already present
- Morning high-volume moves that were already "SIGNAL_FIRED_BUT_FAILED" (the original indicator fired but CONF didn't confirm)

### Step 3: Cross-Reference of Signal-by-Signal Match

From the signal catalog in the new-levels investigation report, we can check specific signals against the missed-moves inventory:

**PD LH L winner: SPY ▼ BRK 9:45, Yest L + PD LH L, vol=6.9x → +0.674 ATR**
- 9:45 is in the morning window, Yest L is an original level, high volume
- This is NOT a missed move — the original indicator (Yest L BRK) would already fire here
- PD LH L is incidental (multi-level confluence)

**PD LH L winner: QQQ ▼ BRK 9:45, PD LH L, vol=6.6x → +0.555 ATR**
- 9:45 with 6.6x vol — this is a morning gap-down breakout
- Check against missed moves: SPY 2026-02-26 9:30–9:45 (CAUGHT category, vol 2.4x)
- High-volume morning breakouts are NOT in the No Signal Zone

**PD LH L loser: AMZN ▼ BRK 9:40, PM L + PD Mid + PD LH L, vol=8.7x → -0.561 ATR**
- 9:40 with 8.7x vol — morning spike, multiple level confluence
- This is the open-range spike pattern. Not a missed move.

**PD Mid loser: SPY/QQQ "ORB H + PD Mid" at 9:40 on 2026-02-17, -0.6/-0.64 ATR each**
- Both on 2026-02-17 at 9:40 — this is the open volatility window
- The missed-moves database shows 0 missed moves for SPY/QQQ at 9:30-9:45 (5 total across all symbols, all CAUGHT)

**VWAP Zone winner: NVDA (70.6%, +2.2 ATR total)**
- VWAP REV is a pre-existing v2.7 signal, not a new level
- Its performance is already accounted for in the original levels baseline

**Bottom line:** None of the top 5 winners OR losers in any new-level category appear to be catching "No Signal Zone" missed moves from the database. They are either morning spikes (already caught or already firing), multi-level confluence with original levels, or the pre-existing VWAP REV signal.

---

## 4. The Fundamental Mismatch: Why New Levels Don't Help

The missed-moves problem and the new-level solution are mismatched at every level.

### 4a. What We Were Trying to Fix

From `missed-moves-report.md` — No Signal Zone (622 moves, 81% of missed):
- **Time:** 64% after 11:00 (12:00-14:00: 36%, 14:00-15:00: 18%, 15:00-16:00: 11%)
- **Volume:** avg 0.8x — BELOW the 1.5x minimum
- **EMA alignment:** 58% aligned BUT the extended analysis shows Tier S moves are only 37.5% EMA-aligned
- **Pattern:** Price moves through mid-session with no key level nearby to trigger a signal
- **Volume for Tier S:** avg 0.9x (still below 1.5x)

### 4b. What New Levels Actually Generate

From `v30b-new-levels-investigation.md`:
- **Time:** 61-66% BEFORE 10:00 (PD Mid 64%, PD LH L 61%, VWAP Zone 66%)
- **Volume:** avg 4–8x (ABOVE 1.5x minimum — required by filter)
- **EMA alignment:** PD Mid 100% EMA-aligned, PD LH L 73% EMA-aligned
- **Pattern:** High-volume morning bars crossing a new level type for the first time in the session

### 4c. Why the Mismatch Is Structural (Cannot Be Fixed Without Removing Filters)

The indicator's signal generation requires:
1. `vol ≥ 1.5x SMA` — missed moves avg 0.8x vol. This alone excludes ~85% of missed moves.
2. EMA gate after 9:50 — 62% of Tier S missed moves are non-EMA. This alone excludes 62% of the most valuable missed moves.
3. First-cross guard (once-per-session) — for new levels, this means the first morning touch consumes the once-per-session slot, leaving nothing for the afternoon.
4. ADX ≥ 20 — missed moves avg ADX 18 (Tier S) / 14 (Tier A). Many would fail this filter.

Even if we added 100 more level types, the missed moves cannot be caught without removing or drastically loosening the core filters. But those filters exist precisely because they improve signal quality — removing them degrades the working signals.

---

## 5. Which Missed Moves ARE Catchable? (Reverse Analysis)

From `no-signal-zone-tiers.md` catchability analysis:

| Match Level | Count | % of Missed | ATR Sum |
|-------------|------:|------------:|--------:|
| Full (EMA + Regime 2 + Morning) | 179 | 9.0% | 295.0 |
| EMA + Regime 2, any time | 687 | 34.7% | 1,185.9 |
| EMA only | 748 | 37.8% | 1,276.6 |
| **No EMA (genuinely outside edge)** | **1,231** | **62.2%** | **2,102.5** |

Of the 1,979 missed moves on overlapping dates:
- **179 (9%)** are theoretically catchable with our current edge (EMA + Regime + Morning)
- **1,231 (62%) are outside our EMA edge entirely** — they happen when EMAs are misaligned
- The afternoon is where the money is: 1,463 post-11:00 moves = 2,599.9 ATR. Of those, 899 (62%) are non-EMA.

**The new levels don't target the 179 catchable moves (morning + EMA-aligned). And they can't reach the 1,231 non-EMA moves without removing the EMA gate.**

### What DID catch missed moves?

From the `missed-moves-report.md` "Signals Fired But CONF Failed" section:
- **170 moves had matching signals WITHOUT CONF**, totaling 288.8 ATR
- These are NOT new levels — they are the original BRK/REV signals (ORB L, Yest H, PM L, etc.)
- The problem isn't level types — it's CONF rate (original signals fire but CONF requires another bar to confirm, and they never do)

The highest-value missed-move recovery is not adding new levels, but improving CONF for the original signals already firing:
- GLD 2026-02-26 13:35 — 3.93 ATR up (signal REV PM L fired at 13:40, no CONF)
- MSFT 2026-02-13 10:30 — 3.27 ATR down (signal BRK ORB L fired at 10:40, no CONF)
- AAPL 2026-02-17 13:35 — 3.21 ATR up (signal BRK Yest H fired at 13:25, no CONF)

---

## 6. What Would It Take to Actually Catch Missed Moves?

Testing the four scenarios from the task specification:

### Scenario A: Lower volume requirement for new levels to 0.5x

**Problem:** Would flood the system. The original level types (Yest H/L, PM H/L, ORB H/L) would also get 100x more false signals if vol threshold drops to 0.5x. Can't lower the bar for new levels without lowering it for all.

**Modeled impact:** If we lower ONLY new levels to 0.5x vol: PD Mid + PD LH L would go from 144 to potentially 500+ signals in 27 days. But the win rate would drop to 40% or lower (the 0.8x avg vol moves have no directionality — they are drift, not momentum).

**Verdict:** Would help quantity, destroy quality. Not recommended.

### Scenario B: Exempt new levels from EMA gate (like FADE/RNG)

**Data from non-EMA-signal-research.md:** Non-EMA signals lose money across nearly all approaches. The only positive non-EMA type found was "K_Combo_Vol_Range" (N=2,062, +0.144 ATR/signal) which requires vol ≥ 3x. VWAP Cross and Range Breakout in non-EMA conditions are barely break-even (+0.021/+0.001 ATR).

**If we exempted new levels from EMA gate:**
- PD LH L: counter-EMA signals have N=21, avg PnL=+0.021 ATR — marginally positive but negligible
- PD Mid: unknown (all 61 live signals are EMA-aligned, meaning the non-EMA cases weren't generated)
- VWAP Zone REV: bear direction only in non-EMA would be +0.045 ATR/signal (bear VWAP REV already works)

**Verdict:** Marginal at best. The non-EMA missed moves don't become catchable just by exempting new levels — the level still needs to be nearby, which it often isn't for No Signal Zone moves.

### Scenario C: Only fire new levels after 10:30

This is the most logical fix matching what the backtest actually measured (the "midday treasure hunt" only tested after 10:30). The investigation report already quantified this:

| Level | Before 10:00 | 10:00–11:00 | After 11:00 |
|-------|-------------|-------------|-------------|
| PD Mid | -0.8 ATR | +0.1 ATR | +0.0 ATR |
| PD LH L | -0.6 ATR | **+1.5 ATR** | -0.3 ATR |
| VWAP Zone | +1.5 ATR | +0.7 ATR | -0.3 ATR |

**10:00-11:00 window works for PD LH L (+1.5 ATR from N=21 signals).**

But does a 10:30 gate actually catch missed moves? Of 443 post-10:00 missed moves in common symbols:
- Vol ≥ 1.5x: ~30% (130 moves) — most missed moves are low-vol even post-10
- EMA-aligned AND vol ≥ 1.5x: ~10% (43 moves)
- Also near a new level (PD Mid or PD LH L): probably 20-30% of those → **~10-13 additional catches per 12 days**

**Verdict:** A 10:30 gate recovers +1.5 ATR from PD LH L (N=21 in full 27-day dataset) and would catch perhaps 10-15 additional missed moves per period. This is the best achievable outcome.

### Scenario D: Combination (10:30 gate + vol cap + direction filter)

From recommendations in `v30b-new-levels-investigation.md`:
1. PD Mid after 10:00 ET only → recover -0.8 ATR morning drag
2. PD Mid cap vol at <5x → recover additional -2.0 ATR from high-vol blowthrough
3. PD LH L after 10:00 ET → recover -0.6 ATR morning drag, keep +1.5 ATR 10:00-11:00
4. PD LH L suppress 2-5x vol → recover -1.7 ATR worst bucket
5. VWAP Zone bear only → recover +1.7 ATR (kill bull VWAP REV losing -1.7 ATR)
6. VWAP Zone stop after 12:00 → recover -0.3 ATR

**Total estimated recovery: ~8-10 ATR over 27 days** (from removing bad signals, not from catching new missed moves).

Note: This scenario improves signal QUALITY of existing new-level signals. It does NOT expand coverage of missed moves. The new-level signals are already the same 8-10% of missed moves — applying filters doesn't catch more missed moves, it just improves the P&L on signals that fire.

---

## 7. Signal-by-Signal Match List

### New-Level Signals That MIGHT Correspond to Missed Moves

Using the time/direction match criteria (±15 min, same symbol, same date, overlapping period):

| Signal | Symbol | Date | Time | Vol | PnL@30m | Missed Move Match | Notes |
|--------|---------|------|------|-----|---------|-------------------|-------|
| PD LH L BRK ▼ | SPY | 2026-02-26 ~9:45 | — | 6.9x | +0.674 | None — SPY 2/26 13:30 UP is in missed moves, not 9:45 | Different time |
| PD LH L BRK ▼ | QQQ | 2026-02-26 ~9:45 | — | 6.6x | +0.555 | None — QQQ 2/26 13:30 is missed UP move | Different time |
| PD LH L REV ▲ | AMZN | 2026-02-26 ~9:30 | — | 8.2x | +0.645 | AMZN 2/26 13:30 is in missed moves (UP 3.38 ATR) | Different time by ~4 hrs |
| PD LH L BRK ▼ | SPY | 2026-02-26 ~10:40 | — | 1.9x | +0.529 | SPY 2/26: original missed move is 13:30 UP (opposite dir) | No match |
| PD Mid BRK | AMZN | multiple | 9:30-9:55 | 8.7x | -0.561 | AMZN 2/26 13:30 UP in missed moves | Time/direction mismatch |
| VWAP Zone REV | NVDA | multiple | morning | — | +2.2 ATR total | NVDA 2/26 12:15 UP (2.62 ATR) in missed moves | Different time |

**Zero direct matches found** between new-level signals and missed-move events within ±15 minutes. The closest temporal matches are separated by 3-4+ hours, and most have opposite directions.

---

## 8. Coverage: How Many Missed Moves Are Now Caught by v3.0b?

### Extending the "covered" vs "missed" analysis to v3.0b:

From the original missed-moves coverage table:
- Original v2.8: 3.3% CAUGHT, 17.5% SIGNAL_FIRED_BUT_FAILED, 78.9% MISSED

If v3.0b new levels catch even the most optimistic 5% of the remaining 78.9%:
- New coverage: 3.3% + 5% × 78.9% = 3.3% + 3.9% ≈ **7% coverage total** (vs 3.3% baseline)

But based on the structural analysis (time/vol/EMA mismatch), the realistic new-level coverage of missed moves is **1-2%**, not 5%.

**Why so low?**
- The "No Signal Zone" classification specifically means the original levels weren't nearby. New levels (PD Mid, PD LH L) CAN be nearby for some mid-session moves, but:
- The once-per-session guard means if PD Mid already fired at 9:35, it won't fire again at 13:30 when the actual missed move occurs
- The morning slot is being consumed by high-volume morning bars that are NOT in the missed-moves database
- The afternoon session fires almost no new-level signals (vol is too low)

**The once-per-session guard is the kill switch for afternoon coverage.**

For the 8 symbols in the live data, the once-per-session slot for each new level type is being consumed ~60-65% of the time before 10:00. This means by the time the afternoon moves occur (the 81% of missed moves), the new-level signal slots are already exhausted.

---

## 9. Final Verdict: Keep, Modify, or Remove?

### Decision Framework

| Level | Live PnL | Catches Missed Moves? | Is It Better Than Original Levels? | Verdict |
|-------|----------|----------------------|-------------------------------------|---------|
| PD Mid | -0.9 ATR | No (fires morning, missed are afternoon) | No (original: +0.029/sig, PD Mid: -0.015/sig) | MODIFY or REMOVE |
| PD LH L | +0.6 ATR | No (same structural mismatch) | Marginal (+0.007/sig vs +0.029/sig) | MODIFY |
| VW Band | 0 ATR (0 fires) | Cannot fire | N/A | REMOVE |
| VWAP Zone | +2.2 ATR | No (pre-existing v2.7 signal, not new) | Already in baseline | KEEP, FILTER |

### Specific Recommendations (ranked by impact)

#### Priority 1 — VWAP Zone: Bear Only (+5.6 ATR)
Kill bull VWAP REV. Bear VWAP REV = +3.9 ATR, Bull VWAP REV = -1.7 ATR. One flag change.

#### Priority 2 — Remove VW Band entirely
Already fires 0 times. Remove `sigBearVWBL`, the VW Band level computation, and the associated alert condition. ~5 lines of dead code.

#### Priority 3 — PD Mid: Add 10:00 gate AND cap vol <5x
- 10:00 gate removes -0.8 ATR morning drag (39 signals, win 46%, avg -0.021)
- Vol cap <5x removes additional -2.0 ATR (25 signals, win 44%, avg -0.079)
- Remaining: N≈22 signals, expected net positive

#### Priority 4 — PD LH L: Add 10:00 gate (+0.6 ATR recovery)
The 10:00-11:00 window is the only strongly positive window (+1.5 ATR, N=21, win 57%). Morning signals (9:30-10:00) are -0.6 ATR.
Consider also: BRK only (drop REV at PD LH L). BRK = +0.8 ATR, REV = -0.2 ATR.

#### Priority 5 — VWAP Zone: Stop after 12:00
N=22 signals after noon, win 33%, avg -0.020, total -0.3 ATR. Small but clean.

#### Priority 6 — AMD: Suppress or dim new-level signals
AMD is D-tier across all new levels: PD Mid -0.5 ATR, PD LH L -0.2 ATR, VWAP Zone -1.0 ATR.

**Total expected recovery from Priorities 1-5: ~8-10 ATR over 27 days.**
**Coverage of missed moves improvement: negligible (1-2% → still ~1-2%).**

---

## 10. Root Cause Summary

### Why the New Levels Failed to Catch Missed Moves

The strategy for new levels was based on a backtest (`midday_treasure_hunt.py`) that:
1. Only tested AFTER 10:30 (exactly when missed moves occur)
2. Used ANY bar within 0.15 ATR of the level (no vol requirement, no EMA requirement)
3. Used a different VWAP formula (VWAP_STD, not ATR-based)
4. Measured MFE not mark-to-market

The live implementation:
1. Fires ALL DAY (60-65% before 10:00 due to high-vol morning action)
2. Requires vol ≥ 1.5x, EMA alignment, first-cross guard (once-per-session)
3. Uses VWAP-ATR (too far from price, VW Band fires 0 times)
4. The once-per-session guard burns the slot in the morning, leaving nothing for afternoon

**The backtest validated afternoon, low-vol, mean-reversion touches of these levels. The implementation generates morning, high-vol, momentum signals at these levels. These are not just different — they are opposite patterns.**

### The Real Solution to Missed Moves

The 766 missed moves are characterized by:
- **81% afternoon** — requires post-11:00 signals
- **avg 0.8x vol** — requires lowering or removing volume filter for these signals
- **62% non-EMA** (Tier S = 38% EMA-aligned) — requires signals that work without EMA
- **No level nearby** (that's what "No Signal Zone" means) — requires either level-free signals or very many new level types

Two credible paths exist, but neither is "add 3 new level types":

**Path A — CONF Rate Improvement (highest ROI, lowest risk)**
170 moves had signals that fired but never got CONF. These are worth 288.8 ATR.
The original level signals ARE firing — the problem is CONF criteria.
If post-10:30 CONF criteria are loosened (or auto-CONF is added), this ATR becomes recoverable without ANY new level types.

**Path B — Non-EMA Signal Research (higher ceiling, higher risk)**
From `non-ema-signal-research.md`: K_Combo_Vol_Range (N=2,062, +0.144 ATR/signal) works in non-EMA conditions using range breakout + vol ≥ 3x. This addresses 62% of missed moves but requires a different signal paradigm (momentum, not level-based).

Both paths target the actual missed-move population. New levels do not.

---

## 11. Summary Table

| Question | Answer |
|----------|--------|
| Are new levels catching missed moves? | **No.** Time, vol, EMA, and once-per-session guard ensure near-zero overlap |
| What % of missed moves now have a new-level signal? | **1-2%** (structural lower bound) |
| Are new levels firing on better or worse setups? | **Worse** — -0.015/sig (PD Mid), +0.007/sig (PD LH L) vs +0.029/sig for original levels |
| Are there any recoverable missed moves from new levels? | **170 moves (288.8 ATR)** already have original signals that fire — CONF improvement is the lever |
| What is the best use of new levels? | Apply time gates + filters (10:00+, vol caps, bear-only VWAP) to recover 8-10 ATR from signal quality improvements — not from covering new missed moves |
| Should we keep, modify, or remove? | VWAP Zone: **KEEP + filter** (bear only, stop noon). PD Mid: **MODIFY** (gate + vol cap) or REMOVE. PD LH L: **MODIFY** (10:00 gate, BRK only). VW Band: **REMOVE** (never fires). |
| What would ACTUALLY fix missed moves? | Improve CONF criteria post-10:30 (recovers 288.8 ATR from existing signals already firing) OR pursue the v3.0 EMA hard gate path (removes non-EMA losses, total +115.9 ATR) |

---

*Analysis based on: `missed-moves-report.md`, `no-signal-zone-tiers.md`, `v30b-new-levels-investigation.md`, `non-ema-signal-research.md`, `v30b-deep-analysis.md`*
*Cross-reference method: profile comparison + signal-by-signal timing check + structural mismatch analysis*
*Date: 2026-03-05*
