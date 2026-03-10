# AutoKLB Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an autonomous experiment loop that lets an AI agent iterate on KLB signal logic overnight, evaluating against the move catalog with walk-forward overfitting protection.

**Architecture:** Three files mirroring Karpathy's autoresearch: `autoklb_prepare.py` (immutable eval harness), `autoklb_signals.py` (agent-editable signal logic), `autoklb_program.md` (human-editable research instructions). The prepare script imports the signals module, runs `classify_signal()` on every catalog move, and prints a fixed-format composite score.

**Tech Stack:** Python 3, pandas, numpy. No new dependencies.

**Design doc:** `docs/plans/2026-03-10-autoklb-design.md`

---

### Task 1: Create `autoklb_signals.py` — v3.6 Signal Logic in Python

**Files:**
- Create: `debug/autoklb_signals.py`
- Reference: `debug/catalog_klb_match.py` (v3.2 baseline to upgrade)
- Reference: `KeyLevelBreakout.pine` (v3.6 source of truth)

**Step 1: Write the signals file**

This is the agent's playground — the file it will modify during experiments. It contains all signal routing, gate thresholds, suppressions, and quality overrides from v3.6. Translate from `catalog_klb_match.py` (v3.2) and add all v3.3–v3.6 changes.

```python
#!/usr/bin/env python3
"""
AutoKLB Signal Logic — v3.6 baseline
=====================================
The ONLY file the agent modifies. Contains all signal routing,
gate thresholds, suppressions, and quality override rules.

Contract: classify_signal(row) -> dict with keys:
  - would_fire: bool
  - signal_type: str | None  ("BRK", "REV", "FADE")
  - blocked_by: list[str]
  - is_dimmed: bool
"""

import numpy as np

# ══════════════════════════════════════════════════════════════════════════════
# GATE THRESHOLDS — agent can tune these
# ══════════════════════════════════════════════════════════════════════════════
BODY_PCT_MIN = 30.0
VOL_RATIO_MIN = 1.0           # v3.3: lowered from 1.5
VOL_EXHAUSTION_MAX = 5.0       # v3.3: trigger vol > 5x → dim
ADX_MIN = 20.0
LEVEL_PROXIMITY_ATR = 0.10     # within 10% ATR to count as "at level"
FRESHNESS_MAX_TESTS = 3        # v3.3: 3rd+ test at same level → dim
ATR_CONSUMED_MAX = 1.5         # v3.3: afternoon exhaustion threshold
SPY_RANGE_EXHAUSTION = 0.008   # v3.3: SPY range > 0.8% in exhaustion check
REV_PROXIMITY_TOL = 0.03       # v3.6: bear REV fires within 0.03 ATR of level

# ── Quality override thresholds ──
QUIET_COIL_VOL_RAMP = 0.5     # v3.3: pre-vol ramp < 0.5 = drying
QUIET_COIL_RANGE = 0.5        # v3.3: trigger range < 0.5 ATR = small
MIDDAY_EMA_CHANGE = 0.02      # v3.3b: EMA change < 0.02 ATR in 30m = flat
BROAD_COIL_RANGE = 0.5        # v3.3b: trigger range < 0.5 ATR
BROAD_COIL_SPY_MIN = 0.003    # v3.3b: SPY moving > 0.3%

# ══════════════════════════════════════════════════════════════════════════════
# SIGNAL ROUTING — agent can modify these sets
# ══════════════════════════════════════════════════════════════════════════════

# BRK levels (barriers — price breaks through)
BRK_BEAR_LEVELS = {
    "PM Low", "PD Low", "Week Low", "ORB Low",
    "Week Open", "Month Open",
    "PD Last Hr Low", "PD Last Hr High",
}
BRK_BULL_LEVELS = {
    "Week Open", "Month Open",
    "PD Last Hr High",          # v3.4: added
}

# REV levels — EMA gated
REV_LEVELS_GATED = {
    "PM Low", "PD Low", "Week Low",             # bull REV at LOWs
    "PD Last Hr Low",                            # bull REV
    # NOTE: PM High, PD High, Week High, ORB High removed — bull REV suppressed v3.3c
}

# REV levels — ungated (no EMA, no VWAP)
REV_LEVELS_UNGATED = {
    "PD Mid", "Today Open", "PD Close",
}

# Direction routing
REV_BULL_LEVELS = {
    "PM Low", "PD Low", "Week Low",             # bull REV at LOWs (gated)
    "PD Last Hr Low",                            # bull REV (gated)
    "PD Mid", "Today Open", "PD Close",          # magnet REV (ungated)
    # v3.3c: PM High, PD High, Week High, ORB High REMOVED for bull REV
}

REV_BEAR_LEVELS = {
    "PM High", "PD High", "Week High", "ORB High",  # bear REV (EXREV) — kept
    "PD Mid", "Today Open", "PD Close",               # magnet REV (ungated)
}

# ── Suppressions ──
DISABLED_SIGNALS = {
    ("ORB Low", "bull", "REV"),          # v3.2: disabled
    ("PM High", "bull", "REV"),          # v3.3c: bull REV at HIGHs suppressed
    ("PD High", "bull", "REV"),          # v3.3c
    ("Week High", "bull", "REV"),        # v3.3c
    ("ORB High", "bull", "REV"),         # v3.3c
}

# Per-symbol suppressions
SYMBOL_DISABLED = {
    "NVDA": {("*", "bull", "REV")},      # v3.3d: all NVDA bull REV suppressed
}

# ── Timing ──
SUPPRESS_AFTERNOON = False               # v3.5: toggleable, default off
ORB_LOW_RECLAIM_MIDDAY_ONLY = True       # v3.4: ORB Low bull REV = midday only

# ══════════════════════════════════════════════════════════════════════════════
# SIGNAL CLASSIFICATION
# ══════════════════════════════════════════════════════════════════════════════

def _is_midday(timing):
    return timing == "midday"

def _is_afternoon(timing):
    return timing == "afternoon"

def _check_symbol_suppression(symbol, level, direction, sig_type):
    """Check per-symbol suppression rules."""
    if symbol not in SYMBOL_DISABLED:
        return False
    for rule in SYMBOL_DISABLED[symbol]:
        rlevel, rdir, rtype = rule
        if (rlevel == "*" or rlevel == level) and rdir == direction and rtype == sig_type:
            return True
    return False


def classify_signal(row):
    """
    For a single catalog move, determine if KLB v3.6 would fire a signal.

    Args:
        row: pandas Series with catalog columns

    Returns:
        dict with keys: would_fire, signal_type, blocked_by, is_dimmed
    """
    level = row["nearest_level_type"]
    dist = row["nearest_level_dist_atr"]
    direction = row["direction"]
    symbol = row["symbol"]
    ema = row["trig_ema_aligned"]
    body = row["trig_body_pct"]
    vol = row["trig_vol_ratio"]
    adx = row["pre_adx"]
    vwap = row["trig_vwap_aligned"]
    timing = row["timing_category"]
    interaction = row["level_interaction"]
    pre_vol = row.get("pre_vol_avg_ratio", np.nan)
    trig_range = row.get("trig_range_atr", np.nan)
    spy_mag = row.get("spy_magnitude_atr", np.nan)

    result = {
        "would_fire": False,
        "signal_type": None,
        "blocked_by": [],
        "is_dimmed": False,
    }

    # ── Afternoon suppression (v3.5) ──
    if SUPPRESS_AFTERNOON and _is_afternoon(timing):
        result["blocked_by"].append("afternoon_suppressed")
        return result

    # ── Proximity check ──
    # v3.6: bear REV gets proximity tolerance
    prox = LEVEL_PROXIMITY_ATR
    if direction == "bear" and level in REV_BEAR_LEVELS:
        prox = max(LEVEL_PROXIMITY_ATR, REV_PROXIMITY_TOL)

    if dist > prox:
        result["blocked_by"].append("no_level_nearby")
        return result

    # ── Determine possible signal types ──
    is_brk = False
    is_rev_gated = False
    is_rev_ungated = False

    # Check disabled signals first
    if (level, direction, "REV") in DISABLED_SIGNALS:
        pass  # REV disabled for this combo
    elif _check_symbol_suppression(symbol, level, direction, "REV"):
        pass  # symbol-specific suppression
    else:
        if direction == "bull":
            if level in REV_BULL_LEVELS:
                if level in REV_LEVELS_UNGATED:
                    is_rev_ungated = True
                elif level in REV_LEVELS_GATED:
                    is_rev_gated = True
        else:
            if level in REV_BEAR_LEVELS:
                if level in REV_LEVELS_UNGATED:
                    is_rev_ungated = True
                elif level in REV_LEVELS_GATED:
                    is_rev_gated = True

    # ORB Low reclaim: midday only (v3.4)
    if level == "ORB Low" and direction == "bull" and ORB_LOW_RECLAIM_MIDDAY_ONLY:
        if is_rev_gated and not _is_midday(timing):
            is_rev_gated = False

    if direction == "bull":
        if level in BRK_BULL_LEVELS and interaction == "broke_through":
            is_brk = True
    else:
        if level in BRK_BEAR_LEVELS and interaction == "broke_through":
            is_brk = True

    if not is_brk and not is_rev_gated and not is_rev_ungated:
        result["blocked_by"].append("no_matching_signal_type")
        return result

    # ── Try each signal type, check gates ──
    # Priority: ungated REV > gated REV > BRK

    if is_rev_ungated:
        blocks = []
        if body < BODY_PCT_MIN:
            blocks.append("body_pct")
        if vol < VOL_RATIO_MIN:
            blocks.append("volume")
        if adx < ADX_MIN:
            blocks.append("adx")
        if not blocks:
            result["signal_type"] = "REV"
            result["would_fire"] = True
            result["is_dimmed"] = _check_dim(vol, pre_vol, trig_range, timing, spy_mag)
            return result
        result["blocked_by"] = blocks

    if is_rev_gated:
        blocks = []
        if not ema and timing != "open_flush":
            blocks.append("ema_gate")
        if body < BODY_PCT_MIN:
            blocks.append("body_pct")
        if vol < VOL_RATIO_MIN:
            blocks.append("volume")
        if adx < ADX_MIN:
            blocks.append("adx")
        if not vwap:
            blocks.append("vwap_filter")
        if not blocks:
            result["signal_type"] = "REV"
            result["would_fire"] = True
            result["is_dimmed"] = _check_dim(vol, pre_vol, trig_range, timing, spy_mag)
            return result
        if not result["blocked_by"]:
            result["blocked_by"] = blocks

    if is_brk:
        blocks = []
        if not ema and timing != "open_flush":
            blocks.append("ema_gate")
        if body < BODY_PCT_MIN:
            blocks.append("body_pct")
        if vol < VOL_RATIO_MIN:
            blocks.append("volume")
        if adx < ADX_MIN:
            blocks.append("adx")
        if not blocks:
            result["signal_type"] = "BRK"
            result["would_fire"] = True
            result["is_dimmed"] = _check_dim(vol, pre_vol, trig_range, timing, spy_mag)
            return result
        if not result["blocked_by"]:
            result["blocked_by"] = blocks

    return result


def _check_dim(vol, pre_vol, trig_range, timing, spy_mag):
    """
    Check if signal should be dimmed (v3.3 quality filters).
    Returns False if a quality override (quiet coil, midday flat, broad coil) applies.
    """
    # ── Quality overrides (cancel dim) ──
    is_quiet_coil = (
        not np.isnan(pre_vol) and pre_vol < QUIET_COIL_VOL_RAMP
        and not np.isnan(trig_range) and trig_range < QUIET_COIL_RANGE
    )
    if is_quiet_coil:
        return False

    is_midday_flat = _is_midday(timing)
    # Note: can't check EMA slope change from catalog — approximate with timing only
    if is_midday_flat:
        return False

    is_broad_coil = (
        not np.isnan(trig_range) and trig_range < BROAD_COIL_RANGE
        and not np.isnan(spy_mag) and abs(spy_mag) > BROAD_COIL_SPY_MIN * 100
        # spy_magnitude_atr is in ATR units, not pct — approximate
    )
    if is_broad_coil:
        return False

    # ── Dim conditions ──
    is_vol_exhaust = not np.isnan(vol) and vol > VOL_EXHAUSTION_MAX
    is_exhausted = (
        _is_afternoon(timing)
        # Can't fully check ATR consumed + SPY range from catalog
        # Approximate: afternoon + high vol = exhaustion signal
    )

    return is_vol_exhaust or is_exhausted
```

**Step 2: Verify it runs standalone**

Run: `cd debug && python3 -c "import autoklb_signals; print('OK: classify_signal loaded')"`
Expected: `OK: classify_signal loaded`

**Step 3: Commit**

```bash
git add debug/autoklb_signals.py
git commit -m "autoklb: v3.6 signal logic — agent-editable file for autonomous research"
```

---

### Task 2: Create `autoklb_prepare.py` — Evaluation Harness

**Files:**
- Create: `debug/autoklb_prepare.py`
- Reference: `debug/autoklb_signals.py` (imports classify_signal)
- Data: `debug/move-catalog.parquet`

**Step 1: Write the prepare/eval harness**

```python
#!/usr/bin/env python3
"""
AutoKLB Evaluation Harness — DO NOT MODIFY
============================================
Loads the move catalog, applies signal logic from autoklb_signals.py,
computes composite scores on train/val splits.

Inspired by karpathy/autoresearch — this is the fixed evaluation,
the agent only modifies autoklb_signals.py.

Usage: python autoklb_prepare.py
Output: fixed-format scores the agent greps for keep/discard decisions.
"""

import time
import importlib
import numpy as np
import pandas as pd
from pathlib import Path

# ── Fixed constants (never changed) ─────────────────────────────────────────
CATALOG_PATH = Path(__file__).parent / "move-catalog.parquet"
EXCLUDE_SYMBOLS = {"TSM"}  # anomalous daily ATR

# Walk-forward split dates
TRAIN_END = "2025-09-30"     # Train: everything up to Sep 2025
VAL_END = "2026-01-31"       # Val: Oct 2025 – Jan 2026
# Holdout: Feb 2026+ (never used during experiments)

MIN_SIGNALS_RAMP = 100       # opportunity ramp reaches 1.0 at N=100
WIN_RATE_BASELINE = 0.50     # quality multiplier baseline


def load_catalog():
    """Load move catalog, filter to primary pass with 1m data."""
    df = pd.read_parquet(CATALOG_PATH)
    mask = (
        (df["pass"] == "primary")
        & (~df["symbol"].isin(EXCLUDE_SYMBOLS))
        & (df["mfe_1m"].notna())
        & (df["mae_1m"].notna())
    )
    return df[mask].copy()


def split_data(df):
    """Walk-forward train/val/holdout split."""
    train = df[df["date"] <= TRAIN_END]
    val = df[(df["date"] > TRAIN_END) & (df["date"] <= VAL_END)]
    holdout = df[df["date"] > VAL_END]
    return train, val, holdout


def compute_pnl(row):
    """Compute signal P&L in ATR units from 1m MFE/MAE."""
    mfe = row["mfe_1m"]
    mae = row["mae_1m"]
    if mfe >= 0.10 and mfe > mae:
        return mfe - mae  # winner
    else:
        return -mae  # loser (stopped out at max adverse)


def compute_score(fired_df):
    """
    Composite metric: Guarded Net ATR.
    score = net_atr * (win_rate / 0.50) * min(1.0, N / 100)
    """
    if len(fired_df) == 0:
        return 0.0, 0.0, 0.0, 0

    pnls = fired_df["pnl_atr"]
    net_atr = pnls.sum()
    n = len(fired_df)
    win_rate = (pnls > 0).mean()

    quality_mult = win_rate / WIN_RATE_BASELINE
    opportunity_ramp = min(1.0, n / MIN_SIGNALS_RAMP)

    score = net_atr * quality_mult * opportunity_ramp
    return score, net_atr, win_rate, n


def run_evaluation(df, label=""):
    """Run signal logic on a dataset split and compute score."""
    import autoklb_signals as signals
    importlib.reload(signals)  # pick up latest changes

    results = df.apply(signals.classify_signal, axis=1, result_type="expand")
    df = df.copy()
    df["would_fire"] = results["would_fire"]
    df["signal_type"] = results["signal_type"]
    df["is_dimmed"] = results["is_dimmed"]

    fired = df[df["would_fire"]].copy()

    # Compute P&L for fired signals (exclude dimmed)
    active = fired[~fired["is_dimmed"]].copy()
    active["pnl_atr"] = active.apply(compute_pnl, axis=1)

    score, net_atr, win_rate, n = compute_score(active)

    # Also compute dimmed stats for info
    dimmed = fired[fired["is_dimmed"]]

    return {
        "score": score,
        "net_atr": net_atr,
        "win_rate": win_rate * 100,
        "n": n,
        "n_dimmed": len(dimmed),
        "n_blocked": len(df) - len(fired),
    }


def main():
    t0 = time.time()

    # Load and split
    df = load_catalog()
    train, val, holdout = split_data(df)

    print(f"catalog_moves:    {len(df)}")
    print(f"train_moves:      {len(train)}")
    print(f"val_moves:        {len(val)}")
    print(f"holdout_moves:    {len(holdout)}")
    print()

    # Evaluate on train and val
    train_r = run_evaluation(train, "train")
    val_r = run_evaluation(val, "val")

    elapsed = time.time() - t0

    # ── Fixed output format (agent greps these lines) ──
    print("---")
    print(f"train_score:      {train_r['score']:.1f}")
    print(f"train_net_atr:    {train_r['net_atr']:.1f}")
    print(f"train_win_rate:   {train_r['win_rate']:.1f}")
    print(f"train_n:          {train_r['n']}")
    print(f"train_n_dimmed:   {train_r['n_dimmed']}")
    print(f"val_score:        {val_r['score']:.1f}")
    print(f"val_net_atr:      {val_r['net_atr']:.1f}")
    print(f"val_win_rate:     {val_r['win_rate']:.1f}")
    print(f"val_n:            {val_r['n']}")
    print(f"val_n_dimmed:     {val_r['n_dimmed']}")
    print(f"total_seconds:    {elapsed:.1f}")


if __name__ == "__main__":
    main()
```

**Step 2: Run baseline evaluation**

Run: `cd debug && python3 autoklb_prepare.py`
Expected: Prints catalog stats, then `---` followed by train/val scores. Should complete in <15 seconds.

**Step 3: Verify output is greppable**

Run: `cd debug && python3 autoklb_prepare.py 2>&1 | grep "^val_score:"`
Expected: One line like `val_score:      42.1`

**Step 4: Commit**

```bash
git add debug/autoklb_prepare.py
git commit -m "autoklb: evaluation harness — immutable prepare script with walk-forward split"
```

---

### Task 3: Create `autoklb_program.md` — Agent Instructions

**Files:**
- Create: `debug/autoklb_program.md`
- Reference: `docs/plans/2026-03-10-autoklb-design.md`

**Step 1: Write the program file**

```markdown
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
```

**Step 2: Commit**

```bash
git add debug/autoklb_program.md
git commit -m "autoklb: agent program instructions with research context"
```

---

### Task 4: Run Baseline & Verify End-to-End

**Files:**
- No new files
- Run: `debug/autoklb_prepare.py`

**Step 1: Run the full evaluation**

Run: `cd debug && python3 autoklb_prepare.py`
Expected: Completes in <15 seconds, prints catalog stats + scores.

**Step 2: Verify scores are reasonable**

Check:
- `train_n` should be in hundreds (not 0, not 50,000+)
- `val_n` should be smaller than train_n (fewer months)
- `train_win_rate` should be roughly 45-55%
- `train_score` should be positive (our signal logic has an edge)
- Signals should fire — if train_n=0, something is wrong with the logic translation

**Step 3: Debug if needed**

If scores look wrong, run diagnostic:
```python
cd debug && python3 -c "
import pandas as pd
import autoklb_signals as s
df = pd.read_parquet('move-catalog.parquet')
p = df[(df['pass']=='primary') & (df['symbol']!='TSM') & df['mfe_1m'].notna()]
r = p.head(100).apply(s.classify_signal, axis=1, result_type='expand')
print(r['would_fire'].sum(), 'of 100 would fire')
print(r['blocked_by'].value_counts())
"
```

**Step 4: Record baseline in results.tsv**

Create `debug/autoklb_results.tsv`:
```
commit	train_score	val_score	train_n	val_n	status	description
<hash>	<score>	<score>	<n>	<n>	keep	v3.6 baseline
```

**Step 5: Commit results**

```bash
git add debug/autoklb_results.tsv
git commit -m "autoklb: baseline results recorded"
```

---

### Task 5: Dry-Run One Experiment Cycle

**Files:**
- Modify: `debug/autoklb_signals.py` (one parameter change)

**Step 1: Make a single parameter change**

Change `VOL_RATIO_MIN` from `1.0` to `0.5` in `autoklb_signals.py`.

**Step 2: Commit and run**

```bash
cd debug
git commit -am "autoklb experiment: lower vol gate to 0.5x"
python3 autoklb_prepare.py > autoklb_run.log 2>&1
grep "^train_score:\|^val_score:" autoklb_run.log
```

**Step 3: Evaluate keep/discard**

- If `val_score` improved → keep, log to results.tsv
- If `val_score` worse → `git reset --hard HEAD~1`, log as discard

**Step 4: Log result**

Append to `debug/autoklb_results.tsv`.

**Step 5: Revert if discarded, commit results**

This verifies the full loop works end-to-end before handing off to autonomous mode.
