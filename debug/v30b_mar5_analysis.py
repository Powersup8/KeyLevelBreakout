#!/usr/bin/env python3
"""
v3.0b March 5, 2026 Signal & Move Analysis
Processes all 18 pine log files, identifies symbols, extracts March 5 data,
and performs comprehensive analysis.
"""

import glob
import csv
import re
import os
from datetime import datetime, date
from collections import defaultdict

# Config
DEBUG_DIR = "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug"
PINE_LOG_PATTERN = os.path.join(DEBUG_DIR, "pine-logs-Key Level Breakout v3.0b_*.csv")

# Verified symbol mapping (hash -> symbol) from March 2026 investigation
# Verified by cross-referencing BATS prices with IB parquet data + level names
VERIFIED_SYMBOL_MAP = {
    '49c92': 'SPY',   'cea64': 'SPY',     # BATS ~682, IB ~685, RS=0.0%
    'fa0b5': 'META',  '67b51': 'META',     # BATS ~665, IB ~668
    '71d98': 'TSM',                         # BATS ~356, IB ~357
    '4d466': 'TSLA',  '21c43': 'TSLA',     # BATS ~401-405, IB ~406, ATR=14.71
    'e94d0': 'MSFT',                        # BATS ~407, IB ~405, Yest H=406.70 matches
    '1f23e': 'QQQ',   '2845e': 'QQQ',      # BATS ~607, IB ~611
    '7aedc': 'NVDA',  'ccab3': 'NVDA',     # BATS ~182, IB ~183
    '77b0c': 'AMZN',  '2f230': 'AMZN',     # BATS ~218, IB ~217
    '4caf9': 'AMD',   'ba67a': 'AMD',       # BATS ~197-203, IB ~202
    '01085': 'AAPL',  '9a085': 'AAPL',     # BATS ~260, IB ~262
}

# Price ranges for symbol identification (approximate March 2026 BATS ranges)
# NOTE: These differ from IB consolidated prices
SYMBOL_RANGES = {
    'TSM': (350, 365),
    'TSLA': (395, 420),
    'MSFT': (400, 415),
    'SPY': (670, 695),
    'META': (625, 735),
    'AMD': (185, 210),
    'AMZN': (205, 250),
    'NVDA': (170, 195),
    'QQQ': (595, 620),
    'AAPL': (250, 270),
    'TSM': (170, 210),
    'GLD': (255, 300),
    'SLV': (28, 35),
}

def parse_price_from_message(msg):
    """Extract close price from OHLC in message."""
    # Pattern: O{price} H{price} L{price} C{price}
    m = re.search(r'C([\d.]+)', msg)
    if m:
        return float(m.group(1))
    return None

def identify_symbol(close_price):
    """Identify symbol from close price."""
    if close_price is None:
        return 'UNKNOWN'
    for sym, (lo, hi) in SYMBOL_RANGES.items():
        if lo <= close_price <= hi:
            return sym
    return f'UNKNOWN_{close_price:.0f}'

def parse_pine_log(filepath):
    """Parse a pine log CSV file and return list of (datetime, message) tuples."""
    rows = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            current_date = None
            current_msg = None
            for row in reader:
                if len(row) >= 2:
                    dt_str = row[0].strip()
                    msg = row[1].strip()
                    if dt_str and msg:
                        if current_date and current_msg:
                            rows.append((current_date, current_msg))
                        current_date = dt_str
                        current_msg = msg
                    elif dt_str and not msg:
                        # continuation line
                        if current_msg:
                            current_msg += ' ' + dt_str
                    elif not dt_str and msg:
                        if current_msg:
                            current_msg += ' ' + msg
                elif len(row) == 1:
                    # continuation of previous message
                    if current_msg:
                        current_msg += ' ' + row[0].strip()
            if current_date and current_msg:
                rows.append((current_date, current_msg))
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
    return rows

def parse_datetime(dt_str):
    """Parse ISO datetime string."""
    try:
        # Handle format like 2026-03-05T09:35:00.000-05:00
        # Python's fromisoformat handles this in 3.7+
        return datetime.fromisoformat(dt_str)
    except:
        return None

def extract_signal_info(msg):
    """Extract structured signal info from a KLB log message."""
    info = {}

    # Time and direction
    m = re.match(r'\[KLB\]\s+(\d+:\d+)\s+(▲|▼)', msg)
    if m:
        info['time'] = m.group(1)
        info['dir'] = 'bull' if m.group(1) and m.group(2) == '▲' else 'bear'
        info['dir_symbol'] = m.group(2)

    # Signal type
    if 'RNG range break' in msg:
        info['type'] = 'RNG'
    elif 'CONF' in msg and '→' in msg:
        info['type'] = 'CONF'
        if '✓' in msg:
            info['conf_result'] = '✓'
            if 'auto-R1' in msg:
                info['conf_detail'] = 'auto-R1'
        elif '✗' in msg:
            info['conf_result'] = '✗'
    elif '◆' in msg:
        info['type'] = 'RETEST'
    elif '5m' in msg and ('HOLD' in msg or 'BAIL' in msg):
        info['type'] = '5M_CHECK'
        info['hold_bail'] = 'HOLD' if 'HOLD' in msg else 'BAIL'
    elif 'VWAP-X' in msg:
        info['type'] = 'VWAP_EXIT'
    elif '🔇' in msg and 'QBS' in msg:
        info['type'] = 'QBS'
    elif '🔊' in msg:
        info['type'] = 'VOL_RAMP'
    elif 'BRK' in msg:
        info['type'] = 'BRK'
    elif 'REV' in msg:
        info['type'] = 'REV'
    elif 'RCL' in msg:
        info['type'] = 'RCL'
    elif '~ ~' in msg:
        info['type'] = 'SUPPRESSED'
    else:
        info['type'] = 'OTHER'

    # Level
    level_pattern = r'(BRK|REV|RCL)\s+([\w\s+]+?)(?=\s+vol=)'
    lm = re.search(level_pattern, msg)
    if lm:
        info['level'] = lm.group(2).strip()

    # Suppressed level pattern: ~ ~ LEVEL
    supp_pattern = r'~ ~\s+([\w\s+]+?)(?=\s+vol=)'
    sm = re.search(supp_pattern, msg)
    if sm:
        info['level'] = sm.group(1).strip()

    # Volume
    vm = re.search(r'vol=([\d.]+)x', msg)
    if vm:
        info['vol'] = float(vm.group(1))

    # Position
    pm = re.search(r'pos=([v^])(\d+)', msg)
    if pm:
        info['pos_dir'] = pm.group(1)
        info['pos_val'] = int(pm.group(2))

    # VWAP
    if 'vwap=above' in msg:
        info['vwap'] = 'above'
    elif 'vwap=below' in msg:
        info['vwap'] = 'below'

    # EMA
    if 'ema=bull' in msg:
        info['ema'] = 'bull'
    elif 'ema=bear' in msg:
        info['ema'] = 'bear'

    # ADX
    adx_m = re.search(r'adx=(\d+)', msg)
    if adx_m:
        info['adx'] = int(adx_m.group(1))

    # Body
    body_m = re.search(r'body=(\d+)%', msg)
    if body_m:
        info['body'] = int(body_m.group(1))

    # OHLC
    ohlc_m = re.search(r'O([\d.]+)\s+H([\d.]+)\s+L([\d.]+)\s+C([\d.]+)', msg)
    if ohlc_m:
        info['open'] = float(ohlc_m.group(1))
        info['high'] = float(ohlc_m.group(2))
        info['low'] = float(ohlc_m.group(3))
        info['close'] = float(ohlc_m.group(4))

    # ATR
    atr_m = re.search(r'ATR=([\d.]+)', msg)
    if atr_m:
        info['atr'] = float(atr_m.group(1))

    # RS
    rs_m = re.search(r'rs=([+-]?[\d.]+)%', msg)
    if rs_m:
        info['rs'] = float(rs_m.group(1))

    # Ramp
    ramp_m = re.search(r'ramp=([\d.]+)x', msg)
    if ramp_m:
        info['ramp'] = float(ramp_m.group(1))

    # Range ATR
    ratr_m = re.search(r'rangeATR=([\d.]+)', msg)
    if ratr_m:
        info['range_atr'] = float(ratr_m.group(1))

    # Flags
    info['big_move'] = '⚡' in msg
    info['body_warn'] = '⚠' in msg
    info['qbs'] = '🔇' in msg
    info['vol_ramp'] = '🔊' in msg

    # Prices (level prices)
    prices_m = re.search(r'prices=([\d./]+)', msg)
    if prices_m:
        info['prices'] = prices_m.group(1)

    return info

def main():
    files = sorted(glob.glob(PINE_LOG_PATTERN))
    print(f"Found {len(files)} pine log files\n")

    # Step 1: Identify symbols
    file_symbol_map = {}
    file_data = {}

    for filepath in files:
        fname = os.path.basename(filepath)
        hash_id = fname.split('_')[-1].replace('.csv', '')
        rows = parse_pine_log(filepath)
        file_data[hash_id] = rows

        # Get representative close price from first OHLC data
        prices = []
        for dt_str, msg in rows:
            price = parse_price_from_message(msg)
            if price and price > 1:
                prices.append(price)

        if prices:
            # Use median price for more robust identification
            prices.sort()
            median_price = prices[len(prices)//2]
            symbol = identify_symbol(median_price)
            file_symbol_map[hash_id] = {
                'symbol': symbol,
                'median_price': median_price,
                'price_range': (min(prices), max(prices)),
                'num_rows': len(rows),
            }
        else:
            file_symbol_map[hash_id] = {
                'symbol': 'UNKNOWN',
                'median_price': None,
                'num_rows': len(rows),
            }

    print("=" * 80)
    print("SYMBOL IDENTIFICATION MAP")
    print("=" * 80)
    for hash_id, info in sorted(file_symbol_map.items(), key=lambda x: x[1].get('median_price', 0) or 0):
        sym = info['symbol']
        mp = info.get('median_price')
        pr = info.get('price_range', (None, None))
        n = info['num_rows']
        print(f"  {hash_id}: {sym:8s} median={mp:>8.2f}  range=({pr[0]:.2f}-{pr[1]:.2f})  rows={n}" if mp else f"  {hash_id}: {sym}")

    # Check for duplicate symbols
    sym_counts = defaultdict(list)
    for h, info in file_symbol_map.items():
        sym_counts[info['symbol']].append(h)

    print("\nDuplicate symbol files:")
    for sym, hashes in sym_counts.items():
        if len(hashes) > 1:
            print(f"  {sym}: {hashes}")

    # Step 2: Extract March 5 data
    print("\n" + "=" * 80)
    print("MARCH 5, 2026 DATA")
    print("=" * 80)

    target_date = date(2026, 3, 5)
    mar5_data = defaultdict(list)  # symbol -> list of (time, msg, info)

    for hash_id, rows in file_data.items():
        symbol = file_symbol_map[hash_id]['symbol']
        for dt_str, msg in rows:
            dt = parse_datetime(dt_str)
            if dt and dt.date() == target_date:
                info = extract_signal_info(msg)
                info['raw_msg'] = msg
                info['datetime'] = dt
                mar5_data[symbol].append((dt, msg, info))

    if not mar5_data:
        print("NO MARCH 5 DATA FOUND!")
        # Check what dates are available
        all_dates = set()
        for hash_id, rows in file_data.items():
            for dt_str, msg in rows:
                dt = parse_datetime(dt_str)
                if dt:
                    all_dates.add(dt.date())
        print(f"\nAvailable dates: {sorted(all_dates)}")
        print(f"Last date: {max(all_dates) if all_dates else 'none'}")
        return

    # Step 3: Complete Signal Timeline for each symbol
    for symbol in sorted(mar5_data.keys()):
        entries = mar5_data[symbol]
        entries.sort(key=lambda x: x[0])

        print(f"\n--- {symbol} ({len(entries)} log entries) ---")
        print(f"{'TIME':6s} | {'TYPE':12s} | {'DIR':3s} | {'LEVEL':20s} | {'VOL':6s} | {'EMA':4s} | {'VWAP':5s} | {'ADX':3s} | {'NOTES'}")
        print("-" * 110)

        for dt, msg, info in entries:
            time_str = info.get('time', dt.strftime('%H:%M'))
            sig_type = info.get('type', '?')
            direction = info.get('dir_symbol', '')
            level = info.get('level', '')[:20]
            vol = f"{info['vol']:.1f}x" if 'vol' in info else ''
            ema = info.get('ema', '')
            vwap = info.get('vwap', '')
            adx = str(info.get('adx', ''))

            notes = []
            if info.get('conf_result'):
                notes.append(f"CONF→{info['conf_result']}")
            if info.get('conf_detail'):
                notes.append(info['conf_detail'])
            if info.get('hold_bail'):
                notes.append(info['hold_bail'])
            if info.get('big_move'):
                notes.append('⚡')
            if info.get('body_warn'):
                notes.append('⚠')
            if info.get('qbs'):
                notes.append('QBS')
            if 'close' in info:
                notes.append(f"C={info['close']:.2f}")
            if 'rs' in info:
                notes.append(f"rs={info['rs']:+.1f}%")

            notes_str = ' '.join(notes)
            print(f"{time_str:6s} | {sig_type:12s} | {direction:3s} | {level:20s} | {vol:6s} | {ema:4s} | {vwap:5s} | {adx:3s} | {notes_str}")

    # Step 4: EMA tracking for TSLA
    print("\n" + "=" * 80)
    print("TSLA EMA TRACKING (March 5)")
    print("=" * 80)
    if 'TSLA' in mar5_data:
        for dt, msg, info in sorted(mar5_data['TSLA'], key=lambda x: x[0]):
            ema = info.get('ema', '?')
            close = info.get('close', '?')
            sig_type = info.get('type', '?')
            time_str = dt.strftime('%H:%M')
            print(f"  {time_str} | ema={ema:4s} | close={close} | {sig_type}")

    # Step 5: Cross-symbol analysis at 12:06
    print("\n" + "=" * 80)
    print("CROSS-SYMBOL ANALYSIS: 12:00-12:15 ET")
    print("=" * 80)
    for symbol in sorted(mar5_data.keys()):
        entries = mar5_data[symbol]
        noon_entries = [(dt, msg, info) for dt, msg, info in entries
                       if dt.hour == 12 and dt.minute <= 15]
        if noon_entries:
            print(f"\n  {symbol}:")
            for dt, msg, info in noon_entries:
                time_str = dt.strftime('%H:%M')
                print(f"    {time_str}: {info.get('type', '?')} {info.get('dir_symbol', '')} {info.get('level', '')} vol={info.get('vol', '?')}x ema={info.get('ema', '?')}")

    # Step 6: 9:35 RNG Cluster Analysis
    print("\n" + "=" * 80)
    print("9:30-9:35 RNG CLUSTER ANALYSIS")
    print("=" * 80)
    for symbol in sorted(mar5_data.keys()):
        entries = mar5_data[symbol]
        rng_entries = [(dt, msg, info) for dt, msg, info in entries
                      if info.get('type') == 'RNG' and dt.hour == 9 and dt.minute <= 35]
        if rng_entries:
            for dt, msg, info in rng_entries:
                time_str = dt.strftime('%H:%M')
                vol = info.get('vol', '?')
                direction = info.get('dir_symbol', '?')
                print(f"  {symbol:8s} {time_str} {direction} vol={vol}x")

    # Step 7: Signal Quality Scorecard
    print("\n" + "=" * 80)
    print("SIGNAL QUALITY SCORECARD (March 5)")
    print("=" * 80)

    total_signals = 0
    total_conf = 0
    total_conf_pass = 0
    total_holds = 0
    total_bails = 0
    total_suppressed = 0

    for symbol in sorted(mar5_data.keys()):
        entries = mar5_data[symbol]

        signals = [e for e in entries if e[2].get('type') in ('BRK', 'REV', 'RCL', 'QBS')]
        confs = [e for e in entries if e[2].get('type') == 'CONF']
        conf_passes = [e for e in confs if e[2].get('conf_result') == '✓']
        holds = [e for e in entries if e[2].get('hold_bail') == 'HOLD']
        bails = [e for e in entries if e[2].get('hold_bail') == 'BAIL']
        suppressed = [e for e in entries if e[2].get('type') == 'SUPPRESSED']
        rngs = [e for e in entries if e[2].get('type') == 'RNG']
        retests = [e for e in entries if e[2].get('type') == 'RETEST']

        total_signals += len(signals)
        total_conf += len(confs)
        total_conf_pass += len(conf_passes)
        total_holds += len(holds)
        total_bails += len(bails)
        total_suppressed += len(suppressed)

        print(f"\n  {symbol}: {len(signals)} signals, {len(confs)} CONF ({len(conf_passes)} ✓), "
              f"{len(holds)} HOLD, {len(bails)} BAIL, {len(suppressed)} suppressed, "
              f"{len(rngs)} RNG, {len(retests)} retests")

    print(f"\n  TOTALS: {total_signals} signals, {total_conf} CONF ({total_conf_pass} ✓), "
          f"{total_holds} HOLD, {total_bails} BAIL, {total_suppressed} suppressed")

    # Step 8: Suppressed signals analysis (what v3.0 filters removed)
    print("\n" + "=" * 80)
    print("SUPPRESSED SIGNALS ANALYSIS (EMA Gate / Filters)")
    print("=" * 80)
    for symbol in sorted(mar5_data.keys()):
        entries = mar5_data[symbol]
        suppressed = [(dt, msg, info) for dt, msg, info in entries
                     if info.get('type') == 'SUPPRESSED']
        if suppressed:
            print(f"\n  {symbol}:")
            for dt, msg, info in suppressed:
                time_str = dt.strftime('%H:%M')
                direction = info.get('dir_symbol', '')
                level = info.get('level', '')
                ema = info.get('ema', '?')
                vwap = info.get('vwap', '?')
                vol = info.get('vol', '?')
                close = info.get('close', '?')

                # Determine suppression reason
                reasons = []
                if info.get('dir_symbol') == '▼' and info.get('ema') == 'bull':
                    reasons.append('EMA-GATE(bear sig, bull ema)')
                elif info.get('dir_symbol') == '▲' and info.get('ema') == 'bear':
                    reasons.append('EMA-GATE(bull sig, bear ema)')
                if dt.hour >= 10 or (dt.hour == 9 and dt.minute >= 50):
                    reasons.append('post-9:50')
                else:
                    reasons.append('pre-9:50(dim only)')

                reason_str = ', '.join(reasons) if reasons else 'unknown'
                print(f"    {time_str} {direction} {level:20s} ema={ema} vwap={vwap} vol={vol}x C={close} | REASON: {reason_str}")

    # Step 9: Look at all TSLA entries for the full day to check for gaps
    print("\n" + "=" * 80)
    print("TSLA FULL DAY LOG (March 5)")
    print("=" * 80)
    if 'TSLA' in mar5_data:
        for dt, msg, info in sorted(mar5_data['TSLA'], key=lambda x: x[0]):
            time_str = dt.strftime('%H:%M:%S')
            # Truncate message for readability
            short_msg = msg[:150] if len(msg) > 150 else msg
            print(f"  {time_str}: {short_msg}")

    # Step 10: Check for signals around user's observed moves
    print("\n" + "=" * 80)
    print("USER OBSERVATIONS CHECK")
    print("=" * 80)

    observations = [
        ("TSLA upmove 9:30", "TSLA", 9, 30),
        ("TSLA downmove 10:01-10:31", "TSLA", 10, 1),
        ("TSLA 10:16 reversal not fired", "TSLA", 10, 16),
        ("TSLA upmove 10:32", "TSLA", 10, 32),
        ("TSLA downmove 12:06", "TSLA", 12, 6),
        ("SPY downmove 12:06", "SPY", 12, 6),
        ("QQQ downmove 12:06", "QQQ", 12, 6),
        ("AMD downmove 12:06", "AMD", 12, 6),
        ("NVDA downmove 12:06", "NVDA", 12, 6),
    ]

    for obs_name, symbol, hour, minute in observations:
        print(f"\n  {obs_name}:")
        if symbol in mar5_data:
            # Look for signals within +/- 10 minutes
            nearby = []
            for dt, msg, info in mar5_data[symbol]:
                dt_min = dt.hour * 60 + dt.minute
                target_min = hour * 60 + minute
                if abs(dt_min - target_min) <= 10:
                    nearby.append((dt, msg, info))

            if nearby:
                for dt, msg, info in sorted(nearby, key=lambda x: x[0]):
                    time_str = dt.strftime('%H:%M')
                    sig_type = info.get('type', '?')
                    direction = info.get('dir_symbol', '')
                    level = info.get('level', '')
                    ema = info.get('ema', '?')
                    close = info.get('close', '')
                    print(f"    {time_str} {sig_type} {direction} {level} ema={ema} C={close}")
            else:
                print(f"    NO SIGNALS within 10 min of target time")
        else:
            print(f"    {symbol} NOT FOUND in March 5 data")

    # Step 11: Compute TSLA level prices from last signals before March 5
    print("\n" + "=" * 80)
    print("TSLA LEVELS (from pine log prices field)")
    print("=" * 80)
    if 'TSLA' in mar5_data:
        # Also check March 4 data for level context
        for hash_id, rows in file_data.items():
            symbol = file_symbol_map[hash_id]['symbol']
            if symbol == 'TSLA':
                # Get last few entries before March 5 and first entries on March 5
                mar4_entries = []
                mar5_entries = []
                for dt_str, msg in rows:
                    dt = parse_datetime(dt_str)
                    if dt:
                        if dt.date() == date(2026, 3, 4):
                            mar4_entries.append((dt, msg))
                        elif dt.date() == date(2026, 3, 5):
                            mar5_entries.append((dt, msg))

                if mar4_entries:
                    print(f"\n  Last March 4 entries:")
                    for dt, msg in mar4_entries[-5:]:
                        time_str = dt.strftime('%H:%M')
                        # Extract prices field
                        prices_m = re.search(r'prices=([\d./]+)', msg)
                        prices = prices_m.group(1) if prices_m else ''
                        # Extract level
                        level_m = re.search(r'(BRK|REV|RCL|~ ~)\s+([\w\s+]+?)(?=\s+vol=)', msg)
                        level = level_m.group(2).strip() if level_m else ''
                        close_m = re.search(r'C([\d.]+)', msg)
                        close = close_m.group(1) if close_m else ''
                        print(f"    {time_str}: {level} prices={prices} C={close}")

                if mar5_entries:
                    print(f"\n  First March 5 entries:")
                    for dt, msg in mar5_entries[:10]:
                        time_str = dt.strftime('%H:%M')
                        prices_m = re.search(r'prices=([\d./]+)', msg)
                        prices = prices_m.group(1) if prices_m else ''
                        level_m = re.search(r'(BRK|REV|RCL|~ ~)\s+([\w\s+]+?)(?=\s+vol=)', msg)
                        level = level_m.group(2).strip() if level_m else ''
                        close_m = re.search(r'C([\d.]+)', msg)
                        close = close_m.group(1) if close_m else ''
                        ohlc_m = re.search(r'O([\d.]+)\s+H([\d.]+)\s+L([\d.]+)\s+C([\d.]+)', msg)
                        ohlc = f"O={ohlc_m.group(1)} H={ohlc_m.group(2)} L={ohlc_m.group(3)} C={ohlc_m.group(4)}" if ohlc_m else ''
                        buf_m = re.search(r'buf=([\d.]+)', msg)
                        buf = buf_m.group(1) if buf_m else ''
                        print(f"    {time_str}: {level} prices={prices} {ohlc} buf={buf}")

    # Step 12: Check all March 5 raw messages for any mention of levels that would
    # correspond to PM H / Yest H for TSLA around 10:16
    print("\n" + "=" * 80)
    print("TSLA: ALL SUPPRESSED/DIM SIGNALS FULL DETAIL (March 5)")
    print("=" * 80)
    if 'TSLA' in mar5_data:
        for dt, msg, info in sorted(mar5_data['TSLA'], key=lambda x: x[0]):
            if info.get('type') == 'SUPPRESSED' or '~ ~' in msg:
                time_str = dt.strftime('%H:%M')
                print(f"\n  {time_str}: {msg}")

    # Step 13: Full raw dump of all TSLA March 5 messages (for the investigation report)
    print("\n" + "=" * 80)
    print("TSLA RAW MESSAGES (March 5) - COMPLETE")
    print("=" * 80)
    for hash_id, rows in file_data.items():
        symbol = file_symbol_map[hash_id]['symbol']
        if symbol == 'TSLA':
            for dt_str, msg in rows:
                dt = parse_datetime(dt_str)
                if dt and dt.date() == target_date:
                    print(f"  {dt_str}: {msg}")

if __name__ == '__main__':
    main()
