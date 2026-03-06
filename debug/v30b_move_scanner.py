"""
v3.0b Move Scanner — Ground Truth + Cross-Symbol Trigger Discovery + Over-Optimization Audit
Analyzes 5sec parquet data for 10 symbols over last 5 trading days (Feb 28 - Mar 4, 2026).
"""

import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
import warnings
import glob
import re
import json
warnings.filterwarnings('ignore')

# ─── Config ───────────────────────────────────────────────────────────────────
PROJ_ROOT = '/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude'
CACHE_5S = f'{PROJ_ROOT}/trading_bot/cache/bars_highres/5sec'
TV_DEBUG = f'{PROJ_ROOT}/misc/TradingView/debug'
SYMBOLS = ['AAPL', 'AMD', 'AMZN', 'GOOGL', 'META', 'MSFT', 'NVDA', 'QQQ', 'SPY', 'TSLA']
TARGET_DATES = ['2026-02-28', '2026-03-02', '2026-03-03', '2026-03-04']  # Will find actual trading days
RTH_START = time(9, 30)
RTH_END = time(16, 0)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_5sec(symbol):
    """Load 5sec data, filter to RTH only."""
    f = f'{CACHE_5S}/{symbol.lower()}_5_secs_ib.parquet'
    df = pd.read_parquet(f)
    df['time'] = df['date'].dt.time
    df = df[(df['time'] >= RTH_START) & (df['time'] < RTH_END)].copy()
    df['trade_date'] = df['date'].dt.date
    return df

def resample_to_5m(df):
    """Resample 5sec data to 5-minute bars."""
    df = df.set_index('date')
    bars = df.resample('5min', label='left', closed='left').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum',
        'barCount': 'sum'
    }).dropna(subset=['open'])
    bars = bars.reset_index()
    bars['time'] = bars['date'].dt.time
    bars = bars[(bars['time'] >= RTH_START) & (bars['time'] < RTH_END)].copy()
    bars['trade_date'] = bars['date'].dt.date
    return bars

def compute_indicators(bars):
    """Compute EMA9, EMA21, ATR14, vol SMA20 on 5m bars."""
    bars = bars.copy()
    bars['ema9'] = bars['close'].ewm(span=9, adjust=False).mean()
    bars['ema21'] = bars['close'].ewm(span=21, adjust=False).mean()
    # ATR
    bars['tr'] = np.maximum(
        bars['high'] - bars['low'],
        np.maximum(
            abs(bars['high'] - bars['close'].shift(1)),
            abs(bars['low'] - bars['close'].shift(1))
        )
    )
    bars['atr14'] = bars['tr'].rolling(14).mean()
    # Volume SMA
    bars['vol_sma20'] = bars['volume'].rolling(20).mean()
    bars['vol_ratio'] = bars['volume'] / bars['vol_sma20'].replace(0, np.nan)
    return bars

def compute_key_levels(bars):
    """Compute key levels for each trading day from 5m bars."""
    levels = {}
    dates = sorted(bars['trade_date'].unique())
    for i, d in enumerate(dates):
        day = bars[bars['trade_date'] == d].copy()
        if len(day) < 5:
            continue
        lvls = {}
        # Yesterday H/L
        if i > 0:
            prev = bars[bars['trade_date'] == dates[i-1]]
            if len(prev) > 0:
                lvls['yest_h'] = prev['high'].max()
                lvls['yest_l'] = prev['low'].min()
        # ORB H/L (first 30 min = 6 bars of 5m)
        first_30 = day[day['time'] < time(10, 0)]
        if len(first_30) > 0:
            lvls['orb_h'] = first_30['high'].max()
            lvls['orb_l'] = first_30['low'].min()
        # PM H/L (first 5 min = 1 bar of 5m)
        first_5 = day[day['time'] < time(9, 35)]
        if len(first_5) > 0:
            lvls['pm_h'] = first_5['high'].max()
            lvls['pm_l'] = first_5['low'].min()
        # VWAP (cumulative)
        vwap_values = []
        cum_vol = 0
        cum_pv = 0
        for _, row in day.iterrows():
            typical = (row['high'] + row['low'] + row['close']) / 3
            cum_vol += row['volume']
            cum_pv += typical * row['volume']
            vwap_values.append(cum_pv / cum_vol if cum_vol > 0 else typical)
        lvls['vwap_series'] = dict(zip(day.index, vwap_values))
        levels[d] = lvls
    return levels

def is_near_level(price, level, atr, threshold=0.15):
    """Check if price is within threshold ATR of a level."""
    if level is None or atr is None or atr == 0:
        return False
    return abs(price - level) / atr <= threshold

def get_level_name(price, levels_dict, atr, threshold=0.15):
    """Return name of nearest key level if within threshold."""
    nearest = None
    nearest_dist = float('inf')
    for name, val in levels_dict.items():
        if name == 'vwap_series':
            continue
        dist = abs(price - val)
        if dist < nearest_dist and dist / atr <= threshold:
            nearest = name
            nearest_dist = dist
    return nearest


# ═══════════════════════════════════════════════════════════════════════════════
# TASK 1: Ground Truth of Significant Moves
# ═══════════════════════════════════════════════════════════════════════════════

def find_significant_moves(bars, symbol, levels, min_atr=0.5, window_bars=6):
    """
    Find all moves >= min_atr ATR within any window_bars (30min = 6x5m bars).
    Uses sliding window approach.
    """
    moves = []
    dates = sorted(bars['trade_date'].unique())

    for d in dates:
        day = bars[bars['trade_date'] == d].copy().reset_index(drop=True)
        if len(day) < window_bars + 1:
            continue

        day_levels = levels.get(d, {})

        for i in range(len(day) - window_bars + 1):
            window = day.iloc[i:i+window_bars]
            atr = window.iloc[0]['atr14']
            if pd.isna(atr) or atr == 0:
                continue

            # Check for directional move
            start_price = window.iloc[0]['open']

            # Bull move: find max high in window
            max_high = window['high'].max()
            max_high_idx = window['high'].idxmax()
            bull_mag = (max_high - start_price) / atr

            # Bear move: find min low in window
            min_low = window['low'].min()
            min_low_idx = window['low'].idxmin()
            bear_mag = (start_price - min_low) / atr

            # Take the larger move
            if bull_mag >= min_atr and bull_mag >= bear_mag:
                end_idx = max_high_idx
                end_bar = day.iloc[end_idx] if end_idx < len(day) else window.iloc[-1]
                direction = 'bull'
                magnitude = bull_mag
                end_price = max_high
            elif bear_mag >= min_atr:
                end_idx = min_low_idx
                end_bar = day.iloc[end_idx] if end_idx < len(day) else window.iloc[-1]
                direction = 'bear'
                magnitude = bear_mag
                end_price = min_low
            else:
                continue

            # Volume profile
            avg_vol_ratio = window['vol_ratio'].mean()

            # EMA alignment at start
            ema_bull = window.iloc[0]['ema9'] > window.iloc[0]['ema21']
            ema_aligned = (direction == 'bull' and ema_bull) or (direction == 'bear' and not ema_bull)

            # Near key level?
            near_level = get_level_name(start_price, day_levels, atr)

            # VWAP at start
            vwap_series = day_levels.get('vwap_series', {})
            vwap_at_start = vwap_series.get(window.index[0] + day.index[0], None)
            vwap_aligned = None
            if vwap_at_start is not None:
                if direction == 'bull':
                    vwap_aligned = start_price > vwap_at_start
                else:
                    vwap_aligned = start_price < vwap_at_start

            moves.append({
                'symbol': symbol,
                'date': d,
                'start_time': window.iloc[0]['date'],
                'end_time': end_bar['date'] if isinstance(end_bar, pd.Series) else window.iloc[-1]['date'],
                'direction': direction,
                'magnitude_atr': round(magnitude, 3),
                'start_price': round(start_price, 2),
                'end_price': round(end_price, 2),
                'avg_vol_ratio': round(avg_vol_ratio, 2),
                'ema_aligned': ema_aligned,
                'near_level': near_level,
                'vwap_aligned': vwap_aligned,
                'atr': round(atr, 3),
                'start_bar_vol_ratio': round(window.iloc[0]['vol_ratio'], 2) if not pd.isna(window.iloc[0]['vol_ratio']) else None,
            })

    return moves

def deduplicate_moves(moves, min_gap_bars=3):
    """Remove overlapping moves, keeping the largest."""
    if not moves:
        return []

    df = pd.DataFrame(moves)
    df = df.sort_values(['symbol', 'date', 'start_time', 'magnitude_atr'], ascending=[True, True, True, False])

    result = []
    for (sym, d), group in df.groupby(['symbol', 'date']):
        group = group.sort_values('magnitude_atr', ascending=False)
        kept = []
        for _, row in group.iterrows():
            overlap = False
            for k in kept:
                # Check time overlap - within 15 min
                time_diff = abs((row['start_time'] - k['start_time']).total_seconds())
                if time_diff < 900:  # 15 min
                    overlap = True
                    break
            if not overlap:
                kept.append(row.to_dict())
        result.extend(kept)

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# TASK 2: Cross-Symbol Simultaneous Moves
# ═══════════════════════════════════════════════════════════════════════════════

def build_5m_move_matrix(all_bars):
    """
    For each 5-minute window, compute the move (close - open) / ATR for each symbol.
    Returns a DataFrame with columns = symbols, index = timestamps.
    """
    dfs = {}
    for symbol, bars in all_bars.items():
        s = bars[['date', 'close', 'open', 'atr14']].copy()
        s['move_atr'] = (s['close'] - s['open']) / s['atr14']
        s = s.set_index('date')['move_atr']
        s.name = symbol
        dfs[symbol] = s

    matrix = pd.DataFrame(dfs)
    return matrix

def find_market_triggers(matrix, threshold=0.3, min_symbols=4):
    """Find 5-min windows where min_symbols+ move >= threshold ATR in same direction."""
    triggers = []

    for ts, row in matrix.iterrows():
        bulls = (row >= threshold).sum()
        bears = (row <= -threshold).sum()

        if bulls >= min_symbols:
            movers = row[row >= threshold].sort_values(ascending=False)
            triggers.append({
                'time': ts,
                'direction': 'bull',
                'n_symbols': bulls,
                'avg_magnitude': round(movers.mean(), 3),
                'symbols': list(movers.index),
                'magnitudes': {s: round(v, 3) for s, v in movers.items()},
                'all_moves': {s: round(v, 3) for s, v in row.dropna().items()},
            })
        if bears >= min_symbols:
            movers = row[row <= -threshold].sort_values(ascending=True)
            triggers.append({
                'time': ts,
                'direction': 'bear',
                'n_symbols': bears,
                'avg_magnitude': round(movers.mean(), 3),
                'symbols': list(movers.index),
                'magnitudes': {s: round(v, 3) for s, v in movers.items()},
                'all_moves': {s: round(v, 3) for s, v in row.dropna().items()},
            })

    return triggers

def compute_follow_through(trigger, all_bars, lookahead_bars_15m=3, lookahead_bars_30m=6):
    """After a trigger, compute 15m and 30m follow-through for each symbol."""
    results = {}
    ts = trigger['time']
    direction = trigger['direction']

    for symbol in SYMBOLS:
        if symbol not in all_bars:
            continue
        bars = all_bars[symbol]
        # Find the bar at or after trigger time
        idx = bars[bars['date'] >= ts].index
        if len(idx) == 0:
            continue
        start_idx = idx[0]
        pos = bars.index.get_loc(start_idx)
        entry_price = bars.iloc[pos]['close']
        atr = bars.iloc[pos]['atr14']
        if pd.isna(atr) or atr == 0:
            continue

        for label, n_bars in [('15m', lookahead_bars_15m), ('30m', lookahead_bars_30m)]:
            end_pos = min(pos + n_bars, len(bars) - 1)
            if end_pos <= pos:
                continue
            future = bars.iloc[pos+1:end_pos+1]
            if len(future) == 0:
                continue

            if direction == 'bull':
                exit_price = future['close'].iloc[-1]
                pnl = (exit_price - entry_price) / atr
                mfe = (future['high'].max() - entry_price) / atr
                mae = (entry_price - future['low'].min()) / atr
            else:
                exit_price = future['close'].iloc[-1]
                pnl = (entry_price - exit_price) / atr
                mfe = (entry_price - future['low'].min()) / atr
                mae = (future['high'].max() - entry_price) / atr

            results[f'{symbol}_{label}'] = {
                'symbol': symbol,
                'horizon': label,
                'pnl_atr': round(pnl, 3),
                'mfe_atr': round(mfe, 3),
                'mae_atr': round(mae, 3),
                'win': pnl > 0,
            }

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# TASK 3: Move Fingerprinting
# ═══════════════════════════════════════════════════════════════════════════════

def classify_move(move, all_bars, all_moves_at_time):
    """Classify a move into a fingerprint type."""
    fingerprints = []

    # Level Break: starts near a key level
    if move['near_level'] is not None:
        fingerprints.append('level_break')

    # Momentum Surge: first bar vol > 3x
    if move.get('start_bar_vol_ratio') and move['start_bar_vol_ratio'] > 3.0:
        fingerprints.append('momentum_surge')

    # Quiet Drift: avg vol < 1.5x
    if move['avg_vol_ratio'] < 1.5:
        fingerprints.append('quiet_drift')

    # Gap Follow-Through: move continues open direction after 9:35
    start_time = move['start_time']
    if hasattr(start_time, 'time'):
        t = start_time.time()
    else:
        t = pd.Timestamp(start_time).time()
    if t <= time(9, 40):
        fingerprints.append('gap_follow_through')

    # Cross-Symbol Cascade: 3+ symbols moving same direction within ±2 min
    same_dir_count = 0
    for other_move in all_moves_at_time:
        if other_move['symbol'] != move['symbol'] and other_move['direction'] == move['direction']:
            time_diff = abs((other_move['start_time'] - move['start_time']).total_seconds())
            if time_diff <= 120:
                same_dir_count += 1
    if same_dir_count >= 2:  # 3+ total including this one
        fingerprints.append('cross_symbol_cascade')

    # Reversal: move goes against prior 15-min trend (check EMA alignment = opposite)
    if not move['ema_aligned']:
        fingerprints.append('reversal')

    if not fingerprints:
        fingerprints.append('unclassified')

    return fingerprints

def compute_move_continuation(move, all_bars, lookahead_min=30):
    """Check if the move continued for lookahead_min minutes after end_time."""
    symbol = move['symbol']
    if symbol not in all_bars:
        return None
    bars = all_bars[symbol]
    end_time = move['end_time']
    atr = move['atr']

    future = bars[bars['date'] > end_time].head(lookahead_min // 5)
    if len(future) == 0:
        return None

    if move['direction'] == 'bull':
        continuation = (future['high'].max() - move['end_price']) / atr
    else:
        continuation = (move['end_price'] - future['low'].min()) / atr

    return round(continuation, 3)


# ═══════════════════════════════════════════════════════════════════════════════
# TASK 4: Over-Optimization Audit
# ═══════════════════════════════════════════════════════════════════════════════

def simulate_v28_signals(bars, symbol, levels):
    """
    Simpler v2.8-like system:
    - Any close through a key level with vol >= 1.5x → signal
    - No EMA Hard Gate
    - No once-per-session limitation on ALL levels
    - No afternoon dimming
    """
    signals = []
    dates = sorted(bars['trade_date'].unique())

    for d in dates:
        day = bars[bars['trade_date'] == d].copy().reset_index(drop=True)
        day_levels = levels.get(d, {})
        if not day_levels:
            continue

        # Track which levels have been touched per direction (once per direction per level)
        touched = {}

        for i in range(1, len(day)):
            prev = day.iloc[i-1]
            curr = day.iloc[i]
            atr = curr['atr14']
            if pd.isna(atr) or atr == 0:
                continue
            vol_ratio = curr['vol_ratio']
            if pd.isna(vol_ratio):
                continue

            for level_name, level_val in day_levels.items():
                if level_name == 'vwap_series':
                    continue

                # Bull breakout: prev close below, curr close above
                if prev['close'] < level_val and curr['close'] > level_val and vol_ratio >= 1.5:
                    key = (level_name, 'bull')
                    if key not in touched:
                        touched[key] = True
                        signals.append({
                            'symbol': symbol,
                            'date': d,
                            'time': curr['date'],
                            'direction': 'bull',
                            'level': level_name,
                            'level_val': level_val,
                            'vol_ratio': round(vol_ratio, 2),
                            'close': curr['close'],
                            'atr': round(atr, 3),
                            'ema_aligned': curr['ema9'] > curr['ema21'],
                            'hour': curr['date'].hour,
                        })

                # Bear breakdown: prev close above, curr close below
                if prev['close'] > level_val and curr['close'] < level_val and vol_ratio >= 1.5:
                    key = (level_name, 'bear')
                    if key not in touched:
                        touched[key] = True
                        signals.append({
                            'symbol': symbol,
                            'date': d,
                            'time': curr['date'],
                            'direction': 'bear',
                            'level': level_name,
                            'level_val': level_val,
                            'vol_ratio': round(vol_ratio, 2),
                            'close': curr['close'],
                            'atr': round(atr, 3),
                            'ema_aligned': curr['ema9'] < curr['ema21'],
                            'hour': curr['date'].hour,
                        })

    return signals

def simulate_v30b_signals(bars, symbol, levels):
    """
    v3.0b-like system:
    - Key level cross with vol >= 1.5x
    - EMA Hard Gate after 9:50 (suppress if counter-EMA)
    - Once-per-session per level per direction
    - Afternoon dimming (after 11:30)
    """
    signals = []
    dates = sorted(bars['trade_date'].unique())

    for d in dates:
        day = bars[bars['trade_date'] == d].copy().reset_index(drop=True)
        day_levels = levels.get(d, {})
        if not day_levels:
            continue

        touched = {}

        for i in range(1, len(day)):
            prev = day.iloc[i-1]
            curr = day.iloc[i]
            atr = curr['atr14']
            if pd.isna(atr) or atr == 0:
                continue
            vol_ratio = curr['vol_ratio']
            if pd.isna(vol_ratio):
                continue

            bar_time = curr['date'].time()
            hour = curr['date'].hour
            minute = curr['date'].minute

            for level_name, level_val in day_levels.items():
                if level_name == 'vwap_series':
                    continue

                for direction in ['bull', 'bear']:
                    # Check level cross
                    if direction == 'bull':
                        crossed = prev['close'] < level_val and curr['close'] > level_val
                        ema_aligned = curr['ema9'] > curr['ema21']
                    else:
                        crossed = prev['close'] > level_val and curr['close'] < level_val
                        ema_aligned = curr['ema9'] < curr['ema21']

                    if not crossed or vol_ratio < 1.5:
                        continue

                    key = (level_name, direction)
                    if key in touched:
                        continue
                    touched[key] = True

                    # EMA Hard Gate after 9:50
                    ema_suppressed = False
                    if bar_time >= time(9, 50) and not ema_aligned:
                        ema_suppressed = True

                    # Afternoon dim
                    afternoon_dim = bar_time >= time(11, 30)

                    signals.append({
                        'symbol': symbol,
                        'date': d,
                        'time': curr['date'],
                        'direction': direction,
                        'level': level_name,
                        'level_val': level_val,
                        'vol_ratio': round(vol_ratio, 2),
                        'close': curr['close'],
                        'atr': round(atr, 3),
                        'ema_aligned': ema_aligned,
                        'ema_suppressed': ema_suppressed,
                        'afternoon_dim': afternoon_dim,
                        'hour': hour,
                        'active': not ema_suppressed,  # v3.0b would fire this
                    })

    return signals

def compute_signal_pnl(signal, bars, lookahead_bars=6):
    """Compute PnL for a signal over lookahead bars."""
    ts = signal['time']
    atr = signal['atr']
    direction = signal['direction']

    future = bars[bars['date'] > ts].head(lookahead_bars)
    if len(future) == 0:
        return None

    entry = signal['close']
    if direction == 'bull':
        pnl = (future['close'].iloc[-1] - entry) / atr
        mfe = (future['high'].max() - entry) / atr
        mae = (entry - future['low'].min()) / atr
    else:
        pnl = (entry - future['close'].iloc[-1]) / atr
        mfe = (entry - future['low'].min()) / atr
        mae = (future['high'].max() - entry) / atr

    return {'pnl': round(pnl, 3), 'mfe': round(mfe, 3), 'mae': round(mae, 3), 'win': pnl > 0}


# ═══════════════════════════════════════════════════════════════════════════════
# TASK 5: TSLA March 4 → March 5 Level Computation
# ═══════════════════════════════════════════════════════════════════════════════

def compute_tsla_levels_for_mar5(all_bars):
    """Compute what Yesterday H, PM H, VWAP would be for TSLA on March 5."""
    bars = all_bars.get('TSLA')
    if bars is None:
        return None

    from datetime import date
    mar4 = bars[bars['trade_date'] == date(2026, 3, 4)]
    if len(mar4) == 0:
        return None

    result = {
        'yest_h': round(mar4['high'].max(), 2),
        'yest_l': round(mar4['low'].min(), 2),
        'yest_close': round(mar4['close'].iloc[-1], 2),
        'yest_open': round(mar4['open'].iloc[0], 2),
    }
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Pine Log Parsing
# ═══════════════════════════════════════════════════════════════════════════════

def load_pine_logs():
    """Load and parse all v3.0b pine logs."""
    logs = sorted(glob.glob(f'{TV_DEBUG}/pine-logs-Key Level Breakout v3.0b_*.csv'))
    all_entries = []
    for f in logs:
        df = pd.read_csv(f)
        df['source_file'] = f.split('/')[-1]
        all_entries.append(df)

    if not all_entries:
        return pd.DataFrame()

    pine = pd.concat(all_entries, ignore_index=True)
    pine['ts'] = pd.to_datetime(pine['Date'])

    # Parse signal entries (BRK, REV, VWAP, etc.)
    signals = []
    for _, row in pine.iterrows():
        msg = str(row['Message'])
        if '[KLB]' not in msg:
            continue

        # Extract time and direction
        time_match = re.search(r'(\d+:\d+)', msg)
        dir_match = re.search(r'(▲|▼)', msg)

        if not time_match or not dir_match:
            continue

        direction = 'bull' if dir_match.group(1) == '▲' else 'bear'

        # Signal type
        sig_type = None
        if ' BRK ' in msg:
            sig_type = 'BRK'
        elif ' REV ' in msg:
            sig_type = 'REV'
        elif ' RCL ' in msg:
            sig_type = 'RCL'
        elif ' RST ' in msg:
            sig_type = 'RST'
        elif '~ ~ VWAP' in msg:
            sig_type = 'VWAP'
        elif ' RNG ' in msg:
            sig_type = 'RNG'
        elif 'CONF' in msg:
            sig_type = 'CONF'
        elif '5m CHECK' in msg:
            sig_type = '5mCHECK'

        if sig_type is None:
            continue

        # Extract vol
        vol_match = re.search(r'vol=([\d.]+)x', msg)
        vol = float(vol_match.group(1)) if vol_match else None

        # Extract level
        level_match = re.search(r'BRK\s+([\w\s+]+)\s+vol=', msg)
        level = level_match.group(1).strip() if level_match else None

        # Check for suppression markers
        suppressed = '~' in msg and sig_type not in ['RNG', 'CONF', '5mCHECK']

        signals.append({
            'ts': row['ts'],
            'date': row['ts'].date(),
            'time_str': time_match.group(1),
            'direction': direction,
            'type': sig_type,
            'vol': vol,
            'level': level,
            'suppressed': suppressed,
            'msg': msg[:200],
            'source': row['source_file'],
        })

    return pd.DataFrame(signals)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    from datetime import date

    print("=" * 80)
    print("v3.0b MOVE SCANNER — Ground Truth + Cross-Symbol Triggers")
    print("=" * 80)

    # ─── Load & Prepare Data ──────────────────────────────────────────────────
    print("\n[1/6] Loading 5sec data and resampling to 5min...")
    all_bars = {}
    all_levels = {}

    for symbol in SYMBOLS:
        print(f"  Loading {symbol}...", end=' ')
        raw = load_5sec(symbol)
        bars = resample_to_5m(raw)
        bars = compute_indicators(bars)
        levels = compute_key_levels(bars)
        all_bars[symbol] = bars
        all_levels[symbol] = levels
        print(f"{len(bars)} bars, {len(levels)} days")

    # Filter to last 5 trading days
    all_dates = set()
    for s in SYMBOLS:
        all_dates.update(all_bars[s]['trade_date'].unique())
    trading_days = sorted(all_dates)
    last_5 = trading_days[-5:]
    print(f"\n  Last 5 trading days: {[str(d) for d in last_5]}")

    # Filter bars to last 5 days
    for symbol in SYMBOLS:
        all_bars[symbol] = all_bars[symbol][all_bars[symbol]['trade_date'].isin(last_5)].copy()

    # ─── Task 1: Ground Truth Moves ──────────────────────────────────────────
    print("\n[2/6] Finding significant moves (>= 0.5 ATR in 30 min)...")
    all_moves = []
    for symbol in SYMBOLS:
        moves = find_significant_moves(all_bars[symbol], symbol, all_levels[symbol])
        all_moves.extend(moves)

    all_moves = deduplicate_moves(all_moves)
    print(f"  Found {len(all_moves)} significant moves across {len(SYMBOLS)} symbols")

    # Summary by symbol and direction
    moves_df = pd.DataFrame(all_moves)
    if len(moves_df) > 0:
        print("\n  Moves by symbol:")
        for s in SYMBOLS:
            s_moves = moves_df[moves_df['symbol'] == s]
            bull = len(s_moves[s_moves['direction'] == 'bull'])
            bear = len(s_moves[s_moves['direction'] == 'bear'])
            avg_mag = s_moves['magnitude_atr'].mean()
            print(f"    {s:6s}: {len(s_moves):3d} moves (bull={bull}, bear={bear}), avg magnitude={avg_mag:.2f} ATR")

        print(f"\n  Moves by date:")
        for d in last_5:
            d_moves = moves_df[moves_df['date'] == d]
            print(f"    {d}: {len(d_moves)} moves")

        print(f"\n  Moves near key levels: {len(moves_df[moves_df['near_level'].notna()])} ({100*len(moves_df[moves_df['near_level'].notna()])/len(moves_df):.0f}%)")
        print(f"  EMA-aligned moves: {len(moves_df[moves_df['ema_aligned']])} ({100*len(moves_df[moves_df['ema_aligned']])/len(moves_df):.0f}%)")

        # Level distribution
        print(f"\n  Near-level distribution:")
        for level, count in moves_df['near_level'].value_counts().items():
            if pd.notna(level):
                print(f"    {level}: {count}")

    # ─── Task 2: Cross-Symbol Triggers ───────────────────────────────────────
    print("\n[3/6] Finding cross-symbol triggers (4+ symbols, same direction, 5min)...")
    matrix = build_5m_move_matrix(all_bars)

    # Also try lower threshold for research
    triggers_4plus = find_market_triggers(matrix, threshold=0.3, min_symbols=4)
    triggers_3plus = find_market_triggers(matrix, threshold=0.3, min_symbols=3)

    print(f"  4+ symbols, >= 0.3 ATR: {len(triggers_4plus)} triggers")
    print(f"  3+ symbols, >= 0.3 ATR: {len(triggers_3plus)} triggers")

    # Follow-through analysis for 4+ triggers
    trigger_results = []
    for t in triggers_4plus:
        ft = compute_follow_through(t, all_bars)
        t['follow_through'] = ft

        # Aggregate follow-through
        ft_15m = [v for k, v in ft.items() if v['horizon'] == '15m']
        ft_30m = [v for k, v in ft.items() if v['horizon'] == '30m']

        if ft_15m:
            t['ft_15m_avg_pnl'] = round(np.mean([x['pnl_atr'] for x in ft_15m]), 3)
            t['ft_15m_win_rate'] = round(np.mean([x['win'] for x in ft_15m]), 3)
        if ft_30m:
            t['ft_30m_avg_pnl'] = round(np.mean([x['pnl_atr'] for x in ft_30m]), 3)
            t['ft_30m_win_rate'] = round(np.mean([x['win'] for x in ft_30m]), 3)

        trigger_results.append(t)

    if trigger_results:
        print(f"\n  Cross-Symbol Trigger Details (4+ symbols):")
        for t in trigger_results:
            time_str = t['time'].strftime('%Y-%m-%d %H:%M') if hasattr(t['time'], 'strftime') else str(t['time'])
            print(f"    {time_str} {t['direction']:4s} | {t['n_symbols']} symbols | avg mag={t['avg_magnitude']:.2f} ATR")
            mover_strs = [f"{s}({t['magnitudes'][s]:.2f})" for s in t['symbols'][:6]]
            print(f"      Movers: {', '.join(mover_strs)}")
            if 'ft_15m_avg_pnl' in t:
                print(f"      15m follow-through: avg PnL={t['ft_15m_avg_pnl']:.3f} ATR, win={t['ft_15m_win_rate']:.0%}")
            if 'ft_30m_avg_pnl' in t:
                print(f"      30m follow-through: avg PnL={t['ft_30m_avg_pnl']:.3f} ATR, win={t['ft_30m_win_rate']:.0%}")

    # Analyze leader/lagger patterns for 3+ triggers
    print(f"\n  Leader Analysis (3+ symbol triggers):")
    leader_counts = {}
    for t in triggers_3plus:
        if t['symbols']:
            leader = t['symbols'][0]  # Largest magnitude = leader
            leader_counts[leader] = leader_counts.get(leader, 0) + 1
    for s, c in sorted(leader_counts.items(), key=lambda x: -x[1]):
        print(f"    {s}: leads {c} times ({100*c/len(triggers_3plus):.0f}%)")

    # Time distribution
    print(f"\n  Trigger time distribution:")
    if triggers_3plus:
        hours = {}
        for t in triggers_3plus:
            h = t['time'].hour if hasattr(t['time'], 'hour') else pd.Timestamp(t['time']).hour
            hours[h] = hours.get(h, 0) + 1
        for h in sorted(hours):
            print(f"    {h}:00: {hours[h]} triggers")

    # ─── Task 3: Move Fingerprinting ─────────────────────────────────────────
    print("\n[4/6] Classifying move fingerprints...")
    fingerprint_stats = {}

    for move in all_moves:
        # Find concurrent moves for cascade detection
        concurrent = [m for m in all_moves if m['date'] == move['date']
                      and abs((m['start_time'] - move['start_time']).total_seconds()) <= 120]

        fps = classify_move(move, all_bars, concurrent)

        # Compute continuation
        continuation = compute_move_continuation(move, all_bars)

        for fp in fps:
            if fp not in fingerprint_stats:
                fingerprint_stats[fp] = {'moves': [], 'continuations': [], 'magnitudes': []}
            fingerprint_stats[fp]['moves'].append(move)
            fingerprint_stats[fp]['magnitudes'].append(move['magnitude_atr'])
            if continuation is not None:
                fingerprint_stats[fp]['continuations'].append(continuation)

    print(f"\n  Fingerprint Classification:")
    print(f"  {'Type':<25s} {'N':>4s} {'Avg Mag':>8s} {'Win%':>6s} {'Avg Cont':>9s}")
    print(f"  {'-'*25} {'-'*4} {'-'*8} {'-'*6} {'-'*9}")
    for fp, stats in sorted(fingerprint_stats.items(), key=lambda x: -len(x[1]['moves'])):
        n = len(stats['moves'])
        avg_mag = np.mean(stats['magnitudes'])
        conts = stats['continuations']
        if conts:
            win_pct = sum(1 for c in conts if c > 0) / len(conts)
            avg_cont = np.mean(conts)
        else:
            win_pct = 0
            avg_cont = 0
        print(f"  {fp:<25s} {n:4d} {avg_mag:8.2f} {win_pct:6.0%} {avg_cont:9.3f}")

    # ─── Task 4: Over-Optimization Audit ─────────────────────────────────────
    print("\n[5/6] Over-Optimization Audit (v2.8 vs v3.0b)...")

    v28_all = []
    v30b_all = []

    for symbol in SYMBOLS:
        v28 = simulate_v28_signals(all_bars[symbol], symbol, all_levels[symbol])
        v30b = simulate_v30b_signals(all_bars[symbol], symbol, all_levels[symbol])

        # Compute PnL for each signal
        for sig in v28:
            pnl = compute_signal_pnl(sig, all_bars[symbol])
            if pnl:
                sig.update(pnl)
        for sig in v30b:
            pnl = compute_signal_pnl(sig, all_bars[symbol])
            if pnl:
                sig.update(pnl)

        v28_all.extend(v28)
        v30b_all.extend(v30b)

    v28_df = pd.DataFrame(v28_all)
    v30b_df = pd.DataFrame(v30b_all)

    print(f"\n  v2.8 signals: {len(v28_df)}")
    print(f"  v3.0b signals: {len(v30b_df)} (active: {len(v30b_df[v30b_df['active']])})")

    if 'pnl' in v28_df.columns and len(v28_df) > 0:
        print(f"\n  v2.8 performance (30min hold):")
        print(f"    Total PnL: {v28_df['pnl'].sum():.2f} ATR")
        print(f"    Win rate: {v28_df['win'].mean():.0%}")
        print(f"    Avg PnL: {v28_df['pnl'].mean():.3f} ATR")
        print(f"    Avg MFE: {v28_df['mfe'].mean():.3f} ATR")
        print(f"    Avg MAE: {v28_df['mae'].mean():.3f} ATR")

    if 'pnl' in v30b_df.columns and len(v30b_df) > 0:
        active = v30b_df[v30b_df['active']]
        suppressed = v30b_df[~v30b_df['active']]

        print(f"\n  v3.0b ACTIVE performance:")
        if len(active) > 0 and 'pnl' in active.columns:
            print(f"    Total PnL: {active['pnl'].sum():.2f} ATR")
            print(f"    Win rate: {active['win'].mean():.0%}")
            print(f"    Avg PnL: {active['pnl'].mean():.3f} ATR")

        print(f"\n  v3.0b SUPPRESSED signals (EMA gate):")
        if len(suppressed) > 0 and 'pnl' in suppressed.columns:
            print(f"    N suppressed: {len(suppressed)}")
            print(f"    Total PnL if allowed: {suppressed['pnl'].sum():.2f} ATR")
            print(f"    Win rate: {suppressed['win'].mean():.0%}")
            print(f"    Avg PnL: {suppressed['pnl'].mean():.3f} ATR")

            # Profitable suppressed signals
            prof_supp = suppressed[suppressed['pnl'] > 0]
            print(f"    Profitable: {len(prof_supp)} ({100*len(prof_supp)/len(suppressed):.0f}%)")
            if len(prof_supp) > 0:
                print(f"    Missed PnL from profitable: {prof_supp['pnl'].sum():.2f} ATR")

        # Afternoon analysis
        afternoon = v30b_df[v30b_df['afternoon_dim']]
        print(f"\n  Afternoon signals (after 11:30):")
        if len(afternoon) > 0 and 'pnl' in afternoon.columns:
            print(f"    N: {len(afternoon)}")
            print(f"    Win rate: {afternoon['win'].mean():.0%}")
            print(f"    Avg PnL: {afternoon['pnl'].mean():.3f} ATR")
            print(f"    Total PnL: {afternoon['pnl'].sum():.2f} ATR")

        # Once-per-session analysis
        # Look for levels that are touched multiple times in v2.8 but blocked in v3.0b
        print(f"\n  Volume filter analysis (signals with vol < 1.5x):")
        # Check bars near levels with low vol
        low_vol_touches = 0
        low_vol_good = 0
        for symbol in SYMBOLS:
            bars = all_bars[symbol]
            for d in last_5:
                day_levels = all_levels[symbol].get(d, {})
                day_bars = bars[bars['trade_date'] == d]
                for _, bar in day_bars.iterrows():
                    atr = bar['atr14']
                    if pd.isna(atr) or atr == 0:
                        continue
                    vol_r = bar['vol_ratio']
                    if pd.isna(vol_r) or vol_r >= 1.5:
                        continue
                    for ln, lv in day_levels.items():
                        if ln == 'vwap_series':
                            continue
                        if is_near_level(bar['close'], lv, atr, 0.05):
                            low_vol_touches += 1
                            # Check if profitable (next 6 bars)
                            future = bars[bars['date'] > bar['date']].head(6)
                            if len(future) > 0:
                                # Simple check: did it move 0.3 ATR in the touch direction?
                                if bar['close'] > lv:
                                    ft_pnl = (future['high'].max() - bar['close']) / atr
                                else:
                                    ft_pnl = (bar['close'] - future['low'].min()) / atr
                                if ft_pnl > 0.3:
                                    low_vol_good += 1
                            break  # Only count once per bar
        print(f"    Low-vol level touches: {low_vol_touches}")
        print(f"    Would have been profitable (>0.3 ATR in 30m): {low_vol_good} ({100*low_vol_good/max(1,low_vol_touches):.0f}%)")

    # ─── TSLA March 5 Level Analysis ──────────────────────────────────────────
    print("\n  TSLA March 4 → March 5 Level Computation:")
    tsla_levels = compute_tsla_levels_for_mar5(all_bars)
    if tsla_levels:
        for k, v in tsla_levels.items():
            print(f"    {k}: {v}")

        # Check EMA state at end of Mar 4
        tsla_bars = all_bars['TSLA']
        mar4_bars = tsla_bars[tsla_bars['trade_date'] == date(2026, 3, 4)]
        if len(mar4_bars) > 0:
            last_bar = mar4_bars.iloc[-1]
            print(f"    EMA9={last_bar['ema9']:.2f}, EMA21={last_bar['ema21']:.2f}")
            print(f"    EMA direction at close: {'bull' if last_bar['ema9'] > last_bar['ema21'] else 'bear'}")

    # ─── Task 5: Right Signal for Right Move ─────────────────────────────────
    print("\n[6/6] Right Signal for Right Move Framework...")

    # Classify moves by what signal type would best capture them
    framework = {
        'level_break': {'desc': 'BRK signal (barrier levels)', 'caught': 0, 'missed': 0, 'total': 0},
        'momentum_surge': {'desc': 'RNG signal', 'caught': 0, 'missed': 0, 'total': 0},
        'quiet_drift': {'desc': 'No signal type (low vol drift)', 'caught': 0, 'missed': 0, 'total': 0},
        'gap_follow_through': {'desc': 'BRK/RNG at open', 'caught': 0, 'missed': 0, 'total': 0},
        'reversal': {'desc': 'REV signal', 'caught': 0, 'missed': 0, 'total': 0},
        'cross_symbol_cascade': {'desc': 'NEW: Cascade signal', 'caught': 0, 'missed': 0, 'total': 0},
    }

    for move in all_moves:
        concurrent = [m for m in all_moves if m['date'] == move['date']
                      and abs((m['start_time'] - move['start_time']).total_seconds()) <= 120]
        fps = classify_move(move, all_bars, concurrent)

        # Check if any v3.0b signal would have caught this move
        # (signal within 10 min of move start, same direction)
        caught = False
        if len(v30b_df) > 0:
            for _, sig in v30b_df[v30b_df['active']].iterrows():
                if (sig['symbol'] == move['symbol']
                    and sig['direction'] == move['direction']
                    and abs((sig['time'] - move['start_time']).total_seconds()) <= 600):
                    caught = True
                    break

        for fp in fps:
            if fp in framework:
                framework[fp]['total'] += 1
                if caught:
                    framework[fp]['caught'] += 1
                else:
                    framework[fp]['missed'] += 1

    print(f"\n  {'Move Type':<25s} {'Total':>6s} {'Caught':>7s} {'Missed':>7s} {'Catch%':>7s}")
    print(f"  {'-'*25} {'-'*6} {'-'*7} {'-'*7} {'-'*7}")
    for fp, stats in framework.items():
        if stats['total'] > 0:
            catch_pct = stats['caught'] / stats['total']
            print(f"  {fp:<25s} {stats['total']:6d} {stats['caught']:7d} {stats['missed']:7d} {catch_pct:7.0%}")

    # ─── Collect all results for report ──────────────────────────────────────
    results = {
        'last_5_days': [str(d) for d in last_5],
        'total_moves': len(all_moves),
        'moves_by_symbol': moves_df.groupby('symbol').size().to_dict() if len(moves_df) > 0 else {},
        'triggers_4plus': len(triggers_4plus),
        'triggers_3plus': len(triggers_3plus),
        'trigger_details': trigger_results,
        'fingerprint_stats': {fp: {'n': len(s['moves']),
                                    'avg_mag': round(np.mean(s['magnitudes']), 3),
                                    'win_pct': round(sum(1 for c in s['continuations'] if c > 0) / max(1, len(s['continuations'])), 3),
                                    'avg_cont': round(np.mean(s['continuations']), 3) if s['continuations'] else 0}
                               for fp, s in fingerprint_stats.items()},
        'v28_signals': len(v28_df),
        'v30b_active': len(v30b_df[v30b_df['active']]) if 'active' in v30b_df.columns else 0,
        'v30b_suppressed': len(v30b_df[~v30b_df['active']]) if 'active' in v30b_df.columns else 0,
        'framework': framework,
        'tsla_levels': tsla_levels,
        'leader_counts': leader_counts,
        'all_moves': all_moves,
        'v28_df': v28_df,
        'v30b_df': v30b_df,
        'triggers_3plus_data': triggers_3plus,
    }

    return results


if __name__ == '__main__':
    results = main()

    # Save raw results for report generation
    import pickle
    pickle_path = f'{TV_DEBUG}/v30b_scan_results.pkl'
    with open(pickle_path, 'wb') as f:
        pickle.dump(results, f)
    print(f"\nResults saved to {pickle_path}")
