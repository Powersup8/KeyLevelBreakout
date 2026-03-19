#!/usr/bin/env python3
"""
Enrich move-catalog.parquet with missing MFE/MAE values.

Fills two gaps:
  1. mfe_1m / mae_1m for rows where it was null (1m data wasn't available
     when catalog was originally built, but now is for some symbols)
  2. mfe_15sec / mae_15sec for all rows where start_time >= HIGHRES_START
     (15sec bars available from Sep 2025 — higher-precision val-period eval)

Entry point: start_time (converted to ET), next 1m/15sec bar close.
Forward window: 60 min (60 × 1m bars  OR  240 × 15sec bars).
Normalization: catalog's own `atr` column.

Writes enriched parquet back in-place.
"""

import time
from pathlib import Path
from datetime import date

import numpy as np
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
DEBUG_DIR   = Path(__file__).parent
CATALOG     = DEBUG_DIR / "move-catalog.parquet"
CACHE_DIR   = Path(
    "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de"
    "/Meine Ablage/Claude/trading_bot/cache/bars"
)
HIGHRES_DIR = Path(
    "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de"
    "/Meine Ablage/Claude/trading_bot/cache/bars_highres/15sec"
)

HIGHRES_START = date(2025, 9, 2)
FWD_1M    = 60    # bars
FWD_15SEC = 240   # bars


# ── Loader ────────────────────────────────────────────────────────────────────

def load_bars(path, rth=True):
    path = Path(path)
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    if "date" in df.columns:
        df = df.set_index("date")
    df.index = pd.to_datetime(df.index)
    if df.index.tz is not None:
        df.index = df.index.tz_convert("US/Eastern").tz_localize(None)
    if rth:
        df = df.between_time("09:30", "16:00")
    return df[["open", "high", "low", "close", "volume"]].copy()


# ── MFE/MAE ───────────────────────────────────────────────────────────────────

def compute_fwd(df_bars, signal_ts, direction, atr, n_bars, min_bars=5):
    """Return (mfe, mae) in ATR units, or (nan, nan) if insufficient data."""
    if df_bars is None or atr <= 0:
        return np.nan, np.nan
    idx = df_bars.index.searchsorted(signal_ts)
    if idx >= len(df_bars):
        return np.nan, np.nan
    entry  = df_bars.iloc[idx]["close"]
    future = df_bars.iloc[idx + 1: idx + 1 + n_bars]
    if len(future) < min_bars:
        return np.nan, np.nan
    if direction == "bull":
        mfe = (future["high"].max() - entry) / atr
        mae = (entry - future["low"].min())  / atr
    else:
        mfe = (entry - future["low"].min())  / atr
        mae = (future["high"].max() - entry) / atr
    return float(max(0.0, mfe)), float(max(0.0, mae))


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    t0 = time.time()

    df = pd.read_parquet(CATALOG)

    # Convert start_time to tz-naive ET
    df["_ts_et"] = (
        pd.to_datetime(df["start_time"])
        .dt.tz_convert("US/Eastern")
        .dt.tz_localize(None)
    )
    df["_date"] = df["_ts_et"].dt.date

    # Add output columns if not present
    if "mfe_15sec" not in df.columns:
        df["mfe_15sec"] = np.nan
    if "mae_15sec" not in df.columns:
        df["mae_15sec"] = np.nan

    symbols = df["symbol"].dropna().unique()
    filled_1m = 0
    filled_15s = 0

    for sym in sorted(symbols):
        sym_mask = df["symbol"] == sym

        # ── 1m enrichment (fill missing mfe_1m) ──────────────────────────────
        needs_1m = sym_mask & df["mfe_1m"].isna()
        n_needs = needs_1m.sum()

        bars_1m = None
        if n_needs > 0:
            bars_1m = load_bars(CACHE_DIR / f"{sym.lower()}_1_min_ib.parquet")

        if bars_1m is not None and n_needs > 0:
            for idx in df.index[needs_1m]:
                row = df.loc[idx]
                mfe, mae = compute_fwd(
                    bars_1m, row["_ts_et"], row["direction"], row["atr"], FWD_1M
                )
                if not np.isnan(mfe):
                    df.at[idx, "mfe_1m"] = mfe
                    df.at[idx, "mae_1m"] = mae
                    filled_1m += 1

        # ── 15sec enrichment (all rows from HIGHRES_START) ───────────────────
        needs_15s = sym_mask & (df["_date"] >= HIGHRES_START)
        n_15s = needs_15s.sum()

        bars_15s = None
        if n_15s > 0:
            bars_15s = load_bars(HIGHRES_DIR / f"{sym.lower()}_15_secs_ib.parquet")

        if bars_15s is not None and n_15s > 0:
            for idx in df.index[needs_15s]:
                row = df.loc[idx]
                mfe, mae = compute_fwd(
                    bars_15s, row["_ts_et"], row["direction"], row["atr"], FWD_15SEC
                )
                if not np.isnan(mfe):
                    df.at[idx, "mfe_15sec"] = mfe
                    df.at[idx, "mae_15sec"] = mae
                    filled_15s += 1

        print(f"  {sym:6s}: 1m filled={needs_1m.sum() - df.loc[needs_1m, 'mfe_1m'].isna().sum()}"
              f"  15s filled={n_15s - df.loc[needs_15s, 'mfe_15sec'].isna().sum()}")

    # Drop helper columns
    df.drop(columns=["_ts_et", "_date"], inplace=True)

    # Save
    df.to_parquet(CATALOG, index=False)

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s")
    print(f"  mfe_1m filled: {filled_1m}")
    print(f"  mfe_15sec filled: {filled_15s}")

    # Summary of usable rows now
    primary = df[(df["pass"] == "primary") & (~df["symbol"].isin({"TSM"}))]
    has_1m  = primary["mfe_1m"].notna().sum()
    has_15s = primary["mfe_15sec"].notna().sum()
    print(f"\n  Primary rows with mfe_1m:    {has_1m:,}  (was 24,824)")
    print(f"  Primary rows with mfe_15sec: {has_15s:,}")


if __name__ == "__main__":
    main()
