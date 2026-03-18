# AutoKLB — Autonomous Signal Research

Autonomous experiment loop for KLB signal optimization.
Inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch).

## Setup

Branch: `autoklb/v38-realdata`

1. **Read files**:
   - `debug/autoklb_signals.py` — the file you modify (signal logic)
   - `debug/autoklb_realdata.py` — real-data harness (DO NOT MODIFY)
   - `debug/autoklb_eval.py` — runs both evals (DO NOT MODIFY)
   - This file — your instructions
2. **Baseline already recorded** in `debug/autoklb_results.tsv`.

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
4. Run: `cd debug && python3 autoklb_eval.py > autoklb_run.log 2>&1`
5. Check catalog: `grep "^train_score:\|^val_score:" debug/autoklb_run.log`
6. Check real-data: `grep "^rd_train_score:\|^rd_val_score:" debug/autoklb_run.log`
7. If both greps empty → crash. Run `tail -50 debug/autoklb_run.log`, fix or skip.
8. Log to results.tsv (all 8 score columns)
9. **KEEP** if `rd_val_score` improved (or equal) AND `rd_train_score` didn't drop >5%
10. **DISCARD** (`git reset --hard HEAD~1`) otherwise
11. REPEAT

**NEVER STOP.** Do not ask the human if you should continue. Run until interrupted.

## Data architecture (v3.8)

- **Signal detection**: native 5m bars from `bars/` — Jan 2024 → Mar 2026 (2 years)
- **MFE/MAE (val, Sep 2025+)**: 15sec bars from `bars_highres/15sec/` — 240 bars = 60 min
- **MFE/MAE (train, Feb 2025–Sep 2025)**: 1m bars from `bars/` — 60 bars = 60 min
- **MFE/MAE (deep train, Jan–Feb 2025)**: 5m bars — 12 bars = 60 min
- **Daily ATR**: prior-day Wilder ATR from `bars/*_1_day_ib.parquet`
- **Train**: Jan 2024 – Sep 2025  |  **Val**: Oct 2025 – Jan 2026  |  **Holdout**: Feb–Mar 2026

## Research agenda (priority order)

### Phase 1 — Time gates (biggest lever first)
- **Midday kill switch**: suppress all signals 11:00–14:00 ET (midday net = -99 ATR)
  - Start: add `MIDDAY_SUPPRESS = True` and gate on `timing == "midday"`
  - Variants: 11:30–13:30, 12:00–14:00, bear-only midday suppression
- **Afternoon trim**: 14:00–16:00 barely breaks even — try suppressing 14:00–15:00
- **Morning-only mode**: keep only 9:30–11:00 where edge is concentrated

### Phase 2 — REV routing (second-biggest drag)
REV is -389 ATR net (v3.3). Bear REV at highs (PM H, ORB H, Week H) are the worst:
- Suppress bear REV at PM High, ORB High, Week High entirely
- Or route them to BRK only (require price to have already broken through)
- Per-symbol: AMD / META bear REV are disproportionate losers — check and suppress

### Phase 3 — BRK level expansion
BRK is +677 ATR net. More BRK-eligible levels = more winners:
- Add VWAP to BRK_BULL_LEVELS (VWAP counter-trend BRK = 83% win rate, proven)
- Add Today Open, PD Close to BRK routing (currently only REV-ungated)
- Add ORB High to BRK_BEAR_LEVELS (breakdowns below ORB High)

### Phase 4 — SL by signal type
Current SL is fixed at 0.15 ATR. Optimal per type:
- BRK: 0.25 ATR optimal (+0.0105/sig)
- REV: 0.10 ATR optimal (+0.0052/sig)
- QBS: 0.08 ATR optimal
→ Add `SL_BY_TYPE = {"BRK": 0.25, "REV": 0.10, "QBS": 0.08}` to signals.py
  and pass signal_type through to the harness SL simulation

### Phase 5 — Gate tuning (familiar territory)
- VOL_RATIO_MIN: current 1.0 — try 0.5 or remove
- FRESHNESS_MAX_TESTS: current 3 — try 2 or 4
- LEVEL_PROXIMITY_ATR: current 0.10 — try 0.15 or 0.20

## Anti-patterns — skip these
- Day-of-week filters (proven flat: 18.7-19.8%)
- ADX > 30 gate (slightly negative)
- close_pos >= 80% as gate (Dead End: cuts 70% of signals, doesn't replicate)
- Volume >= 5x as positive signal (worst bucket: 0.859 MFE)

## Strategy tips
- ONE change per experiment — isolate the variable
- Check train AND val — if train improves but val doesn't, discard
- Push in the same direction until it reverses, then back off one step
- Simpler > complex if score holds
