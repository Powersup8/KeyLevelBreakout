#!/usr/bin/env python3
"""Follow-through analysis for KeyLevelBreakout v2.3 signals."""

import csv
import re
import os
from datetime import datetime, timedelta
from collections import defaultdict

BASE = "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug"

# Symbol -> (pine_log_suffix, candle_suffix)
SYMBOLS = {
    "SPY":   ("d0567", "BATS_SPY, 1_1c35c"),
    "AAPL":  ("9a273", "BATS_AAPL, 1_1fe43"),
    "AMD":   ("6e610", "BATS_AMD, 1_f518b"),
    "AMZN":  ("8b4c8", "BATS_AMZN, 1_ac32b"),
    "GLD":   ("b331c", "BATS_GLD, 1_2c5d7"),
    "GOOGL": ("c5d77", "BATS_GOOGL, 1_4824f"),
    "META":  ("dab68", "BATS_META, 1_bb4a4"),
    "MSFT":  ("916a2", "BATS_MSFT, 1_9b278"),
    "NVDA":  ("dd753", "BATS_NVDA, 1_b80ed"),
    "QQQ":   ("056b6", "BATS_QQQ, 1_b52c4"),
    "SLV":   ("745d1", "BATS_SLV, 1_f06e7"),
    "TSLA":  ("c1645", "BATS_TSLA, 1_9dd8f"),
    "TSM":   ("71a6b", "BATS_TSM, 1_0dbe1"),
}

def parse_time(ts):
    """Parse ISO timestamp to datetime."""
    # Handle both formats: with and without .000
    ts = ts.strip()
    # Remove milliseconds if present
    ts = re.sub(r'\.\d+', '', ts)
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        # Try without timezone offset format
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")

def load_candles(symbol):
    """Load 1m candle data, indexed by datetime."""
    _, candle_file = SYMBOLS[symbol]
    path = os.path.join(BASE, f"{candle_file}.csv")
    candles = {}
    with open(path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if len(row) < 5:
                continue
            ts = parse_time(row[0])
            candles[ts] = {
                'open': float(row[1]),
                'high': float(row[2]),
                'low': float(row[3]),
                'close': float(row[4]),
            }
    return candles

def load_signals(symbol):
    """Load pine log signals, return actionable signals and CONF outcomes."""
    pine_suffix, _ = SYMBOLS[symbol]
    path = os.path.join(BASE, f"pine-logs-Key Level Breakout_{pine_suffix}.csv")
    signals = []
    conf_outcomes = {}  # (date, direction, signal_type) -> outcome

    with open(path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if len(row) < 2:
                continue
            ts_str = row[0]
            msg = row[1]

            ts = parse_time(ts_str)

            # Parse CONF outcomes
            conf_match = re.match(r'\[KLB\] CONF \d+:\d+ ([▲▼]) (BRK|~~|~) → (✓|✗)', msg)
            if conf_match:
                direction = 'bull' if conf_match.group(1) == '▲' else 'bear'
                sig_type = conf_match.group(2)
                outcome = conf_match.group(3)
                # Store CONF with its timestamp for matching
                conf_outcomes[(ts.date(), direction, sig_type)] = outcome
                continue

            # Parse actionable signals: BRK, ~, ~~
            # Pattern: [KLB] HH:MM ▲/▼ BRK/~/~~ level_info vol=Xx pos=^/vNN ...
            sig_match = re.match(
                r'\[KLB\] \d+:\d+ ([▲▼]) (BRK|~~|~) (?:~~|~|BRK)?\s*(.*?)vol=([0-9.]+)x pos=([v^])(\d+) O([0-9.]+) H([0-9.]+) L([0-9.]+) C([0-9.]+) ATR=([0-9.]+)',
                msg
            )
            if sig_match:
                direction = 'bull' if sig_match.group(1) == '▲' else 'bear'
                sig_type = sig_match.group(2)
                level_info = sig_match.group(3).strip()
                vol_ratio = float(sig_match.group(4))
                pos_dir = sig_match.group(5)
                pos_val = int(sig_match.group(6))
                close_price = float(sig_match.group(10))
                atr = float(sig_match.group(11))
                buf = atr * 0.05

                # Extract level types from the level_info
                # Levels: PM H, PM L, ORB H, ORB L, Yest H, Yest L, Week H, Week L
                levels = []
                for lvl in ['PM H', 'PM L', 'ORB H', 'ORB L', 'Yest H', 'Yest L', 'Week H', 'Week L']:
                    if lvl in level_info:
                        levels.append(lvl)

                # Also check for combined signals like "+ Yest H"
                if not levels:
                    # Try to extract from the full message
                    for lvl in ['PM H', 'PM L', 'ORB H', 'ORB L', 'Yest H', 'Yest L', 'Week H', 'Week L']:
                        if lvl in msg:
                            levels.append(lvl)

                signals.append({
                    'timestamp': ts,
                    'direction': direction,
                    'type': sig_type,
                    'levels': levels,
                    'level_str': level_info,
                    'vol_ratio': vol_ratio,
                    'pos_dir': pos_dir,
                    'pos_val': pos_val,
                    'close': close_price,
                    'atr': atr,
                    'buf': buf,
                    'symbol': symbol,
                })

    # Match CONF outcomes to signals
    for sig in signals:
        key = (sig['timestamp'].date(), sig['direction'], sig['type'])
        # Try exact match first
        if key in conf_outcomes:
            sig['conf'] = conf_outcomes[key]
        else:
            sig['conf'] = None

    return signals

def compute_excursions(sig, candles):
    """Compute MFE and MAE at 5/15/30/60 min windows after signal."""
    ts = sig['timestamp']
    direction = sig['direction']
    entry = sig['close']
    buf = sig['buf']
    atr = sig['atr']

    windows = [5, 15, 30, 60]
    results = {}

    for w in windows:
        mfe = 0.0  # max favorable excursion
        mae = 0.0  # max adverse excursion
        bars_found = 0

        for i in range(1, w + 1):
            bar_time = ts + timedelta(minutes=i)
            if bar_time in candles:
                c = candles[bar_time]
                bars_found += 1

                if direction == 'bull':
                    # Favorable = high - entry, adverse = entry - low
                    fav = c['high'] - entry
                    adv = entry - c['low']
                else:
                    # Favorable = entry - low, adverse = high - entry
                    fav = entry - c['low']
                    adv = c['high'] - entry

                mfe = max(mfe, fav)
                mae = max(mae, adv)

        if bars_found > 0:
            results[w] = {
                'mfe': mfe,
                'mae': mae,
                'mfe_atr': mfe / atr if atr > 0 else 0,
                'mae_atr': mae / atr if atr > 0 else 0,
                'mfe_buf': mfe / buf if buf > 0 else 0,
                'mae_buf': mae / buf if buf > 0 else 0,
                'bars': bars_found,
            }
        else:
            results[w] = None

    return results

def classify_signal(excursions, atr):
    """Classify signal as GOOD, BAD, or NEUTRAL."""
    # BAD: MAE > 0.5 * ATR within 15 minutes
    if excursions.get(15) and excursions[15]['mae'] > 0.5 * atr:
        return 'BAD'

    # GOOD: MFE > 0.5 * ATR within 30 minutes AND MFE > 2 * MAE
    if excursions.get(30):
        e30 = excursions[30]
        mae_for_ratio = max(e30['mae'], 0.001)  # avoid division by zero
        if e30['mfe'] > 0.5 * atr and e30['mfe'] > 2 * mae_for_ratio:
            return 'GOOD'

    return 'NEUTRAL'

def vol_bucket(vol):
    if vol > 5:
        return '>5x'
    elif vol > 3:
        return '3-5x'
    elif vol > 1.5:
        return '1.5-3x'
    else:
        return '<1.5x'

def time_bucket(ts):
    h, m = ts.hour, ts.minute
    t = h * 60 + m
    if t < 10 * 60:  # before 10:00
        return '9:30-10:00'
    elif t < 11 * 60:
        return '10:00-11:00'
    elif t < 13 * 60:
        return '11:00-13:00'
    else:
        return '13:00-16:00'

def pos_quality(sig):
    """Extreme position = ^80+ or v80+."""
    if sig['pos_val'] >= 80:
        return 'extreme'
    else:
        return 'normal'

def format_pct(num, denom):
    if denom == 0:
        return "0.0%"
    return f"{100*num/denom:.1f}%"

def format_table(rows, headers):
    """Format a markdown table."""
    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    lines = []
    # Header
    header_line = "| " + " | ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers)) + " |"
    sep_line = "|" + "|".join("-" * (widths[i] + 2) for i in range(len(headers))) + "|"
    lines.append(header_line)
    lines.append(sep_line)
    for row in rows:
        line = "| " + " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)) + " |"
        lines.append(line)
    return "\n".join(lines)

def aggregate_stats(signals_with_data, group_fn, group_name):
    """Aggregate signal statistics by a grouping function."""
    groups = defaultdict(list)
    for sig, exc, cls in signals_with_data:
        key = group_fn(sig)
        if isinstance(key, list):
            for k in key:
                groups[k].append((sig, exc, cls))
        else:
            groups[key].append((sig, exc, cls))

    headers = [group_name, "Count", "GOOD", "BAD", "NEUTRAL", "GOOD%", "BAD%",
               "Avg MFE/ATR 30m", "Avg MAE/ATR 15m", "Avg MFE/MAE 30m"]
    rows = []

    for key in sorted(groups.keys()):
        items = groups[key]
        n = len(items)
        good = sum(1 for _, _, c in items if c == 'GOOD')
        bad = sum(1 for _, _, c in items if c == 'BAD')
        neutral = sum(1 for _, _, c in items if c == 'NEUTRAL')

        mfe30_vals = [e[30]['mfe_atr'] for _, e, _ in items if e.get(30)]
        mae15_vals = [e[15]['mae_atr'] for _, e, _ in items if e.get(15)]

        avg_mfe30 = sum(mfe30_vals) / len(mfe30_vals) if mfe30_vals else 0
        avg_mae15 = sum(mae15_vals) / len(mae15_vals) if mae15_vals else 0

        # MFE/MAE ratio at 30m
        ratios = []
        for _, e, _ in items:
            if e.get(30) and e[30]['mae'] > 0.001:
                ratios.append(e[30]['mfe'] / e[30]['mae'])
        avg_ratio = sum(ratios) / len(ratios) if ratios else 0

        rows.append([
            key, n, good, bad, neutral,
            format_pct(good, n), format_pct(bad, n),
            f"{avg_mfe30:.3f}", f"{avg_mae15:.3f}", f"{avg_ratio:.2f}"
        ])

    return format_table(rows, headers)

def main():
    all_signals = []
    no_candle_data = []

    for symbol in SYMBOLS:
        print(f"Processing {symbol}...")
        candles = load_candles(symbol)
        signals = load_signals(symbol)

        candle_times = sorted(candles.keys())
        if candle_times:
            min_candle = candle_times[0]
            max_candle = candle_times[-1]
        else:
            min_candle = None
            max_candle = None

        for sig in signals:
            # Check if we have candle data for this signal
            if min_candle is None or sig['timestamp'] < min_candle or sig['timestamp'] > max_candle:
                no_candle_data.append(sig)
                continue

            exc = compute_excursions(sig, candles)

            # Need at least 15m data for classification
            if exc.get(15) is None:
                no_candle_data.append(sig)
                continue

            cls = classify_signal(exc, sig['atr'])
            all_signals.append((sig, exc, cls))

    print(f"\nTotal signals with candle data: {len(all_signals)}")
    print(f"Signals without candle data: {len(no_candle_data)}")

    # Now generate the report
    report = []
    report.append("# Follow-Through Analysis: KeyLevelBreakout v2.3")
    report.append(f"**Generated:** 2026-02-28")
    report.append(f"**Symbols:** {', '.join(sorted(SYMBOLS.keys()))}")
    report.append(f"**Total actionable signals analyzed:** {len(all_signals)}")
    report.append(f"**Signals without candle data (pre-Feb 19):** {len(no_candle_data)}")
    report.append("")

    # ===== EXECUTIVE SUMMARY =====
    report.append("## 1. Executive Summary")
    report.append("")

    total = len(all_signals)
    good = sum(1 for _, _, c in all_signals if c == 'GOOD')
    bad = sum(1 for _, _, c in all_signals if c == 'BAD')
    neutral = sum(1 for _, _, c in all_signals if c == 'NEUTRAL')

    report.append(f"| Classification | Count | Percentage |")
    report.append(f"|---------------|-------|------------|")
    report.append(f"| GOOD | {good} | {format_pct(good, total)} |")
    report.append(f"| BAD | {bad} | {format_pct(bad, total)} |")
    report.append(f"| NEUTRAL | {neutral} | {format_pct(neutral, total)} |")
    report.append(f"| **Total** | **{total}** | **100%** |")
    report.append("")

    # Overall MFE/MAE stats
    mfe5 = [e[5]['mfe_atr'] for _, e, _ in all_signals if e.get(5)]
    mfe15 = [e[15]['mfe_atr'] for _, e, _ in all_signals if e.get(15)]
    mfe30 = [e[30]['mfe_atr'] for _, e, _ in all_signals if e.get(30)]
    mfe60 = [e[60]['mfe_atr'] for _, e, _ in all_signals if e.get(60)]
    mae5 = [e[5]['mae_atr'] for _, e, _ in all_signals if e.get(5)]
    mae15 = [e[15]['mae_atr'] for _, e, _ in all_signals if e.get(15)]
    mae30 = [e[30]['mae_atr'] for _, e, _ in all_signals if e.get(30)]
    mae60 = [e[60]['mae_atr'] for _, e, _ in all_signals if e.get(60)]

    def avg(lst):
        return sum(lst)/len(lst) if lst else 0
    def med(lst):
        if not lst: return 0
        s = sorted(lst)
        n = len(s)
        if n % 2 == 0:
            return (s[n//2-1] + s[n//2]) / 2
        return s[n//2]

    report.append("### Average Excursions (as fraction of ATR)")
    report.append("")
    report.append("| Window | Avg MFE | Med MFE | Avg MAE | Med MAE | Avg MFE/MAE |")
    report.append("|--------|---------|---------|---------|---------|-------------|")
    for label, mfe_list, mae_list in [("5min", mfe5, mae5), ("15min", mfe15, mae15),
                                        ("30min", mfe30, mae30), ("60min", mfe60, mae60)]:
        ratios = [m/max(a,0.0001) for m, a in zip(mfe_list, mae_list)]
        report.append(f"| {label} | {avg(mfe_list):.4f} | {med(mfe_list):.4f} | {avg(mae_list):.4f} | {med(mae_list):.4f} | {avg(ratios):.2f} |")
    report.append("")

    # ===== BREAKDOWN BY SIGNAL TYPE =====
    report.append("## 2. Breakdown by Signal Type (BRK vs ~ vs ~~)")
    report.append("")
    report.append(aggregate_stats(all_signals, lambda s: s['type'], "Signal Type"))
    report.append("")

    # ===== BREAKDOWN BY LEVEL TYPE =====
    report.append("## 3. Breakdown by Level Type")
    report.append("")
    def level_fn(sig):
        return sig['levels'] if sig['levels'] else ['Unknown']
    report.append(aggregate_stats(all_signals, level_fn, "Level"))
    report.append("")

    # ===== BREAKDOWN BY VOLUME BUCKET =====
    report.append("## 4. Breakdown by Volume Bucket")
    report.append("")
    report.append(aggregate_stats(all_signals, lambda s: vol_bucket(s['vol_ratio']), "Volume"))
    report.append("")

    # ===== BREAKDOWN BY TIME OF DAY =====
    report.append("## 5. Breakdown by Time of Day")
    report.append("")
    report.append(aggregate_stats(all_signals, lambda s: time_bucket(s['timestamp']), "Time"))
    report.append("")

    # ===== BREAKDOWN BY CONF OUTCOME =====
    report.append("## 6. Breakdown by CONF Outcome")
    report.append("")
    def conf_fn(sig):
        if sig['conf'] == '✓':
            return 'CONF Pass'
        elif sig['conf'] == '✗':
            return 'CONF Fail'
        else:
            return 'No CONF'
    report.append(aggregate_stats(all_signals, conf_fn, "CONF"))
    report.append("")

    # ===== BREAKDOWN BY POSITION QUALITY =====
    report.append("## 7. Breakdown by Position Quality")
    report.append("")
    report.append(aggregate_stats(all_signals, lambda s: pos_quality(s), "Position"))
    report.append("")

    # ===== BREAKDOWN BY DIRECTION =====
    report.append("## 8. Breakdown by Direction")
    report.append("")
    report.append(aggregate_stats(all_signals, lambda s: s['direction'], "Direction"))
    report.append("")

    # ===== BREAKDOWN BY SYMBOL =====
    report.append("## 9. Breakdown by Symbol")
    report.append("")
    report.append(aggregate_stats(all_signals, lambda s: s['symbol'], "Symbol"))
    report.append("")

    # ===== TOP 10 BEST SIGNALS =====
    report.append("## 10. Top 10 Best Signals (Highest MFE/ATR at 30m)")
    report.append("")

    # Sort by 30m MFE/ATR
    ranked_best = [(s, e, c) for s, e, c in all_signals if e.get(30)]
    ranked_best.sort(key=lambda x: x[1][30]['mfe_atr'], reverse=True)

    headers = ["#", "Symbol", "Date", "Time", "Type", "Dir", "Levels", "Vol", "MFE/ATR 30m", "MAE/ATR 15m", "Class", "Close", "ATR"]
    rows = []
    for i, (sig, exc, cls) in enumerate(ranked_best[:10]):
        rows.append([
            i+1, sig['symbol'],
            sig['timestamp'].strftime("%m/%d"),
            sig['timestamp'].strftime("%H:%M"),
            sig['type'], sig['direction'],
            " + ".join(sig['levels'][:2]) if sig['levels'] else "?",
            f"{sig['vol_ratio']:.1f}x",
            f"{exc[30]['mfe_atr']:.4f}",
            f"{exc[15]['mae_atr']:.4f}" if exc.get(15) else "N/A",
            cls, f"{sig['close']:.2f}", f"{sig['atr']:.2f}"
        ])
    report.append(format_table(rows, headers))
    report.append("")

    # ===== TOP 10 WORST SIGNALS =====
    report.append("## 11. Top 10 Worst Signals (Highest MAE/ATR at 15m)")
    report.append("")

    ranked_worst = [(s, e, c) for s, e, c in all_signals if e.get(15)]
    ranked_worst.sort(key=lambda x: x[1][15]['mae_atr'], reverse=True)

    rows = []
    for i, (sig, exc, cls) in enumerate(ranked_worst[:10]):
        rows.append([
            i+1, sig['symbol'],
            sig['timestamp'].strftime("%m/%d"),
            sig['timestamp'].strftime("%H:%M"),
            sig['type'], sig['direction'],
            " + ".join(sig['levels'][:2]) if sig['levels'] else "?",
            f"{sig['vol_ratio']:.1f}x",
            f"{exc[30]['mfe_atr']:.4f}" if exc.get(30) else "N/A",
            f"{exc[15]['mae_atr']:.4f}",
            cls, f"{sig['close']:.2f}", f"{sig['atr']:.2f}"
        ])
    report.append(format_table(rows, headers))
    report.append("")

    # ===== KEY FINDINGS =====
    report.append("## 12. Key Findings and Actionable Insights")
    report.append("")

    # Find best signal type
    type_stats = defaultdict(lambda: {'good': 0, 'bad': 0, 'total': 0})
    for sig, exc, cls in all_signals:
        t = sig['type']
        type_stats[t]['total'] += 1
        if cls == 'GOOD':
            type_stats[t]['good'] += 1
        elif cls == 'BAD':
            type_stats[t]['bad'] += 1

    best_type = max(type_stats.items(), key=lambda x: x[1]['good']/max(x[1]['total'],1))
    worst_type = max(type_stats.items(), key=lambda x: x[1]['bad']/max(x[1]['total'],1))

    report.append(f"1. **Best signal type:** {best_type[0]} ({format_pct(best_type[1]['good'], best_type[1]['total'])} GOOD rate, n={best_type[1]['total']})")
    report.append(f"2. **Worst signal type:** {worst_type[0]} ({format_pct(worst_type[1]['bad'], worst_type[1]['total'])} BAD rate, n={worst_type[1]['total']})")
    report.append("")

    # Volume insight
    vol_stats = defaultdict(lambda: {'good': 0, 'bad': 0, 'total': 0})
    for sig, exc, cls in all_signals:
        vb = vol_bucket(sig['vol_ratio'])
        vol_stats[vb]['total'] += 1
        if cls == 'GOOD':
            vol_stats[vb]['good'] += 1
        elif cls == 'BAD':
            vol_stats[vb]['bad'] += 1

    report.append("3. **Volume impact:**")
    for vb in ['>5x', '3-5x', '1.5-3x', '<1.5x']:
        if vol_stats[vb]['total'] > 0:
            report.append(f"   - {vb}: GOOD={format_pct(vol_stats[vb]['good'], vol_stats[vb]['total'])}, BAD={format_pct(vol_stats[vb]['bad'], vol_stats[vb]['total'])} (n={vol_stats[vb]['total']})")
    report.append("")

    # Time insight
    time_stats = defaultdict(lambda: {'good': 0, 'bad': 0, 'total': 0})
    for sig, exc, cls in all_signals:
        tb = time_bucket(sig['timestamp'])
        time_stats[tb]['total'] += 1
        if cls == 'GOOD':
            time_stats[tb]['good'] += 1
        elif cls == 'BAD':
            time_stats[tb]['bad'] += 1

    report.append("4. **Time-of-day impact:**")
    for tb in ['9:30-10:00', '10:00-11:00', '11:00-13:00', '13:00-16:00']:
        if time_stats[tb]['total'] > 0:
            report.append(f"   - {tb}: GOOD={format_pct(time_stats[tb]['good'], time_stats[tb]['total'])}, BAD={format_pct(time_stats[tb]['bad'], time_stats[tb]['total'])} (n={time_stats[tb]['total']})")
    report.append("")

    # CONF insight
    conf_stats = defaultdict(lambda: {'good': 0, 'bad': 0, 'total': 0})
    for sig, exc, cls in all_signals:
        ck = conf_fn(sig)
        conf_stats[ck]['total'] += 1
        if cls == 'GOOD':
            conf_stats[ck]['good'] += 1
        elif cls == 'BAD':
            conf_stats[ck]['bad'] += 1

    report.append("5. **CONF impact:**")
    for ck in ['CONF Pass', 'CONF Fail', 'No CONF']:
        if conf_stats[ck]['total'] > 0:
            report.append(f"   - {ck}: GOOD={format_pct(conf_stats[ck]['good'], conf_stats[ck]['total'])}, BAD={format_pct(conf_stats[ck]['bad'], conf_stats[ck]['total'])} (n={conf_stats[ck]['total']})")
    report.append("")

    # Position quality insight
    pos_stats = defaultdict(lambda: {'good': 0, 'bad': 0, 'total': 0})
    for sig, exc, cls in all_signals:
        pq = pos_quality(sig)
        pos_stats[pq]['total'] += 1
        if cls == 'GOOD':
            pos_stats[pq]['good'] += 1
        elif cls == 'BAD':
            pos_stats[pq]['bad'] += 1

    report.append("6. **Position quality impact:**")
    for pq in ['extreme', 'normal']:
        if pos_stats[pq]['total'] > 0:
            report.append(f"   - {pq} (pos {'>=80' if pq == 'extreme' else '<80'}): GOOD={format_pct(pos_stats[pq]['good'], pos_stats[pq]['total'])}, BAD={format_pct(pos_stats[pq]['bad'], pos_stats[pq]['total'])} (n={pos_stats[pq]['total']})")
    report.append("")

    # Level insight
    level_stats = defaultdict(lambda: {'good': 0, 'bad': 0, 'total': 0})
    for sig, exc, cls in all_signals:
        for lvl in sig['levels']:
            level_stats[lvl]['total'] += 1
            if cls == 'GOOD':
                level_stats[lvl]['good'] += 1
            elif cls == 'BAD':
                level_stats[lvl]['bad'] += 1

    report.append("7. **Level type impact (sorted by GOOD%):**")
    sorted_levels = sorted(level_stats.items(), key=lambda x: x[1]['good']/max(x[1]['total'],1), reverse=True)
    for lvl, stats in sorted_levels:
        if stats['total'] >= 3:
            report.append(f"   - {lvl}: GOOD={format_pct(stats['good'], stats['total'])}, BAD={format_pct(stats['bad'], stats['total'])} (n={stats['total']})")
    report.append("")

    # ===== PERCENTILE DISTRIBUTIONS =====
    report.append("## 13. MFE/ATR Distribution (30m window)")
    report.append("")
    report.append("Shows what fraction of signals reached various MFE thresholds within 30 minutes.")
    report.append("")

    thresholds_atr = [0.05, 0.10, 0.15, 0.20, 0.30, 0.50, 0.75, 1.00]
    # Overall
    mfe30_all = [e[30]['mfe_atr'] for _, e, _ in all_signals if e.get(30)]
    n_all = len(mfe30_all)
    report.append("### Overall")
    report.append("")
    report.append("| MFE threshold (x ATR) | Signals reaching | % |")
    report.append("|----------------------|-----------------|---|")
    for t in thresholds_atr:
        cnt = sum(1 for m in mfe30_all if m >= t)
        report.append(f"| >= {t:.2f} | {cnt} | {format_pct(cnt, n_all)} |")
    report.append("")

    # By signal type
    report.append("### By Signal Type (30m MFE >= threshold)")
    report.append("")
    type_header = ["Threshold"]
    for st in ['BRK', '~', '~~']:
        type_header.extend([f"{st} count", f"{st} %"])
    report.append("| " + " | ".join(type_header) + " |")
    report.append("|" + "|".join(["---"] * len(type_header)) + "|")
    type_mfe = {}
    for st in ['BRK', '~', '~~']:
        type_mfe[st] = [e[30]['mfe_atr'] for s, e, _ in all_signals if e.get(30) and s['type'] == st]
    for t in thresholds_atr:
        row = [f">= {t:.2f}"]
        for st in ['BRK', '~', '~~']:
            cnt = sum(1 for m in type_mfe[st] if m >= t)
            n_st = len(type_mfe[st])
            row.extend([str(cnt), format_pct(cnt, n_st)])
        report.append("| " + " | ".join(row) + " |")
    report.append("")

    # ===== SOFTER CLASSIFICATION =====
    report.append("## 14. Alternative Classification (Softer Thresholds)")
    report.append("")
    report.append("Using MFE > 0.2*ATR in 30m with MFE > 1.5*MAE for GOOD, MAE > 0.3*ATR in 15m for BAD:")
    report.append("")

    def classify_soft(exc, atr):
        if exc.get(15) and exc[15]['mae'] > 0.3 * atr:
            return 'BAD'
        if exc.get(30):
            e30 = exc[30]
            mae_for_ratio = max(e30['mae'], 0.001)
            if e30['mfe'] > 0.2 * atr and e30['mfe'] > 1.5 * mae_for_ratio:
                return 'GOOD'
        return 'NEUTRAL'

    soft_results = [(s, e, classify_soft(e, s['atr'])) for s, e, _ in all_signals]
    s_total = len(soft_results)
    s_good = sum(1 for _, _, c in soft_results if c == 'GOOD')
    s_bad = sum(1 for _, _, c in soft_results if c == 'BAD')
    s_neutral = s_total - s_good - s_bad

    report.append(f"| Classification | Count | Percentage |")
    report.append(f"|---------------|-------|------------|")
    report.append(f"| GOOD | {s_good} | {format_pct(s_good, s_total)} |")
    report.append(f"| BAD | {s_bad} | {format_pct(s_bad, s_total)} |")
    report.append(f"| NEUTRAL | {s_neutral} | {format_pct(s_neutral, s_total)} |")
    report.append("")

    # Soft classification breakdowns
    report.append("### Soft Classification by Signal Type")
    report.append("")
    report.append(aggregate_stats(soft_results, lambda s: s['type'], "Signal Type"))
    report.append("")

    report.append("### Soft Classification by CONF Outcome")
    report.append("")
    report.append(aggregate_stats(soft_results, conf_fn, "CONF"))
    report.append("")

    report.append("### Soft Classification by Time of Day")
    report.append("")
    report.append(aggregate_stats(soft_results, lambda s: time_bucket(s['timestamp']), "Time"))
    report.append("")

    report.append("### Soft Classification by Level Type")
    report.append("")
    report.append(aggregate_stats(soft_results, level_fn, "Level"))
    report.append("")

    report.append("### Soft Classification by Volume Bucket")
    report.append("")
    report.append(aggregate_stats(soft_results, lambda s: vol_bucket(s['vol_ratio']), "Volume"))
    report.append("")

    # ===== COMBINED FILTERS =====
    report.append("## 15. Combined Filter Analysis")
    report.append("")
    report.append("Testing specific filter combinations to find high-quality setups:")
    report.append("")

    combos = [
        ("BRK + CONF Pass + >5x vol", lambda s: s['type'] == 'BRK' and s['conf'] == '✓' and s['vol_ratio'] > 5),
        ("BRK + CONF Pass", lambda s: s['type'] == 'BRK' and s['conf'] == '✓'),
        ("~ + >5x vol + 9:30-10:00", lambda s: s['type'] == '~' and s['vol_ratio'] > 5 and time_bucket(s['timestamp']) == '9:30-10:00'),
        ("BRK + Yest/Week levels", lambda s: s['type'] == 'BRK' and any(l in ['Yest H','Yest L','Week H','Week L'] for l in s['levels'])),
        ("Any + CONF Pass + extreme pos", lambda s: s['conf'] == '✓' and pos_quality(s) == 'extreme'),
        ("BRK + >5x vol + extreme pos", lambda s: s['type'] == 'BRK' and s['vol_ratio'] > 5 and pos_quality(s) == 'extreme'),
        ("~ reversal + CONF none (no BRK preceding)", lambda s: s['type'] == '~' and s['conf'] is None),
        ("~~ reclaim only", lambda s: s['type'] == '~~'),
        ("Any + 11:00-16:00", lambda s: time_bucket(s['timestamp']) in ['11:00-13:00', '13:00-16:00']),
        ("Any + <1.5x vol", lambda s: s['vol_ratio'] < 1.5),
    ]

    headers_combo = ["Filter", "N", "GOOD", "BAD", "NEUT", "GOOD%", "BAD%", "Avg MFE/ATR 30m", "Avg MAE/ATR 15m"]
    rows_combo = []
    for label, fn in combos:
        subset = [(s, e, c) for s, e, c in soft_results if fn(s)]
        n = len(subset)
        if n == 0:
            rows_combo.append([label, 0, 0, 0, 0, "N/A", "N/A", "N/A", "N/A"])
            continue
        g = sum(1 for _, _, c in subset if c == 'GOOD')
        b = sum(1 for _, _, c in subset if c == 'BAD')
        ne = n - g - b
        mfe_vals = [e[30]['mfe_atr'] for _, e, _ in subset if e.get(30)]
        mae_vals = [e[15]['mae_atr'] for _, e, _ in subset if e.get(15)]
        avg_mfe = sum(mfe_vals)/len(mfe_vals) if mfe_vals else 0
        avg_mae = sum(mae_vals)/len(mae_vals) if mae_vals else 0
        rows_combo.append([label, n, g, b, ne, format_pct(g, n), format_pct(b, n), f"{avg_mfe:.3f}", f"{avg_mae:.3f}"])

    report.append(format_table(rows_combo, headers_combo))
    report.append("")

    # ===== SIGNALS WITHOUT CANDLE DATA =====
    report.append("## 16. Signals Without Candle Data")
    report.append("")
    report.append(f"**Total:** {len(no_candle_data)} signals could not be analyzed (no matching 1m candle data)")
    report.append("")

    # Group by symbol
    no_data_by_symbol = defaultdict(int)
    for sig in no_candle_data:
        no_data_by_symbol[sig['symbol']] += 1

    for sym in sorted(no_data_by_symbol.keys()):
        report.append(f"- {sym}: {no_data_by_symbol[sym]} signals")
    report.append("")

    # Date range of missing signals
    if no_candle_data:
        dates = sorted(set(s['timestamp'].date() for s in no_candle_data))
        report.append(f"Date range of unmeasured signals: {dates[0]} to {dates[-1]}")

    # Write report
    output_path = os.path.join(BASE, "follow-through-analysis.md")
    with open(output_path, 'w') as f:
        f.write("\n".join(report))

    print(f"\nReport written to: {output_path}")
    print(f"GOOD: {good}/{total} ({format_pct(good, total)}), BAD: {bad}/{total} ({format_pct(bad, total)}), NEUTRAL: {neutral}/{total} ({format_pct(neutral, total)})")

if __name__ == "__main__":
    main()
