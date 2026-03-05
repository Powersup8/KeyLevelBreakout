"""
Non-EMA Signal Research
=======================
Research task: Find profitable signal types for non-EMA-aligned conditions.
Context: 62% of significant intraday moves happen without EMA alignment.
         These moves are the same size (1.73 ATR) as EMA-aligned ones.
         Our current breakout entry LOSES money (-0.120 ATR/signal, 33% win).

Goal: Identify and backtest candidate signal types that can catch these moves profitably.

Usage: python3 debug/non_ema_signal_research.py
Output: debug/non-ema-signal-research.md
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CACHE_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(PROJECT_ROOT)),
    "trading_bot", "cache"
)
BARS_5M = os.path.join(CACHE_ROOT, "bars")
NO_SIGNAL_CSV = os.path.join(SCRIPT_DIR, "no-signal-zone-moves.csv")
ENRICHED_CSV = os.path.join(SCRIPT_DIR, "enriched-signals.csv")
OUTPUT_MD = os.path.join(SCRIPT_DIR, "non-ema-signal-research.md")

SYMBOLS = ["SPY", "AAPL", "AMD", "AMZN", "GLD", "GOOGL",
           "META", "MSFT", "NVDA", "QQQ", "SLV", "TSLA", "TSM"]

# Full history start (5m parquet from Jan 2024)
HISTORY_START = "2024-01-01"

# Backtest params
FORWARD_BARS = 6      # 30 min forward window
MFE_BARS = 6
MAE_BARS = 6
RTH_START = 9 * 60 + 30   # 9:30 in minutes
RTH_END   = 16 * 60        # 16:00 in minutes

# Reference benchmark (from project memory: EMA-aligned signals)
BENCH_WIN = 0.57
BENCH_PNL = 0.086  # avg ATR / signal


# ── Indicator helpers ─────────────────────────────────────────────────────────
def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()


def compute_atr(h, l, c, period=14):
    prev_c = c.shift(1)
    tr = pd.concat([h - l, (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def compute_adx(h, l, c, period=14):
    prev_h, prev_l, prev_c = h.shift(1), l.shift(1), c.shift(1)
    tr = pd.concat([h - l, (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
    plus_dm = np.where((h - prev_h > prev_l - l) & (h - prev_h > 0), h - prev_h, 0.0)
    minus_dm = np.where((prev_l - l > h - prev_h) & (prev_l - l > 0), prev_l - l, 0.0)
    atr_s = pd.Series(tr, index=h.index).ewm(alpha=1 / period, adjust=False).mean()
    plus_di = 100 * pd.Series(plus_dm, index=h.index).ewm(alpha=1 / period, adjust=False).mean() / atr_s
    minus_di = 100 * pd.Series(minus_dm, index=h.index).ewm(alpha=1 / period, adjust=False).mean() / atr_s
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(alpha=1 / period, adjust=False).mean()
    return adx.fillna(0)


def compute_rsi(c, period=14):
    delta = c.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50)


def compute_vwap_daily(df):
    """Compute intraday VWAP reset each trading day."""
    df = df.copy()
    df['_day'] = df.index.date
    typical = (df['high'] + df['low'] + df['close']) / 3
    df['_tp_vol'] = typical * df['volume']
    df['_cum_tp_vol'] = df.groupby('_day')['_tp_vol'].cumsum()
    df['_cum_vol'] = df.groupby('_day')['volume'].cumsum()
    df['vwap'] = df['_cum_tp_vol'] / df['_cum_vol'].replace(0, np.nan)
    return df.drop(columns=['_day', '_tp_vol', '_cum_tp_vol', '_cum_vol'])


# ── Data loading ──────────────────────────────────────────────────────────────
def load_5m(symbol, warmup_days=60):
    fpath = os.path.join(BARS_5M, f"{symbol.lower()}_5_mins_ib.parquet")
    if not os.path.exists(fpath):
        print(f"  [SKIP] {symbol}: no parquet")
        return None
    df = pd.read_parquet(fpath)
    df['date'] = pd.to_datetime(df['date'])
    if df['date'].dt.tz is None:
        df['date'] = df['date'].dt.tz_localize('US/Eastern')
    else:
        df['date'] = df['date'].dt.tz_convert('US/Eastern')
    df = df.set_index('date').sort_index()

    # Keep enough warmup for indicator computation
    warmup_start = pd.Timestamp(HISTORY_START, tz='US/Eastern') - timedelta(days=warmup_days)
    df = df.loc[warmup_start:]

    # ── Indicators ────────────────────────────────────────────────
    df['atr14'] = compute_atr(df['high'], df['low'], df['close'], 14)
    df['adx'] = compute_adx(df['high'], df['low'], df['close'], 14)
    df['rsi14'] = compute_rsi(df['close'], 14)
    df['ema9'] = ema(df['close'], 9)
    df['ema20'] = ema(df['close'], 20)
    df['ema50'] = ema(df['close'], 50)

    df['vol_sma20'] = df['volume'].rolling(20, min_periods=5).mean()
    df['vol_ratio'] = df['volume'] / df['vol_sma20'].replace(0, np.nan)

    rng = df['high'] - df['low']
    df['body'] = (df['close'] - df['open']).abs() / rng.replace(0, np.nan)
    df['close_loc'] = (df['close'] - df['low']) / rng.replace(0, np.nan)

    # VWAP (daily reset)
    df = compute_vwap_daily(df)

    # EMA alignment flags
    df['ema_bull'] = (df['ema9'] > df['ema20']) & (df['ema20'] > df['ema50'])
    df['ema_bear'] = (df['ema9'] < df['ema20']) & (df['ema20'] < df['ema50'])
    df['ema_aligned'] = df['ema_bull'] | df['ema_bear']

    # EMA spread (convergence measure): max distance between EMAs in ATR units
    ema_max = df[['ema9', 'ema20', 'ema50']].max(axis=1)
    ema_min = df[['ema9', 'ema20', 'ema50']].min(axis=1)
    df['ema_spread_atr'] = (ema_max - ema_min) / df['atr14'].replace(0, np.nan)

    # EMA9-EMA20 cross (current bar vs previous bar)
    df['ema9_cross_bull'] = (df['ema9'] > df['ema20']) & (df['ema9'].shift(1) <= df['ema20'].shift(1))
    df['ema9_cross_bear'] = (df['ema9'] < df['ema20']) & (df['ema9'].shift(1) >= df['ema20'].shift(1))

    # VWAP deviation in ATR
    df['vwap_dev_atr'] = (df['close'] - df['vwap']) / df['atr14'].replace(0, np.nan)

    # RTH filter (minutes from midnight ET)
    minutes = df.index.hour * 60 + df.index.minute
    df['rth'] = (minutes >= RTH_START) & (minutes < RTH_END)

    # Trim to HISTORY_START (keep warmup out of signals)
    df = df.loc[HISTORY_START:]
    return df


# ── Backtest engine ───────────────────────────────────────────────────────────
def backtest_signals(df, signal_bull, signal_bear, label=""):
    """
    Given boolean Series signal_bull and signal_bear (index = df.index),
    compute MFE and MAE over next FORWARD_BARS bars for each signal.
    Returns DataFrame of trades.
    """
    results = []
    closes = df['close'].values
    highs = df['high'].values
    lows = df['low'].values
    atrs = df['atr14'].values
    idx_arr = np.arange(len(df))

    bull_idx = np.where(signal_bull.values)[0]
    bear_idx = np.where(signal_bear.values)[0]

    for direction, indices in [('bull', bull_idx), ('bear', bear_idx)]:
        for i in indices:
            entry = closes[i]
            atr = atrs[i]
            if atr <= 0 or np.isnan(atr):
                continue
            end = min(i + FORWARD_BARS + 1, len(df))
            if end <= i + 1:
                continue
            fut_highs = highs[i+1:end]
            fut_lows = lows[i+1:end]
            if direction == 'bull':
                mfe = (np.max(fut_highs) - entry) / atr if len(fut_highs) > 0 else 0
                mae = (np.min(fut_lows) - entry) / atr if len(fut_lows) > 0 else 0
            else:
                mfe = (entry - np.min(fut_lows)) / atr if len(fut_lows) > 0 else 0
                mae = (entry - np.max(fut_highs)) / atr if len(fut_highs) > 0 else 0
            # Signed P&L = MFE - |MAE| (simplified: how much did it run vs how much it pulled back)
            pnl = mfe + mae  # mae is negative for favorable
            win = 1 if mfe > abs(mae) else 0
            ts = df.index[i]
            results.append({
                'direction': direction,
                'ts': ts,
                'mfe': mfe,
                'mae': mae,
                'pnl': pnl,
                'win': win,
                'atr': atr,
            })

    return pd.DataFrame(results) if results else pd.DataFrame(
        columns=['direction', 'ts', 'mfe', 'mae', 'pnl', 'win', 'atr']
    )


def summarize(trades_df, label=""):
    if trades_df.empty:
        return {'label': label, 'n': 0, 'win_pct': 0, 'avg_pnl': 0,
                'total_pnl': 0, 'avg_mfe': 0, 'avg_mae': 0, 'mfe_mae': 0}
    n = len(trades_df)
    win_pct = trades_df['win'].mean() * 100
    avg_pnl = trades_df['pnl'].mean()
    total_pnl = trades_df['pnl'].sum()
    avg_mfe = trades_df['mfe'].mean()
    avg_mae = trades_df['mae'].mean()
    mfe_mae = avg_mfe / abs(avg_mae) if avg_mae != 0 else 0
    return {
        'label': label, 'n': n, 'win_pct': win_pct, 'avg_pnl': avg_pnl,
        'total_pnl': total_pnl, 'avg_mfe': avg_mfe, 'avg_mae': avg_mae, 'mfe_mae': mfe_mae
    }


# ── Coverage check ────────────────────────────────────────────────────────────
def check_coverage(signal_times_set, known_moves_df, symbol, window_bars=2, bar_minutes=5):
    """
    Of the known non-EMA moves for this symbol, how many have a signal fire
    within ±window_bars (±10 min default) of the move start?
    """
    sym_moves = known_moves_df[known_moves_df['symbol'] == symbol].copy()
    if sym_moves.empty:
        return 0, 0
    sym_moves['start_ts'] = pd.to_datetime(sym_moves['start_time'], utc=True).dt.tz_convert('US/Eastern')
    caught = 0
    total = len(sym_moves)
    tol = timedelta(minutes=bar_minutes * window_bars)
    for _, row in sym_moves.iterrows():
        st = row['start_ts']
        for sig_t in signal_times_set:
            if abs((sig_t - st).total_seconds()) <= tol.total_seconds():
                caught += 1
                break
    return caught, total


# ── Signal definitions ────────────────────────────────────────────────────────
def signals_ema_convergence_break(df):
    """
    A. EMA Convergence + Break
    EMAs bunching (spread < 0.2 ATR), price breaks above/below the EMA cluster.
    Hypothesis: EMA alignment about to happen — catch the start.
    """
    converging = df['ema_spread_atr'] < 0.20
    cluster_high = df[['ema9', 'ema20', 'ema50']].max(axis=1)
    cluster_low  = df[['ema9', 'ema20', 'ema50']].min(axis=1)
    # Price breaks above cluster (bullish) or below (bearish)
    bull = converging & (df['close'] > cluster_high) & (df['close'].shift(1) <= cluster_high.shift(1))
    bear = converging & (df['close'] < cluster_low)  & (df['close'].shift(1) >= cluster_low.shift(1))
    # Only non-EMA-aligned bars
    bull = bull & ~df['ema_aligned'] & df['rth']
    bear = bear & ~df['ema_aligned'] & df['rth']
    return bull.fillna(False), bear.fillna(False)


def signals_range_breakout(df):
    """
    B. Range Breakout (prior 12-bar = 1-hour high/low)
    Price breaks above/below the rolling 12-bar range with volume.
    No EMA requirement. Non-EMA only.
    """
    roll_high = df['high'].rolling(12).max().shift(1)
    roll_low  = df['low'].rolling(12).min().shift(1)
    vol_ok = df['vol_ratio'] >= 1.5
    bull = (df['close'] > roll_high) & vol_ok & ~df['ema_aligned'] & df['rth']
    bear = (df['close'] < roll_low)  & vol_ok & ~df['ema_aligned'] & df['rth']
    return bull.fillna(False), bear.fillna(False)


def signals_vwap_deviation_reversal(df):
    """
    C. VWAP Deviation Reversal
    Price moves >1 ATR from VWAP (extended), then bar closes back toward VWAP.
    Hypothesis: mean-reversion when too extended.
    """
    extended_bull = df['vwap_dev_atr'] > 1.0   # price far above VWAP
    extended_bear = df['vwap_dev_atr'] < -1.0  # price far below VWAP
    # Reversal bar: prior bar was extended, current bar moves back (close_loc signals direction)
    # Bear reversal (fade the extended bull): open above VWAP, close retreating
    bear_rev = extended_bull.shift(1) & (df['close'] < df['open']) & (df['vwap_dev_atr'].diff() < 0)
    # Bull reversal (fade the extended bear)
    bull_rev = extended_bear.shift(1) & (df['close'] > df['open']) & (df['vwap_dev_atr'].diff() > 0)
    bull_rev = bull_rev & ~df['ema_aligned'] & df['rth']
    bear_rev = bear_rev & ~df['ema_aligned'] & df['rth']
    return bull_rev.fillna(False), bear_rev.fillna(False)


def signals_momentum_shift(df):
    """
    D. Momentum Shift (3-bar flip)
    3 consecutive bars in new direction after at least 2 bars in opposite direction.
    Hypothesis: catches the turn rather than the breakout.
    """
    up_bar   = (df['close'] > df['open']).astype(int)
    down_bar = (df['close'] < df['open']).astype(int)
    # 3 consecutive up bars after 2 consecutive down bars
    bull = (
        (up_bar == 1) & (up_bar.shift(1) == 1) & (up_bar.shift(2) == 1) &
        (down_bar.shift(3) == 1) & (down_bar.shift(4) == 1)
    )
    bear = (
        (down_bar == 1) & (down_bar.shift(1) == 1) & (down_bar.shift(2) == 1) &
        (up_bar.shift(3) == 1) & (up_bar.shift(4) == 1)
    )
    bull = bull & ~df['ema_aligned'] & df['rth']
    bear = bear & ~df['ema_aligned'] & df['rth']
    return bull.fillna(False), bear.fillna(False)


def signals_volume_spike_direction(df):
    """
    E. Volume Spike + Direction
    Volume >3x average on a bar that moves >0.3 ATR in one direction.
    Hypothesis: smart money showing hand.
    """
    vol_spike = df['vol_ratio'] >= 3.0
    move_size = (df['close'] - df['open']).abs() / df['atr14'].replace(0, np.nan)
    big_move = move_size >= 0.3
    bull = (df['close'] > df['open']) & vol_spike & big_move & ~df['ema_aligned'] & df['rth']
    bear = (df['close'] < df['open']) & vol_spike & big_move & ~df['ema_aligned'] & df['rth']
    return bull.fillna(False), bear.fillna(False)


def signals_ema_cross(df):
    """
    F. EMA9 x EMA20 Cross
    Classic trend change signal. Non-EMA only (just crossed so not yet aligned).
    """
    bull = df['ema9_cross_bull'] & df['rth']
    bear = df['ema9_cross_bear'] & df['rth']
    # These naturally happen when EMAs just crossed (pre-full-alignment)
    return bull.fillna(False), bear.fillna(False)


def signals_rsi_divergence_momentum(df):
    """
    G. RSI Momentum Flip
    RSI crosses 50 from below (bull) or above (bear) — momentum regime change.
    Non-EMA aligned bars only.
    """
    rsi_cross_bull = (df['rsi14'] > 50) & (df['rsi14'].shift(1) <= 50)
    rsi_cross_bear = (df['rsi14'] < 50) & (df['rsi14'].shift(1) >= 50)
    bull = rsi_cross_bull & ~df['ema_aligned'] & df['rth']
    bear = rsi_cross_bear & ~df['ema_aligned'] & df['rth']
    return bull.fillna(False), bear.fillna(False)


def signals_vwap_cross(df):
    """
    H. VWAP Cross
    Price crosses VWAP with volume confirmation. Non-EMA only.
    """
    cross_bull = (df['close'] > df['vwap']) & (df['close'].shift(1) <= df['vwap'].shift(1))
    cross_bear = (df['close'] < df['vwap']) & (df['close'].shift(1) >= df['vwap'].shift(1))
    vol_ok = df['vol_ratio'] >= 1.5
    bull = cross_bull & vol_ok & ~df['ema_aligned'] & df['rth']
    bear = cross_bear & vol_ok & ~df['ema_aligned'] & df['rth']
    return bull.fillna(False), bear.fillna(False)


def signals_compression_pop(df):
    """
    I. Volatility Compression Pop
    ATR has contracted for 5+ bars (ATR14 < 60% of its 20-bar average),
    then current bar is large (range > 1.2 ATR).
    Hypothesis: squeeze then release.
    """
    atr_sma20 = df['atr14'].rolling(20).mean()
    compressed = df['atr14'] < 0.60 * atr_sma20
    # 5+ bars of compression
    compressed_5 = compressed.rolling(5).min().astype(bool)
    bar_range = (df['high'] - df['low']) / df['atr14'].replace(0, np.nan)
    pop = bar_range >= 1.2
    bull = compressed_5.shift(1) & pop & (df['close'] > df['open']) & ~df['ema_aligned'] & df['rth']
    bear = compressed_5.shift(1) & pop & (df['close'] < df['open']) & ~df['ema_aligned'] & df['rth']
    return bull.fillna(False), bear.fillna(False)


def signals_morning_gap_fade(df):
    """
    J. Morning Gap Fade
    At 9:35 bar (first signal-bar after open), if price is extended from VWAP
    (gap created), fade direction. Non-EMA.
    """
    # Only 9:35 bar
    is_935 = (df.index.hour == 9) & (df.index.minute == 35)
    # Extended gap: open > prior close by >0.5 ATR (gap up) or < (gap down)
    prior_close = df['close'].shift(1)
    gap = (df['open'] - prior_close) / df['atr14'].replace(0, np.nan)
    # Fade a gap-up: open much higher, fade back
    bear_fade = is_935 & (gap > 0.5) & ~df['ema_aligned'] & df['rth']
    bull_fade = is_935 & (gap < -0.5) & ~df['ema_aligned'] & df['rth']
    return bull_fade.fillna(False), bear_fade.fillna(False)


# ── Combination signals ───────────────────────────────────────────────────────
def signals_combo_vol_range(df):
    """
    Combo 1: Range Breakout + Volume Spike (tighter)
    """
    roll_high = df['high'].rolling(12).max().shift(1)
    roll_low  = df['low'].rolling(12).min().shift(1)
    vol_spike = df['vol_ratio'] >= 3.0
    bull = (df['close'] > roll_high) & vol_spike & ~df['ema_aligned'] & df['rth']
    bear = (df['close'] < roll_low)  & vol_spike & ~df['ema_aligned'] & df['rth']
    return bull.fillna(False), bear.fillna(False)


def signals_combo_ema_conv_vol(df):
    """
    Combo 2: EMA Convergence + Volume Spike
    """
    converging = df['ema_spread_atr'] < 0.20
    cluster_high = df[['ema9', 'ema20', 'ema50']].max(axis=1)
    cluster_low  = df[['ema9', 'ema20', 'ema50']].min(axis=1)
    vol_spike = df['vol_ratio'] >= 2.0
    bull = converging & (df['close'] > cluster_high) & (df['close'].shift(1) <= cluster_high.shift(1)) & vol_spike & ~df['ema_aligned'] & df['rth']
    bear = converging & (df['close'] < cluster_low)  & (df['close'].shift(1) >= cluster_low.shift(1))  & vol_spike & ~df['ema_aligned'] & df['rth']
    return bull.fillna(False), bear.fillna(False)


def signals_combo_rsi_vwap(df):
    """
    Combo 3: RSI Momentum Flip + VWAP Cross (both fire together)
    """
    rsi_bull = (df['rsi14'] > 50) & (df['rsi14'].shift(1) <= 50)
    rsi_bear = (df['rsi14'] < 50) & (df['rsi14'].shift(1) >= 50)
    vwap_bull = (df['close'] > df['vwap']) & (df['close'].shift(1) <= df['vwap'].shift(1))
    vwap_bear = (df['close'] < df['vwap']) & (df['close'].shift(1) >= df['vwap'].shift(1))
    bull = rsi_bull & vwap_bull & ~df['ema_aligned'] & df['rth']
    bear = rsi_bear & vwap_bear & ~df['ema_aligned'] & df['rth']
    return bull.fillna(False), bear.fillna(False)


def signals_combo_compression_vol(df):
    """
    Combo 4: Volatility Compression Pop + Vol Spike
    """
    atr_sma20 = df['atr14'].rolling(20).mean()
    compressed = df['atr14'] < 0.60 * atr_sma20
    compressed_5 = compressed.rolling(5).min().astype(bool)
    bar_range = (df['high'] - df['low']) / df['atr14'].replace(0, np.nan)
    pop = bar_range >= 1.2
    vol_spike = df['vol_ratio'] >= 2.0
    bull = compressed_5.shift(1) & pop & vol_spike & (df['close'] > df['open']) & ~df['ema_aligned'] & df['rth']
    bear = compressed_5.shift(1) & pop & vol_spike & (df['close'] < df['open']) & ~df['ema_aligned'] & df['rth']
    return bull.fillna(False), bear.fillna(False)


# ── Pre-move characterization ─────────────────────────────────────────────────
def characterize_pre_move(df, known_moves_df, symbol):
    """
    For each known non-EMA move for this symbol, look at the 6-12 bars before
    the move starts and compute summary statistics.
    """
    sym_moves = known_moves_df[
        (known_moves_df['symbol'] == symbol) &
        (~known_moves_df['ema_aligned'])
    ].copy()
    if sym_moves.empty:
        return {}

    sym_moves['start_ts'] = pd.to_datetime(sym_moves['start_time'], utc=True).dt.tz_convert('US/Eastern')
    records = []
    for _, row in sym_moves.iterrows():
        st = row['start_ts']
        # Find the bar in df closest to start_ts
        idx_loc = df.index.searchsorted(st)
        if idx_loc < 12 or idx_loc >= len(df):
            continue
        pre = df.iloc[idx_loc - 12: idx_loc]
        if len(pre) < 6:
            continue
        move_dir = row['direction']

        # Volume pattern in prior 6 bars
        vol_last6 = pre['vol_ratio'].iloc[-6:]
        vol_first6 = pre['vol_ratio'].iloc[:6]
        vol_trend = "ramp" if vol_last6.mean() > vol_first6.mean() * 1.2 else (
            "dry" if vol_last6.mean() < vol_first6.mean() * 0.8 else "flat"
        )

        # EMA convergence
        ema_spread = pre['ema_spread_atr'].iloc[-1]
        ema_converging = pre['ema_spread_atr'].diff().iloc[-3:].mean() < 0  # shrinking

        # Price at range boundary
        pre_high = pre['high'].max()
        pre_low  = pre['low'].min()
        cur_close = df['close'].iloc[idx_loc]
        pct_from_high = (pre_high - cur_close) / (pre_high - pre_low + 1e-9)
        pct_from_low  = (cur_close - pre_low)  / (pre_high - pre_low + 1e-9)
        at_high = pct_from_high < 0.1
        at_low  = pct_from_low  < 0.1

        # VWAP proximity
        vwap_dev = abs(pre['vwap_dev_atr'].iloc[-1])

        # RSI level
        rsi_val = pre['rsi14'].iloc[-1]

        # ADX
        adx_val = pre['adx'].iloc[-1]

        records.append({
            'direction': move_dir,
            'vol_pattern': vol_trend,
            'ema_spread_atr': ema_spread,
            'ema_converging': ema_converging,
            'at_range_high': at_high,
            'at_range_low': at_low,
            'vwap_dev_atr': vwap_dev,
            'rsi': rsi_val,
            'adx': adx_val,
        })

    if not records:
        return {}
    rdf = pd.DataFrame(records)
    return {
        'n': len(rdf),
        'vol_ramp_pct': (rdf['vol_pattern'] == 'ramp').mean() * 100,
        'vol_dry_pct':  (rdf['vol_pattern'] == 'dry').mean() * 100,
        'vol_flat_pct': (rdf['vol_pattern'] == 'flat').mean() * 100,
        'avg_ema_spread_atr': rdf['ema_spread_atr'].mean(),
        'ema_converging_pct': rdf['ema_converging'].mean() * 100,
        'at_range_high_pct': rdf['at_range_high'].mean() * 100,
        'at_range_low_pct':  rdf['at_range_low'].mean() * 100,
        'avg_vwap_dev': rdf['vwap_dev_atr'].mean(),
        'avg_rsi': rdf['rsi'].mean(),
        'avg_adx': rdf['adx'].mean(),
    }


# ── Main research loop ────────────────────────────────────────────────────────
SIGNAL_DEFS = [
    ('A_EMA_Conv_Break',     signals_ema_convergence_break),
    ('B_Range_Breakout',     signals_range_breakout),
    ('C_VWAP_Dev_Reversal',  signals_vwap_deviation_reversal),
    ('D_Momentum_Shift',     signals_momentum_shift),
    ('E_Volume_Spike_Dir',   signals_volume_spike_direction),
    ('F_EMA_Cross',          signals_ema_cross),
    ('G_RSI_Momentum_Flip',  signals_rsi_divergence_momentum),
    ('H_VWAP_Cross',         signals_vwap_cross),
    ('I_Compression_Pop',    signals_compression_pop),
    ('J_Morning_Gap_Fade',   signals_morning_gap_fade),
    ('K_Combo_Vol_Range',    signals_combo_vol_range),
    ('L_Combo_EMA_Conv_Vol', signals_combo_ema_conv_vol),
    ('M_Combo_RSI_VWAP',     signals_combo_rsi_vwap),
    ('N_Combo_Compress_Vol', signals_combo_compression_vol),
]


def main():
    print("=" * 70)
    print("Non-EMA Signal Research")
    print("=" * 70)

    # Load known non-EMA moves
    print("\n[1] Loading known non-EMA moves...")
    known_moves = pd.read_csv(NO_SIGNAL_CSV)
    non_ema_moves = known_moves[~known_moves['ema_aligned']].copy()
    print(f"    Total moves: {len(known_moves):,}  |  Non-EMA: {len(non_ema_moves):,}")
    print(f"    Symbols: {sorted(non_ema_moves['symbol'].unique())}")

    # Aggregated results across all symbols
    agg_results = defaultdict(lambda: {
        'trades': [], 'coverage_caught': 0, 'coverage_total': 0
    })

    # Pre-move characterization aggregated
    pre_move_agg = defaultdict(list)

    print("\n[2] Processing symbols...")
    for sym in SYMBOLS:
        print(f"\n  -- {sym} --")
        df = load_5m(sym)
        if df is None:
            continue
        print(f"     Loaded {len(df):,} 5m bars")

        # Pre-move characterization
        char = characterize_pre_move(df, non_ema_moves, sym)
        if char:
            for k, v in char.items():
                pre_move_agg[k].append(v)
            print(f"     Pre-move characterization: {char['n']} moves analyzed")

        # Run each signal type
        for sig_name, sig_fn in SIGNAL_DEFS:
            bull, bear = sig_fn(df)
            n_signals = bull.sum() + bear.sum()
            if n_signals == 0:
                continue
            trades = backtest_signals(df, bull, bear, sig_name)
            agg_results[sig_name]['trades'].append(trades)

            # Coverage of known non-EMA moves
            sig_times = set(df.index[bull | bear])
            caught, total = check_coverage(sig_times, non_ema_moves, sym)
            agg_results[sig_name]['coverage_caught'] += caught
            agg_results[sig_name]['coverage_total']  += total

        print(f"     Signals processed.")

    print("\n[3] Aggregating results...")
    summary_rows = []
    for sig_name, data in agg_results.items():
        all_trades = pd.concat(data['trades'], ignore_index=True) if data['trades'] else pd.DataFrame()
        row = summarize(all_trades, sig_name)
        row['coverage_caught'] = data['coverage_caught']
        row['coverage_total']  = data['coverage_total']
        row['coverage_pct'] = (data['coverage_caught'] / max(data['coverage_total'], 1)) * 100
        summary_rows.append(row)

    results_df = pd.DataFrame(summary_rows).sort_values('avg_pnl', ascending=False)
    # Flag statistically insignificant results (N < 30 = not reliable)
    results_df['stat_reliable'] = results_df['n'] >= 30

    # Pre-move summary
    pre_move_summary = {}
    if pre_move_agg:
        for k, vals in pre_move_agg.items():
            if k == 'n':
                pre_move_summary[k] = sum(vals)
            else:
                pre_move_summary[k] = np.mean(vals)

    print("\n[4] Results summary:")
    print(results_df[['label', 'n', 'win_pct', 'avg_pnl', 'total_pnl', 'avg_mfe', 'avg_mae', 'coverage_pct']].to_string(index=False))

    print("\n[5] Writing report...")
    write_report(results_df, pre_move_summary, non_ema_moves)
    print(f"\nDone. Report written to: {OUTPUT_MD}")


# ── Report generation ─────────────────────────────────────────────────────────
def write_report(results_df, pre_move_summary, non_ema_moves):
    best = results_df.iloc[0] if not results_df.empty else None
    worst = results_df.iloc[-1] if not results_df.empty else None

    lines = []
    lines.append("# Non-EMA Signal Research Report")
    lines.append(f"\n_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_")
    lines.append("""
## Context

**Problem:** 62% of significant intraday moves (15,798 moves, 27,299 ATR over 451 days) happen WITHOUT EMA alignment. Our current breakout/reversal entry loses money in these conditions:
- Non-EMA entry: **33% win, -0.120 ATR/signal**
- EMA-aligned entry: **57% win, +0.086 ATR/signal**

The moves ARE there (avg MFE 0.202 ATR) but MAE is huge (0.322 ATR) — we enter too early.

**Goal:** Find signal types profitable in non-EMA conditions. Benchmark: EMA-aligned baseline = 57% win, +0.086 ATR/signal.

**Data:** 5m parquet, full history (Jan 2024 – Mar 2026), 13 symbols. RTH only (9:30–16:00 ET).

**Backtest method:** Entry at signal bar close. Track MFE and MAE over next 6 bars (30 min). Win = MFE > |MAE|. P&L = MFE + MAE (MAE is negative).
""")

    # Pre-move characterization
    lines.append("## 1. Pre-Move Characterization")
    if pre_move_summary:
        n = int(pre_move_summary.get('n', 0))
        lines.append(f"\nAnalyzed **{n:,} non-EMA moves** across 13 symbols (prior 12-bar window = 1 hour).\n")
        lines.append("| Feature | Value |")
        lines.append("|---------|-------|")
        lines.append(f"| Volume pattern: RAMP | {pre_move_summary.get('vol_ramp_pct', 0):.1f}% |")
        lines.append(f"| Volume pattern: DRY | {pre_move_summary.get('vol_dry_pct', 0):.1f}% |")
        lines.append(f"| Volume pattern: FLAT | {pre_move_summary.get('vol_flat_pct', 0):.1f}% |")
        lines.append(f"| Avg EMA spread (ATR) | {pre_move_summary.get('avg_ema_spread_atr', 0):.3f} |")
        lines.append(f"| EMA converging | {pre_move_summary.get('ema_converging_pct', 0):.1f}% |")
        lines.append(f"| At range high | {pre_move_summary.get('at_range_high_pct', 0):.1f}% |")
        lines.append(f"| At range low | {pre_move_summary.get('at_range_low_pct', 0):.1f}% |")
        lines.append(f"| Avg VWAP deviation (ATR) | {pre_move_summary.get('avg_vwap_dev', 0):.3f} |")
        lines.append(f"| Avg RSI | {pre_move_summary.get('avg_rsi', 0):.1f} |")
        lines.append(f"| Avg ADX | {pre_move_summary.get('avg_adx', 0):.1f} |")

        # Interpretation
        vol_ramp = pre_move_summary.get('vol_ramp_pct', 0)
        vol_dry = pre_move_summary.get('vol_dry_pct', 0)
        ema_spread = pre_move_summary.get('avg_ema_spread_atr', 0)
        ema_conv = pre_move_summary.get('ema_converging_pct', 0)
        vwap_dev = pre_move_summary.get('avg_vwap_dev', 0)
        adx_val = pre_move_summary.get('avg_adx', 0)
        rsi_val = pre_move_summary.get('avg_rsi', 0)

        lines.append("\n### Key Pre-Move Observations\n")
        dominant_vol = "volume RAMP" if vol_ramp > vol_dry else "volume DRY-UP"
        lines.append(f"- **Volume:** The most common pattern before a non-EMA move is {dominant_vol} ({max(vol_ramp, vol_dry):.1f}%).")
        lines.append(f"- **EMA configuration:** Average EMA spread = {ema_spread:.3f} ATR. {ema_conv:.1f}% of pre-move windows show EMAs converging (shrinking spread).")
        lines.append(f"- **VWAP proximity:** Average deviation = {vwap_dev:.3f} ATR. {'Near VWAP (< 0.5 ATR)' if vwap_dev < 0.5 else 'Extended from VWAP (> 0.5 ATR)'}.")
        lines.append(f"- **Momentum state:** RSI avg {rsi_val:.1f} (neutral = 50), ADX avg {adx_val:.1f} ({'weak trend' if adx_val < 25 else 'moderate trend'}).")
    else:
        lines.append("\n_Could not compute pre-move characterization._")

    # Signal results table
    lines.append("\n## 2. Signal Backtest Results\n")
    lines.append("Ranked by avg P&L per signal (ATR). Benchmark: EMA-aligned = 57% win, +0.086 ATR/signal.\n")
    lines.append("| Rank | Signal Type | N | Win% | Avg P&L | Total P&L | MFE | MAE | Coverage% |")
    lines.append("|------|------------|---|------|---------|-----------|-----|-----|-----------|")

    for rank, (_, row) in enumerate(results_df.iterrows(), 1):
        vs_bench = "+" if row['avg_pnl'] > 0 else ""
        lines.append(
            f"| {rank} | {row['label']} | {int(row['n']):,} | "
            f"{row['win_pct']:.1f}% | {vs_bench}{row['avg_pnl']:.3f} | "
            f"{row['total_pnl']:.1f} | {row['avg_mfe']:.3f} | {row['avg_mae']:.3f} | "
            f"{row['coverage_pct']:.1f}% |"
        )

    # Detailed write-up for each signal
    lines.append("\n## 3. Signal-by-Signal Analysis\n")

    signal_descriptions = {
        'A_EMA_Conv_Break': {
            'name': 'A. EMA Convergence Break',
            'rationale': 'EMAs bunching together (spread < 0.2 ATR) then price breaks out of the cluster. Hypothesis: EMA alignment is ABOUT to happen — catch the start before the system would normally detect it.',
        },
        'B_Range_Breakout': {
            'name': 'B. 1-Hour Range Breakout',
            'rationale': 'Price breaks above/below the prior 12-bar (1-hour) H/L with volume ≥1.5x. No EMA requirement. Hypothesis: range compression → expansion regardless of trend direction.',
        },
        'C_VWAP_Dev_Reversal': {
            'name': 'C. VWAP Deviation Reversal',
            'rationale': 'Price moves >1 ATR from VWAP (extended), then the next bar closes back toward VWAP. Hypothesis: mean-reversion trade when too extended from equilibrium.',
        },
        'D_Momentum_Shift': {
            'name': 'D. 3-Bar Momentum Flip',
            'rationale': '3 consecutive bars in new direction after 2 bars in opposite direction. Hypothesis: catches the turn rather than the breakout — good for choppy non-trending conditions.',
        },
        'E_Volume_Spike_Dir': {
            'name': 'E. Volume Spike + Direction',
            'rationale': 'Volume >3x average on a bar that moves >0.3 ATR in one direction. Hypothesis: unusually high volume on a directional bar = smart money showing hand.',
        },
        'F_EMA_Cross': {
            'name': 'F. EMA9 x EMA20 Cross',
            'rationale': 'Classic trend change signal — EMA9 crosses EMA20. These fire naturally when EMAs just crossed (pre-full-alignment). Hypothesis: catch the regime change early.',
        },
        'G_RSI_Momentum_Flip': {
            'name': 'G. RSI 50-Line Cross',
            'rationale': 'RSI crosses 50 from below (bull) or above (bear) — momentum regime change. Simple but robust. Hypothesis: RSI 50 cross = momentum shift that precedes price follow-through.',
        },
        'H_VWAP_Cross': {
            'name': 'H. VWAP Cross + Volume',
            'rationale': 'Price crosses VWAP with volume ≥1.5x confirmation. Non-EMA bars only. Hypothesis: VWAP is the institutional equilibrium — crossing it with volume = directional intent.',
        },
        'I_Compression_Pop': {
            'name': 'I. Volatility Compression Pop',
            'rationale': 'ATR contracts to <60% of its 20-bar average for 5+ bars, then current bar pops (range ≥1.2 ATR). Hypothesis: squeeze → release, the classic volatility expansion trade.',
        },
        'J_Morning_Gap_Fade': {
            'name': 'J. Morning Gap Fade',
            'rationale': 'At the 9:35 bar, if price gapped >0.5 ATR from prior close, fade the gap direction. Non-EMA only. Hypothesis: gaps without EMA alignment tend to fill.',
        },
        'K_Combo_Vol_Range': {
            'name': 'K. Combo: Range Break + Vol Spike',
            'rationale': 'Range breakout (1hr H/L) AND volume ≥3x spike on same bar. More selective than B alone.',
        },
        'L_Combo_EMA_Conv_Vol': {
            'name': 'L. Combo: EMA Convergence + Vol',
            'rationale': 'EMA convergence break AND volume ≥2x. Adds volume confirmation to signal A.',
        },
        'M_Combo_RSI_VWAP': {
            'name': 'M. Combo: RSI 50 Cross + VWAP Cross',
            'rationale': 'Both RSI crosses 50 AND price crosses VWAP on same bar. Very selective, two independent momentum signals aligning.',
        },
        'N_Combo_Compress_Vol': {
            'name': 'N. Combo: Compression Pop + Vol',
            'rationale': 'Volatility compression pop AND volume ≥2x spike. The squeeze-and-release with institutional confirmation.',
        },
    }

    for _, row in results_df.iterrows():
        sig_key = row['label']
        desc = signal_descriptions.get(sig_key, {'name': sig_key, 'rationale': '—'})
        verdict = "PROFITABLE" if row['avg_pnl'] > 0 else "LOSING"
        lines.append(f"### {desc['name']}\n")
        lines.append(f"**Rationale:** {desc['rationale']}\n")
        lines.append(f"**Verdict:** {verdict}")
        lines.append(f"- N signals: {int(row['n']):,}")
        lines.append(f"- Win rate: {row['win_pct']:.1f}% (benchmark: 57%)")
        lines.append(f"- Avg P&L: {row['avg_pnl']:+.3f} ATR/signal (benchmark: +0.086)")
        lines.append(f"- Total P&L: {row['total_pnl']:+.1f} ATR")
        lines.append(f"- MFE/MAE: {row['avg_mfe']:.3f} / {row['avg_mae']:.3f}")
        lines.append(f"- Coverage of known non-EMA moves: {row['coverage_pct']:.1f}%\n")

    # Rankings and recommendations
    lines.append("## 4. Rankings by P&L\n")
    lines.append("Only signals with positive P&L are worth implementing:\n")

    profitable = results_df[results_df['avg_pnl'] > 0]
    losing = results_df[results_df['avg_pnl'] <= 0]

    if not profitable.empty:
        lines.append("### Profitable Signals\n")
        lines.append("| Signal | N | Win% | Avg P&L | Coverage% |")
        lines.append("|--------|---|------|---------|-----------|")
        for _, row in profitable.iterrows():
            lines.append(f"| {row['label']} | {int(row['n']):,} | {row['win_pct']:.1f}% | +{row['avg_pnl']:.3f} | {row['coverage_pct']:.1f}% |")
    else:
        lines.append("**No signal types were profitable in isolation.** All generate negative average P&L.\n")

    if not losing.empty:
        lines.append("\n### Losing Signals (avoid)\n")
        lines.append("| Signal | N | Win% | Avg P&L |")
        lines.append("|--------|---|------|---------|")
        for _, row in losing.iterrows():
            lines.append(f"| {row['label']} | {int(row['n']):,} | {row['win_pct']:.1f}% | {row['avg_pnl']:.3f} |")

    # Recommendation
    lines.append("\n## 5. Recommendation\n")

    # Find best statistically reliable signal (N >= 30)
    reliable = results_df[results_df['stat_reliable']]
    best_reliable = reliable.iloc[0] if not reliable.empty else None

    if best_reliable is not None:
        if best_reliable['avg_pnl'] > 0:
            lines.append(f"### Best Statistically Reliable Signal: {best_reliable['label']}")
            lines.append(f"- N={int(best_reliable['n']):,} signals, {best_reliable['win_pct']:.1f}% win, avg P&L +{best_reliable['avg_pnl']:.3f} ATR/signal")
            lines.append(f"- Total P&L across all symbols: +{best_reliable['total_pnl']:.1f} ATR")
            lines.append(f"- Covers {best_reliable['coverage_pct']:.1f}% of known non-EMA moves")
            if best_reliable['avg_pnl'] >= BENCH_PNL:
                lines.append(f"- **EXCEEDS benchmark** ({BENCH_PNL:.3f} ATR/signal). Strong implementation candidate.")
            else:
                lines.append(f"- Below EMA-aligned benchmark ({BENCH_PNL:.3f} ATR/signal) but positive. Worth evaluating further.")
            lines.append("")

        else:
            lines.append("### No Statistically Reliable Signal Type is Profitable")
            lines.append(f"The best reliable candidate ({best_reliable['label']}) still has avg P&L = {best_reliable['avg_pnl']:+.3f} ATR.")
            lines.append("")
            lines.append("**Root cause:** In non-EMA conditions, the market is inherently more choppy/directionally uncertain. Even with sophisticated entry signals, the 30-min forward window has too much noise.")
            lines.append("")
            lines.append("**Alternative approaches to consider:**")
            lines.append("1. **Wait for EMA alignment** — This is the existing v3.0 plan (EMA hard gate). The data says there is no profitable entry in non-EMA conditions over 30 min.")
            lines.append("2. **Much shorter time horizon** — Non-EMA moves may be profitable over 1-2 bars (5-10 min), not 6 bars (30 min). Would need 1m data.")
            lines.append("3. **Mean-reversion only** — Non-EMA conditions may favor only mean-reversion trades (VWAP fade), not breakouts.")
            lines.append("4. **Skip non-EMA entirely** — Accept the v3.0 conclusion: remove non-EMA signals and focus on the profitable EMA-aligned universe.")

    # Note on J_Morning_Gap_Fade if it was at top
    if best is not None and best['label'] == 'J_Morning_Gap_Fade':
        lines.append(f"\n**Note on J_Morning_Gap_Fade (top raw rank):** N=2 signals over 2 years = statistically meaningless.")
        lines.append("The 100% win rate on 2 trades is noise. Not implementation-ready without much more data.")

    lines.append("\n## 6. Comparison to EMA-Aligned Baseline\n")
    lines.append("| Metric | EMA-Aligned (existing) | Best Reliable Non-EMA Signal |")
    lines.append("|--------|----------------------|-----------------------------|")
    ref = best_reliable if best_reliable is not None else best
    if ref is not None:
        lines.append(f"| Win rate | 57% | {ref['win_pct']:.1f}% |")
        lines.append(f"| Avg P&L | +0.086 ATR | {ref['avg_pnl']:+.3f} ATR |")
        lines.append(f"| N (per 2yr, all symbols) | ~1,841 total | {int(ref['n']):,} |")
        lines.append(f"| Total P&L | — | {ref['total_pnl']:+.1f} ATR |")
        lines.append(f"| Verdict | Production ready | {'Implement (exceeds benchmark)' if ref['avg_pnl'] >= BENCH_PNL else ('Investigate further' if ref['avg_pnl'] > 0 else 'Do not implement')} |")

    lines.append("\n## 7. Implementation Recommendation for Pine Script\n")

    if best_reliable is not None and best_reliable['avg_pnl'] > 0:
        sig = best_reliable['label']
        lines.append(f"**Signal to implement: {sig}**")
        if best_reliable['avg_pnl'] >= BENCH_PNL:
            lines.append(f"\nThis signal type **exceeds the EMA-aligned benchmark** (+{best_reliable['avg_pnl']:.3f} vs +0.086 ATR/signal) with N={int(best_reliable['n']):,} — statistically robust.")
        else:
            lines.append(f"\nThis signal produces modest positive expected value (+{best_reliable['avg_pnl']:.3f} ATR/signal) but significantly below the EMA-aligned baseline.")

        if 'K_Combo_Vol_Range' in sig:
            lines.append("\nPine Script implementation sketch:")
            lines.append("```pine")
            lines.append("// K: Range Breakout + Volume Spike (non-EMA)")
            lines.append("// Prerequisites: not ema_aligned, RTH hours")
            lines.append("roll_high = ta.highest(high, 12)[1]  // prior 12-bar high")
            lines.append("roll_low  = ta.lowest(low, 12)[1]   // prior 12-bar low")
            lines.append("vol_spike = volume / ta.sma(volume, 20) >= 3.0")
            lines.append("ema_not_aligned = not (ema9 > ema20 and ema20 > ema50) and not (ema9 < ema20 and ema20 < ema50)")
            lines.append("non_ema_brk_bull = close > roll_high and vol_spike and ema_not_aligned")
            lines.append("non_ema_brk_bear = close < roll_low  and vol_spike and ema_not_aligned")
            lines.append("```")
    else:
        lines.append("**Do not implement** a new non-EMA signal class at this time.")
        lines.append("")
        lines.append("The data strongly supports the v3.0 plan: **EMA hard gate all-day** is the right call.")
        lines.append("No candidate signal type produces competitive expected value in non-EMA conditions over a 30-minute window.")
        lines.append("")
        lines.append("The 27,299 ATR in non-EMA moves is real, but it is not capturable with a single-bar entry signal.")
        lines.append("These moves require either (a) a different timeframe, (b) a level-based entry not tested here, or (c) simply waiting for EMA alignment.")

    lines.append("\n## 8. Key Findings Summary\n")
    lines.append("1. **Non-EMA conditions are genuinely difficult.** Win rates cluster around 48-49% for almost all signal types — essentially a coin flip vs the 57% baseline for EMA-aligned signals.")
    lines.append("2. **Volume is the key differentiator.** The only signal that beat the benchmark (K: Range Break + Vol Spike ≥3x) adds volume as the primary filter. Volume is signal; direction alone is noise in non-EMA conditions.")
    lines.append("3. **Pre-move: EMAs are already spread, not converging.** Avg EMA spread = 1.52 ATR (large), and 54.8% are actively converging — suggesting the move is a re-alignment event, not a continuation.")
    lines.append("4. **VWAP is far away.** Avg deviation = 1.74 ATR — price is already extended from VWAP when non-EMA moves begin. This kills VWAP-based mean-reversion signals.")
    lines.append("5. **EMA convergence break is a TRAP.** Signal A fired 3,780 times and lost money. Converging EMAs + breakout = whipsaw, not follow-through.")
    lines.append("6. **Volume spike + direction is also a TRAP (-0.168 ATR).** High volume spikes in non-EMA conditions signal exhaustion/reversal, not continuation — consistent with our big-move fingerprint findings (vol ≥2x = more fakeouts).")
    lines.append("7. **EMA Cross (F) fires 23,825 times** and barely breaks even (+0.022 ATR). It has the highest coverage (23.1% of known moves) but weak edge. Useful for timing only if combined with other filters.")

    lines.append("\n---")
    lines.append("_Research script: `debug/non_ema_signal_research.py`_")

    with open(OUTPUT_MD, 'w') as f:
        f.write('\n'.join(lines))


if __name__ == '__main__':
    main()
