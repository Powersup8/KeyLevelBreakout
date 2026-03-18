#!/usr/bin/env python3
"""
AutoKLB Real-Data Harness — v3.8
==================================
DO NOT MODIFY — this is the evaluation harness.

Signal detection : native 5m bars (bars/)  →  Jan 2024 →
MFE/MAE tier    :
  signal >= HIGHRES_START (2025-09-02) : 15sec bars, 240 bars = 60 min
  signal >= ONEM_START    (2025-02-04) : 1m bars,    60 bars  = 60 min
  else                                 : 5m bars,    12 bars  = 60 min

Daily ATR: 1day bars (prior-day Wilder ATR)
"""

import sys
import time
import importlib
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
DEBUG_DIR   = Path(__file__).parent
CACHE_DIR   = Path(
    "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de"
    "/Meine Ablage/Claude/trading_bot/cache/bars"
)
HIGHRES_DIR = Path(
    "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de"
    "/Meine Ablage/Claude/trading_bot/cache/bars_highres/15sec"
)
LEVELS_PATH = DEBUG_DIR / "key-levels-db.parquet"

# ── Constants ─────────────────────────────────────────────────────────────────
SYMBOLS = [
    "SPY", "AAPL", "AMD", "AMZN", "GLD", "GOOGL", "META",
    "MSFT", "NFLX", "NVDA", "QQQ", "SLV", "TSLA", "XLE",
]

TRAIN_END      = date(2025, 9, 30)
VAL_END        = date(2026, 1, 31)
HIGHRES_START  = date(2025, 9, 2)   # 15sec data starts here
ONEM_START     = date(2025, 2, 4)   # 1m data starts here (most symbols)

MIN_SIGNALS_RAMP       = 100
WIN_RATE_BASELINE      = 0.50
COOLDOWN_5M            = 5          # bars; 5 × 5m = 25 min cooldown
MAX_SIGNALS_PER_SYM_DAY = 4        # capacity cap: max 4 signals per symbol per day

# Forward window = 60 minutes, expressed in bar counts
FWD_15SEC = 240   # 240 × 15s
FWD_1M    = 60    # 60 × 1m
FWD_5M    = 12    # 12 × 5m


# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ══════════════════════════════════════════════════════════════════════════════

def _load_ohlcv(path, rth=True):
    """Load any IB parquet, return tz-naive ET, RTH-filtered OHLCV."""
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


def load_5m(symbol):
    return _load_ohlcv(CACHE_DIR / f"{symbol.lower()}_5_mins_ib.parquet")

def load_1m(symbol):
    return _load_ohlcv(CACHE_DIR / f"{symbol.lower()}_1_min_ib.parquet")

def load_15sec(symbol):
    return _load_ohlcv(HIGHRES_DIR / f"{symbol.lower()}_15_secs_ib.parquet")

def load_daily_atr(symbol):
    """Return dict {Timestamp(date): atr_value} using prior-day Wilder ATR(14)."""
    path = CACHE_DIR / f"{symbol.lower()}_1_day_ib.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(path)
    if "date" in df.columns:
        df = df.set_index("date")
    df.index = pd.to_datetime(df.index).normalize()
    atr = _wilder_atr(df["high"], df["low"], df["close"], 14).shift(1)
    return {pd.Timestamp(dt): v for dt, v in atr.items() if not pd.isna(v)}


# ══════════════════════════════════════════════════════════════════════════════
# INDICATORS
# ══════════════════════════════════════════════════════════════════════════════

def _wilder_atr(high, low, close, period=14):
    prev = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev).abs(),
        (low  - prev).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()


def _wilder_adx(high, low, close, period=14):
    prev_high  = high.shift(1)
    prev_low   = low.shift(1)
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)
    up   = high - prev_high
    down = prev_low - low
    pdm  = pd.Series(np.where((up > down) & (up > 0),   up,   0.0), index=high.index)
    mdm  = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=high.index)
    a = 1 / period
    smt  = tr.ewm(alpha=a, min_periods=period, adjust=False).mean()
    smp  = pdm.ewm(alpha=a, min_periods=period, adjust=False).mean()
    smm  = mdm.ewm(alpha=a, min_periods=period, adjust=False).mean()
    pdi  = 100 * smp / smt.replace(0, np.nan)
    mdi  = 100 * smm / smt.replace(0, np.nan)
    denom = (pdi + mdi).replace(0, np.nan)
    dx   = 100 * (pdi - mdi).abs() / denom
    return dx.ewm(alpha=a, min_periods=period, adjust=False).mean()


def compute_indicators(df_5m):
    """Add lagged indicator columns to 5m OHLCV DataFrame."""
    df = df_5m.copy()
    df["ema20"]     = df["close"].ewm(span=20, adjust=False).mean()
    df["ema50"]     = df["close"].ewm(span=50, adjust=False).mean()
    df["adx"]       = _wilder_adx(df["high"], df["low"], df["close"], 14)
    df["vol_sma20"] = df["volume"].rolling(20).mean()

    # Session VWAP — reset each calendar day (vectorized)
    df["_date"] = df.index.date
    df["_tp"]   = (df["high"] + df["low"] + df["close"]) / 3
    df["_tpv"]  = df["_tp"] * df["volume"]
    df["vwap"]  = (df.groupby("_date")["_tpv"].cumsum() /
                   df.groupby("_date")["volume"].cumsum().replace(0, np.nan))
    df.drop(columns=["_date", "_tp", "_tpv"], inplace=True)

    # Lag all by 1 (Pine [1] = confirmed prior bar)
    for col in ["ema20", "ema50", "adx", "vwap", "vol_sma20"]:
        df[f"{col}_p"] = df[col].shift(1)
    df["close_p"]  = df["close"].shift(1)
    df["close_p2"] = df["close"].shift(2)
    df.drop(columns=["ema20", "ema50", "adx", "vwap", "vol_sma20"], inplace=True)
    return df


# ══════════════════════════════════════════════════════════════════════════════
# FORWARD P&L
# ══════════════════════════════════════════════════════════════════════════════

def _forward_pnl(df, signal_ts, direction, daily_atr, n):
    """Compute MFE/MAE over n bars from signal_ts."""
    if df is None or len(df) == 0:
        return np.nan, np.nan
    idx = df.index.searchsorted(signal_ts)
    if idx >= len(df):
        return np.nan, np.nan
    entry  = df.iloc[idx]["close"]
    future = df.iloc[idx + 1: idx + 1 + n]
    if len(future) < max(3, n // 4):
        return np.nan, np.nan
    if direction == "bull":
        mfe = (future["high"].max() - entry) / daily_atr
        mae = (entry - future["low"].min())  / daily_atr
    else:
        mfe = (entry - future["low"].min())  / daily_atr
        mae = (future["high"].max() - entry) / daily_atr
    return max(0.0, mfe), max(0.0, mae)


def get_forward_pnl(signal_ts, direction, daily_atr, df_5m, df_1m, df_15sec):
    """Choose highest-resolution available data for MFE/MAE."""
    d = signal_ts.date()
    if d >= HIGHRES_START and df_15sec is not None:
        mfe, mae = _forward_pnl(df_15sec, signal_ts, direction, daily_atr, FWD_15SEC)
        if not (np.isnan(mfe) or np.isnan(mae)):
            return mfe, mae
    if d >= ONEM_START and df_1m is not None:
        mfe, mae = _forward_pnl(df_1m, signal_ts, direction, daily_atr, FWD_1M)
        if not (np.isnan(mfe) or np.isnan(mae)):
            return mfe, mae
    return _forward_pnl(df_5m, signal_ts, direction, daily_atr, FWD_5M)


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

def _timing(ts):
    from datetime import time as dtime
    t = ts.time()
    if t < dtime(9, 35):   return "open_flush"
    if t < dtime(11, 30):  return "morning"
    if t < dtime(14, 0):   return "midday"
    return "afternoon"


def _level_interaction(close, prev_close, bar_high, bar_low, level_price):
    if prev_close < level_price <= close:   return "broke_through"
    if prev_close > level_price >= close:   return "broke_through"
    if bar_low <= level_price <= bar_high:  return "reversed_at"
    return "near"


def build_row(symbol, ts, bar, daily_atr, level_type, dist_atr, interaction):
    bar_range  = bar["high"] - bar["low"]
    direction  = "bull" if bar["close"] >= bar["open"] else "bear"
    body_pct   = (abs(bar["close"] - bar["open"]) / bar_range * 100
                  if bar_range > 0 else 0.0)
    ema20_p, ema50_p = bar["ema20_p"], bar["ema50_p"]
    ema_bull   = ema20_p > ema50_p if not (pd.isna(ema20_p) or pd.isna(ema50_p)) else False
    ema_bear   = ema20_p < ema50_p if not (pd.isna(ema20_p) or pd.isna(ema50_p)) else False
    vwap_p     = bar["vwap_p"]
    vwap_bull  = bar["close"] > vwap_p if not pd.isna(vwap_p) else False
    vwap_bear  = bar["close"] < vwap_p if not pd.isna(vwap_p) else False
    vol_sma    = bar["vol_sma20_p"]
    vol_ratio  = bar["volume"] / vol_sma if (not pd.isna(vol_sma) and vol_sma > 0) else 0.0
    trig_range = bar_range / daily_atr if daily_atr > 0 else np.nan
    return {
        "nearest_level_type":      level_type,
        "nearest_level_dist_atr":  dist_atr,
        "direction":               direction,
        "symbol":                  symbol,
        "trig_ema_aligned":        ema_bull if direction == "bull" else ema_bear,
        "trig_body_pct":           body_pct,
        "trig_vol_ratio":          vol_ratio,
        "pre_adx":                 bar["adx_p"] if not pd.isna(bar["adx_p"]) else 0.0,
        "trig_vwap_aligned":       vwap_bull if direction == "bull" else vwap_bear,
        "timing_category":         _timing(ts),
        "level_interaction":       interaction,
        "pre_vol_avg_ratio":       vol_ratio,
        "trig_range_atr":          trig_range,
        "spy_magnitude_atr":       np.nan,
    }


# ══════════════════════════════════════════════════════════════════════════════
# SIGNAL EMISSION
# ══════════════════════════════════════════════════════════════════════════════

def emit_signals(symbol, df_5m_ind, levels_sym, daily_atr_map):
    import autoklb_signals as sig
    importlib.reload(sig)

    # Pre-group levels by date for O(1) lookup (avoid O(N) filter per bar)
    levels_by_date = {}
    for d, grp in levels_sym.groupby("date"):
        levels_by_date[d] = grp[["level_name", "level_price"]].to_dict("records")

    fired    = []
    cooldown = {}
    bars     = list(df_5m_ind.iterrows())

    for i, (ts, bar) in enumerate(bars):
        if pd.isna(bar.get("ema20_p")) or pd.isna(bar.get("adx_p")):
            continue
        bar_date   = ts.date()
        daily_atr  = daily_atr_map.get(pd.Timestamp(bar_date), np.nan)
        if np.isnan(daily_atr) or daily_atr <= 0:
            continue
        levels_today = levels_by_date.get(pd.Timestamp(bar_date), [])
        if not levels_today:
            continue
        prev_close = bar.get("close_p", np.nan)
        if pd.isna(prev_close):
            continue

        prox_atr = sig.LEVEL_PROXIMITY_ATR * 1.5

        for lvl in levels_today:
            level_price = lvl["level_price"]
            dist_atr    = abs(bar["close"] - level_price) / daily_atr
            if dist_atr > prox_atr:
                continue
            direction = "bull" if bar["close"] >= bar["open"] else "bear"
            cd_key    = (lvl["level_name"], direction)
            if cd_key in cooldown and (i - cooldown[cd_key]) < COOLDOWN_5M:
                continue
            interaction = _level_interaction(
                bar["close"], prev_close, bar["high"], bar["low"], level_price)
            row    = build_row(symbol, ts, bar, daily_atr,
                               lvl["level_name"], dist_atr, interaction)
            result = sig.classify_signal(row)  # dict supports [] and .get()
            if result["would_fire"] and not result["is_dimmed"]:
                cooldown[cd_key] = i
                fired.append({
                    "symbol":      symbol,
                    "date":        bar_date,
                    "timestamp":   ts,
                    "direction":   direction,
                    "signal_type": result["signal_type"],
                    "level_type":  lvl["level_name"],
                    "timing":      _timing(ts),
                    "daily_atr":   daily_atr,
                })
    return fired


# ══════════════════════════════════════════════════════════════════════════════
# SCORING
# ══════════════════════════════════════════════════════════════════════════════

def compute_pnl(row):
    mfe, mae = row["mfe"], row["mae"]
    if mfe >= 0.10 and mfe > mae:
        return mfe - mae
    return -mae


def compute_score(df):
    if len(df) == 0:
        return 0.0, 0.0, 0.0, 0
    pnls     = df["pnl_atr"]
    net_atr  = pnls.sum()
    n        = len(df)
    win_rate = (pnls > 0).mean()
    score    = net_atr * (win_rate / WIN_RATE_BASELINE) * min(1.0, n / MIN_SIGNALS_RAMP)
    return score, net_atr, win_rate, n


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    t0 = time.time()

    levels_db = pd.read_parquet(LEVELS_PATH)
    levels_db["date"] = pd.to_datetime(levels_db["date"])

    all_signals = []

    for symbol in SYMBOLS:
        df_5m = load_5m(symbol)
        if df_5m is None or len(df_5m) == 0:
            continue

        daily_atr_map = load_daily_atr(symbol)
        df_5m_ind     = compute_indicators(df_5m)
        levels_sym    = levels_db[levels_db["symbol"] == symbol].copy()

        # Load MFE/MAE resolution tiers
        df_1m    = load_1m(symbol)
        df_15sec = load_15sec(symbol)

        fired = emit_signals(symbol, df_5m_ind, levels_sym, daily_atr_map)

        for sig in fired:
            mfe, mae = get_forward_pnl(
                sig["timestamp"], sig["direction"], sig["daily_atr"],
                df_5m, df_1m, df_15sec,
            )
            if not (np.isnan(mfe) or np.isnan(mae)):
                sig["mfe"] = mfe
                sig["mae"] = mae
                all_signals.append(sig)

    if not all_signals:
        print("rd_train_score:    0.0")
        print("rd_val_score:      0.0")
        return

    df          = pd.DataFrame(all_signals)
    df["date_dt"] = pd.to_datetime(df["date"])

    # Capacity cap: keep first MAX_SIGNALS_PER_SYM_DAY per symbol per day
    # Penalises wide proximity (too many signals = unrealistic trading volume)
    df = (df.sort_values(["symbol", "date_dt", "timestamp"])
            .groupby(["symbol", "date_dt"])
            .head(MAX_SIGNALS_PER_SYM_DAY)
            .reset_index(drop=True))

    df["pnl_atr"] = df.apply(compute_pnl, axis=1)

    train = df[df["date_dt"] <= pd.Timestamp(TRAIN_END)]
    val   = df[
        (df["date_dt"] >  pd.Timestamp(TRAIN_END)) &
        (df["date_dt"] <= pd.Timestamp(VAL_END))
    ]

    ts, tn, twr, tN = compute_score(train)
    vs, vn, vwr, vN = compute_score(val)
    elapsed = time.time() - t0

    print("---rd---")
    print(f"rd_train_score:    {ts:.1f}")
    print(f"rd_train_net_atr:  {tn:.1f}")
    print(f"rd_train_win_rate: {twr * 100:.1f}")
    print(f"rd_train_n:        {tN}")
    print(f"rd_val_score:      {vs:.1f}")
    print(f"rd_val_net_atr:    {vn:.1f}")
    print(f"rd_val_win_rate:   {vwr * 100:.1f}")
    print(f"rd_val_n:          {vN}")
    print(f"rd_total_seconds:  {elapsed:.1f}")


if __name__ == "__main__":
    main()
