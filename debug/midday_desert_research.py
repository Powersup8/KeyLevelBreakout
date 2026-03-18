#!/usr/bin/env python3
"""
Midday Desert Research — Why does KLB coverage collapse after 11:00?

Analyzes:
A. Anatomy of the midday desert (coverage timeline, move characteristics)
B. Wider-timeframe levels as midday support/resistance
C. Non-keylevel triggers for midday moves
D. What would work (simulations & quality filters)

Data sources:
- enriched-signals.csv (1841 signals)
- big-moves.csv (9596 rows)
- IB 5m/15m/1h/1d parquet files (13 symbols, 2+ years)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import time, timedelta
import warnings
warnings.filterwarnings('ignore')

# ── Paths ──────────────────────────────────────────────────────────────
BASE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView")
DEBUG = BASE / "debug"
CACHE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars")

SYMBOLS = ['SPY', 'QQQ', 'AAPL', 'AMZN', 'AMD', 'GOOGL', 'META', 'MSFT', 'NVDA', 'TSLA', 'TSM', 'GLD', 'SLV']

# ── Helpers ────────────────────────────────────────────────────────────
def parse_time_to_minutes(t_str):
    """Convert 'H:MM' or 'HH:MM' to minutes since midnight."""
    parts = t_str.split(':')
    return int(parts[0]) * 60 + int(parts[1])

def time_bucket_30m(t_str):
    """Assign time string to 30-min bucket."""
    m = parse_time_to_minutes(t_str)
    if m < 600: return '09:30-10:00'
    elif m < 630: return '10:00-10:30'
    elif m < 660: return '10:30-11:00'
    elif m < 690: return '11:00-11:30'
    elif m < 720: return '11:30-12:00'
    elif m < 750: return '12:00-12:30'
    elif m < 780: return '12:30-13:00'
    elif m < 810: return '13:00-13:30'
    elif m < 840: return '13:30-14:00'
    elif m < 870: return '14:00-14:30'
    elif m < 900: return '14:30-15:00'
    elif m < 930: return '15:00-15:30'
    else: return '15:30-16:00'

def load_ib_data(symbol, timeframe):
    """Load IB parquet data, convert to ET."""
    fname = f"{symbol.lower()}_{timeframe}_ib.parquet"
    fpath = CACHE / fname
    if not fpath.exists():
        return None
    df = pd.read_parquet(fpath)
    df['date'] = pd.to_datetime(df['date'])
    if df['date'].dt.tz is not None:
        df['date'] = df['date'].dt.tz_convert('US/Eastern')
    else:
        df['date'] = df['date'].dt.tz_localize('US/Eastern')
    return df

def compute_atr(daily_df, period=14):
    """Compute ATR from daily OHLC data."""
    h = daily_df['high']
    l = daily_df['low']
    c = daily_df['close'].shift(1)
    tr = pd.concat([h - l, (h - c).abs(), (l - c).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean()


# ══════════════════════════════════════════════════════════════════════
# SECTION A: Anatomy of the Midday Desert
# ══════════════════════════════════════════════════════════════════════
def section_a():
    print("=" * 70)
    print("SECTION A: Anatomy of the Midday Desert")
    print("=" * 70)

    # Load enriched signals
    signals = pd.read_csv(DEBUG / "enriched-signals.csv")
    signals['mins'] = signals['time'].apply(parse_time_to_minutes)
    signals['bucket30'] = signals['time'].apply(time_bucket_30m)

    # A1: Signal count by 30-min bucket
    print("\n--- A1: Signal count by 30-min bucket ---")
    bucket_order = [
        '09:30-10:00', '10:00-10:30', '10:30-11:00', '11:00-11:30',
        '11:30-12:00', '12:00-12:30', '12:30-13:00', '13:00-13:30',
        '13:30-14:00', '14:00-14:30', '14:30-15:00', '15:00-15:30', '15:30-16:00'
    ]
    bucket_counts = signals.groupby('bucket30').agg(
        count=('symbol', 'size'),
        avg_mfe=('mfe', 'mean'),
        avg_mae=('mae', 'mean'),
        pnl=('mfe', lambda x: (x + signals.loc[x.index, 'mae']).sum()),  # mfe + mae (mae is negative)
        win_rate=('mfe', lambda x: (x > -signals.loc[x.index, 'mae']).mean())
    ).reindex(bucket_order)

    n_days = signals['date'].nunique()
    bucket_counts['per_day'] = (bucket_counts['count'] / n_days).round(1)

    results_a1 = []
    for b in bucket_order:
        row = bucket_counts.loc[b] if b in bucket_counts.index else pd.Series({'count': 0, 'per_day': 0, 'avg_mfe': 0, 'avg_mae': 0, 'win_rate': 0})
        results_a1.append({
            'bucket': b,
            'signals': int(row['count']) if not pd.isna(row['count']) else 0,
            'per_day': row['per_day'] if not pd.isna(row.get('per_day', 0)) else 0,
            'avg_mfe': round(row['avg_mfe'], 3) if not pd.isna(row['avg_mfe']) else 0,
            'avg_mae': round(row['avg_mae'], 3) if not pd.isna(row['avg_mae']) else 0,
            'win_rate': round(row['win_rate'] * 100, 1) if not pd.isna(row['win_rate']) else 0
        })
    df_a1 = pd.DataFrame(results_a1)
    print(df_a1.to_string(index=False))

    # A2: Big moves analysis by time
    print("\n--- A2: Big moves by time bucket (>= 1 ATR) ---")
    bigmoves = pd.read_csv(DEBUG / "big-moves.csv")
    bigmoves['mins'] = bigmoves['time'].apply(parse_time_to_minutes)
    bigmoves['bucket30'] = bigmoves['time'].apply(time_bucket_30m)

    # Filter to >= 1 ATR
    bm_1atr = bigmoves[bigmoves['range_atr'] >= 1.0].copy()
    bm_midday = bm_1atr[bm_1atr['mins'] >= 660].copy()  # >= 11:00

    bm_n_days = bigmoves['date'].nunique()
    bm_bucket = bm_1atr.groupby('bucket30').agg(
        count=('symbol', 'size'),
        avg_atr=('range_atr', 'mean'),
        max_atr=('range_atr', 'max'),
        avg_mfe=('mfe', 'mean'),
        avg_vol=('vol_ratio', 'mean')
    ).reindex(bucket_order)
    bm_bucket['per_day'] = (bm_bucket['count'] / bm_n_days).round(1)
    print(bm_bucket.to_string())

    print(f"\nTotal >= 1 ATR moves: {len(bm_1atr)}")
    print(f"  Morning (<11:00): {len(bm_1atr[bm_1atr['mins'] < 660])}")
    print(f"  Midday (>=11:00): {len(bm_midday)}")
    print(f"  Midday per day:   {len(bm_midday) / bm_n_days:.1f}")

    # A2b: Midday big moves by symbol
    print("\n--- A2b: Midday (>=11:00) big moves by symbol ---")
    sym_midday = bm_midday.groupby('symbol').agg(
        count=('date', 'size'),
        avg_atr=('range_atr', 'mean'),
        avg_mfe=('mfe', 'mean'),
        bull_pct=('direction', lambda x: (x == 'bull').mean() * 100)
    ).sort_values('count', ascending=False)
    print(sym_midday.round(2).to_string())

    # A3: Why no signals? Check EMA alignment for midday moves
    print("\n--- A3: Why no signals for midday moves? ---")
    midday_chars = bm_midday.groupby('ema_aligned').agg(
        count=('symbol', 'size'),
        avg_atr=('range_atr', 'mean'),
        avg_mfe=('mfe', 'mean')
    )
    print("EMA alignment of midday moves:")
    print(midday_chars.to_string())
    ema_pct = (bm_midday['ema_aligned'] == True).mean() * 100
    print(f"  EMA aligned: {ema_pct:.1f}%")

    vwap_chars = bm_midday.groupby('vwap_aligned').agg(
        count=('symbol', 'size'),
        avg_atr=('range_atr', 'mean'),
        avg_mfe=('mfe', 'mean')
    )
    print("\nVWAP alignment of midday moves:")
    print(vwap_chars.to_string())

    adx_high = (bm_midday['adx'] > 25).mean() * 100
    print(f"\nADX > 25: {adx_high:.1f}%")

    # A4: What triggers midday moves?
    print("\n--- A4: Midday move characteristics ---")
    print(f"Average volume ratio: {bm_midday['vol_ratio'].mean():.2f}x")
    print(f"Average body %: {bm_midday['body_pct'].mean():.0f}%")
    print(f"Average ADX: {bm_midday['adx'].mean():.1f}")
    print(f"Prev same direction: {bm_midday['prev_same_dir'].mean() * 100:.1f}%")
    print(f"Average prev vol ratio: {bm_midday['prev_vol_ratio'].mean():.2f}x")

    # Volume compression before midday moves
    low_vol_before = (bm_midday['prev_vol_ratio'] < 0.5).mean() * 100
    high_vol_move = (bm_midday['vol_ratio'] >= 3.0).mean() * 100
    print(f"Preceded by low vol (<0.5x): {low_vol_before:.1f}%")
    print(f"Move itself high vol (>=3x): {high_vol_move:.1f}%")

    return signals, bigmoves, bm_midday, bm_1atr


# ══════════════════════════════════════════════════════════════════════
# SECTION B: Wider Timeframe Levels as Midday S/R
# ══════════════════════════════════════════════════════════════════════
def section_b(bm_midday):
    print("\n" + "=" * 70)
    print("SECTION B: Wider-Timeframe Levels as Midday Support/Resistance")
    print("=" * 70)

    # Date range from big-moves
    date_range = sorted(bm_midday['date'].unique())
    # Extend backwards for lookback
    start_date = pd.Timestamp(date_range[0]) - pd.Timedelta(days=30)
    end_date = pd.Timestamp(date_range[-1])

    results = []

    for sym in SYMBOLS:
        print(f"\n  Processing {sym}...")

        # Load daily data for level computation
        daily = load_ib_data(sym, '1_day')
        if daily is None:
            print(f"    Skipping {sym} — no daily data")
            continue

        # Load 5m data for VWAP bands
        fivemin = load_ib_data(sym, '5_mins')
        if fivemin is None:
            print(f"    Skipping {sym} — no 5m data")
            continue

        # Prepare daily data
        daily = daily.sort_values('date').reset_index(drop=True)
        daily['trade_date'] = daily['date'].dt.date
        daily['atr'] = compute_atr(daily)

        # Get midday moves for this symbol
        sym_moves = bm_midday[bm_midday['symbol'] == sym].copy()
        if len(sym_moves) == 0:
            continue

        # Prepare 5m data
        fivemin = fivemin.sort_values('date').reset_index(drop=True)
        fivemin['trade_date'] = fivemin['date'].dt.date
        fivemin['hour'] = fivemin['date'].dt.hour
        fivemin['minute'] = fivemin['date'].dt.minute

        # Filter to RTH (9:30-16:00 ET)
        fivemin = fivemin[
            ((fivemin['hour'] == 9) & (fivemin['minute'] >= 30)) |
            ((fivemin['hour'] >= 10) & (fivemin['hour'] < 16))
        ].copy()

        for _, move in sym_moves.iterrows():
            move_date = pd.Timestamp(move['date']).date()
            move_price = move['open']
            move_dir = move['direction']
            move_atr_val = move['atr']

            if move_atr_val == 0 or pd.isna(move_atr_val):
                continue

            # Get daily data up to but NOT including the move date
            prior_daily = daily[daily['trade_date'] < move_date].tail(20)
            if len(prior_daily) < 5:
                continue

            atr_val = prior_daily['atr'].iloc[-1]
            if pd.isna(atr_val) or atr_val == 0:
                atr_val = move_atr_val

            threshold = move_price * 0.003  # 0.3% proximity

            # Build wider-TF levels
            levels = {}

            # Prior day H/L (already in KLB)
            levels['PD_High'] = prior_daily['high'].iloc[-1]
            levels['PD_Low'] = prior_daily['low'].iloc[-1]

            # 2-day H/L
            if len(prior_daily) >= 2:
                levels['2D_High'] = prior_daily['high'].iloc[-2:].max()
                levels['2D_Low'] = prior_daily['low'].iloc[-2:].min()

            # 3-day H/L
            if len(prior_daily) >= 3:
                levels['3D_High'] = prior_daily['high'].iloc[-3:].max()
                levels['3D_Low'] = prior_daily['low'].iloc[-3:].min()

            # 5-day H/L
            if len(prior_daily) >= 5:
                levels['5D_High'] = prior_daily['high'].iloc[-5:].max()
                levels['5D_Low'] = prior_daily['low'].iloc[-5:].min()

            # 10-day H/L
            if len(prior_daily) >= 10:
                levels['10D_High'] = prior_daily['high'].iloc[-10:].max()
                levels['10D_Low'] = prior_daily['low'].iloc[-10:].min()

            # Weekly open (Monday's open of current week)
            move_ts = pd.Timestamp(move_date)
            week_start = move_ts - pd.Timedelta(days=move_ts.weekday())
            week_daily = daily[daily['trade_date'] >= week_start.date()]
            if len(week_daily) > 0:
                levels['Week_Open'] = week_daily.iloc[0]['open']

            # Monthly open
            month_start = move_ts.replace(day=1)
            month_daily = daily[daily['trade_date'] >= month_start.date()]
            if len(month_daily) > 0:
                levels['Month_Open'] = month_daily.iloc[0]['open']

            # Prior day mid
            levels['PD_Mid'] = (prior_daily['high'].iloc[-1] + prior_daily['low'].iloc[-1]) / 2

            # Fibonacci levels from prior day range
            pd_high = prior_daily['high'].iloc[-1]
            pd_low = prior_daily['low'].iloc[-1]
            pd_range = pd_high - pd_low
            levels['Fib_236'] = pd_low + 0.236 * pd_range
            levels['Fib_382'] = pd_low + 0.382 * pd_range
            levels['Fib_618'] = pd_low + 0.618 * pd_range
            levels['Fib_786'] = pd_low + 0.786 * pd_range

            # VWAP bands from today's intraday data up to the move time
            move_mins = parse_time_to_minutes(move['time'])
            today_5m = fivemin[fivemin['trade_date'] == move_date].copy()
            today_5m['bar_mins'] = today_5m['hour'] * 60 + today_5m['minute']
            pre_move = today_5m[today_5m['bar_mins'] < move_mins]

            if len(pre_move) > 5:
                # Compute VWAP and std dev bands
                typical = (pre_move['high'] + pre_move['low'] + pre_move['close']) / 3
                cum_vol = pre_move['volume'].cumsum()
                cum_tp_vol = (typical * pre_move['volume']).cumsum()
                vwap = cum_tp_vol / cum_vol
                vwap_val = vwap.iloc[-1]

                # Variance for bands
                sq_dev = ((typical - vwap) ** 2 * pre_move['volume']).cumsum()
                variance = sq_dev / cum_vol
                std = np.sqrt(variance.iloc[-1])

                levels['VWAP'] = vwap_val
                levels['VWAP_Upper1'] = vwap_val + std
                levels['VWAP_Lower1'] = vwap_val - std
                levels['VWAP_Upper2'] = vwap_val + 2 * std
                levels['VWAP_Lower2'] = vwap_val - 2 * std

            # Prior day close
            levels['PD_Close'] = prior_daily['close'].iloc[-1]

            # Today's open
            if len(today_5m) > 0:
                levels['Today_Open'] = today_5m.iloc[0]['open']

            # Check proximity for each level
            for level_name, level_price in levels.items():
                if pd.isna(level_price):
                    continue
                dist = abs(move_price - level_price)
                dist_pct = dist / move_price
                dist_atr = dist / atr_val

                # Determine if level acts as breakout or reversal point
                if move_dir == 'bull':
                    role = 'breakout' if move_price > level_price else 'reversal'
                else:
                    role = 'breakout' if move_price < level_price else 'reversal'

                results.append({
                    'symbol': sym,
                    'date': move['date'],
                    'time': move['time'],
                    'move_dir': move_dir,
                    'move_atr': move['range_atr'],
                    'move_mfe': move['mfe'],
                    'move_price': move_price,
                    'level_name': level_name,
                    'level_price': level_price,
                    'dist_pct': dist_pct,
                    'dist_atr': dist_atr,
                    'role': role,
                    'ema_aligned': move['ema_aligned'],
                    'vol_ratio': move['vol_ratio']
                })

    df_levels = pd.DataFrame(results)
    if len(df_levels) == 0:
        print("No level proximity data generated!")
        return pd.DataFrame()

    # B5/B6: Proximity analysis — within 0.3% of move start
    print("\n--- B5/B6: Level proximity to midday moves (within 0.3%) ---")
    near = df_levels[df_levels['dist_pct'] <= 0.003].copy()
    total_moves_with_levels = df_levels.drop_duplicates(subset=['symbol', 'date', 'time'])

    level_stats = near.groupby('level_name').agg(
        hits=('symbol', 'size'),
        avg_dist_pct=('dist_pct', 'mean'),
        avg_move_atr=('move_atr', 'mean'),
        avg_mfe=('move_mfe', 'mean'),
        breakout_pct=('role', lambda x: (x == 'breakout').mean() * 100),
        ema_aligned_pct=('ema_aligned', 'mean')
    ).sort_values('hits', ascending=False)

    n_total_moves = len(total_moves_with_levels)
    level_stats['hit_rate'] = (level_stats['hits'] / n_total_moves * 100).round(1)
    print(f"\nTotal unique midday moves analyzed: {n_total_moves}")
    print(f"Moves with ANY level within 0.3%: {near.drop_duplicates(subset=['symbol','date','time']).shape[0]} ({near.drop_duplicates(subset=['symbol','date','time']).shape[0]/n_total_moves*100:.1f}%)")
    print(level_stats.round(3).to_string())

    # B7: Best wider-TF levels (excluding ones already in KLB)
    print("\n--- B7: NEW levels NOT in KLB (ranked by hit rate * avg MFE) ---")
    existing_klb = ['PD_High', 'PD_Low', 'PD_Mid', 'VWAP']
    new_levels = level_stats[~level_stats.index.isin(existing_klb)].copy()
    new_levels['score'] = new_levels['hit_rate'] * new_levels['avg_mfe']
    new_levels = new_levels.sort_values('score', ascending=False)
    print(new_levels.round(3).to_string())

    # Wider proximity check: within 0.5%
    print("\n--- B6b: Level proximity within 0.5% ---")
    near_05 = df_levels[df_levels['dist_pct'] <= 0.005].copy()
    level_stats_05 = near_05.groupby('level_name').agg(
        hits=('symbol', 'size'),
        avg_move_atr=('move_atr', 'mean'),
        avg_mfe=('move_mfe', 'mean'),
    ).sort_values('hits', ascending=False)
    level_stats_05['hit_rate'] = (level_stats_05['hits'] / n_total_moves * 100).round(1)
    print(level_stats_05.round(3).to_string())

    return df_levels


# ══════════════════════════════════════════════════════════════════════
# SECTION C: Non-Keylevel Triggers for Midday
# ══════════════════════════════════════════════════════════════════════
def section_c():
    print("\n" + "=" * 70)
    print("SECTION C: Non-Keylevel Triggers for Midday")
    print("=" * 70)

    bigmoves = pd.read_csv(DEBUG / "big-moves.csv")
    bigmoves['mins'] = bigmoves['time'].apply(parse_time_to_minutes)

    # Date range from big-moves
    date_range = sorted(bigmoves['date'].unique())
    # Use Jan 20 – Feb 27 range (same as big-moves)
    study_dates = [d for d in date_range]

    # C8: Volume compression → expansion
    print("\n--- C8: Volume compression → expansion (midday) ---")

    compression_results = []
    c9_results = []
    c10_results = []
    c11_results = []

    for sym in SYMBOLS:
        fivemin = load_ib_data(sym, '5_mins')
        daily = load_ib_data(sym, '1_day')
        if fivemin is None or daily is None:
            continue

        fivemin = fivemin.sort_values('date').reset_index(drop=True)
        fivemin['trade_date'] = fivemin['date'].dt.date
        fivemin['hour'] = fivemin['date'].dt.hour
        fivemin['minute'] = fivemin['date'].dt.minute

        # Filter to RTH
        fivemin = fivemin[
            ((fivemin['hour'] == 9) & (fivemin['minute'] >= 30)) |
            ((fivemin['hour'] >= 10) & (fivemin['hour'] < 16))
        ].copy()

        fivemin['bar_mins'] = fivemin['hour'] * 60 + fivemin['minute']

        # Daily ATR
        daily = daily.sort_values('date').reset_index(drop=True)
        daily['trade_date'] = daily['date'].dt.date
        daily['atr'] = compute_atr(daily)
        atr_map = dict(zip(daily['trade_date'], daily['atr']))

        for td in fivemin['trade_date'].unique():
            td_date_str = str(td)
            if td_date_str not in study_dates:
                continue

            day_data = fivemin[fivemin['trade_date'] == td].copy().reset_index(drop=True)
            if len(day_data) < 20:
                continue

            atr_val = atr_map.get(td)
            if pd.isna(atr_val) or atr_val is None or atr_val == 0:
                continue

            # Average volume for the day
            avg_vol = day_data['volume'].mean()
            if avg_vol == 0:
                continue

            day_data['vol_ratio'] = day_data['volume'] / avg_vol
            day_data['range_atr'] = (day_data['high'] - day_data['low']) / atr_val

            # Compute VWAP and bands for C9
            typical = (day_data['high'] + day_data['low'] + day_data['close']) / 3
            cum_vol = day_data['volume'].cumsum()
            cum_tp_vol = (typical * day_data['volume']).cumsum()
            vwap = cum_tp_vol / cum_vol
            sq_dev = ((typical - vwap) ** 2 * day_data['volume']).cumsum()
            variance = sq_dev / cum_vol
            std = np.sqrt(variance)
            day_data['vwap'] = vwap
            day_data['vwap_upper1'] = vwap + std
            day_data['vwap_lower1'] = vwap - std
            day_data['vwap_upper2'] = vwap + 2 * std
            day_data['vwap_lower2'] = vwap - 2 * std

            # C8: Find compression → expansion patterns (midday only)
            for i in range(12, len(day_data) - 3):
                if day_data['bar_mins'].iloc[i] < 660:  # Skip before 11:00
                    continue

                # Check for 12-bar low volume compression
                lookback = day_data.iloc[i-12:i]
                avg_lookback_vol_ratio = lookback['vol_ratio'].mean()

                if avg_lookback_vol_ratio < 0.5:
                    # Check if current bar is expansion (3x+ vol)
                    if day_data['vol_ratio'].iloc[i] >= 3.0:
                        # Measure follow-through: max move in next 6 bars (30 min)
                        future = day_data.iloc[i:min(i+7, len(day_data))]
                        if len(future) < 2:
                            continue
                        max_up = (future['high'].max() - day_data['close'].iloc[i]) / atr_val
                        max_down = (day_data['close'].iloc[i] - future['low'].min()) / atr_val
                        mfe = max(max_up, max_down)
                        hit_1atr = mfe >= 1.0

                        compression_results.append({
                            'symbol': sym,
                            'date': td_date_str,
                            'time': f"{day_data['hour'].iloc[i]}:{day_data['minute'].iloc[i]:02d}",
                            'vol_expansion': day_data['vol_ratio'].iloc[i],
                            'compression_depth': avg_lookback_vol_ratio,
                            'mfe_atr': round(mfe, 2),
                            'hit_1atr': hit_1atr,
                            'bar_mins': day_data['bar_mins'].iloc[i]
                        })

            # C9: VWAP band touches (midday)
            for i in range(5, len(day_data) - 3):
                if day_data['bar_mins'].iloc[i] < 660:
                    continue

                close_i = day_data['close'].iloc[i]
                vwap_u1 = day_data['vwap_upper1'].iloc[i]
                vwap_l1 = day_data['vwap_lower1'].iloc[i]
                vwap_u2 = day_data['vwap_upper2'].iloc[i]
                vwap_l2 = day_data['vwap_lower2'].iloc[i]

                touch = None
                if abs(close_i - vwap_u1) / atr_val < 0.1:
                    touch = 'upper1'
                elif abs(close_i - vwap_l1) / atr_val < 0.1:
                    touch = 'lower1'
                elif abs(close_i - vwap_u2) / atr_val < 0.1:
                    touch = 'upper2'
                elif abs(close_i - vwap_l2) / atr_val < 0.1:
                    touch = 'lower2'

                if touch:
                    future = day_data.iloc[i:min(i+7, len(day_data))]
                    if len(future) < 2:
                        continue
                    max_up = (future['high'].max() - close_i) / atr_val
                    max_down = (close_i - future['low'].min()) / atr_val

                    # Bounce = reversal from band
                    if 'upper' in touch:
                        bounce_atr = max_down
                        breakout_atr = max_up
                    else:
                        bounce_atr = max_up
                        breakout_atr = max_down

                    c9_results.append({
                        'symbol': sym,
                        'date': td_date_str,
                        'time': f"{day_data['hour'].iloc[i]}:{day_data['minute'].iloc[i]:02d}",
                        'band': touch,
                        'bounce_atr': round(bounce_atr, 2),
                        'breakout_atr': round(breakout_atr, 2),
                        'bounce_1atr': bounce_atr >= 1.0,
                        'breakout_1atr': breakout_atr >= 1.0
                    })

            # C11: Pullback-and-continuation after morning move (per day)
            morning = day_data[day_data['bar_mins'] < 660]
            midday = day_data[(day_data['bar_mins'] >= 660) & (day_data['bar_mins'] < 930)]

            if len(morning) >= 4 and len(midday) >= 4:
                morning_move = (morning['close'].iloc[-1] - morning['open'].iloc[0]) / atr_val
                morning_high = morning['high'].max()
                morning_low = morning['low'].min()

                if abs(morning_move) >= 1.0:
                    if morning_move > 0:  # Bull morning
                        # Find pullback depth in midday
                        midday_low = midday['low'].min()
                        pullback = (morning_high - midday_low) / atr_val
                        # Find continuation
                        midday_high = midday['high'].max()
                        continuation = (midday_high - morning_high) / atr_val
                        c11_results.append({
                            'symbol': sym,
                            'date': td_date_str,
                            'morning_dir': 'bull',
                            'morning_move_atr': round(morning_move, 2),
                            'pullback_atr': round(pullback, 2),
                            'continuation_atr': round(max(0, continuation), 2),
                            'continued': continuation > 0.5
                        })
                    else:  # Bear morning
                        midday_high = midday['high'].max()
                        pullback = (midday_high - morning_low) / atr_val
                        midday_low = midday['low'].min()
                        continuation = (morning_low - midday_low) / atr_val
                        c11_results.append({
                            'symbol': sym,
                            'date': td_date_str,
                            'morning_dir': 'bear',
                            'morning_move_atr': round(abs(morning_move), 2),
                            'pullback_atr': round(pullback, 2),
                            'continuation_atr': round(max(0, continuation), 2),
                            'continued': continuation > 0.5
                        })

    # C8 results
    df_c8 = pd.DataFrame(compression_results)
    if len(df_c8) > 0:
        print(f"\nVolume compression→expansion events (midday): {len(df_c8)}")
        print(f"  Hit 1 ATR: {df_c8['hit_1atr'].sum()} ({df_c8['hit_1atr'].mean()*100:.1f}%)")
        print(f"  Avg MFE: {df_c8['mfe_atr'].mean():.2f} ATR")
        print(f"  Avg vol expansion: {df_c8['vol_expansion'].mean():.1f}x")
        print(f"  Events per day: {len(df_c8) / len(study_dates):.1f}")

        # By time
        df_c8['bucket30'] = df_c8['time'].apply(time_bucket_30m)
        c8_by_time = df_c8.groupby('bucket30').agg(
            count=('symbol', 'size'),
            hit_rate=('hit_1atr', 'mean'),
            avg_mfe=('mfe_atr', 'mean')
        )
        print("\n  By time bucket:")
        print(c8_by_time.round(3).to_string())
    else:
        print("\nNo volume compression→expansion events found midday.")

    # C9 results
    df_c9 = pd.DataFrame(c9_results)
    if len(df_c9) > 0:
        print(f"\n--- C9: VWAP band touches (midday) ---")
        print(f"Total touches: {len(df_c9)}")
        c9_by_band = df_c9.groupby('band').agg(
            count=('symbol', 'size'),
            bounce_rate=('bounce_1atr', 'mean'),
            avg_bounce=('bounce_atr', 'mean'),
            breakout_rate=('breakout_1atr', 'mean'),
            avg_breakout=('breakout_atr', 'mean')
        )
        print(c9_by_band.round(3).to_string())
        print(f"\n  Overall bounce rate (1 ATR): {df_c9['bounce_1atr'].mean()*100:.1f}%")
        print(f"  Overall breakout rate (1 ATR): {df_c9['breakout_1atr'].mean()*100:.1f}%")
    else:
        print("\nNo VWAP band touches found midday.")

    # C10: Cross-symbol momentum
    print(f"\n--- C10: Cross-symbol momentum (midday) ---")
    # Build per-5min-bar direction for all symbols
    cross_sym_data = {}
    for sym in SYMBOLS:
        fivemin = load_ib_data(sym, '5_mins')
        if fivemin is None:
            continue
        fivemin = fivemin.sort_values('date').reset_index(drop=True)
        fivemin['trade_date'] = fivemin['date'].dt.date
        fivemin['hour'] = fivemin['date'].dt.hour
        fivemin['minute'] = fivemin['date'].dt.minute
        fivemin = fivemin[
            ((fivemin['hour'] == 9) & (fivemin['minute'] >= 30)) |
            ((fivemin['hour'] >= 10) & (fivemin['hour'] < 16))
        ].copy()
        fivemin['bar_key'] = fivemin['trade_date'].astype(str) + '_' + fivemin['hour'].astype(str) + ':' + fivemin['minute'].apply(lambda x: f'{x:02d}')
        fivemin['dir'] = np.where(fivemin['close'] > fivemin['open'], 1, -1)
        fivemin['pct_move'] = (fivemin['close'] - fivemin['open']) / fivemin['open'] * 100
        cross_sym_data[sym] = fivemin.set_index('bar_key')[['dir', 'pct_move', 'trade_date', 'hour', 'minute']].to_dict('index')

    # Find bars where 4+ symbols move same direction
    all_bar_keys = set()
    for sym in cross_sym_data:
        all_bar_keys.update(cross_sym_data[sym].keys())

    momentum_events = []
    for bk in sorted(all_bar_keys):
        # Only midday
        parts = bk.split('_', 1)
        if len(parts) != 2:
            continue
        date_str, time_str = parts
        h, m = map(int, time_str.split(':'))
        if h * 60 + m < 660:  # Before 11:00
            continue
        if date_str not in study_dates:
            continue

        bull_count = 0
        bear_count = 0
        total = 0
        for sym in cross_sym_data:
            if bk in cross_sym_data[sym]:
                total += 1
                if cross_sym_data[sym][bk]['dir'] == 1:
                    bull_count += 1
                else:
                    bear_count += 1

        if total >= 8 and (bull_count >= 4 or bear_count >= 4):
            dominant_dir = 'bull' if bull_count >= bear_count else 'bear'
            aligned = max(bull_count, bear_count)

            # Check follow-through: do 3 of the next 6 bars (15-30 min window) also align?
            # We'll track this approximately
            momentum_events.append({
                'date': date_str,
                'time': time_str,
                'aligned': aligned,
                'total': total,
                'dir': dominant_dir,
                'align_pct': aligned / total * 100
            })

    df_c10 = pd.DataFrame(momentum_events)
    if len(df_c10) > 0:
        # Analyze different threshold levels
        for thresh in [4, 6, 8, 10]:
            subset = df_c10[df_c10['aligned'] >= thresh]
            print(f"  {thresh}+ symbols aligned: {len(subset)} events ({len(subset)/len(study_dates):.1f}/day)")

        # Check follow-through for high-alignment events
        # For 8+ alignment, check SPY's next 6 bars
        high_align = df_c10[df_c10['aligned'] >= 8].copy()
        if len(high_align) > 0:
            spy_5m = load_ib_data('SPY', '5_mins')
            if spy_5m is not None:
                spy_5m = spy_5m.sort_values('date').reset_index(drop=True)
                spy_5m['trade_date'] = spy_5m['date'].dt.date
                spy_5m['hour'] = spy_5m['date'].dt.hour
                spy_5m['minute'] = spy_5m['date'].dt.minute
                spy_5m = spy_5m[
                    ((spy_5m['hour'] == 9) & (spy_5m['minute'] >= 30)) |
                    ((spy_5m['hour'] >= 10) & (spy_5m['hour'] < 16))
                ].copy()

                daily = load_ib_data('SPY', '1_day')
                daily = daily.sort_values('date').reset_index(drop=True)
                daily['trade_date'] = daily['date'].dt.date
                daily['atr'] = compute_atr(daily)
                atr_map = dict(zip(daily['trade_date'], daily['atr']))

                follow_results = []
                for _, ev in high_align.iterrows():
                    ev_date = pd.Timestamp(ev['date']).date()
                    ev_h, ev_m = map(int, ev['time'].split(':'))
                    ev_mins = ev_h * 60 + ev_m

                    day_spy = spy_5m[spy_5m['trade_date'] == ev_date].reset_index(drop=True)
                    day_spy['bar_mins'] = day_spy['hour'] * 60 + day_spy['minute']

                    # Find the bar
                    bar_idx_list = day_spy[day_spy['bar_mins'] == ev_mins].index
                    if len(bar_idx_list) == 0:
                        continue
                    bar_idx = bar_idx_list[0]

                    future = day_spy.iloc[bar_idx:min(bar_idx+7, len(day_spy))]
                    atr_val = atr_map.get(ev_date, 1.0)
                    if pd.isna(atr_val) or atr_val == 0:
                        continue

                    entry = day_spy['close'].iloc[bar_idx]
                    if ev['dir'] == 'bull':
                        mfe = (future['high'].max() - entry) / atr_val
                        mae = (entry - future['low'].min()) / atr_val
                    else:
                        mfe = (entry - future['low'].min()) / atr_val
                        mae = (future['high'].max() - entry) / atr_val

                    follow_results.append({
                        'date': ev['date'],
                        'time': ev['time'],
                        'dir': ev['dir'],
                        'aligned': ev['aligned'],
                        'mfe_atr': round(mfe, 2),
                        'mae_atr': round(mae, 2),
                        'hit_1atr': mfe >= 1.0
                    })

                df_follow = pd.DataFrame(follow_results)
                if len(df_follow) > 0:
                    print(f"\n  8+ symbol alignment follow-through (SPY):")
                    print(f"    Events: {len(df_follow)}")
                    print(f"    Avg MFE: {df_follow['mfe_atr'].mean():.2f} ATR")
                    print(f"    Avg MAE: {df_follow['mae_atr'].mean():.2f} ATR")
                    print(f"    Hit 1 ATR: {df_follow['hit_1atr'].mean()*100:.1f}%")
    else:
        print("  No cross-symbol momentum events found.")

    # C11 results
    df_c11 = pd.DataFrame(c11_results)
    if len(df_c11) > 0:
        print(f"\n--- C11: Pullback-and-continuation after morning move ---")
        print(f"Days with 1+ ATR morning move: {len(df_c11)}")
        print(f"  Continued midday (>0.5 ATR): {df_c11['continued'].sum()} ({df_c11['continued'].mean()*100:.1f}%)")
        print(f"  Avg pullback: {df_c11['pullback_atr'].mean():.2f} ATR")
        print(f"  Avg continuation: {df_c11['continuation_atr'].mean():.2f} ATR")
        print(f"  Avg morning move: {df_c11['morning_move_atr'].mean():.2f} ATR")

        # By direction
        for d in ['bull', 'bear']:
            sub = df_c11[df_c11['morning_dir'] == d]
            if len(sub) > 0:
                print(f"\n  {d.upper()} morning ({len(sub)} days):")
                print(f"    Continuation rate: {sub['continued'].mean()*100:.1f}%")
                print(f"    Avg pullback: {sub['pullback_atr'].mean():.2f} ATR")
                print(f"    Avg continuation: {sub['continuation_atr'].mean():.2f} ATR")

        # Pullback depth histogram
        print("\n  Pullback depth distribution:")
        bins = [0, 0.3, 0.5, 0.8, 1.0, 1.5, 5.0]
        labels = ['<0.3', '0.3-0.5', '0.5-0.8', '0.8-1.0', '1.0-1.5', '1.5+']
        df_c11['pb_bin'] = pd.cut(df_c11['pullback_atr'], bins=bins, labels=labels)
        pb_dist = df_c11.groupby('pb_bin', observed=True).agg(
            count=('symbol', 'size'),
            cont_rate=('continued', 'mean'),
            avg_cont=('continuation_atr', 'mean')
        )
        print(pb_dist.round(3).to_string())
    else:
        print("\nNo pullback-and-continuation data.")

    return df_c8, df_c9, df_c10, df_c11


# ══════════════════════════════════════════════════════════════════════
# SECTION D: What Would Work?
# ══════════════════════════════════════════════════════════════════════
def section_d(bm_midday, df_levels):
    print("\n" + "=" * 70)
    print("SECTION D: What Would Work? — Simulation & Quality Filters")
    print("=" * 70)

    if len(df_levels) == 0:
        print("No level data available for simulation.")
        return

    # D12: Simulate wider-TF levels + ungated RNG
    print("\n--- D12: Simulated midday signals from wider-TF levels ---")

    # Moves near a wider-TF level (within 0.3%)
    near_level = df_levels[df_levels['dist_pct'] <= 0.003].copy()
    unique_near = near_level.drop_duplicates(subset=['symbol', 'date', 'time'])

    # Exclude already-in-KLB levels
    existing_klb = ['PD_High', 'PD_Low', 'PD_Mid', 'VWAP']
    new_level_near = near_level[~near_level['level_name'].isin(existing_klb)]
    unique_new = new_level_near.drop_duplicates(subset=['symbol', 'date', 'time'])

    total_midday = bm_midday.drop_duplicates(subset=['symbol', 'date', 'time']).shape[0]

    print(f"Total midday moves >= 1 ATR: {total_midday}")
    print(f"Near ANY level (incl existing): {len(unique_near)} ({len(unique_near)/total_midday*100:.1f}%)")
    print(f"Near NEW level (not in KLB): {len(unique_new)} ({len(unique_new)/total_midday*100:.1f}%)")

    # Simulate PnL
    if len(unique_new) > 0:
        print(f"\n  New-level-proximate moves:")
        print(f"    Avg move ATR: {unique_new['move_atr'].mean():.2f}")
        print(f"    Avg MFE: {unique_new['move_mfe'].mean():.2f}")
        print(f"    Total MFE ATR: {unique_new['move_mfe'].sum():.1f}")

    # EMA-aligned subset
    new_ema = unique_new[unique_new['ema_aligned'] == True]
    new_no_ema = unique_new[unique_new['ema_aligned'] == False]
    print(f"\n  EMA aligned: {len(new_ema)} signals, avg MFE: {new_ema['move_mfe'].mean():.2f}" if len(new_ema) > 0 else "")
    print(f"  Not EMA aligned: {len(new_no_ema)} signals, avg MFE: {new_no_ema['move_mfe'].mean():.2f}" if len(new_no_ema) > 0 else "")

    # D13: Alternative quality filters for midday
    print("\n--- D13: Alternative quality filters for midday ---")

    # Test various filters on all midday moves
    filters = {
        'EMA aligned': bm_midday['ema_aligned'] == True,
        'VWAP aligned': bm_midday['vwap_aligned'] == True,
        'ADX > 25': bm_midday['adx'] > 25,
        'ADX > 30': bm_midday['adx'] > 30,
        'ADX > 40': bm_midday['adx'] > 40,
        'Vol >= 2x': bm_midday['vol_ratio'] >= 2.0,
        'Vol >= 3x': bm_midday['vol_ratio'] >= 3.0,
        'Body >= 60%': bm_midday['body_pct'] >= 60,
        'Body >= 70%': bm_midday['body_pct'] >= 70,
        'Prev same dir': bm_midday['prev_same_dir'] == True,
        'EMA + ADX>25': (bm_midday['ema_aligned'] == True) & (bm_midday['adx'] > 25),
        'EMA + Vol>=2x': (bm_midday['ema_aligned'] == True) & (bm_midday['vol_ratio'] >= 2.0),
        'EMA + Body>=60': (bm_midday['ema_aligned'] == True) & (bm_midday['body_pct'] >= 60),
        'VWAP + EMA': (bm_midday['vwap_aligned'] == True) & (bm_midday['ema_aligned'] == True),
        'VWAP + ADX>25': (bm_midday['vwap_aligned'] == True) & (bm_midday['adx'] > 25),
        'Prev same + EMA': (bm_midday['prev_same_dir'] == True) & (bm_midday['ema_aligned'] == True),
    }

    filter_results = []
    for name, mask in filters.items():
        subset = bm_midday[mask]
        if len(subset) == 0:
            continue
        filter_results.append({
            'filter': name,
            'N': len(subset),
            'pct_of_midday': len(subset) / len(bm_midday) * 100,
            'avg_mfe': subset['mfe'].mean(),
            'avg_mae': subset['mae'].mean(),
            'avg_range_atr': subset['range_atr'].mean(),
            'mfe_ge1': (subset['mfe'] >= 1.0).mean() * 100
        })

    df_filters = pd.DataFrame(filter_results).sort_values('avg_mfe', ascending=False)
    print(df_filters.round(3).to_string(index=False))

    # Unfiltered baseline
    print(f"\n  Baseline (all midday moves): N={len(bm_midday)}, avg_mfe={bm_midday['mfe'].mean():.3f}, avg_mae={bm_midday['mae'].mean():.3f}")

    # D12b: Best new level types for midday signal generation
    print("\n--- D12b: Best new level types — expected signals and PnL ---")
    new_only = near_level[~near_level['level_name'].isin(existing_klb)]
    if len(new_only) > 0:
        level_pnl = new_only.groupby('level_name').agg(
            signals=('symbol', 'size'),
            avg_mfe=('move_mfe', 'mean'),
            total_mfe=('move_mfe', 'sum'),
            ema_pct=('ema_aligned', 'mean'),
            avg_move=('move_atr', 'mean')
        ).sort_values('total_mfe', ascending=False)
        level_pnl['score'] = level_pnl['signals'] * level_pnl['avg_mfe']
        print(level_pnl.round(3).to_string())

    # Summary statistics
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    total_midday_atr = bm_midday['mfe'].sum()
    print(f"Total midday moves >= 1 ATR: {total_midday}")
    print(f"Total MFE in midday moves: {total_midday_atr:.0f} ATR")

    if len(unique_new) > 0:
        new_atr = unique_new['move_mfe'].sum()
        print(f"\nWith NEW wider-TF levels:")
        print(f"  Additional signals: ~{len(unique_new)}")
        print(f"  Recoverable MFE: {new_atr:.0f} ATR")
        print(f"  If EMA-filtered: ~{len(new_ema)} signals, {new_ema['move_mfe'].sum():.0f} ATR" if len(new_ema) > 0 else "")


# ══════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("MIDDAY DESERT RESEARCH")
    print("=" * 70)
    print(f"Symbols: {', '.join(SYMBOLS)}")
    print()

    # Section A
    signals, bigmoves, bm_midday, bm_1atr = section_a()

    # Section B
    df_levels = section_b(bm_midday)

    # Section C
    df_c8, df_c9, df_c10, df_c11 = section_c()

    # Section D
    section_d(bm_midday, df_levels)

    print("\n\nDone! See midday-desert-research.md for the formatted report.")
