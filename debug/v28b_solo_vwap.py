#!/usr/bin/env python3
"""
CRITICAL FINDING: Solo MC signals that go AGAINST VWAP have 88% CONF pass rate.
This suggests counter-VWAP is a universal quality filter, not just for opposing pairs.
"""
import pandas as pd

signals = pd.read_csv('debug/v28a-signals.csv')
mc = signals[signals['line_type'] == 'MC'].copy()
mc['dt'] = pd.to_datetime(mc['datetime'], utc=True)
mc['date'] = mc['dt'].dt.date.astype(str)

conf_mc = signals[(signals['line_type'] == 'CONF') & (signals['conf_source'] == 'QBS/MC')].copy()
conf_mc['dt'] = pd.to_datetime(conf_mc['datetime'], utc=True)
conf_mc['date'] = conf_mc['dt'].dt.date.astype(str)

def dir_matches_vwap(d, v):
    return (d == 'bull' and v == 'above') or (d == 'bear' and v == 'below')

# ALL MC signals (not just opposing pairs)
all_mc_results = []
for _, row in mc.iterrows():
    day_conf = conf_mc[(conf_mc['symbol'] == row['symbol']) &
                       (conf_mc['date'] == row['date']) &
                       (conf_mc['direction'] == row['direction'])]
    if len(day_conf) > 0:
        conf = day_conf.iloc[0]['conf_result']
        all_mc_results.append({
            'symbol': row['symbol'],
            'date': row['date'],
            'time': row['time'],
            'direction': row['direction'],
            'vwap': row['vwap'],
            'ema': row['ema'],
            'vol': row['vol'],
            'body': row['body'],
            'adx': row['adx'],
            'close_pos': row['close_pos'],
            'ramp': row['ramp'],
            'range_atr': row['range_atr'],
            'conf': conf,
            'is_good': conf in ['star', 'pass'],
            'vwap_match': dir_matches_vwap(row['direction'], row['vwap']),
        })

amr = pd.DataFrame(all_mc_results)

print("=== ALL MC signals with CONF results ===")
print(f"Total: {len(amr)}")
print(f"Good (star+pass): {amr['is_good'].sum()}/{len(amr)} ({amr['is_good'].mean()*100:.0f}%)")
print()

# VWAP alignment
print("=== VWAP alignment on ALL MC signals ===")
for vwap_val in [True, False]:
    sub = amr[amr['vwap_match'] == vwap_val]
    label = 'VWAP-aligned' if vwap_val else 'VWAP-counter'
    good = sub['is_good'].sum()
    print(f"  {label}: {good}/{len(sub)} good ({good/len(sub)*100:.0f}%)")

print()

# By time window
print("=== VWAP alignment by time window ===")
for time_range, times in [
    ("9:30-9:45", ['9:30', '9:35', '9:40', '9:45']),
    ("9:30-9:40", ['9:30', '9:35', '9:40']),
    ("9:35 only", ['9:35']),
    ("9:40 only", ['9:40']),
    ("9:45 only", ['9:45']),
]:
    sub = amr[amr['time'].isin(times)]
    if len(sub) == 0: continue
    for vwap_val in [True, False]:
        vsub = sub[sub['vwap_match'] == vwap_val]
        if len(vsub) == 0: continue
        label = 'VWAP-aligned' if vwap_val else 'VWAP-counter'
        good = vsub['is_good'].sum()
        print(f"  {time_range} + {label}: {good}/{len(vsub)} ({good/len(vsub)*100:.0f}%)")
    print()

# By symbol
print("=== VWAP-counter quality by symbol ===")
for sym in sorted(amr['symbol'].unique()):
    sub = amr[(amr['symbol'] == sym) & (~amr['vwap_match'])]
    if len(sub) == 0: continue
    good = sub['is_good'].sum()
    print(f"  {sym}: {good}/{len(sub)} ({good/len(sub)*100:.0f}%)")

print()
print("=== VWAP-aligned quality by symbol ===")
for sym in sorted(amr['symbol'].unique()):
    sub = amr[(amr['symbol'] == sym) & (amr['vwap_match'])]
    if len(sub) == 0: continue
    good = sub['is_good'].sum()
    print(f"  {sym}: {good}/{len(sub)} ({good/len(sub)*100:.0f}%)")

print()

# Check if this is actually useful for TRADE QUALITY (not just CONF)
trades = pd.read_csv('debug/v28a-trades.csv')
tr_mc = trades[trades['conf_source'].str.contains('MC', na=False)].copy()

# Join trades with MC signal data
# Trades have signal_time; find matching MC signal
tr_mc['signal_dt'] = pd.to_datetime(tr_mc['signal_time'], utc=True)
tr_mc['tr_date'] = tr_mc['signal_dt'].dt.date.astype(str)

trade_results = []
for _, tr in tr_mc.iterrows():
    mc_match = mc[(mc['symbol'] == tr['symbol']) & (mc['date'] == tr['tr_date']) &
                  (mc['direction'] == tr['direction'])]
    if len(mc_match) > 0:
        m = mc_match.iloc[0]
        vwap_match = dir_matches_vwap(tr['direction'], m['vwap'])
        trade_results.append({
            'pnl_atr': tr['pnl_atr'],
            'mfe_atr': tr['mfe_atr'],
            'vwap_match': vwap_match,
            'time': tr['time'],
            'win': tr['pnl_atr'] > 0,
        })

trd = pd.DataFrame(trade_results)
print("=== MC TRADE performance by VWAP alignment ===")
for vwap_val in [True, False]:
    sub = trd[trd['vwap_match'] == vwap_val]
    label = 'VWAP-aligned' if vwap_val else 'VWAP-counter'
    print(f"  {label}: n={len(sub)}, win={sub['win'].mean()*100:.0f}%, mean_pnl={sub['pnl_atr'].mean():.3f}, mean_mfe={sub['mfe_atr'].mean():.3f}")

print()

# By time + VWAP
def time_to_min(t):
    h, m = t.split(':')
    return int(h) * 60 + int(m)

trd['t_min'] = trd['time'].apply(time_to_min)
for period, min_t, max_t in [
    ("Before 9:50", 0, time_to_min('9:50')),
    ("9:50+", time_to_min('9:50'), 999),
]:
    sub = trd[(trd['t_min'] >= min_t) & (trd['t_min'] < max_t)]
    for vwap_val in [True, False]:
        vsub = sub[sub['vwap_match'] == vwap_val]
        if len(vsub) == 0: continue
        label = 'VWAP-aligned' if vwap_val else 'VWAP-counter'
        print(f"  {period} + {label}: n={len(vsub)}, win={vsub['win'].mean()*100:.0f}%, mean_pnl={vsub['pnl_atr'].mean():.3f}")
    print()

# The killer question: is VWAP-counter + before 9:50 actually profitable?
print("=== THE KEY QUESTION: Can VWAP-counter MC trades before 9:50 be profitable? ===")
early_counter = trd[(trd['t_min'] < time_to_min('9:50')) & (~trd['vwap_match'])]
early_aligned = trd[(trd['t_min'] < time_to_min('9:50')) & (trd['vwap_match'])]

if len(early_counter) > 0:
    print(f"Early counter-VWAP: n={len(early_counter)}")
    print(f"  Win rate: {early_counter['win'].mean()*100:.0f}%")
    print(f"  Mean PnL/ATR: {early_counter['pnl_atr'].mean():.4f}")
    print(f"  Mean MFE/ATR: {early_counter['mfe_atr'].mean():.4f}")

if len(early_aligned) > 0:
    print(f"Early VWAP-aligned: n={len(early_aligned)}")
    print(f"  Win rate: {early_aligned['win'].mean()*100:.0f}%")
    print(f"  Mean PnL/ATR: {early_aligned['pnl_atr'].mean():.4f}")
    print(f"  Mean MFE/ATR: {early_aligned['mfe_atr'].mean():.4f}")
