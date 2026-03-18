#!/usr/bin/env python3
"""
KLB Move Catalog Builder
========================
Builds a comprehensive catalog of ALL tradeable moves (≥0.30 ATR) across 15 symbols
over 500+ trading days. Foundation for all future signal research.

Architecture: load → levels → indicators → detect → enrich → classify → export
Two-pass zig-zag: 0.30 ATR primary + 1.00 ATR large moves with parent-child linking.

Output: parquet catalog (~46K moves), CSV summary, stats markdown.
"""

import pandas as pd
import numpy as np
import warnings
import sys
from pathlib import Path
from datetime import time as dtime, timedelta, date as date_type
import time as time_mod

warnings.filterwarnings("ignore", category=FutureWarning)

# ── Config ────────────────────────────────────────────────────────────────────

CACHE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars")
OUT_DIR = Path(__file__).parent

SYMBOLS = [
    "SPY", "AAPL", "AMD", "AMZN", "GLD", "GOOGL", "META", "MSFT",
    "NFLX", "NVDA", "QQQ", "SLV", "TSLA", "TSM", "XLE",
]

# Zig-zag thresholds
MIN_ATR_MAG = 0.30       # Primary pass minimum move size
REVERSAL_ATR = 0.15      # Primary reversal threshold
LARGE_ATR_MAG = 1.00     # Large move pass minimum
LARGE_REVERSAL_ATR = 0.50  # Large move reversal threshold
MIN_BARS = 1             # Minimum bars for a move

# Time boundaries
RTH_START = dtime(9, 30)
RTH_END = dtime(16, 0)
PM_START = dtime(4, 0)
ORB_END = dtime(10, 0)

ET = "US/Eastern"

# Resolution config (set by CLI args)
RESOLUTION = "5m"  # "5m" or "1m"
PARQUET_SUFFIX = {"5m": "_5_mins_ib.parquet", "1m": "_1_min_ib.parquet"}
OUTPUT_PREFIX = {"5m": "", "1m": "1m-"}  # 1m outputs get "1m-" prefix


# ── Task 1: Data Loading & Indicators ─────────────────────────────────────────

def load_data():
    """Load bar data + daily parquet for all 15 symbols. Convert Berlin→ET."""
    data_bars = {}
    data_daily = {}
    suffix = PARQUET_SUFFIX[RESOLUTION]

    for sym in SYMBOLS:
        fp = CACHE / f"{sym.lower()}{suffix}"
        if not fp.exists():
            print(f"  SKIP {sym}: no {RESOLUTION} data")
            continue
        df = pd.read_parquet(fp)
        df["dt_et"] = df["date"].dt.tz_convert(ET)
        df["trade_date"] = df["dt_et"].dt.date
        df["trade_time"] = df["dt_et"].dt.time
        df["symbol"] = sym
        df = df.sort_values("dt_et").reset_index(drop=True)
        data_bars[sym] = df

        # Daily bars (always load)
        fp_daily = CACHE / f"{sym.lower()}_1_day_ib.parquet"
        if fp_daily.exists():
            dd = pd.read_parquet(fp_daily)
            if dd["date"].dt.tz is None:
                dd["trade_date"] = dd["date"].dt.date
            else:
                dd["trade_date"] = dd["date"].dt.tz_convert(ET).dt.date
            dd["symbol"] = sym
            dd = dd.sort_values("trade_date").reset_index(drop=True)
            data_daily[sym] = dd

    return data_bars, data_daily


def compute_indicators(data_5m):
    """Add technical indicators to 5m DataFrames. Returns dict of enriched DataFrames."""
    enriched = {}

    for sym, df in data_5m.items():
        df = df.copy()

        # ATR14 (Wilder's smoothing on all bars including pre-market for warmup)
        prev_c = df["close"].shift(1)
        tr = pd.concat([
            df["high"] - df["low"],
            (df["high"] - prev_c).abs(),
            (df["low"] - prev_c).abs()
        ], axis=1).max(axis=1)
        df["atr14"] = tr.ewm(alpha=1/14, adjust=False).mean()

        # EMAs
        df["ema21"] = df["close"].ewm(span=21, adjust=False).mean()
        df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()

        # ADX14 (Wilder's)
        prev_h, prev_l = df["high"].shift(1), df["low"].shift(1)
        plus_dm = np.where((df["high"] - prev_h > prev_l - df["low"]) & (df["high"] - prev_h > 0),
                           df["high"] - prev_h, 0)
        minus_dm = np.where((prev_l - df["low"] > df["high"] - prev_h) & (prev_l - df["low"] > 0),
                            prev_l - df["low"], 0)
        atr_for_adx = tr.ewm(alpha=1/14, adjust=False).mean()
        plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(alpha=1/14, adjust=False).mean() / atr_for_adx
        minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=1/14, adjust=False).mean() / atr_for_adx
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        df["adx14"] = dx.ewm(alpha=1/14, adjust=False).mean().fillna(0)

        # VWAP (daily reset) — only on RTH bars
        df["day_key"] = df["trade_date"].astype(str)
        typical = (df["high"] + df["low"] + df["close"]) / 3
        # Mask: only accumulate during RTH
        rth_mask = (df["trade_time"] >= RTH_START) & (df["trade_time"] < RTH_END)
        df["_tp_vol"] = np.where(rth_mask, typical * df["volume"], 0)
        df["_vol"] = np.where(rth_mask, df["volume"], 0)
        df["cum_tp_vol"] = df.groupby("day_key")["_tp_vol"].cumsum()
        df["cum_vol"] = df.groupby("day_key")["_vol"].cumsum()
        df["vwap"] = np.where(df["cum_vol"] > 0, df["cum_tp_vol"] / df["cum_vol"], np.nan)

        # Volume indicators
        df["vol_sma20"] = df["volume"].rolling(20, min_periods=1).mean()
        df["vol_ratio"] = df["volume"] / df["vol_sma20"].replace(0, np.nan)

        # Candle metrics
        rng = df["high"] - df["low"]
        df["body_pct"] = (np.abs(df["close"] - df["open"]) / rng.replace(0, np.nan) * 100).fillna(0)
        df["range_atr"] = rng / df["atr14"].replace(0, np.nan)

        # Daily ATR (from daily bars, mapped to 5m)
        # Use the 5m-level atr14 as fallback if no daily available
        df["daily_atr"] = df["atr14"]  # Will be overridden below if daily data exists

        # Cleanup temp columns
        df.drop(columns=["_tp_vol", "_vol", "cum_tp_vol", "cum_vol", "day_key"], inplace=True)

        enriched[sym] = df

    return enriched


def compute_daily_atr(data_5m, data_daily):
    """Compute proper daily ATR from daily bars and map to 5m frames."""
    for sym in data_5m:
        if sym not in data_daily:
            continue
        dd = data_daily[sym].copy()
        dd["daily_range"] = dd["high"] - dd["low"]
        dd["daily_atr"] = dd["daily_range"].rolling(14, min_periods=1).mean()
        # Use PRIOR day's ATR (available at open)
        dd["daily_atr_prev"] = dd["daily_atr"].shift(1)
        atr_map = dd.set_index("trade_date")["daily_atr_prev"].to_dict()
        data_5m[sym]["daily_atr"] = data_5m[sym]["trade_date"].map(atr_map)
        # Fill any missing with 5m atr14
        data_5m[sym]["daily_atr"].fillna(data_5m[sym]["atr14"], inplace=True)


# ── Task 2: Level Computation ─────────────────────────────────────────────────

def compute_levels(data_5m, data_daily):
    """Compute all key levels per symbol-day. Returns levels[symbol][date] = dict."""
    levels = {}

    for sym in SYMBOLS:
        if sym not in data_5m:
            continue
        levels[sym] = {}
        df_5m = data_5m[sym]
        dd = data_daily.get(sym)
        dates = sorted(df_5m[
            (df_5m["trade_time"] >= RTH_START) & (df_5m["trade_time"] < RTH_END)
        ]["trade_date"].unique())

        for target_date in dates:
            lvls = {}

            # ── From daily bars ──
            if dd is not None:
                prior = dd[dd["trade_date"] < target_date]
                if len(prior) >= 1:
                    pd_row = prior.iloc[-1]
                    lvls["PD High"] = float(pd_row["high"])
                    lvls["PD Low"] = float(pd_row["low"])
                    lvls["PD Close"] = float(pd_row["close"])
                    lvls["PD Mid"] = round((pd_row["high"] + pd_row["low"]) / 2, 4)

                # Week High/Low (last 5 trading days)
                if len(prior) >= 2:
                    week_data = prior.tail(5)
                    lvls["Week High"] = float(week_data["high"].max())
                    lvls["Week Low"] = float(week_data["low"].min())

                # Week Open (Monday's open of current week)
                td = pd.Timestamp(target_date)
                # Find the Monday of this week
                monday = td - timedelta(days=td.weekday())
                mon_row = dd[dd["trade_date"] == monday.date()]
                if not mon_row.empty:
                    lvls["Week Open"] = float(mon_row.iloc[0]["open"])

                # Month Open (1st trading day of month)
                month_start = target_date.replace(day=1)
                month_rows = dd[(dd["trade_date"] >= month_start) & (dd["trade_date"] <= target_date)]
                if not month_rows.empty:
                    lvls["Month Open"] = float(month_rows.iloc[0]["open"])

            # ── From 5m bars ──
            day_5m = df_5m[df_5m["trade_date"] == target_date]

            # Today's Open (first RTH bar)
            rth_bars = day_5m[(day_5m["trade_time"] >= RTH_START) & (day_5m["trade_time"] < RTH_END)]
            if not rth_bars.empty:
                lvls["Today Open"] = float(rth_bars.iloc[0]["open"])

            # PM High/Low (pre-market: 4:00-9:30)
            pm_bars = day_5m[(day_5m["trade_time"] >= PM_START) & (day_5m["trade_time"] < RTH_START)]
            if not pm_bars.empty:
                lvls["PM High"] = float(pm_bars["high"].max())
                lvls["PM Low"] = float(pm_bars["low"].min())

            # ORB High/Low (9:30-10:00) — time-gated in enrichment
            orb_bars = day_5m[(day_5m["trade_time"] >= RTH_START) & (day_5m["trade_time"] < ORB_END)]
            if not orb_bars.empty:
                lvls["ORB High"] = float(orb_bars["high"].max())
                lvls["ORB Low"] = float(orb_bars["low"].min())

            # PD Last Hour High/Low (previous day 15:00-16:00)
            if dd is not None:
                prior_days = dd[dd["trade_date"] < target_date]
                if len(prior_days) >= 1:
                    prev_date = prior_days.iloc[-1]["trade_date"]
                    prev_5m = df_5m[df_5m["trade_date"] == prev_date]
                    last_hr = prev_5m[
                        (prev_5m["trade_time"] >= dtime(15, 0)) &
                        (prev_5m["trade_time"] < RTH_END)
                    ]
                    if not last_hr.empty:
                        lvls["PD Last Hr High"] = float(last_hr["high"].max())
                        lvls["PD Last Hr Low"] = float(last_hr["low"].min())

            levels[sym][target_date] = lvls

    return levels


def export_levels(levels, data_5m):
    """Export key levels as a flat database with channel (zone) information.
    Each level gets a high/low range based on its source bars."""
    rows = []
    for sym in sorted(levels.keys()):
        df = data_5m.get(sym)
        for date in sorted(levels[sym].keys()):
            day_levels = levels[sym][date]
            # Get daily ATR for zone width fallback
            if df is not None:
                day_bars = df[df["trade_date"] == date]
                rth = day_bars[(day_bars["trade_time"] >= RTH_START) & (day_bars["trade_time"] < RTH_END)]
                datr = rth["daily_atr"].iloc[0] if len(rth) > 0 and not np.isnan(rth["daily_atr"].iloc[0]) else None
            else:
                datr = None

            for lname, lprice in day_levels.items():
                row = {
                    "symbol": sym,
                    "date": date,
                    "level_name": lname,
                    "level_price": round(lprice, 4),
                }
                # Channel: define zone around level
                # For bar-derived levels (ORB, PM, PD Last Hr), use the bar range
                # For single-price levels (PD Close, Open, Week/Month Open), use small ATR zone
                zone_half = (datr * 0.02) if datr else 0.0  # Default: 2% of daily ATR
                if "High" in lname or "Low" in lname:
                    # These are extremes — zone extends inward (price can wick through)
                    zone_half = (datr * 0.03) if datr else 0.0  # 3% ATR for wick zone
                row["zone_high"] = round(lprice + zone_half, 4)
                row["zone_low"] = round(lprice - zone_half, 4)
                row["zone_width"] = round(zone_half * 2, 4)
                row["daily_atr"] = round(datr, 4) if datr else None
                rows.append(row)

    levels_df = pd.DataFrame(rows)
    path = OUT_DIR / "key-levels-db.parquet"
    levels_df.to_parquet(path, index=False)
    csv_path = OUT_DIR / "key-levels-db-summary.csv"
    levels_df.head(2000).to_csv(csv_path, index=False)
    print(f"  → {path} ({len(levels_df)} level-day rows)")
    print(f"  → {csv_path}")
    return levels_df


# ── Task 3: Move Detection (Zig-Zag) ─────────────────────────────────────────

def detect_moves_pass(data_5m, min_mag, reversal_thresh, pass_name="primary"):
    """One pass of zig-zag move detection across all symbols.
    Uses DAILY ATR for magnitude/reversal thresholds (not 5m ATR)."""
    all_moves = []
    move_id = 0

    for sym in SYMBOLS:
        if sym not in data_5m:
            continue
        df = data_5m[sym]
        # RTH only for move detection
        rth = df[(df["trade_time"] >= RTH_START) & (df["trade_time"] < RTH_END)].copy()

        for trade_date, grp in rth.groupby("trade_date"):
            grp = grp.sort_values("dt_et").reset_index(drop=True)
            n = len(grp)
            if n < 5:
                continue

            H = grp["high"].values
            L = grp["low"].values
            C = grp["close"].values
            O = grp["open"].values
            T = grp["dt_et"].tolist()
            ATR_5m = grp["atr14"].values
            # Use DAILY ATR for thresholds — measures real tradeable moves
            DATR = grp["daily_atr"].values

            def make_move(direction, si, ei, peak_i):
                nonlocal move_id
                datr = DATR[si] if DATR[si] > 0 and not np.isnan(DATR[si]) else DATR[min(si + 1, n - 1)]
                if datr <= 0 or np.isnan(datr):
                    return None
                if direction == "bull":
                    mag = (H[peak_i] - L[si]) / datr
                    sp, ep, pp = float(L[si]), float(C[ei]), float(H[peak_i])
                else:
                    mag = (H[si] - L[peak_i]) / datr
                    sp, ep, pp = float(H[si]), float(C[ei]), float(L[peak_i])
                dur = ei - si
                if dur < MIN_BARS or mag < min_mag:
                    return None
                move_id += 1
                return {
                    "move_id": f"{pass_name}_{move_id}",
                    "symbol": sym,
                    "date": trade_date,
                    "direction": direction,
                    "start_time": T[si],
                    "end_time": T[ei],
                    "peak_time": T[peak_i],
                    "start_idx": int(si),
                    "end_idx": int(ei),
                    "peak_idx": int(peak_i),
                    "start_price": sp,
                    "end_price": ep,
                    "peak_price": pp,
                    "magnitude_atr": round(mag, 4),
                    "magnitude_pct": round(abs(pp - sp) / sp * 100, 4) if sp > 0 else 0,
                    "duration_bars": dur,
                    "atr": round(float(datr), 4),
                    "pass": pass_name,
                }

            # Initialize zig-zag
            direction = None
            move_si = 0
            run_hi = H[0]
            run_hi_idx = 0
            run_lo = L[0]
            run_lo_idx = 0

            # Determine initial direction from first 3 bars
            if n >= 3:
                hi_idx = int(np.argmax(H[:3]))
                lo_idx = int(np.argmin(L[:3]))
                if lo_idx <= hi_idx:
                    direction = "bull"
                    move_si = lo_idx
                    run_hi = H[hi_idx]
                    run_hi_idx = hi_idx
                    run_lo = L[lo_idx]
                    run_lo_idx = lo_idx
                else:
                    direction = "bear"
                    move_si = hi_idx
                    run_lo = L[lo_idx]
                    run_lo_idx = lo_idx
                    run_hi = H[hi_idx]
                    run_hi_idx = hi_idx

            for i in range(3, n):
                datr = DATR[i] if DATR[i] > 0 and not np.isnan(DATR[i]) else DATR[max(0, i - 1)]
                if datr <= 0 or np.isnan(datr):
                    continue

                if direction == "bull":
                    if H[i] > run_hi:
                        run_hi = H[i]
                        run_hi_idx = i
                    pullback = run_hi - L[i]
                    if pullback / datr >= reversal_thresh:
                        mv = make_move("bull", move_si, run_hi_idx, run_hi_idx)
                        if mv:
                            all_moves.append(mv)
                        direction = "bear"
                        move_si = run_hi_idx
                        run_lo = L[i]
                        run_lo_idx = i

                elif direction == "bear":
                    if L[i] < run_lo:
                        run_lo = L[i]
                        run_lo_idx = i
                    bounce = H[i] - run_lo
                    if bounce / datr >= reversal_thresh:
                        mv = make_move("bear", move_si, run_lo_idx, run_lo_idx)
                        if mv:
                            all_moves.append(mv)
                        direction = "bull"
                        move_si = run_lo_idx
                        run_hi = H[i]
                        run_hi_idx = i

            # End of day — emit final pending move
            if direction == "bull":
                mv = make_move("bull", move_si, run_hi_idx, run_hi_idx)
                if mv:
                    all_moves.append(mv)
            elif direction == "bear":
                mv = make_move("bear", move_si, run_lo_idx, run_lo_idx)
                if mv:
                    all_moves.append(mv)

    return all_moves


def detect_moves(data_5m):
    """Two-pass zig-zag: primary (0.30 ATR) + large (1.00 ATR) with parent-child linking."""
    print("  Primary pass (≥0.30 ATR)...")
    primary = detect_moves_pass(data_5m, MIN_ATR_MAG, REVERSAL_ATR, "primary")
    print(f"    → {len(primary)} primary moves")

    print("  Large pass (≥1.00 ATR)...")
    large = detect_moves_pass(data_5m, LARGE_ATR_MAG, LARGE_REVERSAL_ATR, "large")
    print(f"    → {len(large)} large moves")

    # Link: child moves get parent_move_id if they fall within a large move's time range
    all_moves = primary + large
    moves_df = pd.DataFrame(all_moves)

    if len(moves_df) == 0:
        return moves_df

    # Sort for consistency
    moves_df = moves_df.sort_values(["symbol", "date", "start_time"]).reset_index(drop=True)

    # Parent-child linking
    moves_df["parent_move_id"] = None
    large_df = moves_df[moves_df["pass"] == "large"]
    primary_df = moves_df[moves_df["pass"] == "primary"]

    for _, lg in large_df.iterrows():
        mask = (
            (primary_df["symbol"] == lg["symbol"]) &
            (primary_df["date"] == lg["date"]) &
            (primary_df["start_time"] >= lg["start_time"]) &
            (primary_df["end_time"] <= lg["end_time"])
        )
        moves_df.loc[primary_df[mask].index, "parent_move_id"] = lg["move_id"]

    return moves_df


# ── Task 4: Context Enrichment ────────────────────────────────────────────────

def classify_candle(body_pct, open_p, close_p, high, low):
    """Classify candle type."""
    if body_pct >= 90:
        return "marubozu"
    if body_pct >= 70:
        return "big_body"
    if body_pct < 15:
        return "doji"
    rng = high - low
    if rng == 0:
        return "doji"
    body = abs(close_p - open_p)
    upper_wick = high - max(open_p, close_p)
    lower_wick = min(open_p, close_p) - low
    if lower_wick > body * 2 and upper_wick < body * 0.5:
        return "hammer"
    if upper_wick > body * 2 and lower_wick < body * 0.5:
        return "shooting_star"
    if body_pct < 40:
        return "indecisive"
    return "normal"


def enrich_context(moves_df, data_5m, levels):
    """Add ~35 context columns per move."""
    if moves_df.empty:
        return moves_df

    enriched_rows = []
    total = len(moves_df)
    checkpoint = max(1, total // 20)

    for idx, mv in moves_df.iterrows():
        if idx % checkpoint == 0:
            print(f"    Enriching {idx}/{total} ({idx*100//total}%)...")

        sym = mv["symbol"]
        date = mv["date"]
        df = data_5m.get(sym)
        if df is None:
            enriched_rows.append({})
            continue

        # Get RTH bars for this day
        day_rth = df[
            (df["trade_date"] == date) &
            (df["trade_time"] >= RTH_START) &
            (df["trade_time"] < RTH_END)
        ].reset_index(drop=True)

        if day_rth.empty or mv["start_idx"] >= len(day_rth):
            enriched_rows.append({})
            continue

        si = int(mv["start_idx"])
        ei = int(mv["end_idx"])
        pi = int(mv["peak_idx"])
        atr = mv["atr"]
        ctx = {}

        # ── Pre-move (5 bars before start) ──
        pre_start = max(0, si - 5)
        pre_bars = day_rth.iloc[pre_start:si]
        if len(pre_bars) >= 2:
            ema_vals = pre_bars["ema21"].values
            ctx["pre_ema21_slope"] = round((ema_vals[-1] - ema_vals[0]) / max(atr, 0.001), 4)
        else:
            ctx["pre_ema21_slope"] = 0.0

        if si < len(day_rth):
            bar_s = day_rth.iloc[si]
            ctx["pre_ema21_position"] = "above" if bar_s["close"] > bar_s["ema21"] else "below"
            ctx["pre_vwap_position"] = "above" if (not np.isnan(bar_s["vwap"]) and bar_s["close"] > bar_s["vwap"]) else "below"
            ctx["pre_vwap_dist_atr"] = round((bar_s["close"] - bar_s["vwap"]) / max(atr, 0.001), 4) if not np.isnan(bar_s["vwap"]) else 0.0
            ctx["pre_adx"] = round(float(bar_s["adx14"]), 2)
        else:
            ctx["pre_ema21_position"] = "unknown"
            ctx["pre_vwap_position"] = "unknown"
            ctx["pre_vwap_dist_atr"] = 0.0
            ctx["pre_adx"] = 0.0

        if len(pre_bars) > 0:
            ctx["pre_vol_avg_ratio"] = round(float(pre_bars["vol_ratio"].mean()), 2)
            # Compression: range getting tighter?
            if len(pre_bars) >= 3:
                ranges = (pre_bars["high"] - pre_bars["low"]).values
                ctx["pre_compression"] = round(float(ranges[-1] / max(ranges[0], 0.001)), 4)
            else:
                ctx["pre_compression"] = 1.0
        else:
            ctx["pre_vol_avg_ratio"] = 1.0
            ctx["pre_compression"] = 1.0

        # ── Trigger bar ──
        if si < len(day_rth):
            tb = day_rth.iloc[si]
            ctx["trig_body_pct"] = round(float(tb["body_pct"]), 1)
            ctx["trig_range_atr"] = round(float(tb["range_atr"]), 4) if not np.isnan(tb["range_atr"]) else 0.0
            ctx["trig_vol_ratio"] = round(float(tb["vol_ratio"]), 2) if not np.isnan(tb["vol_ratio"]) else 1.0
            ctx["trig_candle_type"] = classify_candle(tb["body_pct"], tb["open"], tb["close"], tb["high"], tb["low"])
            ctx["trig_ema_aligned"] = (mv["direction"] == "bull" and tb["close"] > tb["ema21"]) or \
                                      (mv["direction"] == "bear" and tb["close"] < tb["ema21"])
            if not np.isnan(tb["vwap"]):
                ctx["trig_vwap_aligned"] = (mv["direction"] == "bull" and tb["close"] > tb["vwap"]) or \
                                           (mv["direction"] == "bear" and tb["close"] < tb["vwap"])
            else:
                ctx["trig_vwap_aligned"] = False

        # ── During move ──
        if ei <= len(day_rth) and si < ei:
            move_bars = day_rth.iloc[si:ei+1]
            ctx["bars_to_peak"] = pi - si
            if mv["direction"] == "bull":
                drawdowns = (move_bars["high"].cummax() - move_bars["low"]) / max(atr, 0.001)
            else:
                drawdowns = (move_bars["high"] - move_bars["low"].cummin()) / max(atr, 0.001)
            ctx["max_drawdown_atr"] = round(float(drawdowns.max()), 4)
            # Smoothness: how linear is the move? (R² of close prices)
            closes = move_bars["close"].values
            if len(closes) >= 3:
                x = np.arange(len(closes))
                corr = np.corrcoef(x, closes)[0, 1]
                ctx["smoothness"] = round(corr ** 2, 4) if not np.isnan(corr) else 0.0
            else:
                ctx["smoothness"] = 1.0
        else:
            ctx["bars_to_peak"] = 0
            ctx["max_drawdown_atr"] = 0.0
            ctx["smoothness"] = 1.0

        # ── Post-move (6/12/24 bars after end) ──
        for lookback in [6, 12, 24]:
            post_end = min(len(day_rth), ei + lookback + 1)
            post_bars = day_rth.iloc[ei:post_end]
            if len(post_bars) >= 2:
                peak_p = mv["peak_price"]
                if mv["direction"] == "bull":
                    worst = post_bars["low"].min()
                    retrace = (peak_p - worst) / max(atr, 0.001)
                else:
                    worst = post_bars["high"].max()
                    retrace = (worst - peak_p) / max(atr, 0.001)
                ctx[f"retracement_{lookback}bar"] = round(float(retrace), 4)
            else:
                ctx[f"retracement_{lookback}bar"] = np.nan

        # Continuation flag: does price continue past peak within 24 bars?
        post_24 = day_rth.iloc[ei:min(len(day_rth), ei + 25)]
        if len(post_24) > 0:
            if mv["direction"] == "bull":
                ctx["continuation_flag"] = bool(post_24["high"].max() > mv["peak_price"])
            else:
                ctx["continuation_flag"] = bool(post_24["low"].min() < mv["peak_price"])
        else:
            ctx["continuation_flag"] = False

        # ── Level context ──
        day_levels = levels.get(sym, {}).get(date, {})
        if day_levels and atr > 0:
            move_start_price = mv["start_price"]
            move_time = mv["start_time"]
            # Filter ORB levels by time
            available_levels = {}
            for lname, lprice in day_levels.items():
                if "ORB" in lname:
                    if hasattr(move_time, 'time'):
                        mt = move_time.time() if hasattr(move_time, 'time') else move_time
                    else:
                        mt = dtime(10, 1)  # default to after ORB
                    if isinstance(mt, dtime) and mt < ORB_END:
                        continue  # ORB not yet available
                available_levels[lname] = lprice

            if available_levels:
                dists = {k: abs(move_start_price - v) / atr for k, v in available_levels.items()}
                nearest = min(dists, key=dists.get)
                ctx["nearest_level_type"] = nearest
                ctx["nearest_level_dist_atr"] = round(dists[nearest], 4)

                # Level interaction: did move break through or bounce?
                nearest_price = available_levels[nearest]
                if dists[nearest] < 0.10:  # Within 0.1 ATR = at the level
                    if mv["direction"] == "bull" and mv["peak_price"] > nearest_price + 0.05 * atr:
                        ctx["level_interaction"] = "broke_through"
                    elif mv["direction"] == "bear" and mv["peak_price"] < nearest_price - 0.05 * atr:
                        ctx["level_interaction"] = "broke_through"
                    else:
                        ctx["level_interaction"] = "bounced_off"
                else:
                    ctx["level_interaction"] = "no_interaction"

                # Levels within 0.5 ATR
                close_levels = {k: v for k, v in dists.items() if v <= 0.5}
                ctx["levels_within_05"] = ",".join(sorted(close_levels.keys())) if close_levels else ""
                ctx["n_levels_within_05"] = len(close_levels)
            else:
                ctx["nearest_level_type"] = ""
                ctx["nearest_level_dist_atr"] = np.nan
                ctx["level_interaction"] = "no_levels"
                ctx["levels_within_05"] = ""
                ctx["n_levels_within_05"] = 0
        else:
            ctx["nearest_level_type"] = ""
            ctx["nearest_level_dist_atr"] = np.nan
            ctx["level_interaction"] = "no_levels"
            ctx["levels_within_05"] = ""
            ctx["n_levels_within_05"] = 0

        # ── Day context ──
        ctx["day_of_week"] = pd.Timestamp(date).dayofweek  # 0=Mon
        # Gap
        if si < len(day_rth):
            today_open = day_rth.iloc[0]["open"]
            pd_close = day_levels.get("PD Close")
            if pd_close and pd_close > 0:
                gap = (today_open - pd_close) / pd_close * 100
                ctx["gap_direction"] = "up" if gap > 0.05 else ("down" if gap < -0.05 else "flat")
                ctx["gap_magnitude_atr"] = round(abs(today_open - pd_close) / max(atr, 0.001), 4)
            else:
                ctx["gap_direction"] = "unknown"
                ctx["gap_magnitude_atr"] = 0.0

        enriched_rows.append(ctx)

    # Merge context into moves_df
    ctx_df = pd.DataFrame(enriched_rows, index=moves_df.index)
    result = pd.concat([moves_df, ctx_df], axis=1)
    return result


# ── Task 5: Cross-Symbol Analysis & Classification ────────────────────────────

def cross_symbol_analysis(moves_df, data_5m):
    """Add SPY context and concurrent-symbol counts."""
    if moves_df.empty:
        return moves_df

    # SPY direction for each move (5-bar momentum at move start)
    spy_df = data_5m.get("SPY")
    spy_direction_map = {}
    spy_mag_map = {}
    if spy_df is not None:
        spy_rth = spy_df[
            (spy_df["trade_time"] >= RTH_START) & (spy_df["trade_time"] < RTH_END)
        ].set_index("dt_et").sort_index()

        for dt in moves_df["start_time"].unique():
            # Find nearest SPY bar
            idx_loc = spy_rth.index.searchsorted(dt)
            if idx_loc >= 5 and idx_loc < len(spy_rth):
                c_now = spy_rth.iloc[idx_loc]["close"]
                c_5ago = spy_rth.iloc[idx_loc - 5]["close"]
                atr_spy = spy_rth.iloc[idx_loc]["atr14"]
                if atr_spy > 0:
                    mom = (c_now - c_5ago) / atr_spy
                    spy_direction_map[dt] = "bull" if mom > 0.05 else ("bear" if mom < -0.05 else "neutral")
                    spy_mag_map[dt] = round(mom, 4)

    moves_df["spy_direction"] = moves_df["start_time"].map(spy_direction_map).fillna("unknown")
    moves_df["spy_magnitude_atr"] = moves_df["start_time"].map(spy_mag_map).fillna(0.0)

    # Concurrent symbols: count moves starting within same 15-min bucket + direction
    # Vectorized approach using time buckets instead of O(n²) pairwise comparison
    moves_df["concurrent_symbols"] = 0
    moves_df["is_broad_move"] = False

    if len(moves_df) > 0:
        # Create 15-min time buckets
        st = pd.to_datetime(moves_df["start_time"], utc=True)
        moves_df["_time_bucket"] = st.dt.floor("15min")

        # Count unique symbols per (bucket, direction) — excluding self
        bucket_counts = moves_df.groupby(["_time_bucket", "direction"])["symbol"].transform("nunique") - 1
        moves_df["concurrent_symbols"] = bucket_counts.clip(lower=0)
        moves_df["is_broad_move"] = moves_df["concurrent_symbols"] >= 4
        moves_df.drop(columns=["_time_bucket"], inplace=True)

    return moves_df


def classify_moves(moves_df):
    """Add 5 category columns."""
    if moves_df.empty:
        return moves_df

    # Magnitude category
    moves_df["mag_category"] = pd.cut(
        moves_df["magnitude_atr"],
        bins=[0, 0.5, 1.0, 2.0, float("inf")],
        labels=["small", "medium", "large", "mega"],
        right=False
    )

    # Speed category
    moves_df["speed_category"] = pd.cut(
        moves_df["duration_bars"],
        bins=[0, 5, 12, float("inf")],
        labels=["explosive", "steady", "grinding"],
        right=False
    )

    # Timing category
    def get_timing(t):
        if hasattr(t, "time"):
            t = t.time()
        if t < dtime(9, 45):
            return "open_flush"
        if t < dtime(11, 0):
            return "morning"
        if t < dtime(13, 0):
            return "midday"
        return "afternoon"

    moves_df["timing_category"] = moves_df["start_time"].apply(get_timing)

    # Pattern category (priority-based classification)
    def classify_pattern(row):
        timing = row.get("timing_category", "")
        gap_dir = row.get("gap_direction", "unknown")
        level_int = row.get("level_interaction", "")
        nearest_dist = row.get("nearest_level_dist_atr", np.nan)
        direction = row["direction"]

        # Gap patterns (open only)
        if timing == "open_flush" and gap_dir != "unknown":
            if (gap_dir == "up" and direction == "bull") or (gap_dir == "down" and direction == "bear"):
                return "gap_continuation"
            elif (gap_dir == "up" and direction == "bear") or (gap_dir == "down" and direction == "bull"):
                return "gap_reversal"

        # Level patterns
        if not np.isnan(nearest_dist) and nearest_dist < 0.3:
            if level_int == "broke_through":
                return "level_breakout"
            elif level_int == "bounced_off":
                return "level_bounce"

        # Reversal: move against prior EMA trend
        ema_pos = row.get("pre_ema21_position", "")
        if (direction == "bull" and ema_pos == "below") or (direction == "bear" and ema_pos == "above"):
            return "reversal"

        # Trend continuation: move with EMA
        if (direction == "bull" and ema_pos == "above") or (direction == "bear" and ema_pos == "below"):
            return "trend_continuation"

        return "unclassified"

    moves_df["pattern_category"] = moves_df.apply(classify_pattern, axis=1)

    # Context category
    def get_context(row):
        cs = row.get("concurrent_symbols", 0)
        if cs >= 4:
            return "broad_move"
        if cs >= 2:
            return "sector_move"
        return "isolated"

    moves_df["context_category"] = moves_df.apply(get_context, axis=1)

    return moves_df


# ── Task 6: Export & Stats Report ─────────────────────────────────────────────

# ── High-Resolution Enrichment ────────────────────────────────────────────────

HIGHRES_SUFFIX_1M = "_1_min_ib.parquet"

def load_highres():
    """Load 1m bars for all symbols. Returns dict[symbol] → DataFrame."""
    data = {}
    for sym in SYMBOLS:
        fp = CACHE / f"{sym.lower()}{HIGHRES_SUFFIX_1M}"
        if not fp.exists():
            continue
        df = pd.read_parquet(fp)
        if df["date"].dt.tz is None:
            df["dt_et"] = df["date"].dt.tz_localize(ET)
        else:
            df["dt_et"] = df["date"].dt.tz_convert(ET)
        df["trade_date"] = df["dt_et"].dt.date
        df["trade_time"] = df["dt_et"].dt.time
        df = df.sort_values("dt_et").reset_index(drop=True)
        data[sym] = df
    return data


def enrich_highres(moves_df):
    """Enrich 5m-detected moves with 1m precision data.

    For each move, loads 1m bars around the move and computes:
    - mfe_1m: true max favorable excursion at 1m
    - mae_1m: true max adverse excursion at 1m
    - bars_to_mfe_1m: exact bars to peak at 1m
    - first_1m_body_pct: trigger bar body % at 1m
    - first_1m_vol_ratio: trigger bar volume ratio at 1m
    - entry_delay_1m: how many 1m bars into the 5m bar the move really starts
    - pre_compression_1m: range contraction in 5 bars before
    - post_peak_retracement_1m: retracement 6 bars after peak
    """
    if moves_df.empty:
        return moves_df

    print("  Loading 1m data...")
    hr_data = load_highres()
    if not hr_data:
        print("  WARNING: No 1m data found, skipping enrichment")
        return moves_df

    loaded_syms = set(hr_data.keys())
    print(f"  {len(loaded_syms)} symbols loaded for 1m enrichment")

    # Pre-index high-res data by (symbol, date) for fast access
    hr_by_day = {}
    for sym, df in hr_data.items():
        for d, grp in df.groupby("trade_date"):
            rth = grp[(grp["trade_time"] >= RTH_START) & (grp["trade_time"] < RTH_END)]
            if len(rth) > 0:
                hr_by_day[(sym, d)] = rth.sort_values("dt_et").reset_index(drop=True)

    total = len(moves_df)
    checkpoint = max(1, total // 20)
    enriched = []

    for idx, mv in moves_df.iterrows():
        if idx % checkpoint == 0 and idx > 0:
            print(f"    1m enriching {idx}/{total} ({idx*100//total}%)...")

        sym = mv["symbol"]
        date = mv["date"]
        atr = mv["atr"]
        ctx = {}

        day_hr = hr_by_day.get((sym, date))
        if day_hr is None or atr <= 0:
            enriched.append(ctx)
            continue

        # Find high-res bars within the move's time window
        st = mv["start_time"]
        et = mv["end_time"]
        pt = mv["peak_time"]

        if hasattr(st, "tzinfo") and st.tzinfo is not None:
            # Ensure timezone-aware comparison
            hr_times = day_hr["dt_et"]
        else:
            hr_times = day_hr["dt_et"].dt.tz_localize(None)

        # Window: 5 min before start to 30 min after end
        pre_window = st - timedelta(minutes=5)
        post_window = et + timedelta(minutes=30)
        mask = (day_hr["dt_et"] >= pre_window) & (day_hr["dt_et"] <= post_window)
        window = day_hr[mask].reset_index(drop=True)

        if len(window) < 3:
            enriched.append(ctx)
            continue

        # Find bars within the move itself
        move_mask = (day_hr["dt_et"] >= st) & (day_hr["dt_et"] <= et)
        move_bars = day_hr[move_mask].reset_index(drop=True)

        if len(move_bars) < 1:
            enriched.append(ctx)
            continue

        H = move_bars["high"].values
        L = move_bars["low"].values
        C = move_bars["close"].values
        O = move_bars["open"].values
        V = move_bars["volume"].values

        # ── MFE / MAE at high-res ──
        # Entry price = close of the first high-res bar (realistic entry, not the perfect extremum)
        entry_price = float(C[0])
        if mv["direction"] == "bull":
            mfe = (H.max() - entry_price) / atr
            mae = (entry_price - L.min()) / atr  # worst dip below entry
            peak_idx = int(np.argmax(H))
        else:
            mfe = (entry_price - L.min()) / atr
            mae = (H.max() - entry_price) / atr  # worst spike above entry
            peak_idx = int(np.argmin(L))

        ctx["mfe_1m"] = round(float(mfe), 4)
        ctx["mae_1m"] = round(float(mae), 4)
        ctx["bars_to_mfe_1m"] = peak_idx

        # ── Trigger bar at high-res ──
        tb = move_bars.iloc[0]
        rng = tb["high"] - tb["low"]
        body = abs(tb["close"] - tb["open"])
        ctx["first_1m_body_pct"] = round(body / max(rng, 0.001) * 100, 1)

        # Volume ratio for trigger bar
        pre_bars = day_hr[day_hr["dt_et"] < st].tail(20)
        if len(pre_bars) >= 5:
            vol_avg = pre_bars["volume"].mean()
            ctx["first_1m_vol_ratio"] = round(tb["volume"] / max(vol_avg, 1), 2)
        else:
            ctx["first_1m_vol_ratio"] = np.nan

        # ── Entry precision: how many HR bars into the 5m bar ──
        # Find first HR bar where move direction is established
        if len(move_bars) >= 2:
            if mv["direction"] == "bull":
                # First bar where close > open (bullish)
                bull_bars = move_bars[move_bars["close"] > move_bars["open"]]
                if len(bull_bars) > 0:
                    ctx["entry_delay_1m"] = int(bull_bars.index[0])
                else:
                    ctx["entry_delay_1m"] = 0
            else:
                bear_bars = move_bars[move_bars["close"] < move_bars["open"]]
                if len(bear_bars) > 0:
                    ctx["entry_delay_1m"] = int(bear_bars.index[0])
                else:
                    ctx["entry_delay_1m"] = 0
        else:
            ctx["entry_delay_1m"] = 0

        # ── Pre-move compression at HR ──
        pre_5 = day_hr[day_hr["dt_et"] < st].tail(5)
        if len(pre_5) >= 3:
            ranges = (pre_5["high"] - pre_5["low"]).values
            ctx["pre_compression_1m"] = round(float(ranges[-1] / max(ranges[0], 0.001)), 4)
        else:
            ctx["pre_compression_1m"] = np.nan

        # ── Post-peak retracement at HR ──
        post_peak_mask = day_hr["dt_et"] > day_hr["dt_et"].iloc[0] + timedelta(minutes=peak_idx)
        post_peak_bars = day_hr[post_peak_mask].head(12)
        if len(post_peak_bars) >= 2:
            if mv["direction"] == "bull":
                peak_price = H.max()
                retrace = (peak_price - post_peak_bars["low"].min()) / atr
            else:
                peak_price = L.min()
                retrace = (post_peak_bars["high"].max() - peak_price) / atr
            ctx["post_peak_retracement_1m"] = round(float(retrace), 4)
        else:
            ctx["post_peak_retracement_1m"] = np.nan

        # ── Move smoothness at HR (R² of close prices) ──
        if len(C) >= 5:
            x = np.arange(len(C))
            corr = np.corrcoef(x, C)[0, 1]
            ctx["smoothness_1m"] = round(corr ** 2, 4) if not np.isnan(corr) else np.nan
        else:
            ctx["smoothness_1m"] = np.nan

        enriched.append(ctx)

    # Merge into moves_df
    ctx_df = pd.DataFrame(enriched, index=moves_df.index)
    result = pd.concat([moves_df, ctx_df], axis=1)

    # Coverage stats
    if "mfe_1m" in result.columns:
        coverage = result["mfe_1m"].notna().sum()
        print(f"  1m enrichment: {coverage}/{total} moves covered ({coverage*100//total}%)")

    return result


def export_results(moves_df):
    """Write parquet, CSV summary, and stats markdown."""
    prefix = OUTPUT_PREFIX[RESOLUTION]
    # 1. Parquet
    parquet_path = OUT_DIR / f"{prefix}move-catalog.parquet"
    # Convert problematic columns for parquet
    df_out = moves_df.copy()
    # Ensure start_time/end_time/peak_time are proper timestamps
    for col in ["start_time", "end_time", "peak_time"]:
        if col in df_out.columns:
            df_out[col] = pd.to_datetime(df_out[col], utc=True)
    # Convert category columns to string
    for col in ["mag_category", "speed_category"]:
        if col in df_out.columns:
            df_out[col] = df_out[col].astype(str)
    df_out.to_parquet(parquet_path, index=False)
    print(f"  → {parquet_path} ({len(df_out)} rows, {len(df_out.columns)} cols)")

    # 2. CSV summary (first 1000 rows)
    csv_path = OUT_DIR / f"{prefix}move-catalog-summary.csv"
    df_out.head(1000).to_csv(csv_path, index=False)
    print(f"  → {csv_path}")

    # 3. Stats markdown
    stats_path = OUT_DIR / f"{prefix}move-catalog-stats.md"
    write_stats_report(moves_df, stats_path)
    print(f"  → {stats_path}")


def write_stats_report(df, path):
    """Write comprehensive stats markdown."""
    if df.empty or "pass" not in df.columns:
        with open(path, "w") as f:
            f.write("# KLB Move Catalog — Stats Report\n\nNo data available.\n")
        return
    primary = df[df["pass"] == "primary"]
    large = df[df["pass"] == "large"]

    lines = [
        "# KLB Move Catalog — Stats Report",
        f"\nGenerated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Dataset Summary",
        f"- **Symbols:** {df['symbol'].nunique()} ({', '.join(sorted(df['symbol'].unique()))})",
        f"- **Date range:** {df['date'].min()} to {df['date'].max()}",
        f"- **Trading days:** {df['date'].nunique()}",
        f"- **Primary moves (≥0.30 ATR):** {len(primary):,}",
        f"- **Large moves (≥1.00 ATR):** {len(large):,}",
        f"- **Total rows:** {len(df):,}",
        f"- **Columns:** {len(df.columns)}",
        "",
    ]

    # Distribution by symbol
    lines.append("## Moves by Symbol")
    lines.append("| Symbol | Primary | Large | Avg Mag | Avg Duration |")
    lines.append("|--------|---------|-------|---------|-------------|")
    for sym in sorted(df["symbol"].unique()):
        p = primary[primary["symbol"] == sym]
        l = large[large["symbol"] == sym]
        avg_mag = f"{p['magnitude_atr'].mean():.2f}" if len(p) > 0 else "—"
        avg_dur = f"{p['duration_bars'].mean():.1f}" if len(p) > 0 else "—"
        lines.append(f"| {sym} | {len(p):,} | {len(l):,} | {avg_mag} | {avg_dur} |")
    lines.append("")

    # Magnitude distribution
    if "mag_category" in df.columns:
        lines.append("## Magnitude Distribution (Primary)")
        for cat in ["small", "medium", "large", "mega"]:
            n = len(primary[primary["mag_category"] == cat])
            pct = n / max(len(primary), 1) * 100
            lines.append(f"- **{cat}:** {n:,} ({pct:.1f}%)")
        lines.append("")

    # Speed distribution
    if "speed_category" in df.columns:
        lines.append("## Speed Distribution (Primary)")
        for cat in ["explosive", "steady", "grinding"]:
            n = len(primary[primary["speed_category"] == cat])
            pct = n / max(len(primary), 1) * 100
            lines.append(f"- **{cat}:** {n:,} ({pct:.1f}%)")
        lines.append("")

    # Timing distribution
    if "timing_category" in df.columns:
        lines.append("## Timing Distribution (Primary)")
        for cat in ["open_flush", "morning", "midday", "afternoon"]:
            n = len(primary[primary["timing_category"] == cat])
            pct = n / max(len(primary), 1) * 100
            lines.append(f"- **{cat}:** {n:,} ({pct:.1f}%)")
        lines.append("")

    # Pattern distribution
    if "pattern_category" in df.columns:
        lines.append("## Pattern Distribution (Primary)")
        lines.append("| Pattern | Count | % | Avg Magnitude |")
        lines.append("|---------|-------|---|---------------|")
        for cat in primary["pattern_category"].value_counts().index:
            subset = primary[primary["pattern_category"] == cat]
            n = len(subset)
            pct = n / max(len(primary), 1) * 100
            avg_m = subset["magnitude_atr"].mean()
            lines.append(f"| {cat} | {n:,} | {pct:.1f}% | {avg_m:.3f} |")
        lines.append("")

    # Context distribution
    if "context_category" in df.columns:
        lines.append("## Market Context (Primary)")
        for cat in ["broad_move", "sector_move", "isolated"]:
            n = len(primary[primary["context_category"] == cat])
            pct = n / max(len(primary), 1) * 100
            lines.append(f"- **{cat}:** {n:,} ({pct:.1f}%)")
        lines.append("")

    # Level interaction
    if "level_interaction" in df.columns:
        lines.append("## Level Interaction (Primary)")
        for cat in primary["level_interaction"].value_counts().index:
            n = len(primary[primary["level_interaction"] == cat])
            pct = n / max(len(primary), 1) * 100
            lines.append(f"- **{cat}:** {n:,} ({pct:.1f}%)")
        lines.append("")

    # Nearest level types
    if "nearest_level_type" in primary.columns:
        lines.append("## Most Common Nearest Levels (Primary, top 10)")
        level_counts = primary[primary["nearest_level_type"] != ""]["nearest_level_type"].value_counts().head(10)
        for ltype, cnt in level_counts.items():
            lines.append(f"- **{ltype}:** {cnt:,}")
        lines.append("")

    # Time-of-day coverage (hourly buckets)
    lines.append("## Moves per Hour (Primary)")
    lines.append("| Hour | Count | Avg Magnitude |")
    lines.append("|------|-------|---------------|")
    if len(primary) > 0:
        primary_copy = primary.copy()
        primary_copy["hour"] = primary_copy["start_time"].apply(
            lambda t: t.hour if hasattr(t, 'hour') else 0
        )
        for h in range(9, 16):
            subset = primary_copy[primary_copy["hour"] == h]
            if len(subset) > 0:
                lines.append(f"| {h:02d}:00 | {len(subset):,} | {subset['magnitude_atr'].mean():.3f} |")
    lines.append("")

    # Direction split
    lines.append("## Direction Split (Primary)")
    for d in ["bull", "bear"]:
        n = len(primary[primary["direction"] == d])
        pct = n / max(len(primary), 1) * 100
        lines.append(f"- **{d}:** {n:,} ({pct:.1f}%)")
    lines.append("")

    # Cross-reference note
    lines.append("## Comparison with Existing Datasets")
    lines.append("- `enriched-signals.csv`: 1,841 KLB signals (24 days, 13 symbols)")
    lines.append("- `big-moves.csv`: 9,596 significant 5m bars")
    lines.append(f"- **This catalog:** {len(primary):,} primary moves ({df['date'].nunique()} days, {df['symbol'].nunique()} symbols)")
    lines.append("- Join on symbol + overlapping time ranges to see which moves KLB catches/misses")
    lines.append("")

    with open(path, "w") as f:
        f.write("\n".join(lines))


# ── Main ──────────────────────────────────────────────────────────────────────

def get_last_catalog_date():
    """Read existing catalog and return the last date, or None if no catalog."""
    prefix = OUTPUT_PREFIX[RESOLUTION]
    parquet_path = OUT_DIR / f"{prefix}move-catalog.parquet"
    if not parquet_path.exists():
        return None
    try:
        existing = pd.read_parquet(parquet_path, columns=["date"])
        if len(existing) == 0:
            return None
        return existing["date"].max()
    except Exception:
        return None


def filter_data_after(data_5m, data_daily, after_date):
    """Filter data to only include days after after_date (with warmup buffer)."""
    # Keep 30 days before for indicator warmup
    warmup_date = after_date - timedelta(days=45)
    filtered_5m = {}
    filtered_daily = {}

    for sym, df in data_5m.items():
        mask = df["trade_date"] >= warmup_date
        filtered_5m[sym] = df[mask].copy()

    for sym, dd in data_daily.items():
        mask = dd["trade_date"] >= warmup_date
        filtered_daily[sym] = dd[mask].copy()

    return filtered_5m, filtered_daily, after_date


def run_pipeline(data_5m, data_daily, after_date=None):
    """Run the full pipeline. If after_date is set, only process days after it."""

    # Task 1b: Compute indicators
    print("\n[1b/6] Computing indicators...")
    data_5m = compute_indicators(data_5m)
    compute_daily_atr(data_5m, data_daily)
    for sym in list(data_5m.keys())[:3]:
        df = data_5m[sym]
        rth = df[(df["trade_time"] >= RTH_START) & (df["trade_time"] < RTH_END)]
        nan_pct = rth[["atr14", "ema21", "ema50", "adx14", "vwap"]].isna().mean() * 100
        print(f"    {sym} NaN%: {dict(nan_pct.round(1))}")

    # Task 2: Level computation
    print("\n[2/6] Computing levels...")
    levels = compute_levels(data_5m, data_daily)
    total_level_days = sum(len(v) for v in levels.values())
    print(f"  {total_level_days} symbol-day level sets computed")

    # Task 2b: Export levels database (only in 5m mode — levels are resolution-independent)
    levels_path = OUT_DIR / "key-levels-db.parquet"
    if after_date is None and RESOLUTION == "5m":
        # Full 5m mode: export all levels
        print("\n[2b/6] Exporting levels database...")
        export_levels(levels, data_5m)
    elif RESOLUTION != "5m":
        print("\n[2b/6] Skipping levels export (using existing 5m levels)")
        pass  # Levels are independent of detection resolution
    elif levels_path.exists():
        # Incremental: merge new levels with existing
        print("\n[2b/6] Merging new levels into database...")
        new_levels_df = []
        for sym in sorted(levels.keys()):
            for date in sorted(levels[sym].keys()):
                if date > after_date:
                    df = data_5m.get(sym)
                    day_bars = df[df["trade_date"] == date] if df is not None else None
                    rth = day_bars[(day_bars["trade_time"] >= RTH_START) & (day_bars["trade_time"] < RTH_END)] if day_bars is not None else None
                    datr = float(rth["daily_atr"].iloc[0]) if rth is not None and len(rth) > 0 and not np.isnan(rth["daily_atr"].iloc[0]) else None
                    for lname, lprice in levels[sym][date].items():
                        zone_half = (datr * 0.03 if "High" in lname or "Low" in lname else datr * 0.02) if datr else 0.0
                        new_levels_df.append({
                            "symbol": sym, "date": date, "level_name": lname,
                            "level_price": round(lprice, 4),
                            "zone_high": round(lprice + zone_half, 4),
                            "zone_low": round(lprice - zone_half, 4),
                            "zone_width": round(zone_half * 2, 4),
                            "daily_atr": round(datr, 4) if datr else None,
                        })
        if new_levels_df:
            existing_levels = pd.read_parquet(levels_path)
            new_df = pd.DataFrame(new_levels_df)
            merged = pd.concat([existing_levels, new_df], ignore_index=True)
            merged.to_parquet(levels_path, index=False)
            print(f"  Added {len(new_df)} new level rows → {len(merged)} total")
        else:
            print("  No new levels to add")

    # For incremental: filter data to only process new days for moves
    if after_date is not None:
        for sym in list(data_5m.keys()):
            df = data_5m[sym]
            data_5m[sym] = df[df["trade_date"] > after_date].copy()
            # Also filter levels
            if sym in levels:
                levels[sym] = {d: v for d, v in levels[sym].items() if d > after_date}

    # Task 3: Move detection
    print("\n[3/6] Detecting moves...")
    moves_df = detect_moves(data_5m)
    print(f"  Total: {len(moves_df)} moves")
    if len(moves_df) > 0:
        primary = moves_df[moves_df["pass"] == "primary"]
        large = moves_df[moves_df["pass"] == "large"]
        print(f"  Primary: {len(primary)}, Large: {len(large)}")

    # Task 4: Enrichment
    print("\n[4/6] Enriching context...")
    moves_df = enrich_context(moves_df, data_5m, levels)
    if len(moves_df) > 0:
        nan_counts = moves_df.isna().sum()
        high_nan = nan_counts[nan_counts > len(moves_df) * 0.5]
        if len(high_nan) > 0:
            print(f"  WARNING: columns >50% NaN: {dict(high_nan)}")
        else:
            print("  No columns >50% NaN")

    # Task 5: Cross-symbol + classification
    print("\n[5/6] Cross-symbol analysis & classification...")
    moves_df = cross_symbol_analysis(moves_df, data_5m)
    moves_df = classify_moves(moves_df)

    return moves_df


def main():
    global RESOLUTION
    t0 = time_mod.time()
    full_rebuild = "--full" in sys.argv

    # Parse resolution flag
    if "--resolution" in sys.argv:
        idx = sys.argv.index("--resolution")
        if idx + 1 < len(sys.argv):
            RESOLUTION = sys.argv[idx + 1]
    elif "--1m" in sys.argv:
        RESOLUTION = "1m"

    if RESOLUTION not in ("5m", "1m"):
        print(f"ERROR: Unknown resolution '{RESOLUTION}'. Use '5m' or '1m'.")
        sys.exit(1)

    prefix = OUTPUT_PREFIX[RESOLUTION]
    print("=" * 60)
    mode = "FULL REBUILD" if full_rebuild else "INCREMENTAL"
    print(f"KLB Move Catalog Builder ({mode}, {RESOLUTION})")
    print("=" * 60)

    # Check for existing catalog
    last_date = None if full_rebuild else get_last_catalog_date()
    if last_date is not None:
        print(f"\n  Existing catalog ends at: {last_date}")
        print(f"  Processing new days only...")
    else:
        if not full_rebuild:
            print("\n  No existing catalog found — running full build")

    # Task 1: Load data
    print("\n[1/6] Loading data...")
    data_5m, data_daily = load_data()
    print(f"  Loaded {len(data_5m)} symbols (5m), {len(data_daily)} symbols (daily)")
    for sym in sorted(data_5m):
        df = data_5m[sym]
        rth = df[(df["trade_time"] >= RTH_START) & (df["trade_time"] < RTH_END)]
        print(f"    {sym}: {len(df):,} total bars, {len(rth):,} RTH, "
              f"{df['trade_date'].min()} to {df['trade_date'].max()}")

    # For incremental: filter to recent data only
    after_date = None
    if last_date is not None:
        data_5m, data_daily, after_date = filter_data_after(data_5m, data_daily, last_date)
        print(f"\n  Filtered to data after {after_date} (with warmup buffer)")

    # Run pipeline
    new_moves = run_pipeline(data_5m, data_daily, after_date)

    # Merge with existing catalog if incremental
    if after_date is not None:
        if len(new_moves) == 0:
            print("\n  No new days to process — catalog is up to date.")
            elapsed = time_mod.time() - t0
            print(f"\n{'=' * 60}")
            print(f"Done in {elapsed:.1f}s — no changes")
            print(f"{'=' * 60}")
            return

        parquet_path = OUT_DIR / f"{prefix}move-catalog.parquet"
        existing = pd.read_parquet(parquet_path)
        # Remove any overlapping dates from existing (safety)
        existing = existing[existing["date"] <= after_date]
        # Ensure column compatibility
        for col in new_moves.columns:
            if col not in existing.columns:
                existing[col] = np.nan
        for col in existing.columns:
            if col not in new_moves.columns:
                new_moves[col] = np.nan
        moves_df = pd.concat([existing, new_moves], ignore_index=True)
        print(f"\n  Merged: {len(existing)} existing + {len(new_moves)} new = {len(moves_df)} total")
    else:
        moves_df = new_moves

    # Optional 1m enrichment
    if len(moves_df) > 0 and "--enrich-1m" in sys.argv:
        print("\n[+] Enriching with 1m data...")
        moves_df = enrich_highres(moves_df)

    # Task 6: Export
    print("\n[6/6] Exporting results...")
    export_results(moves_df)

    elapsed = time_mod.time() - t0
    print(f"\n{'=' * 60}")
    print(f"Done in {elapsed:.1f}s — {len(moves_df)} total moves ({len(moves_df.columns)} cols)")
    print(f"{'=' * 60}")


def enrich_only():
    """Standalone mode: load existing catalog and add 1m enrichment columns."""
    global RESOLUTION
    t0 = time_mod.time()

    prefix = OUTPUT_PREFIX[RESOLUTION]
    parquet_path = OUT_DIR / f"{prefix}move-catalog.parquet"
    if not parquet_path.exists():
        print(f"ERROR: No catalog found at {parquet_path}")
        sys.exit(1)

    print("=" * 60)
    print("KLB Move Catalog — 1m Enrichment")
    print("=" * 60)

    print(f"\n  Loading {parquet_path}...")
    moves_df = pd.read_parquet(parquet_path)
    print(f"  {len(moves_df)} moves, {len(moves_df.columns)} existing cols")

    # Drop existing 1m enrichment columns to avoid duplicates on re-enrichment
    hr_cols = [c for c in moves_df.columns if "_1m" in c]
    if hr_cols:
        print(f"  Dropping {len(hr_cols)} existing 1m columns for re-enrichment")
        moves_df = moves_df.drop(columns=hr_cols)

    print("\n[+] Enriching with 1m data...")
    moves_df = enrich_highres(moves_df)

    # Re-export
    print("\n  Re-exporting...")
    export_results(moves_df)

    elapsed = time_mod.time() - t0
    print(f"\n{'=' * 60}")
    print(f"Done in {elapsed:.1f}s — {len(moves_df)} moves ({len(moves_df.columns)} cols)")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    if "--enrich-only" in sys.argv:
        enrich_only()
    else:
        main()
