#!/usr/bin/env python3
"""
Enrich move-catalog.parquet with daily VIX levels.

Fetches ^VIX daily closes via yfinance and joins to catalog by date.
Adds two columns:
  vix_close  — closing VIX value for that trading day
  vix_regime — categorical: low (<15) | normal (15-20) | elevated (20-28) | fear (>28)

Usage: python3 enrich_vix.py
"""

from pathlib import Path
from datetime import date, timedelta
import numpy as np
import pandas as pd
import yfinance as yf

CATALOG  = Path(__file__).parent / "move-catalog.parquet"
CACHE_DIR = Path(
    "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de"
    "/Meine Ablage/Claude/trading_bot/cache/bars"
)
# Native IB VIX cache (Mar 2025→now daily, Jan 2026→now 5m)
VIX_DAILY_CACHE = CACHE_DIR / "vix_1_day_ib.parquet"
VIX_5M_CACHE    = CACHE_DIR / "vix_5_mins_ib.parquet"


def vix_regime(v):
    if v < 15:   return "low"       # complacency — trending market
    if v < 20:   return "normal"    # baseline
    if v < 28:   return "elevated"  # caution
    return "fear"                   # buy zone per IncomeSharkts chart


def main():
    df = pd.read_parquet(CATALOG)

    d_min = pd.to_datetime(df["date"]).dt.date.min()
    d_max = pd.to_datetime(df["date"]).dt.date.max()

    # Fetch with 5-day buffer on each side for alignment
    fetch_start = d_min - timedelta(days=5)
    fetch_end   = d_max + timedelta(days=5)

    # ── Load from native IB cache where available, yfinance for the rest ──
    cache_series = pd.Series(dtype=float)
    if VIX_DAILY_CACHE.exists():
        c = pd.read_parquet(VIX_DAILY_CACHE)
        c["_date"] = pd.to_datetime(c["date"]).dt.tz_localize(None).dt.date
        cache_series = c.set_index("_date")["close"].sort_index()
        print(f"  Cache daily: {len(cache_series)} rows "
              f"({cache_series.index[0]} → {cache_series.index[-1]})")

    # yfinance fills anything before the cache starts (or all, if no cache)
    yf_end = fetch_end
    yf_start = fetch_start
    print(f"Fetching ^VIX {yf_start} → {yf_end} via yfinance ...")
    vix_yf = yf.download("^VIX", start=str(yf_start), end=str(yf_end),
                         auto_adjust=True, progress=False)

    if vix_yf.empty and cache_series.empty:
        print("ERROR: no VIX data from cache or yfinance.")
        return

    # Build unified series: yfinance base + cache overlay (cache wins for recent dates)
    vix_close = pd.Series(dtype=float)
    if not vix_yf.empty:
        yf_close = vix_yf["Close"].copy()
        if isinstance(yf_close, pd.DataFrame):
            yf_close = yf_close.iloc[:, 0]
        if hasattr(yf_close.index, "tz") and yf_close.index.tz is not None:
            yf_close.index = yf_close.index.tz_localize(None)
        yf_close.index = pd.to_datetime(yf_close.index).date
        vix_close = yf_close.sort_index()

    # Overlay cache (higher fidelity for recent dates)
    if not cache_series.empty:
        vix_close = vix_close.combine_first(cache_series)
    vix_close = vix_close.sort_index()

    print(f"  VIX rows fetched: {len(vix_close)}")
    print(f"  Range: {vix_close.index[0]} → {vix_close.index[-1]}")
    print(f"  Min={vix_close.min():.1f}  Max={vix_close.max():.1f}  Mean={vix_close.mean():.1f}")

    # Join to catalog
    cat_dates = pd.to_datetime(df["date"]).dt.date
    df["vix_close"]  = cat_dates.map(vix_close).astype(float)
    df["vix_regime"] = df["vix_close"].apply(
        lambda v: vix_regime(v) if not np.isnan(v) else None
    )

    filled = df["vix_close"].notna().sum()
    total  = len(df)
    print(f"\n  Filled: {filled:,} / {total:,} rows ({filled/total*100:.1f}%)")

    # Regime breakdown (primary pass only)
    primary = df[df["pass"] == "primary"]
    print(f"\n  Regime breakdown (primary rows = {len(primary):,}):")
    for regime in ["low", "normal", "elevated", "fear"]:
        n = (primary["vix_regime"] == regime).sum()
        pct = n / len(primary) * 100
        print(f"    {regime:10s}: {n:5,}  ({pct:.1f}%)")

    df.to_parquet(CATALOG, index=False)
    print(f"\nSaved enriched catalog → {CATALOG.name}")


if __name__ == "__main__":
    main()
