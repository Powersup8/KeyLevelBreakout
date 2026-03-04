# v2.8a Audit — Action Items & Handover

> **For Claude:** This is a handover doc from a prior session. Read this first, then work through the items in order. All analysis data is in `debug/v28a-*.csv` and reports in `debug/v28a-*.md`. Read `MEMORY.md` for full project context.

**Current version:** v2.8a (`KeyLevelBreakout.pine`, ~1613 lines)
**Last commit:** `8b7b4f6` (pushed to GitHub)

---

## Status Summary

We ran a comprehensive v2.8a signal audit (7,044 signals, 10 symbols, ~100 trading days) and found 9 critical findings. Two were deeply investigated, the rest need investigation and/or implementation.

---

## READY TO IMPLEMENT (analyzed, fix designed)

### 1. MC Time Gate — Suppress Before 9:50

**Problem:** MC fires both bull AND bear within 10 min at open on 126/167 days. Burns once-per-session slot on noise. Neither signal is predictive (45/55% coin flip). No feature distinguishes correct from wrong.

**Key data:** Waiting until 9:50 gives 79% directional accuracy (99/126 pairs).

**Fix:** Add time check to MC raw conditions in `KeyLevelBreakout.pine`:
- Lines 770-773: `rMC_bull` and `rMC_bear` definitions
- Add condition: signal-TF bar must be at or after 9:50 ET
- The time is available as `sigTime` (signal timeframe time) — check `hour(sigTime) == 9 and minute(sigTime) >= 50` or `hour(sigTime) >= 10`
- QBS (🔇) signals are rare (87 total) and may not need the same gate — but consider applying it for consistency

**Full analysis:** `debug/v28a-mc-analysis.md`
**Data:** `debug/v28a-mc-opposing-pairs.csv` (126 pairs with correct/wrong labels)

### 2. ⚡ Big-Move — Remove size.large, Keep as Info Glyph

**Problem:** ⚡ signals have MFE 0.598 vs normal 1.152 (-48% gap at ALL timeframes). MFE drops monotonically with bar range. Entry is at the extreme of a 2x+ ATR bar — you're chasing.

**Fix:** In `KeyLevelBreakout.pine`:
- Find where `isBigMove` triggers `size.large` on labels (search for `isBigMove` in label creation ~line 800+)
- Remove the `size.large` override — let the normal Runner Score determine label size
- Keep the ⚡ glyph appended to the label text (informational)
- Optional: dim ⚡ signals slightly (like moderate ramp dimming does for 1-2x ramp)

**Full analysis:** `debug/v28a-bigmove-analysis.md`

---

## NEEDS INVESTIGATION (data exists, need deeper analysis)

### 3. Volume Filter May Be Inverted

**Finding:** BRK 30m follow-through by volume bucket:
| Vol | MFE | Win% |
|-----|-----|------|
| <2x | **1.112** | 51% |
| 2-5x | 1.004 | 52% |
| 5-10x | 0.660 | 45% |
| 10x+ | 0.478 | 54% |

Runner Score gives +1 for vol ≥5x, but ≥5x has the WORST MFE. This contradicts our v2.7 change.

**Investigate:**
- Is this just because high-vol signals overlap with ⚡ (and ⚡ is the real culprit)?
- Filter to non-⚡ signals only and re-check volume buckets
- Check if vol filter matters differently for CONF ✓ vs all signals
- Data: `debug/v28a-follow-through.csv` has all needed columns

### 4. ✓ Massively Beats ✓★ — Why?

**Finding:** Trade simulation (CONF signals only):
- ✓ (solid): 493 trades, **+22.76 ATR** total, 37% win
- ✓★ (gold): 377 trades, **+2.74 ATR** total, 32% win

✓★ should be premium. It's not.

**Investigate:**
- What makes ✓★ different from ✓? (✓★ = high-conviction auto-promote, usually higher vol/range)
- Is ✓★ correlated with ⚡? If so, the ⚡ exhaustion effect may explain it
- Check ✓★ by symbol, hour, volume, range_atr
- Check if removing ⚡ signals from ✓★ subset improves its performance
- Data: `debug/v28a-trades.csv` has conf type, `debug/v28a-signals.csv` has all features

### 5. TSLA Dominance (79% of P&L)

**Finding:** TSLA = +20.11 ATR, rest = +5.40 ATR across 763 trades.

**Investigate:**
- Is TSLA's edge real or overfitting to a specific regime (downtrend $490→$390)?
- Check TSLA P&L by month — is it concentrated in certain periods?
- Would the system be profitable without TSLA at all?
- Should we adjust strategy per symbol (e.g., AAPL at -5.09 should be excluded)?
- Data: `debug/v28a-trades.csv`

### 6. VWAP Counter-Trend = 83% Win (Small Sample)

**Finding:** 36 VWAP counter-trend BRK signals had 83% win rate and 1.154 MFE. Small sample.

**Investigate:**
- What is a "VWAP counter" BRK? (breakout against VWAP direction)
- Are these reclaim signals in disguise?
- Check by symbol, time, and follow-through profile
- If validated, this could be a new high-priority signal class
- Data: `debug/v28a-follow-through.csv` (filter: type=BRK, vwap=counter)

---

## CONFIRMED WORKING (no action needed)

- **#7: 5m checkpoint** — HOLD +0.120 ATR, BAIL -0.058 ATR. Working as designed.
- **#8: Body ⚠** — 0.716 MFE vs 0.907 without. Fakeout detection confirmed.
- **#9: BRK CONF rate** — 35% overall. Symbol variation documented.

---

## DEFERRED (future work)

### Grinding Trend Detection
- 2026-03-03: SPY/QQQ moved 11+ ATR in 3 hours with zero alerts
- All 6 missed moves were slow grinds, not explosive breakouts
- Indicator is designed for level breakout events, not trend continuations
- Would require fundamentally new signal type
- Analysis: `debug/2026-03-03-missed-moves.md`

---

## File Map

| File | Contents |
|------|----------|
| `debug/v28_signal_audit.py` | Main audit script (run with `python3 debug/v28_signal_audit.py`) |
| `debug/v28a-signal-audit.md` | Full audit report (8 sections) |
| `debug/v28a-mc-analysis.md` | MC opposing pairs deep dive |
| `debug/v28a-bigmove-analysis.md` | ⚡ big-move flag analysis |
| `debug/2026-03-03-missed-moves.md` | Missed moves from Mar 3 |
| `debug/v28a-signals.csv` | 7,044 parsed signals (all types) |
| `debug/v28a-follow-through.csv` | 17,244 MFE/MAE measurements (5m/15m/30m) |
| `debug/v28a-trades.csv` | 870 simulated trades (CONF ✓/✓★ only) |
| `debug/v28a-missed-runs.csv` | 1,756 missed signal runs (≥1 ATR) |
| `debug/v28a-mc-opposing-pairs.csv` | 126 MC opposing pairs with labels |

---

## Recommended Order

1. **Implement #1** (MC time gate) — simple, high impact
2. **Implement #2** (⚡ size.large removal) — simple, high impact
3. **Investigate #4** (✓ vs ✓★) — may be caused by ⚡, so check after #2
4. **Investigate #3** (volume filter) — same, may be ⚡-related
5. **Investigate #5** (TSLA dominance) — affects overall strategy trust
6. **Investigate #6** (VWAP counter) — potential new edge
7. **Version bump to v2.8b** after implementing #1 + #2
