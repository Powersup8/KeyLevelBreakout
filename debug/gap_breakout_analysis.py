#!/usr/bin/env python3
"""
Gap Breakout Analysis for KeyLevelBreakout v2.4
Quantifies how often BRK signals fire at 9:30/9:35/9:40 (likely gap breakouts).
Output: debug/gap-breakout-analysis.md
"""

import re
import os
from collections import defaultdict
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(BASE, "gap-breakout-analysis.md")

# Verified file→symbol mapping from v24_gap_analysis.py
FILE_SYMBOL_MAP = {
    "82a0f": "SPY",
    "42d0e": "AAPL",
    "842b7": "AMD",
    "95b93": "AMZN",
    "1d173": "GLD",
    "51c09": "GOOGL",
    "484bf": "META",
    "493eb": "MSFT",
    "7759b": "NVDA",
    "4e835": "QQQ",
    "65f3b": "SLV",
    "83e42": "TSLA",
    "369c4": "TSM",
}


def parse_time(ts_str):
    ts_str = ts_str.strip().strip('"')
    ts_str = re.sub(r'\.\d+', '', ts_str)
    try:
        return datetime.fromisoformat(ts_str)
    except ValueError:
        return datetime.strptime(ts_str[:19], '%Y-%m-%dT%H:%M:%S')


def detect_symbol(filepath):
    basename = os.path.basename(filepath)
    m = re.search(r'_([a-f0-9]+)\.csv$', basename)
    if m:
        return FILE_SYMBOL_MAP.get(m.group(1))
    return None


def load_all_signals():
    """Load all BRK signals from v2.4 pine log files with CONF matching."""
    import glob
    pattern = os.path.join(BASE, "pine-logs-Key Level Breakout_*.csv")
    files = sorted(glob.glob(pattern))

    all_brk = []

    for fpath in files:
        symbol = detect_symbol(fpath)
        if not symbol:
            continue

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

        file_brk = []
        file_confs = []

        for raw in joined:
            m = re.match(r'^"?([\dT:.+-]+)"?\s*,\s*"?\[KLB\]\s*(.*)', raw)
            if not m:
                continue
            ts = parse_time(m.group(1))
            msg = m.group(2).rstrip('"').strip()

            # CONF outcome
            conf_m = re.match(
                r'CONF\s+[\d:]+\s+([▲▼])\s+(BRK|~~|~)\s+→\s+(✓★|✓|✗)',
                msg
            )
            if conf_m:
                direction = 'bull' if conf_m.group(1) == '▲' else 'bear'
                sig_type = conf_m.group(2)
                raw_result = conf_m.group(3)
                result = 'pass_star' if raw_result == '✓★' else ('pass' if raw_result == '✓' else 'fail')
                file_confs.append({
                    'timestamp': ts,
                    'date': ts.date(),
                    'direction': direction,
                    'sig_type': sig_type,
                    'result': result,
                })
                continue

            # BRK signal only
            sig_m = re.match(r'[\d:]+\s+([▲▼])\s+(BRK)\s+(.*)', msg)
            if not sig_m:
                continue

            direction = 'bull' if sig_m.group(1) == '▲' else 'bear'
            rest = sig_m.group(3).strip()

            vol_m = re.search(r'vol=([\d.]+)x', rest)
            pos_m = re.search(r'pos=([v^])(\d+)', rest)
            atr_m = re.search(r'ATR=([\d.]+)', rest)
            ohlc_m = re.search(r'O([\d.]+)\s+H([\d.]+)\s+L([\d.]+)\s+C([\d.]+)', rest)

            if not (vol_m and pos_m and atr_m and ohlc_m):
                continue

            vol_ratio = float(vol_m.group(1))
            pos_dir = pos_m.group(1)
            pos_val = int(pos_m.group(2))
            atr = float(atr_m.group(1))
            open_price = float(ohlc_m.group(1))
            high_price = float(ohlc_m.group(2))
            low_price = float(ohlc_m.group(3))
            close_price = float(ohlc_m.group(4))

            # Level info: everything before vol=
            level_part = re.split(r'\s+vol=', rest)[0].strip()
            level_part = re.sub(r'^[~]+\s+', '', level_part).strip()
            level_part = re.sub(r'\+\s+~+\s+', '+ ', level_part)
            levels = [l.strip() for l in level_part.split('+') if l.strip()]

            # Time of day (ET already in timestamp)
            bar_time_hm = (ts.hour, ts.minute)

            file_brk.append({
                'timestamp': ts,
                'date': ts.date(),
                'bar_hm': bar_time_hm,
                'bar_label': f"{ts.hour}:{ts.minute:02d}",
                'direction': direction,
                'levels': levels,
                'vol_ratio': vol_ratio,
                'pos_dir': pos_dir,
                'pos_val': pos_val,
                'atr': atr,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'symbol': symbol,
                'conf': None,
                'conf_star': False,
            })

        # Match CONFs to BRKs (most recent BRK before CONF, same date+direction)
        brk_sorted = sorted(file_brk, key=lambda s: s['timestamp'])
        confs_sorted = sorted(file_confs, key=lambda c: c['timestamp'])
        for c in confs_sorted:
            for sig in reversed(brk_sorted):
                if (sig['date'] == c['date'] and
                        sig['direction'] == c['direction'] and
                        sig['timestamp'] <= c['timestamp'] and
                        sig['conf'] is None):
                    sig['conf'] = c['result']
                    sig['conf_star'] = c['result'] == 'pass_star'
                    break

        all_brk.extend(file_brk)

    return all_brk


def fmt_pct(num, denom):
    if denom == 0:
        return "—"
    return f"{100 * num / denom:.1f}%"


def fmt_table(headers, rows):
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    lines = []
    lines.append("| " + " | ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers)) + " |")
    lines.append("|" + "|".join("-" * (w + 2) for w in widths) + "|")
    for row in rows:
        lines.append("| " + " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(row)) + " |")
    return "\n".join(lines)


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


def time_group(bar_hm):
    h, m = bar_hm
    t = h * 60 + m
    if t < 600:      # before 10:00
        return '9:30-10:00'
    elif t < 660:    # 10:00-11:00
        return '10:00-11:00'
    elif t < 780:    # 11:00-13:00
        return '11:00-13:00'
    else:
        return '13:00-16:00'


def conf_stats(sigs):
    """Return (conf_rate%, conf_star_count, n_with_conf, total_n)"""
    total = len(sigs)
    with_conf = [s for s in sigs if s['conf'] is not None]
    passes = [s for s in with_conf if s['conf'] in ('pass', 'pass_star')]
    stars = [s for s in with_conf if s['conf_star']]
    rate = f"{100 * len(passes) / len(with_conf):.1f}%" if with_conf else "—"
    return rate, len(stars), len(with_conf), total


def main():
    print("Loading pine log signals...")
    all_brk = load_all_signals()
    total = len(all_brk)
    print(f"  Total BRK signals: {total}")

    # Overall CONF stats
    with_conf = [s for s in all_brk if s['conf'] is not None]
    passes = [s for s in with_conf if s['conf'] in ('pass', 'pass_star')]
    stars = [s for s in all_brk if s['conf_star']]
    overall_conf_rate = 100 * len(passes) / len(with_conf) if with_conf else 0
    print(f"  Overall CONF rate: {overall_conf_rate:.1f}%  stars: {len(stars)}")

    report = []
    report.append("# Gap Breakout Analysis — KeyLevelBreakout v2.4")
    report.append("")
    report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"**Total BRK signals analyzed:** {total}")
    report.append(f"**Symbols:** {', '.join(sorted(set(s['symbol'] for s in all_brk)))}")
    report.append(f"**Date range:** {min(s['date'] for s in all_brk)} to {max(s['date'] for s in all_brk)}")
    report.append(f"**Overall CONF rate (of signals with CONF):** {overall_conf_rate:.1f}%  (n={len(with_conf)})")
    report.append(f"**Overall ✓★ count:** {len(stars)}")
    report.append("")

    # ── Section A: Time distribution ──────────────────────────────────────────
    report.append("## A. Time Distribution of BRK Signals")
    report.append("")
    report.append("How many BRK signals fire at each 5m bar?")
    report.append("")

    # Collect all bar labels and their counts
    bar_counts = defaultdict(list)
    for s in all_brk:
        bar_counts[s['bar_label']].append(s)

    # Sort bars chronologically
    def bar_sort_key(label):
        parts = label.split(':')
        return int(parts[0]) * 60 + int(parts[1])

    sorted_bars = sorted(bar_counts.keys(), key=bar_sort_key)

    headers_a = ["Bar", "Count", "% of Total", "CONF rate", "✓★"]
    rows_a = []
    for bar in sorted_bars:
        sigs = bar_counts[bar]
        conf_r, star_n, n_conf, n = conf_stats(sigs)
        rows_a.append([
            bar,
            n,
            fmt_pct(n, total),
            conf_r,
            star_n,
        ])
    report.append(fmt_table(headers_a, rows_a))
    report.append("")

    # Morning bars summary
    morning_bars = ['9:30', '9:35', '9:40', '9:45', '9:50', '9:55']
    morning_count = sum(len(bar_counts[b]) for b in morning_bars if b in bar_counts)
    report.append(f"**Opening range (9:30-9:55):** {morning_count} signals = {fmt_pct(morning_count, total)} of all BRK")
    report.append("")

    # ── Section B: 9:35 deep dive ─────────────────────────────────────────────
    report.append("## B. 9:35 Signals Deep Dive")
    report.append("")

    sigs_935 = bar_counts.get('9:35', [])
    n_935 = len(sigs_935)
    report.append(f"**Total 9:35 BRK signals:** {n_935}  ({fmt_pct(n_935, total)} of all BRK)")
    report.append("")

    if sigs_935:
        conf_r, star_n, n_conf, _ = conf_stats(sigs_935)
        report.append(f"**CONF rate (of signals with CONF):** {conf_r}  (n_conf={n_conf})")
        report.append(f"**✓★ count:** {star_n}")
        report.append(f"**Overall CONF rate for comparison:** {overall_conf_rate:.1f}%")
        report.append("")

        # Direction split
        bulls_935 = [s for s in sigs_935 if s['direction'] == 'bull']
        bears_935 = [s for s in sigs_935 if s['direction'] == 'bear']
        report.append(f"**Direction:** {len(bulls_935)} bull ({fmt_pct(len(bulls_935), n_935)}) / "
                       f"{len(bears_935)} bear ({fmt_pct(len(bears_935), n_935)})")
        report.append("")

        # Volume distribution
        report.append("**Volume distribution at 9:35:**")
        report.append("")
        vb_counts_935 = defaultdict(list)
        for s in sigs_935:
            vb_counts_935[vol_bucket(s['vol_ratio'])].append(s)
        headers_vol = ["Volume", "Count", "%", "CONF rate"]
        rows_vol = []
        for vb in ['10x+', '5-10x', '2-5x', '1.5-2x', '<1.5x']:
            vs = vb_counts_935.get(vb, [])
            if vs:
                cr, _, _, _ = conf_stats(vs)
                rows_vol.append([vb, len(vs), fmt_pct(len(vs), n_935), cr])
        report.append(fmt_table(headers_vol, rows_vol))
        report.append("")

        # Level types
        report.append("**Level types at 9:35:**")
        report.append("")
        lvl_counts = defaultdict(int)
        for s in sigs_935:
            for lvl in s['levels']:
                lvl_counts[lvl] += 1
        headers_lvl = ["Level", "Count", "% of 9:35 signals"]
        rows_lvl = sorted(
            [[lvl, cnt, fmt_pct(cnt, n_935)] for lvl, cnt in lvl_counts.items()],
            key=lambda r: -r[1]
        )
        report.append(fmt_table(headers_lvl, rows_lvl))
        report.append("")

        # Symbol breakdown
        report.append("**Symbol breakdown at 9:35:**")
        report.append("")
        sym_counts_935 = defaultdict(list)
        for s in sigs_935:
            sym_counts_935[s['symbol']].append(s)
        headers_sym = ["Symbol", "Count", "CONF rate", "✓★"]
        rows_sym = []
        for sym in sorted(sym_counts_935.keys()):
            ss = sym_counts_935[sym]
            cr, sn, _, _ = conf_stats(ss)
            rows_sym.append([sym, len(ss), cr, sn])
        report.append(fmt_table(headers_sym, rows_sym))
        report.append("")

    # ── Section C: 9:40 deep dive ─────────────────────────────────────────────
    report.append("## C. 9:40 Signals Deep Dive")
    report.append("")

    sigs_940 = bar_counts.get('9:40', [])
    n_940 = len(sigs_940)
    report.append(f"**Total 9:40 BRK signals:** {n_940}  ({fmt_pct(n_940, total)} of all BRK)")
    report.append("")

    if sigs_940:
        conf_r, star_n, n_conf, _ = conf_stats(sigs_940)
        report.append(f"**CONF rate (of signals with CONF):** {conf_r}  (n_conf={n_conf})")
        report.append(f"**✓★ count:** {star_n}")
        report.append(f"**Overall CONF rate for comparison:** {overall_conf_rate:.1f}%")
        report.append("")

        bulls_940 = [s for s in sigs_940 if s['direction'] == 'bull']
        bears_940 = [s for s in sigs_940 if s['direction'] == 'bear']
        report.append(f"**Direction:** {len(bulls_940)} bull ({fmt_pct(len(bulls_940), n_940)}) / "
                       f"{len(bears_940)} bear ({fmt_pct(len(bears_940), n_940)})")
        report.append("")

        report.append("**Volume distribution at 9:40:**")
        report.append("")
        vb_counts_940 = defaultdict(list)
        for s in sigs_940:
            vb_counts_940[vol_bucket(s['vol_ratio'])].append(s)
        rows_vol_940 = []
        for vb in ['10x+', '5-10x', '2-5x', '1.5-2x', '<1.5x']:
            vs = vb_counts_940.get(vb, [])
            if vs:
                cr, _, _, _ = conf_stats(vs)
                rows_vol_940.append([vb, len(vs), fmt_pct(len(vs), n_940), cr])
        report.append(fmt_table(headers_vol, rows_vol_940))
        report.append("")

        # Level types
        report.append("**Level types at 9:40:**")
        report.append("")
        lvl_counts_940 = defaultdict(int)
        for s in sigs_940:
            for lvl in s['levels']:
                lvl_counts_940[lvl] += 1
        rows_lvl_940 = sorted(
            [[lvl, cnt, fmt_pct(cnt, n_940)] for lvl, cnt in lvl_counts_940.items()],
            key=lambda r: -r[1]
        )
        report.append(fmt_table(headers_lvl, rows_lvl_940))
        report.append("")

    # ── Section D: Gap detection heuristic ───────────────────────────────────
    report.append("## D. Gap Detection Heuristic")
    report.append("")
    report.append("Since we lack prior-bar close data, we flag signals by time proximity to open.")
    report.append("")
    report.append("**Heuristic:** Any BRK at 9:30 or 9:35 is flagged as a *potential gap breakout*")
    report.append("(the 5m bar closes at 9:35/9:40, meaning the entire 9:30-9:35 session is included).")
    report.append("9:40 signals are flagged as *second-bar potential gap* — price may have gapped")
    report.append("and consolidated for one bar before the BRK fires.")
    report.append("")

    sigs_930 = bar_counts.get('9:30', [])
    potential_gap = sigs_930 + sigs_935
    second_bar_gap = sigs_940

    report.append(f"- **Potential gap breakouts (9:30 + 9:35):** {len(potential_gap)} signals "
                   f"({fmt_pct(len(potential_gap), total)} of all BRK)")
    report.append(f"- **Second-bar potential gap (9:40):** {len(second_bar_gap)} signals "
                   f"({fmt_pct(len(second_bar_gap), total)} of all BRK)")
    non_gap = [s for s in all_brk if s['bar_hm'] not in [(9,30),(9,35),(9,40)]]
    report.append(f"- **Standard (9:45+) breakouts:** {len(non_gap)} signals "
                   f"({fmt_pct(len(non_gap), total)} of all BRK)")
    report.append("")

    # Body analysis for 9:35 signals: body size relative to ATR
    report.append("### Candle Body Analysis at 9:35")
    report.append("")
    report.append("Body size relative to ATR indicates how 'decisive' the opening bar was.")
    report.append("Large body = gap + momentum; Small body = choppy open.")
    report.append("")

    if sigs_935:
        body_pcts = [(abs(s['close'] - s['open']) / s['atr'] * 100) for s in sigs_935]
        avg_body = sum(body_pcts) / len(body_pcts)
        body_sorted = sorted(body_pcts)
        n_bp = len(body_sorted)
        med_body = body_sorted[n_bp // 2]

        report.append(f"- Average body / ATR at 9:35: {avg_body:.1f}%")
        report.append(f"- Median body / ATR at 9:35: {med_body:.1f}%")

        # Count large vs small body
        large_body = sum(1 for b in body_pcts if b > 30)
        report.append(f"- Body > 30% ATR (gap-like): {large_body} ({fmt_pct(large_body, n_935)})")
        small_body = sum(1 for b in body_pcts if b <= 10)
        report.append(f"- Body <= 10% ATR (indecisive): {small_body} ({fmt_pct(small_body, n_935)})")
        report.append("")

        # Do large-body 9:35 signals confirm better?
        large_935 = [s for s in sigs_935 if abs(s['close'] - s['open']) / s['atr'] > 0.30]
        small_935 = [s for s in sigs_935 if abs(s['close'] - s['open']) / s['atr'] <= 0.10]
        if large_935:
            cr_large, _, _, _ = conf_stats(large_935)
            report.append(f"- Large-body 9:35 CONF rate: {cr_large} (n={len(large_935)})")
        if small_935:
            cr_small, _, _, _ = conf_stats(small_935)
            report.append(f"- Small-body 9:35 CONF rate: {cr_small} (n={len(small_935)})")
        report.append("")

    # ── Section E: Comparison table ───────────────────────────────────────────
    report.append("## E. Comparison Table: Time Cohorts")
    report.append("")
    report.append("CONF rates and signal quality across time cohorts (BRK signals only).")
    report.append("")

    cohorts = [
        ("9:30", [s for s in all_brk if s['bar_hm'] == (9, 30)]),
        ("9:35 (potential gap)", sigs_935),
        ("9:40 (2nd bar gap?)", sigs_940),
        ("9:45-9:55", [s for s in all_brk if s['bar_hm'] in [(9,45),(9,50),(9,55)]]),
        ("10:00-10:55", [s for s in all_brk if 10*60 <= s['bar_hm'][0]*60+s['bar_hm'][1] < 11*60]),
        ("11:00-12:55", [s for s in all_brk if 11*60 <= s['bar_hm'][0]*60+s['bar_hm'][1] < 13*60]),
        ("13:00-16:00", [s for s in all_brk if s['bar_hm'][0]*60+s['bar_hm'][1] >= 13*60]),
        ("ALL", all_brk),
    ]

    headers_e = ["Cohort", "Count", "% of Total", "CONF rate", "✓★", "Bull %", "Avg Vol"]
    rows_e = []
    for label, cohort in cohorts:
        if not cohort:
            rows_e.append([label, 0, "—", "—", 0, "—", "—"])
            continue
        n = len(cohort)
        cr, star_n, n_conf, _ = conf_stats(cohort)
        bull_pct = fmt_pct(sum(1 for s in cohort if s['direction'] == 'bull'), n)
        avg_vol = sum(s['vol_ratio'] for s in cohort) / n
        rows_e.append([label, n, fmt_pct(n, total), cr, star_n, bull_pct, f"{avg_vol:.1f}x"])

    report.append(fmt_table(headers_e, rows_e))
    report.append("")

    # ── Sub-table: 9:35 CONF rate with vs without ✓★ ─────────────────────────
    report.append("### Detailed CONF Breakdown by Cohort")
    report.append("")

    headers_ec = ["Cohort", "N", "N_conf", "Pass", "Fail", "Pass%", "Star%"]
    rows_ec = []
    for label, cohort in cohorts:
        if not cohort:
            continue
        n = len(cohort)
        with_c = [s for s in cohort if s['conf'] is not None]
        pass_c = [s for s in with_c if s['conf'] in ('pass', 'pass_star')]
        fail_c = [s for s in with_c if s['conf'] == 'fail']
        star_c = [s for s in with_c if s['conf_star']]
        rows_ec.append([
            label, n, len(with_c),
            len(pass_c), len(fail_c),
            fmt_pct(len(pass_c), len(with_c)),
            fmt_pct(len(star_c), len(with_c)),
        ])
    report.append(fmt_table(headers_ec, rows_ec))
    report.append("")

    # ── Section F: Recommendation ─────────────────────────────────────────────
    report.append("## F. Recommendation")
    report.append("")

    # Compute key metrics for recommendation
    conf_935 = 0
    n_conf_935 = 0
    if sigs_935:
        wc935 = [s for s in sigs_935 if s['conf'] is not None]
        p935 = [s for s in wc935 if s['conf'] in ('pass', 'pass_star')]
        conf_935 = 100 * len(p935) / len(wc935) if wc935 else 0
        n_conf_935 = len(wc935)

    conf_940 = 0
    if sigs_940:
        wc940 = [s for s in sigs_940 if s['conf'] is not None]
        p940 = [s for s in wc940 if s['conf'] in ('pass', 'pass_star')]
        conf_940 = 100 * len(p940) / len(wc940) if wc940 else 0

    # 10:00-11:00 cohort stats
    prime_cohort = [s for s in all_brk if 10*60 <= s['bar_hm'][0]*60+s['bar_hm'][1] < 11*60]
    wc_prime = [s for s in prime_cohort if s['conf'] is not None]
    p_prime = [s for s in wc_prime if s['conf'] in ('pass', 'pass_star')]
    conf_prime = 100 * len(p_prime) / len(wc_prime) if wc_prime else 0

    report.append(f"### Data Summary")
    report.append(f"- 9:35 signals: {n_935} ({fmt_pct(n_935, total)}) — CONF rate: {conf_935:.1f}%")
    report.append(f"- 9:40 signals: {n_940} ({fmt_pct(n_940, total)}) — CONF rate: {conf_940:.1f}%")
    report.append(f"- 10:00-11:00 (prime): {len(prime_cohort)} signals — CONF rate: {conf_prime:.1f}%")
    report.append(f"- Overall CONF rate: {overall_conf_rate:.1f}%")
    report.append("")

    report.append("### Analysis")
    report.append("")
    report.append("**What is a gap breakout?**")
    report.append("At 9:35, the first complete 5m bar closes. If price gapped UP at the open and")
    report.append("immediately carried through a key level during that first 5m candle, the BRK fires")
    report.append("at 9:35. The trader has no prior price action at that level — just a gap.")
    report.append("")
    report.append("**Key behavioral differences of 9:35 signals:**")
    report.append("- High volume is almost certain (market open = peak volume)")
    report.append("- The breakout candle has no prior failed attempts at the level")
    report.append("- Gap-driven breakouts tend to fill — 'fade the gap' is a well-known strategy")
    report.append("- The opening bar often embeds multiple competing forces (gap fill, momentum, news)")
    report.append("")
    report.append("**What the CONF rate tells us:**")
    report.append("CONF fires 5 bars (5m) after the BRK. A high CONF rate at 9:35 means price")
    report.append("continued in the breakout direction for ~5m. A low CONF rate means reversal.")
    report.append("")

    # Decision logic
    if conf_935 >= overall_conf_rate - 5:
        assessment = "KEEP"
        rationale = (
            f"9:35 CONF rate ({conf_935:.1f}%) is within 5pp of overall ({overall_conf_rate:.1f}%). "
            "These signals are performing comparably to the general population. "
            "Suppression is NOT recommended — they would be discarding real breakouts."
        )
    elif conf_935 >= overall_conf_rate - 15:
        assessment = "FILTER (add conditions)"
        rationale = (
            f"9:35 CONF rate ({conf_935:.1f}%) is moderately below overall ({overall_conf_rate:.1f}%). "
            "Consider adding a filter: only fire 9:35 BRK if vol > 5x AND pos > 80. "
            "This would retain high-conviction gap breakouts while discarding weak ones."
        )
    else:
        assessment = "SUPPRESS"
        rationale = (
            f"9:35 CONF rate ({conf_935:.1f}%) is substantially below overall ({overall_conf_rate:.1f}%). "
            "Gap breakouts at 9:35 are significantly less likely to follow through. "
            "Suppressing or down-grading these signals would improve signal quality."
        )

    report.append(f"### Verdict: **{assessment}** 9:35 signals")
    report.append("")
    report.append(rationale)
    report.append("")

    # ✓★ concentration
    star_at_935 = sum(1 for s in sigs_935 if s['conf_star'])
    report.append(f"**✓★ signal concentration:** {star_at_935}/{len(stars)} of all ✓★ signals "
                   f"({fmt_pct(star_at_935, len(stars)) if stars else '—'}) occur at 9:35.")
    if star_at_935 > 0:
        report.append("Even if suppressing 9:35 overall, consider exempting ✓★ signals.")
    report.append("")

    report.append("### Implementation Options (if filtering is desired)")
    report.append("")
    report.append("1. **Hard suppress:** Skip BRK signals at 9:30 and 9:35 entirely.")
    report.append("   - Simple. Eliminates gap noise. Loses real momentum breakouts.")
    report.append("2. **Soft filter:** Allow 9:35 only if vol ≥ 5x AND pos ≥ 80.")
    report.append("   - More targeted. Preserves high-conviction gap trades.")
    report.append("3. **Dim label:** Show 9:35 signals but with lower alpha / different color.")
    report.append("   - Informational only. Trader still sees the signal but de-prioritized.")
    report.append("4. **No change:** Current behavior. Status quo.")
    report.append("   - Appropriate if CONF rate at 9:35 is not statistically different.")
    report.append("")
    report.append("**Recommended minimum action:** Log `gap=true` on 9:35/9:30 signals in pine")
    report.append("output for future analysis. No behavioral change yet.")
    report.append("")

    # Write report
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write("\n".join(report))

    print(f"\nReport written to: {OUTPUT}")
    return total, n_935, n_940, conf_935, conf_940, overall_conf_rate


if __name__ == "__main__":
    result = main()
    total, n_935, n_940, conf_935, conf_940, overall_conf_rate = result
    print(f"\nSummary:")
    print(f"  Total BRK: {total}")
    print(f"  9:35 signals: {n_935} — CONF rate: {conf_935:.1f}%")
    print(f"  9:40 signals: {n_940} — CONF rate: {conf_940:.1f}%")
    print(f"  Overall CONF rate: {overall_conf_rate:.1f}%")
