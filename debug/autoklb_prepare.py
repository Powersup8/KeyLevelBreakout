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
from datetime import date
import numpy as np
import pandas as pd
from pathlib import Path

# ── Fixed constants (never changed) ─────────────────────────────────────────
CATALOG_PATH = Path(__file__).parent / "move-catalog.parquet"
EXCLUDE_SYMBOLS = {"TSM"}  # anomalous daily ATR

# Walk-forward split dates
TRAIN_END = date(2025, 9, 30)     # Train: everything up to Sep 2025
VAL_END = date(2026, 1, 31)       # Val: Oct 2025 – Jan 2026
# Holdout: Feb 2026+ (never used during experiments)

MIN_SIGNALS_RAMP = 100       # opportunity ramp reaches 1.0 at N=100
WIN_RATE_BASELINE = 0.50     # quality multiplier baseline
HIGHRES_START = date(2025, 9, 2)   # 15sec MFE/MAE available from here


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
    """Compute signal P&L using best available MFE/MAE (15sec > 1m)."""
    if ("mfe_15sec" in row.index
            and pd.notna(row["mfe_15sec"])
            and pd.notna(row["mae_15sec"])):
        mfe = row["mfe_15sec"]
        mae = row["mae_15sec"]
    else:
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
