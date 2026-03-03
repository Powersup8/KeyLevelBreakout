#!/usr/bin/env python3
"""
v2.8 Signal Audit — Comprehensive analysis of KeyLevelBreakout v2.8 Pine logs.

Tasks:
1. Parse v2.8 Pine logs and match to symbols
2. Measure signal follow-through (MFE/MAE in ATR)
3. Investigate MC signals near market open
4. Simulate entry/exit for high-validity signals
5. Find missed signals (>1 ATR moves without fires)
6. Save all results
"""

import pandas as pd
import numpy as np
import re
import os
import glob
from datetime import datetime, timedelta
from pathlib import Path

# ─── Paths ──────────────────────────────────────────────
PROJ = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView")
DEBUG = PROJ / "debug"
CACHE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache")
CACHE_5S  = CACHE / "bars_highres" / "5sec"
CACHE_1M  = CACHE / "bars"
CACHE_5M  = CACHE / "bars"

SYMBOLS = ['SPY', 'QQQ', 'AAPL', 'AMD', 'AMZN', 'META', 'NVDA', 'TSLA', 'GOOGL', 'MSFT', 'GLD', 'SLV', 'TSM']
OUTPUT_FILE = DEBUG / "v28-signal-audit.md"
CSV_OUTPUT  = DEBUG / "v28-signal-audit.csv"

# ─── 1. Parse Pine Logs ───────────────────────────────────

def parse_pine_logs():
    """Parse all Pine log CSVs with evidence stack (v2.8 format)."""
    log_files = sorted(glob.glob(str(DEBUG / "pine-logs-Key Level Breakout_*.csv")))

    # Filter to v2.8 only (has ema= field and 5m CHECK — long format files)
    v28_files = []
    for f in log_files:
        with open(f, 'r') as fh:
            content = fh.read()
        if 'ema=' in content and '5m CHECK' in content:
            v28_files.append(f)

    print(f"Found {len(v28_files)} v2.8 Pine log files (with evidence stack + 5m CHECK)")

    all_signals = []
    all_confs = []
    all_checks = []

    for fpath in v28_files:
        file_hash = os.path.basename(fpath).split('_')[-1].replace('.csv', '')
        df = pd.read_csv(fpath)

        for _, row in df.iterrows():
            msg = str(row.get('Message', ''))
            date_str = str(row.get('Date', ''))

            if '[KLB] CONF' in msg:
                conf = parse_conf(msg, date_str, file_hash)
                if conf:
                    all_confs.append(conf)
            elif '[KLB] 5m CHECK' in msg:
                check = parse_5m_check(msg, date_str, file_hash)
                if check:
                    all_checks.append(check)
            elif '[KLB]' in msg and ('BRK' in msg or '~ ~' in msg or '◆' in msg):
                sig = parse_signal(msg, date_str, file_hash)
                if sig:
                    all_signals.append(sig)

    signals_df = pd.DataFrame(all_signals)
    confs_df = pd.DataFrame(all_confs)
    checks_df = pd.DataFrame(all_checks)

    print(f"Parsed: {len(signals_df)} signals, {len(confs_df)} CONF events, {len(checks_df)} 5m checks")
    return signals_df, confs_df, checks_df, v28_files


def parse_signal(msg, date_str, file_hash):
    """Parse a BRK/REV/VWAP/Retest signal line."""
    try:
        # Skip retest lines (◆ without BRK or ~ ~)
        if '◆' in msg and 'BRK' not in msg and '~ ~' not in msg:
            # It's a retest — parse separately
            return parse_retest(msg, date_str, file_hash)

        # Time
        time_match = re.search(r'\[KLB\]\s+(\d+:\d+)', msg)
        if not time_match:
            return None
        time_str = time_match.group(1)

        # Direction
        direction = 'bull' if '▲' in msg else 'bear' if '▼' in msg else None

        # Signal type
        if 'BRK' in msg:
            sig_type = 'BRK'
        elif '~ ~ VWAP' in msg:
            sig_type = 'VWAP'
        elif '~ ~' in msg:
            sig_type = 'REV'
        else:
            return None

        # Levels
        levels_match = re.search(r'(?:BRK|~ ~)\s+(.*?)(?:\s+vol=)', msg)
        levels_str = levels_match.group(1).strip() if levels_match else ''

        # Volume
        vol_match = re.search(r'vol=(\d+\.?\d*)x', msg)
        vol = float(vol_match.group(1)) if vol_match else None

        # Close position
        pos_match = re.search(r'pos=[v^](\d+)', msg)
        close_pos = int(pos_match.group(1)) if pos_match else None

        # VWAP
        vwap_match = re.search(r'vwap=(above|below|na)', msg)
        vwap = vwap_match.group(1) if vwap_match else None

        # Evidence stack fields (v2.5+)
        ema_match = re.search(r'ema=(bull|bear|na)', msg)
        ema = ema_match.group(1) if ema_match else None

        rs_match = re.search(r'rs=([+-]?\d+\.?\d*)%', msg)
        rs = float(rs_match.group(1)) if rs_match else None

        adx_match = re.search(r'adx=(\d+)', msg)
        adx = int(adx_match.group(1)) if adx_match else None

        body_match = re.search(r'body=(\d+)%', msg)
        body = int(body_match.group(1)) if body_match else None

        # OHLC
        o_match = re.search(r'O([\d.]+)', msg)
        h_match = re.search(r'H([\d.]+)', msg)
        l_match = re.search(r'L([\d.]+)', msg)
        c_match = re.search(r'C([\d.]+)', msg)
        sig_o = float(o_match.group(1)) if o_match else None
        sig_h = float(h_match.group(1)) if h_match else None
        sig_l = float(l_match.group(1)) if l_match else None
        sig_c = float(c_match.group(1)) if c_match else None

        # ATR
        atr_match = re.search(r'ATR=([\d.]+)', msg)
        atr = float(atr_match.group(1)) if atr_match else None

        # SL levels
        sl_match = re.search(r'SL=([\d.]+)/([\d.]+)', msg)
        sl_warn = float(sl_match.group(1)) if sl_match else None
        sl_hard = float(sl_match.group(2)) if sl_match else None

        # Raw volume
        rawvol_match = re.search(r'rawVol=(\d+)', msg)
        raw_vol = int(rawvol_match.group(1)) if rawvol_match else None

        # Level prices
        prices_match = re.search(r'prices=(.*?)$', msg)
        prices = prices_match.group(1).strip() if prices_match else ''

        # Parse individual levels
        has_pmh = 'PM H' in levels_str
        has_pml = 'PM L' in levels_str
        has_yh = 'Yest H' in levels_str
        has_yl = 'Yest L' in levels_str
        has_wh = 'Week H' in levels_str
        has_wl = 'Week L' in levels_str
        has_oh = 'ORB H' in levels_str
        has_ol = 'ORB L' in levels_str
        has_vwap = 'VWAP' in levels_str or sig_type == 'VWAP'

        # Count levels
        level_count = sum([has_pmh, has_pml, has_yh, has_yl, has_wh, has_wl, has_oh, has_ol, has_vwap])

        # Is LOW level (bear advantage)
        is_low_level = has_pml or has_yl or has_wl or has_ol
        is_high_level = has_pmh or has_yh or has_wh or has_oh

        return {
            'file_hash': file_hash,
            'datetime': date_str,
            'time': time_str,
            'direction': direction,
            'type': sig_type,
            'levels': levels_str,
            'level_count': level_count,
            'is_low': is_low_level,
            'is_high': is_high_level,
            'vol': vol,
            'close_pos': close_pos,
            'vwap': vwap,
            'ema': ema,
            'rs': rs,
            'adx': adx,
            'body': body,
            'open': sig_o,
            'high': sig_h,
            'low': sig_l,
            'close': sig_c,
            'atr': atr,
            'sl_warn': sl_warn,
            'sl_hard': sl_hard,
            'raw_vol': raw_vol,
            'prices': prices,
        }
    except Exception as e:
        return None


def parse_retest(msg, date_str, file_hash):
    """Parse a retest ◆ signal."""
    time_match = re.search(r'\[KLB\]\s+(\d+:\d+)', msg)
    if not time_match:
        return None

    direction = 'bull' if '▲' in msg else 'bear' if '▼' in msg else None

    # Retest bar count
    bars_match = re.search(r'◆(\d+|¹|²|³|⁴|⁵|⁶|⁷|⁸|⁹)', msg)

    return {
        'file_hash': file_hash,
        'datetime': date_str,
        'time': time_match.group(1),
        'direction': direction,
        'type': 'RETEST',
        'levels': msg.split('◆')[1].split(' vol=')[0] if '◆' in msg else '',
        'level_count': 0,
        'is_low': False,
        'is_high': False,
        'vol': None,
        'close_pos': None,
        'vwap': None,
        'ema': None,
        'rs': None,
        'adx': None,
        'body': None,
        'open': None,
        'high': None,
        'low': None,
        'close': None,
        'atr': None,
        'sl_warn': None,
        'sl_hard': None,
        'raw_vol': None,
        'prices': '',
    }


def parse_conf(msg, date_str, file_hash):
    """Parse CONF line: ✓, ✓★, or ✗."""
    time_match = re.search(r'CONF\s+(\d+:\d+)', msg)
    if not time_match:
        return None
    direction = 'bull' if '▲' in msg else 'bear' if '▼' in msg else None

    if '✓★' in msg:
        result = 'star'
    elif '✓' in msg:
        result = 'pass'
    elif '✗' in msg:
        result = 'fail'
    else:
        result = 'unknown'

    return {
        'file_hash': file_hash,
        'datetime': date_str,
        'time': time_match.group(1),
        'direction': direction,
        'result': result,
    }


def parse_5m_check(msg, date_str, file_hash):
    """Parse 5m CHECK line."""
    time_match = re.search(r'5m CHECK\s+(\d+:\d+)', msg)
    pnl_match = re.search(r'pnl=([-\d.]+)', msg)
    verdict_match = re.search(r'→\s*(HOLD|BAIL)', msg)
    direction = 'bull' if '▲' in msg else 'bear' if '▼' in msg else None

    return {
        'file_hash': file_hash,
        'datetime': date_str,
        'time': time_match.group(1) if time_match else None,
        'direction': direction,
        'pnl': float(pnl_match.group(1)) if pnl_match else None,
        'verdict': verdict_match.group(1) if verdict_match else None,
    }


# ─── 2. Match Pine Logs to Symbols ──────────────────────────

def match_logs_to_symbols(signals_df):
    """Match Pine log files to symbols using first BRK signal close price vs BATS candle data."""
    # Load BATS candle data for reference
    bats_files = {}
    for f in glob.glob(str(DEBUG / "BATS_*, 1_*.csv")):
        sym_match = re.search(r'BATS_(\w+),', f)
        if sym_match:
            sym = sym_match.group(1)
            bats_files[sym] = f

    # For each file hash, get the first BRK signal's OHLC
    file_hashes = signals_df['file_hash'].unique()
    hash_to_symbol = {}

    for fh in file_hashes:
        file_sigs = signals_df[signals_df['file_hash'] == fh]
        brk_sigs = file_sigs[file_sigs['type'] == 'BRK']
        if len(brk_sigs) == 0:
            brk_sigs = file_sigs  # Use any signal

        if len(brk_sigs) == 0:
            continue

        first_sig = brk_sigs.iloc[0]
        sig_close = first_sig['close']
        sig_atr = first_sig['atr']
        sig_date = first_sig['datetime']

        if pd.isna(sig_close):
            continue

        # Match by looking for the closest price in BATS data on that date
        best_sym = None
        best_diff = float('inf')

        for sym, bats_path in bats_files.items():
            try:
                bats_df = pd.read_csv(bats_path, nrows=1000)
                # Parse the signal date
                sig_dt = pd.to_datetime(sig_date)
                sig_date_only = sig_dt.strftime('%Y-%m-%d')

                # Find candles on that date
                bats_df['time'] = pd.to_datetime(bats_df['time'])
                day_candles = bats_df[bats_df['time'].dt.strftime('%Y-%m-%d') == sig_date_only]

                if len(day_candles) == 0:
                    # Try first day in BATS data
                    first_day = bats_df['time'].dt.strftime('%Y-%m-%d').iloc[0]
                    day_candles = bats_df[bats_df['time'].dt.strftime('%Y-%m-%d') == first_day]

                if len(day_candles) > 0:
                    # Find closest close price
                    diff = abs(day_candles['close'] - sig_close).min()
                    if diff < best_diff:
                        best_diff = diff
                        best_sym = sym
            except Exception:
                continue

        if best_sym and best_diff < (sig_atr if sig_atr else 20):  # within 1 ATR
            hash_to_symbol[fh] = best_sym
        else:
            # Fallback: match by ATR magnitude
            atr_ranges = {
                'SPY': (3, 8), 'QQQ': (4, 9), 'AAPL': (4, 8), 'AMD': (8, 18),
                'AMZN': (12, 22), 'META': (7, 15), 'NVDA': (7, 15), 'TSLA': (12, 25),
                'GOOGL': (5, 10), 'MSFT': (5, 10), 'GLD': (3, 7), 'SLV': (2, 6), 'TSM': (4, 10)
            }
            if sig_atr:
                for sym, (low, high) in atr_ranges.items():
                    if low <= sig_atr <= high and abs(sig_close) > 50:
                        hash_to_symbol[fh] = sym
                        break

    return hash_to_symbol


# ─── 3. Load Parquet Data ─────────────────────────────────

def load_parquet_data(symbol, timeframe='5s'):
    """Load cached parquet data for a symbol."""
    sym_lower = symbol.lower()
    if timeframe == '5s':
        path = CACHE_5S / f"{sym_lower}_5_secs_ib.parquet"
    elif timeframe == '1m':
        path = CACHE_1M / f"{sym_lower}_1_min_ib.parquet"
    elif timeframe == '5m':
        path = CACHE_5M / f"{sym_lower}_5_mins_ib.parquet"
    else:
        return None

    if not path.exists():
        return None

    df = pd.read_parquet(path)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], utc=True)
        df = df.set_index('date').sort_index()
    return df


# ─── 4. Follow-Through Measurement ──────────────────────────

def measure_follow_through(signals_df, hash_to_symbol):
    """Measure MFE/MAE using 1m data (more reliable alignment than 5s)."""
    results = []

    for symbol in SYMBOLS:
        # Get file hashes for this symbol
        sym_hashes = [h for h, s in hash_to_symbol.items() if s == symbol]
        if not sym_hashes:
            continue

        sym_signals = signals_df[
            (signals_df['file_hash'].isin(sym_hashes)) &
            (signals_df['type'].isin(['BRK', 'REV', 'VWAP']))
        ].copy()

        if len(sym_signals) == 0:
            continue

        # Load 1m data
        df_1m = load_parquet_data(symbol, '1m')
        if df_1m is None:
            continue

        for _, sig in sym_signals.iterrows():
            try:
                sig_dt = pd.to_datetime(sig['datetime'], utc=True)
                entry_price = sig['close']
                atr = sig['atr']
                direction = sig['direction']

                if pd.isna(entry_price) or pd.isna(atr) or atr == 0:
                    continue

                # Find bars after signal
                future = df_1m[df_1m.index > sig_dt].head(60)  # 60 min window

                if len(future) < 5:
                    continue

                for window in [5, 15, 30, 60]:
                    window_bars = future.head(window)
                    if len(window_bars) == 0:
                        continue

                    if direction == 'bull':
                        mfe = (window_bars['high'].max() - entry_price) / atr
                        mae = (entry_price - window_bars['low'].min()) / atr
                    else:
                        mfe = (entry_price - window_bars['low'].min()) / atr
                        mae = (window_bars['high'].max() - entry_price) / atr

                    results.append({
                        'symbol': symbol,
                        'datetime': sig['datetime'],
                        'time': sig['time'],
                        'type': sig['type'],
                        'direction': direction,
                        'levels': sig['levels'],
                        'vol': sig['vol'],
                        'ema': sig['ema'],
                        'vwap': sig['vwap'],
                        'adx': sig['adx'],
                        'body': sig['body'],
                        'atr': atr,
                        'entry': entry_price,
                        'window_min': window,
                        'mfe_atr': round(mfe, 4),
                        'mae_atr': round(mae, 4),
                        'mfe_mae_ratio': round(mfe / mae, 2) if mae > 0.001 else 99.9,
                    })
            except Exception:
                continue

    return pd.DataFrame(results)


# ─── 5. QBS/MC Reconstruction ────────────────────────────────

def reconstruct_qbs_mc(symbol, df_5m, signals_df, hash_to_symbol):
    """Reconstruct QBS/MC conditions from 5m data to check if they fire correctly."""
    # QBS: vol drying (<0.5x recent avg) + range >= 1.5x ATR
    # MC: vol explosive (>5x recent avg) + range >= 1.5x ATR

    if df_5m is None or len(df_5m) < 30:
        return []

    df = df_5m.copy()
    df['vol_sma20'] = df['volume'].rolling(20).mean()
    df['vol_ratio'] = df['volume'] / df['vol_sma20']
    df['range'] = df['high'] - df['low']
    df['atr14'] = df['range'].rolling(14).mean()
    df['range_atr'] = df['range'] / df['atr14']
    df['body'] = abs(df['close'] - df['open'])
    df['body_ratio'] = df['body'] / df['range'].replace(0, np.nan)

    # Pre-move volume ramp: average of vol_ratio for bars -4 to -1
    df['pre_vol_1'] = df['vol_ratio'].shift(1)
    df['pre_vol_2'] = df['vol_ratio'].shift(2)
    df['pre_vol_3'] = df['vol_ratio'].shift(3)
    df['pre_vol_4'] = df['vol_ratio'].shift(4)
    df['pre_vol_avg'] = (df['pre_vol_1'] + df['pre_vol_2'] + df['pre_vol_3'] + df['pre_vol_4']) / 4

    # QBS condition: pre_vol_avg < 0.5 (drying) + current range >= 1.5 ATR
    df['is_qbs'] = (df['pre_vol_avg'] < 0.5) & (df['range_atr'] >= 1.5)
    # MC condition: vol_ratio > 5 (explosive) + range >= 1.5 ATR
    df['is_mc'] = (df['vol_ratio'] > 5) & (df['range_atr'] >= 1.5)

    # Direction
    df['is_bull'] = df['close'] > df['open']

    # Filter to market hours (roughly 9:30-16:00 ET)
    if hasattr(df.index, 'hour'):
        df = df[(df.index.hour >= 9) & (df.index.hour < 16)]

    qbs_mc_events = []
    for idx, row in df.iterrows():
        if row['is_qbs'] or row['is_mc']:
            qbs_mc_events.append({
                'symbol': symbol,
                'datetime': str(idx),
                'type': 'QBS' if row['is_qbs'] else 'MC',
                'direction': 'bull' if row['is_bull'] else 'bear',
                'vol_ratio': round(row['vol_ratio'], 2),
                'pre_vol_avg': round(row['pre_vol_avg'], 2),
                'range_atr': round(row['range_atr'], 2),
                'close': row['close'],
                'open': row['open'],
            })

    return qbs_mc_events


# ─── 6. Trade Simulation ────────────────────────────────────

def simulate_trades(signals_df, confs_df, hash_to_symbol):
    """Simulate entry/exit for CONF ✓/✓★ signals."""
    trades = []

    for symbol in SYMBOLS:
        sym_hashes = [h for h, s in hash_to_symbol.items() if s == symbol]
        if not sym_hashes:
            continue

        sym_confs = confs_df[
            (confs_df['file_hash'].isin(sym_hashes)) &
            (confs_df['result'].isin(['pass', 'star']))
        ]

        if len(sym_confs) == 0:
            continue

        # Load 1m data for simulation
        df_1m = load_parquet_data(symbol, '1m')
        if df_1m is None:
            continue

        # Find the BRK signal that each CONF corresponds to
        sym_signals = signals_df[
            (signals_df['file_hash'].isin(sym_hashes)) &
            (signals_df['type'] == 'BRK')
        ]

        for _, conf in sym_confs.iterrows():
            try:
                conf_dt = pd.to_datetime(conf['datetime'], utc=True)
                conf_date = conf_dt.strftime('%Y-%m-%d')

                # Find the most recent BRK signal before this CONF (same day, same direction)
                day_brks = sym_signals[
                    (sym_signals['datetime'].apply(lambda x: pd.to_datetime(x, utc=True).strftime('%Y-%m-%d')) == conf_date) &
                    (sym_signals['direction'] == conf['direction'])
                ]

                if len(day_brks) == 0:
                    continue

                # Get the last BRK before CONF
                brk = day_brks.iloc[-1]
                entry_price = brk['close']
                atr = brk['atr']
                direction = brk['direction']

                if pd.isna(entry_price) or pd.isna(atr) or atr == 0:
                    continue

                # Simulate: entry at signal close
                # SL: 0.15 ATR (hard stop)
                # TP: trailing stop 0.25 ATR from high after +0.05 ATR
                # Max hold: 30 minutes

                sig_dt = pd.to_datetime(brk['datetime'], utc=True)
                future = df_1m[df_1m.index > sig_dt].head(30)

                if len(future) < 2:
                    continue

                sl_dist = 0.15 * atr
                trail_dist = 0.25 * atr
                trail_start = 0.05 * atr

                exit_price = None
                exit_reason = 'timeout'
                exit_bar = len(future)
                max_favorable = 0
                trailing_active = False
                trail_stop = None

                for i, (bar_dt, bar) in enumerate(future.iterrows()):
                    if direction == 'bull':
                        pnl = bar['high'] - entry_price
                        adverse = entry_price - bar['low']

                        max_favorable = max(max_favorable, pnl)

                        # Check hard stop
                        if adverse >= sl_dist:
                            exit_price = entry_price - sl_dist
                            exit_reason = 'stop_loss'
                            exit_bar = i + 1
                            break

                        # Activate trailing after +0.05 ATR
                        if pnl >= trail_start:
                            trailing_active = True
                            new_trail = bar['high'] - trail_dist
                            if trail_stop is None or new_trail > trail_stop:
                                trail_stop = new_trail

                        # Check trailing stop
                        if trailing_active and trail_stop and bar['low'] <= trail_stop:
                            exit_price = trail_stop
                            exit_reason = 'trailing_stop'
                            exit_bar = i + 1
                            break
                    else:  # bear
                        pnl = entry_price - bar['low']
                        adverse = bar['high'] - entry_price

                        max_favorable = max(max_favorable, pnl)

                        if adverse >= sl_dist:
                            exit_price = entry_price + sl_dist
                            exit_reason = 'stop_loss'
                            exit_bar = i + 1
                            break

                        if pnl >= trail_start:
                            trailing_active = True
                            new_trail = bar['low'] + trail_dist
                            if trail_stop is None or new_trail < trail_stop:
                                trail_stop = new_trail

                        if trailing_active and trail_stop and bar['high'] >= trail_stop:
                            exit_price = trail_stop
                            exit_reason = 'trailing_stop'
                            exit_bar = i + 1
                            break

                if exit_price is None:
                    # Timeout: exit at last bar close
                    exit_price = future.iloc[-1]['close']

                if direction == 'bull':
                    trade_pnl = exit_price - entry_price
                else:
                    trade_pnl = entry_price - exit_price

                trade_pnl_atr = trade_pnl / atr

                trades.append({
                    'symbol': symbol,
                    'signal_time': brk['datetime'],
                    'conf_time': conf['datetime'],
                    'conf_result': conf['result'],
                    'direction': direction,
                    'type': brk['type'],
                    'levels': brk['levels'],
                    'entry': entry_price,
                    'exit': round(exit_price, 2),
                    'pnl': round(trade_pnl, 2),
                    'pnl_atr': round(trade_pnl_atr, 4),
                    'mfe_atr': round(max_favorable / atr, 4),
                    'exit_reason': exit_reason,
                    'exit_bar': exit_bar,
                    'atr': atr,
                    'vol': brk['vol'],
                    'ema': brk['ema'],
                    'vwap': brk['vwap'],
                    'time': brk['time'],
                })
            except Exception:
                continue

    return pd.DataFrame(trades)


# ─── 7. Missed Signal Detection ─────────────────────────────

def find_missed_signals(symbol, df_5m, signals_df, hash_to_symbol):
    """Find 5m bars with range >= 1x ATR that had no signal within ±2 bars."""
    if df_5m is None or len(df_5m) < 20:
        return []

    df = df_5m.copy()
    df['range'] = df['high'] - df['low']
    df['atr14'] = df['range'].rolling(14).mean()
    df['range_atr'] = df['range'] / df['atr14']
    df['body'] = abs(df['close'] - df['open'])
    df['direction'] = np.where(df['close'] > df['open'], 'bull', 'bear')

    # Filter to market hours
    if hasattr(df.index, 'hour'):
        market = df[(df.index.hour >= 9) & (df.index.hour < 16)].copy()
    else:
        market = df.copy()

    # Get signal times for this symbol
    sym_hashes = [h for h, s in hash_to_symbol.items() if s == symbol]
    sym_signals = signals_df[signals_df['file_hash'].isin(sym_hashes)]
    signal_times = set()
    for _, sig in sym_signals.iterrows():
        try:
            sig_dt = pd.to_datetime(sig['datetime'], utc=True)
            # Add ±10 min window
            for offset_min in range(-10, 11):
                signal_times.add((sig_dt + timedelta(minutes=offset_min)).strftime('%Y-%m-%d %H:%M'))
        except:
            pass

    # Find big moves without signals
    missed = []
    big_moves = market[market['range_atr'] >= 1.0]

    for idx, row in big_moves.iterrows():
        bar_time = idx.strftime('%Y-%m-%d %H:%M')
        if bar_time not in signal_times:
            missed.append({
                'symbol': symbol,
                'datetime': str(idx),
                'range_atr': round(row['range_atr'], 2),
                'direction': row['direction'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume'],
                'atr14': round(row['atr14'], 2) if not pd.isna(row['atr14']) else None,
            })

    return missed


# ─── 8. Find Consecutive Missed Moves ───────────────────────

def find_missed_runs(symbol, df_5m, signals_df, hash_to_symbol):
    """Find stretches of directional movement (>1 ATR cumulative) without any signal."""
    if df_5m is None or len(df_5m) < 20:
        return []

    df = df_5m.copy()
    df['range'] = df['high'] - df['low']
    df['atr14'] = df['range'].rolling(14).mean()

    # Filter to market hours
    if hasattr(df.index, 'hour'):
        market = df[(df.index.hour >= 9) & (df.index.hour < 16)].copy()
    else:
        market = df.copy()

    # Get signal times
    sym_hashes = [h for h, s in hash_to_symbol.items() if s == symbol]
    sym_signals = signals_df[signals_df['file_hash'].isin(sym_hashes)]

    # Group by date
    if not hasattr(market.index, 'date'):
        return []

    runs = []
    for date, day_df in market.groupby(market.index.date):
        if len(day_df) < 5:
            continue

        # Find signal bars for this day
        day_str = str(date)
        day_signals = sym_signals[
            sym_signals['datetime'].str.startswith(day_str)
        ]
        signal_minutes = set()
        for _, sig in day_signals.iterrows():
            try:
                sig_dt = pd.to_datetime(sig['datetime'], utc=True)
                signal_minutes.add(sig_dt.strftime('%H:%M'))
            except:
                pass

        # Scan for runs of bars without signals that have significant cumulative move
        atr = day_df['atr14'].dropna().mean()
        if pd.isna(atr) or atr == 0:
            continue

        run_start = None
        run_high = None
        run_low = None
        no_signal_count = 0

        for idx, row in day_df.iterrows():
            bar_time = idx.strftime('%H:%M')
            has_signal = bar_time in signal_minutes

            if has_signal:
                # Check if we had a run worth recording
                if run_start is not None and no_signal_count >= 3:
                    run_range = (run_high - run_low) / atr
                    if run_range >= 1.0:
                        runs.append({
                            'symbol': symbol,
                            'date': day_str,
                            'start_time': run_start.strftime('%H:%M'),
                            'end_time': idx.strftime('%H:%M'),
                            'bars': no_signal_count,
                            'high': run_high,
                            'low': run_low,
                            'range_atr': round(run_range, 2),
                            'atr': round(atr, 2),
                        })
                run_start = None
                run_high = None
                run_low = None
                no_signal_count = 0
            else:
                if run_start is None:
                    run_start = idx
                    run_high = row['high']
                    run_low = row['low']
                else:
                    run_high = max(run_high, row['high'])
                    run_low = min(run_low, row['low'])
                no_signal_count += 1

        # Check final run
        if run_start is not None and no_signal_count >= 3:
            run_range = (run_high - run_low) / atr
            if run_range >= 1.0:
                runs.append({
                    'symbol': symbol,
                    'date': day_str,
                    'start_time': run_start.strftime('%H:%M'),
                    'end_time': day_df.index[-1].strftime('%H:%M'),
                    'bars': no_signal_count,
                    'high': run_high,
                    'low': run_low,
                    'range_atr': round(run_range, 2),
                    'atr': round(atr, 2),
                })

    return runs


# ─── MAIN ────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("v2.8 Signal Audit")
    print("=" * 60)

    # 1. Parse Pine logs
    print("\n[1/6] Parsing Pine logs...")
    signals_df, confs_df, checks_df, v28_files = parse_pine_logs()

    # 2. Match to symbols
    print("\n[2/6] Matching Pine logs to symbols...")
    hash_to_symbol = match_logs_to_symbols(signals_df)
    print("Symbol mapping:")
    for h, s in sorted(hash_to_symbol.items(), key=lambda x: x[1]):
        n_sigs = len(signals_df[signals_df['file_hash'] == h])
        print(f"  {h} → {s} ({n_sigs} signals)")

    # Add symbol column to signals
    signals_df['symbol'] = signals_df['file_hash'].map(hash_to_symbol)
    confs_df['symbol'] = confs_df['file_hash'].map(hash_to_symbol)
    checks_df['symbol'] = checks_df['file_hash'].map(hash_to_symbol)

    # 3. Follow-through measurement
    print("\n[3/6] Measuring follow-through (MFE/MAE)...")
    ft_df = measure_follow_through(signals_df, hash_to_symbol)
    print(f"  Measured {len(ft_df)} signal-window combinations")

    # 4. QBS/MC reconstruction
    print("\n[4/6] Reconstructing QBS/MC signals...")
    all_qbs_mc = []
    for sym in SYMBOLS:
        df_5m = load_parquet_data(sym, '5m')
        if df_5m is not None:
            events = reconstruct_qbs_mc(sym, df_5m, signals_df, hash_to_symbol)
            all_qbs_mc.extend(events)
    qbs_mc_df = pd.DataFrame(all_qbs_mc)
    print(f"  Found {len(qbs_mc_df)} QBS/MC events across all symbols")

    # Focus on SPY, QQQ, AMD, AAPL near market open
    if len(qbs_mc_df) > 0:
        focus_syms = ['SPY', 'QQQ', 'AMD', 'AAPL']
        focus = qbs_mc_df[qbs_mc_df['symbol'].isin(focus_syms)].copy()
        focus['hour'] = pd.to_datetime(focus['datetime']).dt.hour
        open_mc = focus[(focus['hour'] >= 9) & (focus['hour'] < 10) & (focus['type'] == 'MC')]
        print(f"  MC signals near open (9:xx) for SPY/QQQ/AMD/AAPL: {len(open_mc)}")

    # 5. Trade simulation
    print("\n[5/6] Simulating trades for CONF ✓/✓★...")
    trades_df = simulate_trades(signals_df, confs_df, hash_to_symbol)
    print(f"  Simulated {len(trades_df)} trades")

    # 6. Missed signals
    print("\n[6/6] Scanning for missed signals...")
    all_missed = []
    all_runs = []
    for sym in SYMBOLS:
        df_5m = load_parquet_data(sym, '5m')
        if df_5m is not None:
            missed = find_missed_signals(sym, df_5m, signals_df, hash_to_symbol)
            all_missed.extend(missed)
            runs = find_missed_runs(sym, df_5m, signals_df, hash_to_symbol)
            all_runs.extend(runs)
    missed_df = pd.DataFrame(all_missed)
    runs_df = pd.DataFrame(all_runs)
    print(f"  Found {len(missed_df)} missed big bars, {len(runs_df)} missed runs (>1 ATR)")

    # ─── Save All Data ───────────────────────────────────
    print("\n" + "=" * 60)
    print("Saving results...")

    signals_df.to_csv(DEBUG / "v28-signals-parsed.csv", index=False)
    confs_df.to_csv(DEBUG / "v28-confs-parsed.csv", index=False)
    checks_df.to_csv(DEBUG / "v28-checks-parsed.csv", index=False)
    ft_df.to_csv(DEBUG / "v28-follow-through.csv", index=False)
    if len(qbs_mc_df) > 0:
        qbs_mc_df.to_csv(DEBUG / "v28-qbs-mc-reconstructed.csv", index=False)
    trades_df.to_csv(DEBUG / "v28-trade-simulation.csv", index=False)
    if len(missed_df) > 0:
        missed_df.to_csv(DEBUG / "v28-missed-signals.csv", index=False)
    if len(runs_df) > 0:
        runs_df.to_csv(DEBUG / "v28-missed-runs.csv", index=False)

    # ─── Generate Report ────────────────────────────────
    report = generate_report(signals_df, confs_df, checks_df, ft_df, qbs_mc_df, trades_df, missed_df, runs_df, hash_to_symbol)

    with open(OUTPUT_FILE, 'w') as f:
        f.write(report)

    print(f"\nReport saved to: {OUTPUT_FILE}")
    print(f"CSV data saved to: debug/v28-*.csv")
    print("Done!")


def generate_report(signals_df, confs_df, checks_df, ft_df, qbs_mc_df, trades_df, missed_df, runs_df, hash_to_symbol):
    """Generate comprehensive markdown report."""
    lines = ["# v2.8 Signal Audit Report\n"]
    lines.append(f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append(f"> Data: {len(signals_df)} signals, {len(confs_df)} CONF events, {len(set(hash_to_symbol.values()))} symbols\n")

    # ─── Section 1: Signal Overview ─────────────────────
    lines.append("## 1. Signal Overview\n")

    if len(signals_df) > 0 and 'symbol' in signals_df.columns:
        # By symbol
        sym_counts = signals_df.groupby(['symbol', 'type']).size().unstack(fill_value=0)
        lines.append("### Signals by Symbol\n")
        lines.append("| Symbol | BRK | REV | VWAP | RETEST | Total |")
        lines.append("|--------|-----|-----|------|--------|-------|")
        for sym in SYMBOLS:
            if sym in sym_counts.index:
                row = sym_counts.loc[sym]
                total = row.sum()
                lines.append(f"| {sym} | {row.get('BRK', 0)} | {row.get('REV', 0)} | {row.get('VWAP', 0)} | {row.get('RETEST', 0)} | {total} |")
        lines.append("")

        # By time
        signals_df['hour'] = signals_df['time'].apply(lambda x: int(x.split(':')[0]) if pd.notna(x) and ':' in str(x) else None)
        time_counts = signals_df.groupby('hour').size()
        lines.append("### Signals by Hour\n")
        lines.append("| Hour | Count | % |")
        lines.append("|------|-------|---|")
        total = len(signals_df)
        for h in sorted(time_counts.index):
            if h is not None:
                n = time_counts[h]
                lines.append(f"| {int(h)}:xx | {n} | {n/total*100:.0f}% |")
        lines.append("")

    # ─── Section 2: CONF Analysis ────────────────────────
    lines.append("## 2. Confirmation Analysis\n")

    if len(confs_df) > 0:
        conf_counts = confs_df['result'].value_counts()
        total_conf = len(confs_df)
        lines.append(f"- Total CONF events: {total_conf}")
        for result, count in conf_counts.items():
            pct = count / total_conf * 100
            label = {'pass': '✓', 'star': '✓★', 'fail': '✗'}.get(result, result)
            lines.append(f"- {label}: {count} ({pct:.0f}%)")
        lines.append("")

        # CONF by symbol
        if 'symbol' in confs_df.columns:
            lines.append("### CONF Rate by Symbol\n")
            lines.append("| Symbol | ✓★ | ✓ | ✗ | Total | Pass% |")
            lines.append("|--------|-----|---|---|-------|-------|")
            for sym in SYMBOLS:
                sym_confs = confs_df[confs_df['symbol'] == sym]
                if len(sym_confs) > 0:
                    star = len(sym_confs[sym_confs['result'] == 'star'])
                    passed = len(sym_confs[sym_confs['result'] == 'pass'])
                    failed = len(sym_confs[sym_confs['result'] == 'fail'])
                    total = len(sym_confs)
                    pass_pct = (star + passed) / total * 100
                    lines.append(f"| {sym} | {star} | {passed} | {failed} | {total} | {pass_pct:.0f}% |")
            lines.append("")

    # ─── Section 3: 5m Check Analysis ────────────────────
    lines.append("## 3. Five-Minute Checkpoint\n")

    if len(checks_df) > 0:
        hold = len(checks_df[checks_df['verdict'] == 'HOLD'])
        bail = len(checks_df[checks_df['verdict'] == 'BAIL'])
        total = hold + bail
        lines.append(f"- HOLD: {hold} ({hold/total*100:.0f}%)")
        lines.append(f"- BAIL: {bail} ({bail/total*100:.0f}%)")

        if 'pnl' in checks_df.columns:
            avg_pnl_hold = checks_df[checks_df['verdict'] == 'HOLD']['pnl'].mean()
            avg_pnl_bail = checks_df[checks_df['verdict'] == 'BAIL']['pnl'].mean()
            lines.append(f"- Avg P&L at 5m (HOLD): {avg_pnl_hold:.3f} ATR")
            lines.append(f"- Avg P&L at 5m (BAIL): {avg_pnl_bail:.3f} ATR")
        lines.append("")

    # ─── Section 4: Follow-Through ──────────────────────
    lines.append("## 4. Follow-Through (MFE/MAE)\n")

    if len(ft_df) > 0:
        # By window
        lines.append("### Average MFE/MAE by Window\n")
        lines.append("| Window | Avg MFE | Avg MAE | MFE/MAE | Win% (MFE>MAE) |")
        lines.append("|--------|---------|---------|---------|-----------------|")
        for window in [5, 15, 30, 60]:
            w_data = ft_df[ft_df['window_min'] == window]
            if len(w_data) > 0:
                avg_mfe = w_data['mfe_atr'].mean()
                avg_mae = w_data['mae_atr'].mean()
                ratio = avg_mfe / avg_mae if avg_mae > 0 else 99.9
                win_pct = (w_data['mfe_atr'] > w_data['mae_atr']).mean() * 100
                lines.append(f"| {window}m | {avg_mfe:.3f} | {avg_mae:.3f} | {ratio:.2f} | {win_pct:.0f}% |")
        lines.append("")

        # By signal type at 30m window
        ft_30 = ft_df[ft_df['window_min'] == 30]
        if len(ft_30) > 0:
            lines.append("### 30m Follow-Through by Signal Type\n")
            lines.append("| Type | N | Avg MFE | Avg MAE | MFE/MAE | Win% |")
            lines.append("|------|---|---------|---------|---------|------|")
            for sig_type in ['BRK', 'REV', 'VWAP']:
                t_data = ft_30[ft_30['type'] == sig_type]
                if len(t_data) > 0:
                    avg_mfe = t_data['mfe_atr'].mean()
                    avg_mae = t_data['mae_atr'].mean()
                    ratio = avg_mfe / avg_mae if avg_mae > 0 else 99.9
                    win_pct = (t_data['mfe_atr'] > t_data['mae_atr']).mean() * 100
                    lines.append(f"| {sig_type} | {len(t_data)} | {avg_mfe:.3f} | {avg_mae:.3f} | {ratio:.2f} | {win_pct:.0f}% |")
            lines.append("")

            # By symbol at 30m
            lines.append("### 30m Follow-Through by Symbol\n")
            lines.append("| Symbol | N | Avg MFE | Avg MAE | MFE/MAE | Win% |")
            lines.append("|--------|---|---------|---------|---------|------|")
            for sym in SYMBOLS:
                s_data = ft_30[ft_30['symbol'] == sym]
                if len(s_data) > 0:
                    avg_mfe = s_data['mfe_atr'].mean()
                    avg_mae = s_data['mae_atr'].mean()
                    ratio = avg_mfe / avg_mae if avg_mae > 0 else 99.9
                    win_pct = (s_data['mfe_atr'] > s_data['mae_atr']).mean() * 100
                    lines.append(f"| {sym} | {len(s_data)} | {avg_mfe:.3f} | {avg_mae:.3f} | {ratio:.2f} | {win_pct:.0f}% |")
            lines.append("")

            # By evidence stack filters at 30m
            lines.append("### 30m Follow-Through by Evidence Stack\n")

            # EMA aligned vs not
            brk_30 = ft_30[ft_30['type'] == 'BRK']
            if len(brk_30) > 0:
                ema_aligned = brk_30[
                    ((brk_30['direction'] == 'bull') & (brk_30['ema'] == 'bull')) |
                    ((brk_30['direction'] == 'bear') & (brk_30['ema'] == 'bear'))
                ]
                ema_counter = brk_30[
                    ((brk_30['direction'] == 'bull') & (brk_30['ema'] == 'bear')) |
                    ((brk_30['direction'] == 'bear') & (brk_30['ema'] == 'bull'))
                ]

                lines.append("| Filter | N | Avg MFE | Win% |")
                lines.append("|--------|---|---------|------|")
                if len(ema_aligned) > 0:
                    lines.append(f"| EMA aligned | {len(ema_aligned)} | {ema_aligned['mfe_atr'].mean():.3f} | {(ema_aligned['mfe_atr'] > ema_aligned['mae_atr']).mean()*100:.0f}% |")
                if len(ema_counter) > 0:
                    lines.append(f"| EMA counter | {len(ema_counter)} | {ema_counter['mfe_atr'].mean():.3f} | {(ema_counter['mfe_atr'] > ema_counter['mae_atr']).mean()*100:.0f}% |")

                # VWAP aligned
                vwap_aligned = brk_30[
                    ((brk_30['direction'] == 'bull') & (brk_30['vwap'] == 'above')) |
                    ((brk_30['direction'] == 'bear') & (brk_30['vwap'] == 'below'))
                ]
                vwap_counter = brk_30[
                    ((brk_30['direction'] == 'bull') & (brk_30['vwap'] == 'below')) |
                    ((brk_30['direction'] == 'bear') & (brk_30['vwap'] == 'above'))
                ]
                if len(vwap_aligned) > 0:
                    lines.append(f"| VWAP aligned | {len(vwap_aligned)} | {vwap_aligned['mfe_atr'].mean():.3f} | {(vwap_aligned['mfe_atr'] > vwap_aligned['mae_atr']).mean()*100:.0f}% |")
                if len(vwap_counter) > 0:
                    lines.append(f"| VWAP counter | {len(vwap_counter)} | {vwap_counter['mfe_atr'].mean():.3f} | {(vwap_counter['mfe_atr'] > vwap_counter['mae_atr']).mean()*100:.0f}% |")

                # Volume buckets
                for vol_label, vol_min, vol_max in [('Vol <2x', 0, 2), ('Vol 2-5x', 2, 5), ('Vol 5-10x', 5, 10), ('Vol 10x+', 10, 999)]:
                    v_data = brk_30[(brk_30['vol'] >= vol_min) & (brk_30['vol'] < vol_max)]
                    if len(v_data) > 0:
                        lines.append(f"| {vol_label} | {len(v_data)} | {v_data['mfe_atr'].mean():.3f} | {(v_data['mfe_atr'] > v_data['mae_atr']).mean()*100:.0f}% |")

                lines.append("")

    # ─── Section 5: QBS/MC Analysis ─────────────────────
    lines.append("## 5. QBS/MC Signal Analysis\n")

    if len(qbs_mc_df) > 0:
        # Overall counts
        qbs_count = len(qbs_mc_df[qbs_mc_df['type'] == 'QBS'])
        mc_count = len(qbs_mc_df[qbs_mc_df['type'] == 'MC'])
        lines.append(f"- Reconstructed QBS events: {qbs_count}")
        lines.append(f"- Reconstructed MC events: {mc_count}")
        lines.append("")

        # SPY/QQQ/AMD/AAPL near open
        focus_syms = ['SPY', 'QQQ', 'AMD', 'AAPL']
        lines.append("### MC Signals Near Market Open (SPY/QQQ/AMD/AAPL)\n")

        focus = qbs_mc_df[qbs_mc_df['symbol'].isin(focus_syms)].copy()
        if len(focus) > 0:
            focus['dt'] = pd.to_datetime(focus['datetime'])
            focus['hour'] = focus['dt'].dt.hour
            focus['minute'] = focus['dt'].dt.minute
            focus['date'] = focus['dt'].dt.date

            open_events = focus[(focus['hour'] == 9) & (focus['minute'] <= 45)]

            if len(open_events) > 0:
                lines.append("| Symbol | Date | Time | Type | Dir | Vol Ratio | Pre-Vol | Range/ATR |")
                lines.append("|--------|------|------|------|-----|-----------|---------|-----------|")
                for _, ev in open_events.sort_values('datetime').iterrows():
                    t = ev['dt'].strftime('%H:%M')
                    lines.append(f"| {ev['symbol']} | {ev['date']} | {t} | {ev['type']} | {ev['direction']} | {ev['vol_ratio']} | {ev['pre_vol_avg']} | {ev['range_atr']} |")
                lines.append("")

                # Check for opposing pairs
                lines.append("### Opposing MC Pairs at Open\n")
                for sym in focus_syms:
                    sym_open = open_events[open_events['symbol'] == sym]
                    for date in sym_open['date'].unique():
                        day_events = sym_open[sym_open['date'] == date]
                        if len(day_events) > 1:
                            dirs = day_events['direction'].unique()
                            if 'bull' in dirs and 'bear' in dirs:
                                lines.append(f"**{sym} {date}**: Both bull AND bear MC at open!")
                                for _, ev in day_events.iterrows():
                                    lines.append(f"  - {ev['dt'].strftime('%H:%M')} {ev['type']} {ev['direction']} vol={ev['vol_ratio']}x range={ev['range_atr']}x ATR")
                                lines.append("")
            else:
                lines.append("No MC events found near open for these symbols.\n")
        else:
            lines.append("No QBS/MC events for SPY/QQQ/AMD/AAPL.\n")
    else:
        lines.append("No QBS/MC events reconstructed.\n")

    # ─── Section 6: Trade Simulation ────────────────────
    lines.append("## 6. Trade Simulation (CONF ✓/✓★)\n")

    if len(trades_df) > 0:
        total_pnl = trades_df['pnl_atr'].sum()
        avg_pnl = trades_df['pnl_atr'].mean()
        win_rate = (trades_df['pnl_atr'] > 0).mean() * 100
        avg_winner = trades_df[trades_df['pnl_atr'] > 0]['pnl_atr'].mean() if (trades_df['pnl_atr'] > 0).any() else 0
        avg_loser = trades_df[trades_df['pnl_atr'] <= 0]['pnl_atr'].mean() if (trades_df['pnl_atr'] <= 0).any() else 0

        lines.append(f"- **Total trades:** {len(trades_df)}")
        lines.append(f"- **Win rate:** {win_rate:.0f}%")
        lines.append(f"- **Total P&L:** {total_pnl:.2f} ATR")
        lines.append(f"- **Avg P&L/trade:** {avg_pnl:.3f} ATR")
        lines.append(f"- **Avg winner:** +{avg_winner:.3f} ATR")
        lines.append(f"- **Avg loser:** {avg_loser:.3f} ATR")
        lines.append("")

        # By exit reason
        lines.append("### Exit Reasons\n")
        lines.append("| Reason | Count | Avg P&L (ATR) | Win% |")
        lines.append("|--------|-------|---------------|------|")
        for reason in ['trailing_stop', 'stop_loss', 'timeout']:
            r_data = trades_df[trades_df['exit_reason'] == reason]
            if len(r_data) > 0:
                lines.append(f"| {reason} | {len(r_data)} | {r_data['pnl_atr'].mean():.3f} | {(r_data['pnl_atr'] > 0).mean()*100:.0f}% |")
        lines.append("")

        # By CONF type
        lines.append("### By CONF Type\n")
        lines.append("| Type | Trades | Win% | Avg P&L | Total P&L |")
        lines.append("|------|--------|------|---------|-----------|")
        for conf_type in ['star', 'pass']:
            c_data = trades_df[trades_df['conf_result'] == conf_type]
            if len(c_data) > 0:
                label = '✓★' if conf_type == 'star' else '✓'
                lines.append(f"| {label} | {len(c_data)} | {(c_data['pnl_atr'] > 0).mean()*100:.0f}% | {c_data['pnl_atr'].mean():.3f} | {c_data['pnl_atr'].sum():.2f} |")
        lines.append("")

        # By symbol
        lines.append("### By Symbol\n")
        lines.append("| Symbol | Trades | Win% | Avg P&L | Total P&L |")
        lines.append("|--------|--------|------|---------|-----------|")
        for sym in SYMBOLS:
            s_data = trades_df[trades_df['symbol'] == sym]
            if len(s_data) > 0:
                lines.append(f"| {sym} | {len(s_data)} | {(s_data['pnl_atr'] > 0).mean()*100:.0f}% | {s_data['pnl_atr'].mean():.3f} | {s_data['pnl_atr'].sum():.2f} |")
        lines.append("")

        # By time
        lines.append("### By Hour\n")
        lines.append("| Hour | Trades | Win% | Avg P&L |")
        lines.append("|------|--------|------|---------|")
        trades_df['hour'] = trades_df['time'].apply(lambda x: int(x.split(':')[0]) if pd.notna(x) and ':' in str(x) else None)
        for h in sorted(trades_df['hour'].dropna().unique()):
            h_data = trades_df[trades_df['hour'] == h]
            if len(h_data) > 0:
                lines.append(f"| {int(h)}:xx | {len(h_data)} | {(h_data['pnl_atr'] > 0).mean()*100:.0f}% | {h_data['pnl_atr'].mean():.3f} |")
        lines.append("")

    # ─── Section 7: Missed Signals ──────────────────────
    lines.append("## 7. Missed Signals\n")

    if len(runs_df) > 0:
        lines.append(f"Found **{len(runs_df)}** stretches of ≥1 ATR movement without any signal.\n")

        # Top missed runs by range
        lines.append("### Top 30 Missed Runs (sorted by range)\n")
        lines.append("| Symbol | Date | Start | End | Bars | Range (ATR) |")
        lines.append("|--------|------|-------|-----|------|-------------|")
        top_runs = runs_df.nlargest(30, 'range_atr')
        for _, run in top_runs.iterrows():
            lines.append(f"| {run['symbol']} | {run['date']} | {run['start_time']} | {run['end_time']} | {run['bars']} | {run['range_atr']} |")
        lines.append("")

        # By symbol
        lines.append("### Missed Runs by Symbol\n")
        lines.append("| Symbol | Count | Avg Range (ATR) | Max Range (ATR) |")
        lines.append("|--------|-------|-----------------|-----------------|")
        for sym in SYMBOLS:
            s_runs = runs_df[runs_df['symbol'] == sym]
            if len(s_runs) > 0:
                lines.append(f"| {sym} | {len(s_runs)} | {s_runs['range_atr'].mean():.2f} | {s_runs['range_atr'].max():.2f} |")
        lines.append("")

        # Specific areas user mentioned
        lines.append("### User-Mentioned Areas\n")
        lines.append("Checking specific areas mentioned by user:\n")

        user_areas = [
            ('SPY', '10:30', '13:40'),
            ('QQQ', '10:30', '13:40'),
            ('NVDA', '10:55', '11:05'),
            ('AAPL', '10:10', '12:30'),
            ('AAPL', '12:30', '14:40'),
            ('TSLA', '10:44', '11:25'),
        ]

        for sym, start, end in user_areas:
            area_runs = runs_df[
                (runs_df['symbol'] == sym) &
                (runs_df['start_time'] >= start) &
                (runs_df['end_time'] <= end)
            ]
            if len(area_runs) > 0:
                for _, run in area_runs.iterrows():
                    lines.append(f"- **{sym} {run['date']} {run['start_time']}-{run['end_time']}**: {run['range_atr']} ATR over {run['bars']} bars (NO SIGNAL)")
            else:
                # Check broader: any runs for this symbol in the time range
                broader = runs_df[
                    (runs_df['symbol'] == sym) &
                    (runs_df['start_time'] <= end) &
                    (runs_df['end_time'] >= start)
                ]
                if len(broader) > 0:
                    for _, run in broader.iterrows():
                        lines.append(f"- **{sym} {run['date']} {run['start_time']}-{run['end_time']}**: {run['range_atr']} ATR over {run['bars']} bars (overlaps window)")
                else:
                    lines.append(f"- {sym} {start}-{end}: No missed runs found in this window")
        lines.append("")

    # ─── Section 8: Logging Gap ─────────────────────────
    lines.append("## 8. v2.8 Logging Gap\n")
    lines.append("**Critical finding:** The following v2.8 features have NO Pine log output:\n")
    lines.append("- 🔇 QBS signals (Quiet Before Storm)")
    lines.append("- 🔊 MC signals (Momentum Cascade)")
    lines.append("- ⚡ Big-move flag")
    lines.append("- ⚠ Body warning (≥80%)")
    lines.append("- Volume ramp glyphs (🔇/🔊 on BRK labels)")
    lines.append("- Moderate ramp dimming")
    lines.append("")
    lines.append("**Recommendation:** Add `log.info()` calls for QBS/MC signals and include glyphs in BRK log message.\n")

    return '\n'.join(lines)


if __name__ == '__main__':
    main()
