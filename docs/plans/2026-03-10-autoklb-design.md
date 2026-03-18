# AutoKLB — Autonomous Signal Research Loop

**Date:** 2026-03-10
**Inspired by:** [karpathy/autoresearch](https://github.com/karpathy/autoresearch)
**Goal:** Let an AI agent autonomously iterate on KLB signal logic overnight, evaluating against historical data with overfitting protection.

## Architecture

Four files in `debug/`:

| File | Role | Modified by |
|---|---|---|
| `autoklb_prepare.py` | Load catalog, split data, run signals, compute score | **Nobody** (immutable) |
| `autoklb_signals.py` | Signal logic: gates, routing, suppressions, overrides | **Agent** |
| `autoklb_program.md` | Experiment instructions + research context | **Human** |
| `autoklb_results.tsv` | Experiment log (commit, scores, status, description) | **Agent** |

## Data Flow

```
move-catalog.parquet ──→ autoklb_prepare.py ──→ imports autoklb_signals.py
                              │                        │
                              │     applies classify_signal() to each move
                              │                        │
                              ▼                        ▼
                         train/val split ──→ compute score on both
                              │
                              ▼
                         print fixed-format results (agent greps)
```

## Composite Metric (Guarded Net ATR)

```
score = net_atr × quality_multiplier × opportunity_ramp

  quality_multiplier = win_rate / 0.50    (>1 above 50% win, penalty below)
  opportunity_ramp   = min(1.0, N / 100)  (ramp 0→1 for first 100 signals)
```

Why this metric:
- Net ATR drives it (profit is king)
- Win rate guard prevents asymmetric loss strategies
- Opportunity ramp prevents cherry-picking few perfect signals
- Simple, interpretable, no cliff edges to game

## Walk-Forward Data Split

- **Train:** Jan 2024 – Sep 2025 (21 months, ~70%)
- **Val:** Oct 2025 – Jan 2026 (4 months, ~20%)
- **Holdout:** Feb – Mar 2026 (untouched until final evaluation)

Only moves with 1m MFE/MAE data are scored (38% coverage = ~27K moves). 5m data overstates MFE by ~31% and would distort the metric.

## Agent Scope (Option 2: Parameters + Signal Routing)

### What the agent CAN modify in `autoklb_signals.py`:

**Gate thresholds (~15 parameters):**
- `BODY_PCT_MIN`, `VOL_RATIO_MIN`, `VOL_EXHAUSTION_MAX`
- `ADX_MIN`, `LEVEL_PROXIMITY_ATR`, `FRESHNESS_MAX_TESTS`
- `ATR_CONSUMED_EXHAUSTION`, adaptive SL params, proximity tolerance

**Signal routing (~20 mappings):**
- `BRK_BEAR_LEVELS`, `BRK_BULL_LEVELS` — which levels produce breakouts
- `REV_BULL_LEVELS`, `REV_BEAR_LEVELS` — which levels produce reversals
- `REV_LEVELS_GATED`, `REV_LEVELS_UNGATED` — EMA gate routing
- `DISABLED_SIGNALS` — suppression rules per (level, direction, type)
- Per-symbol overrides (e.g., NVDA bull REV suppression)

**Quality overrides (~3 boost rules):**
- Quiet coil parameters and override behavior
- Midday flat EMA boost
- Broad coil boost

### What the agent CANNOT modify:
- `autoklb_prepare.py` (evaluation harness, data split, metric)
- Move catalog data
- Function signature: `classify_signal(row) -> dict` with fixed return keys

## Signal Function Contract

```python
def classify_signal(row) -> dict:
    """
    row: a Series from the move catalog with columns like
         nearest_level_type, nearest_level_dist_atr, direction,
         trig_ema_aligned, trig_body_pct, trig_vol_ratio, etc.

    Returns: {
        "would_fire": bool,
        "signal_type": str | None,   # "BRK", "REV", "FADE", etc.
        "blocked_by": list[str],
        "is_dimmed": bool,
    }
    """
```

## Experiment Loop

```
LOOP:
  1. Read current autoklb_signals.py + results history
  2. Propose ONE change (parameter tweak or routing modification)
  3. git commit the change
  4. Run: python debug/autoklb_prepare.py > debug/autoklb_run.log 2>&1
  5. Grep results: grep "^train_score:\|^val_score:" debug/autoklb_run.log
  6. If crash → tail -50 debug/autoklb_run.log, fix or skip
  7. Log to autoklb_results.tsv
  8. KEEP if val_score improved AND train_score didn't degrade >5%
  9. DISCARD (git reset) otherwise
  10. REPEAT indefinitely
```

## Keep/Discard Rules

- **KEEP:** `val_score` improved (or equal) AND `train_score` didn't drop more than 5%
- **DISCARD:** val_score worse, OR train improved but val didn't follow (overfitting)
- **CRASH:** Log as crash, attempt fix if trivial, skip if fundamental

## Research Context (seeded into program.md)

### Known patterns (already implemented, params tunable):
- Quiet coil (low vol + small range) = 35.8% great rate
- Bull REV at magnets = structurally broken → suppressed
- Level freshness: 3rd+ test = noise → threshold tunable
- Midday + flat EMA = quality window → boost active
- Volume gate counterproductive at 1.5x → lowered to 1.0x
- NVDA bull REV = -707 ATR → suppressed
- Bear REV proximity tolerance = 0.03 ATR (v3.6)
- Adaptive SL: morning 0.10, midday 0.25 ATR (v3.5)

### Anti-patterns (don't waste experiments):
- Day-of-week filters (flat 18.7-19.8%)
- ADX > 30 (slightly negative 0.97x)
- Runner score prediction (r=0.053)
- Individual pre-move factors (max 1.3x lift alone)
- Morning is BELOW baseline (18.1% vs 20.0%)

## Key Differences from Karpathy's autoresearch

| Aspect | autoresearch | AutoKLB |
|---|---|---|
| Domain | LLM training | Trading signals |
| Time per experiment | 5 min (GPU training) | ~10 sec (catalog scan) |
| Experiments/hour | ~12 | ~360 |
| Metric | `val_bpb` (single) | `train_score` + `val_score` (dual) |
| Overfitting protection | Held-out val set | Walk-forward split + val gatekeeper |
| Agent edits | `train.py` (architecture) | `autoklb_signals.py` (routing + params) |
| Keep rule | val_bpb improved | val_score improved + train stable |
