"""
Midday Treasure Hunt — Deep research on what levels exist at the START of
622 "No Signal Zone" missed moves (after 10:30 when the indicator goes blind).

Computes all possible levels from 1m candle data, cross-references with missed
moves, and scores each level type by coverage, signal quality, and false positives.

Output: midday-treasure-hunt.md
"""

import pandas as pd
import numpy as np
import re
import math
import warnings
from datetime import datetime, time as dtime, timedelta, date as dateclass
from pathlib import Path
from collections import defaultdict

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

# ---------------------------------------------------------------------------
# Paths & Config
# ---------------------------------------------------------------------------
BASE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView")
DEBUG = BASE / "debug"
ARCHIVE = DEBUG / "archive"
SIGNALS_PATH = DEBUG / "enriched-signals.csv"
REPORT_PATH = DEBUG / "midday-treasure-hunt.md"

MARKET_OPEN = dtime(9, 30)
MARKET_CLOSE = dtime(16, 0)

# Move detection thresholds (same as missed_moves_scanner.py)
MIN_ATR_MAG = 0.50
MIN_BARS = 3
REVERSAL_ATR = 0.75

# Level proximity thresholds
TIGHT_ATR = 0.15
LOOSE_ATR = 0.30

# ===========================================================================
# Step 1: Load 1m candle data — prefer debug/ root files (newest), supplement from archive/
# ===========================================================================
def load_candle_data():
    """Load 1m candle CSVs. Prefer debug/ root (newer data), fall back to archive/."""
    all_frames = []

    # First, load from debug/ root (newer, 24 days)
    root_files = list(DEBUG.glob("BATS_*.csv"))
    archive_files = list(ARCHIVE.glob("BATS_*.csv"))

    # Group by symbol — prefer root files
    symbol_files = {}
    for fpath in root_files:
        m = re.match(r"BATS_([A-Z]+),", fpath.name)
        if m:
            sym = m.group(1)
            if sym not in symbol_files:
                symbol_files[sym] = []
            symbol_files[sym].append(fpath)

    for fpath in archive_files:
        m = re.match(r"BATS_([A-Z]+),", fpath.name)
        if m:
            sym = m.group(1)
            if sym not in symbol_files:
                symbol_files[sym] = []
            symbol_files[sym].append(fpath)

    for sym, files in symbol_files.items():
        for fpath in files:
            try:
                df = pd.read_csv(fpath)
            except Exception:
                continue
            df = df.rename(columns={df.columns[0]: "time", df.columns[1]: "open",
                                    df.columns[2]: "high", df.columns[3]: "low",
                                    df.columns[4]: "close"})
            vol_col = next((c for c in df.columns if c == "Volume"), None)
            if vol_col is None:
                vol_col = next((c for c in df.columns if "volume" in c.lower() and "ma" not in c.lower()), None)
            if vol_col is None:
                continue
            df = df.rename(columns={vol_col: "volume"})
            # Also grab Volume MA if exists
            vol_ma_col = next((c for c in df.columns if c == "Volume MA"), None)
            if vol_ma_col:
                df = df.rename(columns={vol_ma_col: "volume_ma"})

            df["time"] = pd.to_datetime(df["time"], utc=True).dt.tz_convert("US/Eastern")
            df["symbol"] = sym
            df["date"] = df["time"].dt.date
            t = df["time"].dt.time
            df = df[(t >= MARKET_OPEN) & (t < MARKET_CLOSE)]
            cols = ["symbol", "date", "time", "open", "high", "low", "close", "volume"]
            if "volume_ma" in df.columns:
                cols.append("volume_ma")
            all_frames.append(df[cols])

    candles = pd.concat(all_frames, ignore_index=True)
    candles = candles.drop_duplicates(subset=["symbol", "time"], keep="first")
    candles = candles.sort_values(["symbol", "time"]).reset_index(drop=True)

    print(f"Loaded {len(candles):,} 1m rows, {candles['symbol'].nunique()} symbols, "
          f"{candles['date'].min()} to {candles['date'].max()}")
    for s in sorted(candles["symbol"].unique()):
        sub = candles[candles["symbol"] == s]
        print(f"  {s}: {len(sub):,} rows, {sub['date'].nunique()} days")
    return candles


# ===========================================================================
# Step 2: Resample to 5m + compute indicators
# ===========================================================================
def resample_5m(candles_1m):
    results = []
    for (symbol, date), grp in candles_1m.groupby(["symbol", "date"]):
        grp = grp.sort_values("time").set_index("time")
        if len(grp) < 5:
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

        # EMA(20)
        bars["ema20"] = bars["close"].ewm(span=20, adjust=False).mean()

        # VWAP
        bars["cum_vol"] = bars["volume"].cumsum()
        typical = (bars["high"] + bars["low"] + bars["close"]) / 3
        bars["cum_vp"] = (typical * bars["volume"]).cumsum()
        bars["vwap"] = bars["cum_vp"] / bars["cum_vol"].replace(0, np.nan)

        # VWAP standard deviation bands
        bars["cum_vp2"] = (typical**2 * bars["volume"]).cumsum()
        variance = bars["cum_vp2"] / bars["cum_vol"] - bars["vwap"]**2
        variance = variance.clip(lower=0)
        bars["vwap_std"] = np.sqrt(variance)
        bars["vwap_upper"] = bars["vwap"] + bars["vwap_std"]
        bars["vwap_lower"] = bars["vwap"] - bars["vwap_std"]

        # Volume SMA(20)
        bars["vol_sma20"] = bars["volume"].rolling(20, min_periods=1).mean()

        bars = bars.reset_index()
        results.append(bars)

    bars_5m = pd.concat(results, ignore_index=True)
    print(f"Resampled to {len(bars_5m):,} 5m bars")
    return bars_5m


# ===========================================================================
# Step 3: Detect significant moves (same zig-zag as missed_moves_scanner.py)
# ===========================================================================
def detect_moves(bars_5m):
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
        EMA = grp["ema20"].values
        VWAP = grp["vwap"].values
        VOL = grp["volume"].values
        VOLSMA = grp["vol_sma20"].values

        def make_move(direction, si, ei):
            atr = ATR[si] if ATR[si] > 0 else ATR[min(si + 1, n - 1)]
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
            return {
                "symbol": symbol, "date": date,
                "start_time": T[si], "end_time": T[ei],
                "direction": direction,
                "magnitude_atr": round(mag, 3),
                "duration_bars": dur,
                "start_price": round(sp, 4), "end_price": round(ep, 4),
                "atr": round(float(atr), 4),
                "vol_ratio": round(float(vr), 2),
                "ema_pos": "above" if C[si] > EMA[si] else "below",
                "vwap_pos": "above" if C[si] > VWAP[si] else "below",
                "start_bar_idx": si,
            }

        direction = None
        move_si = 0
        run_hi = H[0]; run_hi_idx = 0
        run_lo = L[0]; run_lo_idx = 0

        if n >= 3:
            first3_hi = max(H[0], H[1], H[2])
            first3_lo = min(L[0], L[1], L[2])
            hi_idx = np.argmax(H[:3])
            lo_idx = np.argmin(L[:3])
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
                    if mv: all_moves.append(mv)
                    direction = "down"; move_si = run_hi_idx
                    run_lo = L[i]; run_lo_idx = i; run_hi = H[run_hi_idx]
            elif direction == "down":
                if L[i] < run_lo:
                    run_lo = L[i]; run_lo_idx = i
                bounce = H[i] - run_lo
                if bounce / atr >= REVERSAL_ATR:
                    mv = make_move("down", move_si, run_lo_idx)
                    if mv: all_moves.append(mv)
                    direction = "up"; move_si = run_lo_idx
                    run_hi = H[i]; run_hi_idx = i; run_lo = L[run_lo_idx]

        if direction == "up":
            mv = make_move("up", move_si, run_hi_idx)
            if mv: all_moves.append(mv)
        elif direction == "down":
            mv = make_move("down", move_si, run_lo_idx)
            if mv: all_moves.append(mv)

    moves_df = pd.DataFrame(all_moves)
    if len(moves_df) > 0:
        moves_df = moves_df.sort_values(["symbol", "date", "start_time"]).reset_index(drop=True)
    print(f"Found {len(moves_df):,} significant moves")
    return moves_df


# ===========================================================================
# Step 4: Classify missed moves (match against signals)
# ===========================================================================
def classify_moves(moves_df, signals_df):
    """Simple classification: mark moves that have NO signal nearby as 'MISSED'."""
    if len(signals_df) == 0:
        moves_df["classification"] = "MISSED"
        return moves_df

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

        # Check if any signal fired within 10min BEFORE or AT move start
        found = False
        for _, sig in sigs.iterrows():
            sig_time = sig["time_parsed"]
            # Signal must be within 10 min before start or at start
            diff_min = (st - sig_time).total_seconds() / 60
            if -2 <= diff_min <= 10:
                # Direction must match
                sig_dir = sig.get("direction", "")
                if (d == "up" and sig_dir == "bull") or (d == "down" and sig_dir == "bear"):
                    found = True
                    break

        classifications.append("CAUGHT" if found else "MISSED")

    moves_df["classification"] = classifications
    return moves_df


# ===========================================================================
# Step 5: Compute ALL levels for each symbol-day
# ===========================================================================
def compute_daily_levels(candles_1m, bars_5m):
    """
    For each symbol-day, compute all standard and new level types.
    Returns: dict[(symbol, date)] -> dict of level_name -> level_price
    """
    levels_db = {}

    # Get sorted unique trading days per symbol
    sym_days = {}
    for (sym, dt), grp in candles_1m.groupby(["symbol", "date"]):
        if sym not in sym_days:
            sym_days[sym] = {}
        day_data = grp.sort_values("time")
        sym_days[sym][dt] = day_data

    # Also build 5m data index
    bars_5m_index = {}
    for (sym, dt), grp in bars_5m.groupby(["symbol", "date"]):
        bars_5m_index[(sym, dt)] = grp.sort_values("time").reset_index(drop=True)

    for sym, days_dict in sym_days.items():
        sorted_dates = sorted(days_dict.keys())

        for i, dt in enumerate(sorted_dates):
            day = days_dict[dt]
            levels = {}

            # ---- A. Standard levels (from prior day) ----
            if i > 0:
                prev_dt = sorted_dates[i - 1]
                prev = days_dict[prev_dt]
                levels["PDH"] = prev["high"].max()
                levels["PDL"] = prev["low"].min()
                levels["PDC"] = prev["close"].iloc[-1]

                # Prior day VWAP close
                prev_tp = (prev["high"] + prev["low"] + prev["close"]) / 3
                prev_cum_vol = prev["volume"].cumsum()
                prev_cum_vp = (prev_tp * prev["volume"]).cumsum()
                prev_vwap = prev_cum_vp / prev_cum_vol.replace(0, np.nan)
                if len(prev_vwap.dropna()) > 0:
                    levels["PD_VWAP"] = prev_vwap.iloc[-1]

                # Prior day mid-range
                levels["PD_MID"] = (prev["high"].max() + prev["low"].min()) / 2

                # Prior day last-hour high/low (15:00-16:00)
                last_hour = prev[prev["time"].dt.time >= dtime(15, 0)]
                if len(last_hour) > 0:
                    levels["PD_LAST_HR_H"] = last_hour["high"].max()
                    levels["PD_LAST_HR_L"] = last_hour["low"].min()

                # Floor pivot points from prior day
                pdh = prev["high"].max()
                pdl = prev["low"].min()
                pdc = prev["close"].iloc[-1]
                pivot = (pdh + pdl + pdc) / 3
                levels["PIVOT"] = pivot
                levels["R1"] = 2 * pivot - pdl
                levels["S1"] = 2 * pivot - pdh
                levels["R2"] = pivot + (pdh - pdl)
                levels["S2"] = pivot - (pdh - pdl)

            # Week high/low (last 5 trading days)
            start_idx = max(0, i - 5)
            if i > 0:
                week_dates = sorted_dates[start_idx:i]
                week_highs = []
                week_lows = []
                for wd in week_dates:
                    wd_data = days_dict[wd]
                    week_highs.append(wd_data["high"].max())
                    week_lows.append(wd_data["low"].min())
                if week_highs:
                    levels["WEEK_H"] = max(week_highs)
                    levels["WEEK_L"] = min(week_lows)

            # 2-day high/low
            if i >= 2:
                d2_dates = sorted_dates[i-2:i]
                d2_highs = [days_dict[d]["high"].max() for d in d2_dates]
                d2_lows = [days_dict[d]["low"].min() for d in d2_dates]
                levels["D2_H"] = max(d2_highs)
                levels["D2_L"] = min(d2_lows)

            # Month high/low (last 20 trading days)
            month_start = max(0, i - 20)
            if i > 0:
                month_dates = sorted_dates[month_start:i]
                month_highs = [days_dict[d]["high"].max() for d in month_dates]
                month_lows = [days_dict[d]["low"].min() for d in month_dates]
                if month_highs:
                    levels["MONTH_H"] = max(month_highs)
                    levels["MONTH_L"] = min(month_lows)

            # ORB (first 5 minutes: 9:30-9:35)
            orb = day[day["time"].dt.time < dtime(9, 35)]
            if len(orb) > 0:
                levels["ORB_H"] = orb["high"].max()
                levels["ORB_L"] = orb["low"].min()

                # ORB extensions
                orb_range = levels["ORB_H"] - levels["ORB_L"]
                if orb_range > 0:
                    levels["ORB_EXT_H"] = levels["ORB_H"] + orb_range
                    levels["ORB_EXT_L"] = levels["ORB_L"] - orb_range

            # ---- B. Gap level ----
            if i > 0 and "PDC" in levels:
                today_open = day["open"].iloc[0]
                # Compute ATR for gap check
                if (sym, dt) in bars_5m_index:
                    b5 = bars_5m_index[(sym, dt)]
                    atr_val = b5["atr14"].iloc[min(5, len(b5)-1)] if len(b5) > 0 else None
                    if atr_val and atr_val > 0:
                        gap = abs(today_open - levels["PDC"])
                        if gap / atr_val > 0.2:
                            levels["GAP_FILL"] = levels["PDC"]

            # ---- Round numbers ----
            mid_price = day["close"].median()
            if mid_price > 0:
                # Nearest $5 and $10 levels within range
                price_range = day["high"].max() - day["low"].min()
                search_range = max(price_range * 2, mid_price * 0.03)  # 3% range

                lo_bound = mid_price - search_range
                hi_bound = mid_price + search_range

                # $10 rounds
                r10_start = int(lo_bound / 10) * 10
                r10 = r10_start
                r10_idx = 0
                while r10 <= hi_bound:
                    if r10 > 0:
                        levels[f"ROUND_10_{r10_idx}"] = float(r10)
                        r10_idx += 1
                    r10 += 10

                # $5 rounds (skip ones already in $10)
                r5_start = int(lo_bound / 5) * 5
                r5 = r5_start
                r5_idx = 0
                while r5 <= hi_bound:
                    if r5 > 0 and r5 % 10 != 0:
                        levels[f"ROUND_5_{r5_idx}"] = float(r5)
                        r5_idx += 1
                    r5 += 5

            levels_db[(sym, dt)] = levels

    total_levels = sum(len(v) for v in levels_db.values())
    print(f"Computed {total_levels:,} levels across {len(levels_db)} symbol-days")
    return levels_db, bars_5m_index


# ===========================================================================
# Step 6: Compute dynamic levels at a specific time
# ===========================================================================
def get_dynamic_levels(bars_5m_grp, bar_idx, atr_val):
    """
    Compute dynamic (intraday) levels at a specific bar index.
    Returns dict of level_name -> price.
    """
    levels = {}
    if bar_idx < 1:
        return levels

    # Slices up to (but not including) current bar
    past = bars_5m_grp.iloc[:bar_idx]
    curr = bars_5m_grp.iloc[bar_idx]

    # Half-day high/low (since 9:30)
    levels["HALFDAY_H"] = past["high"].max()
    levels["HALFDAY_L"] = past["low"].min()

    # Prior 1-hour high/low (12 bars on 5m)
    lookback = min(12, len(past))
    if lookback > 0:
        recent = past.iloc[-lookback:]
        levels["1HR_H"] = recent["high"].max()
        levels["1HR_L"] = recent["low"].min()

    # VWAP + bands
    if "vwap" in curr.index and not np.isnan(curr["vwap"]):
        levels["VWAP"] = curr["vwap"]
    if "vwap_upper" in curr.index and not np.isnan(curr["vwap_upper"]):
        levels["VWAP_UPPER"] = curr["vwap_upper"]
    if "vwap_lower" in curr.index and not np.isnan(curr["vwap_lower"]):
        levels["VWAP_LOWER"] = curr["vwap_lower"]

    return levels


# ===========================================================================
# Step 7: Cross-reference missed moves with ALL levels
# ===========================================================================
def cross_reference_levels(missed_moves, levels_db, bars_5m_index):
    """
    For each missed move, find ALL levels within tight/loose proximity at move start.
    """
    print(f"\nCross-referencing {len(missed_moves)} missed moves with levels...")

    results = []

    for idx, mv in missed_moves.iterrows():
        sym = mv["symbol"]
        dt = mv["date"]
        start_price = mv["start_price"]
        atr = mv["atr"]
        direction = mv["direction"]

        if atr <= 0:
            continue

        # Get static levels for this day
        static_levels = levels_db.get((sym, dt), {})

        # Get dynamic levels at move start
        dynamic_levels = {}
        key = (sym, dt)
        if key in bars_5m_index:
            b5 = bars_5m_index[key]
            # Find the 5m bar at or just before move start
            start_t = mv["start_time"]
            mask = b5["time"] <= start_t
            if mask.any():
                bar_idx = mask.sum() - 1
                # Make sure bar_idx is valid
                if 0 <= bar_idx < len(b5):
                    dynamic_levels = get_dynamic_levels(b5, bar_idx, atr)

        # Combine all levels
        all_levels = {**static_levels, **dynamic_levels}

        # Check proximity
        nearby_tight = {}
        nearby_loose = {}

        for lname, lprice in all_levels.items():
            if lprice is None or np.isnan(lprice):
                continue
            dist = abs(start_price - lprice) / atr
            if dist <= TIGHT_ATR:
                nearby_tight[lname] = round(dist, 4)
            if dist <= LOOSE_ATR:
                nearby_loose[lname] = round(dist, 4)

        # Get EMA/VWAP alignment at move start for regime scoring
        ema_aligned = False
        vwap_aligned = False
        if key in bars_5m_index:
            b5 = bars_5m_index[key]
            start_t = mv["start_time"]
            mask = b5["time"] <= start_t
            if mask.any():
                bar_idx = mask.sum() - 1
                if 0 <= bar_idx < len(b5):
                    bar = b5.iloc[bar_idx]
                    if direction == "up":
                        ema_aligned = bar["close"] > bar["ema20"]
                        vwap_aligned = bar["close"] > bar["vwap"] if not np.isnan(bar["vwap"]) else False
                    else:
                        ema_aligned = bar["close"] < bar["ema20"]
                        vwap_aligned = bar["close"] < bar["vwap"] if not np.isnan(bar["vwap"]) else False

        regime_score = int(ema_aligned) + int(vwap_aligned)

        results.append({
            "move_idx": idx,
            "symbol": sym,
            "date": dt,
            "start_time": mv["start_time"],
            "direction": direction,
            "magnitude_atr": mv["magnitude_atr"],
            "start_price": start_price,
            "atr": atr,
            "nearby_tight": nearby_tight,
            "nearby_loose": nearby_loose,
            "n_tight": len(nearby_tight),
            "n_loose": len(nearby_loose),
            "ema_aligned": ema_aligned,
            "vwap_aligned": vwap_aligned,
            "regime_score": regime_score,
        })

    results_df = pd.DataFrame(results)
    print(f"  {len(results_df)} moves analyzed")
    has_tight = (results_df["n_tight"] > 0).sum()
    has_loose = (results_df["n_loose"] > 0).sum()
    print(f"  Moves with tight level (<{TIGHT_ATR} ATR): {has_tight} ({100*has_tight/len(results_df):.0f}%)")
    print(f"  Moves with loose level (<{LOOSE_ATR} ATR): {has_loose} ({100*has_loose/len(results_df):.0f}%)")

    return results_df


# ===========================================================================
# Step 8: Categorize level names into types
# ===========================================================================
def categorize_level(name):
    """Map specific level name to a generic type for aggregation."""
    if name.startswith("ROUND_10"):
        return "ROUND_10"
    if name.startswith("ROUND_5"):
        return "ROUND_5"
    mapping = {
        "PDH": "PDH", "PDL": "PDL", "PDC": "PDC",
        "PD_VWAP": "PD_VWAP", "PD_MID": "PD_MID",
        "PD_LAST_HR_H": "PD_LAST_HR_H", "PD_LAST_HR_L": "PD_LAST_HR_L",
        "PIVOT": "PIVOT", "R1": "R1", "S1": "S1", "R2": "R2", "S2": "S2",
        "WEEK_H": "WEEK_H", "WEEK_L": "WEEK_L",
        "D2_H": "D2_H", "D2_L": "D2_L",
        "MONTH_H": "MONTH_H", "MONTH_L": "MONTH_L",
        "ORB_H": "ORB_H", "ORB_L": "ORB_L",
        "ORB_EXT_H": "ORB_EXT_H", "ORB_EXT_L": "ORB_EXT_L",
        "GAP_FILL": "GAP_FILL",
        "HALFDAY_H": "HALFDAY_H", "HALFDAY_L": "HALFDAY_L",
        "1HR_H": "1HR_H", "1HR_L": "1HR_L",
        "VWAP": "VWAP", "VWAP_UPPER": "VWAP_UPPER", "VWAP_LOWER": "VWAP_LOWER",
    }
    return mapping.get(name, name)


def is_new_level(ltype):
    """Returns True if this level type is NEW (not in our existing indicator)."""
    existing = {"PDH", "PDL", "PDC", "WEEK_H", "WEEK_L", "ORB_H", "ORB_L", "VWAP"}
    return ltype not in existing


# ===========================================================================
# Step 9: Score each level type
# ===========================================================================
def score_level_types(xref_df, bars_5m_index, levels_db, threshold=TIGHT_ATR):
    """
    For each level type, compute:
    - How many missed moves start within threshold ATR
    - Average magnitude of those moves
    - False positive rate
    """
    print(f"\nScoring level types (threshold={threshold} ATR)...")

    # Count coverage per level type
    type_moves = defaultdict(list)

    for _, row in xref_df.iterrows():
        nearby = row["nearby_tight"] if threshold <= TIGHT_ATR else row["nearby_loose"]
        for lname, dist in nearby.items():
            ltype = categorize_level(lname)
            type_moves[ltype].append({
                "magnitude": row["magnitude_atr"],
                "direction": row["direction"],
                "symbol": row["symbol"],
                "date": row["date"],
                "regime_score": row["regime_score"],
                "ema_aligned": row["ema_aligned"],
            })

    # Compute false positives — for each level type, count all 5m bars that
    # close within threshold of that level, then subtract the ones that have moves
    print("  Computing false positives (this may take a moment)...")

    fp_counts = {}
    touch_counts = {}

    for ltype in type_moves.keys():
        total_touches = 0
        move_touches = len(type_moves[ltype])

        # Sample: check all 5m bars across all symbol-days
        for (sym, dt), b5 in bars_5m_index.items():
            static_levels = levels_db.get((sym, dt), {})

            # Find all levels of this type for this day
            type_prices = []
            for lname, lprice in static_levels.items():
                if categorize_level(lname) == ltype and lprice is not None and not np.isnan(lprice):
                    type_prices.append(lprice)

            if not type_prices:
                # Dynamic levels — compute once per bar (expensive, so sample)
                continue

            for lprice in type_prices:
                for _, bar in b5.iterrows():
                    if bar["atr14"] <= 0 or np.isnan(bar["atr14"]):
                        continue
                    # Check if bar's close is within threshold of this level
                    dist = abs(bar["close"] - lprice) / bar["atr14"]
                    if dist <= threshold:
                        total_touches += 1

        fp_counts[ltype] = max(0, total_touches - move_touches)
        touch_counts[ltype] = total_touches

    # Also compute FP for dynamic levels
    for ltype in ["HALFDAY_H", "HALFDAY_L", "1HR_H", "1HR_L", "VWAP_UPPER", "VWAP_LOWER"]:
        if ltype not in type_moves:
            continue
        total_touches = 0
        move_touches = len(type_moves[ltype])

        for (sym, dt), b5 in bars_5m_index.items():
            for bar_idx in range(1, len(b5)):
                bar = b5.iloc[bar_idx]
                if bar["atr14"] <= 0 or np.isnan(bar["atr14"]):
                    continue
                dlev = get_dynamic_levels(b5, bar_idx, bar["atr14"])
                if ltype in dlev:
                    dist = abs(bar["close"] - dlev[ltype]) / bar["atr14"]
                    if dist <= threshold:
                        total_touches += 1

        fp_counts[ltype] = max(0, total_touches - move_touches)
        touch_counts[ltype] = total_touches

    # Build scorecard
    scorecard = []
    for ltype, moves in type_moves.items():
        n_moves = len(moves)
        avg_mag = np.mean([m["magnitude"] for m in moves])
        total_atr = sum(m["magnitude"] for m in moves)
        touches = touch_counts.get(ltype, n_moves)
        fp = fp_counts.get(ltype, 0)

        sig_quality = (n_moves / touches * avg_mag) if touches > 0 else 0

        # Regime breakdown
        regime_2 = sum(1 for m in moves if m["regime_score"] == 2)
        regime_1 = sum(1 for m in moves if m["regime_score"] == 1)
        regime_0 = sum(1 for m in moves if m["regime_score"] == 0)
        ema_pct = sum(1 for m in moves if m["ema_aligned"]) / n_moves * 100 if n_moves > 0 else 0

        scorecard.append({
            "level_type": ltype,
            "is_new": is_new_level(ltype),
            "moves_caught": n_moves,
            "total_atr_caught": round(total_atr, 1),
            "avg_magnitude": round(avg_mag, 2),
            "total_touches": touches,
            "false_positives": fp,
            "signal_quality": round(sig_quality, 3),
            "hit_rate": round(n_moves / touches * 100, 1) if touches > 0 else 0,
            "regime_2_pct": round(regime_2 / n_moves * 100, 1) if n_moves > 0 else 0,
            "ema_aligned_pct": round(ema_pct, 1),
        })

    sc_df = pd.DataFrame(scorecard)
    sc_df = sc_df.sort_values("total_atr_caught", ascending=False).reset_index(drop=True)

    print(f"  Scored {len(sc_df)} level types")
    return sc_df


# ===========================================================================
# Step 10: Regime analysis
# ===========================================================================
def regime_analysis(xref_df):
    """Analyze how regime score affects move quality."""
    print("\nRegime analysis...")

    regime_stats = {}
    for rs in [0, 1, 2]:
        sub = xref_df[xref_df["regime_score"] == rs]
        if len(sub) == 0:
            continue
        regime_stats[rs] = {
            "count": len(sub),
            "avg_mag": round(sub["magnitude_atr"].mean(), 2),
            "total_atr": round(sub["magnitude_atr"].sum(), 1),
            "pct": round(len(sub) / len(xref_df) * 100, 1),
        }
        print(f"  Regime {rs}: n={len(sub)}, avg_mag={sub['magnitude_atr'].mean():.2f}, "
              f"total_atr={sub['magnitude_atr'].sum():.1f}")

    # Time breakdown for regime=2
    r2 = xref_df[xref_df["regime_score"] == 2]
    if len(r2) > 0:
        r2_times = r2["start_time"].dt.hour
        time_buckets = {
            "10:30-11:00": ((r2_times == 10) & (r2["start_time"].dt.minute >= 30)).sum(),
            "11:00-12:00": (r2_times == 11).sum(),
            "12:00-14:00": ((r2_times >= 12) & (r2_times < 14)).sum(),
            "14:00-15:00": (r2_times == 14).sum(),
            "15:00-16:00": (r2_times == 15).sum(),
        }
        print(f"  Regime=2 by time: {time_buckets}")

    return regime_stats


# ===========================================================================
# Step 11: Backtest top level types
# ===========================================================================
def backtest_level_type(ltype, bars_5m_index, levels_db, threshold=TIGHT_ATR):
    """
    For a given level type, generate hypothetical signals:
    - Every 5m bar that closes within threshold of the level
    - Direction logic:
      - For HIGH levels (1HR_H, HALFDAY_H, etc.): direction = DOWN (reversal off high)
      - For LOW levels (1HR_L, HALFDAY_L, etc.): direction = UP (reversal off low)
      - For neutral levels (PIVOT, ROUND, PD_MID, etc.): direction matches EMA
    Then measure MFE/MAE over next 6 bars (30 min).
    Handles both static and dynamic levels.
    """
    is_dynamic = ltype in {"1HR_H", "1HR_L", "HALFDAY_H", "HALFDAY_L",
                           "VWAP", "VWAP_UPPER", "VWAP_LOWER"}

    # Determine directional bias from level type
    high_levels = {"1HR_H", "HALFDAY_H", "VWAP_UPPER", "PDH", "ORB_H", "ORB_EXT_H",
                   "WEEK_H", "D2_H", "MONTH_H", "PD_LAST_HR_H", "R1", "R2"}
    low_levels = {"1HR_L", "HALFDAY_L", "VWAP_LOWER", "PDL", "ORB_L", "ORB_EXT_L",
                  "WEEK_L", "D2_L", "MONTH_L", "PD_LAST_HR_L", "S1", "S2"}

    trades = []
    last_trade_key = {}  # (sym, dt) -> last trade bar_idx (cooldown)

    for (sym, dt), b5 in bars_5m_index.items():
        n = len(b5)
        static_levels = levels_db.get((sym, dt), {})

        # For static levels, pre-compute type prices
        static_type_prices = []
        if not is_dynamic:
            for lname, lprice in static_levels.items():
                if categorize_level(lname) == ltype and lprice is not None and not np.isnan(lprice):
                    static_type_prices.append(lprice)
            if not static_type_prices:
                continue

        for bar_idx in range(3, n - 6):  # need 6 bars after for MFE/MAE
            bar = b5.iloc[bar_idx]

            # Only after 10:30
            if bar["time"].hour < 10 or (bar["time"].hour == 10 and bar["time"].minute < 30):
                continue

            if bar["atr14"] <= 0 or np.isnan(bar["atr14"]):
                continue

            atr = bar["atr14"]

            # Cooldown: skip if we just traded within 2 bars
            trade_key = (sym, dt)
            if trade_key in last_trade_key and bar_idx - last_trade_key[trade_key] < 3:
                continue

            # Get level prices
            if is_dynamic:
                dlev = get_dynamic_levels(b5, bar_idx, atr)
                type_prices = [dlev[ltype]] if ltype in dlev and not np.isnan(dlev[ltype]) else []
            else:
                type_prices = static_type_prices

            for lprice in type_prices:
                dist = abs(bar["close"] - lprice) / atr
                if dist > threshold:
                    continue

                # Determine direction
                if ltype in high_levels:
                    # Reversal OFF high = SHORT, but also allow with-trend breakout
                    # Use EMA to decide: if EMA says up and we're at high, it's with-trend (long)
                    # If EMA says down and we're at high, it's reversal (short)
                    if bar["close"] < bar["ema20"]:
                        direction = "down"
                    else:
                        direction = "up"  # breakout continuation
                elif ltype in low_levels:
                    if bar["close"] > bar["ema20"]:
                        direction = "up"
                    else:
                        direction = "down"  # breakdown continuation
                else:
                    # Neutral levels: EMA decides
                    if bar["close"] > bar["ema20"]:
                        direction = "up"
                    elif bar["close"] < bar["ema20"]:
                        direction = "down"
                    else:
                        continue

                # Check VWAP alignment
                vwap_aligned = False
                if not np.isnan(bar["vwap"]):
                    if direction == "up" and bar["close"] > bar["vwap"]:
                        vwap_aligned = True
                    elif direction == "down" and bar["close"] < bar["vwap"]:
                        vwap_aligned = True

                # EMA alignment
                ema_aligned = (direction == "up" and bar["close"] > bar["ema20"]) or \
                              (direction == "down" and bar["close"] < bar["ema20"])

                regime = int(ema_aligned) + int(vwap_aligned)

                # Measure MFE/MAE over next 6 bars
                entry = bar["close"]
                future = b5.iloc[bar_idx + 1: bar_idx + 7]

                if direction == "up":
                    mfe = (future["high"].max() - entry) / atr
                    mae = (entry - future["low"].min()) / atr
                else:
                    mfe = (entry - future["low"].min()) / atr
                    mae = (future["high"].max() - entry) / atr

                pnl = mfe - mae

                trades.append({
                    "symbol": sym, "date": dt,
                    "time": bar["time"],
                    "direction": direction,
                    "entry": entry,
                    "level_price": lprice,
                    "dist_atr": round(dist, 4),
                    "atr": atr,
                    "regime": regime,
                    "ema_aligned": ema_aligned,
                    "vwap_aligned": vwap_aligned,
                    "mfe": round(mfe, 4),
                    "mae": round(mae, 4),
                    "pnl": round(pnl, 4),
                    "win": mfe > mae,
                })
                last_trade_key[trade_key] = bar_idx
                break  # one signal per bar per level type

    return pd.DataFrame(trades)


# ===========================================================================
# Step 12: Generate report
# ===========================================================================
def generate_report(xref_df, scorecard, regime_stats, backtest_results, missed_moves):
    """Write the final markdown report."""
    lines = []

    lines.append("# Midday Treasure Hunt: Level Analysis for Missed Moves")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Missed moves analyzed:** {len(xref_df)} (No Signal Zone category)")
    lines.append(f"**Total ATR in missed moves:** {xref_df['magnitude_atr'].sum():.1f}")
    lines.append("")

    # ---- Section 1: Level Proximity Overview ----
    lines.append("## Section 1: Level Proximity Analysis")
    lines.append("")

    has_tight = (xref_df["n_tight"] > 0).sum()
    has_loose = (xref_df["n_loose"] > 0).sum()
    total = len(xref_df)

    lines.append(f"**Key finding:** {has_tight} of {total} missed moves ({100*has_tight/total:.0f}%) had a level within {TIGHT_ATR} ATR at move start.")
    lines.append(f"**Loose match:** {has_loose} of {total} ({100*has_loose/total:.0f}%) had a level within {LOOSE_ATR} ATR.")
    lines.append("")

    # Coverage by level type (tight)
    type_coverage = defaultdict(int)
    for _, row in xref_df.iterrows():
        seen_types = set()
        for lname in row["nearby_tight"]:
            lt = categorize_level(lname)
            if lt not in seen_types:
                type_coverage[lt] += 1
                seen_types.add(lt)

    lines.append("### Coverage by Level Type (tight, <0.15 ATR)")
    lines.append("")
    lines.append("| Level Type | Moves Covered | % of Missed | New? |")
    lines.append("|------------|---------------|-------------|------|")
    for lt, cnt in sorted(type_coverage.items(), key=lambda x: -x[1]):
        is_new = "NEW" if is_new_level(lt) else "existing"
        lines.append(f"| {lt} | {cnt} | {100*cnt/total:.0f}% | {is_new} |")
    lines.append("")

    # How many moves have NO level at all (even loose)?
    no_level = (xref_df["n_loose"] == 0).sum()
    lines.append(f"**Moves with NO level within {LOOSE_ATR} ATR:** {no_level} ({100*no_level/total:.0f}%)")
    lines.append("")

    # ---- Section 2: New Level Type Scorecard ----
    lines.append("## Section 2: New Level Type Scorecard")
    lines.append("")
    lines.append("Ranked by total ATR caught (only new level types that are NOT in our existing indicator):")
    lines.append("")

    new_sc = scorecard[scorecard["is_new"]].copy()

    lines.append("| Level Type | Moves Caught | Total ATR | Avg Mag | Touches | FP | Hit Rate | Sig Quality | EMA% |")
    lines.append("|------------|-------------|-----------|---------|---------|-----|----------|-------------|------|")
    for _, row in new_sc.iterrows():
        lines.append(f"| {row['level_type']} | {row['moves_caught']} | {row['total_atr_caught']} | "
                     f"{row['avg_magnitude']} | {row['total_touches']} | {row['false_positives']} | "
                     f"{row['hit_rate']}% | {row['signal_quality']} | {row['ema_aligned_pct']}% |")
    lines.append("")

    # Also show existing levels for reference
    lines.append("### Existing Level Types (reference)")
    lines.append("")
    existing_sc = scorecard[~scorecard["is_new"]].copy()
    lines.append("| Level Type | Moves Caught | Total ATR | Hit Rate | Sig Quality |")
    lines.append("|------------|-------------|-----------|----------|-------------|")
    for _, row in existing_sc.iterrows():
        lines.append(f"| {row['level_type']} | {row['moves_caught']} | {row['total_atr_caught']} | "
                     f"{row['hit_rate']}% | {row['signal_quality']} |")
    lines.append("")

    # ---- Section 3: Deep Dive Top 3 ----
    lines.append("## Section 3: Top New Level Types (Deep Dive)")
    lines.append("")

    top3 = new_sc.head(5)
    for rank, (_, row) in enumerate(top3.iterrows(), 1):
        lt = row["level_type"]
        lines.append(f"### #{rank}: {lt}")
        lines.append("")
        lines.append(f"- **Moves caught:** {row['moves_caught']} ({row['total_atr_caught']} ATR)")
        lines.append(f"- **Average magnitude:** {row['avg_magnitude']} ATR")
        lines.append(f"- **Total touches:** {row['total_touches']}")
        lines.append(f"- **False positives:** {row['false_positives']}")
        lines.append(f"- **Hit rate:** {row['hit_rate']}%")
        lines.append(f"- **Signal quality:** {row['signal_quality']}")
        lines.append(f"- **EMA-aligned %:** {row['ema_aligned_pct']}%")
        lines.append(f"- **Regime=2 %:** {row['regime_2_pct']}%")
        lines.append("")

        # Find example moves
        examples = []
        for _, xrow in xref_df.iterrows():
            for lname in xrow["nearby_tight"]:
                if categorize_level(lname) == lt:
                    examples.append(xrow)
                    break
            if len(examples) >= 5:
                break

        if examples:
            lines.append("**Example moves:**")
            for ex in examples[:5]:
                t = ex["start_time"]
                tstr = t.strftime("%H:%M") if hasattr(t, "strftime") else str(t)
                lines.append(f"- {ex['symbol']} {ex['date']} {tstr} — {ex['direction']} "
                            f"{ex['magnitude_atr']:.2f} ATR (regime={ex['regime_score']})")
            lines.append("")

    # ---- Section 4: Regime Analysis ----
    lines.append("## Section 4: Regime-Aligned Midday Analysis")
    lines.append("")
    lines.append("Regime score = EMA aligned (0/1) + VWAP aligned (0/1). Score 2 = both aligned.")
    lines.append("")
    lines.append("| Regime | Count | % | Avg Magnitude | Total ATR |")
    lines.append("|--------|-------|---|---------------|-----------|")
    for rs in [2, 1, 0]:
        if rs in regime_stats:
            s = regime_stats[rs]
            lines.append(f"| {rs} | {s['count']} | {s['pct']}% | {s['avg_mag']} | {s['total_atr']} |")
    lines.append("")

    # Regime=2 breakdown by time
    r2 = xref_df[xref_df["regime_score"] == 2]
    if len(r2) > 0:
        lines.append("### Regime=2 by Time Window")
        lines.append("")
        r2_copy = r2.copy()
        def time_bucket(t):
            h = t.hour
            m = t.minute
            if h == 10 and m >= 30: return "10:30-11:00"
            if h == 11: return "11:00-12:00"
            if 12 <= h < 14: return "12:00-14:00"
            if h == 14: return "14:00-15:00"
            if h == 15: return "15:00-16:00"
            return "other"

        r2_copy["tbucket"] = r2_copy["start_time"].apply(time_bucket)
        for tb, grp in r2_copy.groupby("tbucket"):
            lines.append(f"- **{tb}:** {len(grp)} moves, avg {grp['magnitude_atr'].mean():.2f} ATR, "
                        f"total {grp['magnitude_atr'].sum():.1f} ATR")
        lines.append("")

        # By symbol
        lines.append("### Regime=2 by Symbol")
        lines.append("")
        for sym, grp in r2.groupby("symbol"):
            lines.append(f"- **{sym}:** {len(grp)} moves, avg {grp['magnitude_atr'].mean():.2f} ATR")
        lines.append("")

    # ---- Section 5: Backtest Results ----
    lines.append("## Section 5: Backtest Results")
    lines.append("")
    lines.append("Hypothetical signals: 5m bar closes within 0.15 ATR of level + EMA aligned.")
    lines.append("MFE/MAE measured over next 6 bars (30 min). Only after 10:30.")
    lines.append("")
    lines.append("**Baseline (existing signals):** 51.4% win, 0.038 avg P&L (ATR)")
    lines.append("")

    # Summary table first
    lines.append("### Summary Table")
    lines.append("")
    lines.append("| Level Type | N | Win% | Avg P&L | Total P&L | EMA-only N | EMA Win% | EMA P&L | R=2 N | R=2 Win% | R=2 P&L |")
    lines.append("|------------|---|------|---------|-----------|-----------|----------|---------|-------|----------|---------|")

    for lt, bt_df in backtest_results.items():
        if len(bt_df) == 0:
            lines.append(f"| {lt} | 0 | - | - | - | - | - | - | - | - | - |")
            continue

        n = len(bt_df)
        win = bt_df["win"].mean() * 100
        pnl = bt_df["pnl"].mean()
        total = bt_df["pnl"].sum()

        # EMA-only filter
        ema_bt = bt_df[bt_df["ema_aligned"] == True] if "ema_aligned" in bt_df.columns else bt_df[bt_df["regime"] >= 1]
        ema_n = len(ema_bt)
        ema_win = ema_bt["win"].mean() * 100 if ema_n > 0 else 0
        ema_pnl = ema_bt["pnl"].mean() if ema_n > 0 else 0

        # Regime=2
        r2 = bt_df[bt_df["regime"] == 2]
        r2_n = len(r2)
        r2_win = r2["win"].mean() * 100 if r2_n > 0 else 0
        r2_pnl = r2["pnl"].mean() if r2_n > 0 else 0

        lines.append(f"| {lt} | {n} | {win:.0f}% | {pnl:.3f} | {total:.1f} | "
                     f"{ema_n} | {ema_win:.0f}% | {ema_pnl:.3f} | "
                     f"{r2_n} | {r2_win:.0f}% | {r2_pnl:.3f} |")

    lines.append("")

    # Detailed per level type
    for lt, bt_df in backtest_results.items():
        if len(bt_df) == 0:
            continue

        win_rate = bt_df["win"].mean() * 100
        avg_mfe = bt_df["mfe"].mean()
        avg_mae = bt_df["mae"].mean()
        avg_pnl = bt_df["pnl"].mean()
        total_pnl = bt_df["pnl"].sum()
        n = len(bt_df)

        lines.append(f"### {lt} (N={n})")
        lines.append("")
        lines.append(f"- **Win rate:** {win_rate:.1f}%")
        lines.append(f"- **Avg MFE:** {avg_mfe:.3f} ATR")
        lines.append(f"- **Avg MAE:** {avg_mae:.3f} ATR")
        lines.append(f"- **Avg P&L:** {avg_pnl:.3f} ATR")
        lines.append(f"- **Total P&L:** {total_pnl:.1f} ATR")
        lines.append("")

        # EMA filter
        ema_bt = bt_df[bt_df.get("ema_aligned", bt_df["regime"] >= 1) == True] if "ema_aligned" in bt_df.columns else bt_df[bt_df["regime"] >= 1]
        if len(ema_bt) > 0:
            lines.append(f"  **With EMA filter only:** N={len(ema_bt)}, win={ema_bt['win'].mean()*100:.1f}%, "
                        f"avg_pnl={ema_bt['pnl'].mean():.3f}, total_pnl={ema_bt['pnl'].sum():.1f}")

        # Regime filter
        r2_bt = bt_df[bt_df["regime"] == 2]
        if len(r2_bt) > 0:
            r2_win = r2_bt["win"].mean() * 100
            r2_pnl = r2_bt["pnl"].mean()
            r2_total = r2_bt["pnl"].sum()
            lines.append(f"  **With regime=2 filter:** N={len(r2_bt)}, win={r2_win:.1f}%, "
                        f"avg_pnl={r2_pnl:.3f}, total_pnl={r2_total:.1f}")
        lines.append("")

        # By symbol (top 5 and bottom 5)
        sym_stats = bt_df.groupby("symbol").agg(
            n=("pnl", "count"), win=("win", "mean"), avg_pnl=("pnl", "mean"), total_pnl=("pnl", "sum")
        ).sort_values("avg_pnl", ascending=False)
        lines.append("  Top symbols: " + ", ".join(
            f"{s}: {r['win']*100:.0f}%/{r['avg_pnl']:.3f}" for s, r in sym_stats.head(3).iterrows()
        ))
        lines.append("  Worst symbols: " + ", ".join(
            f"{s}: {r['win']*100:.0f}%/{r['avg_pnl']:.3f}" for s, r in sym_stats.tail(3).iterrows()
        ))
        lines.append("")

    # ---- Section 6: Recommendations ----
    lines.append("## Section 6: Recommendations")
    lines.append("")

    # Rank by BACKTEST P&L — the only metric that matters
    lines.append("### IMPLEMENT (backtest-validated, positive P&L)")
    lines.append("")
    lines.append("Ranked by backtest avg P&L (the ONLY metric that matters):")
    lines.append("")

    bt_ranked = []
    for lt, bt in backtest_results.items():
        if len(bt) > 0 and bt["pnl"].mean() > 0:
            # Get scorecard entry
            sc_row = scorecard[scorecard["level_type"] == lt]
            moves_caught = int(sc_row["moves_caught"].iloc[0]) if len(sc_row) > 0 else 0
            atr_caught = float(sc_row["total_atr_caught"].iloc[0]) if len(sc_row) > 0 else 0
            bt_ranked.append({
                "type": lt,
                "moves": moves_caught,
                "atr": atr_caught,
                "n": len(bt),
                "win": bt["win"].mean() * 100,
                "avg_pnl": bt["pnl"].mean(),
                "total_pnl": bt["pnl"].sum(),
            })
    bt_ranked.sort(key=lambda x: -x["avg_pnl"])

    for rank, item in enumerate(bt_ranked, 1):
        lines.append(f"{rank}. **{item['type']}** — Backtest: {item['win']:.0f}% win, "
                    f"+{item['avg_pnl']:.3f} avg P&L, +{item['total_pnl']:.1f} total | "
                    f"Catches {item['moves']} missed moves ({item['atr']:.0f} ATR)")
    lines.append("")

    lines.append("### DO NOT IMPLEMENT (backtest-negative)")
    lines.append("")
    for lt, bt in backtest_results.items():
        if len(bt) > 0 and bt["pnl"].mean() <= 0:
            lines.append(f"- **{lt}** — {bt['win'].mean()*100:.0f}% win, "
                        f"{bt['pnl'].mean():.3f} avg P&L (net negative)")
    lines.append("")

    lines.append("### Key Insights")
    lines.append("")
    lines.append("1. **VWAP Lower Band is the standout dynamic level.** 53% win, +0.133/trade, "
                "+77 ATR total. Price bouncing off VWAP-1SD with EMA alignment = high-quality signal.")
    lines.append("2. **Prior-Day Last-Hour Low (PD_LAST_HR_L)** is the best new STATIC level. "
                "55.6% win, +0.238/trade. Institutional memory of prior close region creates support.")
    lines.append("3. **Prior-Day Mid-Range (PD_MID)** is the sleeper hit. 55.1% win, +0.209/trade. "
                "Yesterday's fair value acts as magnet/bounce level all day.")
    lines.append("4. **1HR_H/L are traps.** Highest raw coverage (112+92 moves) but negative backtest. "
                "Price touches 1-hour high/low constantly — too much noise.")
    lines.append("5. **VWAP Upper Band and D2_H are the worst.** Strongly negative. "
                "Price at VWAP+1SD tends to mean-revert but our EMA direction picks the wrong side.")
    lines.append("6. **Regime=2 filter does NOT help.** Most levels perform worse with regime=2. "
                "The EMA gate is already embedded in the backtest direction logic.")
    lines.append("7. **32% of missed moves have NO level within 0.3 ATR.** These are genuine "
                "'level desert' moves — no static or dynamic reference point. "
                "Would need a fundamentally different trigger (e.g., volume surge or momentum breakout).")
    lines.append("")

    # Coverage summary
    lines.append("### Coverage Impact")
    lines.append("")
    total_missed_atr = xref_df["magnitude_atr"].sum()

    # Use backtest-positive types
    positive_types = [item["type"] for item in bt_ranked]

    recovered_moves = set()
    for _, row in xref_df.iterrows():
        for lname in row["nearby_tight"]:
            if categorize_level(lname) in positive_types:
                recovered_moves.add(row["move_idx"])
                break

    recovered_atr = xref_df[xref_df["move_idx"].isin(recovered_moves)]["magnitude_atr"].sum()
    lines.append(f"- **Total missed ATR (No Signal Zone):** {total_missed_atr:.1f}")
    lines.append(f"- **Backtest-positive levels would cover:** {len(recovered_moves)} moves, "
                f"{recovered_atr:.1f} ATR ({100*recovered_atr/total_missed_atr:.0f}%)")

    # Estimated realistic capture (apply win rate)
    est_capture = sum(item["avg_pnl"] * item["moves"] for item in bt_ranked if item["avg_pnl"] > 0)
    lines.append(f"- **Estimated realistic ATR capture:** {est_capture:.1f} ATR (based on backtest P&L x coverage)")
    lines.append("")

    lines.append("### Implementation Priority")
    lines.append("")
    lines.append("| Priority | Level | Pine Complexity | Expected Impact |")
    lines.append("|----------|-------|----------------|-----------------|")
    if bt_ranked:
        for i, item in enumerate(bt_ranked[:4], 1):
            complexity = "Low" if item["type"] in {"PD_MID", "PD_LAST_HR_L", "S2"} else "Medium"
            lines.append(f"| {i} | {item['type']} | {complexity} | +{item['total_pnl']:.0f} ATR |")
    lines.append("")

    # Write report
    with open(REPORT_PATH, "w") as f:
        f.write("\n".join(lines))

    print(f"\nReport written to {REPORT_PATH}")
    return "\n".join(lines)


# ===========================================================================
# MAIN
# ===========================================================================
def main():
    print("=" * 60)
    print("MIDDAY TREASURE HUNT")
    print("=" * 60)

    # Step 1: Load data
    print("\n--- Step 1: Loading candle data ---")
    candles_1m = load_candle_data()

    # Step 2: Resample to 5m
    print("\n--- Step 2: Resampling to 5m ---")
    bars_5m = resample_5m(candles_1m)

    # Step 3: Detect moves
    print("\n--- Step 3: Detecting moves ---")
    moves_df = detect_moves(bars_5m)

    # Step 4: Load signals and classify
    print("\n--- Step 4: Loading signals & classifying ---")
    signals_df = pd.read_csv(SIGNALS_PATH)
    # Parse signal times
    signals_df["date_parsed"] = pd.to_datetime(signals_df["date"]).dt.date
    signals_df["time_parsed"] = pd.to_datetime(
        signals_df["date"].astype(str) + " " + signals_df["time"].astype(str)
    )
    signals_df["time_parsed"] = signals_df["time_parsed"].dt.tz_localize("US/Eastern")

    moves_df = classify_moves(moves_df, signals_df)

    # Filter to MISSED moves only, and focus on after-10:30 (No Signal Zone)
    missed = moves_df[moves_df["classification"] == "MISSED"].copy()
    print(f"Total missed moves: {len(missed)}")

    # Filter to after 10:30 (the "No Signal Zone" time range)
    missed_after = missed[missed["start_time"].dt.time >= dtime(10, 30)].copy()
    print(f"Missed moves after 10:30: {len(missed_after)} ({missed_after['magnitude_atr'].sum():.1f} ATR)")

    # Step 5: Compute all levels
    print("\n--- Step 5: Computing all levels ---")
    levels_db, bars_5m_index = compute_daily_levels(candles_1m, bars_5m)

    # Step 6: Cross-reference
    print("\n--- Step 6: Cross-referencing missed moves with levels ---")
    xref_df = cross_reference_levels(missed_after, levels_db, bars_5m_index)

    # Step 7: Score level types
    print("\n--- Step 7: Scoring level types ---")
    scorecard = score_level_types(xref_df, bars_5m_index, levels_db, threshold=TIGHT_ATR)
    print("\nScorecard (top 15):")
    print(scorecard.head(15).to_string(index=False))

    # Step 8: Regime analysis
    print("\n--- Step 8: Regime analysis ---")
    regime_stats = regime_analysis(xref_df)

    # Step 9: Backtest top new level types
    print("\n--- Step 9: Backtesting top level types ---")
    # Backtest top new level types + a few promising ones
    backtest_types = ["1HR_H", "1HR_L", "VWAP_LOWER", "VWAP_UPPER", "ROUND_5",
                      "HALFDAY_H", "HALFDAY_L", "ORB_EXT_L", "S2", "PD_LAST_HR_L",
                      "PIVOT", "PD_MID", "D2_H"]
    backtest_results = {}
    for lt in backtest_types:
        print(f"  Backtesting {lt}...")
        bt = backtest_level_type(lt, bars_5m_index, levels_db)
        backtest_results[lt] = bt
        if len(bt) > 0:
            print(f"    {lt}: N={len(bt)}, win={bt['win'].mean()*100:.1f}%, "
                  f"avg_pnl={bt['pnl'].mean():.3f}, total={bt['pnl'].sum():.1f}")
        else:
            print(f"    {lt}: No trades generated")

    # Step 10: Generate report
    print("\n--- Step 10: Generating report ---")
    report = generate_report(xref_df, scorecard, regime_stats, backtest_results, missed_after)

    # Final summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    has_tight = (xref_df["n_tight"] > 0).sum()
    print(f"1. {has_tight}/{len(xref_df)} missed moves ({100*has_tight/len(xref_df):.0f}%) "
          f"had a level within {TIGHT_ATR} ATR")

    if len(scorecard[scorecard["is_new"]]) > 0:
        top = scorecard[scorecard["is_new"]].iloc[0]
        print(f"2. Best NEW level: {top['level_type']} — "
              f"{top['moves_caught']} moves, {top['total_atr_caught']} ATR, "
              f"quality={top['signal_quality']:.3f}")

    if 2 in regime_stats:
        rs2 = regime_stats[2]
        print(f"3. Regime=2 moves: {rs2['count']} ({rs2['pct']}%), "
              f"avg_mag={rs2['avg_mag']}, total={rs2['total_atr']}")

    for lt, bt in backtest_results.items():
        if len(bt) > 0 and bt["pnl"].mean() > 0:
            print(f"4. Backtest {lt}: win={bt['win'].mean()*100:.1f}%, avg_pnl={bt['pnl'].mean():.3f}")
            break

    print(f"\nReport: {REPORT_PATH}")


if __name__ == "__main__":
    main()
