#!/usr/bin/env python3
"""
Scan IB 5-minute data for major moves (>= 0.5 ATR) on a target date.
Reports: daily stats, key levels, major intraday moves, cross-symbol coordination.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import time
import warnings
warnings.filterwarnings('ignore')

# ── Config ──────────────────────────────────────────────────────────────
CACHE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars")
SYMBOLS = ["SPY", "AAPL", "AMD", "AMZN", "GLD", "GOOGL", "META", "MSFT", "NFLX", "NVDA", "QQQ", "SLV", "TSLA", "TSM", "XLE"]
TARGET_DATE = "2026-03-07"
ET = "US/Eastern"
RTH_START = time(9, 30)
RTH_END = time(16, 0)
PM_START = time(9, 0)
ATR_PERIOD = 14
MAJOR_ATR_THRESHOLD = 1.0
NOTABLE_ATR_THRESHOLD = 0.5


def load_5m(symbol):
    fp = CACHE / f"{symbol.lower()}_5_mins_ib.parquet"
    if not fp.exists():
        return None
    df = pd.read_parquet(fp)
    df['dt_et'] = df['date'].dt.tz_convert(ET)
    df['trade_date'] = df['dt_et'].dt.date
    df['trade_time'] = df['dt_et'].dt.time
    return df


def load_daily(symbol):
    fp = CACHE / f"{symbol.lower()}_1_day_ib.parquet"
    if not fp.exists():
        return None
    df = pd.read_parquet(fp)
    if df['date'].dt.tz is None:
        df['trade_date'] = df['date'].dt.date
    else:
        df['trade_date'] = df['date'].dt.tz_convert(ET).dt.date
    return df


def compute_atr(daily_df, before_date, period=ATR_PERIOD):
    hist = daily_df[daily_df['trade_date'] < before_date].tail(period + 1)
    if len(hist) < period:
        return None
    tr = pd.DataFrame({
        'hl': hist['high'] - hist['low'],
        'hc': (hist['high'] - hist['close'].shift(1)).abs(),
        'lc': (hist['low'] - hist['close'].shift(1)).abs()
    }).max(axis=1)
    return tr.tail(period).mean()


def find_moves(rth_df, atr_val, threshold=NOTABLE_ATR_THRESHOLD):
    """
    Find directional moves >= threshold ATR.
    Uses a zigzag approach: identify significant swings, then measure between them.
    """
    if rth_df.empty or atr_val is None or atr_val == 0:
        return []

    df = rth_df.reset_index(drop=True)
    n = len(df)
    if n < 3:
        return []

    highs = df['high'].values
    lows = df['low'].values
    # Keep as pandas Series to preserve tz-aware timestamps
    dt_et = df['dt_et'].reset_index(drop=True)

    moves = []

    # Method: scan all pairs of bars (i, j) where j > i, and measure
    # max high - min low between them, checking if directional (low before high or vice versa).
    # For efficiency, limit to windows up to full day (78 bars for 5m).
    # Use vectorized rolling to find candidate windows.

    # For each starting bar, track running min-low and max-high
    for i in range(n):
        run_high = highs[i]
        run_low = lows[i]
        run_high_idx = i
        run_low_idx = i

        for j in range(i + 1, n):
            if highs[j] > run_high:
                run_high = highs[j]
                run_high_idx = j
            if lows[j] < run_low:
                run_low = lows[j]
                run_low_idx = j

            magnitude = run_high - run_low
            mag_atr = magnitude / atr_val

            if mag_atr < threshold:
                continue

            # Only report if we can determine direction
            if run_low_idx < run_high_idx:
                moves.append({
                    'direction': 'BULL',
                    'start_time': dt_et.iloc[run_low_idx],
                    'end_time': dt_et.iloc[run_high_idx],
                    'low': run_low,
                    'high': run_high,
                    'magnitude': magnitude,
                    'mag_atr': mag_atr,
                    'bars': run_high_idx - run_low_idx + 1,
                })
            elif run_high_idx < run_low_idx:
                moves.append({
                    'direction': 'BEAR',
                    'start_time': dt_et.iloc[run_high_idx],
                    'end_time': dt_et.iloc[run_low_idx],
                    'high': run_high,
                    'low': run_low,
                    'magnitude': magnitude,
                    'mag_atr': mag_atr,
                    'bars': run_low_idx - run_high_idx + 1,
                })

    if not moves:
        return []

    # De-duplicate: keep largest move per overlapping time range + direction
    moves.sort(key=lambda m: m['mag_atr'], reverse=True)
    kept = []
    for m in moves:
        overlap = False
        for k in kept:
            if m['direction'] == k['direction']:
                ov_start = max(m['start_time'], k['start_time'])
                ov_end = min(m['end_time'], k['end_time'])
                if ov_start <= ov_end:
                    m_dur = max((m['end_time'] - m['start_time']).total_seconds(), 1)
                    o_dur = (ov_end - ov_start).total_seconds()
                    if o_dur / m_dur > 0.3:
                        overlap = True
                        break
        if not overlap:
            kept.append(m)

    # Limit to top moves to avoid noise
    kept = kept[:10]
    kept.sort(key=lambda m: m['start_time'])
    return kept


def get_prior_day_levels(df_5m, daily_df, target_date):
    levels = {}

    if daily_df is not None:
        prior_days = daily_df[daily_df['trade_date'] < target_date].tail(5)
        if len(prior_days) >= 1:
            pd_row = prior_days.iloc[-1]
            levels['PD High'] = pd_row['high']
            levels['PD Low'] = pd_row['low']
            levels['PD Close'] = pd_row['close']
        if len(prior_days) >= 5:
            levels['Week High'] = prior_days['high'].max()
            levels['Week Low'] = prior_days['low'].min()
        if len(prior_days) >= 2:
            levels['Yesterday High'] = prior_days.iloc[-1]['high']
            levels['Yesterday Low'] = prior_days.iloc[-1]['low']

    if df_5m is not None:
        target_data = df_5m[df_5m['trade_date'] == target_date]

        pm = target_data[(target_data['trade_time'] >= PM_START) & (target_data['trade_time'] < RTH_START)]
        if not pm.empty:
            levels['PM High'] = pm['high'].max()
            levels['PM Low'] = pm['low'].min()

        orb = target_data[(target_data['trade_time'] >= RTH_START) & (target_data['trade_time'] < time(10, 0))]
        if not orb.empty:
            levels['ORB High'] = orb['high'].max()
            levels['ORB Low'] = orb['low'].min()

    return levels


def fmt_time(ts):
    """Format a tz-aware timestamp to HH:MM ET string."""
    if hasattr(ts, 'strftime'):
        return ts.strftime('%H:%M')
    return str(ts)


def main():
    target_date = pd.Timestamp(TARGET_DATE).date()

    spy_5m = load_5m("SPY")
    if spy_5m is None:
        print("ERROR: Cannot load SPY 5m data")
        return

    available_dates = sorted(spy_5m['trade_date'].unique())
    print(f"Latest available date: {available_dates[-1]}")
    print(f"Target date: {target_date}")

    if target_date not in available_dates:
        print(f"\n!! {target_date} not found in data. Using most recent trading day: {available_dates[-1]}")
        target_date = available_dates[-1]

    print(f"\n{'='*100}")
    print(f"  MAJOR MOVES REPORT -- {target_date}")
    print(f"{'='*100}\n")

    all_symbol_data = {}
    all_moves = []

    for sym in SYMBOLS:
        df_5m = load_5m(sym)
        daily_df = load_daily(sym)

        if df_5m is None:
            print(f"  {sym}: No 5m data found")
            continue

        rth = df_5m[
            (df_5m['trade_date'] == target_date) &
            (df_5m['trade_time'] >= RTH_START) &
            (df_5m['trade_time'] < RTH_END)
        ].copy().reset_index(drop=True)

        if rth.empty:
            print(f"  {sym}: No RTH data for {target_date}")
            continue

        atr = compute_atr(daily_df, target_date) if daily_df is not None else None

        day_open = rth.iloc[0]['open']
        day_high = rth['high'].max()
        day_low = rth['low'].min()
        day_close = rth.iloc[-1]['close']
        day_range = day_high - day_low
        day_volume = rth['volume'].sum()
        day_change = day_close - day_open
        day_change_pct = (day_change / day_open) * 100
        range_atr = day_range / atr if atr else 0

        levels = get_prior_day_levels(df_5m, daily_df, target_date)
        moves = find_moves(rth, atr)

        for m in moves:
            m['symbol'] = sym
            all_moves.append(m)

        all_symbol_data[sym] = {
            'open': day_open, 'high': day_high, 'low': day_low, 'close': day_close,
            'range': day_range, 'volume': day_volume, 'change': day_change,
            'change_pct': day_change_pct, 'atr': atr, 'range_atr': range_atr,
            'levels': levels, 'moves': moves,
        }

    # ── Print Report ────────────────────────────────────────────────────
    sorted_syms = sorted(all_symbol_data.keys(),
                         key=lambda s: abs(all_symbol_data[s].get('range_atr', 0)), reverse=True)

    # 1. Daily Summary
    print("+--- DAILY SUMMARY -------------------------------------------------------------------+")
    print(f"  {'Symbol':<7} {'Open':>9} {'High':>9} {'Low':>9} {'Close':>9} {'Chg%':>7} {'Range':>8} {'RngATR':>7} {'ATR':>7} {'Volume':>12}")
    print(f"  {'---':<7} {'---':>9} {'---':>9} {'---':>9} {'---':>9} {'---':>7} {'---':>8} {'---':>7} {'---':>7} {'---':>12}")
    for sym in sorted_syms:
        d = all_symbol_data[sym]
        arrow = "^" if d['change'] > 0 else "v" if d['change'] < 0 else "-"
        print(f"  {sym:<7} {d['open']:>9.2f} {d['high']:>9.2f} {d['low']:>9.2f} {d['close']:>9.2f} "
              f"{arrow}{d['change_pct']:>+6.2f}% {d['range']:>8.2f} {d['range_atr']:>6.2f}x "
              f"{d['atr']:>7.2f} {d['volume']:>12,.0f}")
    print("+-------------------------------------------------------------------------------------+\n")

    # 2. Key Levels
    print("+--- KEY LEVELS ----------------------------------------------------------------------+")
    for sym in sorted_syms:
        d = all_symbol_data[sym]
        lvls = d['levels']
        if not lvls:
            continue
        parts = [f"{k}: {v:.2f}" for k, v in sorted(lvls.items())]
        print(f"  {sym:<6} {' | '.join(parts)}")
    print("+-------------------------------------------------------------------------------------+\n")

    # 3. Major Moves (>= 1 ATR)
    print("+--- MAJOR MOVES (>= 1.0 ATR) -------------------------------------------------------+")
    major_count = 0
    for sym in sorted_syms:
        d = all_symbol_data[sym]
        majors = [m for m in d['moves'] if m['mag_atr'] >= MAJOR_ATR_THRESHOLD]
        if not majors:
            continue
        major_count += len(majors)
        for m in majors:
            dir_arrow = "^" if m['direction'] == 'BULL' else "v"
            print(f"  {sym:<6} {dir_arrow} {m['direction']:<5} {fmt_time(m['start_time'])}->{fmt_time(m['end_time'])}  "
                  f"${m['low']:.2f}->${m['high']:.2f}  "
                  f"{m['mag_atr']:.2f} ATR  ({m['bars']} bars, ${m['magnitude']:.2f})")
    if major_count == 0:
        print("  No moves >= 1.0 ATR found")
    print(f"\n  Total major: {major_count}")
    print("+-------------------------------------------------------------------------------------+\n")

    # 4. Notable Moves (0.5-1.0 ATR)
    print("+--- NOTABLE MOVES (0.5-1.0 ATR) ----------------------------------------------------+")
    notable_count = 0
    for sym in sorted_syms:
        d = all_symbol_data[sym]
        notables = [m for m in d['moves'] if NOTABLE_ATR_THRESHOLD <= m['mag_atr'] < MAJOR_ATR_THRESHOLD]
        if not notables:
            continue
        notable_count += len(notables)
        for m in notables:
            dir_arrow = "^" if m['direction'] == 'BULL' else "v"
            print(f"  {sym:<6} {dir_arrow} {m['direction']:<5} {fmt_time(m['start_time'])}->{fmt_time(m['end_time'])}  "
                  f"${m['low']:.2f}->${m['high']:.2f}  "
                  f"{m['mag_atr']:.2f} ATR  ({m['bars']} bars, ${m['magnitude']:.2f})")
    if notable_count == 0:
        print("  No notable moves found")
    print(f"\n  Total notable: {notable_count}")
    print("+-------------------------------------------------------------------------------------+\n")

    # 5. Cross-Symbol Coordination
    print("+--- CROSS-SYMBOL COORDINATION (4+ symbols, same direction, within 15 min) -----------+")
    found_clusters = False
    for direction in ['BULL', 'BEAR']:
        # Use all moves >= 0.5 ATR for coordination detection
        dir_moves = [m for m in all_moves if m['direction'] == direction and m['mag_atr'] >= 0.5]
        if len(dir_moves) < 4:
            continue

        dir_moves.sort(key=lambda m: m['start_time'])

        clusters = []
        for i, anchor in enumerate(dir_moves):
            window_end = anchor['start_time'] + pd.Timedelta(minutes=15)
            cluster = [m for m in dir_moves
                      if anchor['start_time'] <= m['start_time'] <= window_end]
            cluster_syms = list(set(m['symbol'] for m in cluster))
            if len(cluster_syms) >= 4:
                clusters.append({
                    'direction': direction,
                    'start': anchor['start_time'],
                    'end': window_end,
                    'symbols': cluster_syms,
                    'count': len(cluster_syms),
                    'moves': cluster,
                })

        # De-dup
        if clusters:
            clusters.sort(key=lambda c: c['count'], reverse=True)
            kept_clusters = []
            for c in clusters:
                ov = False
                for k in kept_clusters:
                    if c['start'] <= k['end'] and c['end'] >= k['start'] and c['direction'] == k['direction']:
                        ov = True
                        break
                if not ov:
                    kept_clusters.append(c)

            for c in kept_clusters:
                found_clusters = True
                d_arrow = "^" if c['direction'] == 'BULL' else "v"
                print(f"  {d_arrow} {c['direction']} ~{fmt_time(c['start'])} ET -- {c['count']} symbols: {', '.join(sorted(c['symbols']))}")
                print(f"    Avg magnitude: {np.mean([m['mag_atr'] for m in c['moves']]):.2f} ATR")
                for m in sorted(c['moves'], key=lambda x: x['mag_atr'], reverse=True):
                    print(f"      {m['symbol']:<6} {fmt_time(m['start_time'])}->{fmt_time(m['end_time'])} {m['mag_atr']:.2f} ATR")
                print()

    if not found_clusters:
        print("  No coordinated moves found (fewer than 4 symbols moving together)")
    print("+-------------------------------------------------------------------------------------+\n")

    # 6. Top moves
    if all_moves:
        top = sorted(all_moves, key=lambda m: m['mag_atr'], reverse=True)[:15]
        print("+--- TOP 15 MOVES BY ATR MAGNITUDE --------------------------------------------------+")
        for i, m in enumerate(top, 1):
            dir_arrow = "^" if m['direction'] == 'BULL' else "v"
            print(f"  {i:>2}. {m['symbol']:<6} {dir_arrow} {m['direction']:<5} {fmt_time(m['start_time'])}->{fmt_time(m['end_time'])}  "
                  f"{m['mag_atr']:.2f} ATR  ${m['low']:.2f}->${m['high']:.2f}")
        print("+-------------------------------------------------------------------------------------+")


if __name__ == '__main__':
    main()
