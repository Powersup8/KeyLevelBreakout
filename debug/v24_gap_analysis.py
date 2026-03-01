#!/usr/bin/env python3
"""
v2.4 Gap Analysis — closes 6 open analysis gaps using pine logs + 5s candle data.
Output: debug/v24-gap-analysis.md
"""

import re
import os
import math
from collections import defaultdict
from datetime import datetime, timedelta
from statistics import mean, median

import pandas as pd

# ── Paths ────────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(BASE, "v24-gap-analysis.md")
_PROJ_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(BASE)))  # Claude/ dir
PARQ_5S_DIR = os.path.join(_PROJ_ROOT, "trading_bot", "cache", "bars_highres", "5sec")
PARQ_1M_DIR = os.path.join(_PROJ_ROOT, "trading_bot", "cache", "bars")

ALL_SYMBOLS = [
    "SPY", "AAPL", "AMD", "AMZN", "GLD", "GOOGL",
    "META", "MSFT", "NVDA", "QQQ", "SLV", "TSLA", "TSM",
]

# Verified file→symbol mapping using parquet ground truth (Jan-Feb 2026 prices)
# Fingerprinted by median close & ATR from each pine log vs 5s parquet price ranges
FILE_SYMBOL_MAP = {
    "82a0f": "SPY",    # median=689, range=677-698
    "42d0e": "AAPL",   # median=267, range=253-280
    "842b7": "AMD",    # median=213, range=195-259, ATR=11.6 (high vol)
    "95b93": "AMZN",   # median=210, range=197-247, ATR=6.6
    "1d173": "GLD",    # median=464, range=428-508
    "51c09": "GOOGL",  # median=320, range=298-347
    "484bf": "META",   # median=655, range=603-731
    "493eb": "MSFT",   # median=403, range=383-483
    "7759b": "NVDA",   # median=188, range=171-196
    "4e835": "QQQ",    # median=607, range=594-636
    "65f3b": "SLV",    # median=79,  range=65-109
    "83e42": "TSLA",   # median=416, range=391-440
    "369c4": "TSM",    # median=343, range=323-390
}

# ── Classification thresholds ────────────────────────────────────────────────
# GOOD: MFE > 0.5 ATR within 30m AND MFE > 2x MAE
# BAD:  MAE > 0.5 ATR within 15m


# ── Parsing pine logs ────────────────────────────────────────────────────────

def parse_time(ts_str):
    """Parse ISO timestamp string to datetime."""
    ts_str = ts_str.strip().strip('"')
    ts_str = re.sub(r'\.\d+', '', ts_str)  # remove milliseconds
    try:
        return datetime.fromisoformat(ts_str)
    except ValueError:
        return datetime.strptime(ts_str[:19], '%Y-%m-%dT%H:%M:%S')


def detect_symbol(filepath):
    """Detect symbol from filename suffix using verified mapping."""
    basename = os.path.basename(filepath)
    m = re.search(r'_([a-f0-9]+)\.csv$', basename)
    if m:
        suffix = m.group(1)
        return FILE_SYMBOL_MAP.get(suffix)
    return None


def load_pine_logs():
    """Load all pine log CSVs, detecting symbols via filename mapping. Returns list of signals."""
    import glob
    pattern = os.path.join(BASE, "pine-logs-Key Level Breakout_*.csv")
    files = sorted(glob.glob(pattern))

    all_signals = []
    conf_outcomes = []  # collect separately, then match

    for fpath in files:
        with open(fpath, 'r', encoding='utf-8') as f:
            raw_lines = f.readlines()

        # Join multi-line records
        joined = []
        for line in raw_lines[1:]:  # skip header
            line = line.rstrip('\n')
            if not line:
                continue
            if re.match(r'^"?202\d-', line):
                joined.append(line)
            elif joined:
                joined[-1] += ' ' + line

        symbol = detect_symbol(fpath)
        if not symbol:
            print(f"  WARN: Could not detect symbol for {os.path.basename(fpath)}, skipping")
            continue

        file_signals = []
        file_confs = []

        for raw in joined:
            # Split timestamp and message
            m = re.match(r'^"?([\dT:.+-]+)"?\s*,\s*"?\[KLB\]\s*(.*)', raw)
            if not m:
                continue
            ts = parse_time(m.group(1))
            msg = m.group(2).rstrip('"').strip()

            # ── CONF outcome ──
            conf_m = re.match(
                r'CONF\s+[\d:]+\s+([▲▼])\s+(BRK|~~|~)\s+→\s+(✓★|✓|✗)',
                msg
            )
            if conf_m:
                direction = 'bull' if conf_m.group(1) == '▲' else 'bear'
                sig_type = conf_m.group(2)
                raw_result = conf_m.group(3)
                conf_result = 'pass_star' if raw_result == '✓★' else ('pass' if raw_result == '✓' else 'fail')
                file_confs.append({
                    'timestamp': ts,
                    'date': ts.date(),
                    'direction': direction,
                    'sig_type': sig_type,
                    'result': conf_result,
                    'symbol': symbol,
                })
                continue

            # ── Signal: BRK / ~ / ~~ ──
            sig_m = re.match(
                r'[\d:]+\s+([▲▼])\s+(BRK|~~|~)\s+(?:~~|~|BRK)?\s*(.*)',
                msg
            )
            if not sig_m:
                continue

            direction = 'bull' if sig_m.group(1) == '▲' else 'bear'
            sig_type = sig_m.group(2)
            rest = sig_m.group(3).strip()

            # Extract fields via regex
            vol_m = re.search(r'vol=([\d.]+)x', rest)
            pos_m = re.search(r'pos=([v^])(\d+)', rest)
            vwap_m = re.search(r'vwap=(above|below)', rest)
            atr_m = re.search(r'ATR=([\d.]+)', rest)
            ohlc_m = re.search(r'O([\d.]+)\s+H([\d.]+)\s+L([\d.]+)\s+C([\d.]+)', rest)

            if not (vol_m and pos_m and atr_m and ohlc_m):
                continue

            vol_ratio = float(vol_m.group(1))
            pos_dir = pos_m.group(1)
            pos_val = int(pos_m.group(2))
            vwap = vwap_m.group(1) if vwap_m else None
            atr = float(atr_m.group(1))
            close_price = float(ohlc_m.group(4))

            # Extract levels (everything before vol=)
            level_part = re.split(r'\s+vol=', rest)[0]
            level_part = re.sub(r'^[~]+\s+', '', level_part).strip()
            # Remove secondary signal type markers like "+ ~ ORB L"
            level_part = re.sub(r'\+\s+~+\s+', '+ ', level_part)
            levels = [l.strip() for l in level_part.split('+') if l.strip()]

            sig = {
                'timestamp': ts,
                'date': ts.date(),
                'weekday': ts.strftime('%a'),
                'direction': direction,
                'type': sig_type,
                'levels': levels,
                'level_count': len(levels),
                'vol_ratio': vol_ratio,
                'pos_dir': pos_dir,
                'pos_val': pos_val,
                'vwap': vwap,
                'atr': atr,
                'close': close_price,
                'symbol': symbol,
                'conf': None,       # filled in below
                'conf_star': False,  # filled in below
            }
            file_signals.append(sig)

        # Match CONF outcomes to BRK signals
        # Each CONF applies to the most recent BRK (same date+direction) before it
        brk_sigs = sorted(
            [s for s in file_signals if s['type'] == 'BRK'],
            key=lambda s: s['timestamp']
        )
        confs_sorted = sorted(file_confs, key=lambda c: c['timestamp'])
        used_confs = set()
        for c_idx, c in enumerate(confs_sorted):
            # Find the most recent BRK before this CONF (same date+direction)
            best_brk = None
            for sig in reversed(brk_sigs):
                if (sig['date'] == c['date'] and
                    sig['direction'] == c['direction'] and
                    sig['timestamp'] <= c['timestamp'] and
                    sig['conf'] is None):  # not already matched
                    best_brk = sig
                    break
            if best_brk:
                best_brk['conf'] = c['result']
                best_brk['conf_star'] = c['result'] == 'pass_star'
                used_confs.add(c_idx)

        all_signals.extend(file_signals)
        conf_outcomes.extend(file_confs)
        print(f"  {symbol}: {len(file_signals)} signals, {len(file_confs)} CONFs")

    return all_signals, conf_outcomes


# ── Loading 5s candles ───────────────────────────────────────────────────────

def load_candles(symbol):
    """Load candle data for a symbol: 5s preferred, 1m as fallback.
    Returns (DataFrame indexed by datetime, bar_seconds)."""
    # Try 5s first
    fname_5s = f"{symbol.lower()}_5_secs_ib.parquet"
    fpath_5s = os.path.join(PARQ_5S_DIR, fname_5s)
    if os.path.exists(fpath_5s):
        df = pd.read_parquet(fpath_5s)
        df = df.set_index('date').sort_index()
        df = df.between_time('09:30', '15:59')
        return df, 5

    # Fallback to 1m
    fname_1m = f"{symbol.lower()}_1_min_ib.parquet"
    fpath_1m = os.path.join(PARQ_1M_DIR, fname_1m)
    if os.path.exists(fpath_1m):
        df = pd.read_parquet(fpath_1m)
        df = df.set_index('date').sort_index()
        df = df.between_time('09:30', '15:59')
        return df, 60

    return None, 0


def compute_excursions(sig, candles_df, bar_secs):
    """
    Compute MFE/MAE at various time windows.
    Adapts window sizes based on bar resolution (5s or 60s).
    Windows: 30s, 1m, 2m, 5m, 15m, 30m
    """
    ts = sig['timestamp']
    direction = sig['direction']
    entry = sig['close']
    atr = sig['atr']

    # Convert signal timestamp to match candle index timezone
    if ts.tzinfo is None:
        import pytz
        ts_tz = pytz.timezone('US/Eastern').localize(ts)
    else:
        ts_tz = ts

    # Window durations in seconds
    windows = {
        '30s': 30, '1m': 60, '2m': 120,
        '5m': 300, '15m': 900, '30m': 1800,
    }
    results = {}

    for label, duration_secs in windows.items():
        # Skip sub-minute windows for 1m data
        if bar_secs >= 60 and duration_secs < 60:
            results[label] = None
            continue

        end_ts = ts_tz + timedelta(seconds=duration_secs)
        window_df = candles_df.loc[
            (candles_df.index > ts_tz) & (candles_df.index <= end_ts)
        ]

        if len(window_df) == 0:
            results[label] = None
            continue

        if direction == 'bull':
            mfe = window_df['high'].max() - entry
            mae = entry - window_df['low'].min()
        else:
            mfe = entry - window_df['low'].min()
            mae = window_df['high'].max() - entry

        mfe = max(mfe, 0)
        mae = max(mae, 0)

        results[label] = {
            'mfe': mfe,
            'mae': mae,
            'mfe_atr': mfe / atr if atr > 0 else 0,
            'mae_atr': mae / atr if atr > 0 else 0,
            'bars': len(window_df),
        }

    return results


def classify_signal(exc, atr):
    """Classify using standard thresholds. Returns GOOD/BAD/NEUTRAL."""
    # BAD: MAE > 0.5 ATR within 15m
    e15 = exc.get('15m')
    if e15 and e15['mae'] > 0.5 * atr:
        return 'BAD'

    # GOOD: MFE > 0.5 ATR within 30m AND MFE > 2x MAE
    e30 = exc.get('30m')
    if e30:
        mae_safe = max(e30['mae'], 0.001)
        if e30['mfe'] > 0.5 * atr and e30['mfe'] > 2 * mae_safe:
            return 'GOOD'

    return 'NEUTRAL'


# ── Helper functions ─────────────────────────────────────────────────────────

def time_bucket(ts):
    """Classify timestamp into time buckets."""
    t = ts.hour * 60 + ts.minute
    if t < 600:    # 10:00
        return '9:30-10'
    elif t < 660:  # 11:00
        return '10-11'
    elif t < 780:  # 13:00
        return '11-13'
    else:
        return '13-16'


def vol_bucket(vol):
    if vol >= 10:
        return '10x+'
    elif vol >= 5:
        return '5-10x'
    elif vol >= 2:
        return '2-5x'
    elif vol >= 1.5:
        return '1.5-2x'
    else:
        return '<1.5x'


def fmt_pct(num, denom):
    if denom == 0:
        return "—"
    return f"{100 * num / denom:.1f}%"


def fmt_table(headers, rows):
    """Format a markdown table."""
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    lines = []
    lines.append("| " + " | ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers)) + " |")
    lines.append("|" + "|".join("-" * (w + 2) for w in widths) + "|")
    for row in rows:
        lines.append("| " + " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(row)) + " |")
    return "\n".join(lines)


def wilson_ci(successes, n, z=1.96):
    """Wilson score confidence interval for a proportion."""
    if n == 0:
        return 0, 0, 1
    p_hat = successes / n
    denom = 1 + z * z / n
    center = (p_hat + z * z / (2 * n)) / denom
    spread = z * math.sqrt((p_hat * (1 - p_hat) + z * z / (4 * n)) / n) / denom
    lo = max(0, center - spread)
    hi = min(1, center + spread)
    return p_hat, lo, hi


# ── The 6 Analyses ───────────────────────────────────────────────────────────

def gap_a_jan29_cross_validation(signals):
    """Gap A: Do key findings hold without the Jan 29 monster day?"""
    lines = []
    lines.append("## Gap A: Jan 29 Cross-Validation")
    lines.append("")
    lines.append("**Question:** Do our key findings hold without the monster day?")
    lines.append("")

    jan29 = [s for s in signals if s['date'] == datetime(2026, 1, 29).date()]
    non_jan29 = [s for s in signals if s['date'] != datetime(2026, 1, 29).date()]

    lines.append(f"- Jan 29 signals: {len(jan29)}")
    lines.append(f"- All other days: {len(non_jan29)}")
    lines.append(f"- Total: {len(signals)}")
    lines.append("")

    # Compute metrics for full vs excluding Jan 29
    def metrics(subset, label):
        n = len(subset)
        if n == 0:
            return {}
        brk = [s for s in subset if s['type'] == 'BRK']
        brk_conf = [s for s in brk if s['conf'] in ('pass', 'pass_star')]
        brk_fail = [s for s in brk if s['conf'] == 'fail']
        brk_with_conf = [s for s in brk if s['conf'] is not None]

        by_time = defaultdict(list)
        by_vol = defaultdict(list)
        for s in brk_with_conf:
            by_time[time_bucket(s['timestamp'])].append(s)
            by_vol[vol_bucket(s['vol_ratio'])].append(s)

        return {
            'label': label,
            'n': n,
            'brk_n': len(brk),
            'conf_rate': fmt_pct(len(brk_conf), len(brk_with_conf)) if brk_with_conf else '—',
            'conf_star_n': sum(1 for s in brk if s['conf_star']),
            'time_conf': {
                tb: fmt_pct(
                    sum(1 for s in sigs if s['conf'] in ('pass', 'pass_star')),
                    len(sigs)
                ) for tb, sigs in by_time.items()
            },
            'vol_conf': {
                vb: fmt_pct(
                    sum(1 for s in sigs if s['conf'] in ('pass', 'pass_star')),
                    len(sigs)
                ) for vb, sigs in by_vol.items()
            },
        }

    full = metrics(signals, "Full dataset")
    excl = metrics(non_jan29, "Excl. Jan 29")

    headers = ["Metric", "Full dataset", "Excl. Jan 29", "Delta"]
    rows = []
    rows.append(["Total signals", full['n'], excl['n'], full['n'] - excl['n']])
    rows.append(["BRK signals", full['brk_n'], excl['brk_n'], full['brk_n'] - excl['brk_n']])
    rows.append(["BRK CONF rate", full['conf_rate'], excl['conf_rate'], ""])
    rows.append(["✓★ count", full['conf_star_n'], excl['conf_star_n'],
                  full['conf_star_n'] - excl['conf_star_n']])

    lines.append("### Core Metrics")
    lines.append("")
    lines.append(fmt_table(headers, rows))
    lines.append("")

    # CONF rate by time bucket
    lines.append("### CONF Rate by Time Bucket")
    lines.append("")
    time_headers = ["Time", "Full", "Excl. Jan 29"]
    time_rows = []
    for tb in ['9:30-10', '10-11', '11-13', '13-16']:
        time_rows.append([
            tb,
            full['time_conf'].get(tb, '—'),
            excl['time_conf'].get(tb, '—'),
        ])
    lines.append(fmt_table(time_headers, time_rows))
    lines.append("")

    # CONF rate by volume bucket
    lines.append("### CONF Rate by Volume Bucket")
    lines.append("")
    vol_headers = ["Volume", "Full", "Excl. Jan 29"]
    vol_rows = []
    for vb in ['<1.5x', '1.5-2x', '2-5x', '5-10x', '10x+']:
        vol_rows.append([
            vb,
            full['vol_conf'].get(vb, '—'),
            excl['vol_conf'].get(vb, '—'),
        ])
    lines.append(fmt_table(vol_headers, vol_rows))
    lines.append("")

    return "\n".join(lines)


def gap_b_day_of_week(signals):
    """Gap B: Do Monday/Friday differ from mid-week?"""
    lines = []
    lines.append("## Gap B: Day-of-Week Effects")
    lines.append("")
    lines.append("**Question:** Do Monday/Friday differ from mid-week?")
    lines.append("")

    by_dow = defaultdict(list)
    for s in signals:
        by_dow[s['weekday']].append(s)

    headers = ["Day", "Signals", "BRK", "CONF rate", "✓★ count", "Avg vol"]
    rows = []
    for dow in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']:
        sigs = by_dow.get(dow, [])
        n = len(sigs)
        brk = [s for s in sigs if s['type'] == 'BRK']
        brk_with_conf = [s for s in brk if s['conf'] is not None]
        brk_pass = [s for s in brk if s['conf'] in ('pass', 'pass_star')]
        stars = sum(1 for s in brk if s['conf_star'])
        avg_vol = mean(s['vol_ratio'] for s in sigs) if sigs else 0
        rows.append([
            dow, n, len(brk),
            fmt_pct(len(brk_pass), len(brk_with_conf)),
            stars,
            f"{avg_vol:.1f}x",
        ])

    lines.append(fmt_table(headers, rows))
    lines.append("")

    return "\n".join(lines)


def gap_c_symbol_time_interactions(signals):
    """Gap C: Does AMZN have a different optimal window than SPY?"""
    lines = []
    lines.append("## Gap C: Symbol × Time Interactions")
    lines.append("")
    lines.append("**Question:** Do symbols have different optimal time windows?")
    lines.append("")
    lines.append("CONF rate per cell (BRK only). **Bold** = >10pp above column average, *italic* = >10pp below.")
    lines.append("")

    time_buckets = ['9:30-10', '10-11', '11-13', '13-16']

    # Compute column averages first
    col_data = defaultdict(lambda: {'pass': 0, 'total': 0})
    cell_data = defaultdict(lambda: defaultdict(lambda: {'pass': 0, 'total': 0}))

    for s in signals:
        if s['type'] != 'BRK' or s['conf'] is None:
            continue
        tb = time_bucket(s['timestamp'])
        sym = s['symbol']
        is_pass = s['conf'] in ('pass', 'pass_star')
        col_data[tb]['total'] += 1
        col_data[tb]['pass'] += int(is_pass)
        cell_data[sym][tb]['total'] += 1
        cell_data[sym][tb]['pass'] += int(is_pass)

    col_avg = {}
    for tb in time_buckets:
        d = col_data[tb]
        col_avg[tb] = (d['pass'] / d['total'] * 100) if d['total'] > 0 else 0

    headers = ["Symbol"] + [f"{tb} (avg {col_avg[tb]:.0f}%)" for tb in time_buckets]
    rows = []
    for sym in sorted(ALL_SYMBOLS):
        row = [sym]
        for tb in time_buckets:
            d = cell_data[sym][tb]
            if d['total'] == 0:
                row.append("—")
            else:
                rate = d['pass'] / d['total'] * 100
                text = f"{rate:.0f}% (n={d['total']})"
                diff = rate - col_avg[tb]
                if diff > 10:
                    text = f"**{text}**"
                elif diff < -10:
                    text = f"*{text}*"
                row.append(text)
        rows.append(row)

    # Add column average row
    avg_row = ["**Average**"]
    for tb in time_buckets:
        d = col_data[tb]
        avg_row.append(f"{col_avg[tb]:.0f}% (n={d['total']})")
    rows.append(avg_row)

    lines.append(fmt_table(headers, rows))
    lines.append("")

    return "\n".join(lines)


def gap_d_reclaim_deep_dive(signals, candles_cache, bar_secs_cache):
    """Gap D: Why are reclaims (~~ ) mixed? What predicts a good reclaim?"""
    lines = []
    lines.append("## Gap D: Reclaim (~~ ) Deep Dive")
    lines.append("")
    lines.append("**Question:** What predicts a good reclaim vs bad one?")
    lines.append("")

    reclaims = [s for s in signals if s['type'] == '~~']
    brks = [s for s in signals if s['type'] == 'BRK']

    lines.append(f"Total reclaims: {len(reclaims)}")
    lines.append("")

    # For each reclaim, find the prior BRK at the same level on the same day
    reclaim_data = []
    for rcl in reclaims:
        # Find prior BRK on same day with matching level
        prior_brks = [
            b for b in brks
            if b['symbol'] == rcl['symbol']
            and b['date'] == rcl['date']
            and b['timestamp'] < rcl['timestamp']
            and set(b['levels']) & set(rcl['levels'])  # at least one shared level
        ]
        time_since_brk = None
        brk_vol = None
        if prior_brks:
            closest = max(prior_brks, key=lambda b: b['timestamp'])
            time_since_brk = (rcl['timestamp'] - closest['timestamp']).total_seconds() / 60
            brk_vol = closest['vol_ratio']

        # Compute 5s excursions if candle data available
        exc = None
        classification = None
        candles_df = candles_cache.get(rcl['symbol'])
        bsecs = bar_secs_cache.get(rcl['symbol'], 5)
        if candles_df is not None:
            exc = compute_excursions(rcl, candles_df, bsecs)
            if exc.get('15m'):
                classification = classify_signal(exc, rcl['atr'])

        reclaim_data.append({
            'sig': rcl,
            'time_since_brk': time_since_brk,
            'brk_vol': brk_vol,
            'vol_ratio_vs_brk': (rcl['vol_ratio'] / brk_vol) if brk_vol and brk_vol > 0 else None,
            'exc': exc,
            'cls': classification,
        })

    # ── Analysis by time-since-BRK bucket ──
    lines.append("### By Time Since Prior BRK")
    lines.append("")

    def time_since_bucket(mins):
        if mins is None:
            return 'No prior BRK'
        elif mins < 15:
            return '<15m'
        elif mins < 60:
            return '15-60m'
        elif mins < 180:
            return '1-3h'
        else:
            return '3h+'

    by_tsb = defaultdict(list)
    for rd in reclaim_data:
        by_tsb[time_since_bucket(rd['time_since_brk'])].append(rd)

    headers = ["Time since BRK", "Count", "GOOD", "BAD", "NEUTRAL", "Unmatched", "GOOD%", "BAD%"]
    rows = []
    for bucket in ['<15m', '15-60m', '1-3h', '3h+', 'No prior BRK']:
        items = by_tsb.get(bucket, [])
        n = len(items)
        good = sum(1 for r in items if r['cls'] == 'GOOD')
        bad = sum(1 for r in items if r['cls'] == 'BAD')
        neut = sum(1 for r in items if r['cls'] == 'NEUTRAL')
        unmatched = sum(1 for r in items if r['cls'] is None)
        rows.append([bucket, n, good, bad, neut, unmatched, fmt_pct(good, n - unmatched), fmt_pct(bad, n - unmatched)])
    lines.append(fmt_table(headers, rows))
    lines.append("")

    # ── Analysis by volume at reclaim vs BRK ──
    lines.append("### By Volume Ratio (Reclaim vol / BRK vol)")
    lines.append("")

    def vol_ratio_bucket(ratio):
        if ratio is None:
            return 'Unknown'
        elif ratio < 0.5:
            return '<0.5x'
        elif ratio < 1.0:
            return '0.5-1x'
        elif ratio < 2.0:
            return '1-2x'
        else:
            return '2x+'

    by_vr = defaultdict(list)
    for rd in reclaim_data:
        by_vr[vol_ratio_bucket(rd['vol_ratio_vs_brk'])].append(rd)

    rows = []
    for bucket in ['<0.5x', '0.5-1x', '1-2x', '2x+', 'Unknown']:
        items = by_vr.get(bucket, [])
        n = len(items)
        good = sum(1 for r in items if r['cls'] == 'GOOD')
        bad = sum(1 for r in items if r['cls'] == 'BAD')
        neut = sum(1 for r in items if r['cls'] == 'NEUTRAL')
        unmatched = sum(1 for r in items if r['cls'] is None)
        rows.append([bucket, n, good, bad, neut, unmatched, fmt_pct(good, n - unmatched), fmt_pct(bad, n - unmatched)])
    lines.append(fmt_table(headers, rows))
    lines.append("")

    # ── 5s MFE/MAE at multiple windows ──
    classified = [rd for rd in reclaim_data if rd['exc'] is not None]
    if classified:
        lines.append("### Reclaim MFE/MAE by Time Window (ATR-normalized)")
        lines.append("")
        win_headers = ["Window", "Avg MFE/ATR", "Avg MAE/ATR", "Avg MFE/MAE", "Coverage"]
        win_rows = []
        for wlabel in ['30s', '1m', '2m', '5m', '15m', '30m']:
            mfe_vals = [rd['exc'][wlabel]['mfe_atr'] for rd in classified if rd['exc'].get(wlabel)]
            mae_vals = [rd['exc'][wlabel]['mae_atr'] for rd in classified if rd['exc'].get(wlabel)]
            ratios = []
            for rd in classified:
                e = rd['exc'].get(wlabel)
                if e and e['mae'] > 0.001:
                    ratios.append(e['mfe'] / e['mae'])
            coverage = len(mfe_vals)
            win_rows.append([
                wlabel,
                f"{mean(mfe_vals):.3f}" if mfe_vals else "—",
                f"{mean(mae_vals):.3f}" if mae_vals else "—",
                f"{mean(ratios):.2f}" if ratios else "—",
                f"{coverage}/{len(classified)}",
            ])
        lines.append(fmt_table(win_headers, win_rows))
        lines.append("")

    # ── By level type ──
    lines.append("### By Level Type")
    lines.append("")
    by_level = defaultdict(list)
    for rd in reclaim_data:
        for lvl in rd['sig']['levels']:
            by_level[lvl].append(rd)

    headers_lvl = ["Level", "Count", "GOOD", "BAD", "GOOD%", "BAD%"]
    rows_lvl = []
    for lvl in sorted(by_level.keys()):
        items = by_level[lvl]
        classified_items = [r for r in items if r['cls'] is not None]
        n = len(classified_items)
        good = sum(1 for r in classified_items if r['cls'] == 'GOOD')
        bad = sum(1 for r in classified_items if r['cls'] == 'BAD')
        rows_lvl.append([lvl, len(items), good, bad, fmt_pct(good, n), fmt_pct(bad, n)])
    lines.append(fmt_table(headers_lvl, rows_lvl))
    lines.append("")

    return "\n".join(lines)


def gap_e_multi_level_quality(signals, candles_cache, bar_secs_cache):
    """Gap E: Does multi-level confluence actually boost follow-through?"""
    lines = []
    lines.append("## Gap E: Multi-Level Breakout Quality")
    lines.append("")
    lines.append("**Question:** Does level confluence boost follow-through (not just CONF)?")
    lines.append("")

    single = [s for s in signals if s['level_count'] == 1]
    multi = [s for s in signals if s['level_count'] > 1]

    lines.append(f"- Single-level signals: {len(single)}")
    lines.append(f"- Multi-level signals: {len(multi)}")
    lines.append("")

    # CONF rate comparison
    def conf_stats(subset, label):
        brk = [s for s in subset if s['type'] == 'BRK']
        brk_with_conf = [s for s in brk if s['conf'] is not None]
        brk_pass = [s for s in brk if s['conf'] in ('pass', 'pass_star')]
        return label, len(subset), len(brk), fmt_pct(len(brk_pass), len(brk_with_conf))

    headers = ["Group", "Total", "BRK", "CONF rate"]
    rows = [
        list(conf_stats(single, "Single-level")),
        list(conf_stats(multi, "Multi-level")),
    ]
    lines.append("### CONF Rate (from pine logs)")
    lines.append("")
    lines.append(fmt_table(headers, rows))
    lines.append("")

    # 5s MFE/MAE comparison
    def excursion_stats(subset, candles_cache, bar_secs_cache):
        results = []
        for s in subset:
            df = candles_cache.get(s['symbol'])
            if df is None:
                continue
            bsecs = bar_secs_cache.get(s['symbol'], 5)
            exc = compute_excursions(s, df, bsecs)
            if exc.get('15m'):
                cls = classify_signal(exc, s['atr'])
                results.append((s, exc, cls))
        return results

    lines.append("### 5s Follow-Through Comparison")
    lines.append("")

    single_exc = excursion_stats(single, candles_cache, bar_secs_cache)
    multi_exc = excursion_stats(multi, candles_cache, bar_secs_cache)

    ft_headers = ["Group", "Matched", "GOOD", "BAD", "GOOD%", "BAD%",
                   "MFE/ATR 5m", "MFE/ATR 30m", "MAE/ATR 15m"]
    ft_rows = []
    for label, data in [("Single-level", single_exc), ("Multi-level", multi_exc)]:
        n = len(data)
        good = sum(1 for _, _, c in data if c == 'GOOD')
        bad = sum(1 for _, _, c in data if c == 'BAD')
        mfe5 = [e['5m']['mfe_atr'] for _, e, _ in data if e.get('5m')]
        mfe30 = [e['30m']['mfe_atr'] for _, e, _ in data if e.get('30m')]
        mae15 = [e['15m']['mae_atr'] for _, e, _ in data if e.get('15m')]
        ft_rows.append([
            label, n, good, bad,
            fmt_pct(good, n), fmt_pct(bad, n),
            f"{mean(mfe5):.3f}" if mfe5 else "—",
            f"{mean(mfe30):.3f}" if mfe30 else "—",
            f"{mean(mae15):.3f}" if mae15 else "—",
        ])
    lines.append(fmt_table(ft_headers, ft_rows))
    lines.append("")

    return "\n".join(lines)


def gap_f_counter_trend_ci(signals):
    """Gap F: Is 75 counter-trend signals enough to trust '10% CONF'?"""
    lines = []
    lines.append("## Gap F: Counter-Trend Confidence Interval")
    lines.append("")
    lines.append("**Question:** Is our counter-trend sample size sufficient?")
    lines.append("")

    # Counter-trend: bull + vwap=below, or bear + vwap=above
    ct_brk = [
        s for s in signals
        if s['type'] == 'BRK' and s['vwap'] is not None
        and ((s['direction'] == 'bull' and s['vwap'] == 'below')
             or (s['direction'] == 'bear' and s['vwap'] == 'above'))
        and s['conf'] is not None
    ]
    wt_brk = [
        s for s in signals
        if s['type'] == 'BRK' and s['vwap'] is not None
        and ((s['direction'] == 'bull' and s['vwap'] == 'above')
             or (s['direction'] == 'bear' and s['vwap'] == 'below'))
        and s['conf'] is not None
    ]

    ct_pass = sum(1 for s in ct_brk if s['conf'] in ('pass', 'pass_star'))
    wt_pass = sum(1 for s in wt_brk if s['conf'] in ('pass', 'pass_star'))

    ct_n = len(ct_brk)
    wt_n = len(wt_brk)

    ct_phat, ct_lo, ct_hi = wilson_ci(ct_pass, ct_n)
    wt_phat, wt_lo, wt_hi = wilson_ci(wt_pass, wt_n)

    lines.append("### Wilson Score 95% Confidence Intervals")
    lines.append("")
    headers = ["Group", "N", "Passes", "Point est.", "95% CI low", "95% CI high", "CI width"]
    rows = [
        ["Counter-trend", ct_n, ct_pass,
         f"{ct_phat:.1%}", f"{ct_lo:.1%}", f"{ct_hi:.1%}", f"{(ct_hi - ct_lo):.1%}"],
        ["With-trend", wt_n, wt_pass,
         f"{wt_phat:.1%}", f"{wt_lo:.1%}", f"{wt_hi:.1%}", f"{(wt_hi - wt_lo):.1%}"],
    ]
    lines.append(fmt_table(headers, rows))
    lines.append("")

    # Required sample size for ±5pp precision
    # n = z^2 * p*(1-p) / margin^2
    margin = 0.05
    z = 1.96
    ct_needed = math.ceil(z * z * ct_phat * (1 - ct_phat) / (margin * margin)) if ct_n > 0 else 0
    wt_needed = math.ceil(z * z * wt_phat * (1 - wt_phat) / (margin * margin)) if wt_n > 0 else 0

    lines.append("### Sample Size Requirements (for ±5pp precision at 95% confidence)")
    lines.append("")
    lines.append(f"- Counter-trend: need **{ct_needed}** signals (have {ct_n}) → {'sufficient' if ct_n >= ct_needed else f'need {ct_needed - ct_n} more'}")
    lines.append(f"- With-trend: need **{wt_needed}** signals (have {wt_n}) → {'sufficient' if wt_n >= wt_needed else f'need {wt_needed - wt_n} more'}")
    lines.append("")

    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("═" * 60)
    print("v2.4 Gap Analysis")
    print("═" * 60)

    # 1. Parse pine logs
    print("\n[1/5] Parsing pine logs...")
    signals, confs = load_pine_logs()
    print(f"  Total: {len(signals)} signals, {len(confs)} CONFs")

    # Sanity checks
    brk_signals = [s for s in signals if s['type'] == 'BRK']
    brk_with_conf = [s for s in brk_signals if s['conf'] is not None]
    brk_pass = [s for s in brk_signals if s['conf'] in ('pass', 'pass_star')]
    print(f"  BRK: {len(brk_signals)}, with CONF: {len(brk_with_conf)}, pass: {len(brk_pass)}")
    if brk_with_conf:
        print(f"  Overall CONF rate: {100 * len(brk_pass) / len(brk_with_conf):.1f}%")

    # 2. Load candles (5s preferred, 1m fallback)
    print("\n[2/5] Loading candle data...")
    candles_cache = {}
    bar_secs_cache = {}
    for sym in ALL_SYMBOLS:
        df, bsecs = load_candles(sym)
        if df is not None and len(df) > 0:
            candles_cache[sym] = df
            bar_secs_cache[sym] = bsecs
            res_label = "5s" if bsecs == 5 else "1m"
            print(f"  {sym}: {len(df):,} bars ({res_label}, {df.index.min().date()} to {df.index.max().date()})")
        else:
            print(f"  {sym}: NO DATA")

    # 3. Run 6 analyses
    print("\n[3/5] Running Gap A (Jan 29 cross-validation)...")
    section_a = gap_a_jan29_cross_validation(signals)

    print("[3/5] Running Gap B (day-of-week)...")
    section_b = gap_b_day_of_week(signals)

    print("[3/5] Running Gap C (symbol × time)...")
    section_c = gap_c_symbol_time_interactions(signals)

    print("[3/5] Running Gap D (reclaim deep dive)...")
    section_d = gap_d_reclaim_deep_dive(signals, candles_cache, bar_secs_cache)

    print("[3/5] Running Gap E (multi-level quality)...")
    section_e = gap_e_multi_level_quality(signals, candles_cache, bar_secs_cache)

    print("[3/5] Running Gap F (counter-trend CI)...")
    section_f = gap_f_counter_trend_ci(signals)

    # 4. Assemble report
    print("\n[4/5] Writing report...")

    # Summary stats
    symbols_found = sorted(set(s['symbol'] for s in signals))
    dates = sorted(set(s['date'] for s in signals))

    report = []
    report.append("# v2.4 Gap Analysis")
    report.append("")
    report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"**Symbols:** {', '.join(symbols_found)} ({len(symbols_found)} total)")
    report.append(f"**Date range:** {dates[0]} to {dates[-1]} ({len(dates)} trading days)")
    report.append(f"**Total signals:** {len(signals)}")
    report.append(f"**5s candle coverage:** {len(candles_cache)}/{len(ALL_SYMBOLS)} symbols")
    report.append("")

    # Signal type breakdown
    type_counts = defaultdict(int)
    for s in signals:
        type_counts[s['type']] += 1
    report.append("### Signal Breakdown")
    report.append(f"- BRK: {type_counts.get('BRK', 0)}")
    report.append(f"- ~ (reversal): {type_counts.get('~', 0)}")
    report.append(f"- ~~ (reclaim): {type_counts.get('~~', 0)}")
    report.append("")
    report.append("---")
    report.append("")

    report.append(section_a)
    report.append("---")
    report.append("")
    report.append(section_b)
    report.append("---")
    report.append("")
    report.append(section_c)
    report.append("---")
    report.append("")
    report.append(section_d)
    report.append("---")
    report.append("")
    report.append(section_e)
    report.append("---")
    report.append("")
    report.append(section_f)

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write("\n".join(report))

    print(f"\n[5/5] Done! Report written to: {OUTPUT}")
    print(f"  Sections: A through F (6 gaps)")


if __name__ == "__main__":
    main()
