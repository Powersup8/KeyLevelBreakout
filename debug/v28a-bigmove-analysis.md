# v2.8a ⚡ Big-Move Flag Analysis (2026-03-03)

## Problem
⚡ (bar range ≥ 2x ATR) triggers `size.large` labels, implying "size up." But ⚡ signals have **0.598 MFE vs 1.152 for normal** — nearly half the follow-through.

## Root Cause: Entry at Exhaustion

MFE drops monotonically as bar range increases:

| Range ATR | N | ⚡ % | MFE | MAE | Win% |
|-----------|---|------|-----|-----|------|
| <1.5 | 331 | 0% | 1.329 | 1.147 | 53% |
| 1.5-2.0 | 360 | 0% | 1.024 | 0.891 | 50% |
| 2.0-3.0 | 431 | 94% | 0.691 | 0.796 | 48% |
| 3.0-5.0 | 305 | 100% | 0.561 | 0.567 | 49% |
| 5.0+ | 148 | 100% | 0.426 | 0.362 | 61% |

The bigger the signal bar, the less room to run. Entry is near the bar's extreme (bull close_pos 84% vs normal 80%).

## Consistent Across All Timeframes

| Window | ⚡ MFE | Normal MFE | Gap |
|--------|--------|-----------|-----|
| 5m | 0.284 | 0.527 | -46% |
| 15m | 0.442 | 0.850 | -48% |
| 30m | 0.598 | 1.152 | -48% |

## Volume Compounds the Problem

| Vol bucket | ⚡ MFE |
|-----------|--------|
| <2x | 0.867 |
| 2-5x | 0.693 |
| 5-10x | 0.617 |
| 10x+ | 0.476 |

High volume + big move = exhaustion (worst MFE).

## ⚡ + ⚠ Body Warn = Worst Combo

| | MFE | MAE | Win% |
|--|-----|-----|------|
| ⚡+⚠ | 0.548 | 0.680 | 49% |
| ⚡ only | 0.623 | 0.632 | 50% |

## Exception: 11:xx Hour

⚡ at 11:xx: MFE=1.276, Win=62% (n=16). Small sample but midday big moves may signal trend START after consolidation, not exhaustion.

## 5.0+ ATR: Hold Signal, Not Entry

Range 5.0+ has the best win rate (61%) and best MFE/MAE ratio (1.18). These massive moves don't reverse — good for holding existing positions, bad for fresh entries.

## By Symbol

| Symbol | ⚡ MFE | Normal MFE | Gap |
|--------|--------|-----------|-----|
| TSLA | 0.981 | 2.088 | -53% |
| META | 0.897 | 2.047 | -56% |
| QQQ | 0.742 | 1.020 | -27% |
| AMD | 0.575 | 1.638 | -65% |
| AAPL | 0.260 | 0.541 | -52% |

Every symbol shows the same pattern. AMD gap is worst (-65%).

## Recommended Fix
1. **Remove `size.large` from ⚡** — stop treating big-move as "size up"
2. **Keep ⚡ glyph** on labels as informational marker
3. **Optional:** dim ⚡ signals (like moderate ramp dimming) to discourage fresh entries
4. **If already in position:** ⚡ confirms "hold" (5.0+ range doesn't reverse)
