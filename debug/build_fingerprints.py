#!/usr/bin/env python3
"""Build move fingerprints: ~55 new features per move.
Enables clustering, pattern matching, and predictive analysis.
Output: debug/move-fingerprints.parquet (joined to catalog by move_id)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import time

# ── Config ────────────────────────────────────────────────────────────────────
CACHE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/"
             "Meine Ablage/Claude/trading_bot/cache/bars")
DEBUG = Path(__file__).parent
CATALOG_PATH = DEBUG / "move-catalog.parquet"
LEVELS_PATH = DEBUG / "key-levels-db.parquet"
OUTPUT_PATH = DEBUG / "move-fingerprints.parquet"

SYMBOLS = ["SPY","AAPL","AMD","AMZN","GLD","GOOGL","META","MSFT",
           "NFLX","NVDA","QQQ","SLV","TSLA","TSM","XLE"]
TECH = {"AAPL","AMZN","GOOGL","META","MSFT","NVDA","NFLX"}
COMMODITY = {"GLD","SLV","XLE"}


# ── Data Loading ──────────────────────────────────────────────────────────────

def load_5m_with_indicators():
    """Load 5m bars for all symbols, compute indicators."""
    data = {}
    for sym in SYMBOLS:
        fp = CACHE / f"{sym.lower()}_5_mins_ib.parquet"
        if not fp.exists():
            print(f"  WARN: {sym} 5m not found")
            continue
        df = pd.read_parquet(fp)
        if df["date"].dt.tz is not None:
            df["date"] = df["date"].dt.tz_convert("US/Eastern")
        else:
            df["date"] = df["date"].dt.tz_localize("UTC").dt.tz_convert("US/Eastern")
        h = df["date"].dt.hour
        m = df["date"].dt.minute
        df = df[((h == 9) & (m >= 30)) | ((h >= 10) & (h < 16))].copy()
        df = df.sort_values("date").reset_index(drop=True)
        if len(df) == 0:
            continue
        # Indicators
        df["ema21"] = df["close"].ewm(span=21, adjust=False).mean()
        df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
        tr = pd.concat([
            df["high"] - df["low"],
            (df["high"] - df["close"].shift(1)).abs(),
            (df["low"] - df["close"].shift(1)).abs()
        ], axis=1).max(axis=1)
        df["atr14"] = tr.ewm(alpha=1/14, adjust=False).mean()
        df["trade_date"] = df["date"].dt.date
        tp = (df["high"] + df["low"] + df["close"]) / 3
        cum_vol = df.groupby("trade_date")["volume"].cumsum()
        cum_tpv = (tp * df["volume"]).groupby(df["trade_date"]).cumsum()
        df["vwap"] = cum_tpv / cum_vol.replace(0, np.nan)
        # ADX
        plus_dm = df["high"].diff().clip(lower=0)
        minus_dm = (-df["low"].diff()).clip(lower=0)
        cond = plus_dm < minus_dm
        plus_dm[cond] = 0
        minus_dm[~cond] = 0
        atr_s = tr.ewm(alpha=1/14, adjust=False).mean().replace(0, np.nan)
        plus_di = 100 * plus_dm.ewm(alpha=1/14, adjust=False).mean() / atr_s
        minus_di = 100 * minus_dm.ewm(alpha=1/14, adjust=False).mean() / atr_s
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        df["adx"] = dx.ewm(alpha=1/14, adjust=False).mean()
        df["vol_sma20"] = df["volume"].rolling(20, min_periods=1).mean()
        df["vol_ratio"] = df["volume"] / df["vol_sma20"].replace(0, np.nan)
        df["above_ema21"] = df["close"] > df["ema21"]
        df["above_vwap"] = df["close"] > df["vwap"]
        data[sym] = df
    return data


def build_lookups(data_5m):
    """Precompute per-symbol-date numpy arrays for fast lookups."""
    sym_days = {}
    for sym, df in data_5m.items():
        sym_days[sym] = {}
        for date, g in df.groupby("trade_date"):
            g = g.reset_index(drop=True)
            sym_days[sym][str(date)] = {
                "close": g["close"].values,
                "high": g["high"].values,
                "low": g["low"].values,
                "open": g["open"].values,
                "ema21": g["ema21"].values,
                "ema50": g["ema50"].values,
                "vwap": g["vwap"].values.astype(float),
                "adx": g["adx"].values.astype(float),
                "vol_ratio": g["vol_ratio"].values.astype(float),
                "above_ema": g["above_ema21"].values,
                "above_vwap": g["above_vwap"].values,
                "atr14": g["atr14"].values.astype(float),
                "n": len(g),
            }
    return sym_days


def build_breadth_lookup(sym_days):
    """Precompute per-date-bar breadth counts."""
    all_dates = set()
    for sym in sym_days:
        all_dates.update(sym_days[sym].keys())
    breadth = {}
    for d in all_dates:
        max_n = max(
            (sym_days[s][d]["n"] for s in sym_days if d in sym_days[s]),
            default=0)
        if max_n == 0:
            continue
        ema_c = np.zeros(max_n, dtype=int)
        vwap_c = np.zeros(max_n, dtype=int)
        for sym in SYMBOLS:
            if sym not in sym_days or d not in sym_days[sym]:
                continue
            sd = sym_days[sym][d]
            n = sd["n"]
            ema_c[:n] += sd["above_ema"].astype(int)
            vwap_c[:n] += sd["above_vwap"].astype(int)
        breadth[d] = {"ema": ema_c, "vwap": vwap_c}
    return breadth


def build_move_bins(catalog):
    """Bin moves into 5-min buckets for fast concurrent lookups."""
    bins = {}
    for _, row in catalog.iterrows():
        t = row["start_time"]
        mins = (t.hour * 60 + t.minute) - 570
        bucket = mins // 5
        key = (str(row["date"]), bucket)
        if key not in bins:
            bins[key] = []
        bins[key].append({
            "move_id": row["move_id"],
            "symbol": row["symbol"],
            "direction": row["direction"],
            "start_time": t,
        })
    return bins


# ── Feature Groups ────────────────────────────────────────────────────────────

def enrich_prior_moves(catalog):
    """Group 1: Prior move history within same symbol-date (8 features)."""
    cat = catalog.sort_values(["symbol", "date", "start_time"])
    out = {k: [] for k in [
        "move_id", "moves_today_count", "moves_today_bull_pct",
        "cumulative_atr_today", "day_net_atr",
        "prev_move_dir_same", "prev_move_magnitude",
        "prev_move_gap_bars", "prev_move_held"]}

    for (sym, date), group in cat.groupby(["symbol", "date"]):
        dirs = group["direction"].values
        mags = group["magnitude_atr"].values
        si = group["start_idx"].values
        ei = group["end_idx"].values
        ret12 = group["retracement_12bar"].values
        mids = group["move_id"].values
        for i in range(len(group)):
            out["move_id"].append(mids[i])
            out["moves_today_count"].append(i)
            if i > 0:
                bc = sum(1 for d in dirs[:i] if d == "bull")
                out["moves_today_bull_pct"].append(bc / i)
                out["cumulative_atr_today"].append(float(mags[:i].sum()))
                ba = sum(mags[j] for j in range(i) if dirs[j] == "bull")
                be = sum(mags[j] for j in range(i) if dirs[j] == "bear")
                out["day_net_atr"].append(ba - be)
                out["prev_move_dir_same"].append(dirs[i-1] == dirs[i])
                out["prev_move_magnitude"].append(float(mags[i-1]))
                out["prev_move_gap_bars"].append(int(si[i] - ei[i-1]))
                out["prev_move_held"].append(float(ret12[i-1]))
            else:
                out["moves_today_bull_pct"].append(np.nan)
                out["cumulative_atr_today"].append(0.0)
                out["day_net_atr"].append(0.0)
                out["prev_move_dir_same"].append(np.nan)
                out["prev_move_magnitude"].append(np.nan)
                out["prev_move_gap_bars"].append(np.nan)
                out["prev_move_held"].append(np.nan)
    return pd.DataFrame(out)


def enrich_premove_and_volume(catalog, sym_days):
    """Groups 2+3: 12-bar lookback price + volume (13 features)."""
    rows = []
    total = len(catalog)
    for cnt, (_, row) in enumerate(catalog.iterrows()):
        if cnt % 10000 == 0 and cnt > 0:
            print(f"    ...{cnt:,}/{total:,}")
        r = {"move_id": row["move_id"]}
        sym, d = row["symbol"], str(row["date"])
        if sym not in sym_days or d not in sym_days[sym]:
            rows.append(r)
            continue
        sd = sym_days[sym][d]
        si = row["start_idx"]
        if si >= sd["n"]:
            rows.append(r)
            continue
        atr = row["atr"] if row["atr"] > 0 else 1.0
        lb = min(12, si)
        if lb < 3:
            rows.append(r)
            continue
        closes = sd["close"][si-lb:si]
        highs = sd["high"][si-lb:si]
        lows = sd["low"][si-lb:si]
        vols = sd["vol_ratio"][si-lb:si]
        # Price action
        x = np.arange(len(closes))
        r["pre_12bar_trend_slope"] = np.polyfit(x, closes, 1)[0] / atr
        r["pre_12bar_range_atr"] = float((highs.max() - lows.min()) / atr)
        mid = len(closes) // 2
        if mid > 1:
            s1 = np.polyfit(np.arange(mid), closes[:mid], 1)[0]
            s2 = np.polyfit(np.arange(len(closes)-mid), closes[mid:], 1)[0]
            r["pre_6bar_acceleration"] = (s2 - s1) / atr
        move_sign = 1 if row["direction"] == "bull" else -1
        diffs = np.diff(closes)
        same = (diffs * move_sign) > 0
        mx = cur = 0
        for s in same:
            if s: cur += 1; mx = max(mx, cur)
            else: cur = 0
        r["pre_consecutive_same_dir"] = mx
        ranges = highs - lows
        avg_r = ranges.mean()
        r["pre_narrow_bar_count"] = int((ranges < 0.5 * avg_r).sum()) if avg_r > 0 else 0
        e21 = sd["ema21"][si]
        e50 = sd["ema50"][si]
        cl = sd["close"][si]
        if not np.isnan(e21):
            r["pre_ema21_dist_atr"] = (cl - e21) / atr
        if not np.isnan(e50):
            r["pre_ema50_dist_atr"] = (cl - e50) / atr
            r["pre_ema50_position"] = "above" if cl > e50 else "below"
        # Volume
        vc = vols[~np.isnan(vols)]
        if len(vc) > 2:
            sl = np.polyfit(np.arange(len(vc)), vc, 1)[0]
            r["pre_vol_slope"] = sl
            r["pre_vol_spike_count"] = int((vc > 2.0).sum())
            r["pre_vol_dry_count"] = int((vc < 0.5).sum())
            if abs(sl) < 0.02: r["pre_vol_pattern"] = "flat"
            elif sl > 0.05: r["pre_vol_pattern"] = "rising"
            elif sl < -0.05: r["pre_vol_pattern"] = "declining"
            else: r["pre_vol_pattern"] = "flat"
            if vc[-1] > 3.0: r["pre_vol_pattern"] = "spike"
        tv = sd["vol_ratio"][si]
        pa = np.nanmean(vols)
        if pa > 0 and not np.isnan(tv):
            r["trig_vol_vs_pre12"] = tv / pa
        rows.append(r)
    return pd.DataFrame(rows)


def enrich_spy_state(catalog, sym_days):
    """Group 4: SPY full state at move time (8 features)."""
    spy = sym_days.get("SPY", {})
    rows = []
    for _, row in catalog.iterrows():
        r = {"move_id": row["move_id"]}
        d = str(row["date"])
        if d not in spy:
            rows.append(r)
            continue
        sd = spy[d]
        bi = min(row["start_idx"], sd["n"] - 1)
        if bi < 0:
            rows.append(r)
            continue
        sa = sd["atr14"][bi]
        if np.isnan(sa) or sa <= 0: sa = 1.0
        r["spy_ema_aligned"] = bool(sd["above_ema"][bi])
        r["spy_vwap_aligned"] = bool(sd["above_vwap"][bi])
        r["spy_adx"] = float(sd["adx"][bi])
        so = sd["open"][0]
        if so > 0:
            r["spy_intraday_return"] = (sd["close"][bi] - so) / so * 100
        dh = sd["high"][:bi+1].max()
        dl = sd["low"][:bi+1].min()
        r["spy_range_consumed"] = (dh - dl) / sa
        r["spy_vol_ratio"] = float(sd["vol_ratio"][bi])
        if bi >= 5:
            en = sd["ema21"][bi]
            e5 = sd["ema21"][bi-5]
            if not np.isnan(en) and not np.isnan(e5):
                r["spy_ema_slope"] = (en - e5) / sa
        if dh > dl:
            r["spy_range_position"] = (sd["close"][bi] - dl) / (dh - dl)
        rows.append(r)
    return pd.DataFrame(rows)


def enrich_cross_symbol(catalog, sym_days, breadth_lookup, move_bins):
    """Groups 5+6: Market breadth + cross-symbol timing (10 features)."""
    rows = []
    total = len(catalog)
    for cnt, (_, row) in enumerate(catalog.iterrows()):
        if cnt % 10000 == 0 and cnt > 0:
            print(f"    ...{cnt:,}/{total:,}")
        r = {"move_id": row["move_id"]}
        d = str(row["date"])
        bi = row["start_idx"]
        sym = row["symbol"]
        direction = row["direction"]
        # Breadth
        if d in breadth_lookup:
            bl = breadth_lookup[d]
            bii = min(bi, len(bl["ema"]) - 1)
            if bii >= 0:
                r["breadth_above_ema"] = int(bl["ema"][bii])
                r["breadth_above_vwap"] = int(bl["vwap"][bii])
        # Concurrent from bins
        t = row["start_time"]
        mins = (t.hour * 60 + t.minute) - 570
        bucket = mins // 5
        nearby = []
        for b in range(bucket - 3, bucket + 4):
            key = (d, b)
            if key in move_bins:
                nearby.extend(move_bins[key])
        nearby = [m for m in nearby if m["symbol"] != sym]
        bn = sum(1 for m in nearby if m["direction"] == "bull")
        be = sum(1 for m in nearby if m["direction"] == "bear")
        tn = bn + be
        r["breadth_bull_moves_15min"] = bn
        r["breadth_bear_moves_15min"] = be
        r["breadth_net"] = (bn - be) / max(tn, 1)
        same_dir = [m for m in nearby if m["direction"] == direction]
        if len(same_dir) > 0:
            all_t = sorted([m["start_time"] for m in same_dir] + [t])
            rank = all_t.index(t)
            r["leader_score"] = 1.0 - (rank / max(len(all_t) - 1, 1))
        else:
            r["leader_score"] = 0.5
        spy_s = [m for m in same_dir if m["symbol"] == "SPY"]
        r["spy_led"] = bool(len(spy_s) > 0 and spy_s[0]["start_time"] < t)
        r["tech_same_dir_count"] = sum(1 for m in same_dir if m["symbol"] in TECH)
        r["commodity_same_dir_count"] = sum(1 for m in same_dir if m["symbol"] in COMMODITY)
        # Symbol daily bias
        if sym in sym_days and d in sym_days[sym]:
            sd = sym_days[sym][d]
            bii = min(bi, sd["n"] - 1)
            if bii >= 0 and sd["open"][0] > 0:
                r["symbol_daily_bias"] = (sd["close"][bii] - sd["open"][0]) / sd["open"][0] * 100
        rows.append(r)
    return pd.DataFrame(rows)


def enrich_level_context(catalog, levels_db):
    """Group 7: Enhanced level context (8 features)."""
    lvl_idx = {}
    for _, lrow in levels_db.iterrows():
        key = (lrow["symbol"], str(lrow["date"]))
        if key not in lvl_idx:
            lvl_idx[key] = []
        lvl_idx[key].append({"name": lrow["level_name"],
                             "price": lrow["level_price"],
                             "zw": lrow.get("zone_width", np.nan)})
    BRK = {"PM Low","PD Low","Week Low","ORB Low","Week Open","Month Open",
           "PD Last Hr Low","PD Last Hr High"}
    REV_G = {"PM High","PD High","Week High","ORB High","PM Low","PD Low",
             "Week Low","PD Last Hr Low"}
    REV_U = {"PD Mid","Today Open","PD Close"}
    # Pre-group catalog for level_tests_today
    cat_by_key = {}
    for _, row in catalog.iterrows():
        key = (row["symbol"], str(row["date"]))
        if key not in cat_by_key:
            cat_by_key[key] = []
        cat_by_key[key].append((row["start_time"], row["nearest_level_type"]))

    rows = []
    for _, row in catalog.iterrows():
        r = {"move_id": row["move_id"]}
        nt = row.get("nearest_level_type", "")
        price = row["start_price"]
        atr = row["atr"] if row["atr"] > 0 else 1.0
        if nt in REV_U: r["level_type_klb"] = "REV_ungated"
        elif nt in REV_G: r["level_type_klb"] = "REV_gated"
        elif nt in BRK: r["level_type_klb"] = "BRK"
        else: r["level_type_klb"] = "other"
        key = (row["symbol"], str(row["date"]))
        if key not in lvl_idx:
            rows.append(r)
            continue
        levels = lvl_idx[key]
        for lev in levels:
            if lev["name"] == nt and pd.notna(lev["zw"]):
                r["level_zone_width_atr"] = lev["zw"] / atr
                break
        dists = sorted([(abs(price - l["price"]) / atr, l["price"]) for l in levels])
        if len(dists) >= 2:
            r["second_nearest_dist_atr"] = dists[1][0]
            if dists[0][0] > 0.001:
                r["level_sandwich_ratio"] = dists[0][0] / max(dists[1][0], 0.001)
        if dists:
            r["level_approach_from"] = "above" if price > dists[0][1] else "below"
        sups = [d for d, p in dists if p < price]
        ress = [d for d, p in dists if p > price]
        if sups: r["nearest_support_atr"] = sups[0]
        if ress: r["nearest_resistance_atr"] = ress[0]
        # Level tests today
        if key in cat_by_key:
            r["level_tests_today"] = sum(
                1 for t, lt in cat_by_key[key]
                if t < row["start_time"] and lt == nt)
        rows.append(r)
    return pd.DataFrame(rows)


def enrich_intraday(catalog, sym_days):
    """Group 8: Intraday progress (3 features)."""
    rows = []
    for _, row in catalog.iterrows():
        r = {"move_id": row["move_id"]}
        t = row["start_time"]
        if pd.notna(t):
            r["minutes_since_open"] = (t.hour - 9) * 60 + t.minute - 30
        sym, d = row["symbol"], str(row["date"])
        if sym not in sym_days or d not in sym_days[sym]:
            rows.append(r)
            continue
        sd = sym_days[sym][d]
        bi = min(row["start_idx"], sd["n"] - 1)
        if bi < 0:
            rows.append(r)
            continue
        atr = row["atr"] if row["atr"] > 0 else 1.0
        dh = sd["high"][:bi+1].max()
        dl = sd["low"][:bi+1].min()
        if dh > dl:
            r["intraday_range_position"] = (row["start_price"] - dl) / (dh - dl)
        r["daily_atr_consumed"] = (dh - dl) / atr
        rows.append(r)
    return pd.DataFrame(rows)


def enrich_move_shape(catalog, sym_days):
    """Group 9: Move shape DNA (10 features)."""
    rows = []
    for _, row in catalog.iterrows():
        r = {"move_id": row["move_id"]}
        sym, d = row["symbol"], str(row["date"])
        if sym not in sym_days or d not in sym_days[sym]:
            rows.append(r)
            continue
        sd = sym_days[sym][d]
        si, ei, pi = row["start_idx"], row["end_idx"], row["peak_idx"]
        if si >= sd["n"] or ei >= sd["n"] or ei <= si:
            rows.append(r)
            continue
        closes = sd["close"][si:ei+1]
        n = len(closes)
        if n < 2:
            rows.append(r)
            continue
        sp = closes[0]
        mag = (row["peak_price"] - sp) if row["direction"] == "bull" else (sp - row["peak_price"])
        if abs(mag) < 1e-6: mag = 1e-6
        # 5-point trajectory
        idx5 = np.linspace(0, n-1, 5).astype(int)
        traj = closes[idx5]
        tn = (traj - sp) / mag if row["direction"] == "bull" else (sp - traj) / mag
        for j in range(5):
            r[f"shape_5pt_{j}"] = float(tn[j])
        if pi > si:
            r["shape_max_dd_position"] = (pi - si) / max(ei - si, 1)
        third = max(1, n // 3)
        fl = (closes[third] - sp) if row["direction"] == "bull" else (sp - closes[third])
        r["shape_front_loaded"] = fl / mag
        atr = row["atr"] if row["atr"] > 0 else 1.0
        rngs = sd["high"][si:ei+1] - sd["low"][si:ei+1]
        r["shape_pause_count"] = int((rngs < 0.2 * atr).sum())
        diffs = np.diff(closes)
        r["shape_direction_changes"] = int(np.sum(np.diff(np.sign(diffs)) != 0))
        rows.append(r)
    return pd.DataFrame(rows)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    t0 = time.time()
    print("=" * 60)
    print("MOVE FINGERPRINT BUILDER")
    print("=" * 60)

    print("\n[1/4] Loading data...")
    catalog = pd.read_parquet(CATALOG_PATH)
    primary = catalog[catalog["pass"] == "primary"].copy()
    print(f"  Catalog: {len(primary):,} primary moves")
    levels_db = pd.read_parquet(LEVELS_PATH)
    print(f"  Levels: {len(levels_db):,} rows")
    data_5m = load_5m_with_indicators()
    total_bars = sum(len(df) for df in data_5m.values())
    print(f"  5m bars: {len(data_5m)} symbols, {total_bars:,} bars")

    print("\n[2/4] Building lookups...")
    sym_days = build_lookups(data_5m)
    breadth = build_breadth_lookup(sym_days)
    move_bins = build_move_bins(primary)
    print(f"  {len(breadth)} dates, {len(move_bins)} time buckets")
    del data_5m  # free memory

    print("\n[3/4] Computing features...")
    print("  G1: Prior moves...")
    g1 = enrich_prior_moves(primary)
    print(f"    {len(g1.columns)-1} features")

    print("  G2+3: Pre-move + volume...")
    g23 = enrich_premove_and_volume(primary, sym_days)
    print(f"    {len(g23.columns)-1} features")

    print("  G4: SPY state...")
    g4 = enrich_spy_state(primary, sym_days)
    print(f"    {len(g4.columns)-1} features")

    print("  G5+6: Breadth + timing...")
    g56 = enrich_cross_symbol(primary, sym_days, breadth, move_bins)
    print(f"    {len(g56.columns)-1} features")

    print("  G7: Level context...")
    g7 = enrich_level_context(primary, levels_db)
    print(f"    {len(g7.columns)-1} features")

    print("  G8: Intraday...")
    g8 = enrich_intraday(primary, sym_days)
    print(f"    {len(g8.columns)-1} features")

    print("  G9: Move shape...")
    g9 = enrich_move_shape(primary, sym_days)
    print(f"    {len(g9.columns)-1} features")

    print("\n[4/4] Merging and saving...")
    fp = primary[["move_id"]].copy()
    for g in [g1, g23, g4, g56, g7, g8, g9]:
        fp = fp.merge(g, on="move_id", how="left")
        fp = fp.loc[:, ~fp.columns.duplicated()]

    n_feat = len(fp.columns) - 1
    print(f"  {len(fp):,} moves x {n_feat} features")

    nan_pct = fp.select_dtypes(include=[np.number]).isnull().mean()
    high_nan = nan_pct[nan_pct > 0.3].sort_values(ascending=False)
    if len(high_nan) > 0:
        print(f"\n  Columns >30% NaN:")
        for col, pct in high_nan.items():
            print(f"    {col:35s} {pct:.1%}")

    fp.to_parquet(OUTPUT_PATH, index=False)
    sz = OUTPUT_PATH.stat().st_size / 1024 / 1024
    print(f"\n  Saved: {OUTPUT_PATH.name} ({sz:.1f} MB)")

    # Quick stats
    print(f"\n{'='*60}")
    print(f"DONE in {time.time()-t0:.0f}s")
    print(f"{'='*60}")
    numeric = fp.select_dtypes(include=[np.number]).columns.drop("move_id", errors="ignore")
    for col in sorted(numeric)[:25]:
        v = fp[col].dropna()
        if len(v) > 0:
            print(f"  {col:35s}  N={len(v):6,}  u={v.mean():+8.3f}  s={v.std():7.3f}")
    if len(numeric) > 25:
        print(f"  ... and {len(numeric)-25} more")


if __name__ == "__main__":
    main()
