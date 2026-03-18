# v2.8b Volume Investigation — #3 + #4 Combined

**Date:** 2026-03-04
**Dataset:** 7,044 signals, 1,575 BRK, 870 trades, 10 symbols, ~100 days

---

## Finding: ⚡ Contamination Explains the "Inverted Volume"

### The Original Problem (#3)

BRK 30m follow-through by volume — higher volume = worse MFE:

| Vol | n | MFE | MAE | Win% |
|-----|---|-----|-----|------|
| <2x | 320 | **1.112** | 1.035 | 51% |
| 2-5x | 616 | 1.004 | 0.839 | 52% |
| 5-10x | 334 | 0.660 | 0.814 | 45% |
| 10x+ | 305 | 0.478 | 0.493 | 54% |

### Root Cause: ⚡ Dominates High-Volume Buckets

| Vol Bucket | % that are ⚡ |
|------------|--------------|
| <2x | 9% |
| 2-5x | 40% |
| 5-10x | **84%** |
| 10x+ | **98%** |

### After Removing ⚡: Volume Works Normally

**Non-⚡ BRK, 30m window (fine-grained):**

| Vol | n | MFE | MAE | Win% | MFE/MAE |
|-----|---|-----|-----|------|---------|
| 1.5-2x | 291 | 1.136 | 1.079 | 51% | 1.05 |
| **2-3x** | **237** | **1.252** | **0.884** | **54%** | **1.42** |
| 3-5x | 133 | 1.137 | 0.897 | 53% | 1.27 |
| 5-10x | 52 | 0.895 | 1.209 | 46% | 0.74 |
| 10x+ | 6 | 0.548 | 1.642 | 33% | 0.33 |

**Sweet spot: 2-3x volume.** Best MFE (1.252), best MFE/MAE ratio (1.42), best win rate (54%).

Even without ⚡, ≥5x volume still hurts (MFE 0.859, 45% win, n=58 vs <5x: MFE 1.178, 52% win, n=661).

### Consistent Across All Windows (Non-⚡)

| Window | <2x MFE | 2-5x MFE | 5-10x MFE |
|--------|---------|----------|-----------|
| 5m | 0.503 | **0.558** | 0.461 |
| 15m | 0.812 | **0.909** | 0.685 |
| 30m | 1.136 | **1.211** | 0.895 |

2-5x wins at every timeframe.

---

## Finding: This Directly Explains #4 (✓★ Underperforms ✓)

### The Problem

| CONF Type | Trades | Total P&L | Avg P&L | Win% |
|-----------|--------|-----------|---------|------|
| ✓ (solid) | 493 | **+22.76 ATR** | +0.046 | 37% |
| ✓★ (gold) | 377 | +2.74 ATR | +0.007 | 32% |

✓★ requires ≥5x vol + ≥80% close pos. But ≥5x vol is the **worst** MFE bucket.

### ✓★ BRK Trades by Volume

| Vol | n | Total P&L | Avg | MFE |
|-----|---|-----------|-----|-----|
| <2x | 26 | +3.04 | +0.117 | 0.365 |
| 2-5x | 78 | +2.56 | +0.033 | 0.292 |
| **5-10x** | **51** | **-0.48** | **-0.009** | **0.227** |
| **10x+** | **7** | **-0.90** | **-0.128** | **0.112** |

### ✓ BRK Trades by Volume (same pattern)

| Vol | n | Total P&L | Avg | MFE |
|-----|---|-----------|-----|-----|
| <2x | 86 | +9.03 | +0.105 | 0.340 |
| **2-5x** | **156** | **+11.30** | **+0.072** | **0.325** |
| 5-10x | 34 | -2.80 | -0.082 | 0.126 |
| 10x+ | 11 | -0.57 | -0.052 | 0.153 |

Both ✓ and ✓★ show the SAME drop-off at ≥5x. ✓★ just has more of its trades in the bad bucket by definition.

### QBS/MC ✓★ Is Net Negative

| Source | n | Total P&L |
|--------|---|-----------|
| BRK ✓★ | 162 | +4.22 ATR |
| QBS/MC ✓★ | 215 | **-1.47 ATR** |

---

## CONF Rate Paradox

Higher volume = higher CONF rate but worse MFE per trade:

| Vol | CONF Rate | MFE (30m) |
|-----|-----------|-----------|
| <2x | 24% | 1.112 |
| 2-5x | 28% | 1.004 |
| 5-10x | 33% | 0.660 |
| 10x+ | **57%** | **0.478** |

High-volume signals "survive" (next signal fires same direction) but don't RUN. The follow-through is exhausted — another signal fires but the distance traveled is minimal.

---

## Actionable Recommendations

### 1. Runner Score Vol Factor: Change ≥5x → 2-3x

Current: `vol >= 5.0` gives +1 point.
Data says: 2-3x is the sweet spot (MFE 1.252, 54% win). ≥5x hurts (MFE 0.859, 45% win).

**Proposed:** `vol >= 2.0 and vol < 5.0` gives +1 point. Or simply `vol >= 2.0`.

### 2. ✓★ Gold Criteria: BOTH conditions are problematic

Current: ≥5x vol AND ≥80% close pos.
Problems:
- **≥5x vol:** Channels ✓★ into the worst-performing volume bucket (MFE 0.859)
- **≥80% close pos:** Already documented as overfitting in Design Journal Dead Ends — "+9.9pp lift in one analysis, did NOT replicate across 13 symbols, cuts 70% of valid signals"
- `closeLoc` threshold was already lowered from 0.4 → 0.3 in v2.8 for the same reason

**Decision: Option B — Redefine ✓★ with validated criteria.**

### New ✓★ Definition: BRK + vol<5x + morning (9-10h)

Old: `vol >= 5.0 AND closePos >= 80` (lines 1081, 1229, 1321)
New: `conf_source == BRK AND vol < 5.0 AND hour <= 10`

| Metric | Old ✓★ | **New ✓★** | Improvement |
|--------|--------|-----------|-------------|
| Total P&L | +2.74 ATR | **+23.10 ATR** | **8.4x** |
| Avg/trade | 0.007 | **0.097** | **14x** |
| Win% | 32% | **42%** | +10pp |
| Max Drawdown | n/a | **-1.95 ATR** | shallowest |
| Recovery Ratio | n/a | **11.9x** | best |
| TSLA dependency | n/a | **35%** | diversified |
| Profitable symbols | n/a | **8/10** | most |

Monthly consistency (1 losing month out of 7).

### Implementation Notes
- `highConv` condition at lines 1081, 1229: change to `vol < 5.0 AND hour(time) <= 10`
- Line 1321 (QBS/MC CONF): QBS/MC ✓★ is net negative (-1.47 ATR) — remove ✓★ for QBS/MC entirely, always use plain ✓
- Runner Score vol factor (line ~480): change `vol >= 5.0` to `vol >= 2.0 and vol < 5.0`

### 3. Consider Volume Ceiling Warning

Signals with ≥5x volume and non-⚡ have MFE 0.859 — significantly below average. Could add a visual warning similar to ⚠ body warning.

---

## Status: #3 and #4 Both Resolved

- **#3 (Volume Inverted):** Explained by ⚡ contamination (84-98% of high-vol buckets). Non-⚡ sweet spot is 2-3x.
- **#4 (✓★ < ✓):** Caused by ✓★'s ≥5x vol requirement putting trades in the worst MFE bucket.
- Both fix naturally with Runner Score + ✓★ criteria changes.
