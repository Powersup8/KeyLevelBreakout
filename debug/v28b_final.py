#!/usr/bin/env python3
"""Final MC smart filter analysis: delay strategy and solo MC check."""
import pandas as pd

signals = pd.read_csv('debug/v28a-signals.csv')
pairs = pd.read_csv('debug/v28a-mc-opposing-pairs.csv')
mc = signals[signals['line_type'] == 'MC'].copy()
mc['dt'] = pd.to_datetime(mc['datetime'], utc=True)
mc['date'] = mc['dt'].dt.date.astype(str)

enriched = []
for _, p in pairs.iterrows():
    sym, date = p['symbol'], p['date']
    day_mc = mc[(mc['symbol'] == sym) & (mc['date'] == date)]
    first_mc = day_mc[(day_mc['direction'] == p['first_dir']) & (day_mc['time'] == p['first_time'])]
    second_mc = day_mc[(day_mc['direction'] == p['second_dir']) & (day_mc['time'] == p['second_time'])]
    if len(first_mc) == 0 or len(second_mc) == 0: continue
    f, s = first_mc.iloc[0], second_mc.iloc[0]
    enriched.append({
        'first_correct': p['first_correct'], 'second_correct': p['second_correct'],
        'first_dir': p['first_dir'], 'second_dir': p['second_dir'],
        'first_time': p['first_time'], 'second_time': p['second_time'],
        'first_vwap': f['vwap'], 'second_vwap': s['vwap'],
        'first_ema': f['ema'], 'second_ema': s['ema'],
        'first_vol': f['vol'], 'second_vol': s['vol'],
        'first_ramp': f['ramp'], 'second_ramp': s['ramp'],
        'first_body': f['body'], 'second_body': s['body'],
        'first_adx': f['adx'], 'second_adx': s['adx'],
        'first_close_pos': f['close_pos'], 'second_close_pos': s['close_pos'],
        'first_range_atr': f['range_atr'], 'second_range_atr': s['range_atr'],
        'actual_dir': p['actual_dir'], 'move_30m': p['move_30m'],
        'symbol': sym, 'date': date,
    })
df = pd.DataFrame(enriched)

def dir_matches_vwap(d, v):
    return (d == 'bull' and v == 'above') or (d == 'bear' and v == 'below')

def time_to_min(t):
    h, m = t.split(':')
    return int(h) * 60 + int(m)

print("=== DELAY STRATEGY: Wait, then compare ===")
correct = 0
for _, row in df.iterrows():
    f_m = dir_matches_vwap(row['first_dir'], row['first_vwap'])
    s_m = dir_matches_vwap(row['second_dir'], row['second_vwap'])
    if f_m and not s_m:
        if row['second_correct']: correct += 1
    elif s_m and not f_m:
        if row['first_correct']: correct += 1
    else:
        s1, s2 = 0, 0
        if row['first_vol'] < row['second_vol']: s1 += 1
        else: s2 += 1
        if row['first_body'] > row['second_body']: s1 += 1
        else: s2 += 1
        if row['first_close_pos'] < row['second_close_pos']: s1 += 1
        else: s2 += 1
        if s1 > s2:
            if row['first_correct']: correct += 1
        else:
            if row['second_correct']: correct += 1
print(f"Counter-VWAP + multi-score: {correct}/126 ({correct/126*100:.1f}%)")

# Solo MC VWAP analysis
conf_mc_df = signals[(signals['line_type'] == 'CONF') & (signals['conf_source'] == 'QBS/MC')].copy()
conf_mc_df['dt'] = pd.to_datetime(conf_mc_df['datetime'], utc=True)
conf_mc_df['date'] = conf_mc_df['dt'].dt.date.astype(str)

solo_data = []
all_mc_grouped = mc.groupby(['symbol', 'date'])
for (sym, date), grp in all_mc_grouped:
    dirs = grp['direction'].unique()
    if len(dirs) == 1:
        row = grp.iloc[0]
        solo_data.append({
            'symbol': sym, 'date': date,
            'direction': dirs[0], 'time': row['time'],
            'vwap': row['vwap'], 'ema': row['ema'],
            'vol': row['vol'], 'body': row['body'],
        })
solo = pd.DataFrame(solo_data)

solo_results = []
for _, s in solo.iterrows():
    day_conf = conf_mc_df[(conf_mc_df['symbol'] == s['symbol']) &
                          (conf_mc_df['date'] == s['date']) &
                          (conf_mc_df['direction'] == s['direction'])]
    if len(day_conf) > 0:
        conf = day_conf.iloc[0]['conf_result']
        vwap_match = dir_matches_vwap(s['direction'], s['vwap'])
        solo_results.append({'vwap_match': vwap_match, 'conf': conf,
                           'is_good': conf in ['star', 'pass']})

sr = pd.DataFrame(solo_results)
print("\n=== Solo MC: VWAP alignment vs CONF ===")
for vwap_val in [True, False]:
    sub = sr[sr['vwap_match'] == vwap_val]
    label = 'VWAP-aligned' if vwap_val else 'VWAP-counter'
    good = sub['is_good'].sum()
    print(f"  {label}: {good}/{len(sub)} good ({good/len(sub)*100:.0f}%)")
    print(f"    CONF: {sub['conf'].value_counts().to_dict()}")

# Implementation feasibility check
print("\n=== IMPLEMENTATION FEASIBILITY ===")
print("Pine Script state needed:")
print("  var float mc_bull_vol = na, mc_bull_body = na, mc_bull_cp = na")
print("  var float mc_bear_vol = na, mc_bear_body = na, mc_bear_cp = na")
print("  var string mc_bull_vwap = na, mc_bear_vwap = na")
print("  var bool mc_bull_fired = false, mc_bear_fired = false")
print()
print("When MC fires, store features. Don't emit signal yet.")
print("At 9:50 OR when second MC fires (whichever first):")
print("  If opposing pair: apply counter-VWAP + multi-score")
print("  If solo by 9:50: emit the stored MC signal")
print()
print("COMPLEXITY: ~30 lines of Pine Script")
print("BENEFIT: 64.3% accuracy vs 45% baseline (+19.3%)")
print("RISK: 64.3% vs 79% (9:50 gate) -- still 15% worse")
print("TRADEOFF: gains MC signal 5-15 min earlier on pair days")
print()

# What fraction of profitable MC trades happen before 9:50?
trades = pd.read_csv('debug/v28a-trades.csv')
tr_mc = trades[trades['conf_source'].str.contains('MC', na=False)].copy()
tr_mc['t_min'] = tr_mc['time'].apply(time_to_min)

early = tr_mc[tr_mc['t_min'] < time_to_min('9:50')]
late = tr_mc[tr_mc['t_min'] >= time_to_min('9:50')]

print("=== MC Trade Performance by Time ===")
print(f"Before 9:50: {len(early)} trades, win={early['pnl_atr'].gt(0).mean()*100:.0f}%, mean_pnl={early['pnl_atr'].mean():.3f}")
print(f"After 9:50:  {len(late)} trades, win={late['pnl_atr'].gt(0).mean()*100:.0f}%, mean_pnl={late['pnl_atr'].mean():.3f}")
print()

# The early trades have NEGATIVE expectancy!
# This means even with 64.3% direction accuracy, the early MC trades lose money.
# The 9:50 gate is not just about direction — it's about trade quality.

print("=== BOTTOM LINE ===")
print(f"Early MC trade expectancy: {early['pnl_atr'].mean():.3f} ATR (NEGATIVE)")
print(f"Late MC trade expectancy: {late['pnl_atr'].mean():.3f} ATR (positive)")
print()
print("Even if we perfectly predicted direction at the open,")
print("the WHIPSAW and slippage during 9:30-9:50 would hurt.")
print("The noise isn't just about direction — it's about FOLLOW-THROUGH.")
print("The 9:50 gate works because moves AFTER 9:50 have real momentum.")
