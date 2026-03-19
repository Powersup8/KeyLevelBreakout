#!/usr/bin/env python3
"""
Comprehensive analysis of all v3.7a KLB pine log files.
Outputs a markdown report to pine-log-analysis-v37a.md
"""

import csv
import os
import glob
import re
from collections import defaultdict
from datetime import datetime

BASE = "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug"
OUTPUT = os.path.join(BASE, "pine-log-analysis-v37a.md")

# ─── 1. Find all v3.7a files ──────────────────────────────────────────────────
files = sorted(glob.glob(os.path.join(BASE, "pine-logs-Key Level Breakout v3.7a_*.csv")))
print(f"Found {len(files)} files")

# ─── 2. Extract symbol from each file ─────────────────────────────────────────
def extract_symbol(filepath):
    """Read up to 200 rows to find [KLB:SYMBOL] tag."""
    with open(filepath, newline='', encoding='utf-8') as fh:
        reader = csv.reader(fh)
        next(reader, None)  # skip header
        for i, row in enumerate(reader):
            if i > 200:
                break
            if len(row) < 2:
                continue
            msg = row[1]
            m = re.search(r'\[KLB:([A-Z]+)\]', msg)
            if m:
                return m.group(1)
    return "UNKNOWN"

hash_to_symbol = {}
for f in files:
    h = os.path.basename(f).replace("pine-logs-Key Level Breakout v3.7a_", "").replace(".csv", "")
    sym = extract_symbol(f)
    hash_to_symbol[h] = sym

# ─── 3. Parse all rows ────────────────────────────────────────────────────────

# Data structures
records = []   # list of dicts per meaningful row

def classify_row(msg):
    """Return dict with parsed fields, or None if not a signal/check row."""
    result = {
        'raw': msg,
        'symbol': None,
        'date': None,
        'time': None,
        'sig_type': None,   # BRK, REV, FADE, RNG, QBS, CONF_OK, CONF_FAIL, CHECK
        'direction': None,  # bull, bear
        'is_dim': False,
        'pnl': None,
        'check_outcome': None,  # HOLD or BAIL
        'vol': None,
        'conf_type': None,   # what type was CONFed (BRK, QBS, etc.)
    }

    # Extract symbol
    m = re.search(r'\[KLB:([A-Z]+)\]', msg)
    if m:
        result['symbol'] = m.group(1)
    else:
        result['symbol'] = 'SPY'  # old [KLB] entries are SPY

    # Extract time from message
    m = re.search(r'\b(\d{1,2}:\d{2})\b', msg)
    if m:
        result['time'] = m.group(1)

    # CONF rows
    if 'CONF' in msg and ('✓' in msg or '✗' in msg):
        result['sig_type'] = 'CONF_OK' if '✓' in msg else 'CONF_FAIL'
        result['direction'] = 'bull' if '▲' in msg else ('bear' if '▼' in msg else None)
        # Extract what type was confed
        cm = re.search(r'CONF\s+\S+\s+[▲▼]\s+(\w+)', msg)
        if cm:
            result['conf_type'] = cm.group(1)
        return result

    # 5m CHECK rows
    if '5m CHECK' in msg:
        result['sig_type'] = 'CHECK'
        result['direction'] = 'bull' if '▲' in msg else ('bear' if '▼' in msg else None)
        pm = re.search(r'pnl=(-?\d+\.?\d*)', msg)
        if pm:
            result['pnl'] = float(pm.group(1))
        result['check_outcome'] = 'BAIL' if 'BAIL' in msg else 'HOLD'
        return result

    # Direction
    result['direction'] = 'bull' if '▲' in msg else ('bear' if '▼' in msg else None)

    # RNG
    if 'RNG range break' in msg:
        result['sig_type'] = 'RNG'
        vm = re.search(r'vol=(\d+\.?\d*)x', msg)
        if vm:
            result['vol'] = float(vm.group(1))
        return result

    # FADE
    if 'FADE' in msg and 'vol=' not in msg:
        result['sig_type'] = 'FADE'
        return result

    # QBS
    if 'QBS' in msg:
        result['sig_type'] = 'QBS'
        vm = re.search(r'vol=(\d+\.?\d*)x', msg)
        if vm:
            result['vol'] = float(vm.group(1))
        return result

    # REV: contains ~ before level name
    if '~' in msg and 'vol=' in msg:
        result['sig_type'] = 'REV'
        vm = re.search(r'vol=(\d+\.?\d*)x', msg)
        if vm:
            result['vol'] = float(vm.group(1))
        # Dim: message has ? suffix or dim-related marker
        # In v3.7a, dim signals often have 'x~' or '?' patterns
        if 'x~' in msg or '?' in msg:
            result['is_dim'] = True
        return result

    # BRK: has vol= but no RNG/FADE/QBS/~
    if 'vol=' in msg and 'RNG' not in msg and 'FADE' not in msg and 'QBS' not in msg and '~' not in msg:
        result['sig_type'] = 'BRK'
        vm = re.search(r'vol=(\d+\.?\d*)x', msg)
        if vm:
            result['vol'] = float(vm.group(1))
        if '?' in msg:
            result['is_dim'] = True
        return result

    return None


# ─── Process all files ────────────────────────────────────────────────────────
all_records = []
file_stats = []  # per-file summary

for f in files:
    h = os.path.basename(f).replace("pine-logs-Key Level Breakout v3.7a_", "").replace(".csv", "")
    sym = hash_to_symbol.get(h, 'UNKNOWN')
    size_kb = os.path.getsize(f) // 1024
    file_type = 'large' if size_kb > 50 else 'small'

    row_count = 0
    parsed_count = 0
    min_date = None
    max_date = None

    with open(f, newline='', encoding='utf-8') as fh:
        reader = csv.reader(fh)
        next(reader, None)
        for row in reader:
            if len(row) < 2:
                continue
            row_count += 1
            ts_str = row[0].strip()
            msg = row[1].strip()

            # Parse date from ISO timestamp
            try:
                # e.g. 2026-02-05T10:00:00.000-05:00
                dt = datetime.fromisoformat(ts_str.replace('.000', ''))
                date_str = dt.strftime('%Y-%m-%d')
            except Exception:
                date_str = ts_str[:10]

            rec = classify_row(msg)
            if rec is None:
                continue

            rec['date'] = date_str
            rec['file_hash'] = h
            rec['file_symbol'] = sym  # symbol from file detection
            if rec['symbol'] is None:
                rec['symbol'] = sym

            all_records.append(rec)
            parsed_count += 1

            if min_date is None or date_str < min_date:
                min_date = date_str
            if max_date is None or date_str > max_date:
                max_date = date_str

    file_stats.append({
        'hash': h,
        'symbol': sym,
        'size_kb': size_kb,
        'type': file_type,
        'total_rows': row_count,
        'parsed': parsed_count,
        'min_date': min_date,
        'max_date': max_date,
    })

print(f"Total parsed records: {len(all_records)}")

# ─── 4. Compute statistics ────────────────────────────────────────────────────

# Separate by type
signals = [r for r in all_records if r['sig_type'] in ('BRK', 'REV', 'FADE', NG := 'RNG', 'QBS')]
# Fix: include RNG properly
signals = [r for r in all_records if r['sig_type'] in ('BRK', 'REV', 'FADE', 'RNG', 'QBS')]
confs = [r for r in all_records if r['sig_type'] in ('CONF_OK', 'CONF_FAIL')]
checks = [r for r in all_records if r['sig_type'] == 'CHECK']

# Overall counts by type
type_counts = defaultdict(int)
for r in signals:
    type_counts[r['sig_type']] += 1

# By symbol
symbol_counts = defaultdict(lambda: defaultdict(int))
for r in signals:
    sym = r['symbol']
    symbol_counts[sym]['total'] += 1
    symbol_counts[sym][r['sig_type']] += 1
    if r['direction'] == 'bull':
        symbol_counts[sym]['bull'] += 1
    elif r['direction'] == 'bear':
        symbol_counts[sym]['bear'] += 1

# By date
date_counts = defaultdict(int)
for r in signals:
    date_counts[r['date']] += 1

# CONF stats
conf_ok = len([r for r in confs if r['sig_type'] == 'CONF_OK'])
conf_fail = len([r for r in confs if r['sig_type'] == 'CONF_FAIL'])
conf_total = conf_ok + conf_fail
conf_rate = conf_ok / conf_total * 100 if conf_total > 0 else 0

# CONF by type
conf_type_ok = defaultdict(int)
conf_type_fail = defaultdict(int)
for r in confs:
    ct = r.get('conf_type', 'unknown') or 'unknown'
    if r['sig_type'] == 'CONF_OK':
        conf_type_ok[ct] += 1
    else:
        conf_type_fail[ct] += 1

# 5m CHECK stats
hold_records = [r for r in checks if r['check_outcome'] == 'HOLD']
bail_records = [r for r in checks if r['check_outcome'] == 'BAIL']
hold_count = len(hold_records)
bail_count = len(bail_records)
total_checks = len(checks)
bail_rate = bail_count / total_checks * 100 if total_checks > 0 else 0

hold_pnls = [r['pnl'] for r in hold_records if r['pnl'] is not None]
bail_pnls = [r['pnl'] for r in bail_records if r['pnl'] is not None]
all_pnls = [r['pnl'] for r in checks if r['pnl'] is not None]

def avg(lst):
    return sum(lst) / len(lst) if lst else 0

# By symbol for checks
check_by_symbol = defaultdict(lambda: {'hold': 0, 'bail': 0, 'hold_pnl': [], 'bail_pnl': []})
for r in checks:
    sym = r['symbol']
    if r['check_outcome'] == 'HOLD':
        check_by_symbol[sym]['hold'] += 1
        if r['pnl'] is not None:
            check_by_symbol[sym]['hold_pnl'].append(r['pnl'])
    else:
        check_by_symbol[sym]['bail'] += 1
        if r['pnl'] is not None:
            check_by_symbol[sym]['bail_pnl'].append(r['pnl'])

# Date range
all_dates = [r['date'] for r in all_records if r['date']]
min_date_overall = min(all_dates) if all_dates else 'N/A'
max_date_overall = max(all_dates) if all_dates else 'N/A'

# Top days by signal count
top_days = sorted(date_counts.items(), key=lambda x: x[1], reverse=True)[:15]

# Dim vs non-dim BRK/REV
brk_records = [r for r in signals if r['sig_type'] == 'BRK']
rev_records = [r for r in signals if r['sig_type'] == 'REV']
brk_dim = [r for r in brk_records if r['is_dim']]
brk_nondim = [r for r in brk_records if not r['is_dim']]
rev_dim = [r for r in rev_records if r['is_dim']]
rev_nondim = [r for r in rev_records if not r['is_dim']]

# Time-of-day distribution for signals
def time_bucket(t):
    if t is None:
        return 'unknown'
    try:
        h, m = map(int, t.split(':'))
        mins = h * 60 + m
        if mins < 9 * 60 + 30:
            return 'pre-market (<9:30)'
        elif mins < 11 * 60:
            return 'morning (9:30-11)'
        elif mins < 14 * 60:
            return 'midday (11-14)'
        elif mins < 16 * 60:
            return 'afternoon (14-16)'
        else:
            return 'post-market (>16:00)'
    except:
        return 'unknown'

time_dist = defaultdict(int)
for r in signals:
    time_dist[time_bucket(r.get('time'))] += 1

# Per-symbol CONF rate
conf_by_symbol = defaultdict(lambda: {'ok': 0, 'fail': 0})
for r in confs:
    sym = r['symbol']
    if r['sig_type'] == 'CONF_OK':
        conf_by_symbol[sym]['ok'] += 1
    else:
        conf_by_symbol[sym]['fail'] += 1

# Vol stats for BRK/REV
brk_vols = [r['vol'] for r in brk_records if r['vol'] is not None]
rev_vols = [r['vol'] for r in rev_records if r['vol'] is not None]

# Daily signal counts grouped by symbol for finding peak days
daily_by_sym = defaultdict(lambda: defaultdict(int))
for r in signals:
    daily_by_sym[r['symbol']][r['date']] += 1

# ─── 5. Step 5: Must-trade signal performance ─────────────────────────────────
# Non-dim BRK and REV signals paired with their CONF and CHECK rows
# Strategy: since we can't directly pair rows by timestamp perfectly,
# we count non-dim BRK+REV CONF_OK rate and 5m CHECK outcomes by direction/type

must_trade_signals = [r for r in signals if r['sig_type'] in ('BRK', 'REV') and not r['is_dim']]
mt_bull = [r for r in must_trade_signals if r['direction'] == 'bull']
mt_bear = [r for r in must_trade_signals if r['direction'] == 'bear']

# 5m CHECK pnl by direction
check_bull = [r for r in checks if r['direction'] == 'bull']
check_bear = [r for r in checks if r['direction'] == 'bear']
bull_hold_pnl = [r['pnl'] for r in check_bull if r['check_outcome'] == 'HOLD' and r['pnl'] is not None]
bull_bail_pnl = [r['pnl'] for r in check_bull if r['check_outcome'] == 'BAIL' and r['pnl'] is not None]
bear_hold_pnl = [r['pnl'] for r in check_bear if r['check_outcome'] == 'HOLD' and r['pnl'] is not None]
bear_bail_pnl = [r['pnl'] for r in check_bear if r['check_outcome'] == 'BAIL' and r['pnl'] is not None]

# pnl > 0 win rate for checks
def win_rate(pnls):
    if not pnls:
        return 0
    return sum(1 for p in pnls if p > 0) / len(pnls) * 100

# CONF rate for BRK vs REV
brk_confs = [r for r in confs if r.get('conf_type') == 'BRK']
rev_confs = [r for r in confs if r.get('conf_type') == 'REV']
qbs_confs = [r for r in confs if r.get('conf_type') == 'QBS']

# ─── 6. Generate report ───────────────────────────────────────────────────────

lines = []
lines.append("# KLB Pine Log Analysis — v3.7a")
lines.append(f"\n_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_")
lines.append(f"\n**Files processed:** {len(files)} total ({sum(1 for fs in file_stats if fs['type'] == 'large')} large, {sum(1 for fs in file_stats if fs['type'] == 'small')} small)")
lines.append(f"\n**Date range:** {min_date_overall} → {max_date_overall}")
lines.append(f"\n**Total rows parsed into signal records:** {len(all_records):,}")

lines.append("\n\n---\n")
lines.append("## 1. File → Symbol Mapping\n")
lines.append("| Hash | Symbol | Size (KB) | Type | Date Range | Parsed Rows |")
lines.append("|------|--------|-----------|------|------------|-------------|")
for fs in sorted(file_stats, key=lambda x: (x['symbol'], x['min_date'] or '')):
    lines.append(f"| {fs['hash']} | **{fs['symbol']}** | {fs['size_kb']} | {fs['type']} | {fs['min_date']} → {fs['max_date']} | {fs['parsed']:,} |")

lines.append("\n\n---\n")
lines.append("## 2. Overall Signal Counts by Type\n")
lines.append(f"**Total signals:** {sum(type_counts.values()):,}\n")
lines.append("| Signal Type | Count | % of Total |")
lines.append("|-------------|-------|------------|")
total_sig = sum(type_counts.values())
for st in ['BRK', 'REV', 'FADE', 'RNG', 'QBS']:
    c = type_counts.get(st, 0)
    pct = c / total_sig * 100 if total_sig > 0 else 0
    lines.append(f"| {st} | {c:,} | {pct:.1f}% |")

lines.append(f"\n**Also:** CONF rows: {conf_total:,} | 5m CHECK rows: {total_checks:,}")

lines.append("\n\n---\n")
lines.append("## 3. Signal Counts by Symbol\n")
lines.append("| Symbol | Total | BRK | REV | FADE | RNG | QBS | Bull | Bear |")
lines.append("|--------|-------|-----|-----|------|-----|-----|------|------|")
for sym in sorted(symbol_counts.keys()):
    sc = symbol_counts[sym]
    lines.append(f"| **{sym}** | {sc['total']} | {sc.get('BRK',0)} | {sc.get('REV',0)} | {sc.get('FADE',0)} | {sc.get('RNG',0)} | {sc.get('QBS',0)} | {sc.get('bull',0)} | {sc.get('bear',0)} |")

lines.append("\n\n---\n")
lines.append("## 4. CONF Rate\n")
lines.append(f"- **Total CONF rows:** {conf_total:,}")
lines.append(f"- **CONF ✓:** {conf_ok:,} ({conf_rate:.1f}%)")
lines.append(f"- **CONF ✗:** {conf_fail:,} ({100-conf_rate:.1f}%)")
lines.append("\n### CONF ✓ by signal type promoted:")
lines.append("| Type | CONF ✓ | CONF ✗ | Rate |")
lines.append("|------|--------|--------|------|")
all_conf_types = sorted(set(list(conf_type_ok.keys()) + list(conf_type_fail.keys())))
for ct in all_conf_types:
    ok = conf_type_ok.get(ct, 0)
    fail = conf_type_fail.get(ct, 0)
    total_ct = ok + fail
    rate = ok / total_ct * 100 if total_ct > 0 else 0
    lines.append(f"| {ct} | {ok} | {fail} | {rate:.1f}% |")

lines.append("\n### CONF rate by symbol:")
lines.append("| Symbol | CONF ✓ | CONF ✗ | Rate |")
lines.append("|--------|--------|--------|------|")
for sym in sorted(conf_by_symbol.keys()):
    cs = conf_by_symbol[sym]
    total_cs = cs['ok'] + cs['fail']
    rate = cs['ok'] / total_cs * 100 if total_cs > 0 else 0
    lines.append(f"| **{sym}** | {cs['ok']} | {cs['fail']} | {rate:.1f}% |")

lines.append("\n\n---\n")
lines.append("## 5. 5m CHECK (HOLD vs BAIL) Statistics\n")
lines.append(f"- **Total 5m CHECKs:** {total_checks:,}")
lines.append(f"- **HOLD:** {hold_count:,} ({100-bail_rate:.1f}%)")
lines.append(f"- **BAIL:** {bail_count:,} ({bail_rate:.1f}%)")
lines.append(f"\n**PnL at 5m check (in ATR fractions):**")
lines.append(f"- All checks avg pnl: {avg(all_pnls):+.3f}")
lines.append(f"- HOLD checks avg pnl: {avg(hold_pnls):+.3f} (n={len(hold_pnls)})")
lines.append(f"- BAIL checks avg pnl: {avg(bail_pnls):+.3f} (n={len(bail_pnls)})")
lines.append(f"- Win rate at check time (pnl>0): {win_rate(all_pnls):.1f}%")
lines.append(f"  - HOLD win rate: {win_rate(hold_pnls):.1f}%")
lines.append(f"  - BAIL win rate: {win_rate(bail_pnls):.1f}%")

lines.append("\n### 5m CHECK by direction:")
lines.append(f"- Bull HOLD avg pnl: {avg(bull_hold_pnl):+.3f} (n={len(bull_hold_pnl)}), BAIL avg: {avg(bull_bail_pnl):+.3f} (n={len(bull_bail_pnl)})")
lines.append(f"- Bear HOLD avg pnl: {avg(bear_hold_pnl):+.3f} (n={len(bear_hold_pnl)}), BAIL avg: {avg(bear_bail_pnl):+.3f} (n={len(bear_bail_pnl)})")

lines.append("\n### 5m CHECK by symbol:")
lines.append("| Symbol | HOLD | BAIL | Bail% | HOLD avg pnl | BAIL avg pnl |")
lines.append("|--------|------|------|-------|--------------|--------------|")
for sym in sorted(check_by_symbol.keys()):
    cs = check_by_symbol[sym]
    total_cs = cs['hold'] + cs['bail']
    br = cs['bail'] / total_cs * 100 if total_cs > 0 else 0
    lines.append(f"| **{sym}** | {cs['hold']} | {cs['bail']} | {br:.1f}% | {avg(cs['hold_pnl']):+.3f} | {avg(cs['bail_pnl']):+.3f} |")

lines.append("\n\n---\n")
lines.append("## 6. Top Active Days\n")
lines.append("| Date | Signal Count |")
lines.append("|------|-------------|")
for d, c in top_days:
    lines.append(f"| {d} | {c} |")

lines.append("\n\n---\n")
lines.append("## 7. Time-of-Day Distribution\n")
lines.append("| Period | Total | BRK | REV | FADE | RNG | QBS | % |")
lines.append("|--------|-------|-----|-----|------|-----|-----|---|")

# Recompute by type×time
type_time_dist = defaultdict(lambda: defaultdict(int))
for r in signals:
    bucket = time_bucket(r.get('time'))
    type_time_dist[bucket][r['sig_type']] += 1
    type_time_dist[bucket]['_total'] += 1

for period in ['morning (9:30-11)', 'midday (11-14)', 'afternoon (14-16)', 'pre-market (<9:30)', 'post-market (>16:00)', 'unknown']:
    c = type_time_dist[period]['_total']
    if c == 0:
        continue
    pct = c / total_sig * 100 if total_sig > 0 else 0
    brk_t = type_time_dist[period]['BRK']
    rev_t = type_time_dist[period]['REV']
    fade_t = type_time_dist[period]['FADE']
    rng_t = type_time_dist[period]['RNG']
    qbs_t = type_time_dist[period]['QBS']
    lines.append(f"| {period} | {c} | {brk_t} | {rev_t} | {fade_t} | {rng_t} | {qbs_t} | {pct:.1f}% |")

non_rng_total = total_sig - type_counts.get('RNG', 0)
non_rng_morning = type_time_dist['morning (9:30-11)']['_total'] - type_time_dist['morning (9:30-11)']['RNG']
lines.append(f"\n_Note: RNG fires exclusively at open (all 1,834 in morning window), inflating morning% to 73.7%._")
lines.append(f"_Excluding RNG: morning={non_rng_morning}/{non_rng_total} = {non_rng_morning/non_rng_total*100:.1f}% of non-RNG signals._")

lines.append("\n\n---\n")
lines.append("## 8. Must-Trade Signal Summary (non-dim BRK + REV)\n")
lines.append(f"- **Non-dim BRK signals:** {len(brk_nondim):,}")
lines.append(f"- **Non-dim REV signals:** {len(rev_nondim):,}")
lines.append(f"- **Dim BRK signals:** {len(brk_dim):,}")
lines.append(f"- **Dim REV signals:** {len(rev_dim):,}")
lines.append(f"\nNote: dim detection uses 'x~' or '?' markers in message. If v3.7a doesn't emit these,")
lines.append(f"dim counts may undercount — check raw dim values above.")
lines.append(f"\n- Bull must-trade: {len(mt_bull):,} | Bear must-trade: {len(mt_bear):,}")

lines.append("\n\n---\n")
lines.append("## 9. Volume Statistics\n")
lines.append(f"- BRK avg vol: {avg(brk_vols):.2f}x (n={len(brk_vols)})")
lines.append(f"- REV avg vol: {avg(rev_vols):.2f}x (n={len(rev_vols)})")
rng_vols = [r['vol'] for r in signals if r['sig_type'] == 'RNG' and r['vol'] is not None]
lines.append(f"- RNG avg vol: {avg(rng_vols):.2f}x (n={len(rng_vols)})")

lines.append("\n\n---\n")
lines.append("## 10. Anomalies & Patterns\n")

# Check for files with same symbol (duplicates)
sym_to_files = defaultdict(list)
for fs in file_stats:
    sym_to_files[fs['symbol']].append(fs['hash'])

dupe_syms = {s: hs for s, hs in sym_to_files.items() if len(hs) > 1}
if dupe_syms:
    lines.append(f"**Multiple files for same symbol (potential duplicate coverage):**")
    for sym, hashes in sorted(dupe_syms.items()):
        lines.append(f"- {sym}: {', '.join(hashes)}")
    lines.append("")

# Symbols with no CONF rows
no_conf_syms = [sym for sym in symbol_counts if sym not in conf_by_symbol]
if no_conf_syms:
    lines.append(f"**Symbols with NO CONF rows:** {', '.join(sorted(no_conf_syms))}")
    lines.append("")

# Symbols with no 5m CHECK rows
no_check_syms = [sym for sym in symbol_counts if sym not in check_by_symbol]
if no_check_syms:
    lines.append(f"**Symbols with NO 5m CHECK rows:** {', '.join(sorted(no_check_syms))}")
    lines.append("")

# High bail rate symbols
high_bail = [(sym, cs) for sym, cs in check_by_symbol.items()
             if cs['bail'] + cs['hold'] >= 5 and cs['bail'] / (cs['bail'] + cs['hold']) > 0.3]
if high_bail:
    lines.append(f"**High BAIL rate symbols (>30%, n≥5):**")
    for sym, cs in sorted(high_bail, key=lambda x: x[1]['bail'] / (x[1]['bail'] + x[1]['hold']), reverse=True):
        total_cs = cs['hold'] + cs['bail']
        br = cs['bail'] / total_cs * 100
        lines.append(f"- {sym}: {br:.1f}% bail rate (n={total_cs})")
    lines.append("")

# Symbols with very high REV rates
for sym in sorted(symbol_counts.keys()):
    sc = symbol_counts[sym]
    if sc['total'] > 10:
        rev_pct = sc.get('REV', 0) / sc['total'] * 100
        if rev_pct > 50:
            lines.append(f"**{sym}: High REV rate** — {rev_pct:.0f}% of signals are REV")

lines.append("\n")
lines.append("---\n")
lines.append("## 11. Daily Signal Count Heatmap (top 5 per symbol)\n")
lines.append("| Symbol | Best Day | Count | 2nd | Count | 3rd | Count |")
lines.append("|--------|----------|-------|-----|-------|-----|-------|")
for sym in sorted(daily_by_sym.keys()):
    daily = sorted(daily_by_sym[sym].items(), key=lambda x: x[1], reverse=True)
    row_parts = [f"**{sym}**"]
    for i in range(3):
        if i < len(daily):
            row_parts.append(daily[i][0])
            row_parts.append(str(daily[i][1]))
        else:
            row_parts.append("—")
            row_parts.append("—")
    lines.append("| " + " | ".join(row_parts) + " |")

# Write output
with open(OUTPUT, 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(lines))

print(f"\nReport written to: {OUTPUT}")
print(f"\n=== Quick Stats ===")
print(f"Total signals: {total_sig:,}")
print(f"Type breakdown: {dict(type_counts)}")
print(f"CONF rate: {conf_rate:.1f}%")
print(f"BAIL rate: {bail_rate:.1f}%")
print(f"Avg pnl at check: {avg(all_pnls):+.3f}")
print(f"Date range: {min_date_overall} to {max_date_overall}")
