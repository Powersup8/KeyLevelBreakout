#!/usr/bin/env python3
"""
AutoKLB Holdout Evaluation
===========================
Evaluates Feb–Mar 2026 (holdout) performance of current signals.py.
Compares against train and val to check for overfitting.

Run: python3 debug/autoklb_holdout.py
"""

import sys
import importlib
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

# ── Import harness functions directly ─────────────────────────────────────────
DEBUG_DIR = Path(__file__).parent
sys.path.insert(0, str(DEBUG_DIR))

# Reload harness to pick up any changes
import autoklb_realdata as harness
importlib.reload(harness)

HOLDOUT_START = date(2026, 2, 1)
HOLDOUT_END   = date(2026, 3, 31)   # through today


def main():
    import time
    t0 = time.time()

    print(f"AutoKLB Holdout Check — Feb–Mar 2026")
    print(f"Train:   Jan 2024 – Sep 2025")
    print(f"Val:     Oct 2025 – Jan 2026")
    print(f"Holdout: {HOLDOUT_START} – {HOLDOUT_END}")
    print()

    # Load levels (same as harness main())
    levels_db = pd.read_parquet(harness.LEVELS_PATH)
    levels_db["date"] = pd.to_datetime(levels_db["date"])

    all_signals = []

    for symbol in harness.SYMBOLS:
        df_5m     = harness.load_5m(symbol)
        if df_5m is None or len(df_5m) == 0:
            continue

        daily_atr_map = harness.load_daily_atr(symbol)
        levels_sym    = levels_db[levels_db["symbol"] == symbol].copy()
        df_5m_ind     = harness.compute_indicators(df_5m)
        df_1m     = harness.load_1m(symbol)
        df_15sec  = harness.load_15sec(symbol)

        fired = harness.emit_signals(symbol, df_5m_ind, levels_sym, daily_atr_map)

        for sig in fired:
            mfe, mae = harness.get_forward_pnl(
                sig["timestamp"], sig["direction"], sig["daily_atr"],
                df_5m, df_1m, df_15sec,
            )
            if not (np.isnan(mfe) or np.isnan(mae)):
                sig["mfe"] = mfe
                sig["mae"] = mae
                all_signals.append(sig)

    if not all_signals:
        print("No signals found.")
        return

    df = pd.DataFrame(all_signals)
    df["date_dt"] = pd.to_datetime(df["date"])

    # Capacity cap (same as harness)
    df = (df.sort_values(["symbol", "date_dt", "timestamp"])
            .groupby(["symbol", "date_dt"])
            .head(harness.MAX_SIGNALS_PER_SYM_DAY)
            .reset_index(drop=True))

    df["pnl_atr"] = df.apply(harness.compute_pnl, axis=1)

    train   = df[df["date_dt"] <= pd.Timestamp(harness.TRAIN_END)]
    val     = df[(df["date_dt"] >  pd.Timestamp(harness.TRAIN_END)) &
                 (df["date_dt"] <= pd.Timestamp(harness.VAL_END))]
    holdout = df[(df["date_dt"] >  pd.Timestamp(harness.VAL_END)) &
                 (df["date_dt"] <= pd.Timestamp(HOLDOUT_END))]

    ts, tn, twr, tN = harness.compute_score(train)
    vs, vn, vwr, vN = harness.compute_score(val)
    hs, hn, hwr, hN = harness.compute_score(holdout)

    elapsed = time.time() - t0

    print(f"{'Split':<12} {'Score':>8}  {'Net ATR':>8}  {'Win%':>7}  {'N':>6}")
    print(f"{'─'*12} {'─'*8}  {'─'*8}  {'─'*7}  {'─'*6}")
    print(f"{'Train':<12} {ts:>8.1f}  {tn:>8.3f}  {twr*100:>6.1f}%  {tN:>6}")
    print(f"{'Val':<12} {vs:>8.1f}  {vn:>8.3f}  {vwr*100:>6.1f}%  {vN:>6}")
    print(f"{'Holdout':<12} {hs:>8.1f}  {hn:>8.3f}  {hwr*100:>6.1f}%  {hN:>6}")
    print()

    # Overfitting check
    if vN > 0 and hN > 0:
        val_net   = vn
        hold_net  = hn
        ratio = hold_net / val_net if val_net != 0 else float('nan')
        print(f"Holdout/Val net ATR ratio: {ratio:.2f}  (1.0 = perfect, >0.7 = healthy)")
        if ratio >= 0.7:
            print("✓ Holdout looks HEALTHY — generalization is solid.")
        elif ratio >= 0.4:
            print("⚠ Holdout shows SOME degradation — watch closely.")
        else:
            print("✗ Holdout DIVERGING — likely overfitting to val period.")

    print(f"\n(completed in {elapsed:.0f}s)")

    # Per-symbol holdout breakdown
    print(f"\n── Per-symbol holdout breakdown ──")
    for sym in sorted(holdout["symbol"].unique()):
        sym_df = holdout[holdout["symbol"] == sym]
        s, n, wr, N = harness.compute_score(sym_df)
        flag = "✓" if n > 0 else "✗"
        print(f"  {sym:<6} score={s:>7.1f}  net={n:>7.3f}  win={wr*100:>5.1f}%  N={N}  {flag}")


if __name__ == "__main__":
    main()
