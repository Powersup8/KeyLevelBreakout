"""
No Signal Zone Tier Analysis — Identify significant moves we MISSED,
tier them by magnitude, compute indicator profiles, and compare to our
known signal edge.

Uses IB parquet (primary, ~12 months) with TV CSV fallback.
Output: debug/no-signal-zone-tiers.md
"""

import pandas as pd
import numpy as np
import re
import warnings
from datetime import time as dtime
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

# ---------------------------------------------------------------------------
# Paths & Config
# ---------------------------------------------------------------------------
BASE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView")
DEBUG = BASE / "debug"
ARCHIVE = DEBUG / "archive"
SIGNALS_PATH = DEBUG / "enriched-signals.csv"
PARQUET_DIR = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars")
REPORT_PATH = DEBUG / "no-signal-zone-tiers.md"

SYMBOLS = ["SPY", "AAPL", "AMD", "AMZN", "GLD", "GOOGL", "META", "MSFT", "NVDA", "QQQ", "SLV", "TSLA", "TSM"]
MARKET_OPEN = dtime(9, 30)
MARKET_CLOSE = dtime(16, 0)

# Move detection
MIN_ATR_MAG = 0.50
MIN_BARS = 3
REVERSAL_ATR = 0.75

# Signal match window
SIGNAL_WINDOW_MIN = 15  # +/- minutes

# ============================================================================
# Step 1: Load 1-minute candle data (parquet primary, TV CSV fallback)
# ============================================================================
def load_candle_data():
    """Load 1m candles. Prefer IB parquet, fall back to TV CSVs."""
    all_frames = []
    sources = {}

    for sym in SYMBOLS:
        pq_path = PARQUET_DIR / f"{sym.lower()}_1_min_ib.parquet"
        if pq_path.exists():
            try:
                df = pd.read_parquet(pq_path)
                df = df.rename(columns={"date": "time"})
                if "time" not in df.columns and df.index.name == "date":
                    df = df.reset_index().rename(columns={"date": "time"})
                elif "time" not in df.columns:
                    df = df.reset_index()
                    if "date" in df.columns:
                        df = df.rename(columns={"date": "time"})
                # Ensure tz-aware
                if df["time"].dt.tz is None:
                    df["time"] = df["time"].dt.tz_localize("US/Eastern")
                else:
                    df["time"] = df["time"].dt.tz_convert("US/Eastern")
                df["symbol"] = sym
                df["date"] = df["time"].dt.date
                t = df["time"].dt.time
                df = df[(t >= MARKET_OPEN) & (t < MARKET_CLOSE)]
                df = df[["symbol", "date", "time", "open", "high", "low", "close", "volume"]]
                all_frames.append(df)
                sources[sym] = f"parquet ({len(df):,} rows, {df['date'].nunique()} days)"
                continue
            except Exception as e:
                print(f"  {sym}: parquet failed ({e}), trying CSV...")

        # Fallback: TV CSVs
        csv_files = list(DEBUG.glob(f"BATS_{sym}, 1_*.csv")) + list(ARCHIVE.glob(f"BATS_{sym}, 1_*.csv"))
        if not csv_files:
            print(f"  {sym}: NO DATA")
            continue
        sym_frames = []
        for fpath in csv_files:
            try:
                raw = pd.read_csv(fpath)
            except Exception:
                continue
            raw = raw.rename(columns={raw.columns[0]: "time", raw.columns[1]: "open",
                                      raw.columns[2]: "high", raw.columns[3]: "low",
                                      raw.columns[4]: "close"})
            vol_col = next((c for c in raw.columns if c == "Volume"), None)
            if vol_col is None:
                vol_col = next((c for c in raw.columns if "volume" in c.lower() and "ma" not in c.lower()), None)
            if vol_col is None:
                continue
            raw = raw.rename(columns={vol_col: "volume"})
            raw["time"] = pd.to_datetime(raw["time"], utc=True).dt.tz_convert("US/Eastern")
            raw["symbol"] = sym
            raw["date"] = raw["time"].dt.date
            t = raw["time"].dt.time
            raw = raw[(t >= MARKET_OPEN) & (t < MARKET_CLOSE)]
            sym_frames.append(raw[["symbol", "date", "time", "open", "high", "low", "close", "volume"]])
        if sym_frames:
            df = pd.concat(sym_frames, ignore_index=True).drop_duplicates(subset=["time"], keep="first")
            all_frames.append(df)
            sources[sym] = f"CSV ({len(df):,} rows, {df['date'].nunique()} days)"

    candles = pd.concat(all_frames, ignore_index=True)
    candles = candles.drop_duplicates(subset=["symbol", "time"], keep="first")
    candles = candles.sort_values(["symbol", "time"]).reset_index(drop=True)

    print(f"\n=== Candle Data Loaded ===")
    print(f"Total: {len(candles):,} rows, {candles['symbol'].nunique()} symbols, "
          f"{candles['date'].min()} to {candles['date'].max()}")
    for sym in sorted(sources):
        print(f"  {sym}: {sources[sym]}")
    return candles


# ============================================================================
# Step 2: Resample to 5m + compute indicators
# ============================================================================
def resample_5m(candles_1m):
    """Resample 1m to 5m bars and compute ATR(14), EMA9/20/50, VWAP, ADX(14), vol SMA(20)."""
    results = []
    for (symbol, date), grp in candles_1m.groupby(["symbol", "date"]):
        grp = grp.sort_values("time").set_index("time")
        if len(grp) < 10:
            continue
        bars = grp.resample("5min").agg({
            "open": "first", "high": "max", "low": "min",
            "close": "last", "volume": "sum",
            "symbol": "first", "date": "first"
        }).dropna(subset=["open"])
        if len(bars) < 5:
            continue

        # ATR(14)
        bars["prev_close"] = bars["close"].shift(1)
        bars["tr"] = np.maximum(
            bars["high"] - bars["low"],
            np.maximum(
                (bars["high"] - bars["prev_close"]).abs(),
                (bars["low"] - bars["prev_close"]).abs()
            ))
        bars["tr"] = bars["tr"].fillna(bars["high"] - bars["low"])
        bars["atr14"] = bars["tr"].rolling(14, min_periods=1).mean()

        # EMAs
        bars["ema9"] = bars["close"].ewm(span=9, adjust=False).mean()
        bars["ema20"] = bars["close"].ewm(span=20, adjust=False).mean()
        bars["ema50"] = bars["close"].ewm(span=50, adjust=False).mean()

        # VWAP (intraday reset)
        bars["cum_vol"] = bars["volume"].cumsum()
        typical = (bars["high"] + bars["low"] + bars["close"]) / 3
        bars["cum_vp"] = (typical * bars["volume"]).cumsum()
        bars["vwap"] = bars["cum_vp"] / bars["cum_vol"].replace(0, np.nan)

        # Volume SMA(20)
        bars["vol_sma20"] = bars["volume"].rolling(20, min_periods=1).mean()

        # ADX(14) approximation
        bars["adx14"] = compute_adx(bars, period=14)

        bars = bars.reset_index()
        results.append(bars)

    bars_5m = pd.concat(results, ignore_index=True)
    print(f"Resampled to {len(bars_5m):,} 5m bars")
    return bars_5m


def compute_adx(df, period=14):
    """Simple ADX approximation on a DataFrame with high/low/close columns."""
    high = df["high"].values
    low = df["low"].values
    close = df["close"].values
    n = len(high)
    adx = np.full(n, np.nan)
    if n < period + 1:
        return adx

    # +DM / -DM
    plus_dm = np.zeros(n)
    minus_dm = np.zeros(n)
    tr = np.zeros(n)
    for i in range(1, n):
        up = high[i] - high[i-1]
        down = low[i-1] - low[i]
        plus_dm[i] = up if (up > down and up > 0) else 0
        minus_dm[i] = down if (down > up and down > 0) else 0
        tr[i] = max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1]))

    # Smoothed
    alpha = 1.0 / period
    sm_tr = np.zeros(n)
    sm_plus = np.zeros(n)
    sm_minus = np.zeros(n)
    sm_tr[period] = tr[1:period+1].sum()
    sm_plus[period] = plus_dm[1:period+1].sum()
    sm_minus[period] = minus_dm[1:period+1].sum()
    for i in range(period + 1, n):
        sm_tr[i] = sm_tr[i-1] - sm_tr[i-1] / period + tr[i]
        sm_plus[i] = sm_plus[i-1] - sm_plus[i-1] / period + plus_dm[i]
        sm_minus[i] = sm_minus[i-1] - sm_minus[i-1] / period + minus_dm[i]

    di_plus = np.where(sm_tr > 0, 100 * sm_plus / sm_tr, 0)
    di_minus = np.where(sm_tr > 0, 100 * sm_minus / sm_tr, 0)
    di_sum = di_plus + di_minus
    dx = np.where(di_sum > 0, 100 * np.abs(di_plus - di_minus) / di_sum, 0)

    # Smooth DX -> ADX
    adx_vals = np.full(n, np.nan)
    start = 2 * period
    if start < n:
        adx_vals[start] = dx[period+1:start+1].mean()
        for i in range(start + 1, n):
            adx_vals[i] = (adx_vals[i-1] * (period - 1) + dx[i]) / period

    return adx_vals


# ============================================================================
# Step 3: Detect significant moves (zig-zag same as midday_treasure_hunt.py)
# ============================================================================
def detect_moves(bars_5m):
    """Detect significant moves using zig-zag reversal detection on 5m bars."""
    all_moves = []
    for (symbol, date), grp in bars_5m.groupby(["symbol", "date"]):
        grp = grp.sort_values("time").reset_index(drop=True)
        n = len(grp)
        if n < 5:
            continue
        H = grp["high"].values
        L = grp["low"].values
        C = grp["close"].values
        T = list(grp["time"])
        ATR = grp["atr14"].values
        EMA9 = grp["ema9"].values
        EMA20 = grp["ema20"].values
        EMA50 = grp["ema50"].values
        VWAP = grp["vwap"].values
        VOL = grp["volume"].values
        VOLSMA = grp["vol_sma20"].values
        ADX = grp["adx14"].values

        def make_move(direction, si, ei):
            atr = ATR[si] if ATR[si] > 0 and not np.isnan(ATR[si]) else ATR[min(si + 1, n - 1)]
            if atr <= 0 or np.isnan(atr):
                return None
            if direction == "up":
                mag = (H[ei] - L[si]) / atr
                sp, ep = float(L[si]), float(H[ei])
            else:
                mag = (H[si] - L[ei]) / atr
                sp, ep = float(H[si]), float(L[ei])
            dur = ei - si
            if dur < MIN_BARS or mag < MIN_ATR_MAG:
                return None
            vr = VOL[si] / VOLSMA[si] if VOLSMA[si] > 0 else 0

            # EMA alignment at move start
            ema9_v = EMA9[si]; ema20_v = EMA20[si]; ema50_v = EMA50[si]
            if direction == "up":
                ema_aligned = (ema9_v > ema20_v > ema50_v)
            else:
                ema_aligned = (ema9_v < ema20_v < ema50_v)

            vwap_v = VWAP[si]
            if direction == "up":
                vwap_aligned = C[si] > vwap_v if not np.isnan(vwap_v) else False
            else:
                vwap_aligned = C[si] < vwap_v if not np.isnan(vwap_v) else False

            regime = int(ema_aligned) + int(vwap_aligned)

            adx_v = ADX[si] if not np.isnan(ADX[si]) else 0

            return {
                "symbol": symbol, "date": date,
                "start_time": T[si], "end_time": T[ei],
                "direction": "bull" if direction == "up" else "bear",
                "magnitude_atr": round(mag, 3),
                "duration_bars": dur,
                "start_price": round(sp, 4), "end_price": round(ep, 4),
                "atr": round(float(atr), 4),
                "vol_ratio": round(float(vr), 2),
                "ema_aligned": ema_aligned,
                "vwap_aligned": vwap_aligned,
                "regime_score": regime,
                "ema9": round(float(ema9_v), 4),
                "ema20": round(float(ema20_v), 4),
                "ema50": round(float(ema50_v), 4),
                "vwap": round(float(vwap_v), 4) if not np.isnan(vwap_v) else np.nan,
                "adx": round(float(adx_v), 1),
                "start_bar_idx": si,
            }

        # Zig-zag initialization
        direction = None
        move_si = 0
        run_hi = H[0]; run_hi_idx = 0
        run_lo = L[0]; run_lo_idx = 0

        if n >= 3:
            first3_hi = max(H[0], H[1], H[2])
            first3_lo = min(L[0], L[1], L[2])
            hi_idx = int(np.argmax(H[:3]))
            lo_idx = int(np.argmin(L[:3]))
            if lo_idx <= hi_idx:
                direction = "up"; move_si = lo_idx
                run_hi = first3_hi; run_hi_idx = hi_idx
                run_lo = L[lo_idx]; run_lo_idx = lo_idx
            else:
                direction = "down"; move_si = hi_idx
                run_lo = first3_lo; run_lo_idx = lo_idx
                run_hi = H[hi_idx]; run_hi_idx = hi_idx

        for i in range(3, n):
            atr = ATR[i] if ATR[i] > 0 and not np.isnan(ATR[i]) else ATR[max(0, i - 1)]
            if atr <= 0 or np.isnan(atr):
                continue
            if direction == "up":
                if H[i] > run_hi:
                    run_hi = H[i]; run_hi_idx = i
                pullback = run_hi - L[i]
                if pullback / atr >= REVERSAL_ATR:
                    mv = make_move("up", move_si, run_hi_idx)
                    if mv:
                        all_moves.append(mv)
                    direction = "down"; move_si = run_hi_idx
                    run_lo = L[i]; run_lo_idx = i; run_hi = H[run_hi_idx]
            elif direction == "down":
                if L[i] < run_lo:
                    run_lo = L[i]; run_lo_idx = i
                bounce = H[i] - run_lo
                if bounce / atr >= REVERSAL_ATR:
                    mv = make_move("down", move_si, run_lo_idx)
                    if mv:
                        all_moves.append(mv)
                    direction = "up"; move_si = run_lo_idx
                    run_hi = H[i]; run_hi_idx = i; run_lo = L[run_lo_idx]

        # Final move
        if direction == "up":
            mv = make_move("up", move_si, run_hi_idx)
            if mv:
                all_moves.append(mv)
        elif direction == "down":
            mv = make_move("down", move_si, run_lo_idx)
            if mv:
                all_moves.append(mv)

    moves_df = pd.DataFrame(all_moves)
    if len(moves_df) > 0:
        moves_df = moves_df.sort_values(["symbol", "date", "start_time"]).reset_index(drop=True)
    print(f"Found {len(moves_df):,} significant moves (≥{MIN_ATR_MAG} ATR, ≥{MIN_BARS} bars)")
    return moves_df


# ============================================================================
# Step 4: Cross-reference with existing signals to find "No Signal Zone" moves
# ============================================================================
def load_signals():
    """Load enriched signals CSV."""
    sigs = pd.read_csv(SIGNALS_PATH)
    # Parse date + time into datetime
    sigs["date_parsed"] = pd.to_datetime(sigs["date"]).dt.date
    sigs["datetime"] = pd.to_datetime(sigs["date"] + " " + sigs["time"])
    sigs["datetime"] = sigs["datetime"].dt.tz_localize("US/Eastern")
    print(f"Loaded {len(sigs):,} existing signals, {sigs['date_parsed'].min()} to {sigs['date_parsed'].max()}")
    return sigs


def classify_moves(moves_df, signals_df):
    """Mark moves as CAUGHT or MISSED based on signal proximity."""
    window = pd.Timedelta(minutes=SIGNAL_WINDOW_MIN)
    classifications = []

    for _, mv in moves_df.iterrows():
        sym = mv["symbol"]
        dt = mv["date"]
        st = mv["start_time"]
        d = mv["direction"]

        # Find signals for same symbol and date
        sig_mask = (signals_df["symbol"] == sym) & (signals_df["date_parsed"] == dt)
        sigs = signals_df[sig_mask]

        if len(sigs) == 0:
            classifications.append("MISSED")
            continue

        # Check if any signal is within ±15 min of move start and same direction
        matched = False
        for _, sig in sigs.iterrows():
            sig_dir = sig["direction"]
            if sig_dir != d:
                continue
            time_diff = abs((st - sig["datetime"]).total_seconds())
            if time_diff <= SIGNAL_WINDOW_MIN * 60:
                matched = True
                break

        classifications.append("CAUGHT" if matched else "MISSED")

    moves_df = moves_df.copy()
    moves_df["classification"] = classifications
    caught = (moves_df["classification"] == "CAUGHT").sum()
    missed = (moves_df["classification"] == "MISSED").sum()
    print(f"Classification: {caught:,} CAUGHT, {missed:,} MISSED")
    return moves_df


# ============================================================================
# Step 5: Compute time buckets and tier the moves
# ============================================================================
def add_time_bucket(df):
    """Add time bucket matching our signals CSV format: 9:30-10:00, 10:00-11:00, 11:00-12:00, 12:00+."""
    buckets = []
    fine_buckets = []
    for _, row in df.iterrows():
        t = row["start_time"]
        if hasattr(t, "time"):
            t = t.time()
        # Coarse buckets (match enriched-signals.csv)
        if t < dtime(10, 0):
            buckets.append("9:30-10:00")
        elif t < dtime(11, 0):
            buckets.append("10:00-11:00")
        elif t < dtime(12, 0):
            buckets.append("11:00-12:00")
        else:
            buckets.append("12:00+")
        # Fine buckets for deeper analysis
        if t < dtime(10, 0):
            fine_buckets.append("9:30-10:00")
        elif t < dtime(10, 30):
            fine_buckets.append("10:00-10:30")
        elif t < dtime(11, 0):
            fine_buckets.append("10:30-11:00")
        elif t < dtime(12, 0):
            fine_buckets.append("11:00-12:00")
        elif t < dtime(14, 0):
            fine_buckets.append("12:00-14:00")
        else:
            fine_buckets.append("14:00-16:00")
    df = df.copy()
    df["time_bucket"] = buckets
    df["time_bucket_fine"] = fine_buckets
    return df


def add_tiers(df):
    """Tier by magnitude: S >= 2.0, A 1.0-2.0, B 0.5-1.0."""
    tiers = []
    for mag in df["magnitude_atr"]:
        if mag >= 2.0:
            tiers.append("S")
        elif mag >= 1.0:
            tiers.append("A")
        else:
            tiers.append("B")
    df = df.copy()
    df["tier"] = tiers
    return df


# ============================================================================
# Step 6: Compute signal profiles for existing caught signals
# ============================================================================
def compute_caught_profiles(signals_df):
    """Compute indicator profiles for our existing signals (for comparison)."""
    sigs = signals_df.copy()

    # EMA alignment
    ema_aligned = (sigs["ema"].isin(["bull", "bear"])).mean()

    # VWAP alignment with direction
    vwap_aligned = 0
    for _, s in sigs.iterrows():
        if s["direction"] == "bull" and s["vwap"] == "above":
            vwap_aligned += 1
        elif s["direction"] == "bear" and s["vwap"] == "below":
            vwap_aligned += 1
    vwap_aligned /= max(len(sigs), 1)

    # Direction split
    bear_pct = (sigs["direction"] == "bear").mean()
    bull_pct = (sigs["direction"] == "bull").mean()

    # Time distribution
    time_dist = sigs["time_bucket"].value_counts(normalize=True).to_dict()

    # Volume distribution
    vol_dist = sigs["vol_bucket"].value_counts(normalize=True).to_dict()

    # ADX
    adx_mean = sigs["adx"].mean()

    # GOOD signals profile (CONF pass with good MFE)
    good = sigs[sigs["conf"].isin(["✓", "✓★"])]
    good_ema = (good["ema"].isin(["bull", "bear"])).mean() if len(good) > 0 else 0

    good_vwap = 0
    for _, s in good.iterrows():
        if s["direction"] == "bull" and s["vwap"] == "above":
            good_vwap += 1
        elif s["direction"] == "bear" and s["vwap"] == "below":
            good_vwap += 1
    good_vwap = good_vwap / max(len(good), 1)

    good_bear = (good["direction"] == "bear").mean() if len(good) > 0 else 0
    good_time = good["time_bucket"].value_counts(normalize=True).to_dict() if len(good) > 0 else {}
    good_adx = good["adx"].mean() if len(good) > 0 else 0

    return {
        "all": {
            "count": len(sigs),
            "ema_aligned": ema_aligned,
            "vwap_aligned": vwap_aligned,
            "bear_pct": bear_pct,
            "bull_pct": bull_pct,
            "time_dist": time_dist,
            "vol_dist": vol_dist,
            "adx_mean": adx_mean,
        },
        "good": {
            "count": len(good),
            "ema_aligned": good_ema,
            "vwap_aligned": good_vwap,
            "bear_pct": good_bear,
            "bull_pct": 1 - good_bear if len(good) > 0 else 0,
            "time_dist": good_time,
            "adx_mean": good_adx,
        }
    }


# ============================================================================
# Step 7: Write report
# ============================================================================
def write_report(missed_df, all_moves_df, signal_profiles, signals_df):
    """Write the comprehensive tier analysis report."""
    lines = []
    lines.append("# No Signal Zone — Tier Analysis")
    lines.append("")
    lines.append(f"**Generated:** 2026-03-05")
    lines.append(f"**Data:** IB parquet (primary) + TV CSV (fallback), {all_moves_df['date'].min()} to {all_moves_df['date'].max()}")
    lines.append(f"**Symbols:** {', '.join(sorted(all_moves_df['symbol'].unique()))}")
    lines.append("")

    # Overall summary
    total_moves = len(all_moves_df)
    caught = (all_moves_df["classification"] == "CAUGHT").sum()
    missed = (all_moves_df["classification"] == "MISSED").sum()
    total_missed_atr = missed_df["magnitude_atr"].sum()
    lines.append("## Overall Summary")
    lines.append("")
    lines.append(f"- **Total significant moves detected:** {total_moves:,}")
    lines.append(f"- **Caught (signal within ±{SIGNAL_WINDOW_MIN}min):** {caught:,} ({100*caught/total_moves:.1f}%)")
    lines.append(f"- **Missed (No Signal Zone):** {missed:,} ({100*missed/total_moves:.1f}%)")
    lines.append(f"- **Total missed ATR:** {total_missed_atr:.1f}")
    lines.append(f"- **Avg missed move magnitude:** {missed_df['magnitude_atr'].mean():.2f} ATR")
    lines.append("")

    # Date range coverage
    signal_dates = set(signals_df["date_parsed"].unique())
    move_dates = set(all_moves_df["date"].unique())
    overlap_dates = signal_dates & move_dates
    non_overlap = move_dates - signal_dates
    lines.append(f"- **Signal date range:** {signals_df['date_parsed'].min()} to {signals_df['date_parsed'].max()} ({len(signal_dates)} days)")
    lines.append(f"- **Move date range:** {all_moves_df['date'].min()} to {all_moves_df['date'].max()} ({len(move_dates)} days)")
    lines.append(f"- **Overlapping days:** {len(overlap_dates)}")
    lines.append(f"- **Days with moves but NO signals:** {len(non_overlap)} (these are all auto-MISSED)")
    lines.append("")

    # Filter missed_df to only overlapping dates for fair comparison
    missed_overlap = missed_df[missed_df["date"].isin(overlap_dates)]
    missed_non_overlap = missed_df[~missed_df["date"].isin(overlap_dates)]
    lines.append(f"### Fair Comparison (overlapping dates only)")
    lines.append(f"- **Missed moves on overlapping dates:** {len(missed_overlap):,} (fair comparison)")
    lines.append(f"- **Missed moves on non-overlap dates:** {len(missed_non_overlap):,} (no signals to compare)")
    lines.append("")
    lines.append("*All analysis below uses ONLY overlapping dates for fair comparison.*")
    lines.append("")

    # Use fair comparison set
    fair_missed = missed_overlap if len(missed_overlap) > 0 else missed_df

    # Tier breakdown
    lines.append("## Tier Breakdown")
    lines.append("")
    lines.append("| Tier | Criteria | Count | Total ATR | Avg Mag | Avg Duration |")
    lines.append("|------|----------|------:|----------:|--------:|-------------:|")
    for tier in ["S", "A", "B"]:
        t = fair_missed[fair_missed["tier"] == tier]
        if len(t) == 0:
            lines.append(f"| {tier} | {'≥2.0 ATR' if tier == 'S' else '1.0-2.0 ATR' if tier == 'A' else '0.5-1.0 ATR'} | 0 | 0 | 0 | 0 |")
            continue
        criteria = "≥2.0 ATR" if tier == "S" else "1.0-2.0 ATR" if tier == "A" else "0.5-1.0 ATR"
        lines.append(f"| {tier} | {criteria} | {len(t):,} | {t['magnitude_atr'].sum():.1f} | "
                     f"{t['magnitude_atr'].mean():.2f} | {t['duration_bars'].mean():.1f} bars |")
    lines.append("")

    # Per-tier indicator profiles
    lines.append("## Per-Tier Indicator Profiles")
    lines.append("")
    lines.append("| Metric | Tier S | Tier A | Tier B | Our Signals | Our GOOD |")
    lines.append("|--------|-------:|-------:|-------:|------------:|---------:|")

    sp = signal_profiles

    for metric_name, missed_fn, all_fn, good_fn in [
        ("EMA Aligned %",
         lambda d: 100 * d["ema_aligned"].mean() if len(d) > 0 else 0,
         lambda: 100 * sp["all"]["ema_aligned"],
         lambda: 100 * sp["good"]["ema_aligned"]),
        ("VWAP Aligned %",
         lambda d: 100 * d["vwap_aligned"].mean() if len(d) > 0 else 0,
         lambda: 100 * sp["all"]["vwap_aligned"],
         lambda: 100 * sp["good"]["vwap_aligned"]),
        ("Regime Score 2 %",
         lambda d: 100 * (d["regime_score"] == 2).mean() if len(d) > 0 else 0,
         lambda: "—",
         lambda: "—"),
        ("Regime Score 0 %",
         lambda d: 100 * (d["regime_score"] == 0).mean() if len(d) > 0 else 0,
         lambda: "—",
         lambda: "—"),
        ("Bear Direction %",
         lambda d: 100 * (d["direction"] == "bear").mean() if len(d) > 0 else 0,
         lambda: 100 * sp["all"]["bear_pct"],
         lambda: 100 * sp["good"]["bear_pct"]),
        ("Avg Vol Ratio",
         lambda d: d["vol_ratio"].mean() if len(d) > 0 else 0,
         lambda: "—",
         lambda: "—"),
        ("Avg ADX",
         lambda d: d["adx"].mean() if len(d) > 0 else 0,
         lambda: sp["all"]["adx_mean"],
         lambda: sp["good"]["adx_mean"]),
    ]:
        tier_s = fair_missed[fair_missed["tier"] == "S"]
        tier_a = fair_missed[fair_missed["tier"] == "A"]
        tier_b = fair_missed[fair_missed["tier"] == "B"]
        s_val = missed_fn(tier_s)
        a_val = missed_fn(tier_a)
        b_val = missed_fn(tier_b)
        all_val = all_fn()
        good_val = good_fn()

        def fmt(v):
            if isinstance(v, str):
                return v
            return f"{v:.1f}"

        lines.append(f"| {metric_name} | {fmt(s_val)} | {fmt(a_val)} | {fmt(b_val)} | {fmt(all_val)} | {fmt(good_val)} |")
    lines.append("")

    # Time distribution comparison (coarse buckets matching signals CSV)
    lines.append("## Time Distribution (Coarse — matches signal buckets)")
    lines.append("")
    lines.append("| Time Bucket | Missed S | Missed A | Missed B | Our Signals | Our GOOD |")
    lines.append("|-------------|:--------:|:--------:|:--------:|:-----------:|:--------:|")
    coarse_buckets = ["9:30-10:00", "10:00-11:00", "11:00-12:00", "12:00+"]
    for tb in coarse_buckets:
        tier_s = fair_missed[fair_missed["tier"] == "S"]
        tier_a = fair_missed[fair_missed["tier"] == "A"]
        tier_b = fair_missed[fair_missed["tier"] == "B"]
        s_pct = 100 * (tier_s["time_bucket"] == tb).mean() if len(tier_s) > 0 else 0
        a_pct = 100 * (tier_a["time_bucket"] == tb).mean() if len(tier_a) > 0 else 0
        b_pct = 100 * (tier_b["time_bucket"] == tb).mean() if len(tier_b) > 0 else 0
        all_pct = 100 * sp["all"]["time_dist"].get(tb, 0)
        good_pct = 100 * sp["good"]["time_dist"].get(tb, 0)
        lines.append(f"| {tb} | {s_pct:.0f}% | {a_pct:.0f}% | {b_pct:.0f}% | {all_pct:.0f}% | {good_pct:.0f}% |")
    lines.append("")

    # Fine time distribution
    lines.append("## Time Distribution (Fine — 30min buckets)")
    lines.append("")
    lines.append("| Time Bucket | Missed S | Missed A | Missed B | Missed All |")
    lines.append("|-------------|:--------:|:--------:|:--------:|:----------:|")
    fine_buckets = ["9:30-10:00", "10:00-10:30", "10:30-11:00", "11:00-12:00", "12:00-14:00", "14:00-16:00"]
    for tb in fine_buckets:
        tier_s = fair_missed[fair_missed["tier"] == "S"]
        tier_a = fair_missed[fair_missed["tier"] == "A"]
        tier_b = fair_missed[fair_missed["tier"] == "B"]
        s_pct = 100 * (tier_s["time_bucket_fine"] == tb).mean() if len(tier_s) > 0 else 0
        a_pct = 100 * (tier_a["time_bucket_fine"] == tb).mean() if len(tier_a) > 0 else 0
        b_pct = 100 * (tier_b["time_bucket_fine"] == tb).mean() if len(tier_b) > 0 else 0
        all_pct = 100 * (fair_missed["time_bucket_fine"] == tb).mean() if len(fair_missed) > 0 else 0
        lines.append(f"| {tb} | {s_pct:.0f}% | {a_pct:.0f}% | {b_pct:.0f}% | {all_pct:.0f}% |")
    lines.append("")

    # Symbol distribution for missed moves
    lines.append("## Symbol Distribution (Missed Moves)")
    lines.append("")
    lines.append("| Symbol | Tier S | Tier A | Tier B | Total Missed | Missed ATR |")
    lines.append("|--------|-------:|-------:|-------:|-------------:|-----------:|")
    for sym in sorted(fair_missed["symbol"].unique()):
        sym_d = fair_missed[fair_missed["symbol"] == sym]
        s_n = len(sym_d[sym_d["tier"] == "S"])
        a_n = len(sym_d[sym_d["tier"] == "A"])
        b_n = len(sym_d[sym_d["tier"] == "B"])
        total_atr = sym_d["magnitude_atr"].sum()
        lines.append(f"| {sym} | {s_n} | {a_n} | {b_n} | {len(sym_d)} | {total_atr:.1f} |")
    lines.append("")

    # "Catchable" analysis — moves matching our good signal profile
    lines.append("## Catchability Analysis")
    lines.append("")
    lines.append("Which missed moves match our KNOWN edge (EMA aligned + regime 2 + morning)?")
    lines.append("")

    # Define "catchable" = EMA aligned + regime 2 (VWAP + EMA both aligned)
    fair_missed_c = fair_missed.copy()
    fair_missed_c["morning"] = fair_missed_c["time_bucket"].isin(["9:30-10:00", "10:00-11:00"])
    fair_missed_c["match_ema"] = fair_missed_c["ema_aligned"]
    fair_missed_c["match_regime2"] = fair_missed_c["regime_score"] == 2
    fair_missed_c["match_morning"] = fair_missed_c["morning"]

    # Full match: EMA + regime 2 + morning
    full_match = fair_missed_c["match_ema"] & fair_missed_c["match_regime2"] & fair_missed_c["match_morning"]
    # Partial match: EMA + regime 2 (any time)
    partial_match = fair_missed_c["match_ema"] & fair_missed_c["match_regime2"]
    # EMA only
    ema_only = fair_missed_c["match_ema"]

    lines.append("| Match Level | Count | % of Missed | ATR Sum | Avg Mag |")
    lines.append("|-------------|------:|------------:|--------:|--------:|")
    for label, mask in [
        ("Full (EMA + Regime 2 + Morning)", full_match),
        ("Partial (EMA + Regime 2, any time)", partial_match),
        ("EMA Only", ema_only),
        ("No EMA (genuinely outside edge)", ~ema_only),
    ]:
        subset = fair_missed_c[mask]
        pct = 100 * len(subset) / max(len(fair_missed_c), 1)
        atr_sum = subset["magnitude_atr"].sum()
        avg_mag = subset["magnitude_atr"].mean() if len(subset) > 0 else 0
        lines.append(f"| {label} | {len(subset):,} | {pct:.1f}% | {atr_sum:.1f} | {avg_mag:.2f} |")
    lines.append("")

    # Per-tier catchability
    lines.append("### Per-Tier Catchability")
    lines.append("")
    lines.append("| Tier | Total | Full Match | % | EMA Gate Would Block |")
    lines.append("|------|------:|-----------:|--:|---------------------:|")
    for tier in ["S", "A", "B"]:
        t = fair_missed_c[fair_missed_c["tier"] == tier]
        fm = t[t["match_ema"] & t["match_regime2"] & t["match_morning"]]
        blocked = t[~t["match_ema"]]
        pct = 100 * len(fm) / max(len(t), 1)
        blocked_pct = 100 * len(blocked) / max(len(t), 1)
        lines.append(f"| {tier} | {len(t)} | {len(fm)} | {pct:.0f}% | {len(blocked)} ({blocked_pct:.0f}%) |")
    lines.append("")

    # EMA gate impact
    lines.append("## EMA Gate Impact")
    lines.append("")
    lines.append("Our v3.0 EMA gate filters out non-EMA signals. How many missed moves would it also block?")
    lines.append("")
    non_ema = fair_missed[~fair_missed["ema_aligned"]]
    ema_yes = fair_missed[fair_missed["ema_aligned"]]
    lines.append(f"- **EMA-aligned missed moves:** {len(ema_yes):,} ({100*len(ema_yes)/max(len(fair_missed),1):.1f}%) — {ema_yes['magnitude_atr'].sum():.1f} ATR")
    lines.append(f"- **Non-EMA missed moves:** {len(non_ema):,} ({100*len(non_ema)/max(len(fair_missed),1):.1f}%) — {non_ema['magnitude_atr'].sum():.1f} ATR")
    lines.append("")
    lines.append("If we expanded our indicator to catch EMA-aligned moves in the No Signal Zone,")
    lines.append(f"we'd target {len(ema_yes):,} moves worth {ema_yes['magnitude_atr'].sum():.1f} ATR.")
    lines.append(f"The {len(non_ema):,} non-EMA moves ({non_ema['magnitude_atr'].sum():.1f} ATR) are genuinely outside our edge.")
    lines.append("")

    # Top 20 missed Tier S moves
    lines.append("## Top 20 Missed Tier S Moves")
    lines.append("")
    if len(fair_missed[fair_missed["tier"] == "S"]) > 0:
        top_s = fair_missed[fair_missed["tier"] == "S"].nlargest(20, "magnitude_atr")
        lines.append("| # | Symbol | Date | Time | Dir | Mag | EMA | Regime | Vol | ADX |")
        lines.append("|---|--------|------|------|-----|----:|:---:|-------:|----:|----:|")
        for i, (_, row) in enumerate(top_s.iterrows(), 1):
            t = row["start_time"]
            if hasattr(t, "strftime"):
                tstr = t.strftime("%H:%M")
            else:
                tstr = str(t)
            lines.append(f"| {i} | {row['symbol']} | {row['date']} | {tstr} | {row['direction']} | "
                         f"{row['magnitude_atr']:.2f} | {'Y' if row['ema_aligned'] else 'N'} | "
                         f"{row['regime_score']} | {row['vol_ratio']:.1f}x | {row['adx']:.0f} |")
        lines.append("")
    else:
        lines.append("*No Tier S missed moves found on overlapping dates.*")
        lines.append("")

    # Top 20 missed Tier S overall (including non-overlap days)
    if len(missed_non_overlap) > 0 and len(missed_df[missed_df["tier"] == "S"]) > len(fair_missed[fair_missed["tier"] == "S"]):
        all_s = missed_df[missed_df["tier"] == "S"].nlargest(20, "magnitude_atr")
        lines.append("## Top 20 Missed Tier S Moves (ALL dates)")
        lines.append("")
        lines.append("| # | Symbol | Date | Time | Dir | Mag | EMA | Regime | Vol | ADX |")
        lines.append("|---|--------|------|------|-----|----:|:---:|-------:|----:|----:|")
        for i, (_, row) in enumerate(all_s.iterrows(), 1):
            t = row["start_time"]
            if hasattr(t, "strftime"):
                tstr = t.strftime("%H:%M")
            else:
                tstr = str(t)
            lines.append(f"| {i} | {row['symbol']} | {row['date']} | {tstr} | {row['direction']} | "
                         f"{row['magnitude_atr']:.2f} | {'Y' if row['ema_aligned'] else 'N'} | "
                         f"{row['regime_score']} | {row['vol_ratio']:.1f}x | {row['adx']:.0f} |")
        lines.append("")

    # Conclusion
    lines.append("## Conclusions")
    lines.append("")

    total_missed_atr_fair = fair_missed["magnitude_atr"].sum()
    catchable_atr = fair_missed_c[partial_match]["magnitude_atr"].sum()
    outside_atr = fair_missed_c[~ema_only]["magnitude_atr"].sum()
    ema_only_atr = fair_missed_c[ema_only & ~partial_match]["magnitude_atr"].sum()

    lines.append(f"### ATR Budget (overlapping dates)")
    lines.append(f"- **Total missed:** {total_missed_atr_fair:.1f} ATR across {len(fair_missed):,} moves")
    lines.append(f"- **Catchable (EMA + Regime 2):** {catchable_atr:.1f} ATR ({100*catchable_atr/max(total_missed_atr_fair,0.01):.0f}%)")
    lines.append(f"- **EMA-only (partial edge):** {ema_only_atr:.1f} ATR ({100*ema_only_atr/max(total_missed_atr_fair,0.01):.0f}%)")
    lines.append(f"- **Outside our edge (no EMA):** {outside_atr:.1f} ATR ({100*outside_atr/max(total_missed_atr_fair,0.01):.0f}%)")
    lines.append("")

    # Morning vs afternoon split for missed
    morning_missed = fair_missed[fair_missed["time_bucket"].isin(["9:30-10:00", "10:00-11:00"])]
    afternoon_missed = fair_missed[~fair_missed["time_bucket"].isin(["9:30-10:00", "10:00-11:00"])]
    lines.append(f"### Time Split")
    lines.append(f"- **Morning missed (before 11:00):** {len(morning_missed):,} moves, {morning_missed['magnitude_atr'].sum():.1f} ATR")
    lines.append(f"- **Afternoon missed (after 11:00):** {len(afternoon_missed):,} moves, {afternoon_missed['magnitude_atr'].sum():.1f} ATR")
    lines.append("")

    # Key takeaways
    ema_rate = 100 * fair_missed["ema_aligned"].mean() if len(fair_missed) > 0 else 0
    regime2_rate = 100 * (fair_missed["regime_score"] == 2).mean() if len(fair_missed) > 0 else 0
    bear_rate = 100 * (fair_missed["direction"] == "bear").mean() if len(fair_missed) > 0 else 0

    lines.append("### Key Takeaways")
    lines.append("")
    lines.append(f"1. **EMA alignment:** {ema_rate:.0f}% of missed moves are EMA-aligned "
                 f"(vs {100*sp['all']['ema_aligned']:.0f}% of our signals, {100*sp['good']['ema_aligned']:.0f}% of GOOD)")
    lines.append(f"2. **Regime score 2:** {regime2_rate:.0f}% of missed moves have full regime alignment")
    lines.append(f"3. **Direction:** {bear_rate:.0f}% bear (vs {100*sp['all']['bear_pct']:.0f}% of our signals)")

    # Determine if afternoon is dominated
    aft_ema = afternoon_missed["ema_aligned"].mean() if len(afternoon_missed) > 0 else 0
    morn_ema = morning_missed["ema_aligned"].mean() if len(morning_missed) > 0 else 0
    lines.append(f"4. **Morning EMA rate:** {100*morn_ema:.0f}% vs **Afternoon EMA rate:** {100*aft_ema:.0f}%")

    tier_s = fair_missed[fair_missed["tier"] == "S"]
    if len(tier_s) > 0:
        s_ema = 100 * tier_s["ema_aligned"].mean()
        s_regime = 100 * (tier_s["regime_score"] == 2).mean()
        lines.append(f"5. **Tier S home runs:** {len(tier_s)} moves, {s_ema:.0f}% EMA aligned, {s_regime:.0f}% regime 2")
    lines.append("")

    report = "\n".join(lines)
    REPORT_PATH.write_text(report)
    print(f"\nReport written to {REPORT_PATH}")
    return report


# ============================================================================
# Main
# ============================================================================
def main():
    print("=" * 70)
    print("No Signal Zone — Tier Analysis")
    print("=" * 70)

    # Step 1: Load candle data
    print("\n--- Step 1: Loading candle data ---")
    candles = load_candle_data()

    # Step 2: Resample to 5m + indicators
    print("\n--- Step 2: Resampling to 5m + computing indicators ---")
    bars_5m = resample_5m(candles)

    # Step 3: Detect moves
    print("\n--- Step 3: Detecting significant moves ---")
    moves = detect_moves(bars_5m)
    if len(moves) == 0:
        print("ERROR: No moves detected!")
        return

    # Step 4: Load signals + classify
    print("\n--- Step 4: Loading signals + classifying moves ---")
    signals = load_signals()
    moves = classify_moves(moves, signals)

    # Step 5: Add time buckets + tiers
    print("\n--- Step 5: Adding time buckets + tiers ---")
    moves = add_time_bucket(moves)
    moves = add_tiers(moves)

    missed = moves[moves["classification"] == "MISSED"].copy()
    print(f"\nMissed moves by tier:")
    for tier in ["S", "A", "B"]:
        t = missed[missed["tier"] == tier]
        print(f"  Tier {tier}: {len(t):,} moves, {t['magnitude_atr'].sum():.1f} ATR total")

    # Step 6: Compute signal profiles
    print("\n--- Step 6: Computing signal profiles ---")
    signal_profiles = compute_caught_profiles(signals)
    print(f"  All signals: {signal_profiles['all']['count']}, EMA aligned: {100*signal_profiles['all']['ema_aligned']:.1f}%")
    print(f"  GOOD signals: {signal_profiles['good']['count']}, EMA aligned: {100*signal_profiles['good']['ema_aligned']:.1f}%")

    # Step 7: Write report
    print("\n--- Step 7: Writing report ---")
    write_report(missed, moves, signal_profiles, signals)

    # Also save moves to CSV for further analysis
    csv_path = DEBUG / "no-signal-zone-moves.csv"
    moves.to_csv(csv_path, index=False)
    print(f"Moves saved to {csv_path}")

    print("\nDone!")


if __name__ == "__main__":
    main()
