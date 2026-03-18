#!/usr/bin/env python3
"""Parse all v3.2 pine log files for March 6, 2026 entries."""
import glob
import csv
import re
from collections import defaultdict
from datetime import datetime

LOG_DIR = "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug"
PATTERN = f"{LOG_DIR}/pine-logs-Key Level Breakout v3.2_*.csv"

files = sorted(glob.glob(PATTERN))
print(f"Found {len(files)} pine log files\n")

# Collect all March 6 entries across all files
all_entries = []
file_symbols = {}

for fpath in files:
    fname = fpath.split("/")[-1]
    hash_id = fname.split("_")[-1].replace(".csv", "")
    mar6_rows = []

    with open(fpath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) < 2:
                continue
            date_str = row[0]
            msg = row[1]
            # Check for March 6, 2026
            if '2026-03-06' in date_str:
                mar6_rows.append((date_str, msg))

    if mar6_rows:
        # Try to identify symbol from message content (prices, levels)
        # Look for symbol-specific clues
        symbol = "UNKNOWN"
        # Check ATR range to identify symbol
        for _, msg in mar6_rows:
            # Try to figure out symbol from context - check for specific price ranges
            # SPY ~580-600, AAPL ~230-250, AMD ~100-130, AMZN ~200-230, etc.
            atr_match = re.search(r'ATR=([\d.]+)', msg)
            close_match = re.search(r'C([\d.]+)', msg)
            if close_match:
                close = float(close_match.group(1))
                if 560 < close < 620:
                    symbol = "SPY"
                elif 220 < close < 260:
                    symbol = "AAPL"
                elif 85 < close < 140:
                    symbol = "AMD"
                elif 195 < close < 230:
                    symbol = "AMZN"
                elif 250 < close < 300:
                    symbol = "GLD"
                elif 170 < close < 210:
                    symbol = "GOOGL"
                elif 600 < close < 720:
                    symbol = "META"
                elif 400 < close < 460:
                    symbol = "MSFT"
                elif 110 < close < 155:
                    symbol = "NVDA"
                elif 490 < close < 550:
                    symbol = "QQQ"
                elif 28 < close < 38:
                    symbol = "SLV"
                elif 250 < close < 380:
                    symbol = "TSLA"
                elif 155 < close < 200:
                    symbol = "TSM"
                break

        file_symbols[hash_id] = symbol
        for date_str, msg in mar6_rows:
            all_entries.append((symbol, hash_id, date_str, msg))
        print(f"  {fname}: {len(mar6_rows)} entries on Mar 6 → {symbol}")
    else:
        print(f"  {fname}: 0 entries on Mar 6")

print(f"\nTotal March 6 entries: {len(all_entries)}")
print(f"Symbols with data: {sorted(set(e[0] for e in all_entries))}")

# Now parse and categorize
signals = []  # (symbol, time, dir, type, level, details)
confs = []    # (symbol, time, result, details)
bails = []    # (symbol, time, result, details)
other = []    # everything else

for symbol, hash_id, date_str, msg in all_entries:
    # Extract time from message
    time_match = re.search(r'\[KLB\]\s+(\d+:\d+)', msg)
    time_str = time_match.group(1) if time_match else "??:??"

    # Direction
    direction = "BULL" if '▲' in msg else "BEAR" if '▼' in msg else "?"

    # Signal type detection
    if 'CONF ✓★' in msg or 'CONF ✓⭐' in msg or 'CONF ✓✦' in msg:
        confs.append((symbol, time_str, "CONF_STAR", msg.strip()))
    elif 'CONF ✓' in msg:
        confs.append((symbol, time_str, "CONF_PASS", msg.strip()))
    elif 'CONF ✗' in msg:
        confs.append((symbol, time_str, "CONF_FAIL", msg.strip()))
    elif 'BAIL' in msg:
        bail_type = "BAIL" if "→BAIL" in msg or "BAIL" in msg else "HOLD"
        bails.append((symbol, time_str, bail_type, msg.strip()))
    elif 'HOLD' in msg:
        bails.append((symbol, time_str, "HOLD", msg.strip()))
    elif 'RNG range break' in msg:
        vol_match = re.search(r'vol=([\d.]+)x', msg)
        vol = vol_match.group(1) if vol_match else "?"
        signals.append((symbol, time_str, direction, "RNG", "range", f"vol={vol}x"))
    elif 'FADE at' in msg:
        level_match = re.search(r'FADE at ([\d.]+)', msg)
        level = level_match.group(1) if level_match else "?"
        signals.append((symbol, time_str, direction, "FADE", f"@{level}", ""))
    elif 'EXREV' in msg:
        signals.append((symbol, time_str, direction, "EXREV", "", msg.strip()))
    elif 'QBS' in msg or 'Quick Bear' in msg or 'Quick Bull' in msg:
        signals.append((symbol, time_str, direction, "QBS", "", msg.strip()))
    elif re.search(r'~ [~x✓★⭐✦]', msg):
        # Standard BRK/REV signal - parse level name and confirmation status
        # Check for REV
        is_rev = 'REV' in msg
        sig_type = "REV" if is_rev else "BRK"

        # Parse level name(s)
        level_match = re.search(r'(?:~ [~x✓★⭐✦]+\s+)(.*?)(?:\s+vol=)', msg)
        level_name = level_match.group(1).strip() if level_match else "?"

        # Parse confirmation status from the ~x✓ markers
        conf_marker = re.search(r'~ ([~x✓★⭐✦]+)\s', msg)
        conf_str = conf_marker.group(1) if conf_marker else ""

        # Parse key metrics
        vol_match = re.search(r'vol=([\d.]+)x', msg)
        rs_match = re.search(r'rs=\+?([\d]+)%', msg)
        ema_match = re.search(r'ema=(\w+)', msg)
        vwap_match = re.search(r'vwap=(\w+)', msg)
        adx_match = re.search(r'adx=(\d+)', msg)

        vol = vol_match.group(1) if vol_match else "?"
        rs = rs_match.group(1) if rs_match else "?"
        ema = ema_match.group(1) if ema_match else "?"
        vwap = vwap_match.group(1) if vwap_match else "?"
        adx = adx_match.group(1) if adx_match else "?"

        details = f"vol={vol}x ema={ema} vwap={vwap} rs={rs}% adx={adx} conf={conf_str}"
        signals.append((symbol, time_str, direction, sig_type, level_name, details))
    else:
        other.append((symbol, time_str, msg.strip()))

# Print results
print("\n" + "="*100)
print("SIGNALS (BRK/REV/RNG/FADE/EXREV/QBS)")
print("="*100)
print(f"{'Symbol':<8} {'Time':<7} {'Dir':<5} {'Type':<6} {'Level':<25} {'Details'}")
print("-"*100)
for sym, t, d, typ, lvl, det in sorted(signals, key=lambda x: (x[0], x[1])):
    print(f"{sym:<8} {t:<7} {d:<5} {typ:<6} {lvl:<25} {det}")

print(f"\nTotal signals: {len(signals)}")

print("\n" + "="*100)
print("CONFIRMATIONS")
print("="*100)
print(f"{'Symbol':<8} {'Time':<7} {'Result':<12} {'Message'}")
print("-"*100)
for sym, t, res, msg in sorted(confs, key=lambda x: (x[0], x[1])):
    # Truncate message
    print(f"{sym:<8} {t:<7} {res:<12} {msg[:100]}")

print(f"\nTotal CONF entries: {len(confs)}")

print("\n" + "="*100)
print("BAIL/HOLD")
print("="*100)
for sym, t, res, msg in sorted(bails, key=lambda x: (x[0], x[1])):
    print(f"{sym:<8} {t:<7} {res:<12} {msg[:120]}")

print(f"\nTotal BAIL/HOLD entries: {len(bails)}")

if other:
    print("\n" + "="*100)
    print("OTHER ENTRIES")
    print("="*100)
    for sym, t, msg in sorted(other, key=lambda x: (x[0], x[1])):
        print(f"{sym:<8} {t:<7} {msg[:120]}")

# Summary by symbol
print("\n" + "="*100)
print("SUMMARY BY SYMBOL")
print("="*100)
sym_signals = defaultdict(list)
for s in signals:
    sym_signals[s[0]].append(s)
sym_confs = defaultdict(list)
for c in confs:
    sym_confs[c[0]].append(c)

for sym in sorted(set(e[0] for e in all_entries)):
    sigs = sym_signals.get(sym, [])
    cfs = sym_confs.get(sym, [])
    conf_pass = sum(1 for c in cfs if c[2] in ("CONF_PASS", "CONF_STAR"))
    conf_fail = sum(1 for c in cfs if c[2] == "CONF_FAIL")
    print(f"\n{sym}: {len(sigs)} signals, {conf_pass} CONF pass, {conf_fail} CONF fail")
    for s in sigs:
        print(f"  {s[1]} {s[2]} {s[3]} {s[4]} | {s[5]}")
    for c in cfs:
        print(f"  {c[1]} {c[2]} | {c[3][:80]}")
