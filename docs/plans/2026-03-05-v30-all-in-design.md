# v3.0 All-In Design

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform Key Level Breakout from a morning-only breakout indicator into an all-day signal system with validated filters, new level types, and a new non-EMA signal type.

**Architecture:** 3-phase approach — cleanup first (kill MC, add EMA gate, auto-confirm), then new signal generation (3 new levels, CONF extension, FADE signal, Range+Vol signal), then display upgrades (regime score, dimming, runner score redesign).

**Tech Stack:** Pine Script v6, TradingView indicator

---

## Data Foundation

All features below are validated against:
- 1,841 signals (enriched-signals.csv, 13 symbols, 28 days)
- 25,304 significant moves (no-signal-zone-moves.csv, 13 symbols, 451 days)
- 9,596 big-move bars (big-moves.csv)
- Backtests on 5m parquet data (May 2024 – Mar 2026)

---

## Phase 1: Cleanup (highest impact, simplest)

### 1. Kill MC (Momentum Cascade)
**Impact:** ~0 ATR change, -80 lines of code
**Data:** MC fires 99.4% before 9:50 on opening noise. Opposing bull+bear pairs = coin flip. Only 7 MC signals would fire after 9:50.

**Remove:**
- `mcBull` / `mcBear` signal generation
- MC auto-confirm mechanism
- Orange label creation for MC signals
- 🔊 explosive volume glyph (only used by MC)
- MC-specific alertconditions
- `mcFiredBull` / `mcFiredBear` once-per-session tracking

**Keep:**
- 🔇 QBS (Quiet Before Storm) — evaluate separately, not part of MC removal

### 2. EMA Hard Gate
**Impact:** +45.6 ATR recovered
**Data:** Non-EMA signals net negative BOTH pre-9:50 (-32.3 ATR, N=283) AND post-9:50 (-13.3 ATR, N=208). Removing all non-EMA: 1841→1350 signals, P&L +70.3→+115.9 ATR.

**Logic:**
- After 9:50 ET: If signal direction doesn't match EMA direction → **suppress entirely** (don't generate signal)
- Before 9:50 ET: If signal direction doesn't match EMA direction → **dim only** (generate but gray/small)
- "EMA matches direction" = EMA9 > EMA20 > EMA50 for bull, or EMA9 < EMA20 < EMA50 for bear
- Exception: Range+Vol signals (feature #7) bypass EMA gate — they're designed for non-EMA conditions

### 3. Auto-Confirm R1
**Impact:** +3.8 ATR, faster entry
**Data:** N=389, +0.106/signal, 58.6% win, MFE/MAE 1.60. 12/13 symbols positive.

**Logic:**
- If EMA aligned + time < 10:30 ET → CONF passes immediately (no follow-through bar needed)
- Replaces MC's two-step process with one-step auto-confirm
- Display as ✓ (not ✓★) — auto-confirm is standard quality

---

## Phase 2: New Signal Generation

### 4. Three New Key Levels
**Impact:** ~165 ATR from midday coverage
**Data:** Midday treasure hunt backtest (17 level types tested, 3 validated positive):

| Level | Backtest Win% | Avg P&L | Total ATR | Computation |
|-------|:---:|:---:|:---:|---|
| PD_LAST_HR_L | 55.6% | +0.238 | +53.5 | Prior day's 15:00-16:00 low |
| PD_MID | 55.1% | +0.209 | +34.9 | (PDH + PDL) / 2 |
| VWAP_LOWER | 53.3% | +0.133 | +77.3 | VWAP - 1×ATR(14) |

**Pine implementation:**
- PD_LAST_HR_L: Use `request.security` to get prior day's last-hour low. New `levelType` value "PD Last Hr L"
- PD_MID: Compute from existing PDH/PDL: `pdMid = (pdH + pdL) / 2`. New `levelType` value "PD Mid"
- VWAP_LOWER: Dynamic level `vwapLow = ta.vwap - atr`. Recalculates every bar. New `levelType` value "VWAP Band"
- All three participate in existing BRK/REV signal detection — no new signal type needed
- All three get existing CONF tracking, label generation, alerts

**Levels NOT implemented (backtest negative):**
- 1HR_H (-62 ATR), VWAP_UPPER (-82 ATR), HALFDAY_L (-44 ATR), D2_H (-37 ATR)

### 5. CONF Window Extension (1→3 bars)
**Impact:** 289 ATR directly recoverable
**Data:** 3/4/26 investigation: 5/5 symbols fired correct bullish BRK at 9:35, ALL had CONF ✗ at 9:40 due to natural pullback. Direction was correct 100%.

**Logic:**
- Change CONF evaluation from 1 bar after signal to 3 bars (15 min on 5m TF)
- Track highest/lowest close over 3 bars instead of just the next bar
- CONF ✓ if ANY of the 3 bars confirms (close in right direction beyond threshold)
- CONF ✗ only after ALL 3 bars fail
- Auto-Confirm R1 (feature #3) still overrides — it fires immediately

### 6. Failed Breakout Fade (FADE signal)
**Impact:** 179 ATR
**Data:** 110 missed moves. Peak time 10:00-10:30. BRK fires → CONF fails → price crosses back through level → move continues OPPOSITE direction.

**Logic:**
- After CONF ✗ on a BRK signal, monitor for price crossing back through the original level
- If price crosses back within 6 bars (30 min) of original signal → fire FADE signal in opposite direction
- FADE direction = opposite of original BRK
- FADE gets its own CONF tracking (standard 3-bar window)
- Once per level per session (don't re-FADE)

**Visual:**
- Purple/magenta label color (new = distinguishes from BRK blue / REV green)
- Label text: "FADE" + level name
- Standard size (not large)

### 7. Range+Volume Signal (RNG signal type)
**Impact:** +297 ATR in backtest (+0.144/signal, N=2,062)
**Data:** Non-EMA signal research. ONLY profitable non-EMA signal type found (10 of 14 tested lost money).

**Logic:**
- Compute 12-bar range on signal TF: `rangeH = ta.highest(high, 12)`, `rangeL = ta.lowest(low, 12)`
- Compute volume threshold: `volAvg = ta.sma(volume, 20)`
- Signal fires when:
  - Close breaks above rangeH (bull) or below rangeL (bear)
  - Volume on breakout bar ≥ 3× volAvg
  - Regular trading hours only (9:30-16:00 ET)
- **NO EMA requirement** — this signal is designed for non-EMA conditions
- Gets standard CONF tracking (3-bar window)
- Once per direction per session (same as QBS/MC pattern)

**Visual:**
- Teal/cyan label color
- Label text: "RNG" + direction glyph
- Standard size

---

## Phase 3: Display Upgrades

### 8. Regime Score Display
**Impact:** Visual — promotes score=2 signals, dims score=1
**Data:** Score 2 (EMA+VWAP both match): 56.8% win, +110.3 ATR. Score 1: 37.7% win, -42.2 ATR.

**Logic:**
- Compute: regime_score = (EMA matches direction ? 1 : 0) + (VWAP matches direction ? 1 : 0)
- Display as Ⓡ0 / Ⓡ1 / Ⓡ2 on label (or simpler: just R0/R1/R2)
- Score 2 = normal display
- Score 1 bull signals = dim (gray, small) — actively harmful combo
- Score 0 = already suppressed by EMA gate (post-9:50) or dimmed (pre-9:50)

### 9. Dim Regime-Mismatched Bulls
**Data:** Regime Score 1 + Bull: 31.2% win, -0.176 P&L. Regime Score 1 + Bear: still positive.

**Logic:**
- Bull signal + regime score 1 → dim (gray label, size.small)
- Bear signal + regime score 1 → normal display (bear has edge even at score 1)
- This is asymmetric — intentional, data-backed

### 10. Runner Score Redesign
**Impact:** Quality of life — current score is broken (r=-0.02)
**Data:** Current 5 factors have zero correlation with outcomes.

**New 5 factors (each worth 1 point):**
1. EMA aligned (always true after EMA gate, but relevant for pre-9:50 dimmed signals)
2. Regime score = 2
3. CONF pass (✓ or ✓★)
4. Volume ≥ 10x (true momentum, not exhaustion)
5. Time before 11:00 (morning advantage)

---

## What's NOT in v3.0

| Feature | Why Not |
|---|---|
| Counter-VWAP as primary | Too rare (N=52) |
| 1HR H/L levels | Backtest negative (-62 ATR) |
| VWAP Upper band | Backtest negative (-82 ATR) |
| Complex 9-factor scoring | Marginal improvement over simpler approach |
| Midday EMA cross signals | +0.022/signal — too weak to justify complexity |
| Symbol-specific filters | Negative delta when tested |

---

## Success Criteria

| Metric | v2.9 | v3.0 Target |
|---|---|---|
| Total signals/day (13 sym) | ~66 | ~45-55 (fewer, higher quality) |
| Win rate (all signals) | 51.4% | 55%+ |
| Signals after 10:30 | ~5% | ~20%+ (new levels + RNG) |
| CONF pass rate | 51% | 60%+ (3-bar window) |
| Net P&L (ATR, 28-day basis) | +70.3 | +150+ |

---

## Risk Mitigation

- **Pine Script limits:** New levels + Range+Vol add computation. Monitor `max_bars_back` and `max_labels_count`.
- **Over-fitting:** All features validated on 451+ days and 13 symbols. No single-symbol optimizations.
- **Complexity creep:** Net code change is ~+40 lines (MC deletion offsets additions).
- **Phased rollout:** Phase 1 changes are independent — can ship Phase 1 alone if Phase 2 has issues.
