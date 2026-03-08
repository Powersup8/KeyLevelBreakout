#!/usr/bin/env python3
"""
Investigation of missed moves for March 6, 2026 KLB daily investigation.
Loads IB 5-minute data, computes levels, analyzes each miss in detail.
"""
import pandas as pd
import numpy as np
from datetime import datetime, time

IB_CACHE = "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars"
TARGET_DATE = pd.Timestamp("2026-03-06")
ET = "US/Eastern"

# Symbols to load
SYMBOLS = ["AMD", "TSLA", "NVDA", "META", "SPY", "QQQ"]

# Missed moves to investigate
MISSES = [
    {"symbol": "AMD",  "time": "12:05", "direction": "bear", "note": "downmove missed"},
    {"symbol": "TSLA", "time": "11:05", "direction": "bear", "note": "downmove missed"},
    {"symbol": "TSLA", "time": "12:40", "direction": "bull", "note": "upmove missed"},
    {"symbol": "TSLA", "time": "13:15", "direction": "bull", "note": "signaled bull but then it was over"},
    {"symbol": "NVDA", "time": "9:30",  "direction": "bull", "note": "upmove we didn't fetch it"},
    {"symbol": "NVDA", "time": "12:00", "direction": "bear", "note": "down we didn't catch"},
    {"symbol": "META", "time": "9:30",  "direction": "bear", "note": "great move we got it but no conf or label that says GO IN"},
    {"symbol": "META", "time": "9:35",  "direction": "bull", "note": "significant upmove, only REV ORB L, not conf, not marked good to go"},
    {"symbol": "META", "time": "10:30", "direction": "bear", "note": "bearish signal with diamond but went up then neutral"},
]


def load_5m(symbol: str) -> pd.DataFrame:
    """Load 5m IB data, convert to ET, filter to RTH."""
    path = f"{IB_CACHE}/{symbol.lower()}_5_mins_ib.parquet"
    df = pd.read_parquet(path)
    # Date col is in Europe/Berlin
    df["date"] = pd.to_datetime(df["date"], utc=True).dt.tz_convert(ET)
    df = df.set_index("date").sort_index()
    return df


def filter_rth(df: pd.DataFrame, date: pd.Timestamp) -> pd.DataFrame:
    """Filter to regular trading hours 9:30-16:00 ET for a specific date."""
    start = pd.Timestamp(f"{date.date()} 09:30:00", tz=ET)
    end = pd.Timestamp(f"{date.date()} 16:00:00", tz=ET)
    return df[(df.index >= start) & (df.index < end)]


def get_prior_day(df: pd.DataFrame, date: pd.Timestamp) -> pd.DataFrame:
    """Get RTH data for the prior trading day."""
    # Get all unique dates before target
    all_dates = df.index.normalize().unique()
    prior_dates = all_dates[all_dates < pd.Timestamp(date.date(), tz=ET)]
    if len(prior_dates) == 0:
        return pd.DataFrame()
    prior_date = prior_dates[-1]
    return filter_rth(df, prior_date)


def compute_atr(df: pd.DataFrame, date: pd.Timestamp, period: int = 14) -> float:
    """Compute ATR from daily bars derived from 5m data."""
    # Get all RTH dates before target
    all_dates = df.index.normalize().unique()
    prior_dates = all_dates[all_dates < pd.Timestamp(date.date(), tz=ET)]
    if len(prior_dates) < period:
        prior_dates = prior_dates[-period:] if len(prior_dates) > 0 else prior_dates
    else:
        prior_dates = prior_dates[-period:]

    trs = []
    prev_close = None
    for d in prior_dates:
        day_data = filter_rth(df, d)
        if len(day_data) == 0:
            continue
        h = day_data["high"].max()
        l = day_data["low"].min()
        if prev_close is not None:
            tr = max(h - l, abs(h - prev_close), abs(l - prev_close))
        else:
            tr = h - l
        trs.append(tr)
        prev_close = day_data["close"].iloc[-1]

    return np.mean(trs) if trs else 0.0


def compute_ema(series: pd.Series, period: int = 21) -> pd.Series:
    """Compute EMA."""
    return series.ewm(span=period, adjust=False).mean()


def compute_vol_ratio(vol_series: pd.Series, idx: int, lookback: int = 20) -> float:
    """Compute volume relative to 20-bar average."""
    if idx < lookback:
        avg = vol_series.iloc[:idx].mean() if idx > 0 else vol_series.iloc[idx]
    else:
        avg = vol_series.iloc[idx-lookback:idx].mean()
    return vol_series.iloc[idx] / avg if avg > 0 else 0.0


def analyze_miss(data_dict: dict, miss: dict, levels_dict: dict, atr_dict: dict):
    """Analyze a single missed move."""
    sym = miss["symbol"]
    target_time = miss["time"]
    direction = miss["direction"]

    df = data_dict[sym]
    spy_df = data_dict["SPY"]
    qqq_df = data_dict["QQQ"]

    pd_high, pd_low, pd_close = levels_dict[sym]
    atr = atr_dict[sym]

    # Find the bar at or near the target time
    h, m = map(int, target_time.split(":"))
    target_ts = pd.Timestamp(f"{TARGET_DATE.date()} {h:02d}:{m:02d}:00", tz=ET)

    # Get 5-bar window (25 min) around target time
    window_start = target_ts - pd.Timedelta(minutes=10)
    window_end = target_ts + pd.Timedelta(minutes=15)
    window = df[(df.index >= window_start) & (df.index <= window_end)]

    # Compute EMA on the full day data
    ema21 = compute_ema(df["close"], 21)

    # Find the closest bar
    if target_ts in df.index:
        target_idx = df.index.get_loc(target_ts)
    else:
        # Find closest
        diffs = abs(df.index - target_ts)
        target_idx = diffs.argmin()

    target_bar = df.iloc[target_idx]
    target_ema = ema21.iloc[target_idx]

    # EMA status
    ema_status = "above" if target_bar["close"] > target_ema else "below"
    ema_trend = "bull" if ema21.iloc[target_idx] > ema21.iloc[max(0, target_idx-3)] else "bear"

    # Volume ratio
    vol_ratio = compute_vol_ratio(df["volume"], target_idx)

    # MFE: how far did the move go after this time?
    if direction == "bear":
        future = df.iloc[target_idx:target_idx+12]  # 60 min forward
        if len(future) > 0:
            mfe = target_bar["close"] - future["low"].min()
        else:
            mfe = 0
    else:  # bull
        future = df.iloc[target_idx:target_idx+12]
        if len(future) > 0:
            mfe = future["high"].max() - target_bar["close"]
        else:
            mfe = 0

    mfe_atr = mfe / atr if atr > 0 else 0

    # Check nearby levels
    price = target_bar["close"]
    level_distances = {
        "PD High": abs(price - pd_high) / atr if atr > 0 else 999,
        "PD Low": abs(price - pd_low) / atr if atr > 0 else 999,
        "PD Close": abs(price - pd_close) / atr if atr > 0 else 999,
    }

    # Also compute today's Open, ORB H/L (first 30 min)
    today_open = df.iloc[0]["open"] if len(df) > 0 else 0
    orb_data = df[df.index < pd.Timestamp(f"{TARGET_DATE.date()} 10:00:00", tz=ET)]
    orb_high = orb_data["high"].max() if len(orb_data) > 0 else 0
    orb_low = orb_data["low"].min() if len(orb_data) > 0 else 0

    level_distances["Today Open"] = abs(price - today_open) / atr if atr > 0 else 999
    level_distances["ORB High"] = abs(price - orb_high) / atr if atr > 0 else 999
    level_distances["ORB Low"] = abs(price - orb_low) / atr if atr > 0 else 999

    # VWAP approximation (cumulative volume-weighted average)
    cum_vol = df["volume"].iloc[:target_idx+1].cumsum()
    cum_vwap = (df["close"].iloc[:target_idx+1] * df["volume"].iloc[:target_idx+1]).cumsum()
    vwap = cum_vwap.iloc[-1] / cum_vol.iloc[-1] if cum_vol.iloc[-1] > 0 else price
    level_distances["VWAP"] = abs(price - vwap) / atr if atr > 0 else 999
    vwap_status = "above" if price > vwap else "below"

    # Nearest level
    nearest_level = min(level_distances, key=level_distances.get)
    nearest_dist = level_distances[nearest_level]

    # SPY and QQQ at the same time
    spy_bar = None
    qqq_bar = None
    if target_ts in spy_df.index:
        spy_bar = spy_df.loc[target_ts]
    elif len(spy_df) > 0:
        diffs = abs(spy_df.index - target_ts)
        spy_bar = spy_df.iloc[diffs.argmin()]

    if target_ts in qqq_df.index:
        qqq_bar = qqq_df.loc[target_ts]
    elif len(qqq_df) > 0:
        diffs = abs(qqq_df.index - target_ts)
        qqq_bar = qqq_df.iloc[diffs.argmin()]

    # SPY change from open
    spy_open = data_dict["SPY"].iloc[0]["open"] if len(data_dict["SPY"]) > 0 else 0
    spy_chg = ((spy_bar["close"] / spy_open) - 1) * 100 if spy_bar is not None and spy_open > 0 else 0

    result = {
        "symbol": sym,
        "time": target_time,
        "direction": direction,
        "note": miss["note"],
        "price": price,
        "open": target_bar["open"],
        "high": target_bar["high"],
        "low": target_bar["low"],
        "close": target_bar["close"],
        "volume": target_bar["volume"],
        "vol_ratio": vol_ratio,
        "ema21": target_ema,
        "ema_status": ema_status,
        "ema_trend": ema_trend,
        "vwap": vwap,
        "vwap_status": vwap_status,
        "mfe": mfe,
        "mfe_atr": mfe_atr,
        "atr": atr,
        "pd_high": pd_high,
        "pd_low": pd_low,
        "pd_close": pd_close,
        "today_open": today_open,
        "orb_high": orb_high,
        "orb_low": orb_low,
        "nearest_level": nearest_level,
        "nearest_dist_atr": nearest_dist,
        "all_levels": level_distances,
        "spy_chg": spy_chg,
        "window": window[["open", "high", "low", "close", "volume"]].to_string(),
    }

    return result


def main():
    print("=" * 100)
    print("KLB DAILY INVESTIGATION — March 6, 2026 — Missed Moves Analysis")
    print("=" * 100)

    # Load all data
    data_5m = {}
    for sym in SYMBOLS:
        df = load_5m(sym)
        rth = filter_rth(df, TARGET_DATE)
        data_5m[sym] = rth
        print(f"  {sym}: {len(rth)} bars on Mar 6")

    # Compute prior-day levels and ATR for each symbol
    levels = {}
    atrs = {}
    for sym in SYMBOLS:
        df_full = load_5m(sym)
        pd_data = get_prior_day(df_full, TARGET_DATE)
        if len(pd_data) > 0:
            pd_high = pd_data["high"].max()
            pd_low = pd_data["low"].min()
            pd_close = pd_data["close"].iloc[-1]
        else:
            pd_high = pd_low = pd_close = 0
        levels[sym] = (pd_high, pd_low, pd_close)
        atrs[sym] = compute_atr(df_full, TARGET_DATE)
        print(f"  {sym} levels: PD H={pd_high:.2f} L={pd_low:.2f} C={pd_close:.2f} ATR={atrs[sym]:.2f}")

    # Day overview for each miss symbol
    print("\n" + "=" * 100)
    print("DAY OVERVIEW")
    print("=" * 100)
    for sym in ["AMD", "TSLA", "NVDA", "META", "SPY", "QQQ"]:
        df = data_5m[sym]
        if len(df) == 0:
            print(f"  {sym}: NO DATA")
            continue
        day_open = df.iloc[0]["open"]
        day_high = df["high"].max()
        day_low = df["low"].min()
        day_close = df.iloc[-1]["close"]
        day_range = day_high - day_low
        chg_pct = ((day_close / day_open) - 1) * 100
        range_atr = day_range / atrs[sym] if atrs[sym] > 0 else 0
        print(f"  {sym}: O={day_open:.2f} H={day_high:.2f} L={day_low:.2f} C={day_close:.2f} "
              f"chg={chg_pct:+.1f}% range={day_range:.2f} ({range_atr:.1f}xATR)")

    # Analyze each miss
    print("\n" + "=" * 100)
    print("DETAILED MISS ANALYSIS")
    print("=" * 100)

    results = []
    for miss in MISSES:
        r = analyze_miss(data_5m, miss, levels, atrs)
        results.append(r)

        print(f"\n{'─' * 100}")
        print(f"MISS: {r['symbol']} {r['time']} {r['direction'].upper()} — {r['note']}")
        print(f"{'─' * 100}")
        print(f"  Price action at {r['time']}:")
        print(f"    O={r['open']:.2f} H={r['high']:.2f} L={r['low']:.2f} C={r['close']:.2f}")
        print(f"    Volume: {r['volume']:.0f} ({r['vol_ratio']:.1f}x avg)")
        print(f"  Indicators:")
        print(f"    EMA(21): {r['ema21']:.2f} — price {r['ema_status']} EMA, trend={r['ema_trend']}")
        print(f"    VWAP: {r['vwap']:.2f} — price {r['vwap_status']} VWAP")
        print(f"  Move quality (MFE):")
        print(f"    MFE = {r['mfe']:.2f} ({r['mfe_atr']:.2f} ATR) — {'SIGNIFICANT' if r['mfe_atr'] > 0.5 else 'MODERATE' if r['mfe_atr'] > 0.25 else 'SMALL'}")
        print(f"  Key levels:")
        print(f"    PD High: {r['pd_high']:.2f} (dist: {r['all_levels']['PD High']:.2f} ATR)")
        print(f"    PD Low: {r['pd_low']:.2f} (dist: {r['all_levels']['PD Low']:.2f} ATR)")
        print(f"    PD Close: {r['pd_close']:.2f} (dist: {r['all_levels']['PD Close']:.2f} ATR)")
        print(f"    Today Open: {r['today_open']:.2f} (dist: {r['all_levels']['Today Open']:.2f} ATR)")
        print(f"    ORB High: {r['orb_high']:.2f} (dist: {r['all_levels']['ORB High']:.2f} ATR)")
        print(f"    ORB Low: {r['orb_low']:.2f} (dist: {r['all_levels']['ORB Low']:.2f} ATR)")
        print(f"    VWAP: {r['vwap']:.2f} (dist: {r['all_levels']['VWAP']:.2f} ATR)")
        print(f"    → Nearest: {r['nearest_level']} ({r['nearest_dist_atr']:.2f} ATR away)")
        print(f"  Market context:")
        print(f"    SPY change from open: {r['spy_chg']:+.2f}%")

        # Diagnosis
        print(f"  DIAGNOSIS:")
        if r['nearest_dist_atr'] > 0.5:
            print(f"    ⚠ NO LEVEL NEARBY — nearest is {r['nearest_level']} at {r['nearest_dist_atr']:.1f} ATR")
            print(f"    → Root cause: No key level within trigger distance")
        elif r['ema_status'] != r['direction'].replace('bear', 'below').replace('bull', 'above'):
            ema_dir = "below" if r['direction'] == "bear" else "above"
            print(f"    ⚠ EMA GATE — price {r['ema_status']} EMA but move was {r['direction']}")
            if r['ema_trend'] != r['direction'].replace('bear', 'bear').replace('bull', 'bull'):
                print(f"    → EMA trend is {r['ema_trend']}, opposing the move direction")

        time_h = int(r['time'].split(':')[0])
        if time_h >= 11:
            print(f"    ⚠ MIDDAY DESERT — time {r['time']} is in the low-coverage zone")

        print(f"\n  5-bar window:")
        print(f"  {r['window']}")

    # Cross-symbol analysis
    print("\n" + "=" * 100)
    print("CROSS-SYMBOL ANALYSIS")
    print("=" * 100)

    # Check each miss time across all symbols
    for miss in MISSES:
        sym = miss["symbol"]
        h, m = map(int, miss["time"].split(":"))
        target_ts = pd.Timestamp(f"{TARGET_DATE.date()} {h:02d}:{m:02d}:00", tz=ET)

        print(f"\n  At {miss['time']} ({sym} {miss['direction']} miss):")
        for check_sym in SYMBOLS:
            df = data_5m[check_sym]
            if target_ts in df.index:
                bar = df.loc[target_ts]
                chg = ((bar["close"] - bar["open"]) / bar["open"]) * 100
                direction = "UP" if chg > 0.05 else "DOWN" if chg < -0.05 else "FLAT"
                print(f"    {check_sym}: {direction} {chg:+.2f}% (O={bar['open']:.2f} C={bar['close']:.2f})")
            else:
                # find nearest
                diffs = abs(df.index - target_ts)
                if len(diffs) > 0:
                    nearest_idx = diffs.argmin()
                    bar = df.iloc[nearest_idx]
                    chg = ((bar["close"] - bar["open"]) / bar["open"]) * 100
                    direction = "UP" if chg > 0.05 else "DOWN" if chg < -0.05 else "FLAT"
                    actual_time = df.index[nearest_idx].strftime("%H:%M")
                    print(f"    {check_sym}: {direction} {chg:+.2f}% at {actual_time} (O={bar['open']:.2f} C={bar['close']:.2f})")

    # Summary stats
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)

    total_mfe = sum(r['mfe_atr'] for r in results)
    sig_moves = [r for r in results if r['mfe_atr'] > 0.5]
    no_level = [r for r in results if r['nearest_dist_atr'] > 0.5]
    midday = [r for r in results if int(r['time'].split(':')[0]) >= 11]

    print(f"  Total misses analyzed: {len(results)}")
    print(f"  Total MFE missed: {total_mfe:.1f} ATR")
    print(f"  Significant moves (>0.5 ATR): {len(sig_moves)}")
    print(f"  No nearby level: {len(no_level)}")
    print(f"  Midday (11:00+): {len(midday)}")

    print("\n  Root cause breakdown:")
    causes = {"no_level": 0, "ema_gate": 0, "midday_desert": 0, "conf_issue": 0, "signal_type": 0}
    for r in results:
        if r['nearest_dist_atr'] > 0.5:
            causes["no_level"] += 1
        elif int(r['time'].split(':')[0]) >= 11:
            causes["midday_desert"] += 1
        else:
            causes["conf_issue"] += 1  # approximation

    for cause, count in causes.items():
        if count > 0:
            print(f"    {cause}: {count}")


if __name__ == "__main__":
    main()
