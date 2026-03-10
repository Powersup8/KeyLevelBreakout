# AutoKLB — Autonomous Signal Research

Autonomous experiment loop for KLB signal optimization.
Inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch).

## Setup

1. **Create branch**: `git checkout -b autoklb/<tag>` from current main.
2. **Read files**:
   - `debug/autoklb_signals.py` — the file you modify (signal logic)
   - `debug/autoklb_prepare.py` — evaluation harness (DO NOT MODIFY)
   - This file — your instructions
3. **Initialize results.tsv**: Create `debug/autoklb_results.tsv` with header row.
4. **Run baseline**: `cd debug && python3 autoklb_prepare.py > autoklb_run.log 2>&1`
5. **Record baseline** in results.tsv.

## Rules

**What you CAN do:**
- Modify `debug/autoklb_signals.py` — gate thresholds, signal routing sets,
  suppression rules, quality override logic, dim conditions.

**What you CANNOT do:**
- Modify `debug/autoklb_prepare.py` (evaluation harness, data split, metric)
- Modify the move catalog data
- Change the `classify_signal()` return signature
- Install new packages

**The goal: maximize `val_score`.** The metric is Guarded Net ATR:
`score = net_atr × (win_rate / 0.50) × min(1.0, N / 100)`

## Output format

The eval script prints:
```
---
train_score:      159.3
train_net_atr:    156.0
train_win_rate:   51.2
train_n:          800
val_score:        42.1
val_net_atr:      41.5
val_win_rate:     50.8
val_n:            210
total_seconds:    8.2
```

Extract key metrics: `grep "^train_score:\|^val_score:" debug/autoklb_run.log`

## Results logging

Log every experiment to `debug/autoklb_results.tsv` (tab-separated):

```
commit	train_score	val_score	train_n	val_n	status	description
a1b2c3d	159.3	42.1	800	210	keep	baseline
```

## Experiment loop

LOOP FOREVER:

1. Read current `autoklb_signals.py` + results history
2. Propose ONE change (parameter tweak or routing modification)
3. `git commit` the change
4. Run: `cd debug && python3 autoklb_prepare.py > autoklb_run.log 2>&1`
5. Read results: `grep "^train_score:\|^val_score:" debug/autoklb_run.log`
6. If grep is empty → crash. Run `tail -50 debug/autoklb_run.log`, fix or skip.
7. Log to results.tsv
8. **KEEP** if `val_score` improved (or equal) AND `train_score` didn't drop >5%
9. **DISCARD** (`git reset --hard HEAD~1`) otherwise
10. REPEAT

**NEVER STOP.** Do not ask the human if you should continue. Run until interrupted.

## Research context — what we already know

### Proven patterns (already in baseline, params tunable):
- Quiet coil (low vol + small range) = 35.8% great rate, 1.8x lift
- Bull REV at HIGHs (magnets) = structurally broken → suppressed
- NVDA bull REV = -707 ATR → suppressed
- Level freshness: 3rd+ test = noise
- Midday + flat EMA = quality window, 31.1% great
- Volume gate 1.0x better than 1.5x
- Bear REV proximity tolerance 0.03 ATR
- ORB Low reclaim midday-only = 27.2% great

### Promising directions to explore:
- Volume gate could go even lower (0.5x? 0.0x?)
- Freshness threshold: 3 tests might not be optimal (try 2 or 4)
- ADX minimum: 20 might be too high or too low
- Body% minimum: 30% might filter good signals
- Level proximity: 0.10 ATR might miss close-but-not-touching signals
- Proximity tolerance for bull REV too (not just bear)
- Suppress specific level+direction combos showing negative ATR
- Afternoon suppression toggle (currently off — turn on?)
- ORB Low reclaim: remove midday restriction?

### Anti-patterns — don't waste experiments on:
- Day-of-week filters (flat at 18.7-19.8%, no edge)
- ADX > 30 as a gate (slightly negative 0.97x)
- Individual pre-move factors (max 1.3x lift alone)

### Strategy tips:
- Make ONE change per experiment — isolate the variable
- Try the opposite of the current setting (e.g., if gate is on, try off)
- If a parameter change helps, try pushing it further in the same direction
- If stuck, try removing complexity (simpler = better if score holds)
- Check both train AND val — divergence = overfitting
