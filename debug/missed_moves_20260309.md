# KLB Missed Moves Analysis — 2026-03-09

Generated: 2026-03-10
Script: `debug/v34_missed_moves_analysis.py`

**Summary:**
- Total zig-zag moves detected (>= 0.3 ATR, 5m RTH bars): **25**
- Caught by KLB: **7** (28%)
- Missed: **18** (72%)
- Scalps missed (0.3–0.8 ATR): **12**
- Majors missed (>= 0.8 ATR): **6**

---

## Section 1: Trigger Classification — All Missed Moves

| Symbol | Time ET | Dir  | Mag (ATR×) | Daily ATR | Tier  | Trigger          | Root Cause |
|--------|---------|------|------------|-----------|-------|------------------|------------|
| SPY    | 09:30   | bear | 1.13×      | 9.47      | SCALP | LEVEL_NEARBY     | Level 666.38 at 0.00 ATR distance — signal fired but RNG only, no directional signal |
| AMZN   | 09:30   | bear | 1.86×      | 6.98      | SCALP | WRONG_DIRECTION  | KLB fired bull RNG at open; actual move was bear |
| META   | 09:30   | bull | 2.11×      | 21.32     | SCALP | WRONG_DIRECTION  | KLB fired bear RNG/BRK at open; META briefly bounced before continuing down |
| MSFT   | 09:30   | bear | 1.15×      | 10.89     | SCALP | DIM_SUPPRESSED   | KLB fired DIM signal (⚠); move was suppressed by quality filters |
| NFLX   | 09:30   | bear | 1.60×      | 3.39      | SCALP | WRONG_DIRECTION  | KLB fired bull RNG; actual move was bear |
| TSM    | 09:30   | bull | 3.58×      | 12.76     | MAJOR | WRONG_DIRECTION  | KLB fired bear signals; TSM popped bull |
| XLE    | 09:30   | bull | 1.47×      | 1.24      | SCALP | WRONG_DIRECTION  | KLB fired bear signals; XLE moved bull |
| AMZN   | 09:55   | bull | 2.90×      | 6.98      | MAJOR | WRONG_DIRECTION  | KLB still in bear mode; AMZN reversed bull sharply |
| SPY    | 10:10   | bull | 3.12×      | 9.47      | MAJOR | VWAP_RECLAIM     | Price below VWAP (663.13 vs VWAP 664.57), below ORB Low — no KLB signal fired |
| TSLA   | 10:10   | bull | 4.10×      | 14.37     | MAJOR | WRONG_DIRECTION  | KLB fired bear BRK Week L at exactly 10:10 — entered short while bull reversal began |
| NFLX   | 10:30   | bull | 1.67×      | 3.39      | SCALP | ORB_RECLAIM      | Price near ORB Low (97.65), dist=0.29 ATR — ORB Low reclaim signal not triggered |
| XLE    | 10:55   | bear | 2.41×      | 1.24      | SCALP | LEVEL_NEARBY     | Level 57.01 right at price — no directional signal fired |
| MSFT   | 11:20   | bear | 1.21×      | 10.89     | SCALP | LEVEL_NEARBY     | Level 408.54 within 0.01 ATR — no signal fired |
| QQQ    | 12:40   | bear | 1.11×      | 11.19     | SCALP | LEVEL_NEARBY     | Level 601.32 within 0.02 ATR — no signal fired |
| SPY    | 12:45   | bear | 1.32×      | 9.47      | SCALP | WRONG_DIRECTION  | KLB in bull mode (PD LH L signal); bear move followed |
| SPY    | 13:40   | bull | 4.03×      | 9.47      | MAJOR | DIM_SUPPRESSED   | KLB fired VWAP bull with ⚠ DIM — SPY afternoon 4 ATR bull run was suppressed |
| QQQ    | 13:40   | bull | 3.31×      | 11.19     | MAJOR | LEVEL_NEARBY     | Level 597.68 within 0.01 ATR — no signal fired (corresponding to SPY's 13:40 move) |
| MSFT   | 14:05   | bull | 1.47×      | 10.89     | SCALP | WRONG_DIRECTION  | KLB in bear mode; MSFT bounced bull |

**Trigger breakdown — all 18 missed:**
| Trigger | Count | % |
|---------|-------|---|
| WRONG_DIRECTION | 9 | 50% |
| LEVEL_NEARBY    | 5 | 28% |
| DIM_SUPPRESSED  | 2 | 11% |
| VWAP_RECLAIM    | 1 | 6%  |
| ORB_RECLAIM     | 1 | 6%  |

---

## Section 2: The 10:10 ET Coordinated Bull Reversal — Deep Dive

**Context:** Between 09:30–10:10 ET, a broad selloff brought all major indices and tech stocks down. At ~10:10 ET a coordinated reversal occurred. This was the most significant missed opportunity of the day.

### Overview table — 5 key symbols at 10:10 ET

| Sym  | Bar (ET) | Dir  | Mag    | Start $ | VWAP   | Below VWAP? | ORB Low | vs ORB_L | KLB Signal at 10:10              |
|------|----------|------|--------|---------|--------|-------------|---------|----------|-----------------------------------|
| SPY  | 10:10    | bull | 3.12×  | 663.13  | 664.57 | YES -1.44   | 664.64  | -1.51    | None — KLB silent                |
| QQQ  | 10:10    | bull | ~2.5×* | 592.37  | 593.47 | YES -1.10   | 593.27  | -0.90    | None — KLB silent                |
| NVDA | 10:10    | bull | ✓ CAUGHT | 176.95 | 176.85 | No +0.10  | 176.15  | +0.80    | Caught by opening RNG (09:35)    |
| TSLA | 10:10    | bull | 4.10×  | 383.26  | 386.17 | YES -2.91   | 387.34  | -4.08    | KLB fired bear BRK Week L ↓      |
| META | 10:10    | bull | ~2.5×* | 628.89  | 631.01 | YES -2.12   | 630.59  | -1.70    | KLB fired bear BRK ORB L ↓      |

*QQQ and META bull moves not detected as separate zig-zag legs (opening bear move was still active at zig-zag threshold). Visually they reversed from 10:10.

**Key finding:** SPY, QQQ, TSLA, META were all below VWAP and below (or at) ORB Low at 10:10 ET. NVDA was above VWAP and already caught. The other 4 had a clear VWAP reclaim setup. KLB had no signal for SPY/QQQ, and was actively short TSLA/META.

### SPY — Bar-by-bar 10:00–10:25 ET (ATR=9.47, ORB H=667.63 L=664.64)

```
Time (ET)  Open    High    Low     Close   Vol/Avg  VWAP    vs VWAP    vs ORB_L
10:00      664.05  665.87  663.75  665.84  1.2×     664.82  +1.02      +1.20  ← above both
10:05      665.80  665.96  662.87  663.51  1.8×     664.72  -1.21      -1.13  ← breaks below VWAP and ORB_L
10:10      663.50  663.57  662.39  663.13  1.2×     664.57  -1.44      -1.51  ← flush bottom, below both
10:15      663.15  664.18  662.84  663.93  1.0×     664.51  -0.58      -0.71  ← reclaims partially
10:20      663.89  665.66  663.02  665.29  1.1×     664.52  +0.77      +0.65  ← VWAP RECLAIM confirmed
10:25      665.30  665.56  663.63  664.06  0.9×     664.51  -0.45      -0.58
```

**Signal that could have caught it:** Bull VWAP reclaim at 10:20 — close crosses above VWAP (+0.77) after 2-bar flush below VWAP and ORB Low. Volume was 1.0–1.2× average (not elevated but not dry). The reversal bar (10:20) closed +0.77 above VWAP, 0.65 above ORB Low — clean reclaim.

### NVDA — Bar-by-bar 10:00–10:25 ET (ATR=6.60, ORB H=178.16 L=176.15)

```
Time (ET)  Open    High    Low     Close   Vol/Avg  VWAP    vs VWAP    vs ORB_L
10:00      176.93  178.01  176.76  177.84  1.8×     176.83  +1.01      +1.69  ← stayed above
10:05      177.85  177.88  176.81  176.93  1.2×     176.86  +0.07      +0.78  ← tested VWAP
10:10      176.94  177.06  176.25  176.95  1.3×     176.85  +0.10      +0.80  ← held above VWAP/ORB_L
10:15      176.97  177.85  176.84  177.71  1.3×     176.89  +0.82      +1.56  ← bounced
10:20      177.70  178.30  177.26  178.25  1.5×     176.98  +1.27      +2.10  ← continuation
```

**NVDA was different:** Never broke below VWAP or ORB Low. The reversal was already underway from the opening RNG signal at 09:35. NVDA held structure while others flushed — it was the leader.

### QQQ — Bar-by-bar 10:00–10:20 ET (ATR=11.19, ORB H=596.47 L=593.27)

```
Time (ET)  Open    High    Low     Close   Vol/Avg  VWAP    vs VWAP    vs ORB_L
10:00      592.71  595.18  592.27  595.08  ?        593.57  +1.51      +1.81
10:05      595.06  595.27  592.41  593.08  ?        593.57  -0.49      -0.19  ← just below VWAP, at ORB_L
10:10      593.07  593.19  591.56  592.37  ?        593.47  -1.10      -0.90  ← below VWAP, below ORB_L
10:15      592.40  593.61  592.02  593.26  ?        593.43  -0.17      -0.01  ← returning to ORB_L
10:20      593.27  595.03  592.29  594.76  ?        593.47  +1.29      +1.49  ← VWAP RECLAIM confirmed
```

**Same pattern as SPY:** Flush below VWAP + ORB Low at 10:10, then VWAP reclaim bar at 10:20.

### TSLA — Critical case (KLB actively shorted at 10:10)

At 10:10, TSLA was trading 383.26 vs VWAP 386.17 (−2.91). KLB fired **bear BRK Week L** at exactly this bar (`10:10 ▼ BRK Week L vol=2.3x pos=v80 vwap=below ema=bear`). A short was entered right at the bottom of the reversal.

The TSLA bull move was 4.10× ATR — the largest single move of the day among focus symbols. KLB entered in the exact wrong direction at the exact bottom.

**Why KLB was wrong on TSLA:** TSLA broke below a weekly low level, which is structurally a valid bear BRK signal. But the coordinated market reversal overrode it. Without cross-symbol context (4 other symbols also bottoming), this is nearly impossible to avoid from a single-symbol perspective.

**What could have prevented the loss:** Cross-symbol regime signal — if 3+ symbols simultaneously break below VWAP then reclaim, suppress individual bear signals and potentially flip to bull.

### META — Similar to TSLA

META fired bear BRK ORB L at 09:40–09:45, confirmed into the 10:10 flush. At 10:10, META was 628.89 vs VWAP 631.01 (−2.12), below ORB Low 630.59. The bull reversal from 10:20 onwards brought META back above VWAP by 10:20 (+1.21). KLB had no bull reversal signal.

---

## Section 3: Scalp Move Patterns (0.3–0.8 ATR)

**12 scalps missed** across the day.

### Trigger breakdown — Scalps (12 total)
| Trigger | Count | % |
|---------|-------|---|
| WRONG_DIRECTION | 6  | 50% |
| LEVEL_NEARBY    | 4  | 33% |
| DIM_SUPPRESSED  | 1  | 8%  |
| ORB_RECLAIM     | 1  | 8%  |

### What do the scalps have in common?

1. **Opening direction mistakes (7 scalps at 09:30–09:45):** The open was chaotic. KLB picked a direction (usually the dominant early move) but several symbols reversed quickly. AMZN, META, NFLX, TSM, XLE all had KLB fire in the wrong direction at open. This is an inherent limitation of the opening 5-min bar — not easily solvable without being slower to commit.

2. **Level proximity without a signal (4 scalps: SPY 9:30, XLE 10:55, MSFT 11:20, QQQ 12:40):** A key level was right at the price when the move started. KLB identified the level in its price universe but either: (a) no directional signal fired, or (b) the signal type matched but the gate failed. These are `LEVEL_NEARBY` misses — the highest-quality potential catches since KLB already has the level information.

3. **Volume context:** Mean vol ratio at scalp start = 2.3×, median = 1.8×. These are moderately elevated — not spikes (would be 5×+) but clearly active. The Quiet Coil override would not apply.

### Trigger breakdown — Majors (6 total)
| Trigger | Count | % |
|---------|-------|---|
| WRONG_DIRECTION | 3  | 50% |
| DIM_SUPPRESSED  | 1  | 17% |
| VWAP_RECLAIM    | 1  | 17% |
| LEVEL_NEARBY    | 1  | 17% |

**Key major misses:**
- **SPY 13:40 (+4.0× ATR):** KLB fired VWAP bull with DIM (⚠). This was the second-largest bull run of the day. The afternoon suppression filters killed it.
- **QQQ 13:40 (+3.3× ATR):** Level 597.68 right at price — no signal. Corresponds to SPY's 13:40 move. If SPY had fired, the cross-symbol boost might have helped QQQ too.
- **SPY 10:10 (+3.1× ATR):** VWAP reclaim — no signal type for this in KLB.
- **TSLA 10:10 (+4.1× ATR):** Wrong direction — KLB entered short at the bull reversal bottom.
- **TSM 09:30 (+3.6× ATR):** Opening direction miss.
- **AMZN 09:55 (+2.9× ATR):** AMZN reversed from bear to bull after the opening flush; KLB had no reclaim signal.

---

## Section 4: Proposed New Signal Types / Improvements

Ranked by: (expected moves caught) × (signal quality estimate) / (implementation complexity)

---

### Rank 1 — VWAP Reclaim after opening flush
**Expected moves caught on 2026-03-09:** SPY 10:10, QQQ 10:10, AMZN 09:55, TSLA (would have prevented the wrong-direction entry) = **3–4 major moves**

**Signal condition (grounded in observed data):**
- Price is below VWAP at bar close
- Previous bar also closed below VWAP (2-bar flush confirmation)
- Current close > VWAP (reclaim bar)
- Volume >= 0.8× average (not required to be elevated)
- Emit: bull REV signal, DIM if EMA is bear (ema overrideable)

**Why this is high quality:** VWAP reclaim after a flush is structurally sound — stops are clear below the flush low, entry is defined (VWAP cross), and the signal fires AFTER the reversal is confirmed (not predictive). SPY's 10:20 bar, QQQ's 10:20 bar, and AMZN's 09:55 bar all showed this pattern cleanly.

**Complexity:** Low. KLB already computes VWAP. Need: `prev_close_below_vwap AND close_above_vwap` condition. Similar to existing `VWAP REV` logic but specialized for the reclaim-after-flush case.

**Caveats:** Would not prevent the TSLA short at 10:10 on its own — that required cross-symbol context. Would at minimum flag the bull reversal on SPY/QQQ, giving visual context.

---

### Rank 2 — DIM override for coordinated reversal (Cross-Symbol Regime)
**Expected moves caught on 2026-03-09:** Prevented the TSLA 10:10 short entry, potentially QQQ 13:40 bull, SPY 13:40 DIM = **2–3 major moves + prevent 1 large loss**

**Signal condition:**
- When 3+ symbols are simultaneously below VWAP (or have just reclaimed VWAP)
- Set a bull regime flag for 1–2 bars
- Bull regime: suppress new bear signals, reduce DIM threshold for bull signals

**Why this matters:** TSLA's 10:10 bear BRK was technically valid in isolation. Only the cross-symbol context (SPY/QQQ/META/NVDA all bottoming at the same time) reveals it's a regime reversal. This is the scanner's unique advantage over a single-symbol system.

**Complexity:** Medium. Requires reading multi-symbol state in the scanner. Partially possible with existing scanner infrastructure. Not a small change but high value.

---

### Rank 3 — Remove DIM on large afternoon bull moves at VWAP
**Expected moves caught on 2026-03-09:** SPY 13:40 (+4.0× ATR, DIM_SUPPRESSED), QQQ 13:40 (+3.3× ATR LEVEL_NEARBY) = **2 major moves**

**Signal condition:** The SPY 13:40 KLB signal was already correct (`VWAP bull`) but DIM (⚠). A "large move override" that un-dims signals when the trigger bar's range is >= 1.5× ATR would have fired this.

**Grounding:** The 13:50 KLB log shows `VWAP bull` firing with `rangeATR=1.1` — below the threshold. But the actual move was 4.0× ATR. The issue is that KLB DIM'd based on pre-move criteria that were conservative. The `isQuietCoil` and `isBroadCoil` overrides already address some of this. Check if they were evaluated at 13:40.

**Complexity:** Very low — verify if existing overrides would have triggered. If not, add: `isBigCandle = rangeATR >= 2.0 → suppress DIM for VWAP signals`.

---

### Rank 4 — ORB Low Reclaim (verify v3.4 is working)
**Expected moves caught on 2026-03-09:** NFLX 10:30 (+1.67× ATR, ORB_RECLAIM) = **1 scalp move** (may already be implemented)

**Signal condition:** Already exists in v3.4 without EMA gate for midday. Check: was NFLX's ORB Low reclaim at 10:30 within the midday window? Answer: 10:30 ET is morning, not midday — so the EMA gate would still apply. NFLX's 10:30 bar: price returned to ORB Low (97.65), distance 0.29 ATR. If EMA was bear at this time, signal would be blocked.

**Complexity:** Very low — check log to confirm suppression, then remove EMA gate for ORB Low reclaim across all morning hours (not just midday).

---

### Rank 5 — Opening 5-min direction filter
**Expected moves caught on 2026-03-09:** Opening scalps (AMZN bear, NFLX bear, XLE bull) = **3–5 scalps** but low quality

**Problem:** 50% of all misses were "WRONG_DIRECTION" at open. KLB picks a direction based on the first bar but frequently the opposite move follows.

**Solution considered:** Wait for 2 confirming bars before committing direction at open. But this means missing the first-bar breakout (which is often the best).

**Recommendation:** Do NOT implement. Opening direction noise is a known limitation. The v3.3 morning quality finding (18.1% great rate vs 20% baseline) suggests the open is already below average. Adding a filter here would reduce noise but also reduce catch rate on the opening RNG signals that KLB does catch correctly.

---

### Summary table

| Rank | Signal / Fix | Moves on 3/9 | Quality | Complexity | Recommendation |
|------|-------------|-------------|---------|------------|----------------|
| 1 | VWAP Reclaim (bull) | 3–4 major | High (45%+ win) | Low | **Implement** |
| 2 | Cross-symbol DIM override | 2–3 major + 1 prevented loss | High | Medium | **Design first** |
| 3 | Large-candle DIM override | 2 major | High | Very Low | **Verify first** |
| 4 | ORB Low Reclaim (morning) | 1 scalp | Medium | Very Low | **Quick check** |
| 5 | Opening direction filter | 3–5 scalps | Low | Low | **Skip** |

---

## Appendix: Caught signals on 2026-03-09

For reference, what KLB did catch:

| Symbol | Time ET | Dir  | Mag    | Signal | Notes |
|--------|---------|------|--------|--------|-------|
| AAPL   | 09:30   | bull | 3.27×  | RNG/BRK | Opening breakout caught |
| AMD    | 09:30   | bull | 3.36×  | RNG/BRK | Opening breakout caught |
| GOOGL  | 09:30   | bull | 3.56×  | RNG/BRK | Opening breakout caught |
| MSFT   | 09:45   | bull | 1.53×  | BRK?   | After initial bear move |
| NVDA   | 09:30   | bull | 2.69×  | RNG    | Opening breakout caught — held through 10:10 |
| QQQ    | 09:35   | bull | 1.86×  | RNG    | Opening bull caught |
| TSLA   | 09:30   | bear | 2.12×  | RNG    | Opening bear move caught |

**Key observation:** KLB is strong on opening directional breakouts (5/7 catches are at 09:30–09:35). It is weak on: (1) reversals within the first hour, (2) afternoon VWAP reclaims, (3) coordinated multi-symbol reversals.
