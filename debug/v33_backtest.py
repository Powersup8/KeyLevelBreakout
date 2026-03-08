#!/usr/bin/env python3
"""
KLB v3.3 Backtest — Pine Log Signals vs IB 1m MFE/MAE
======================================================
Parses v3.3 Pine log CSVs, identifies symbols from price data,
loads IB 1m candle data for MFE/MAE over 60 minutes post-signal,
and compares vs v3.2 logs.

v3.3 changes (8 quality filters):
  1. Vol exhaust dim: trigger vol > 5x avg → dim (not suppress)
  2. Exhaustion: afternoon + range > 1.5 ATR consumed + SPY > 0.8% → dim
  3. Level freshness: level tested 3+ times today → dim
  4. Quiet coil: drying volume + small range → EMA bypass (catches monsters)
  5. Midday flat-EMA: midday + flat EMA → override dim (quality signal)
  6. Broad coil: small trigger + SPY moving → override dim
  7. EMA bypass pre-9:50 (carried from v3.2 but expanded)
  8. Regime dim for R1 bull

Output: v33-backtest-results.md
"""

import pandas as pd
import numpy as np
import re
import csv
import glob
from pathlib import Path
from datetime import time as dtime, datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ── Config ────────────────────────────────────────────────────────────────────
SYMBOLS = ['SPY','AAPL','AMD','AMZN','GLD','GOOGL','META','MSFT','NFLX','NVDA','QQQ','SLV','TSLA','TSM','XLE']
BAR_DIR = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars/')
LOG_DIR = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug/')
OUT_DIR = LOG_DIR

V33_GLOB = 'pine-logs-Key Level Breakout v3.3_*.csv'
V32_GLOB = 'pine-logs-Key Level Breakout v3.2_*.csv'

MFE_MINUTES = 60  # 60-minute forward window for MFE/MAE
ATR_PERIOD = 14
WIN_MFE_THRESHOLD = 0.10  # WIN if MFE >= 0.10 ATR and MFE > MAE


# ── Pine Log Parsing ─────────────────────────────────────────────────────────

# Signal line pattern: [KLB] HH:MM ▲/▼ TYPE LEVELS vol=Xx ...
# Types in log: BRK, ~, ~~, x~, FADE, RNG, QBS (🔇 QBS)
# BRK = breakout, ~ = reversal (no reclaim), ~~ = reversal+reclaim (EXREV),
# x~ = reversal counter-EMA, FADE = fade, RNG = range break

SIG_PATTERN = re.compile(
    r'\[KLB\]\s+'
    r'(\d+:\d+)\s+'         # time HH:MM
    r'([▲▼])\s+'            # direction
    r'(.+?)\s+'             # type + levels (everything before vol=)
    r'vol=([0-9.]+)x\s+'   # vol ratio
    r'pos=([v^]\d+)\s+'    # close position
    r'vwap=(above|below|na)\s+'
    r'ema=(bull|bear|na)\s+'
    r'rs=([+-]?[0-9.]+%?)\s+'
    r'adx=(\d+|na)\s+'
    r'body=(\d+)%\s+'
    r'ramp=([0-9.]+)x\s+'
    r'rangeATR=([0-9.]+)\s*'
    r'(.*?)\s*'             # flags (⚡ ⚠ 🔇 etc) + OHLC
    r'O([0-9.]+)\s+'
    r'H([0-9.]+)\s+'
    r'L([0-9.]+)\s+'
    r'C([0-9.]+)\s+'
    r'ATR=([0-9.]+)'
)

# Simpler pattern for lines that might have extra whitespace / multiline
SIG_PATTERN_SIMPLE = re.compile(
    r'\[KLB\]\s+(\d+:\d+)\s+([▲▼])\s+(.+?)\s+vol=([0-9.]+)x'
)

RNG_PATTERN = re.compile(
    r'\[KLB\]\s+(\d+:\d+)\s+([▲▼])\s+RNG\s+range\s+break\s+vol=([0-9.]+)x'
)

FADE_PATTERN = re.compile(
    r'\[KLB\]\s+(\d+:\d+)\s+([▲▼])\s+FADE\s+at\s+([0-9.]+)'
)

CONF_PATTERN = re.compile(
    r'\[KLB\]\s+CONF\s+(\d+:\d+)\s+([▲▼])\s+(BRK|QBS)\s+→\s+(✓★?|✗|✓)\s*\((.+?)\)'
)

CHECK_PATTERN = re.compile(
    r'\[KLB\]\s+5m\s+CHECK\s+(\d+:\d+)\s+([▲▼])\s+pnl=([+-]?[0-9.]+)\s+(SPY[✓✗~])\s+→\s+(HOLD|BAIL)'
)

# QBS pattern (🔇 QBS in log) - these get logged via the QBS-specific log.info
QBS_PATTERN = re.compile(
    r'\[KLB\]\s+(\d+:\d+)\s+([▲▼])\s+🔇\s+QBS\s+'
    r'ramp=([0-9.]+)x\s+'
    r'vol=([0-9.]+)x\s+'
    r'pos=([v^]\d+)\s+'
    r'vwap=(above|below|na)\s+'
    r'ema=(bull|bear|na)\s+'
    r'adx=(\d+|na)\s+'
    r'body=(\d+)%\s+'
    r'rangeATR=([0-9.]+)\s*'
    r'(.*?)\s*'  # flags
    r'O([0-9.]+)\s+'
    r'H([0-9.]+)\s+'
    r'L([0-9.]+)\s+'
    r'C([0-9.]+)\s+'
    r'ATR=([0-9.]+)'
)


def parse_type_and_levels(type_level_str):
    """Parse the type+levels string from a signal line.

    Examples:
      'BRK PM L + Yest L'  -> type='BRK', levels=['PM L', 'Yest L']
      '~ ~ VWAP'           -> type='REV', levels=['VWAP']
      '~ x~ ORB H'         -> type='REV', levels=['ORB H'], counter_ema=True
      '~~ PM L'            -> type='EXREV', levels=['PM L'] (reclaim)

    Returns: (sig_type, levels_str, is_dimmed, is_counter_ema)
    """
    s = type_level_str.strip()
    is_dimmed = False
    is_counter_ema = False

    # Check for dim marker (? suffix is in the label, not the log line type field)
    # The log line has "dim" or "moddim" suffix for QBS, but for main signals
    # the dim is indicated by specific conditions we need to detect

    # Determine signal type
    if s.startswith('BRK '):
        sig_type = 'BRK'
        levels_str = s[4:].strip()
    elif s.startswith('~ x~ '):
        # Counter-EMA reversal (would be dimmed or suppressed in most cases)
        sig_type = 'REV'
        levels_str = s[5:].strip()
        is_counter_ema = True
    elif s.startswith('~ ~~ '):
        # Reclaim reversal
        sig_type = 'EXREV'
        levels_str = s[5:].strip()
    elif s.startswith('~~ '):
        # Reclaim reversal (alternate format)
        sig_type = 'EXREV'
        levels_str = s[3:].strip()
    elif s.startswith('~ ~ '):
        # Standard reversal
        sig_type = 'REV'
        levels_str = s[4:].strip()
    elif s.startswith('~ '):
        # Plain reversal
        sig_type = 'REV'
        levels_str = s[2:].strip()
    else:
        sig_type = 'UNK'
        levels_str = s

    # Clean up levels: split by ' + ' for multi-level signals
    # Also remove any '~ ' prefix from level names (nested reversal markers)
    levels_cleaned = []
    for part in levels_str.split(' + '):
        part = part.strip()
        # Remove leading ~ markers from each level part
        while part.startswith('~ '):
            part = part[2:]
        if part:
            levels_cleaned.append(part)
    levels_str = ' + '.join(levels_cleaned)

    return sig_type, levels_str, is_dimmed, is_counter_ema


def parse_pine_log(filepath):
    """Parse a v3.3 (or v3.2) Pine log CSV into signal records.

    Returns list of dicts, one per signal.
    """
    signals = []
    confs = []
    checks = []

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)

        for row in reader:
            if len(row) < 2:
                continue
            timestamp_str = row[0]
            # Handle multiline messages (CSV quoting can split)
            message = ' '.join(row[1:]).strip()

            # Parse timestamp
            try:
                ts = pd.Timestamp(timestamp_str)
            except:
                continue

            # Skip non-KLB lines
            if '[KLB]' not in message:
                continue

            # ── RNG signal ──
            m = RNG_PATTERN.search(message)
            if m:
                time_str, direction_char, vol_str = m.groups()
                signals.append({
                    'timestamp': ts,
                    'time_str': time_str,
                    'direction': 'bull' if direction_char == '▲' else 'bear',
                    'sig_type': 'RNG',
                    'levels': 'range',
                    'vol_ratio': float(vol_str),
                    'close_pos': None,
                    'vwap': None,
                    'ema': None,
                    'rs': None,
                    'adx': None,
                    'body_pct': None,
                    'ramp': None,
                    'range_atr': None,
                    'is_big_move': False,
                    'is_vol_drying': False,
                    'is_body_warn': False,
                    'open': None, 'high': None, 'low': None, 'close': None,
                    'atr': None,
                    'is_counter_ema': False,
                    'is_dim': False,
                    'dim_reason': None,
                    'conf': None,
                    'check_result': None,
                })
                continue

            # ── FADE signal ──
            m = FADE_PATTERN.search(message)
            if m:
                time_str, direction_char, level_price = m.groups()
                signals.append({
                    'timestamp': ts,
                    'time_str': time_str,
                    'direction': 'bull' if direction_char == '▲' else 'bear',
                    'sig_type': 'FADE',
                    'levels': f'at {level_price}',
                    'vol_ratio': None,
                    'close_pos': None,
                    'vwap': None,
                    'ema': None,
                    'rs': None,
                    'adx': None,
                    'body_pct': None,
                    'ramp': None,
                    'range_atr': None,
                    'is_big_move': False,
                    'is_vol_drying': False,
                    'is_body_warn': False,
                    'open': None, 'high': None, 'low': None, 'close': float(level_price),
                    'atr': None,
                    'is_counter_ema': False,
                    'is_dim': False,
                    'dim_reason': None,
                    'conf': None,
                    'check_result': None,
                })
                continue

            # ── CONF line ──
            m = CONF_PATTERN.search(message)
            if m:
                time_str, dir_char, brk_type, result, detail = m.groups()
                confs.append({
                    'timestamp': ts,
                    'time_str': time_str,
                    'direction': 'bull' if dir_char == '▲' else 'bear',
                    'type': brk_type,
                    'result': result,
                    'detail': detail,
                })
                continue

            # ── 5m CHECK line ──
            m = CHECK_PATTERN.search(message)
            if m:
                time_str, dir_char, pnl_str, spy_str, action = m.groups()
                checks.append({
                    'timestamp': ts,
                    'time_str': time_str,
                    'direction': 'bull' if dir_char == '▲' else 'bear',
                    'pnl': float(pnl_str),
                    'spy': spy_str,
                    'action': action,
                })
                continue

            # ── QBS signal ──
            m = QBS_PATTERN.search(message)
            if m:
                (time_str, direction_char, ramp_str, vol_str, pos_str,
                 vwap_str, ema_str, adx_str, body_str, range_atr_str,
                 flags_str, o, h, l, c, atr_str) = m.groups()

                flags = flags_str.strip()
                is_dim = 'dim' in flags or 'moddim' in flags

                signals.append({
                    'timestamp': ts,
                    'time_str': time_str,
                    'direction': 'bull' if direction_char == '▲' else 'bear',
                    'sig_type': 'QBS',
                    'levels': 'QBS',
                    'vol_ratio': float(vol_str),
                    'close_pos': pos_str,
                    'vwap': vwap_str,
                    'ema': ema_str,
                    'rs': None,
                    'adx': int(adx_str) if adx_str != 'na' else None,
                    'body_pct': int(body_str),
                    'ramp': float(ramp_str),
                    'range_atr': float(range_atr_str),
                    'is_big_move': '⚡' in flags,
                    'is_vol_drying': True,  # QBS always has vol drying
                    'is_body_warn': '⚠' in flags,
                    'open': float(o), 'high': float(h),
                    'low': float(l), 'close': float(c),
                    'atr': float(atr_str),
                    'is_counter_ema': False,
                    'is_dim': is_dim,
                    'dim_reason': 'qbs_dim' if 'dim' in flags else ('qbs_moddim' if 'moddim' in flags else None),
                    'conf': None,
                    'check_result': None,
                })
                continue

            # ── Main BRK/REV signal ──
            m = SIG_PATTERN.search(message)
            if m:
                (time_str, direction_char, type_levels, vol_str, pos_str,
                 vwap_str, ema_str, rs_str, adx_str, body_str,
                 ramp_str, range_atr_str, flags_and_rest,
                 o, h, l, c, atr_str) = m.groups()

                sig_type, levels_str, _, is_counter_ema = parse_type_and_levels(type_levels)
                flags = flags_and_rest.strip()

                # Detect dim indicators from log context:
                # The log itself doesn't explicitly say "dimmed" for BRK/REV signals.
                # We infer dim status from:
                #   - vol > 5x (vol exhaust dim)
                #   - counter-EMA (x~ prefix)
                #   - 🔇 = vol drying (this is a glyph, not dim)
                # We'll compute dim conditions in post-processing
                vol_ratio = float(vol_str)
                range_atr = float(range_atr_str)
                ramp = float(ramp_str)
                body_pct = int(body_str)

                signals.append({
                    'timestamp': ts,
                    'time_str': time_str,
                    'direction': 'bull' if direction_char == '▲' else 'bear',
                    'sig_type': sig_type,
                    'levels': levels_str,
                    'vol_ratio': vol_ratio,
                    'close_pos': pos_str,
                    'vwap': vwap_str,
                    'ema': ema_str,
                    'rs': rs_str,
                    'adx': int(adx_str) if adx_str != 'na' else None,
                    'body_pct': body_pct,
                    'ramp': ramp,
                    'range_atr': range_atr,
                    'is_big_move': '⚡' in flags,
                    'is_vol_drying': '🔇' in message,
                    'is_body_warn': '⚠' in flags,
                    'open': float(o), 'high': float(h),
                    'low': float(l), 'close': float(c),
                    'atr': float(atr_str),
                    'is_counter_ema': is_counter_ema,
                    'is_dim': False,  # computed in post-processing
                    'dim_reason': None,
                    'conf': None,
                    'check_result': None,
                })
                continue

    # ── Attach CONF results to signals ──
    # Match CONF to the most recent signal of same direction within 1 bar
    for conf in confs:
        # Find matching signal: same direction, same timestamp (or just before)
        best = None
        for sig in signals:
            if sig['direction'] != conf['direction']:
                continue
            if sig['sig_type'] not in ('BRK', 'QBS'):
                continue
            dt = abs((conf['timestamp'] - sig['timestamp']).total_seconds())
            if dt <= 300:  # within 5 minutes
                if best is None or dt < abs((conf['timestamp'] - best['timestamp']).total_seconds()):
                    best = sig
        if best is not None:
            best['conf'] = conf['result']

    # ── Attach 5m CHECK results ──
    for chk in checks:
        best = None
        for sig in signals:
            if sig['direction'] != chk['direction']:
                continue
            if sig['conf'] is None:
                continue
            dt = (chk['timestamp'] - sig['timestamp']).total_seconds()
            if 0 <= dt <= 600:  # within 10 min after signal
                if best is None or dt < (chk['timestamp'] - best['timestamp']).total_seconds():
                    best = sig
        if best is not None:
            best['check_result'] = chk['action']

    return signals


def identify_symbol(signals, bar_dir=BAR_DIR, symbols=SYMBOLS):
    """Identify which symbol a log file belongs to by matching prices to daily bars.

    Strategy: Take the first few signals with OHLC data, get the date, and compare
    the close price against daily bars for each symbol. Best match wins.
    """
    # Get first few signals with close prices
    samples = [s for s in signals if s.get('close') is not None and s.get('atr') is not None][:10]
    if not samples:
        return None

    best_sym = None
    best_score = float('inf')

    for sym in symbols:
        fp = bar_dir / f'{sym.lower()}_1_day_ib.parquet'
        if not fp.exists():
            continue
        try:
            daily = pd.read_parquet(fp)
            dt = pd.to_datetime(daily['date'])
            if dt.dt.tz is not None:
                dt = dt.dt.tz_convert('US/Eastern')
            daily['date'] = dt
            daily = daily.set_index('date').sort_index()
        except:
            continue

        total_err = 0
        matched = 0
        for sig in samples:
            sig_date = sig['timestamp'].date() if hasattr(sig['timestamp'], 'date') else None
            if sig_date is None:
                continue

            # Find closest daily bar
            day_bars = daily[daily.index.date == sig_date]
            if len(day_bars) == 0:
                # Try nearby dates
                continue

            # Compare close prices
            daily_close = day_bars['close'].iloc[0]
            sig_close = sig['close']
            if daily_close > 0:
                pct_err = abs(sig_close - daily_close) / daily_close
                total_err += pct_err
                matched += 1

        if matched > 0:
            avg_err = total_err / matched
            if avg_err < best_score:
                best_score = avg_err
                best_sym = sym

    # Sanity check: error should be < 5%
    if best_score > 0.05:
        return None
    return best_sym


# ── IB Data Loading ──────────────────────────────────────────────────────────

def load_1m(symbol):
    """Load 1-minute bars from IB cache. Already in US/Eastern."""
    fp = BAR_DIR / f'{symbol.lower()}_1_min_ib.parquet'
    df = pd.read_parquet(fp)
    dt = pd.to_datetime(df['date'])
    if dt.dt.tz is None:
        dt = dt.dt.tz_localize('US/Eastern')
    elif str(dt.dt.tz) != 'US/Eastern':
        dt = dt.dt.tz_convert('US/Eastern')
    df['date'] = dt
    df = df.set_index('date').sort_index()
    # RTH filter: 9:30-16:00 ET
    df = df.between_time('09:30', '15:59')
    return df


def load_daily(symbol):
    """Load daily bars for ATR computation."""
    fp = BAR_DIR / f'{symbol.lower()}_1_day_ib.parquet'
    df = pd.read_parquet(fp)
    dt = pd.to_datetime(df['date'])
    if dt.dt.tz is not None:
        dt = dt.dt.tz_convert('US/Eastern')
    df['date'] = dt
    df = df.set_index('date').sort_index()
    return df


def compute_atr(daily_df, period=ATR_PERIOD):
    """Compute 14-period ATR from daily bars. Returns Series indexed by date."""
    tr = pd.DataFrame({
        'hl': daily_df['high'] - daily_df['low'],
        'hc': (daily_df['high'] - daily_df['close'].shift(1)).abs(),
        'lc': (daily_df['low'] - daily_df['close'].shift(1)).abs()
    })
    tr['tr'] = tr.max(axis=1)
    atr = tr['tr'].ewm(span=period, adjust=False).mean()
    atr.index = atr.index.date
    return atr


# ── MFE/MAE Measurement ─────────────────────────────────────────────────────

def measure_mfe_mae(signals, bars_1m, atr_series):
    """For each signal, measure MFE and MAE over MFE_MINUTES using 1m bars.

    Args:
        signals: list of signal dicts (with 'timestamp', 'direction', 'close', 'atr')
        bars_1m: DataFrame of 1m bars indexed by datetime
        atr_series: Series of daily ATR indexed by date

    Mutates signals in place, adding mfe/mae fields.
    """
    for sig in signals:
        ts = sig['timestamp']
        direction = sig['direction']
        entry = sig.get('close')
        atr = sig.get('atr')

        # Use ATR from signal or from daily series
        if atr is None or atr == 0:
            sig_date = ts.date() if hasattr(ts, 'date') else None
            if sig_date and sig_date in atr_series.index:
                atr = atr_series[sig_date]
            else:
                atr = None

        if entry is None or atr is None or atr == 0:
            sig.update({'mfe': 0, 'mae': 0, 'mfe_atr': 0, 'mae_atr': 0,
                        'pnl_atr': 0, 'outcome': 'FLAT', 'bars_to_mfe': 0})
            continue

        # Convert Pine timestamp to match IB data timezone
        # Pine logs are in ET (America/New_York), IB data is US/Eastern (same)
        if ts.tzinfo is None:
            ts_et = pd.Timestamp(ts, tz='US/Eastern')
        else:
            ts_et = ts.tz_convert('US/Eastern')

        # Find the signal bar's end time and measure from next bar
        # Signal fires on 5m bar close, so entry is at the 5m bar's close time
        # Next 1m bar starts at signal_time + 1 min
        start_time = ts_et + pd.Timedelta(minutes=1)
        end_time = ts_et + pd.Timedelta(minutes=MFE_MINUTES)

        # Also cap at 16:00 ET (end of RTH)
        eod = ts_et.normalize() + pd.Timedelta(hours=16)
        end_time = min(end_time, eod)

        # Get forward bars
        mask = (bars_1m.index >= start_time) & (bars_1m.index <= end_time)
        forward = bars_1m[mask]

        if len(forward) == 0:
            sig.update({'mfe': 0, 'mae': 0, 'mfe_atr': 0, 'mae_atr': 0,
                        'pnl_atr': 0, 'outcome': 'FLAT', 'bars_to_mfe': 0})
            continue

        # Compute MFE and MAE
        if direction == 'bull':
            fav_excursions = forward['high'] - entry
            adv_excursions = entry - forward['low']
        else:
            fav_excursions = entry - forward['low']
            adv_excursions = forward['high'] - entry

        mfe = fav_excursions.max()
        mae = adv_excursions.max()
        mfe = max(0, mfe)
        mae = max(0, mae)

        # Bars to MFE (index of max favorable excursion)
        if mfe > 0:
            bars_to_mfe = fav_excursions.idxmax()
            bars_to_mfe = int((bars_to_mfe - start_time).total_seconds() / 60) + 1
        else:
            bars_to_mfe = 0

        mfe_atr = mfe / atr
        mae_atr = mae / atr
        pnl_atr = mfe_atr - mae_atr

        # Outcome classification
        if mfe_atr >= WIN_MFE_THRESHOLD and mfe > mae:
            outcome = 'WIN'
        elif mae_atr > mfe_atr and mae_atr >= WIN_MFE_THRESHOLD:
            outcome = 'LOSS'
        else:
            outcome = 'FLAT'

        sig.update({
            'mfe': mfe, 'mae': mae,
            'mfe_atr': mfe_atr, 'mae_atr': mae_atr,
            'pnl_atr': pnl_atr, 'outcome': outcome,
            'bars_to_mfe': bars_to_mfe,
        })


# ── Dim Status Computation ──────────────────────────────────────────────────

def compute_dim_status(signals):
    """Compute which signals would be dimmed by v3.3 quality filters.

    v3.3 dim conditions (from Pine code line 1421):
      isDimBull = ((Dim mode + no evidence stack) or isVolModerate or emaGateDim
                   or isRegimeDim or isVolExhaust or isExhausted or isFreshDim)
                  AND NOT isQuietCoil AND NOT isMiddayFlat AND NOT isBroadCoil

    We can approximate:
      - isVolExhaust: vol > 5x
      - isVolModerate: ramp 1.0-2.0x (for QBS only)
      - is_counter_ema: x~ prefix (ema gate dim)
      - isFreshDim: level tested 3+ times today (tracked by count)
      - isExhausted: afternoon + large range + big SPY move (approximate)
      - isQuietCoil: vol drying (🔇) + rangeATR < 0.5
      - isMiddayFlat: midday + flat EMA (we can't fully detect from logs)
      - isBroadCoil: small range + SPY moving (approximate from rangeATR + rs)

    We infer what we can from log fields.
    """
    # Track level fire counts per day for freshness
    daily_level_counts = {}  # (date, level) -> count

    for sig in signals:
        sig_date = sig['timestamp'].date() if hasattr(sig['timestamp'], 'date') else None
        time_str = sig.get('time_str', '')
        vol = sig.get('vol_ratio') or 0
        range_atr = sig.get('range_atr') or 0
        ramp = sig.get('ramp') or 0
        ema = sig.get('ema')
        direction = sig.get('direction')
        levels = sig.get('levels', '')
        sig_type = sig.get('sig_type', '')

        # Parse hour
        try:
            parts = time_str.split(':')
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
        except:
            hour = 12
            minute = 0

        dim_reasons = []

        # 1. Vol exhaust dim: vol > 5x
        if vol > 5.0:
            dim_reasons.append('vol_exhaust')

        # 2. Counter-EMA (ema gate dim)
        if sig.get('is_counter_ema'):
            dim_reasons.append('counter_ema')

        # 3. EMA misaligned (after 9:50, direction != ema)
        is_post_950 = (hour > 9) or (hour == 9 and minute >= 50)
        if is_post_950 and ema is not None and ema != 'na':
            ema_aligned = (direction == 'bull' and ema == 'bull') or \
                          (direction == 'bear' and ema == 'bear')
            if not ema_aligned and sig_type not in ('RNG', 'FADE'):
                dim_reasons.append('ema_dim')

        # 4. Level freshness: track per-day level counts
        if sig_date and levels:
            key = (sig_date, levels)
            daily_level_counts[key] = daily_level_counts.get(key, 0) + 1
            if daily_level_counts[key] >= 3:
                dim_reasons.append('freshness')

        # 5. Exhaustion: afternoon (1pm+) + big range consumed
        if hour >= 13 and range_atr > 1.5:
            dim_reasons.append('exhaustion')

        # ── Override conditions (cancel dim) ──
        is_quiet_coil = sig.get('is_vol_drying', False) and range_atr < 0.5
        is_midday_flat = (11 <= hour < 14)  # approximate
        is_broad_coil = range_atr < 0.5  # approximate (can't check SPY from here)

        overrides = []
        if is_quiet_coil:
            overrides.append('quiet_coil')
        if is_broad_coil and range_atr < 0.5:
            overrides.append('broad_coil')

        # Set dim status
        if dim_reasons and not overrides:
            sig['is_dim'] = True
            sig['dim_reason'] = ','.join(dim_reasons)
        elif dim_reasons and overrides:
            sig['is_dim'] = False
            sig['dim_reason'] = f"override({','.join(overrides)})"
        else:
            sig['is_dim'] = False
            sig['dim_reason'] = None

    return signals


# ── Main ─────────────────────────────────────────────────────────────────────

def load_and_parse_logs(version='v33'):
    """Load all Pine log files for a version, parse signals, identify symbols."""
    pattern = V33_GLOB if version == 'v33' else V32_GLOB
    files = sorted(glob.glob(str(LOG_DIR / pattern)))

    all_signals = []
    symbol_map = {}  # filepath -> symbol

    print(f'  Found {len(files)} {version} log files')

    for fp in files:
        short = Path(fp).name.split('_')[-1].replace('.csv', '')
        signals = parse_pine_log(fp)

        if not signals:
            print(f'    {short}: 0 signals (empty)')
            continue

        # Identify symbol
        symbol = identify_symbol(signals)
        if symbol is None:
            print(f'    {short}: could not identify symbol (price mismatch)')
            continue

        symbol_map[fp] = symbol

        # Tag signals with symbol and version
        for s in signals:
            s['symbol'] = symbol
            s['version'] = version
            s['log_file'] = short

        all_signals.extend(signals)
        print(f'    {short}: {symbol} — {len(signals)} signals')

    return all_signals, symbol_map


def run_backtest():
    """Run the full v3.3 backtest with MFE/MAE from 1m IB data."""
    print('='*70)
    print('KLB v3.3 Backtest — Pine Logs + IB 1m MFE/MAE')
    print('='*70)
    print()

    # ── Parse v3.3 logs ──
    print('Parsing v3.3 logs...')
    signals_v33, sym_map_v33 = load_and_parse_logs('v33')
    print(f'  Total v3.3 signals: {len(signals_v33)}')
    print()

    # ── Parse v3.2 logs ──
    print('Parsing v3.2 logs...')
    signals_v32, sym_map_v32 = load_and_parse_logs('v32')
    print(f'  Total v3.2 signals: {len(signals_v32)}')
    print()

    # ── Compute dim status for v3.3 ──
    print('Computing dim status...')
    signals_v33 = compute_dim_status(signals_v33)

    # ── Load IB data and measure MFE/MAE ──
    symbols_seen = sorted(set(s['symbol'] for s in signals_v33))
    print(f'Symbols in v3.3: {symbols_seen}')
    print()

    ib_cache = {}  # symbol -> (bars_1m, atr_series)

    for sym in symbols_seen:
        print(f'  Loading IB 1m data for {sym}...', end=' ', flush=True)
        try:
            bars_1m = load_1m(sym)
            daily = load_daily(sym)
            atr_series = compute_atr(daily)
            ib_cache[sym] = (bars_1m, atr_series)
            print(f'{len(bars_1m)} bars, {len(atr_series)} ATR values')
        except Exception as e:
            print(f'ERROR: {e}')

    # ── Measure MFE/MAE for v3.3 signals ──
    print('\nMeasuring MFE/MAE for v3.3 signals...')
    for sym in symbols_seen:
        if sym not in ib_cache:
            continue
        bars_1m, atr_series = ib_cache[sym]
        sym_signals = [s for s in signals_v33 if s['symbol'] == sym]
        measure_mfe_mae(sym_signals, bars_1m, atr_series)
        matched = sum(1 for s in sym_signals if s.get('mfe_atr', 0) != 0 or s.get('mae_atr', 0) != 0)
        print(f'  {sym}: {len(sym_signals)} signals, {matched} with MFE/MAE data')

    # ── Measure MFE/MAE for v3.2 signals ──
    print('\nMeasuring MFE/MAE for v3.2 signals...')
    for sym in set(s['symbol'] for s in signals_v32):
        if sym not in ib_cache:
            # Load if not already loaded
            try:
                bars_1m = load_1m(sym)
                daily = load_daily(sym)
                atr_series = compute_atr(daily)
                ib_cache[sym] = (bars_1m, atr_series)
            except:
                continue
        bars_1m, atr_series = ib_cache[sym]
        sym_signals = [s for s in signals_v32 if s['symbol'] == sym]
        measure_mfe_mae(sym_signals, bars_1m, atr_series)
        matched = sum(1 for s in sym_signals if s.get('mfe_atr', 0) != 0 or s.get('mae_atr', 0) != 0)
        print(f'  {sym}: {len(sym_signals)} signals, {matched} with MFE/MAE data')

    # ── Generate report ──
    print('\nGenerating report...')
    report = generate_report(signals_v33, signals_v32)

    report_path = OUT_DIR / 'v33-backtest-results.md'
    with open(report_path, 'w') as f:
        f.write(report)
    print(f'\nReport saved to: {report_path}')

    return signals_v33, signals_v32


# ── Report Generation ────────────────────────────────────────────────────────

def sig_stats(signals, label=''):
    """Compute aggregate stats for signal list."""
    if not signals:
        return {'n': 0, 'wins': 0, 'losses': 0, 'flats': 0, 'win_rate': 0,
                'avg_mfe': 0, 'avg_mae': 0, 'net_atr': 0, 'avg_pnl': 0, 'label': label}
    n = len(signals)
    wins = sum(1 for s in signals if s.get('outcome') == 'WIN')
    losses = sum(1 for s in signals if s.get('outcome') == 'LOSS')
    flats = sum(1 for s in signals if s.get('outcome') == 'FLAT')
    avg_mfe = np.mean([s.get('mfe_atr', 0) for s in signals])
    avg_mae = np.mean([s.get('mae_atr', 0) for s in signals])
    net_atr = sum(s.get('pnl_atr', 0) for s in signals)
    avg_pnl = net_atr / n if n > 0 else 0
    win_rate = wins / n * 100 if n > 0 else 0
    return {
        'n': n, 'wins': wins, 'losses': losses, 'flats': flats,
        'win_rate': win_rate, 'avg_mfe': avg_mfe, 'avg_mae': avg_mae,
        'net_atr': net_atr, 'avg_pnl': avg_pnl, 'label': label
    }


def format_sig(s):
    """Format a signal for display."""
    ts = s.get('timestamp', '')
    if hasattr(ts, 'strftime'):
        ts = ts.strftime('%Y-%m-%d %H:%M')
    return (f"{s.get('symbol','?')} {ts} {s.get('sig_type','?')} {s.get('direction','?')} "
            f"{s.get('levels','?')} vol={s.get('vol_ratio','?')}x "
            f"MFE={s.get('mfe_atr',0):.3f} MAE={s.get('mae_atr',0):.3f} "
            f"P&L={s.get('pnl_atr',0):.3f} [{s.get('outcome','?')}]"
            f"{' DIM:'+s.get('dim_reason','') if s.get('is_dim') else ''}")


def generate_report(signals_v33, signals_v32):
    """Generate full markdown report."""
    L = []  # lines

    # ── Filter to signals with MFE/MAE data ──
    v33_with_data = [s for s in signals_v33 if s.get('mfe_atr') is not None]
    v32_with_data = [s for s in signals_v32 if s.get('mfe_atr') is not None]

    L.append('# KLB v3.3 Backtest Results')
    L.append(f'**Date:** {datetime.now().strftime("%Y-%m-%d")}')
    L.append(f'**Data:** Pine logs → IB 1m bars, {MFE_MINUTES}-min MFE/MAE window')
    L.append(f'**Symbols:** {", ".join(sorted(set(s["symbol"] for s in signals_v33)))}')
    L.append(f'**v3.3 signals:** {len(signals_v33)} parsed, {len(v33_with_data)} with MFE/MAE')
    L.append(f'**v3.2 signals:** {len(signals_v32)} parsed, {len(v32_with_data)} with MFE/MAE')
    L.append('')

    # ════════════════════════════════════════════════════════════════════════
    # 1. OVERALL SUMMARY
    # ════════════════════════════════════════════════════════════════════════
    st33 = sig_stats(v33_with_data, 'v3.3')
    st32 = sig_stats(v32_with_data, 'v3.2')

    L.append('## 1. Overall Summary')
    L.append('')
    L.append('| Metric | v3.2 | v3.3 | Delta |')
    L.append('|--------|------|------|-------|')
    L.append(f'| Total Signals | {st32["n"]} | {st33["n"]} | {st33["n"] - st32["n"]:+d} |')
    L.append(f'| Win Rate | {st32["win_rate"]:.1f}% | {st33["win_rate"]:.1f}% | {st33["win_rate"] - st32["win_rate"]:+.1f}pp |')
    L.append(f'| Avg MFE (ATR) | {st32["avg_mfe"]:.4f} | {st33["avg_mfe"]:.4f} | {st33["avg_mfe"] - st32["avg_mfe"]:+.4f} |')
    L.append(f'| Avg MAE (ATR) | {st32["avg_mae"]:.4f} | {st33["avg_mae"]:.4f} | {st33["avg_mae"] - st32["avg_mae"]:+.4f} |')
    L.append(f'| Avg P&L/sig (ATR) | {st32["avg_pnl"]:.4f} | {st33["avg_pnl"]:.4f} | {st33["avg_pnl"] - st32["avg_pnl"]:+.4f} |')
    L.append(f'| Net ATR | {st32["net_atr"]:.1f} | {st33["net_atr"]:.1f} | {st33["net_atr"] - st32["net_atr"]:+.1f} |')
    L.append('')

    # ════════════════════════════════════════════════════════════════════════
    # 2. BY SIGNAL TYPE
    # ════════════════════════════════════════════════════════════════════════
    L.append('## 2. By Signal Type')
    L.append('')

    all_types = sorted(set(s.get('sig_type', '?') for s in v33_with_data))
    L.append('### v3.3 Signal Types')
    L.append('')
    L.append('| Type | N | Win% | Avg MFE | Avg MAE | Avg P&L | Net ATR |')
    L.append('|------|:-:|:----:|:-------:|:-------:|:-------:|:-------:|')
    for t in all_types:
        sigs = [s for s in v33_with_data if s.get('sig_type') == t]
        st = sig_stats(sigs)
        L.append(f'| {t} | {st["n"]} | {st["win_rate"]:.1f}% | {st["avg_mfe"]:.4f} | '
                 f'{st["avg_mae"]:.4f} | {st["avg_pnl"]:.4f} | {st["net_atr"]:+.1f} |')
    L.append('')

    # v3.2 types for comparison
    all_types_32 = sorted(set(s.get('sig_type', '?') for s in v32_with_data))
    if v32_with_data:
        L.append('### v3.2 Signal Types (comparison)')
        L.append('')
        L.append('| Type | N | Win% | Avg MFE | Avg MAE | Avg P&L | Net ATR |')
        L.append('|------|:-:|:----:|:-------:|:-------:|:-------:|:-------:|')
        for t in all_types_32:
            sigs = [s for s in v32_with_data if s.get('sig_type') == t]
            st = sig_stats(sigs)
            L.append(f'| {t} | {st["n"]} | {st["win_rate"]:.1f}% | {st["avg_mfe"]:.4f} | '
                     f'{st["avg_mae"]:.4f} | {st["avg_pnl"]:.4f} | {st["net_atr"]:+.1f} |')
        L.append('')

    # ════════════════════════════════════════════════════════════════════════
    # 3. BY SYMBOL
    # ════════════════════════════════════════════════════════════════════════
    L.append('## 3. By Symbol')
    L.append('')
    L.append('| Symbol | v3.3 N | Win% | Avg MFE | Avg MAE | Net ATR | v3.2 N | v3.2 ATR | Delta |')
    L.append('|--------|:------:|:----:|:-------:|:-------:|:-------:|:------:|:--------:|:-----:|')

    for sym in SYMBOLS:
        s33 = [s for s in v33_with_data if s['symbol'] == sym]
        s32 = [s for s in v32_with_data if s['symbol'] == sym]
        st33 = sig_stats(s33)
        st32 = sig_stats(s32)
        delta = st33['net_atr'] - st32['net_atr']
        L.append(f'| {sym} | {st33["n"]} | {st33["win_rate"]:.1f}% | {st33["avg_mfe"]:.4f} | '
                 f'{st33["avg_mae"]:.4f} | {st33["net_atr"]:+.1f} | {st32["n"]} | {st32["net_atr"]:+.1f} | {delta:+.1f} |')
    L.append('')

    # ════════════════════════════════════════════════════════════════════════
    # 4. BY TIMING
    # ════════════════════════════════════════════════════════════════════════
    L.append('## 4. By Time of Day')
    L.append('')

    def get_hour(s):
        try:
            return int(s.get('time_str', '12:00').split(':')[0])
        except:
            return 12

    hours = sorted(set(get_hour(s) for s in v33_with_data))
    L.append('| Hour (ET) | N | Win% | Avg MFE | Avg MAE | Avg P&L | Net ATR |')
    L.append('|:---------:|:-:|:----:|:-------:|:-------:|:-------:|:-------:|')
    for h in hours:
        h_sigs = [s for s in v33_with_data if get_hour(s) == h]
        st = sig_stats(h_sigs)
        L.append(f'| {h:02d}:xx | {st["n"]} | {st["win_rate"]:.1f}% | {st["avg_mfe"]:.4f} | '
                 f'{st["avg_mae"]:.4f} | {st["avg_pnl"]:.4f} | {st["net_atr"]:+.1f} |')
    L.append('')

    # Timing buckets: Morning (9:30-11), Midday (11-14), Afternoon (14-16)
    L.append('### Timing Buckets')
    L.append('')
    buckets = [
        ('Morning 9:30-11', lambda s: get_hour(s) < 11),
        ('Midday 11-14', lambda s: 11 <= get_hour(s) < 14),
        ('Afternoon 14-16', lambda s: get_hour(s) >= 14),
    ]
    L.append('| Bucket | N | Win% | Avg P&L | Net ATR |')
    L.append('|--------|:-:|:----:|:-------:|:-------:|')
    for name, filt in buckets:
        b_sigs = [s for s in v33_with_data if filt(s)]
        st = sig_stats(b_sigs)
        L.append(f'| {name} | {st["n"]} | {st["win_rate"]:.1f}% | {st["avg_pnl"]:.4f} | {st["net_atr"]:+.1f} |')
    L.append('')

    # ════════════════════════════════════════════════════════════════════════
    # 5. DIM vs NON-DIM PERFORMANCE (v3.3 quality filters)
    # ════════════════════════════════════════════════════════════════════════
    L.append('## 5. Dim vs Non-Dim Performance (v3.3 Quality Filters)')
    L.append('')
    L.append('Signals dimmed by v3.3 filters should have WORSE performance than non-dimmed.')
    L.append('If dimmed signals perform badly, the filters are working correctly.')
    L.append('')

    dimmed = [s for s in v33_with_data if s.get('is_dim')]
    not_dimmed = [s for s in v33_with_data if not s.get('is_dim')]

    st_dim = sig_stats(dimmed, 'Dimmed')
    st_ndim = sig_stats(not_dimmed, 'Not Dimmed')

    L.append('| Status | N | Win% | Avg MFE | Avg MAE | Avg P&L | Net ATR |')
    L.append('|--------|:-:|:----:|:-------:|:-------:|:-------:|:-------:|')
    L.append(f'| Not Dimmed | {st_ndim["n"]} | {st_ndim["win_rate"]:.1f}% | {st_ndim["avg_mfe"]:.4f} | '
             f'{st_ndim["avg_mae"]:.4f} | {st_ndim["avg_pnl"]:.4f} | {st_ndim["net_atr"]:+.1f} |')
    L.append(f'| Dimmed | {st_dim["n"]} | {st_dim["win_rate"]:.1f}% | {st_dim["avg_mfe"]:.4f} | '
             f'{st_dim["avg_mae"]:.4f} | {st_dim["avg_pnl"]:.4f} | {st_dim["net_atr"]:+.1f} |')
    L.append('')

    # ── By dim reason ──
    L.append('### By Dim Reason')
    L.append('')
    dim_reasons = {}
    for s in v33_with_data:
        reason = s.get('dim_reason') or 'none'
        if reason not in dim_reasons:
            dim_reasons[reason] = []
        dim_reasons[reason].append(s)

    L.append('| Dim Reason | N | Win% | Avg P&L | Net ATR |')
    L.append('|------------|:-:|:----:|:-------:|:-------:|')
    for reason in sorted(dim_reasons.keys()):
        sigs = dim_reasons[reason]
        st = sig_stats(sigs)
        L.append(f'| {reason} | {st["n"]} | {st["win_rate"]:.1f}% | {st["avg_pnl"]:.4f} | {st["net_atr"]:+.1f} |')
    L.append('')

    # ── Vol exhaust specifically ──
    L.append('### Vol Exhaust Dim (vol > 5x)')
    L.append('')
    vol_exh = [s for s in v33_with_data if s.get('vol_ratio') and s['vol_ratio'] > 5.0]
    vol_norm = [s for s in v33_with_data if s.get('vol_ratio') and s['vol_ratio'] <= 5.0]
    st_exh = sig_stats(vol_exh, 'Vol > 5x')
    st_norm = sig_stats(vol_norm, 'Vol <= 5x')

    L.append('| Group | N | Win% | Avg MFE | Avg MAE | Avg P&L | Net ATR |')
    L.append('|-------|:-:|:----:|:-------:|:-------:|:-------:|:-------:|')
    L.append(f'| Vol <= 5x | {st_norm["n"]} | {st_norm["win_rate"]:.1f}% | {st_norm["avg_mfe"]:.4f} | '
             f'{st_norm["avg_mae"]:.4f} | {st_norm["avg_pnl"]:.4f} | {st_norm["net_atr"]:+.1f} |')
    L.append(f'| Vol > 5x | {st_exh["n"]} | {st_exh["win_rate"]:.1f}% | {st_exh["avg_mfe"]:.4f} | '
             f'{st_exh["avg_mae"]:.4f} | {st_exh["avg_pnl"]:.4f} | {st_exh["net_atr"]:+.1f} |')
    L.append('')

    # ── Vol drying (🔇) ──
    L.append('### Vol Drying (🔇 = ramp < 0.5x)')
    L.append('')
    vol_dry = [s for s in v33_with_data if s.get('is_vol_drying')]
    vol_not_dry = [s for s in v33_with_data if not s.get('is_vol_drying')]
    st_dry = sig_stats(vol_dry)
    st_ndry = sig_stats(vol_not_dry)
    L.append('| Group | N | Win% | Avg P&L | Net ATR |')
    L.append('|-------|:-:|:----:|:-------:|:-------:|')
    L.append(f'| Normal vol | {st_ndry["n"]} | {st_ndry["win_rate"]:.1f}% | {st_ndry["avg_pnl"]:.4f} | {st_ndry["net_atr"]:+.1f} |')
    L.append(f'| Vol drying | {st_dry["n"]} | {st_dry["win_rate"]:.1f}% | {st_dry["avg_pnl"]:.4f} | {st_dry["net_atr"]:+.1f} |')
    L.append('')

    # ── Quiet Coil (vol drying + small range < 0.5 ATR) ──
    L.append('### Quiet Coil (vol drying + rangeATR < 0.5)')
    L.append('')
    quiet_coil = [s for s in v33_with_data
                  if s.get('is_vol_drying') and (s.get('range_atr') or 999) < 0.5]
    not_quiet = [s for s in v33_with_data
                 if not (s.get('is_vol_drying') and (s.get('range_atr') or 999) < 0.5)]
    st_qc = sig_stats(quiet_coil)
    st_nqc = sig_stats(not_quiet)
    L.append('| Group | N | Win% | Avg MFE | Avg MAE | Avg P&L | Net ATR |')
    L.append('|-------|:-:|:----:|:-------:|:-------:|:-------:|:-------:|')
    L.append(f'| Not Quiet Coil | {st_nqc["n"]} | {st_nqc["win_rate"]:.1f}% | {st_nqc["avg_mfe"]:.4f} | '
             f'{st_nqc["avg_mae"]:.4f} | {st_nqc["avg_pnl"]:.4f} | {st_nqc["net_atr"]:+.1f} |')
    L.append(f'| Quiet Coil | {st_qc["n"]} | {st_qc["win_rate"]:.1f}% | {st_qc["avg_mfe"]:.4f} | '
             f'{st_qc["avg_mae"]:.4f} | {st_qc["avg_pnl"]:.4f} | {st_qc["net_atr"]:+.1f} |')
    L.append('')

    if quiet_coil:
        L.append('**Quiet Coil signals (detail):**')
        for s in sorted(quiet_coil, key=lambda x: x.get('pnl_atr', 0), reverse=True)[:10]:
            L.append(f'- {format_sig(s)}')
        L.append('')

    # ════════════════════════════════════════════════════════════════════════
    # 6. CONF PASS ANALYSIS
    # ════════════════════════════════════════════════════════════════════════
    L.append('## 6. Confirmation (CONF) Analysis')
    L.append('')
    conf_pass = [s for s in v33_with_data if s.get('conf') in ('✓', '✓★')]
    conf_fail = [s for s in v33_with_data if s.get('conf') == '✗']
    conf_none = [s for s in v33_with_data if s.get('conf') is None]

    st_pass = sig_stats(conf_pass)
    st_fail = sig_stats(conf_fail)
    st_none = sig_stats(conf_none)

    L.append('| CONF Status | N | Win% | Avg P&L | Net ATR |')
    L.append('|-------------|:-:|:----:|:-------:|:-------:|')
    L.append(f'| Pass (✓/✓★) | {st_pass["n"]} | {st_pass["win_rate"]:.1f}% | {st_pass["avg_pnl"]:.4f} | {st_pass["net_atr"]:+.1f} |')
    L.append(f'| Fail (✗) | {st_fail["n"]} | {st_fail["win_rate"]:.1f}% | {st_fail["avg_pnl"]:.4f} | {st_fail["net_atr"]:+.1f} |')
    L.append(f'| No CONF | {st_none["n"]} | {st_none["win_rate"]:.1f}% | {st_none["avg_pnl"]:.4f} | {st_none["net_atr"]:+.1f} |')
    L.append('')

    # ── 5m CHECK BAIL analysis ──
    bail_sigs = [s for s in v33_with_data if s.get('check_result') == 'BAIL']
    hold_sigs = [s for s in v33_with_data if s.get('check_result') == 'HOLD']

    if bail_sigs or hold_sigs:
        L.append('### 5m Checkpoint (HOLD vs BAIL)')
        L.append('')
        st_hold = sig_stats(hold_sigs)
        st_bail = sig_stats(bail_sigs)
        L.append('| Action | N | Win% | Avg P&L | Net ATR |')
        L.append('|--------|:-:|:----:|:-------:|:-------:|')
        L.append(f'| HOLD | {st_hold["n"]} | {st_hold["win_rate"]:.1f}% | {st_hold["avg_pnl"]:.4f} | {st_hold["net_atr"]:+.1f} |')
        L.append(f'| BAIL | {st_bail["n"]} | {st_bail["win_rate"]:.1f}% | {st_bail["avg_pnl"]:.4f} | {st_bail["net_atr"]:+.1f} |')
        L.append('')

    # ════════════════════════════════════════════════════════════════════════
    # 7. v3.3 vs v3.2 COMPARISON
    # ════════════════════════════════════════════════════════════════════════
    L.append('## 7. v3.3 vs v3.2 Signal Comparison')
    L.append('')

    # Find signals unique to v3.3 or v3.2 by matching on (symbol, timestamp, direction)
    def sig_key(s):
        ts = s.get('timestamp')
        if hasattr(ts, 'strftime'):
            ts_str = ts.strftime('%Y-%m-%d %H:%M')
        else:
            ts_str = str(ts)
        return (s.get('symbol', '?'), ts_str, s.get('direction', '?'))

    v33_keys = set(sig_key(s) for s in signals_v33)
    v32_keys = set(sig_key(s) for s in signals_v32)

    new_in_v33 = v33_keys - v32_keys
    removed_in_v33 = v32_keys - v33_keys
    common = v33_keys & v32_keys

    L.append(f'- **Common signals:** {len(common)}')
    L.append(f'- **New in v3.3:** {len(new_in_v33)} (quiet coil EMA bypass, etc.)')
    L.append(f'- **Removed in v3.3:** {len(removed_in_v33)} (suppressed by new filters)')
    L.append('')

    # Performance of new v3.3 signals
    new_sigs = [s for s in v33_with_data if sig_key(s) in new_in_v33]
    if new_sigs:
        st_new = sig_stats(new_sigs)
        L.append('### New v3.3 Signals')
        L.append(f'N={st_new["n"]}, Win%={st_new["win_rate"]:.1f}%, '
                 f'Avg P&L={st_new["avg_pnl"]:.4f}, Net ATR={st_new["net_atr"]:+.1f}')
        L.append('')
        L.append('**Top 5:**')
        for s in sorted(new_sigs, key=lambda x: x.get('pnl_atr', 0), reverse=True)[:5]:
            L.append(f'- {format_sig(s)}')
        L.append('')
        L.append('**Bottom 5:**')
        for s in sorted(new_sigs, key=lambda x: x.get('pnl_atr', 0))[:5]:
            L.append(f'- {format_sig(s)}')
        L.append('')

    # Performance of removed signals (from v3.2 data)
    removed_sigs = [s for s in v32_with_data if sig_key(s) in removed_in_v33]
    if removed_sigs:
        st_rem = sig_stats(removed_sigs)
        L.append('### Removed from v3.2 (rightly dimmed/suppressed?)')
        L.append(f'N={st_rem["n"]}, Win%={st_rem["win_rate"]:.1f}%, '
                 f'Avg P&L={st_rem["avg_pnl"]:.4f}, Net ATR={st_rem["net_atr"]:+.1f}')
        L.append('')
        L.append('If these were losers, v3.3 filters are working correctly.')
        L.append('')

    # ── Changed signal types (same key, different sig_type) ──
    v33_by_key = {sig_key(s): s for s in v33_with_data}
    v32_by_key = {sig_key(s): s for s in v32_with_data}

    type_changes = []
    for k in common:
        s33 = v33_by_key.get(k)
        s32 = v32_by_key.get(k)
        if s33 and s32 and s33.get('sig_type') != s32.get('sig_type'):
            type_changes.append((s32, s33))

    if type_changes:
        L.append(f'### Signal Type Changes ({len(type_changes)} signals)')
        L.append('')
        L.append('| Symbol | Time | v3.2 Type | v3.3 Type | v3.3 P&L |')
        L.append('|--------|------|-----------|-----------|----------|')
        for s32, s33 in type_changes[:20]:
            ts = s33.get('timestamp', '')
            if hasattr(ts, 'strftime'):
                ts = ts.strftime('%m-%d %H:%M')
            L.append(f'| {s33.get("symbol")} | {ts} | {s32.get("sig_type")} | '
                     f'{s33.get("sig_type")} | {s33.get("pnl_atr", 0):+.3f} |')
        L.append('')

    # ════════════════════════════════════════════════════════════════════════
    # 8. LEVEL ANALYSIS
    # ════════════════════════════════════════════════════════════════════════
    L.append('## 8. By Level')
    L.append('')

    level_groups = {}
    for s in v33_with_data:
        lvl = s.get('levels', '?')
        if lvl not in level_groups:
            level_groups[lvl] = []
        level_groups[lvl].append(s)

    # Sort by count descending
    sorted_levels = sorted(level_groups.items(), key=lambda x: len(x[1]), reverse=True)

    L.append('| Level | N | Win% | Avg MFE | Avg MAE | Avg P&L | Net ATR |')
    L.append('|-------|:-:|:----:|:-------:|:-------:|:-------:|:-------:|')
    for lvl, sigs in sorted_levels[:25]:
        st = sig_stats(sigs)
        L.append(f'| {lvl} | {st["n"]} | {st["win_rate"]:.1f}% | {st["avg_mfe"]:.4f} | '
                 f'{st["avg_mae"]:.4f} | {st["avg_pnl"]:.4f} | {st["net_atr"]:+.1f} |')
    L.append('')

    # ════════════════════════════════════════════════════════════════════════
    # 9. BIG MOVE ANALYSIS (⚡ = rangeATR >= 2.0)
    # ════════════════════════════════════════════════════════════════════════
    L.append('## 9. Big Move Analysis (rangeATR >= 2.0)')
    L.append('')
    big = [s for s in v33_with_data if s.get('is_big_move')]
    not_big = [s for s in v33_with_data if not s.get('is_big_move')]
    st_big = sig_stats(big)
    st_nbig = sig_stats(not_big)
    L.append('| Group | N | Win% | Avg MFE | Avg MAE | Avg P&L | Net ATR |')
    L.append('|-------|:-:|:----:|:-------:|:-------:|:-------:|:-------:|')
    L.append(f'| Normal | {st_nbig["n"]} | {st_nbig["win_rate"]:.1f}% | {st_nbig["avg_mfe"]:.4f} | '
             f'{st_nbig["avg_mae"]:.4f} | {st_nbig["avg_pnl"]:.4f} | {st_nbig["net_atr"]:+.1f} |')
    L.append(f'| Big Move ⚡ | {st_big["n"]} | {st_big["win_rate"]:.1f}% | {st_big["avg_mfe"]:.4f} | '
             f'{st_big["avg_mae"]:.4f} | {st_big["avg_pnl"]:.4f} | {st_big["net_atr"]:+.1f} |')
    L.append('')

    # ════════════════════════════════════════════════════════════════════════
    # 10. TOP/BOTTOM SIGNALS
    # ════════════════════════════════════════════════════════════════════════
    L.append('## 10. Top 10 Best & Worst Signals')
    L.append('')

    sorted_by_pnl = sorted(v33_with_data, key=lambda s: s.get('pnl_atr', 0), reverse=True)

    L.append('### Top 10 Best')
    for s in sorted_by_pnl[:10]:
        L.append(f'- {format_sig(s)}')
    L.append('')

    L.append('### Top 10 Worst')
    for s in sorted_by_pnl[-10:]:
        L.append(f'- {format_sig(s)}')
    L.append('')

    # ════════════════════════════════════════════════════════════════════════
    # 11. EMA ALIGNMENT
    # ════════════════════════════════════════════════════════════════════════
    L.append('## 11. EMA Alignment')
    L.append('')

    ema_aligned = [s for s in v33_with_data
                   if s.get('ema') and s['ema'] != 'na'
                   and ((s['direction'] == 'bull' and s['ema'] == 'bull')
                     or (s['direction'] == 'bear' and s['ema'] == 'bear'))]
    ema_counter = [s for s in v33_with_data
                   if s.get('ema') and s['ema'] != 'na'
                   and not ((s['direction'] == 'bull' and s['ema'] == 'bull')
                         or (s['direction'] == 'bear' and s['ema'] == 'bear'))]

    st_aligned = sig_stats(ema_aligned)
    st_counter = sig_stats(ema_counter)

    L.append('| EMA | N | Win% | Avg MFE | Avg MAE | Avg P&L | Net ATR |')
    L.append('|-----|:-:|:----:|:-------:|:-------:|:-------:|:-------:|')
    L.append(f'| Aligned | {st_aligned["n"]} | {st_aligned["win_rate"]:.1f}% | {st_aligned["avg_mfe"]:.4f} | '
             f'{st_aligned["avg_mae"]:.4f} | {st_aligned["avg_pnl"]:.4f} | {st_aligned["net_atr"]:+.1f} |')
    L.append(f'| Counter | {st_counter["n"]} | {st_counter["win_rate"]:.1f}% | {st_counter["avg_mfe"]:.4f} | '
             f'{st_counter["avg_mae"]:.4f} | {st_counter["avg_pnl"]:.4f} | {st_counter["net_atr"]:+.1f} |')
    L.append('')

    # ════════════════════════════════════════════════════════════════════════
    # 12. DIRECTION (Bull vs Bear)
    # ════════════════════════════════════════════════════════════════════════
    L.append('## 12. Direction')
    L.append('')
    bulls = [s for s in v33_with_data if s['direction'] == 'bull']
    bears = [s for s in v33_with_data if s['direction'] == 'bear']
    st_bull = sig_stats(bulls)
    st_bear = sig_stats(bears)
    L.append('| Dir | N | Win% | Avg P&L | Net ATR |')
    L.append('|-----|:-:|:----:|:-------:|:-------:|')
    L.append(f'| Bull | {st_bull["n"]} | {st_bull["win_rate"]:.1f}% | {st_bull["avg_pnl"]:.4f} | {st_bull["net_atr"]:+.1f} |')
    L.append(f'| Bear | {st_bear["n"]} | {st_bear["win_rate"]:.1f}% | {st_bear["avg_pnl"]:.4f} | {st_bear["net_atr"]:+.1f} |')
    L.append('')

    return '\n'.join(L)


# ── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == '__main__':
    signals_v33, signals_v32 = run_backtest()
