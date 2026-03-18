#!/usr/bin/env python3
"""
v3.1 Pine Log Validation Script
Compares v3.0b vs v3.1 pine logs to validate:
1. PD Mid BRK→REV change impact
2. SPY BAIL modifier impact
3. Net signal quality
"""

import csv
import re
import os
import glob
from datetime import datetime, timedelta
from collections import defaultdict

BASE = "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug"
CACHE = "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars"

# ── Symbol identification by price range ──
# We'll identify symbols from the first O price in each file
PRICE_RANGES = {
    'SLV': (20, 40),
    'GLD': (50, 100),  # could overlap
    'AMD': (85, 160),
    'AAPL': (200, 280),
    'QQQ': (460, 560),
    'SPY': (550, 620),
    'MSFT': (400, 460),
    'TSLA': (300, 450),
    'META': (550, 720),
    'GOOGL': (180, 210),
    'NVDA': (115, 155),
    'AMZN': (220, 260),
    'TSM': (180, 220),
}

def identify_symbol(price):
    """Identify symbol from price. Uses knowledge of Jan-Feb 2026 price ranges."""
    # More specific ranges based on actual data
    if 20 <= price <= 35:
        return 'SLV'
    elif 35 < price <= 80:
        return 'GLD'
    elif 80 < price <= 170:
        return 'NVDA' if price < 145 else 'AMD'
    elif 170 < price <= 210:
        # GOOGL ~190, TSM ~195-210
        return 'GOOGL' if price < 200 else 'TSM'
    elif 220 < price <= 275:
        return 'AMZN'
    elif 275 < price <= 370:
        return 'TSLA'
    elif 370 < price <= 465:
        return 'MSFT'
    elif 465 < price <= 540:
        return 'QQQ'
    elif 540 < price <= 640:
        return 'SPY'
    elif 640 < price <= 730:
        return 'META'
    elif 230 <= price <= 250:
        return 'AMZN'
    else:
        return f'UNK_{price}'

def parse_pine_log(filepath):
    """Parse a pine log CSV and extract all signals, CONFs, and 5m CHECKs."""
    signals = []
    confs = []
    checks = []
    fades = []
    retests = []
    symbol = None

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)

        for row in reader:
            if len(row) < 2:
                continue
            ts_str = row[0]
            msg = ','.join(row[1:])  # rejoin in case commas in message

            if '[KLB]' not in msg:
                continue

            # Parse timestamp
            try:
                ts = datetime.fromisoformat(ts_str.replace('.000-05:00', '-05:00').replace('.000-04:00', '-04:00'))
            except:
                continue

            date = ts.strftime('%Y-%m-%d')
            time = ts.strftime('%H:%M')

            # Extract first O price for symbol ID
            if symbol is None:
                m = re.search(r'O(\d+\.\d+)', msg)
                if m:
                    price = float(m.group(1))
                    symbol = identify_symbol(price)

            # Signal line: [KLB] 9:40 ▲ BRK PM H vol=5.5x ...
            sig_match = re.search(r'\[KLB\] (\d+:\d+) ([▲▼]) (BRK|REV|RNG|FADE|~ ~) (.+)', msg)
            if sig_match:
                sig_time = sig_match.group(1)
                direction = 'bull' if sig_match.group(2) == '▲' else 'bear'
                sig_type = sig_match.group(3)
                details = sig_match.group(4)

                # Skip RNG-only lines (no level info)
                if sig_type == 'RNG' and 'range break' in details:
                    continue

                # Skip tilde-only (dim) signals
                if sig_type == '~ ~':
                    continue

                # Extract level name
                level = ''
                if sig_type in ('BRK', 'REV'):
                    level_match = re.match(r'([\w\s\+]+?)(?:\s+vol=)', details)
                    if level_match:
                        level = level_match.group(1).strip()
                elif sig_type == 'FADE':
                    level = details.strip()

                # Extract key metrics
                vol_m = re.search(r'vol=([\d.]+)x', details)
                ema_m = re.search(r'ema=(\w+)', details)
                vwap_m = re.search(r'vwap=(\w+)', details)
                rs_m = re.search(r'rs=([+\-\d.]+)%', details)

                signals.append({
                    'date': date,
                    'time': time,
                    'ts': ts,
                    'direction': direction,
                    'type': sig_type,
                    'level': level,
                    'vol': float(vol_m.group(1)) if vol_m else 0,
                    'ema': ema_m.group(1) if ema_m else '',
                    'vwap': vwap_m.group(1) if vwap_m else '',
                    'rs': float(rs_m.group(1)) if rs_m else 0,
                    'details': details,
                    'has_pd_mid': 'PD Mid' in details,
                })

            # CONF line: [KLB] CONF 9:40 ▲ BRK → ✓ (auto-R1: EMA+morning)
            conf_match = re.search(r'\[KLB\] CONF (\d+:\d+) ([▲▼]) (\w+) → (✓|✗)(.*)', msg)
            if conf_match:
                conf_time = conf_match.group(1)
                direction = 'bull' if conf_match.group(2) == '▲' else 'bear'
                conf_type = conf_match.group(3)
                result = 'pass' if conf_match.group(4) == '✓' else 'fail'
                reason = conf_match.group(5).strip()

                confs.append({
                    'date': date,
                    'time': time,
                    'conf_time': conf_time,
                    'ts': ts,
                    'direction': direction,
                    'type': conf_type,
                    'result': result,
                    'reason': reason,
                })

            # 5m CHECK line: [KLB] 5m CHECK 9:45 ▲ pnl=0.02 → BAIL
            # v3.1 variant: [KLB] 5m CHECK 9:45 ▲ pnl=0.02 SPY✗ → BAIL
            check_match = re.search(r'\[KLB\] 5m CHECK (\d+:\d+) ([▲▼]) pnl=([+\-\d.]+)\s*(SPY[✓✗~])?\s*→ (HOLD|BAIL)', msg)
            if check_match:
                chk_time = check_match.group(1)
                direction = 'bull' if check_match.group(2) == '▲' else 'bear'
                pnl = float(check_match.group(3))
                spy_align = check_match.group(4) if check_match.group(4) else None
                decision = check_match.group(5)

                checks.append({
                    'date': date,
                    'time': time,
                    'chk_time': chk_time,
                    'ts': ts,
                    'direction': direction,
                    'pnl': pnl,
                    'spy_align': spy_align,
                    'decision': decision,
                })

            # FADE line
            fade_match = re.search(r'\[KLB\] .+ FADE at ([\d.]+)', msg)
            if fade_match:
                fades.append({
                    'date': date,
                    'time': time,
                    'ts': ts,
                    'price': float(fade_match.group(1)),
                })

            # Retest line (◆)
            retest_match = re.search(r'\[KLB\] .+ ◆', msg)
            if retest_match:
                retests.append({
                    'date': date,
                    'time': time,
                    'ts': ts,
                    'details': msg,
                })

    return {
        'symbol': symbol,
        'signals': signals,
        'confs': confs,
        'checks': checks,
        'fades': fades,
        'retests': retests,
        'filepath': filepath,
    }


def load_spy_data():
    """Load SPY 5m data for regime calculation. Convert to ET timezone."""
    try:
        import pandas as pd
        spy_5m = pd.read_parquet(os.path.join(CACHE, 'spy_5_mins_ib.parquet'))
        # Convert date column from Europe/Berlin to US/Eastern
        spy_5m['date_et'] = spy_5m['date'].dt.tz_convert('US/Eastern')
        spy_5m['day'] = spy_5m['date_et'].dt.strftime('%Y-%m-%d')
        spy_5m['time_et'] = spy_5m['date_et'].dt.strftime('%H:%M')
        # Pre-compute day opens (first bar at 9:30)
        day_opens = {}
        for day, grp in spy_5m.groupby('day'):
            first_bar = grp.sort_values('date_et').iloc[0]
            day_opens[day] = first_bar['open']
        return spy_5m, day_opens
    except Exception as e:
        print(f"Warning: Could not load SPY data: {e}")
        return None, None


def get_spy_regime(spy_5m, day_opens, ts):
    """
    Compute SPY regime at a given timestamp.
    ts is a naive datetime in US/Eastern.
    Returns: 1 (BULL), -1 (BEAR), 0 (NEUTRAL), and the % change
    """
    if spy_5m is None or day_opens is None:
        return 0, 0.0

    # Strip timezone if present (timestamps are already in ET)
    if ts.tzinfo is not None:
        ts = ts.replace(tzinfo=None)

    date = ts.strftime('%Y-%m-%d')
    time_str = ts.strftime('%H:%M')

    if date not in day_opens:
        return 0, 0.0

    spy_open = day_opens[date]

    # Find the closest 5m bar at or before this time
    day_data = spy_5m[spy_5m['day'] == date].sort_values('date_et')
    if len(day_data) == 0:
        return 0, 0.0

    # Find bar at or before signal time
    matching = day_data[day_data['time_et'] <= time_str]
    if len(matching) == 0:
        return 0, 0.0

    spy_close = matching.iloc[-1]['close']
    spy_chg = (spy_close - spy_open) / spy_open

    if spy_chg > 0.003:
        return 1, spy_chg  # BULL
    elif spy_chg < -0.003:
        return -1, spy_chg  # BEAR
    else:
        return 0, spy_chg  # NEUTRAL


def replay_bail_v31(direction, pnl, spy_regime):
    """
    Apply v3.1 BAIL rules:
    - SPY aligned → HOLD always
    - SPY neutral → HOLD if pnl > -0.10
    - SPY opposed → HOLD if pnl > 0.05 (same as old)
    """
    dir_sign = 1 if direction == 'bull' else -1

    if dir_sign == spy_regime:
        # Aligned
        return 'HOLD', 'SPY-aligned'
    elif spy_regime == 0:
        # Neutral
        if pnl > -0.10:
            return 'HOLD', 'SPY-neutral(loose)'
        else:
            return 'BAIL', 'SPY-neutral(strict)'
    else:
        # Opposed
        if pnl > 0.05:
            return 'HOLD', 'SPY-opposed(ok)'
        else:
            return 'BAIL', 'SPY-opposed(strict)'


def replay_bail_v30(pnl):
    """
    Apply v3.0b BAIL rules:
    - HOLD if pnl > 0.05
    - BAIL otherwise
    """
    if pnl > 0.05:
        return 'HOLD'
    else:
        return 'BAIL'


def main():
    import pandas as pd

    # ── 1. Load all pine log files ──
    v30b_files = sorted(glob.glob(os.path.join(BASE, 'pine-logs-Key Level Breakout v3.0b_*.csv')))
    v31_files = sorted(glob.glob(os.path.join(BASE, 'pine-logs-Key Level Breakout v3.1_*.csv')))

    print(f"Found {len(v30b_files)} v3.0b files, {len(v31_files)} v3.1 files")

    # Parse all files
    v30b_data = []
    v31_data = []

    for f in v30b_files:
        parsed = parse_pine_log(f)
        v30b_data.append(parsed)

    for f in v31_files:
        parsed = parse_pine_log(f)
        v31_data.append(parsed)

    # ── 2. Identify symbols ──
    print("\n=== v3.0b Files ===")
    v30b_by_symbol = {}
    for d in v30b_data:
        sym = d['symbol'] or 'UNKNOWN'
        fname = os.path.basename(d['filepath'])
        n_sig = len(d['signals'])
        n_conf = len(d['confs'])
        n_chk = len(d['checks'])
        print(f"  {fname}: {sym} | {n_sig} signals, {n_conf} confs, {n_chk} checks")
        if sym not in v30b_by_symbol:
            v30b_by_symbol[sym] = d
        else:
            # Merge if same symbol (pick one with more data)
            if len(d['signals']) > len(v30b_by_symbol[sym]['signals']):
                v30b_by_symbol[sym] = d

    print("\n=== v3.1 Files ===")
    v31_by_symbol = {}
    for d in v31_data:
        sym = d['symbol'] or 'UNKNOWN'
        fname = os.path.basename(d['filepath'])
        n_sig = len(d['signals'])
        n_conf = len(d['confs'])
        n_chk = len(d['checks'])
        print(f"  {fname}: {sym} | {n_sig} signals, {n_conf} confs, {n_chk} checks")
        if sym not in v31_by_symbol:
            v31_by_symbol[sym] = d
        else:
            if len(d['signals']) > len(v31_by_symbol[sym]['signals']):
                v31_by_symbol[sym] = d

    # ── 3. Load SPY data ──
    print("\n=== Loading SPY data ===")
    spy_5m, day_opens = load_spy_data()
    if spy_5m is not None:
        print(f"  SPY 5m: {len(spy_5m)} rows")
        print(f"  Day opens: {len(day_opens)} days")
        # Verify with a known date
        if '2026-02-02' in day_opens:
            regime, chg = get_spy_regime(spy_5m, day_opens, datetime(2026, 2, 2, 9, 40))
            r_str = {1: 'BULL', -1: 'BEAR', 0: 'NEUTRAL'}.get(regime, '?')
            print(f"  Verify: Feb 2 9:40 → {r_str} ({chg:+.4f})")

    # ── 4. Find PD Mid signals ──
    print("\n" + "="*80)
    print("ANALYSIS 1: PD Mid Signals (BRK→REV change)")
    print("="*80)

    pd_mid_v30b = []
    pd_mid_v31 = []

    for d in v30b_data:
        for sig in d['signals']:
            if sig['has_pd_mid'] or 'PD Mid' in sig.get('level', ''):
                pd_mid_v30b.append({**sig, 'symbol': d['symbol']})

    for d in v31_data:
        for sig in d['signals']:
            if sig['has_pd_mid'] or 'PD Mid' in sig.get('level', ''):
                pd_mid_v31.append({**sig, 'symbol': d['symbol']})

    print(f"\nv3.0b PD Mid signals: {len(pd_mid_v30b)}")
    for sig in pd_mid_v30b:
        print(f"  {sig['symbol']} {sig['date']} {sig['time']} {sig['direction']} {sig['type']} {sig['level']}")

    print(f"\nv3.1 PD Mid signals: {len(pd_mid_v31)}")
    for sig in pd_mid_v31:
        print(f"  {sig['symbol']} {sig['date']} {sig['time']} {sig['direction']} {sig['type']} {sig['level']}")

    # Check CONF outcomes for PD Mid BRK signals in v3.0b
    print("\nPD Mid BRK outcomes in v3.0b:")
    for d in v30b_data:
        for sig in d['signals']:
            if 'PD Mid' in sig.get('level', '') and sig['type'] == 'BRK':
                # Find matching CONF
                conf_found = False
                for conf in d['confs']:
                    if conf['date'] == sig['date'] and abs((conf['ts'] - sig['ts']).total_seconds()) < 600:
                        conf_found = True
                        # Find matching 5m CHECK
                        chk_found = False
                        for chk in d['checks']:
                            if chk['date'] == sig['date'] and abs((chk['ts'] - sig['ts']).total_seconds()) < 900:
                                print(f"  {d['symbol']} {sig['date']} {sig['time']}: {sig['level']} → CONF {conf['result']} → 5m pnl={chk['pnl']:.2f} {chk['decision']}")
                                chk_found = True
                                break
                        if not chk_found:
                            print(f"  {d['symbol']} {sig['date']} {sig['time']}: {sig['level']} → CONF {conf['result']} (no 5m CHECK)")
                        break
                if not conf_found:
                    print(f"  {d['symbol']} {sig['date']} {sig['time']}: {sig['level']} (no CONF)")

    # ── 5. Replay BAIL decisions ──
    print("\n" + "="*80)
    print("ANALYSIS 2: SPY BAIL Modifier Replay")
    print("="*80)

    # Collect all 5m CHECKs from v3.0b and replay with v3.1 rules
    bail_changes = []
    all_checks_v30b = []

    for d in v30b_data:
        sym = d['symbol']
        for chk in d['checks']:
            # Get SPY regime
            regime, spy_chg = get_spy_regime(spy_5m, day_opens, chk['ts'])

            # Old decision (from log)
            old_decision = chk['decision']

            # New v3.1 decision
            new_decision, reason = replay_bail_v31(chk['direction'], chk['pnl'], regime)

            record = {
                'symbol': sym,
                'date': chk['date'],
                'time': chk['time'],
                'direction': chk['direction'],
                'pnl': chk['pnl'],
                'spy_regime': regime,
                'spy_chg': spy_chg,
                'old_decision': old_decision,
                'new_decision': new_decision,
                'new_reason': reason,
                'changed': old_decision != new_decision,
            }
            all_checks_v30b.append(record)

            if old_decision != new_decision:
                bail_changes.append(record)

    print(f"\nTotal 5m CHECKs in v3.0b: {len(all_checks_v30b)}")
    print(f"Changed decisions under v3.1 rules: {len(bail_changes)}")

    # Breakdown
    bail_to_hold = [c for c in bail_changes if c['old_decision'] == 'BAIL' and c['new_decision'] == 'HOLD']
    hold_to_bail = [c for c in bail_changes if c['old_decision'] == 'HOLD' and c['new_decision'] == 'BAIL']

    print(f"\n  BAIL → HOLD: {len(bail_to_hold)} (saved signals)")
    for c in bail_to_hold:
        regime_str = {1: 'BULL', -1: 'BEAR', 0: 'NEUTRAL'}.get(c['spy_regime'], '?')
        print(f"    {c['symbol']:6s} {c['date']} {c['time']} {c['direction']:4s} pnl={c['pnl']:+.2f} SPY={regime_str}({c['spy_chg']:+.3f}) → {c['new_reason']}")

    print(f"\n  HOLD → BAIL: {len(hold_to_bail)} (killed signals)")
    for c in hold_to_bail:
        regime_str = {1: 'BULL', -1: 'BEAR', 0: 'NEUTRAL'}.get(c['spy_regime'], '?')
        print(f"    {c['symbol']:6s} {c['date']} {c['time']} {c['direction']:4s} pnl={c['pnl']:+.2f} SPY={regime_str}({c['spy_chg']:+.3f}) → {c['new_reason']}")

    # ── 5b. Also look at v3.1 actual BAIL decisions for comparison ──
    print("\n=== v3.1 Actual 5m CHECK Decisions ===")
    all_checks_v31 = []
    for d in v31_data:
        sym = d['symbol']
        for chk in d['checks']:
            spy_tag = chk.get('spy_align', '')
            all_checks_v31.append({
                'symbol': sym,
                'date': chk['date'],
                'time': chk['time'],
                'direction': chk['direction'],
                'pnl': chk['pnl'],
                'spy_align': spy_tag,
                'decision': chk['decision'],
            })

    print(f"Total v3.1 5m CHECKs: {len(all_checks_v31)}")
    v31_holds = sum(1 for c in all_checks_v31 if c['decision'] == 'HOLD')
    v31_bails = sum(1 for c in all_checks_v31 if c['decision'] == 'BAIL')
    print(f"  HOLD: {v31_holds}, BAIL: {v31_bails}")

    # Show v3.1 checks with SPY info
    for c in all_checks_v31:
        spy_str = c['spy_align'] or 'N/A'
        print(f"  {c['symbol']:6s} {c['date']} {c['time']} {c['direction']:4s} pnl={c['pnl']:+.2f} {spy_str} → {c['decision']}")

    # ── 6. Direct v3.0b vs v3.1 comparison (same symbol+date) ──
    print("\n" + "="*80)
    print("ANALYSIS 3: Direct v3.0b vs v3.1 Signal Comparison")
    print("="*80)

    # Match files by symbol
    common_symbols = set(v30b_by_symbol.keys()) & set(v31_by_symbol.keys())
    print(f"\nCommon symbols: {sorted(common_symbols)}")
    print(f"v3.0b only: {sorted(set(v30b_by_symbol.keys()) - common_symbols)}")
    print(f"v3.1 only: {sorted(set(v31_by_symbol.keys()) - common_symbols)}")

    for sym in sorted(common_symbols):
        d30 = v30b_by_symbol[sym]
        d31 = v31_by_symbol[sym]

        # Build signal keys: (date, time, direction, type)
        sigs30 = set()
        sigs30_detail = {}
        for s in d30['signals']:
            key = (s['date'], s['time'], s['direction'], s['type'], s['level'])
            sigs30.add(key)
            sigs30_detail[key] = s

        sigs31 = set()
        sigs31_detail = {}
        for s in d31['signals']:
            key = (s['date'], s['time'], s['direction'], s['type'], s['level'])
            sigs31.add(key)
            sigs31_detail[key] = s

        new_in_v31 = sigs31 - sigs30
        lost_in_v31 = sigs30 - sigs31

        if new_in_v31 or lost_in_v31:
            print(f"\n--- {sym} ---")
            if new_in_v31:
                print(f"  NEW in v3.1 ({len(new_in_v31)}):")
                for key in sorted(new_in_v31):
                    s = sigs31_detail[key]
                    print(f"    + {key[0]} {key[1]} {key[2]:4s} {key[3]} {key[4]}")
            if lost_in_v31:
                print(f"  LOST in v3.1 ({len(lost_in_v31)}):")
                for key in sorted(lost_in_v31):
                    s = sigs30_detail[key]
                    print(f"    - {key[0]} {key[1]} {key[2]:4s} {key[3]} {key[4]}")

        # Compare CONF outcomes
        confs30 = {(c['date'], c['conf_time'], c['direction']): c for c in d30['confs']}
        confs31 = {(c['date'], c['conf_time'], c['direction']): c for c in d31['confs']}

        conf_diffs = []
        for key in set(confs30.keys()) | set(confs31.keys()):
            if key in confs30 and key in confs31:
                if confs30[key]['result'] != confs31[key]['result']:
                    conf_diffs.append((key, confs30[key], confs31[key]))

        if conf_diffs:
            print(f"  CONF differences:")
            for key, c30, c31 in conf_diffs:
                print(f"    {key[0]} {key[1]} {key[2]}: v3.0b={c30['result']} vs v3.1={c31['result']}")

        # Compare 5m CHECK outcomes
        chks30 = {(c['date'], c['chk_time'], c['direction']): c for c in d30['checks']}
        chks31 = {(c['date'], c['chk_time'], c['direction']): c for c in d31['checks']}

        chk_diffs = []
        for key in set(chks30.keys()) | set(chks31.keys()):
            if key in chks30 and key in chks31:
                if chks30[key]['decision'] != chks31[key]['decision']:
                    chk_diffs.append((key, chks30[key], chks31[key]))
            elif key in chks30 and key not in chks31:
                chk_diffs.append((key, chks30[key], None))
            elif key not in chks30 and key in chks31:
                chk_diffs.append((key, None, chks31[key]))

        if chk_diffs:
            print(f"  5m CHECK differences:")
            for key, c30, c31 in chk_diffs:
                d30_str = f"pnl={c30['pnl']:.2f} {c30['decision']}" if c30 else "MISSING"
                d31_str = f"pnl={c31['pnl']:.2f} {c31.get('spy_align','')} {c31['decision']}" if c31 else "MISSING"
                print(f"    {key[0]} {key[1]} {key[2]}: v3.0b={d30_str} | v3.1={d31_str}")

    # ── 7. Summary Stats ──
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)

    # Count all signals
    total_sigs_v30b = sum(len(d['signals']) for d in v30b_data)
    total_sigs_v31 = sum(len(d['signals']) for d in v31_data)
    total_confs_v30b = sum(len(d['confs']) for d in v30b_data)
    total_confs_v31 = sum(len(d['confs']) for d in v31_data)
    total_chks_v30b = sum(len(d['checks']) for d in v30b_data)
    total_chks_v31 = sum(len(d['checks']) for d in v31_data)

    print(f"\n{'Metric':<30s} {'v3.0b':>8s} {'v3.1':>8s} {'Delta':>8s}")
    print("-" * 56)
    print(f"{'Total BRK/REV/FADE signals':<30s} {total_sigs_v30b:>8d} {total_sigs_v31:>8d} {total_sigs_v31-total_sigs_v30b:>+8d}")
    print(f"{'CONF results':<30s} {total_confs_v30b:>8d} {total_confs_v31:>8d} {total_confs_v31-total_confs_v30b:>+8d}")
    print(f"{'5m CHECKs':<30s} {total_chks_v30b:>8d} {total_chks_v31:>8d} {total_chks_v31-total_chks_v30b:>+8d}")

    # CONF pass rates
    conf_pass_v30b = sum(1 for d in v30b_data for c in d['confs'] if c['result'] == 'pass')
    conf_pass_v31 = sum(1 for d in v31_data for c in d['confs'] if c['result'] == 'pass')

    if total_confs_v30b > 0:
        print(f"{'CONF pass rate':<30s} {conf_pass_v30b/total_confs_v30b*100:>7.1f}% {conf_pass_v31/total_confs_v31*100 if total_confs_v31 else 0:>7.1f}%")

    # HOLD rates
    hold_v30b = sum(1 for d in v30b_data for c in d['checks'] if c['decision'] == 'HOLD')
    hold_v31 = sum(1 for d in v31_data for c in d['checks'] if c['decision'] == 'HOLD')
    bail_v30b = sum(1 for d in v30b_data for c in d['checks'] if c['decision'] == 'BAIL')
    bail_v31 = sum(1 for d in v31_data for c in d['checks'] if c['decision'] == 'BAIL')

    print(f"{'5m HOLD':<30s} {hold_v30b:>8d} {hold_v31:>8d} {hold_v31-hold_v30b:>+8d}")
    print(f"{'5m BAIL':<30s} {bail_v30b:>8d} {bail_v31:>8d} {bail_v31-bail_v30b:>+8d}")

    if total_chks_v30b > 0 and total_chks_v31 > 0:
        print(f"{'HOLD rate':<30s} {hold_v30b/total_chks_v30b*100:>7.1f}% {hold_v31/total_chks_v31*100:>7.1f}%")

    # Average PNL of HOLD vs BAIL signals
    hold_pnl_v30b = [c['pnl'] for d in v30b_data for c in d['checks'] if c['decision'] == 'HOLD']
    bail_pnl_v30b = [c['pnl'] for d in v30b_data for c in d['checks'] if c['decision'] == 'BAIL']
    hold_pnl_v31 = [c['pnl'] for d in v31_data for c in d['checks'] if c['decision'] == 'HOLD']
    bail_pnl_v31 = [c['pnl'] for d in v31_data for c in d['checks'] if c['decision'] == 'BAIL']

    if hold_pnl_v30b:
        print(f"{'Avg HOLD pnl':<30s} {sum(hold_pnl_v30b)/len(hold_pnl_v30b):>+7.3f}  {sum(hold_pnl_v31)/len(hold_pnl_v31):>+7.3f}" if hold_pnl_v31 else "")
    if bail_pnl_v30b:
        print(f"{'Avg BAIL pnl':<30s} {sum(bail_pnl_v30b)/len(bail_pnl_v30b):>+7.3f}  {sum(bail_pnl_v31)/len(bail_pnl_v31):>+7.3f}" if bail_pnl_v31 else "")

    # PD Mid specific
    pd_mid_brk_v30b = [s for d in v30b_data for s in d['signals'] if 'PD Mid' in s.get('level', '')]
    pd_mid_rev_v31 = [s for d in v31_data for s in d['signals'] if 'PD Mid' in s.get('level', '') and s['type'] == 'REV']
    pd_mid_brk_v31 = [s for d in v31_data for s in d['signals'] if 'PD Mid' in s.get('level', '') and s['type'] == 'BRK']

    print(f"\n{'PD Mid BRK (v3.0b)':<30s} {len(pd_mid_brk_v30b):>8d}")
    print(f"{'PD Mid REV (v3.1)':<30s} {len(pd_mid_rev_v31):>8d}")
    print(f"{'PD Mid BRK (v3.1)':<30s} {len(pd_mid_brk_v31):>8d}")

    # FADE signals
    fades_v30b = sum(len(d['fades']) for d in v30b_data)
    fades_v31 = sum(len(d['fades']) for d in v31_data)
    print(f"{'FADE signals':<30s} {fades_v30b:>8d} {fades_v31:>8d} {fades_v31-fades_v30b:>+8d}")

    # ── 8. Duplicate analysis (files covering same symbol) ──
    print("\n" + "="*80)
    print("ANALYSIS 4: Per-Symbol Signal Counts (all files)")
    print("="*80)

    # Group by symbol across all files
    v30b_sym_counts = defaultdict(lambda: {'signals': 0, 'confs': 0, 'checks': 0, 'files': 0})
    v31_sym_counts = defaultdict(lambda: {'signals': 0, 'confs': 0, 'checks': 0, 'files': 0})

    for d in v30b_data:
        sym = d['symbol'] or 'UNK'
        v30b_sym_counts[sym]['signals'] += len(d['signals'])
        v30b_sym_counts[sym]['confs'] += len(d['confs'])
        v30b_sym_counts[sym]['checks'] += len(d['checks'])
        v30b_sym_counts[sym]['files'] += 1

    for d in v31_data:
        sym = d['symbol'] or 'UNK'
        v31_sym_counts[sym]['signals'] += len(d['signals'])
        v31_sym_counts[sym]['confs'] += len(d['confs'])
        v31_sym_counts[sym]['checks'] += len(d['checks'])
        v31_sym_counts[sym]['files'] += 1

    all_syms = sorted(set(list(v30b_sym_counts.keys()) + list(v31_sym_counts.keys())))

    print(f"\n{'Symbol':<8s} {'v3.0b Files':>11s} {'v3.0b Sigs':>10s} {'v3.1 Files':>10s} {'v3.1 Sigs':>10s}")
    print("-" * 52)
    for sym in all_syms:
        c30 = v30b_sym_counts.get(sym, {'signals': 0, 'files': 0})
        c31 = v31_sym_counts.get(sym, {'signals': 0, 'files': 0})
        print(f"{sym:<8s} {c30['files']:>11d} {c30['signals']:>10d} {c31['files']:>10d} {c31['signals']:>10d}")

    return {
        'v30b_data': v30b_data,
        'v31_data': v31_data,
        'bail_changes': bail_changes,
        'all_checks_v30b': all_checks_v30b,
        'pd_mid_v30b': pd_mid_v30b,
        'pd_mid_v31': pd_mid_v31,
    }


if __name__ == '__main__':
    results = main()
