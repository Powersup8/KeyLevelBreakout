#!/usr/bin/env python3
"""Analyze the 2,895 suppressed bull REV at HIGH signals — profitability breakdown."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util

spec = importlib.util.spec_from_file_location('v33bt', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'v33_backtest.py'))
bt = importlib.util.module_from_spec(spec)
sys.modules['v33bt'] = bt
spec.loader.exec_module(bt)

HIGH_LEVELS = ['PM H', 'ORB H', 'Yest H', 'Week H']

def is_suppressed(row):
    if row.get('sig_type', '') != 'REV': return False
    if row.get('direction', '') != 'bull': return False
    lvl = row.get('levels', '')
    return any(h in lvl for h in HIGH_LEVELS)

# Load v3.3 signals
sigs, _ = bt.load_and_parse_logs('v33')
bt.compute_dim_status(sigs)

# Load IB data and measure MFE/MAE (same pattern as v33_backtest.py run_backtest)
syms = sorted(set(r['symbol'] for r in sigs if r.get('symbol')))
ib_cache = {}
for s in syms:
    try:
        bars_1m = bt.load_1m(s)
        daily_df = bt.load_daily(s)
        atr_series = bt.compute_atr(daily_df)
        ib_cache[s] = (bars_1m, atr_series)
    except Exception as e:
        print(f'  {s}: ERROR {e}')

# Measure MFE/MAE per symbol
for s in syms:
    if s not in ib_cache:
        continue
    bars_1m, atr_series = ib_cache[s]
    sym_sigs = [r for r in sigs if r['symbol'] == s]
    bt.measure_mfe_mae(sym_sigs, bars_1m, atr_series)

# Filter to suppressed with data
suppressed = [r for r in sigs if is_suppressed(r) and r.get('mfe_atr') is not None]
print(f'Suppressed signals with MFE/MAE data: {len(suppressed)}')

wins = [r for r in suppressed if r.get('outcome') == 'WIN']
losses = [r for r in suppressed if r.get('outcome') == 'LOSS']
flats = [r for r in suppressed if r.get('outcome') == 'FLAT']

print(f'  WIN:  {len(wins)} ({100*len(wins)/len(suppressed):.1f}%)')
print(f'  LOSS: {len(losses)} ({100*len(losses)/len(suppressed):.1f}%)')
print(f'  FLAT: {len(flats)} ({100*len(flats)/len(suppressed):.1f}%)')
print()

# === WINNERS BREAKDOWN ===
if wins:
    mfes = [r['mfe_atr'] for r in wins]
    pnls = [r['pnl_atr'] for r in wins]
    print('=== WINNERS BREAKDOWN ===')
    print(f'  Total winner P&L: {sum(pnls):.1f} ATR')
    print(f'  Avg winner P&L:   {sum(pnls)/len(pnls):.3f} ATR')
    print(f'  Avg winner MFE:   {sum(mfes)/len(mfes):.3f} ATR')
    print()

    buckets = [(0, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 0.5), (0.5, 1.0), (1.0, 999)]
    labels = ['0-0.1', '0.1-0.2', '0.2-0.3', '0.3-0.5', '0.5-1.0', '1.0+']
    print(f'  {"MFE bucket":<12} {"Count":>6} {"Total P&L":>10} {"Avg P&L":>8}')
    print(f'  {"─"*12} {"─"*6} {"─"*10} {"─"*8}')
    for (lo, hi), lbl in zip(buckets, labels):
        b = [r for r in wins if lo <= r['mfe_atr'] < hi]
        if b:
            tp = sum(r['pnl_atr'] for r in b)
            print(f'  {lbl:<12} {len(b):>6} {tp:>+10.1f} {tp/len(b):>+8.3f}')

print()

# === LOSERS BREAKDOWN ===
if losses:
    maes = [r['mae_atr'] for r in losses]
    pnls = [r['pnl_atr'] for r in losses]
    print('=== LOSERS BREAKDOWN ===')
    print(f'  Total loser P&L:  {sum(pnls):.1f} ATR')
    print(f'  Avg loser P&L:    {sum(pnls)/len(pnls):.3f} ATR')
    print(f'  Avg loser MAE:    {sum(maes)/len(maes):.3f} ATR')
    print()

    buckets = [(0, 0.2), (0.2, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 5.0), (5.0, 999)]
    labels = ['0-0.2', '0.2-0.5', '0.5-1.0', '1.0-2.0', '2.0-5.0', '5.0+']
    print(f'  {"MAE bucket":<12} {"Count":>6} {"Total P&L":>10} {"Avg P&L":>8}')
    print(f'  {"─"*12} {"─"*6} {"─"*10} {"─"*8}')
    for (lo, hi), lbl in zip(buckets, labels):
        b = [r for r in losses if lo <= r['mae_atr'] < hi]
        if b:
            tp = sum(r['pnl_atr'] for r in b)
            print(f'  {lbl:<12} {len(b):>6} {tp:>+10.1f} {tp/len(b):>+8.3f}')

print()

# === MAJOR MOVES ===
print('=== 7 MAJOR MOVES (MFE >= 1.0) ===')
majors = sorted([r for r in suppressed if r['mfe_atr'] >= 1.0], key=lambda r: -r['mfe_atr'])
for r in majors:
    vol = r.get('vol_ratio', 'N/A')
    dim = r.get('dim_reasons', '')
    ema = r.get('ema_dir', '')
    print(f'  {r["symbol"]:5} {str(r["timestamp"].date())} {r["timestamp"].strftime("%H:%M"):5} lvl=[{r["levels"]}]  MFE={r["mfe_atr"]:.3f}  vol={vol}  ema={ema}  dim={dim}')

print()

# === MID-SIZE WINNERS ===
mid_winners = sorted([r for r in wins if 0.5 <= r['mfe_atr'] < 1.0], key=lambda r: -r['mfe_atr'])
print(f'=== MID-SIZE WINNERS (MFE 0.5-1.0 ATR): {len(mid_winners)} ===')
for r in mid_winners[:20]:
    vol = r.get('vol_ratio', 'N/A')
    ema = r.get('ema_dir', '')
    print(f'  {r["symbol"]:5} {str(r["timestamp"].date())} {r["timestamp"].strftime("%H:%M"):5} lvl=[{r["levels"]}]  MFE={r["mfe_atr"]:.3f}  P&L={r["pnl_atr"]:+.3f}  vol={vol}  ema={ema}')

print()

# === WHAT DISTINGUISHES WINNERS FROM LOSERS? ===
print('=== FILTER ANALYSIS: Can we rescue winners? ===')
print()

# By time of day
print('By time of day:')
from collections import defaultdict
time_buckets = defaultdict(lambda: {'win': 0, 'loss': 0, 'flat': 0, 'pnl': 0})
for r in suppressed:
    h = r['timestamp'].strftime('%H:%M')[:2]
    if h == '09':
        tb = '09:30-09:59'
    else:
        tb = f'{h}:xx'
    time_buckets[tb][r['outcome'].lower()] += 1
    time_buckets[tb]['pnl'] += r['pnl_atr']

for tb in sorted(time_buckets.keys()):
    d = time_buckets[tb]
    n = d['win'] + d['loss'] + d['flat']
    wr = 100 * d['win'] / n if n else 0
    print(f'  {tb:<14} N={n:>5}  Win={wr:.0f}%  Net={d["pnl"]:>+8.1f} ATR')

print()

# By level (single vs combined)
print('Single level vs combined:')
single = [r for r in suppressed if '+' not in r['levels']]
combined = [r for r in suppressed if '+' in r['levels']]
for label, grp in [('Single level', single), ('Combined levels', combined)]:
    n = len(grp)
    w = sum(1 for r in grp if r['outcome'] == 'WIN')
    p = sum(r['pnl_atr'] for r in grp)
    wr = 100 * w / n if n else 0
    print(f'  {label:<18} N={n:>5}  Win={wr:.0f}%  Net={p:>+8.1f} ATR')

print()

# By NVDA vs not
print('NVDA vs non-NVDA:')
nvda = [r for r in suppressed if r['symbol'] == 'NVDA']
non_nvda = [r for r in suppressed if r['symbol'] != 'NVDA']
for label, grp in [('NVDA', nvda), ('Non-NVDA', non_nvda)]:
    n = len(grp)
    w = sum(1 for r in grp if r['outcome'] == 'WIN')
    p = sum(r['pnl_atr'] for r in grp)
    wr = 100 * w / n if n else 0
    mfe_avg = sum(r['mfe_atr'] for r in grp) / n if n else 0
    mae_avg = sum(r['mae_atr'] for r in grp) / n if n else 0
    print(f'  {label:<18} N={n:>5}  Win={wr:.0f}%  MFE={mfe_avg:.3f}  MAE={mae_avg:.3f}  Net={p:>+8.1f} ATR')

print()

# By morning vs rest (can we keep morning only?)
print('Morning (09:30-09:59) vs rest:')
morning = [r for r in suppressed if r['timestamp'].strftime('%H:%M') < '10:00']
rest = [r for r in suppressed if r['timestamp'].strftime('%H:%M') >= '10:00']
for label, grp in [('Morning', morning), ('10:00+', rest)]:
    n = len(grp)
    w = sum(1 for r in grp if r['outcome'] == 'WIN')
    p = sum(r['pnl_atr'] for r in grp)
    wr = 100 * w / n if n else 0
    print(f'  {label:<18} N={n:>5}  Win={wr:.0f}%  Net={p:>+8.1f} ATR')

# Morning non-NVDA
morning_nonnvda = [r for r in morning if r['symbol'] != 'NVDA']
n = len(morning_nonnvda)
w = sum(1 for r in morning_nonnvda if r['outcome'] == 'WIN')
p = sum(r['pnl_atr'] for r in morning_nonnvda)
wr = 100 * w / n if n else 0
print(f'  {"Morn non-NVDA":<18} N={n:>5}  Win={wr:.0f}%  Net={p:>+8.1f} ATR')

print()

# By dim status
print('Dim vs not dimmed:')
dimmed = [r for r in suppressed if r.get('dim_reasons', '') and r['dim_reasons'] != 'none']
not_dimmed = [r for r in suppressed if not r.get('dim_reasons', '') or r['dim_reasons'] == 'none']
for label, grp in [('Dimmed', dimmed), ('Not dimmed', not_dimmed)]:
    n = len(grp)
    if n == 0: continue
    w = sum(1 for r in grp if r['outcome'] == 'WIN')
    p = sum(r['pnl_atr'] for r in grp)
    wr = 100 * w / n if n else 0
    print(f'  {label:<18} N={n:>5}  Win={wr:.0f}%  Net={p:>+8.1f} ATR')

print()

# === BOTTOM LINE ===
total_win_pnl = sum(r['pnl_atr'] for r in wins)
total_loss_pnl = sum(r['pnl_atr'] for r in losses)
print('=== BOTTOM LINE ===')
print(f'  All {len(suppressed)} suppressed signals:')
print(f'    Winner total P&L:  {total_win_pnl:+.1f} ATR ({len(wins)} signals)')
print(f'    Loser total P&L:   {total_loss_pnl:+.1f} ATR ({len(losses)} signals)')
print(f'    Net:               {total_win_pnl + total_loss_pnl:+.1f} ATR')

for thresh in [0.3, 0.5, 1.0]:
    good = [r for r in wins if r['mfe_atr'] >= thresh]
    print(f'  Winners with MFE>={thresh}: {len(good)} signals, P&L={sum(r["pnl_atr"] for r in good):+.1f} ATR')
