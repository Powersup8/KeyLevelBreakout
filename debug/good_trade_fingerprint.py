"""
Good Trade Fingerprint Analysis
- Parse Pine logs → extract signal attributes
- Match CONF results to originating breakout signals
- Measure MFE/MAE from 1m candle data
- Profile good vs bad trades
- Scan for missed opportunities
"""
import csv, re, sys
from datetime import datetime, timedelta, timezone
from collections import defaultdict
ET = timezone(timedelta(hours=-5))

LOG_FILE = "pine-logs-Key Level Breakout_11473.csv"
CANDLE_FILE = "BATS_TSLA, 1_356f9.csv"

# ── Parse 1m candle data ──────────────────────────────────
candles = {}  # datetime → {o, h, l, c, vol}
with open(CANDLE_FILE) as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        dt = datetime.fromisoformat(row[0])
        candles[dt] = {
            'o': float(row[1]), 'h': float(row[2]),
            'l': float(row[3]), 'c': float(row[4]),
            'vol': float(row[18])
        }

sorted_times = sorted(candles.keys())

def is_regular(dt):
    return (dt.hour == 9 and dt.minute >= 30) or (10 <= dt.hour <= 15) or (dt.hour == 16 and dt.minute == 0)

def measure_mfe_mae(entry_time, direction, entry_price, atr, minutes=60):
    """Measure MFE/MAE over next N minutes from entry"""
    mfe = 0.0
    mae = 0.0
    start = entry_time + timedelta(minutes=1)
    end = entry_time + timedelta(minutes=minutes)
    for t in sorted_times:
        if t < start:
            continue
        if t > end:
            break
        if not is_regular(t):
            continue
        c = candles[t]
        if direction == "bull":
            excursion_h = c['h'] - entry_price
            excursion_l = c['l'] - entry_price
            mfe = max(mfe, excursion_h)
            mae = min(mae, excursion_l)
        else:
            excursion_h = entry_price - c['l']
            excursion_l = entry_price - c['h']
            mfe = max(mfe, excursion_h)
            mae = min(mae, excursion_l)
    return mfe / atr if atr > 0 else 0, mae / atr if atr > 0 else 0

# ── Parse Pine log signals ────────────────────────────────
signals = []  # list of dicts
conf_results = {}  # date_str → result

with open(LOG_FILE) as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        dt_str = row[0]
        msg = row[1]
        dt = datetime.fromisoformat(dt_str)
        
        # CONF result
        if "CONF" in msg and "→" in msg:
            date_key = dt.strftime("%Y-%m-%d")
            time_key = dt.strftime("%H:%M")
            direction = "bull" if "▲" in msg else "bear"
            result = "✓★" if "✓★" in msg else "✓" if "✓" in msg else "✗"
            conf_results[(date_key, direction)] = {
                'result': result, 'time': time_key, 'dt': dt
            }
            continue
        
        # Skip retests (◆)
        if "◆" in msg and "BRK" not in msg:
            continue
        
        # Parse signal attributes
        m_dir = "bull" if "▲" in msg else "bear" if "▼" in msg else None
        if not m_dir:
            continue
        
        m_type = "BRK" if "BRK" in msg else "REV" if ("~ " in msg or "~~" in msg) else None
        if not m_type:
            continue
            
        # Extract attributes
        vol_m = re.search(r'vol=(\d+\.?\d*)x', msg)
        pos_m = re.search(r'pos=([v^])(\d+)', msg)
        vwap_m = re.search(r'vwap=(\w+)', msg)
        ema_m = re.search(r'ema=(\w+)', msg)
        rs_m = re.search(r'rs=([+-]?\d+\.?\d*)%', msg)
        adx_m = re.search(r'adx=(\d+)', msg)
        body_m = re.search(r'body=(\d+)%', msg)
        atr_m = re.search(r'ATR=(\d+\.?\d*)', msg)
        ohlc_m = re.search(r'O(\d+\.?\d*) H(\d+\.?\d*) L(\d+\.?\d*) C(\d+\.?\d*)', msg)
        
        # Level names
        levels = []
        for lvl in ["PM H", "PM L", "Yest H", "Yest L", "Week H", "Week L", "ORB H", "ORB L"]:
            if lvl in msg:
                levels.append(lvl)
        
        time_str = re.search(r'(\d+:\d+)', msg)
        
        sig = {
            'dt': dt,
            'date': dt.strftime("%Y-%m-%d"),
            'time': time_str.group(1) if time_str else "",
            'direction': m_dir,
            'type': m_type,
            'levels': levels,
            'vol': float(vol_m.group(1)) if vol_m else 0,
            'pos': int(pos_m.group(2)) if pos_m else 0,
            'pos_dir': pos_m.group(1) if pos_m else "",
            'vwap': vwap_m.group(1) if vwap_m else "",
            'ema': ema_m.group(1) if ema_m else "",
            'rs': float(rs_m.group(1)) if rs_m else 0,
            'adx': int(adx_m.group(1)) if adx_m else 0,
            'body': int(body_m.group(1)) if body_m else 0,
            'atr': float(atr_m.group(1)) if atr_m else 0,
            'close': float(ohlc_m.group(4)) if ohlc_m else 0,
            'open': float(ohlc_m.group(1)) if ohlc_m else 0,
            'high': float(ohlc_m.group(2)) if ohlc_m else 0,
            'low': float(ohlc_m.group(3)) if ohlc_m else 0,
            'multi_level': len(levels) >= 2,
            'msg': msg
        }
        
        # Time bucket
        hour = dt.hour
        minute = dt.minute
        total_min = hour * 60 + minute
        if total_min < 600:  # before 10:00
            sig['time_bucket'] = "9:30-10:00"
        elif total_min < 660:
            sig['time_bucket'] = "10:00-11:00"
        elif total_min < 720:
            sig['time_bucket'] = "11:00-12:00"
        else:
            sig['time_bucket'] = "12:00+"
        
        # Volume bucket
        if sig['vol'] < 2:
            sig['vol_bucket'] = "<2x"
        elif sig['vol'] <= 5:
            sig['vol_bucket'] = "2-5x"
        elif sig['vol'] <= 10:
            sig['vol_bucket'] = "5-10x"
        else:
            sig['vol_bucket'] = "10x+"
        
        signals.append(sig)

# ── Match signals to CONF results ─────────────────────────
# Only first BRK signal per day+direction gets CONF
for sig in signals:
    if sig['type'] == 'BRK':
        key = (sig['date'], sig['direction'])
        if key in conf_results:
            sig['conf'] = conf_results[key]['result']
        else:
            sig['conf'] = None  # no CONF tracked (not first breakout?)
    else:
        sig['conf'] = None

# ── Measure MFE/MAE for all signals ──────────────────────
for sig in signals:
    mfe, mae = measure_mfe_mae(sig['dt'], sig['direction'], sig['close'], sig['atr'], minutes=60)
    sig['mfe_atr'] = mfe
    sig['mae_atr'] = mae
    sig['mfe_mae_ratio'] = mfe / abs(mae) if mae != 0 else 999

# ── Output analysis ───────────────────────────────────────
out = []
def p(s=""):
    out.append(s)

p("# Good Trade Fingerprint Analysis — TSLA v2.6d")
p(f"Data: {len(signals)} signals, {len(conf_results)} CONF results")
p(f"Period: {signals[0]['date']} to {signals[-1]['date']}")
p()

# Separate good (CONF ✓/✓★) vs failed
good_brk = [s for s in signals if s['conf'] in ('✓', '✓★')]
bad_brk = [s for s in signals if s['conf'] == '✗']
all_brk = good_brk + bad_brk
reversals = [s for s in signals if s['type'] == 'REV']

p(f"## CONF Results: {len(good_brk)} good / {len(bad_brk)} bad / {len(reversals)} reversals")
p()

# ── Profile comparison ────────────────────────────────────
def profile(sigs, label):
    if not sigs:
        return
    p(f"### {label} (n={len(sigs)})")
    
    # Time distribution
    time_dist = defaultdict(int)
    for s in sigs:
        time_dist[s['time_bucket']] += 1
    p("**Time:** " + ", ".join(f"{k}: {v} ({v*100//len(sigs)}%)" for k, v in sorted(time_dist.items())))
    
    # Volume
    vol_dist = defaultdict(int)
    for s in sigs:
        vol_dist[s['vol_bucket']] += 1
    avg_vol = sum(s['vol'] for s in sigs) / len(sigs)
    p(f"**Volume:** avg {avg_vol:.1f}x — " + ", ".join(f"{k}: {v}" for k, v in sorted(vol_dist.items())))
    
    # VWAP alignment
    vwap_aligned = sum(1 for s in sigs if 
        (s['direction'] == 'bull' and s['vwap'] == 'above') or
        (s['direction'] == 'bear' and s['vwap'] == 'below'))
    p(f"**VWAP aligned:** {vwap_aligned}/{len(sigs)} ({vwap_aligned*100//len(sigs)}%)")
    
    # EMA alignment
    ema_aligned = sum(1 for s in sigs if
        (s['direction'] == 'bull' and s['ema'] == 'bull') or
        (s['direction'] == 'bear' and s['ema'] == 'bear'))
    p(f"**EMA aligned:** {ema_aligned}/{len(sigs)} ({ema_aligned*100//len(sigs)}%)")
    
    # ADX
    avg_adx = sum(s['adx'] for s in sigs) / len(sigs)
    high_adx = sum(1 for s in sigs if s['adx'] >= 25)
    p(f"**ADX:** avg {avg_adx:.0f}, ≥25: {high_adx}/{len(sigs)} ({high_adx*100//len(sigs)}%)")
    
    # Body quality
    avg_body = sum(s['body'] for s in sigs) / len(sigs)
    strong_body = sum(1 for s in sigs if s['body'] >= 70)
    p(f"**Body:** avg {avg_body:.0f}%, ≥70%: {strong_body}/{len(sigs)} ({strong_body*100//len(sigs)}%)")
    
    # RS
    avg_rs = sum(s['rs'] for s in sigs) / len(sigs)
    p(f"**RS vs SPY:** avg {avg_rs:+.1f}%")
    
    # Multi-level
    multi = sum(1 for s in sigs if s['multi_level'])
    p(f"**Multi-level:** {multi}/{len(sigs)} ({multi*100//len(sigs)}%)")
    
    # Direction
    bulls = sum(1 for s in sigs if s['direction'] == 'bull')
    p(f"**Direction:** bull {bulls}, bear {len(sigs)-bulls}")
    
    # Level types
    level_dist = defaultdict(int)
    for s in sigs:
        for l in s['levels']:
            level_dist[l] += 1
    p(f"**Levels:** " + ", ".join(f"{k}: {v}" for k, v in sorted(level_dist.items(), key=lambda x: -x[1])))
    
    # MFE/MAE
    avg_mfe = sum(s['mfe_atr'] for s in sigs) / len(sigs)
    avg_mae = sum(s['mae_atr'] for s in sigs) / len(sigs)
    p(f"**MFE (60min):** avg {avg_mfe:.2f} ATR")
    p(f"**MAE (60min):** avg {avg_mae:.2f} ATR")
    p()

profile(good_brk, "GOOD Breakouts (CONF ✓/✓★)")
profile(bad_brk, "BAD Breakouts (CONF ✗)")
profile(reversals, "Reversals (all)")

# ── Individual good trades ────────────────────────────────
p("## Individual Good Trades")
p()
p("| Date | Time | Dir | Levels | Vol | Body | ADX | VWAP | EMA | RS | MFE | MAE |")
p("|------|------|-----|--------|-----|------|-----|------|-----|----|-----|-----|")
for s in good_brk:
    p(f"| {s['date']} | {s['time']} | {'▲' if s['direction']=='bull' else '▼'} | {'+'.join(s['levels'])} | {s['vol']:.1f}x | {s['body']}% | {s['adx']} | {s['vwap']} | {s['ema']} | {s['rs']:+.1f}% | {s['mfe_atr']:.2f} | {s['mae_atr']:.2f} |")
p()

p("## Individual Bad Trades")
p()
p("| Date | Time | Dir | Levels | Vol | Body | ADX | VWAP | EMA | RS | MFE | MAE |")
p("|------|------|-----|--------|-----|------|-----|------|-----|----|-----|-----|")
for s in bad_brk:
    p(f"| {s['date']} | {s['time']} | {'▲' if s['direction']=='bull' else '▼'} | {'+'.join(s['levels'])} | {s['vol']:.1f}x | {s['body']}% | {s['adx']} | {s['vwap']} | {s['ema']} | {s['rs']:+.1f}% | {s['mfe_atr']:.2f} | {s['mae_atr']:.2f} |")
p()

# ── Fingerprint: what separates good from bad ─────────────
p("## Fingerprint: Good vs Bad")
p()
if good_brk and bad_brk:
    metrics = [
        ("Avg Volume", lambda s: s['vol']),
        ("Avg Body %", lambda s: s['body']),
        ("Avg ADX", lambda s: s['adx']),
        ("Avg RS %", lambda s: s['rs']),
        ("VWAP aligned %", lambda sigs: sum(1 for s in sigs if (s['direction']=='bull' and s['vwap']=='above') or (s['direction']=='bear' and s['vwap']=='below')) * 100 / len(sigs)),
        ("EMA aligned %", lambda sigs: sum(1 for s in sigs if (s['direction']=='bull' and s['ema']=='bull') or (s['direction']=='bear' and s['ema']=='bear')) * 100 / len(sigs)),
        ("Multi-level %", lambda sigs: sum(1 for s in sigs if s['multi_level']) * 100 / len(sigs)),
        ("Before 11:00 %", lambda sigs: sum(1 for s in sigs if s['time_bucket'] in ('9:30-10:00', '10:00-11:00')) * 100 / len(sigs)),
        ("Avg MFE (ATR)", lambda s: s['mfe_atr']),
        ("Avg MAE (ATR)", lambda s: s['mae_atr']),
    ]
    
    p("| Metric | GOOD | BAD | Delta |")
    p("|--------|------|-----|-------|")
    for name, fn in metrics:
        if "%" in name and "Avg" not in name:
            g = fn(good_brk)
            b = fn(bad_brk)
            p(f"| {name} | {g:.0f}% | {b:.0f}% | {g-b:+.0f}% |")
        else:
            g = sum(fn(s) for s in good_brk) / len(good_brk)
            b = sum(fn(s) for s in bad_brk) / len(bad_brk)
            p(f"| {name} | {g:.1f} | {b:.1f} | {g-b:+.1f} |")
p()

# ── Scan for missed opportunities ─────────────────────────
# Look for 5m bars that match "good fingerprint" but no signal fired
p("## Missed Opportunities Scan")
p("Looking for 5m bars with: strong directional move, high volume, near key levels, no signal")
p()

# Build 5m bars from 1m data
bars_5m = {}
for t, c in candles.items():
    if not is_regular(t):
        continue
    date = t.date()
    slot_min = (t.minute // 5) * 5
    key = (date, t.hour, slot_min)
    if key not in bars_5m:
        bars_5m[key] = {'o': c['o'], 'h': c['h'], 'l': c['l'], 'c': c['c'], 'vol': c['vol'], 'dt': t}
    else:
        bars_5m[key]['h'] = max(bars_5m[key]['h'], c['h'])
        bars_5m[key]['l'] = min(bars_5m[key]['l'], c['l'])
        bars_5m[key]['c'] = c['c']
        bars_5m[key]['vol'] += c['vol']

# Get signal timestamps for exclusion
signal_times = set()
for s in signals:
    signal_times.add(s['dt'].strftime("%Y-%m-%d %H:%M"))

# Get daily volume SMA (approx from 5m bars)
daily_vol = defaultdict(list)
for key, bar in bars_5m.items():
    daily_vol[key[0]].append(bar['vol'])

# Key levels per day (extract from signals)
daily_levels = defaultdict(dict)
for s in signals:
    for lvl_name in s['levels']:
        # Parse price from msg
        prices_m = re.search(r'prices=([0-9./]+)', s['msg'])
        if prices_m:
            prices = prices_m.group(1).split('/')
            daily_levels[s['date']][lvl_name] = [float(p) for p in prices if p]

# Look for strong 5m bars with no signal
# "Good fingerprint": vol > 2x avg, body > 60%, near a key level, clear direction
missed = []
for key, bar in sorted(bars_5m.items()):
    date, hour, minute = key
    date_str = date.isoformat()
    time_str = f"{hour}:{minute:02d}"
    dt_str = f"{date_str} {hour:02d}:{minute:02d}"
    
    if dt_str in signal_times:
        continue  # already has a signal
    
    # Compute bar metrics
    body = abs(bar['c'] - bar['o'])
    full_range = bar['h'] - bar['l']
    if full_range == 0:
        continue
    body_pct = body / full_range
    
    # Direction
    is_bull = bar['c'] > bar['o']
    
    # Volume ratio (vs day average)
    day_vols = daily_vol.get(date, [])
    if not day_vols or len(day_vols) < 10:
        continue
    avg_vol = sum(day_vols) / len(day_vols)
    vol_ratio = bar['vol'] / avg_vol if avg_vol > 0 else 0
    
    # Check: strong move + volume + body quality
    if vol_ratio < 2.0 or body_pct < 0.6 or full_range < 1.0:
        continue
    
    # Check proximity to key levels
    near_level = None
    for lvl_name, prices in daily_levels.get(date_str, {}).items():
        for price in prices:
            if abs(bar['h'] - price) < 1.0 or abs(bar['l'] - price) < 1.0 or abs(bar['c'] - price) < 1.0:
                near_level = f"{lvl_name}@{price:.2f}"
                break
        if near_level:
            break
    
    # MFE check: did this move continue?
    entry_dt = datetime(date.year, date.month, date.day, hour, minute, tzinfo=ET) + timedelta(minutes=5)
    atr = 14.85  # approximate for TSLA
    mfe, mae = measure_mfe_mae(entry_dt, "bull" if is_bull else "bear", bar['c'], atr, minutes=30)
    
    if mfe > 0.15:  # meaningful follow-through
        missed.append({
            'date': date_str,
            'time': time_str,
            'dir': '▲' if is_bull else '▼',
            'o': bar['o'], 'h': bar['h'], 'l': bar['l'], 'c': bar['c'],
            'vol': vol_ratio,
            'body': body_pct * 100,
            'near_level': near_level or "—",
            'mfe': mfe,
            'mae': mae,
            'range': full_range
        })

# Sort by MFE descending
missed.sort(key=lambda x: -x['mfe'])

p(f"Found {len(missed)} potential missed signals (vol≥2x, body≥60%, range≥$1, MFE>0.15 ATR)")
p()
if missed:
    p("### Top 20 Missed Opportunities (by MFE)")
    p()
    p("| Date | Time | Dir | O→C | Range | Vol | Body | Near Level | MFE | MAE |")
    p("|------|------|-----|-----|-------|-----|------|------------|-----|-----|")
    for m in missed[:20]:
        p(f"| {m['date']} | {m['time']} | {m['dir']} | {m['o']:.2f}→{m['c']:.2f} | ${m['range']:.2f} | {m['vol']:.1f}x | {m['body']:.0f}% | {m['near_level']} | {m['mfe']:.2f} | {m['mae']:.2f} |")
p()

# ── Summary ───────────────────────────────────────────────
p("## Key Takeaways")
p()
if good_brk and bad_brk:
    g_vol = sum(s['vol'] for s in good_brk) / len(good_brk)
    b_vol = sum(s['vol'] for s in bad_brk) / len(bad_brk)
    g_body = sum(s['body'] for s in good_brk) / len(good_brk)
    b_body = sum(s['body'] for s in bad_brk) / len(bad_brk)
    g_adx = sum(s['adx'] for s in good_brk) / len(good_brk)
    b_adx = sum(s['adx'] for s in bad_brk) / len(bad_brk)
    g_morning = sum(1 for s in good_brk if s['time_bucket'] in ('9:30-10:00', '10:00-11:00')) * 100 / len(good_brk)
    b_morning = sum(1 for s in bad_brk if s['time_bucket'] in ('9:30-10:00', '10:00-11:00')) * 100 / len(bad_brk)
    
    p("**Good trade fingerprint:**")
    if g_vol > b_vol * 1.2:
        p(f"- Higher volume: {g_vol:.1f}x avg (vs {b_vol:.1f}x for bad)")
    if g_body > b_body * 1.1:
        p(f"- Stronger body: {g_body:.0f}% avg (vs {b_body:.0f}% for bad)")
    if g_adx > b_adx * 1.1:
        p(f"- Higher ADX: {g_adx:.0f} avg (vs {b_adx:.0f} for bad)")
    if g_morning > b_morning:
        p(f"- More morning: {g_morning:.0f}% before 11am (vs {b_morning:.0f}% for bad)")
    
    g_vwap = sum(1 for s in good_brk if (s['direction']=='bull' and s['vwap']=='above') or (s['direction']=='bear' and s['vwap']=='below')) * 100 / len(good_brk)
    b_vwap = sum(1 for s in bad_brk if (s['direction']=='bull' and s['vwap']=='above') or (s['direction']=='bear' and s['vwap']=='below')) * 100 / len(bad_brk)
    if g_vwap > b_vwap:
        p(f"- VWAP aligned: {g_vwap:.0f}% (vs {b_vwap:.0f}% for bad)")

# Write to file
output_path = "good-trade-fingerprint.md"
with open(output_path, 'w') as f:
    f.write('\n'.join(out))
print(f"Analysis written to debug/{output_path}")
print(f"Signals: {len(signals)}, Good BRK: {len(good_brk)}, Bad BRK: {len(bad_brk)}, Reversals: {len(reversals)}")
print(f"Missed opportunities: {len(missed)}")
