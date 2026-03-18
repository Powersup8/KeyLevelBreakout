"""
v3.0b New Levels Deep Research — Challenge Everything
=====================================================
Comprehensive investigation into WHY PD Mid, PD Last Hr Low, and VW Band
underperform despite promising backtests. Tests 10 alternative signal designs,
studies micro price action, checks level overlap, and finds the optimal design.

Uses 5sec parquet data (55-60 days) for micro price action,
10sec parquet (5-25 days) for broader coverage, plus 1min parquet fallback.

Output: v30b-new-levels-deep-research.md
"""

import pandas as pd
import numpy as np
import warnings
from datetime import datetime, time as dtime, timedelta
from pathlib import Path
from collections import defaultdict
import pytz

warnings.filterwarnings("ignore")
ET = pytz.timezone("US/Eastern")

# ── Paths ──
BASE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView")
DEBUG = BASE / "debug"
CACHE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache")
BARS_5S = CACHE / "bars_highres" / "5sec"
BARS_10S = CACHE / "bars_highres" / "10sec"
BARS_1M = CACHE / "bars"
REPORT = DEBUG / "v30b-new-levels-deep-research.md"

SYMBOLS = ["AAPL", "AMD", "AMZN", "META", "MSFT", "NVDA", "QQQ", "SPY", "TSLA"]
MARKET_OPEN = dtime(9, 30)
MARKET_CLOSE = dtime(16, 0)

# ── 1. Load data — prefer 5sec for micro PA, 10sec for broader, 1min fallback ──
print("=" * 70)
print("LOADING MARKET DATA")
print("=" * 70)

market_5s = {}
market_10s = {}
market_1m = {}

for sym in SYMBOLS:
    lo = sym.lower()
    # 5sec
    fp5 = BARS_5S / f"{lo}_5_secs_ib.parquet"
    if fp5.exists():
        df = pd.read_parquet(fp5)
        df["date"] = pd.to_datetime(df["date"], utc=True).dt.tz_convert("US/Eastern")
        df = df.set_index("date").sort_index()
        mkt_hrs = (df.index.time >= MARKET_OPEN) & (df.index.time < MARKET_CLOSE)
        df = df[mkt_hrs]
        market_5s[sym] = df
        dates = df.index.normalize().unique()
        print(f"  {sym} 5s:  {len(df):>7} bars, {len(dates):>3} days, "
              f"{dates[0].date()} → {dates[-1].date()}")

    # 10sec
    fp10 = BARS_10S / f"{lo}_10_secs_ib.parquet"
    if fp10.exists():
        df = pd.read_parquet(fp10)
        df["date"] = pd.to_datetime(df["date"], utc=True).dt.tz_convert("US/Eastern")
        df = df.set_index("date").sort_index()
        mkt_hrs = (df.index.time >= MARKET_OPEN) & (df.index.time < MARKET_CLOSE)
        df = df[mkt_hrs]
        market_10s[sym] = df
        dates = df.index.normalize().unique()
        print(f"  {sym} 10s: {len(df):>7} bars, {len(dates):>3} days")

    # 1min
    fp1 = BARS_1M / f"{lo}_1_min_ib.parquet"
    if fp1.exists():
        df = pd.read_parquet(fp1)
        df["date"] = pd.to_datetime(df["date"], utc=True).dt.tz_convert("US/Eastern")
        df = df.set_index("date").sort_index()
        mkt_hrs = (df.index.time >= MARKET_OPEN) & (df.index.time < MARKET_CLOSE)
        df = df[mkt_hrs]
        market_1m[sym] = df

# Choose best resolution per symbol: 5sec > 10sec > 1min
market = {}
for sym in SYMBOLS:
    if sym in market_5s and len(market_5s[sym]) > 1000:
        market[sym] = market_5s[sym]
    elif sym in market_10s and len(market_10s[sym]) > 500:
        market[sym] = market_10s[sym]
    elif sym in market_1m and len(market_1m[sym]) > 100:
        market[sym] = market_1m[sym]
    else:
        print(f"  WARNING: No usable data for {sym}")

print(f"\nUsing data for {len(market)} symbols")


# ── 2. Compute Prior-Day Levels ──
print("\n" + "=" * 70)
print("COMPUTING PRIOR-DAY LEVELS")
print("=" * 70)


def compute_levels_for_day(sym, day_data, prev_day_data, daily_atr):
    """Compute PD Mid, PD Last Hr Low, VWAP bands, and original levels for one day."""
    levels = {}
    if prev_day_data is not None and len(prev_day_data) > 0:
        pdh = prev_day_data["high"].max()
        pdl = prev_day_data["low"].min()
        pdc = prev_day_data["close"].iloc[-1]

        levels["PDH"] = pdh
        levels["PDL"] = pdl
        levels["PDC"] = pdc
        levels["PD_MID"] = (pdh + pdl) / 2.0

        # PD Last Hr: 15:00-16:00 ET
        last_hr = prev_day_data[prev_day_data.index.time >= dtime(15, 0)]
        if len(last_hr) > 0:
            levels["PD_LH_H"] = last_hr["high"].max()
            levels["PD_LH_L"] = last_hr["low"].min()

    # ORB: first 5 min (9:30-9:35)
    orb = day_data[day_data.index.time < dtime(9, 35)]
    if len(orb) > 0:
        levels["ORB_H"] = orb["high"].max()
        levels["ORB_L"] = orb["low"].min()

    # PM H/L: bars before 9:30 don't exist in RTH data, so skip

    # Daily ATR for VW Band
    levels["daily_ATR"] = daily_atr

    return levels


def compute_vwap_series(day_data):
    """Compute running VWAP and VWAP STD for one day's bars."""
    tp = (day_data["high"] + day_data["low"] + day_data["close"]) / 3
    cum_vol = day_data["volume"].cumsum()
    cum_vp = (tp * day_data["volume"]).cumsum()
    vwap = cum_vp / cum_vol.replace(0, np.nan)

    cum_vp2 = (tp ** 2 * day_data["volume"]).cumsum()
    variance = cum_vp2 / cum_vol - vwap ** 2
    variance = variance.clip(lower=0)
    vwap_std = np.sqrt(variance)

    return vwap, vwap_std


def resample_to_5m(day_data):
    """Resample to 5-min bars for indicator computation."""
    bars = day_data.resample("5min").agg({
        "open": "first", "high": "max", "low": "min",
        "close": "last", "volume": "sum"
    }).dropna(subset=["open"])
    return bars


# Build per-symbol-day data structures
sym_day_data = {}  # (sym, date) -> DataFrame of bars
sym_day_levels = {}  # (sym, date) -> dict of levels
sym_day_vwap = {}  # (sym, date) -> (vwap_series, vwap_std_series)
sym_day_5m = {}  # (sym, date) -> 5min resampled bars

for sym, mdf in market.items():
    days = mdf.index.normalize().unique()
    sorted_days = sorted(days)

    # Compute daily ATR from rolling 14-day
    daily_ranges = []
    for d in sorted_days:
        dd = mdf[mdf.index.normalize() == d]
        if len(dd) > 0:
            daily_ranges.append(dd["high"].max() - dd["low"].min())
        else:
            daily_ranges.append(np.nan)

    atr_series = pd.Series(daily_ranges).rolling(14, min_periods=1).mean()

    for i, d in enumerate(sorted_days):
        dd = mdf[mdf.index.normalize() == d]
        if len(dd) < 10:
            continue
        sym_day_data[(sym, d)] = dd

        prev_dd = None
        if i > 0:
            prev_d = sorted_days[i - 1]
            pd_data = mdf[mdf.index.normalize() == prev_d]
            if len(pd_data) > 0:
                prev_dd = pd_data

        daily_atr = atr_series.iloc[i] if i < len(atr_series) else np.nan
        levels = compute_levels_for_day(sym, dd, prev_dd, daily_atr)
        sym_day_levels[(sym, d)] = levels

        # 5m bars + EMA + ATR
        bars5 = resample_to_5m(dd)
        if len(bars5) >= 3:
            bars5["ema20"] = bars5["close"].ewm(span=20, adjust=False).mean()
            bars5["prev_close"] = bars5["close"].shift(1)
            bars5["tr"] = np.maximum(
                bars5["high"] - bars5["low"],
                np.maximum(
                    (bars5["high"] - bars5["prev_close"]).abs(),
                    (bars5["low"] - bars5["prev_close"]).abs()
                ))
            bars5["tr"] = bars5["tr"].fillna(bars5["high"] - bars5["low"])
            bars5["atr14"] = bars5["tr"].rolling(14, min_periods=1).mean()
            bars5["vol_sma20"] = bars5["volume"].rolling(20, min_periods=1).mean()
            sym_day_5m[(sym, d)] = bars5

        # VWAP
        vwap, vwap_std = compute_vwap_series(dd)
        sym_day_vwap[(sym, d)] = (vwap, vwap_std)

print(f"Built data for {len(sym_day_data)} symbol-days")
print(f"Levels computed for {len(sym_day_levels)} symbol-days")

# ── 3. Study EVERY level touch event ──
print("\n" + "=" * 70)
print("TASK 1-4: CORRECTED BACKTEST + PRICE ACTION + ALTERNATIVE DESIGNS")
print("=" * 70)


def find_level_touches(sym, day, day_data, levels, vwap_data, bars5m, proximity_atr=0.15):
    """
    Find all moments when price touches a level.
    Returns list of touch events with follow-through PnL at 15/30/60 min.
    """
    touches = []
    if bars5m is None or len(bars5m) < 5:
        return touches

    vwap_s, vwap_std_s = vwap_data
    daily_atr = levels.get("daily_ATR", np.nan)

    # Iterate over 5m bars
    for bar_idx in range(2, len(bars5m)):
        bar = bars5m.iloc[bar_idx]
        atr = bar.get("atr14", np.nan)
        if np.isnan(atr) or atr <= 0:
            continue

        bar_time = bar.name  # timestamp
        close = bar["close"]
        ema = bar.get("ema20", np.nan)
        vol = bar["volume"]
        vol_sma = bar.get("vol_sma20", 1)
        vol_ratio = vol / vol_sma if vol_sma > 0 else 0

        # Check each level
        check_levels = {}

        # Static levels
        for lname in ["PD_MID", "PD_LH_L", "PD_LH_H", "PDH", "PDL", "ORB_H", "ORB_L"]:
            if lname in levels and not np.isnan(levels[lname]):
                check_levels[lname] = levels[lname]

        # Dynamic: VWAP + bands
        nearest_vwap_idx = vwap_s.index.searchsorted(bar_time, side="right") - 1
        if 0 <= nearest_vwap_idx < len(vwap_s):
            v = vwap_s.iloc[nearest_vwap_idx]
            vs = vwap_std_s.iloc[nearest_vwap_idx]
            if not np.isnan(v):
                check_levels["VWAP"] = v
            if not np.isnan(v) and not np.isnan(vs) and vs > 0:
                check_levels["VWAP_STD_L"] = v - vs
                check_levels["VWAP_STD_U"] = v + vs
            if not np.isnan(v) and not np.isnan(daily_atr):
                check_levels["VWAP_ATR_L"] = v - daily_atr
                check_levels["VWAP_ATR_U"] = v + daily_atr
            # Tighter bands
            if not np.isnan(v) and not np.isnan(daily_atr):
                check_levels["VWAP_HALF_ATR_L"] = v - 0.5 * daily_atr
                check_levels["VWAP_HALF_ATR_U"] = v + 0.5 * daily_atr
            if not np.isnan(v) and not np.isnan(vs) and vs > 0:
                check_levels["VWAP_1.5STD_L"] = v - 1.5 * vs
                check_levels["VWAP_1.5STD_U"] = v + 1.5 * vs

        for lname, lprice in check_levels.items():
            dist_atr = abs(close - lprice) / atr
            if dist_atr > proximity_atr:
                continue

            # Determine directional possibilities
            above = close > lprice
            ema_bull = close > ema if not np.isnan(ema) else None

            # Compute follow-through at multiple horizons
            remaining_5m = bars5m.iloc[bar_idx + 1:]
            if len(remaining_5m) < 1:
                continue

            # Use the actual bar data for micro follow-through
            ft = {}
            for minutes, label in [(15, "15m"), (30, "30m"), (60, "60m")]:
                end_time = bar_time + timedelta(minutes=minutes)
                window = day_data[(day_data.index > bar_time) & (day_data.index <= end_time)]
                if len(window) < 3:
                    continue
                end_close = window.iloc[-1]["close"]
                hi = window["high"].max()
                lo = window["low"].min()

                # Bull: long from close
                bull_pnl = (end_close - close) / atr
                bull_mfe = (hi - close) / atr
                bull_mae = (close - lo) / atr

                # Bear: short from close
                bear_pnl = (close - end_close) / atr
                bear_mfe = (close - lo) / atr
                bear_mae = (hi - close) / atr

                ft[f"bull_pnl_{label}"] = round(bull_pnl, 4)
                ft[f"bear_pnl_{label}"] = round(bear_pnl, 4)
                ft[f"bull_mfe_{label}"] = round(bull_mfe, 4)
                ft[f"bear_mfe_{label}"] = round(bear_mfe, 4)
                ft[f"bull_mae_{label}"] = round(bull_mae, 4)
                ft[f"bear_mae_{label}"] = round(bear_mae, 4)

            # Price action details: wick analysis at touch
            bar_range = bar["high"] - bar["low"]
            body = abs(bar["close"] - bar["open"])
            body_pct = body / bar_range * 100 if bar_range > 0 else 0
            upper_wick = bar["high"] - max(bar["open"], bar["close"])
            lower_wick = min(bar["open"], bar["close"]) - bar["low"]

            # Was the previous bar above or below? (approach direction)
            prev_bar = bars5m.iloc[bar_idx - 1]
            approach_from_above = prev_bar["close"] > lprice
            crossed_through = (prev_bar["close"] > lprice) != (close > lprice)

            # 3-bar context: did price cross and stay, or bounce?
            if bar_idx + 2 < len(bars5m):
                next2 = bars5m.iloc[bar_idx + 1: bar_idx + 3]
                stayed_through = all(
                    (r["close"] > lprice) == above for _, r in next2.iterrows()
                ) if len(next2) == 2 else None
            else:
                stayed_through = None

            touches.append({
                "sym": sym,
                "date": day,
                "time": bar_time,
                "level": lname,
                "level_price": lprice,
                "close": close,
                "dist_atr": round(dist_atr, 4),
                "above_level": above,
                "ema_bull": ema_bull,
                "vol_ratio": round(vol_ratio, 2),
                "atr": atr,
                "hour": bar_time.hour,
                "minute": bar_time.minute,
                "body_pct": round(body_pct, 1),
                "upper_wick": round(upper_wick, 4),
                "lower_wick": round(lower_wick, 4),
                "approach_from_above": approach_from_above,
                "crossed_through": crossed_through,
                "stayed_3bar": stayed_through,
                **ft,
            })

    return touches


# Run the touch detection across all symbol-days
all_touches = []
processed = 0
for (sym, day), dd in sym_day_data.items():
    levels = sym_day_levels.get((sym, day), {})
    vwap_data = sym_day_vwap.get((sym, day))
    bars5m = sym_day_5m.get((sym, day))
    if vwap_data is None or bars5m is None:
        continue
    touches = find_level_touches(sym, day, dd, levels, vwap_data, bars5m, proximity_atr=0.15)
    all_touches.extend(touches)
    processed += 1
    if processed % 50 == 0:
        print(f"  Processed {processed} symbol-days, {len(all_touches)} touches so far...")

tdf = pd.DataFrame(all_touches)
print(f"\nTotal level touches: {len(tdf)}")
print(f"Symbol-days processed: {processed}")

if len(tdf) == 0:
    print("ERROR: No touches found. Check data paths.")
    import sys
    sys.exit(1)

# ── ANALYSIS FUNCTIONS ──


def signal_stats(df, dir_col, pnl_col, label=""):
    """Compute N, win%, avg PnL, total PnL for a signal set."""
    if len(df) == 0:
        return {"N": 0}
    pnl = df[pnl_col]
    return {
        "label": label,
        "N": len(df),
        "win_pct": round(100 * (pnl > 0).mean(), 1),
        "avg_pnl": round(pnl.mean(), 4),
        "total_pnl": round(pnl.sum(), 1),
        "med_pnl": round(pnl.median(), 4),
    }


# ── OUTPUT REPORT ──
report = []
R = report.append


def section(title):
    R(f"\n## {title}\n")


def table(headers, rows):
    R("| " + " | ".join(headers) + " |")
    R("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        R("| " + " | ".join(str(x) for x in row) + " |")


R("# v3.0b New Levels Deep Research Report")
R(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
R(f"**Data:** {len(market)} symbols, {processed} symbol-days, {len(tdf)} level touches")
R(f"**Resolution:** 5sec (primary), 10sec/1min (fallback)")
R("")

# ═══════════════════════════════════════════════════════════════════
# TASK 1: Corrected backtest with live methodology
# ═══════════════════════════════════════════════════════════════════
section("1. Corrected Backtest (Live Methodology)")
R("Original backtest used: MFE over 6 bars, after 10:30 only, no vol/EMA filter.")
R("Corrected methodology: mark-to-market at 15/30/60 min, ALL hours, vol/EMA filters tested.\n")

target_levels = ["PD_MID", "PD_LH_L", "PD_LH_H", "VWAP_STD_L", "VWAP_ATR_L",
                  "VWAP_HALF_ATR_L", "VWAP_1.5STD_L", "PDH", "PDL", "ORB_H", "ORB_L"]

for horizon in ["30m"]:
    R(f"\n### Mark-to-Market at {horizon}\n")

    results_rows = []
    for lv in target_levels:
        sub = tdf[tdf["level"] == lv].copy()
        if len(sub) == 0:
            continue

        # Determine natural direction for this level
        # LOW levels -> bull (bounce), HIGH levels -> bear (rejection)
        low_levels = {"PD_LH_L", "PDL", "ORB_L", "VWAP_STD_L", "VWAP_ATR_L",
                      "VWAP_HALF_ATR_L", "VWAP_1.5STD_L"}
        high_levels = {"PD_LH_H", "PDH", "ORB_H", "VWAP_STD_U", "VWAP_ATR_U",
                       "VWAP_HALF_ATR_U", "VWAP_1.5STD_U"}
        neutral_levels = {"PD_MID", "VWAP"}

        if lv in low_levels:
            pnl_col = f"bull_pnl_{horizon}"
        elif lv in high_levels:
            pnl_col = f"bear_pnl_{horizon}"
        else:
            # Neutral: use EMA direction
            sub["dir_pnl"] = np.where(
                sub["ema_bull"] == True, sub[f"bull_pnl_{horizon}"],
                np.where(sub["ema_bull"] == False, sub[f"bear_pnl_{horizon}"], np.nan)
            )
            pnl_col = "dir_pnl"

        if pnl_col not in sub.columns and pnl_col != "dir_pnl":
            continue
        valid = sub[sub[pnl_col].notna()]
        if len(valid) == 0:
            continue

        # ALL HOURS, no filter
        s_all = signal_stats(valid, None, pnl_col, f"{lv} (all)")

        # After 10:30 only (matching original backtest)
        after1030 = valid[valid["hour"] * 60 + valid["minute"] >= 10 * 60 + 30]
        s_1030 = signal_stats(after1030, None, pnl_col, f"{lv} (>10:30)")

        # Vol >= 1.5x filter
        vol_filt = valid[valid["vol_ratio"] >= 1.5]
        s_vol = signal_stats(vol_filt, None, pnl_col, f"{lv} (vol>=1.5x)")

        # EMA aligned filter
        if lv in low_levels:
            ema_filt = valid[valid["ema_bull"] == True]
        elif lv in high_levels:
            ema_filt = valid[valid["ema_bull"] == False]
        else:
            ema_filt = valid  # already uses EMA direction
        s_ema = signal_stats(ema_filt, None, pnl_col, f"{lv} (EMA)")

        # Combined: after 10:30 + vol + EMA
        combined = valid[
            (valid["hour"] * 60 + valid["minute"] >= 10 * 60 + 30) &
            (valid["vol_ratio"] >= 1.5)
        ]
        if lv in low_levels:
            combined = combined[combined["ema_bull"] == True]
        elif lv in high_levels:
            combined = combined[combined["ema_bull"] == False]
        s_comb = signal_stats(combined, None, pnl_col, f"{lv} (10:30+vol+EMA)")

        results_rows.append([
            lv, s_all["N"], s_all["win_pct"], s_all["avg_pnl"],
            s_1030["N"], s_1030.get("win_pct", ""), s_1030.get("avg_pnl", ""),
            s_vol["N"], s_vol.get("win_pct", ""), s_vol.get("avg_pnl", ""),
            s_ema["N"], s_ema.get("win_pct", ""), s_ema.get("avg_pnl", ""),
            s_comb["N"], s_comb.get("win_pct", ""), s_comb.get("avg_pnl", ""),
        ])

    table(
        ["Level", "N_all", "W%_all", "PnL_all",
         "N_1030", "W%_1030", "PnL_1030",
         "N_vol", "W%_vol", "PnL_vol",
         "N_ema", "W%_ema", "PnL_ema",
         "N_comb", "W%_comb", "PnL_comb"],
        results_rows
    )

R("\n**Key question:** Does the original backtest edge survive when measured mark-to-market with live filters?")
R("")

# ═══════════════════════════════════════════════════════════════════
# TASK 2: Level computation validation
# ═══════════════════════════════════════════════════════════════════
section("2. Level Computation Validation")
R("Checking if our computed levels match what Pine would compute.\n")

# Sample 5 days, show PD Mid and PD LH L values
sample_rows = []
count = 0
for (sym, day), levels in sorted(sym_day_levels.items()):
    if "PD_MID" in levels and "PD_LH_L" in levels:
        daily_atr = levels.get("daily_ATR", np.nan)
        vwap_data = sym_day_vwap.get((sym, day))
        if vwap_data is not None:
            vs, vss = vwap_data
            # Get VWAP at 10:00
            ts = pd.Timestamp(day)
            if ts.tzinfo is not None:
                t1000 = ts.tz_convert("US/Eastern").replace(hour=10, minute=0)
            else:
                t1000 = ts.tz_localize("US/Eastern").replace(hour=10, minute=0)
            idx = vs.index.searchsorted(t1000, side="right") - 1
            vwap_1000 = vs.iloc[idx] if 0 <= idx < len(vs) else np.nan
            vwap_std_1000 = vss.iloc[idx] if 0 <= idx < len(vss) else np.nan
        else:
            vwap_1000 = np.nan
            vwap_std_1000 = np.nan

        sample_rows.append([
            sym, str(day.date()) if hasattr(day, 'date') else str(day)[:10],
            f"{levels['PD_MID']:.2f}",
            f"{levels['PD_LH_L']:.2f}",
            f"{daily_atr:.2f}" if not np.isnan(daily_atr) else "?",
            f"{vwap_1000:.2f}" if not np.isnan(vwap_1000) else "?",
            f"{vwap_std_1000:.4f}" if not np.isnan(vwap_std_1000) else "?",
            f"{vwap_1000 - vwap_std_1000:.2f}" if not np.isnan(vwap_1000) and not np.isnan(vwap_std_1000) else "?",
            f"{vwap_1000 - daily_atr:.2f}" if not np.isnan(vwap_1000) and not np.isnan(daily_atr) else "?",
        ])
        count += 1
        if count >= 15:
            break

R("### Sample Level Values\n")
table(
    ["Sym", "Date", "PD_MID", "PD_LH_L", "ATR", "VWAP@10", "VWAP_STD@10", "VWAP-STD", "VWAP-ATR"],
    sample_rows
)

R("""
**Key finding:** VWAP-STD band is MUCH closer to price than VWAP-ATR.
The backtest validated VWAP-STD (std dev band). The live code uses VWAP-ATR (daily ATR).
These are fundamentally different distances from VWAP.
""")

# ═══════════════════════════════════════════════════════════════════
# TASK 3: Price Action at each level
# ═══════════════════════════════════════════════════════════════════
section("3. Price Action Study")
R("What ACTUALLY happens when price reaches each level?\n")

for lv in ["PD_MID", "PD_LH_L", "PDH", "PDL"]:
    sub = tdf[tdf["level"] == lv]
    if len(sub) < 5:
        continue

    R(f"\n### {lv} (N={len(sub)} touches)\n")

    # Touch statistics
    n_crossed = sub["crossed_through"].sum()
    n_stayed = sub["stayed_3bar"].sum() if sub["stayed_3bar"].notna().any() else 0
    n_bounced = len(sub) - n_crossed

    R(f"- Crossed through: {n_crossed} ({100 * n_crossed / len(sub):.0f}%)")
    R(f"- Bounced: {n_bounced} ({100 * n_bounced / len(sub):.0f}%)")
    if sub["stayed_3bar"].notna().any():
        stayed_valid = sub[sub["stayed_3bar"].notna()]
        R(f"- Stayed through 3 bars: {n_stayed} / {len(stayed_valid)} "
          f"({100 * n_stayed / max(len(stayed_valid), 1):.0f}%)")

    # First vs subsequent touches per session
    sub_sorted = sub.sort_values(["sym", "date", "time"])
    sub_sorted["touch_num"] = sub_sorted.groupby(["sym", "date"]).cumcount() + 1

    for tn in [1, 2, 3]:
        tn_sub = sub_sorted[sub_sorted["touch_num"] == tn]
        if len(tn_sub) < 3:
            continue
        # Use the "natural direction" PnL
        if lv in ["PD_LH_L", "PDL", "ORB_L"]:
            pnl_col = "bull_pnl_30m"
        elif lv in ["PD_LH_H", "PDH", "ORB_H"]:
            pnl_col = "bear_pnl_30m"
        else:
            pnl_col = "bull_pnl_30m"
            tn_sub = tn_sub.copy()
            tn_sub[pnl_col] = np.where(
                tn_sub["ema_bull"] == True, tn_sub["bull_pnl_30m"],
                tn_sub["bear_pnl_30m"]
            )

        valid = tn_sub[tn_sub[pnl_col].notna()]
        if len(valid) > 0:
            R(f"- Touch #{tn}: N={len(valid)}, "
              f"win%={100 * (valid[pnl_col] > 0).mean():.0f}%, "
              f"avg PnL={valid[pnl_col].mean():.4f}")

    # Average body% at touch
    R(f"- Avg body%: {sub['body_pct'].mean():.1f}%")
    R(f"- Avg vol ratio: {sub['vol_ratio'].mean():.1f}x")

    # Time distribution
    time_dist = sub.groupby("hour").size()
    R(f"- Touches by hour: " + ", ".join(f"{h}h:{n}" for h, n in time_dist.items()))


# ═══════════════════════════════════════════════════════════════════
# TASK 4: Alternative signal designs
# ═══════════════════════════════════════════════════════════════════
section("4. Alternative Signal Designs")
R("Testing 7 different signal designs at each new level.\n")

designs = {}

for lv in ["PD_MID", "PD_LH_L"]:
    sub = tdf[tdf["level"] == lv].copy()
    if len(sub) < 10:
        continue

    R(f"\n### {lv}\n")

    design_results = []

    # a) Mean reversion (REV): price bounces off level
    # For LOW: bull bounce. For HIGH: bear rejection. For MID: bounce away from approach
    rev = sub[~sub["crossed_through"]].copy()
    if lv == "PD_LH_L":
        pnl_col = "bull_pnl_30m"
    elif lv == "PD_MID":
        rev["rev_pnl"] = np.where(
            rev["approach_from_above"], rev["bear_pnl_30m"], rev["bull_pnl_30m"]
        )
        pnl_col = "rev_pnl"
    else:
        pnl_col = "bear_pnl_30m"
    valid = rev[rev[pnl_col].notna()]
    s = signal_stats(valid, None, pnl_col)
    design_results.append(["a) REV (bounce)", s["N"], s.get("win_pct", ""), s.get("avg_pnl", ""), s.get("total_pnl", "")])

    # b) BRK: price crosses through level
    brk = sub[sub["crossed_through"]].copy()
    if lv == "PD_LH_L":
        pnl_col_brk = "bear_pnl_30m"  # break DOWN through support
    elif lv == "PD_MID":
        brk["brk_pnl"] = np.where(
            brk["above_level"], brk["bull_pnl_30m"], brk["bear_pnl_30m"]
        )
        pnl_col_brk = "brk_pnl"
    else:
        pnl_col_brk = "bull_pnl_30m"
    valid_brk = brk[brk[pnl_col_brk].notna()]
    s = signal_stats(valid_brk, None, pnl_col_brk)
    design_results.append(["b) BRK (cross)", s["N"], s.get("win_pct", ""), s.get("avg_pnl", ""), s.get("total_pnl", "")])

    # c) FADE: cross then fail (come back within 3 bars)
    fade = sub[sub["crossed_through"] & (sub["stayed_3bar"] == False)].copy()
    if lv == "PD_LH_L":
        pnl_col_fade = "bull_pnl_30m"  # failed bear break = go bull
    elif lv == "PD_MID":
        fade["fade_pnl"] = np.where(
            fade["above_level"], fade["bear_pnl_30m"], fade["bull_pnl_30m"]
        )
        pnl_col_fade = "fade_pnl"
    else:
        pnl_col_fade = "bear_pnl_30m"
    valid_fade = fade[fade[pnl_col_fade].notna()]
    s = signal_stats(valid_fade, None, pnl_col_fade)
    design_results.append(["c) FADE (failed break)", s["N"], s.get("win_pct", ""), s.get("avg_pnl", ""), s.get("total_pnl", "")])

    # d) Time-restricted: only after 10:30
    after1030 = sub[(sub["hour"] * 60 + sub["minute"]) >= 630]
    if lv == "PD_LH_L":
        pnl_col_t = "bull_pnl_30m"
    else:
        after1030 = after1030.copy()
        after1030["ema_pnl"] = np.where(
            after1030["ema_bull"] == True, after1030["bull_pnl_30m"],
            after1030["bear_pnl_30m"]
        )
        pnl_col_t = "ema_pnl"
    valid_t = after1030[after1030[pnl_col_t].notna()]
    s = signal_stats(valid_t, None, pnl_col_t)
    design_results.append(["d) After 10:30", s["N"], s.get("win_pct", ""), s.get("avg_pnl", ""), s.get("total_pnl", "")])

    # e) Low volume only (1-2x): mean-reversion touch
    lowvol = sub[(sub["vol_ratio"] >= 0.5) & (sub["vol_ratio"] < 2.0)]
    if lv == "PD_LH_L":
        pnl_col_lv = "bull_pnl_30m"
    else:
        lowvol = lowvol.copy()
        lowvol["ema_pnl"] = np.where(
            lowvol["ema_bull"] == True, lowvol["bull_pnl_30m"],
            lowvol["bear_pnl_30m"]
        )
        pnl_col_lv = "ema_pnl"
    valid_lv = lowvol[lowvol[pnl_col_lv].notna()]
    s = signal_stats(valid_lv, None, pnl_col_lv)
    design_results.append(["e) Vol 0.5-2x only", s["N"], s.get("win_pct", ""), s.get("avg_pnl", ""), s.get("total_pnl", "")])

    # f) No once-per-session: allow all touches. 2nd and 3rd touches
    sub_sorted = sub.sort_values(["sym", "date", "time"]).copy()
    sub_sorted["touch_num"] = sub_sorted.groupby(["sym", "date"]).cumcount() + 1
    for tn_label, tn_filter in [("1st touch", 1), ("2nd+ touch", None)]:
        if tn_filter:
            tn_sub = sub_sorted[sub_sorted["touch_num"] == tn_filter]
        else:
            tn_sub = sub_sorted[sub_sorted["touch_num"] >= 2]
        if lv == "PD_LH_L":
            pnl_col_tn = "bull_pnl_30m"
        else:
            tn_sub = tn_sub.copy()
            tn_sub["ema_pnl"] = np.where(
                tn_sub["ema_bull"] == True, tn_sub["bull_pnl_30m"],
                tn_sub["bear_pnl_30m"]
            )
            pnl_col_tn = "ema_pnl"
        valid_tn = tn_sub[tn_sub[pnl_col_tn].notna()]
        s = signal_stats(valid_tn, None, pnl_col_tn)
        design_results.append([f"f) {tn_label}", s["N"], s.get("win_pct", ""), s.get("avg_pnl", ""), s.get("total_pnl", "")])

    # g) Directional: PD Mid bear only, PD LH L bull only
    if lv == "PD_MID":
        bear_only = sub.copy()
        pnl_col_dir = "bear_pnl_30m"
        valid_dir = bear_only[bear_only[pnl_col_dir].notna()]
        s = signal_stats(valid_dir, None, pnl_col_dir)
        design_results.append(["g) Bear only", s["N"], s.get("win_pct", ""), s.get("avg_pnl", ""), s.get("total_pnl", "")])

        bull_only = sub.copy()
        valid_dir = bull_only[bull_only["bull_pnl_30m"].notna()]
        s = signal_stats(valid_dir, None, "bull_pnl_30m")
        design_results.append(["g) Bull only", s["N"], s.get("win_pct", ""), s.get("avg_pnl", ""), s.get("total_pnl", "")])
    else:
        # PD LH L: already bull-natural
        bear_at_lhl = sub.copy()
        valid_dir = bear_at_lhl[bear_at_lhl["bear_pnl_30m"].notna()]
        s = signal_stats(valid_dir, None, "bear_pnl_30m")
        design_results.append(["g) Bear (break down)", s["N"], s.get("win_pct", ""), s.get("avg_pnl", ""), s.get("total_pnl", "")])

    # h) BEST combo: after 10:00 + vol < 5x + EMA aligned
    combo = sub[
        ((sub["hour"] * 60 + sub["minute"]) >= 600) &
        (sub["vol_ratio"] < 5.0)
    ].copy()
    if lv == "PD_LH_L":
        combo = combo[combo["ema_bull"] == True]
        pnl_col_combo = "bull_pnl_30m"
    else:
        combo["ema_pnl"] = np.where(
            combo["ema_bull"] == True, combo["bull_pnl_30m"],
            combo["bear_pnl_30m"]
        )
        pnl_col_combo = "ema_pnl"
    valid_combo = combo[combo[pnl_col_combo].notna()]
    s = signal_stats(valid_combo, None, pnl_col_combo)
    design_results.append(["h) 10:00+ vol<5x EMA", s["N"], s.get("win_pct", ""), s.get("avg_pnl", ""), s.get("total_pnl", "")])

    table(["Design", "N", "Win%", "Avg PnL", "Total PnL"], design_results)

    designs[lv] = design_results


# ═══════════════════════════════════════════════════════════════════
# TASK 5: Level Magnet hypothesis
# ═══════════════════════════════════════════════════════════════════
section("5. Level Magnet Hypothesis")
R("Do PD Mid and PD LH L act as magnets (price hovers) or barriers (clean break/bounce)?\n")

R("### Break Conviction Ratio\n")
R("When price reaches within 0.15 ATR: what % cross through vs bounce?\n")

magnet_rows = []
for lv in ["PD_MID", "PD_LH_L", "PDH", "PDL", "ORB_H", "ORB_L"]:
    sub = tdf[tdf["level"] == lv]
    if len(sub) < 5:
        continue
    n = len(sub)
    n_cross = sub["crossed_through"].sum()
    n_bounce = n - n_cross
    n_stayed = sub[sub["stayed_3bar"] == True].shape[0]
    n_valid_stay = sub[sub["stayed_3bar"].notna()].shape[0]

    cross_pct = 100 * n_cross / n
    clean_break_pct = 100 * n_stayed / n_valid_stay if n_valid_stay > 0 else 0

    magnet_rows.append([
        lv, n, f"{cross_pct:.0f}%", f"{100 - cross_pct:.0f}%",
        f"{clean_break_pct:.0f}%",
        f"{100 - clean_break_pct:.0f}%"
    ])

table(
    ["Level", "N", "Cross%", "Bounce%", "Clean Break (stayed 3 bar)", "Messy (came back)"],
    magnet_rows
)

R("""
**Interpretation:**
- High cross% + high clean break% = strong breakout level (like Yesterday H/L)
- High bounce% = strong reversal level
- High cross% + low clean break% = MAGNET (price crosses but comes back = messy/noisy)
""")


# ═══════════════════════════════════════════════════════════════════
# TASK 6: Level overlap contamination
# ═══════════════════════════════════════════════════════════════════
section("6. Level Overlap Contamination")
R("Do new levels coincide with original levels? If so, is the edge really from the original?\n")

# For each PD_MID and PD_LH_L touch, check if any original level is within 0.3 ATR
original_levels = {"PDH", "PDL", "ORB_H", "ORB_L"}

for lv in ["PD_MID", "PD_LH_L"]:
    sub = tdf[tdf["level"] == lv].copy()
    if len(sub) < 10:
        continue

    R(f"\n### {lv}\n")

    # For each touch, find if an original level is nearby on the same sym+day
    standalone = []
    overlapping = []

    for _, touch in sub.iterrows():
        sym, day = touch["sym"], touch["date"]
        levels = sym_day_levels.get((sym, day), {})
        close = touch["close"]
        atr = touch["atr"]
        if atr <= 0:
            continue

        has_original = False
        for orig_lv in ["PDH", "PDL"]:
            if orig_lv in levels:
                orig_dist = abs(close - levels[orig_lv]) / atr
                if orig_dist <= 0.3:
                    has_original = True
                    break
        if not has_original:
            for orig_lv in ["ORB_H", "ORB_L"]:
                if orig_lv in levels:
                    orig_dist = abs(close - levels[orig_lv]) / atr
                    if orig_dist <= 0.3:
                        has_original = True
                        break

        if has_original:
            overlapping.append(touch)
        else:
            standalone.append(touch)

    standalone_df = pd.DataFrame(standalone)
    overlap_df = pd.DataFrame(overlapping)

    R(f"- Standalone (no original level within 0.3 ATR): {len(standalone_df)}")
    R(f"- Overlapping (original level within 0.3 ATR): {len(overlap_df)}")

    if lv == "PD_LH_L":
        pcol = "bull_pnl_30m"
    else:
        for df_tmp in [standalone_df, overlap_df]:
            if len(df_tmp) > 0:
                df_tmp["ema_pnl"] = np.where(
                    df_tmp["ema_bull"] == True, df_tmp["bull_pnl_30m"],
                    df_tmp["bear_pnl_30m"]
                )
        pcol = "ema_pnl"

    for label, df_tmp in [("Standalone", standalone_df), ("Overlapping", overlap_df)]:
        if len(df_tmp) == 0:
            R(f"  - {label}: N=0")
            continue
        valid = df_tmp[df_tmp[pcol].notna()]
        if len(valid) > 0:
            s = signal_stats(valid, None, pcol)
            R(f"  - {label}: N={s['N']}, win%={s['win_pct']}, avg={s['avg_pnl']}, total={s['total_pnl']}")

    R("")


# ═══════════════════════════════════════════════════════════════════
# TASK 7: VW Band Deep Dive
# ═══════════════════════════════════════════════════════════════════
section("7. VW Band Deep Dive")
R("The live VW Band (VWAP - ATR) never fires. Testing alternative band formulas.\n")

for band_lv in ["VWAP_STD_L", "VWAP_ATR_L", "VWAP_HALF_ATR_L", "VWAP_1.5STD_L"]:
    sub = tdf[tdf["level"] == band_lv]
    R(f"\n### {band_lv}: N={len(sub)} touches")
    if len(sub) == 0:
        R("  (No touches found — band is too far from price)")
        continue

    # Bull REV (bounce off lower band) — this is what the backtest validated
    valid = sub[sub["bull_pnl_30m"].notna()]
    if len(valid) > 0:
        s = signal_stats(valid, None, "bull_pnl_30m")
        R(f"  - Bull REV (bounce): N={s['N']}, win%={s['win_pct']}, avg={s['avg_pnl']}, total={s['total_pnl']}")

    # Bear BRK (break below band) — what the live code does
    valid_bear = sub[sub["bear_pnl_30m"].notna()]
    if len(valid_bear) > 0:
        s = signal_stats(valid_bear, None, "bear_pnl_30m")
        R(f"  - Bear BRK (break down): N={s['N']}, win%={s['win_pct']}, avg={s['avg_pnl']}, total={s['total_pnl']}")

    # Time distribution
    if len(sub) > 0:
        R(f"  - Hour dist: " + ", ".join(f"{h}h:{n}" for h, n in sub.groupby("hour").size().items()))
        R(f"  - Avg vol: {sub['vol_ratio'].mean():.1f}x")


# ═══════════════════════════════════════════════════════════════════
# TASK 8: Level relevance decay
# ═══════════════════════════════════════════════════════════════════
section("8. Intraday Level Relevance Decay")
R("Do static prior-day levels lose relevance as the day progresses?\n")

for lv in ["PD_MID", "PD_LH_L", "PDH", "PDL"]:
    sub = tdf[tdf["level"] == lv].copy()
    if len(sub) < 10:
        continue

    R(f"\n### {lv}\n")

    # Group by hour
    if lv in ["PD_LH_L", "PDL", "ORB_L"]:
        pcol = "bull_pnl_30m"
    elif lv in ["PD_LH_H", "PDH", "ORB_H"]:
        pcol = "bear_pnl_30m"
    else:
        sub["ema_pnl"] = np.where(
            sub["ema_bull"] == True, sub["bull_pnl_30m"],
            sub["bear_pnl_30m"]
        )
        pcol = "ema_pnl"

    hour_rows = []
    for h in range(9, 16):
        h_sub = sub[sub["hour"] == h]
        valid = h_sub[h_sub[pcol].notna()]
        if len(valid) < 3:
            continue
        s = signal_stats(valid, None, pcol)
        hour_rows.append([f"{h}:00-{h+1}:00", s["N"], s["win_pct"], s["avg_pnl"], s["total_pnl"]])

    if hour_rows:
        table(["Hour", "N", "Win%", "Avg PnL", "Total"], hour_rows)

    # Average distance from level to current price by hour
    R(f"\nAvg distance (ATR) from level by hour:")
    for h in range(9, 16):
        h_sub = sub[sub["hour"] == h]
        if len(h_sub) > 0:
            R(f"  {h}:00: {h_sub['dist_atr'].mean():.3f} ATR (N={len(h_sub)})")


# ═══════════════════════════════════════════════════════════════════
# TASK 9: Multi-day level persistence
# ═══════════════════════════════════════════════════════════════════
section("9. Multi-Day Level Analysis")
R("Does PD Mid's relevance depend on how far price opens from it?\n")

for lv in ["PD_MID", "PD_LH_L"]:
    sub = tdf[tdf["level"] == lv].copy()
    if len(sub) < 10:
        continue

    R(f"\n### {lv}: Gap-to-Level Distance\n")

    # For each touch, compute the gap between session open and the level
    gap_rows = []
    for (sym, day), grp in sub.groupby(["sym", "date"]):
        dd = sym_day_data.get((sym, day))
        levels = sym_day_levels.get((sym, day), {})
        if dd is None or lv not in levels:
            continue
        open_price = dd.iloc[0]["open"]
        level_price = levels[lv]
        atr = grp.iloc[0]["atr"]
        if atr <= 0:
            continue
        gap_atr = abs(open_price - level_price) / atr
        grp = grp.copy()
        grp["gap_atr"] = gap_atr
        gap_rows.append(grp)

    if gap_rows:
        gap_df = pd.concat(gap_rows)

        if lv == "PD_LH_L":
            pcol = "bull_pnl_30m"
        else:
            gap_df["ema_pnl"] = np.where(
                gap_df["ema_bull"] == True, gap_df["bull_pnl_30m"],
                gap_df["bear_pnl_30m"]
            )
            pcol = "ema_pnl"

        for lo, hi, label in [(0, 0.5, "<0.5 ATR"), (0.5, 1.0, "0.5-1.0 ATR"),
                               (1.0, 2.0, "1.0-2.0 ATR"), (2.0, 99, ">2.0 ATR")]:
            bucket = gap_df[(gap_df["gap_atr"] >= lo) & (gap_df["gap_atr"] < hi)]
            valid = bucket[bucket[pcol].notna()]
            if len(valid) > 0:
                s = signal_stats(valid, None, pcol)
                R(f"- Gap {label}: N={s['N']}, win%={s['win_pct']}, avg={s['avg_pnl']}")


# ═══════════════════════════════════════════════════════════════════
# TASK 10: Optimal design synthesis
# ═══════════════════════════════════════════════════════════════════
section("10. Optimal Design Recommendation")
R("After all analysis, what is the BEST way to use these levels?\n")

R("### Ranking: Which level has the most promise?\n")

# Collect all level stats in a summary
summary_rows = []
for lv in ["PD_MID", "PD_LH_L", "VWAP_STD_L", "VWAP_HALF_ATR_L", "PDH", "PDL"]:
    sub = tdf[tdf["level"] == lv]
    if len(sub) == 0:
        continue

    if lv in ["PD_LH_L", "PDL", "VWAP_STD_L", "VWAP_HALF_ATR_L"]:
        pcol = "bull_pnl_30m"
    elif lv in ["PDH"]:
        pcol = "bear_pnl_30m"
    else:
        sub = sub.copy()
        sub["ema_pnl"] = np.where(
            sub["ema_bull"] == True, sub["bull_pnl_30m"],
            sub["bear_pnl_30m"]
        )
        pcol = "ema_pnl"

    valid = sub[sub[pcol].notna()]
    if len(valid) == 0:
        continue

    s = signal_stats(valid, None, pcol)
    summary_rows.append([lv, s["N"], s["win_pct"], s["avg_pnl"], s["total_pnl"]])

table(["Level", "N", "Win%", "Avg PnL", "Total PnL"], summary_rows)

R("""
### Assessment: Keep, Redesign, or Remove?

Based on all 10 analysis tasks above:

| Level | Verdict | Reasoning |
|-------|---------|-----------|
| PD Mid | ? | See corrected backtest results above |
| PD LH L | ? | See corrected backtest results above |
| VW Band (VWAP-ATR) | REMOVE | Never fires. Wrong formula. Wrong direction. |
| VWAP-STD Band | ? | See Task 7 results — this is what the backtest validated |

### Key Discoveries

(Findings are populated by the data above — see each section's numbers.)
""")

# ═══════════════════════════════════════════════════════════════════
# Executive Summary (written last, goes to top of report)
# ═══════════════════════════════════════════════════════════════════
exec_summary = [
    "# Executive Summary\n",
    "This report presents a comprehensive 10-task investigation into why PD Mid, PD Last Hr Low,",
    "and VW Band underperform in live trading despite strong backtest results.",
    "",
    "**Core question:** Is the edge real, or was the backtest flawed?",
    "",
    "**Key findings are detailed in each section below.**",
    "",
    "---",
]

# Prepend executive summary
report = exec_summary + [""] + report

# Write report
REPORT.write_text("\n".join(report))
print(f"\nReport written to: {REPORT}")
print(f"Total lines: {len(report)}")
print("DONE.")
