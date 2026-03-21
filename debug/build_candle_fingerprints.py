#!/usr/bin/env python3
"""
Build TSLA Open Scalper candle fingerprint database.
One row per trading day with PM signals, binary conf, RTH bar-by-bar, patterns, outcomes.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ─── Paths ───────────────────────────────────────────────────────────
BASE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude")
CACHE = BASE / "trading_bot/cache"
OUT_DIR = BASE / "misc/TradingView/debug"

TSLA_15S = CACHE / "bars_highres/15sec/tsla_15_secs_ib.parquet"
TSLA_1M  = CACHE / "bars/tsla_1_min_ib.parquet"
SPY_15S  = CACHE / "bars_highres/15sec/spy_15_secs_ib.parquet"
VIX_DAY  = CACHE / "bars/vix_1_day_ib.parquet"

OUT_PQ   = OUT_DIR / "tsla_candle_fingerprints.parquet"
OUT_CSV  = OUT_DIR / "tsla_candle_fingerprints_summary.csv"


def load_data():
    """Load all data files and convert to Eastern time."""
    print("Loading data...")

    tsla_15s = pd.read_parquet(TSLA_15S)
    tsla_15s['date'] = pd.to_datetime(tsla_15s['date'], utc=True).dt.tz_convert('US/Eastern')
    tsla_15s = tsla_15s.set_index('date').sort_index()

    tsla_1m = pd.read_parquet(TSLA_1M)
    tsla_1m['date'] = pd.to_datetime(tsla_1m['date'], utc=True).dt.tz_convert('US/Eastern')
    tsla_1m = tsla_1m.set_index('date').sort_index()

    spy_15s = pd.read_parquet(SPY_15S)
    spy_15s['date'] = pd.to_datetime(spy_15s['date'], utc=True).dt.tz_convert('US/Eastern')
    spy_15s = spy_15s.set_index('date').sort_index()

    vix = pd.read_parquet(VIX_DAY)
    vix['date'] = pd.to_datetime(vix['date'])
    vix = vix.set_index('date').sort_index()

    print(f"  TSLA 15s: {len(tsla_15s):,} bars, {tsla_15s.index[0].date()} to {tsla_15s.index[-1].date()}")
    print(f"  TSLA 1m:  {len(tsla_1m):,} bars, {tsla_1m.index[0].date()} to {tsla_1m.index[-1].date()}")
    print(f"  SPY 15s:  {len(spy_15s):,} bars, {spy_15s.index[0].date()} to {spy_15s.index[-1].date()}")
    print(f"  VIX day:  {len(vix):,} bars, {vix.index[0].date() if hasattr(vix.index[0], 'date') else vix.index[0]} to {vix.index[-1].date() if hasattr(vix.index[-1], 'date') else vix.index[-1]}")

    return tsla_15s, tsla_1m, spy_15s, vix


def get_trading_days(tsla_1m):
    """Get list of trading days from 1m data."""
    return sorted(tsla_1m.index.date)


def time_filter(df, day, h_start, m_start, h_end, m_end):
    """Filter dataframe for a specific time window on a given day."""
    import datetime as dt
    start = pd.Timestamp(dt.datetime(day.year, day.month, day.day, h_start, m_start),
                         tz='US/Eastern')
    end = pd.Timestamp(dt.datetime(day.year, day.month, day.day, h_end, m_end),
                       tz='US/Eastern')
    return df[(df.index >= start) & (df.index <= end)]


def compute_pm_signals(tsla_15s_day, day):
    """Compute all pre-market signals from 15sec bars, 9:20-9:29."""
    import datetime as dt

    pm = time_filter(tsla_15s_day, day, 9, 20, 9, 29)
    if len(pm) < 10:
        return None

    result = {}

    pm_high = pm['high'].max()
    pm_low = pm['low'].min()
    pm_range = pm_high - pm_low
    pm_close = pm['close'].iloc[-1]

    result['pm_position'] = (pm_close - pm_low) / pm_range if pm_range > 0 else 0.5

    # Acceleration: price change over last N minutes of PM
    # 2m accel: ~8 bars of 15sec = 2 minutes before end
    n_bars = len(pm)
    result['pm_accel_2m'] = pm['close'].iloc[-1] - pm['close'].iloc[max(0, -9)] if n_bars >= 9 else np.nan
    result['pm_accel_4m'] = pm['close'].iloc[-1] - pm['close'].iloc[max(0, n_bars - 17)] if n_bars >= 17 else np.nan
    result['pm_accel_10m'] = pm['close'].iloc[-1] - pm['close'].iloc[0]

    # VWAP
    if (pm['volume'] > 0).any():
        result['pm_vwap'] = (pm['close'] * pm['volume']).sum() / pm['volume'].sum()
    else:
        result['pm_vwap'] = pm_close

    # EMA5 of pseudo 1m bars (aggregate 15s -> 1m, then EMA5)
    pm_1m = pm['close'].resample('1min').last().dropna()
    if len(pm_1m) >= 5:
        result['pm_ema5'] = pm_1m.ewm(span=5, adjust=False).mean().iloc[-1]
    else:
        result['pm_ema5'] = pm_close

    result['pm_close_vs_vwap'] = pm_close - result['pm_vwap']
    result['pm_close_vs_ema5'] = pm_close - result['pm_ema5']

    # Linear regression for slope, R2, curvature
    prices = pm['close'].values
    x = np.arange(len(prices), dtype=float)
    if len(prices) >= 3:
        # Slope via linear regression ($/bar -> $/min: *4 since 15sec bars)
        coeffs = np.polyfit(x, prices, 1)
        result['pm_slope'] = coeffs[0] * 4  # per minute

        # R2
        pred = np.polyval(coeffs, x)
        ss_res = np.sum((prices - pred) ** 2)
        ss_tot = np.sum((prices - prices.mean()) ** 2)
        result['pm_r2'] = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        # Curvature (2nd order coefficient)
        if len(prices) >= 5:
            coeffs2 = np.polyfit(x, prices, 2)
            result['pm_curvature'] = coeffs2[0]
        else:
            result['pm_curvature'] = 0.0
    else:
        result['pm_slope'] = 0.0
        result['pm_r2'] = 0.0
        result['pm_curvature'] = 0.0

    # Volume
    pm_5m = time_filter(tsla_15s_day, day, 9, 25, 9, 29)
    result['pm_vol_5m'] = pm_5m['volume'].sum() if len(pm_5m) > 0 else 0
    result['pm_vol_10m'] = pm['volume'].sum()

    # Vol ratio: last 2m vs first 8m
    pm_last2m = time_filter(tsla_15s_day, day, 9, 28, 9, 29)
    pm_first8m = time_filter(tsla_15s_day, day, 9, 20, 9, 27)
    vol_first8 = pm_first8m['volume'].sum()
    vol_last2 = pm_last2m['volume'].sum()
    result['pm_vol_ratio'] = vol_last2 / vol_first8 if vol_first8 > 0 else np.nan

    result['pm_range'] = pm_range

    # Last 30s direction (last 2 bars of 15sec)
    if n_bars >= 2:
        result['pm_last_30s_dir'] = 'G' if pm['close'].iloc[-1] >= pm['close'].iloc[-3] else 'R'
    else:
        result['pm_last_30s_dir'] = 'R'

    # Consecutive down bars into close
    consec = 0
    for i in range(n_bars - 1, -1, -1):
        if pm['close'].iloc[i] < pm['open'].iloc[i]:
            consec += 1
        else:
            break
    result['pm_consec_down_bars'] = consec

    # PM direction sequence (40 chars for 40 bars)
    dirs = ['G' if pm['close'].iloc[i] >= pm['open'].iloc[i] else 'R' for i in range(n_bars)]
    result['pm_dir_sequence'] = ''.join(dirs).ljust(40, '?')[:40]
    result['pm_last5_dirs'] = ''.join(dirs[-5:]) if len(dirs) >= 5 else ''.join(dirs).ljust(5, '?')
    result['pm_green_pct'] = sum(1 for d in dirs if d == 'G') / len(dirs) if dirs else 0.5

    return result


def compute_spy_signals(spy_15s, day):
    """Compute SPY cross-asset signals from 15sec bars."""
    pm = time_filter(spy_15s, day, 9, 20, 9, 29)
    if len(pm) < 5:
        return {'spy_accel_2m': np.nan, 'spy_accel_10m': np.nan, 'spy_direction': 'R'}

    n = len(pm)
    accel_2m = pm['close'].iloc[-1] - pm['close'].iloc[max(0, n - 9)]
    accel_10m = pm['close'].iloc[-1] - pm['close'].iloc[0]
    direction = 'G' if pm['close'].iloc[-1] >= pm['open'].iloc[0] else 'R'

    return {'spy_accel_2m': accel_2m, 'spy_accel_10m': accel_10m, 'spy_direction': direction}


def compute_binary_conf(pm_signals, vix_prev, gap, gap_pct, prev_close):
    """Replicate the Pine Script binary confidence system."""
    result = {}

    conf = 0
    hard_kill = False
    kill_reason = 'none'

    pm_pos = pm_signals.get('pm_position', 0.5)
    pm_accel = pm_signals.get('pm_accel_2m', 0)
    pm_late_trend = pm_signals.get('pm_accel_10m', 0)
    pm_vol_5m = pm_signals.get('pm_vol_5m', 0)

    # Check 1: PM Position above Q1
    if pm_pos > 0.219:
        conf += 1
    # Check 2: 2m acceleration positive
    if not np.isnan(pm_accel) and pm_accel > 0:
        conf += 1
    # Check 3: VIX sweet spot
    if not np.isnan(vix_prev) and 18 <= vix_prev <= 25:
        conf += 1
    # Check 4: Triple PM alignment (TSLA only — we don't have QQQ, use SPY direction)
    # Simplified: TSLA up + SPY direction up
    tsla_up = not np.isnan(pm_late_trend) and pm_late_trend > 0
    # Note: original uses SPY+QQQ, we only track SPY here
    # We'll give the point if TSLA is up (conservative)
    if tsla_up:
        conf += 1
    # Check 5: No gap danger
    gap_danger_flat = False
    if not np.isnan(gap) and gap < -2 and not np.isnan(pm_late_trend) and abs(pm_late_trend) < 0.48:
        gap_danger_flat = True
    if not gap_danger_flat:
        conf += 1

    # Hard kills
    if not np.isnan(vix_prev) and vix_prev <= 15:
        hard_kill = True
        kill_reason = 'VIX'
    if pm_pos < 0.219 and pm_signals.get('pm_last_30s_dir', 'G') == 'R':
        hard_kill = True
        kill_reason = 'P9'
    if gap_danger_flat:
        hard_kill = True
        kill_reason = 'GAP'
    if not np.isnan(gap) and gap < -5:
        hard_kill = True
        kill_reason = 'GAP_BIG'
    if pm_vol_5m < 3000 and pm_vol_5m > 0 and conf < 4:
        hard_kill = True
        kill_reason = 'LOW_VOL'

    # PUT rescue
    if hard_kill and not np.isnan(pm_accel) and pm_accel > 1.0 and pm_pos > 0.7 and conf >= 3:
        hard_kill = False
        kill_reason = 'none'

    is_call_tier = not hard_kill and conf >= 3

    # VWAP / EMA agreement
    vwap_agrees = pm_signals.get('pm_close_vs_vwap', 0) > 0  # close above VWAP = bullish
    ema_agrees = pm_signals.get('pm_close_vs_ema5', 0) > 0
    triple_agree = vwap_agrees and ema_agrees and pm_pos > 0.5

    result['conf'] = conf
    result['hard_kill'] = hard_kill
    result['kill_reason'] = kill_reason
    result['is_call_tier'] = is_call_tier
    result['vwap_agrees'] = vwap_agrees
    result['ema_agrees'] = ema_agrees
    result['triple_agree'] = triple_agree
    result['agree_count'] = int(vwap_agrees) + int(ema_agrees)

    return result


def compute_rth_fingerprint(tsla_1m_day, day, open_930):
    """Extract RTH 1m bars 9:30-9:49 (20 bars) and compute fingerprint."""
    import datetime as dt

    rth = time_filter(tsla_1m_day, day, 9, 30, 9, 49)
    if len(rth) < 1:
        return None

    result = {}

    # Pad to 20 bars if needed
    for i in range(20):
        if i < len(rth):
            bar = rth.iloc[i]
            result[f'bar{i}_open'] = bar['open']
            result[f'bar{i}_high'] = bar['high']
            result[f'bar{i}_low'] = bar['low']
            result[f'bar{i}_close'] = bar['close']
            result[f'bar{i}_volume'] = bar['volume']
            rng = bar['high'] - bar['low']
            body = abs(bar['close'] - bar['open'])
            result[f'bar{i}_dir'] = 'G' if bar['close'] >= bar['open'] else 'R'
            result[f'bar{i}_range'] = rng
            result[f'bar{i}_body'] = body
            result[f'bar{i}_body_pct'] = body / rng if rng > 0 else 0
            result[f'bar{i}_change'] = bar['close'] - open_930
        else:
            for col in ['open', 'high', 'low', 'close', 'volume', 'range', 'body', 'body_pct', 'change']:
                result[f'bar{i}_{col}'] = np.nan
            result[f'bar{i}_dir'] = '?'

    return result


def compute_15s_first_minute(tsla_15s_day, day):
    """Extract first 4 bars of 15sec at RTH open (9:30:00 - 9:30:45)."""
    import datetime as dt

    start = pd.Timestamp(dt.datetime(day.year, day.month, day.day, 9, 30, 0), tz='US/Eastern')
    end = pd.Timestamp(dt.datetime(day.year, day.month, day.day, 9, 30, 45), tz='US/Eastern')
    bars = tsla_15s_day[(tsla_15s_day.index >= start) & (tsla_15s_day.index <= end)]

    result = {}
    open_930 = bars['open'].iloc[0] if len(bars) > 0 else np.nan

    for i in range(4):
        if i < len(bars):
            bar = bars.iloc[i]
            result[f'bar15s_{i}_dir'] = 'G' if bar['close'] >= bar['open'] else 'R'
            result[f'bar15s_{i}_range'] = bar['high'] - bar['low']
            result[f'bar15s_{i}_change'] = bar['close'] - open_930 if not np.isnan(open_930) else np.nan
        else:
            result[f'bar15s_{i}_dir'] = '?'
            result[f'bar15s_{i}_range'] = np.nan
            result[f'bar15s_{i}_change'] = np.nan

    return result


def classify_pattern(rth_fp):
    """Classify opening pattern from RTH fingerprint."""
    if rth_fp is None:
        return {'bar0_dir': '?', 'bar1_dir': '?', 'bar2_dir': '?',
                'first3_pattern': '???', 'opening_pattern': 'UNKNOWN'}

    b0d = rth_fp.get('bar0_dir', '?')
    b1d = rth_fp.get('bar1_dir', '?')
    b2d = rth_fp.get('bar2_dir', '?')
    b0r = rth_fp.get('bar0_range', 0) or 0

    first3 = b0d + b1d + b2d

    # Classification priority: specific multi-bar patterns first
    if b0d == 'G' and b1d == 'R' and b2d == 'R':
        pattern = 'INVV'
    elif b0d == 'R' and b1d == 'G' and b2d == 'G':
        pattern = 'VSHAPE'
    elif b0d == 'G' and b1d == 'R':
        pattern = 'FAKEUP'
    elif b0d == 'R' and b1d == 'G':
        pattern = 'FAKEDN'
    elif b0d == 'R' and b0r > 2.50:
        pattern = 'CRASH'
    elif b0d == 'R':
        pattern = 'DRIFT_DN'
    elif b0d == 'G' and b0r > 2.50:
        pattern = 'SURGE'
    elif b0d == 'G':
        pattern = 'DRIFT_UP'
    else:
        pattern = 'UNKNOWN'

    return {
        'bar0_dir': b0d, 'bar1_dir': b1d, 'bar2_dir': b2d,
        'first3_pattern': first3, 'opening_pattern': pattern
    }


def compute_outcomes(rth_fp, tsla_1m_day, day, open_930):
    """Compute PnL and MFE/MAE at multiple horizons."""
    import datetime as dt

    result = {}

    # PnL at each minute (1-20)
    for i in range(20):
        close_i = rth_fp.get(f'bar{i}_close', np.nan) if rth_fp else np.nan
        if not np.isnan(close_i) and not np.isnan(open_930):
            result[f'pnl_call_{i+1}m'] = close_i - open_930
            result[f'pnl_put_{i+1}m'] = open_930 - close_i
        else:
            result[f'pnl_call_{i+1}m'] = np.nan
            result[f'pnl_put_{i+1}m'] = np.nan

    # MFE/MAE from 1m bars
    rth_full = time_filter(tsla_1m_day, day, 9, 30, 9, 49)

    for horizon, n_bars in [(5, 5), (10, 10), (20, 20)]:
        bars = rth_full.iloc[:n_bars] if len(rth_full) >= n_bars else rth_full
        if len(bars) > 0 and not np.isnan(open_930):
            max_high = bars['high'].max()
            min_low = bars['low'].min()
            result[f'mfe_call_{horizon}m'] = max_high - open_930
            result[f'mfe_put_{horizon}m'] = open_930 - min_low
            result[f'mae_call_{horizon}m'] = open_930 - min_low  # adverse for calls = price drops
            result[f'mae_put_{horizon}m'] = max_high - open_930  # adverse for puts = price rises
        else:
            for prefix in ['mfe_call', 'mfe_put', 'mae_call', 'mae_put']:
                result[f'{prefix}_{horizon}m'] = np.nan

    # bar1 confirms binary conf direction
    bar1_close = rth_fp.get('bar1_close', np.nan) if rth_fp else np.nan
    if not np.isnan(bar1_close) and not np.isnan(open_930):
        result['bar1_confirms_binary'] = bar1_close > open_930  # True = confirms calls
    else:
        result['bar1_confirms_binary'] = np.nan

    # Best side at various horizons
    for horizon in [2, 5, 20]:
        call_pnl = result.get(f'pnl_call_{horizon}m', np.nan)
        put_pnl = result.get(f'pnl_put_{horizon}m', np.nan)
        if not np.isnan(call_pnl) and not np.isnan(put_pnl):
            result[f'best_side_{horizon}m'] = 'CALL' if call_pnl >= put_pnl else 'PUT'
        else:
            result[f'best_side_{horizon}m'] = '?'

    # Day close direction (full RTH)
    rth_all = time_filter(tsla_1m_day, day, 9, 30, 15, 59)
    if len(rth_all) > 0 and not np.isnan(open_930):
        day_close = rth_all['close'].iloc[-1]
        result['day_close_direction'] = 'BULL' if day_close >= open_930 else 'BEAR'
    else:
        result['day_close_direction'] = '?'

    return result


def build_database():
    """Main build function."""
    tsla_15s, tsla_1m, spy_15s, vix = load_data()

    # Get unique trading days from 1m data (RTH only, 9:30+)
    rth_mask = (tsla_1m.index.hour == 9) & (tsla_1m.index.minute == 30)
    trading_days = sorted(set(tsla_1m[rth_mask].index.date))
    print(f"\nFound {len(trading_days)} trading days with 9:30 bar in 1m data")

    # Also get days with PM data in 15s
    pm_days_15s = set()
    mask_920 = (tsla_15s.index.hour == 9) & (tsla_15s.index.minute >= 20) & (tsla_15s.index.minute <= 29)
    pm_days_15s = set(tsla_15s[mask_920].index.date)

    common_days = sorted(set(trading_days) & pm_days_15s)
    print(f"Days with both PM 15s + RTH 1m: {len(common_days)}")

    # Build VIX lookup (prev day close)
    vix_map = {}
    vix_dates = sorted(vix.index)
    for i in range(1, len(vix_dates)):
        d = vix_dates[i]
        day_key = d.date() if hasattr(d, 'date') else d
        prev_close = vix.loc[vix_dates[i-1], 'close']
        vix_map[day_key] = prev_close

    # Pre-compute prev_close for each day from 1m data
    prev_close_map = {}
    rth_close = tsla_1m[(tsla_1m.index.hour >= 9) & (tsla_1m.index.hour < 16)]
    day_closes = rth_close.groupby(rth_close.index.date)['close'].last()
    prev_dates = sorted(day_closes.index)
    for i in range(1, len(prev_dates)):
        prev_close_map[prev_dates[i]] = day_closes[prev_dates[i-1]]

    rows = []
    skipped = 0

    for idx, day in enumerate(common_days):
        if idx % 50 == 0:
            print(f"  Processing day {idx+1}/{len(common_days)}: {day}")

        # Get day slices
        tsla_15s_day = tsla_15s[tsla_15s.index.date == day]
        tsla_1m_day = tsla_1m[tsla_1m.index.date == day]
        spy_15s_day = spy_15s[spy_15s.index.date == day] if day in set(spy_15s.index.date) else pd.DataFrame()

        # Get open_930
        bar_930 = tsla_1m_day[(tsla_1m_day.index.hour == 9) & (tsla_1m_day.index.minute == 30)]
        if len(bar_930) == 0:
            skipped += 1
            continue
        open_930 = bar_930['open'].iloc[0]

        prev_close = prev_close_map.get(day, np.nan)
        vix_prev = vix_map.get(day, np.nan)

        row = {'date': day, 'open_930': open_930, 'prev_close': prev_close}

        # PM signals
        pm_signals = compute_pm_signals(tsla_15s_day, day)
        if pm_signals is None:
            skipped += 1
            continue
        row.update(pm_signals)

        # SPY signals
        if len(spy_15s_day) > 0:
            spy_sigs = compute_spy_signals(spy_15s_day, day)
        else:
            spy_sigs = {'spy_accel_2m': np.nan, 'spy_accel_10m': np.nan, 'spy_direction': '?'}
        row.update(spy_sigs)

        # Gap
        gap = open_930 - prev_close if not np.isnan(prev_close) else np.nan
        gap_pct = gap / prev_close if not np.isnan(prev_close) and prev_close != 0 else np.nan
        row['gap'] = gap
        row['gap_pct'] = gap_pct
        row['vix_prev'] = vix_prev

        # Binary conf
        conf_result = compute_binary_conf(pm_signals, vix_prev, gap, gap_pct, prev_close)
        row.update(conf_result)

        # RTH fingerprint (1m bars)
        rth_fp = compute_rth_fingerprint(tsla_1m_day, day, open_930)
        if rth_fp:
            row.update(rth_fp)

        # 15sec first minute
        fp_15s = compute_15s_first_minute(tsla_15s_day, day)
        row.update(fp_15s)

        # Pattern classification
        pattern = classify_pattern(rth_fp)
        row.update(pattern)

        # Outcomes
        outcomes = compute_outcomes(rth_fp, tsla_1m_day, day, open_930)
        row.update(outcomes)

        rows.append(row)

    print(f"\nBuilt {len(rows)} day records, skipped {skipped}")

    # Create DataFrame
    df = pd.DataFrame(rows)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').sort_index()

    # Save parquet
    df.to_parquet(OUT_PQ, engine='pyarrow')
    print(f"\nSaved parquet: {OUT_PQ}")
    print(f"  Shape: {df.shape}")
    print(f"  Columns: {len(df.columns)}")
    print(f"  Date range: {df.index[0].date()} to {df.index[-1].date()}")

    # Save summary CSV
    summary_cols = ['conf', 'is_call_tier', 'agree_count', 'opening_pattern',
                    'first3_pattern', 'bar0_dir', 'bar0_range']
    for c in ['pnl_call_2m', 'pnl_put_2m', 'best_side_2m']:
        if c in df.columns:
            summary_cols.append(c)

    summary = df[summary_cols].copy()
    summary.to_csv(OUT_CSV)
    print(f"Saved summary CSV: {OUT_CSV}")

    # ─── Validation ────────────────────────────────────────────────
    print("\n" + "="*60)
    print("VALIDATION")
    print("="*60)
    print(f"Total days: {len(df)}")
    print(f"Date range: {df.index[0].date()} to {df.index[-1].date()}")
    print(f"Column count: {len(df.columns)}")

    print("\n--- 5 Random Days ---")
    sample = df.sample(min(5, len(df)), random_state=42)
    for d in sample.index:
        r = sample.loc[d]
        print(f"  {d.date()}: conf={r['conf']}, call={r['is_call_tier']}, "
              f"pattern={r['opening_pattern']}, first3={r['first3_pattern']}, "
              f"bar0_range=${r.get('bar0_range', 0):.2f}, "
              f"call_2m=${r.get('pnl_call_2m', 0):.2f}, put_2m=${r.get('pnl_put_2m', 0):.2f}, "
              f"best={r.get('best_side_2m', '?')}")

    print("\n--- Pattern Distribution ---")
    print(df['opening_pattern'].value_counts().to_string())

    print("\n--- Agreement Distribution ---")
    print(df['agree_count'].value_counts().sort_index().to_string())

    print("\n--- Best Side Distribution (2m) ---")
    if 'best_side_2m' in df.columns:
        print(df['best_side_2m'].value_counts().to_string())

    print("\n--- Confidence Distribution ---")
    print(df['conf'].value_counts().sort_index().to_string())

    print("\n--- Call vs Put Tier ---")
    print(df['is_call_tier'].value_counts().to_string())

    return df


if __name__ == '__main__':
    build_database()
