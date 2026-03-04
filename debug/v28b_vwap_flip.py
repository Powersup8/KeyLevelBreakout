#!/usr/bin/env python3
"""
Deeper analysis of the 70 pairs where VWAP flipped between first and second MC.
These are the cases where both MCs align with their respective VWAP reading.
"""
import pandas as pd
import numpy as np

signals = pd.read_csv('debug/v28a-signals.csv')
pairs = pd.read_csv('debug/v28a-mc-opposing-pairs.csv')
mc = signals[signals['line_type'] == 'MC'].copy()
mc['dt'] = pd.to_datetime(mc['datetime'], utc=True)
mc['date'] = mc['dt'].dt.date.astype(str)
conf_mc = signals[(signals['line_type'] == 'CONF') & (signals['conf_source'] == 'QBS/MC')].copy()
conf_mc['dt'] = pd.to_datetime(conf_mc['datetime'], utc=True)
conf_mc['date'] = conf_mc['dt'].dt.date.astype(str)

enriched = []
for _, p in pairs.iterrows():
    sym, date = p['symbol'], p['date']
    day_mc = mc[(mc['symbol'] == sym) & (mc['date'] == date)]
    first_mc = day_mc[(day_mc['direction'] == p['first_dir']) & (day_mc['time'] == p['first_time'])]
    second_mc = day_mc[(day_mc['direction'] == p['second_dir']) & (day_mc['time'] == p['second_time'])]
    if len(first_mc) == 0 or len(second_mc) == 0: continue
    f, s = first_mc.iloc[0], second_mc.iloc[0]

    day_conf = conf_mc[(conf_mc['symbol'] == sym) & (conf_mc['date'] == date)]
    fc = day_conf[day_conf['direction'] == p['first_dir']]
    sc = day_conf[day_conf['direction'] == p['second_dir']]

    enriched.append({
        'first_correct': p['first_correct'], 'second_correct': p['second_correct'],
        'first_dir': p['first_dir'], 'second_dir': p['second_dir'],
        'first_vwap': f['vwap'], 'second_vwap': s['vwap'],
        'first_ema': f['ema'], 'second_ema': s['ema'],
        'first_vol': f['vol'], 'second_vol': s['vol'],
        'first_ramp': f['ramp'], 'second_ramp': s['ramp'],
        'first_body': f['body'], 'second_body': s['body'],
        'first_adx': f['adx'], 'second_adx': s['adx'],
        'first_close_pos': f['close_pos'], 'second_close_pos': s['close_pos'],
        'first_range_atr': f['range_atr'], 'second_range_atr': s['range_atr'],
        'first_conf': fc.iloc[0]['conf_result'] if len(fc) > 0 else 'none',
        'second_conf': sc.iloc[0]['conf_result'] if len(sc) > 0 else 'none',
        'symbol': sym, 'date': date, 'move_30m': p['move_30m'],
        'first_time': p['first_time'], 'second_time': p['second_time'],
    })
df = pd.DataFrame(enriched)

def dir_matches_vwap(d, v):
    return (d == 'bull' and v == 'above') or (d == 'bear' and v == 'below')

# Filter to VWAP-flipped cases (both match their VWAP)
vwap_flipped = []
for _, row in df.iterrows():
    f_m = dir_matches_vwap(row['first_dir'], row['first_vwap'])
    s_m = dir_matches_vwap(row['second_dir'], row['second_vwap'])
    if f_m and s_m:
        vwap_flipped.append(row)

vf = pd.DataFrame(vwap_flipped)
print(f"=== VWAP-flipped pairs: {len(vf)} ===")
print(f"First correct: {vf['first_correct'].sum()}/{len(vf)} ({vf['first_correct'].mean()*100:.0f}%)")
print(f"Second correct: {vf['second_correct'].sum()}/{len(vf)} ({vf['second_correct'].mean()*100:.0f}%)")
print()

# In these cases, VWAP itself can't help (both MCs are "with VWAP" at their bar)
# What about other features?

print("=== Feature tests on VWAP-flipped cases ===")

def test_feature(vf, name, pick_first_mask):
    pick_second_mask = ~pick_first_mask
    n = len(vf)
    correct = ((pick_first_mask & vf['first_correct']) | (pick_second_mask & vf['second_correct'])).sum()
    acc = correct / n * 100
    print(f"  {name}: {correct}/{n} ({acc:.0f}%) {'***' if acc >= 60 else ''}")
    return acc

# Lower volume
test_feature(vf, "Pick lower vol", vf['first_vol'] < vf['second_vol'])
test_feature(vf, "Pick higher vol", vf['first_vol'] > vf['second_vol'])

# Higher body
test_feature(vf, "Pick higher body%", vf['first_body'] > vf['second_body'])
test_feature(vf, "Pick lower body%", vf['first_body'] < vf['second_body'])

# Lower close_pos
test_feature(vf, "Pick lower close_pos", vf['first_close_pos'] < vf['second_close_pos'])
test_feature(vf, "Pick higher close_pos", vf['first_close_pos'] > vf['second_close_pos'])

# Higher ADX
test_feature(vf, "Pick higher ADX", vf['first_adx'] > vf['second_adx'])
test_feature(vf, "Pick lower ADX", vf['first_adx'] < vf['second_adx'])

# Higher ramp
test_feature(vf, "Pick higher ramp", vf['first_ramp'] > vf['second_ramp'])
test_feature(vf, "Pick lower ramp", vf['first_ramp'] < vf['second_ramp'])

# Range ATR
test_feature(vf, "Pick smaller bar", vf['first_range_atr'] < vf['second_range_atr'])
test_feature(vf, "Pick bigger bar", vf['first_range_atr'] > vf['second_range_atr'])

# EMA match
first_ema_match = ((vf['first_dir'] == 'bull') & (vf['first_ema'] == 'bull')) | ((vf['first_dir'] == 'bear') & (vf['first_ema'] == 'bear'))
second_ema_match = ((vf['second_dir'] == 'bull') & (vf['second_ema'] == 'bull')) | ((vf['second_dir'] == 'bear') & (vf['second_ema'] == 'bear'))
test_feature(vf, "Pick EMA match", first_ema_match)
test_feature(vf, "Pick EMA counter", ~first_ema_match)

# Always second
test_feature(vf, "Always second", pd.Series([False]*len(vf), index=vf.index))
test_feature(vf, "Always first", pd.Series([True]*len(vf), index=vf.index))

# CONF
first_conf_better = vf['first_conf'].isin(['star', 'pass']) & ~vf['second_conf'].isin(['star', 'pass'])
second_conf_better = vf['second_conf'].isin(['star', 'pass']) & ~vf['first_conf'].isin(['star', 'pass'])
exclusive_conf = first_conf_better | second_conf_better
if exclusive_conf.sum() > 0:
    sub = vf[exclusive_conf]
    correct = ((first_conf_better[exclusive_conf] & sub['first_correct']) | (second_conf_better[exclusive_conf] & sub['second_correct'])).sum()
    print(f"  Pick better CONF (exclusive): {correct}/{exclusive_conf.sum()} ({correct/exclusive_conf.sum()*100:.0f}%)")

print()

# The VWAP flip tells us price crossed VWAP between the two MC signals
# Direction of VWAP flip might matter
# If VWAP was 'above' -> 'below': price dropped below VWAP (bearish cross)
# If VWAP was 'below' -> 'above': price rose above VWAP (bullish cross)
print("=== VWAP flip direction ===")
vf_copy = vf.copy()
vf_copy['vwap_flip'] = vf_copy.apply(
    lambda r: 'above_to_below' if r['first_vwap'] == 'above' else 'below_to_above', axis=1)

for flip in ['above_to_below', 'below_to_above']:
    sub = vf_copy[vf_copy['vwap_flip'] == flip]
    first_right = sub['first_correct'].sum()
    second_right = sub['second_correct'].sum()
    print(f"  {flip}: n={len(sub)}, first={first_right}/{len(sub)} ({first_right/len(sub)*100:.0f}%), second={second_right}/{len(sub)} ({second_right/len(sub)*100:.0f}%)")

print()

# Key insight: when VWAP flips, does the SECOND MC (the one after the flip) tend to be correct?
# The second MC is the reversal that pushed price back through VWAP
# If the flip "sticks", second is correct. If it's just a VWAP whipsaw, first is correct.

# Let's look at the move_30m magnitude for flipped cases
print("=== Move magnitude in VWAP-flipped cases ===")
print(f"Mean |move_30m|: {vf['move_30m'].abs().mean():.2f}")
print(f"Mean move_30m when first correct: {vf[vf['first_correct']]['move_30m'].mean():.2f}")
print(f"Mean move_30m when second correct: {vf[vf['second_correct']]['move_30m'].mean():.2f}")
print()

# Now let's try MULTI-SCORE approach on VWAP-flipped cases
# Score each MC on multiple dimensions
print("=== Multi-score approaches on VWAP-flipped ===")
for combo_name, features in [
    ("vol+body+close", [('vol', 'lower'), ('body', 'higher'), ('close_pos', 'lower')]),
    ("vol+body", [('vol', 'lower'), ('body', 'higher')]),
    ("vol+ramp", [('vol', 'lower'), ('ramp', 'higher')]),
    ("vol+adx", [('vol', 'lower'), ('adx', 'higher')]),
    ("vol+body+adx", [('vol', 'lower'), ('body', 'higher'), ('adx', 'higher')]),
    ("body+adx+close", [('body', 'higher'), ('adx', 'higher'), ('close_pos', 'lower')]),
    ("all5", [('vol', 'lower'), ('body', 'higher'), ('close_pos', 'lower'), ('adx', 'higher'), ('ramp', 'higher')]),
]:
    correct = 0
    for _, row in vf.iterrows():
        score_first = 0
        score_second = 0
        for feat, direction in features:
            if direction == 'lower':
                if row[f'first_{feat}'] < row[f'second_{feat}']: score_first += 1
                else: score_second += 1
            else:
                if row[f'first_{feat}'] > row[f'second_{feat}']: score_first += 1
                else: score_second += 1
        if score_first > score_second:
            if row['first_correct']: correct += 1
        else:
            if row['second_correct']: correct += 1
    print(f"  {combo_name}: {correct}/{len(vf)} ({correct/len(vf)*100:.0f}%)")

print()

# Finally: comprehensive strategy combining counter-VWAP + best fallback
print("=== FINAL COMPOSITE STRATEGIES ===")

def compute_composite(df, fallback_fn, name):
    correct = 0
    for _, row in df.iterrows():
        f_m = dir_matches_vwap(row['first_dir'], row['first_vwap'])
        s_m = dir_matches_vwap(row['second_dir'], row['second_vwap'])

        if f_m and not s_m:
            # Only first matches VWAP -> counter = pick second
            if row['second_correct']: correct += 1
        elif s_m and not f_m:
            # Only second matches VWAP -> counter = pick first
            if row['first_correct']: correct += 1
        elif not f_m and not s_m:
            # Neither matches -> fallback
            pick = fallback_fn(row)
            if pick == 'first' and row['first_correct']: correct += 1
            elif pick == 'second' and row['second_correct']: correct += 1
        else:
            # Both match (VWAP flipped) -> fallback
            pick = fallback_fn(row)
            if pick == 'first' and row['first_correct']: correct += 1
            elif pick == 'second' and row['second_correct']: correct += 1

    print(f"  {name}: {correct}/{len(df)} ({correct/len(df)*100:.1f}%)")
    return correct

# Best multi-score from above
def multi_score_vol_body_close(row):
    s1, s2 = 0, 0
    if row['first_vol'] < row['second_vol']: s1 += 1
    else: s2 += 1
    if row['first_body'] > row['second_body']: s1 += 1
    else: s2 += 1
    if row['first_close_pos'] < row['second_close_pos']: s1 += 1
    else: s2 += 1
    return 'first' if s1 > s2 else 'second'

def multi_score_all5(row):
    s1, s2 = 0, 0
    if row['first_vol'] < row['second_vol']: s1 += 1
    else: s2 += 1
    if row['first_body'] > row['second_body']: s1 += 1
    else: s2 += 1
    if row['first_close_pos'] < row['second_close_pos']: s1 += 1
    else: s2 += 1
    if row['first_adx'] > row['second_adx']: s1 += 1
    else: s2 += 1
    if row['first_ramp'] > row['second_ramp']: s1 += 1
    else: s2 += 1
    return 'first' if s1 > s2 else 'second'

def pick_second(row):
    return 'second'

def pick_lower_vol(row):
    return 'first' if row['first_vol'] < row['second_vol'] else 'second'

compute_composite(df, pick_second, "Counter-VWAP + always second")
compute_composite(df, pick_lower_vol, "Counter-VWAP + lower vol")
compute_composite(df, multi_score_vol_body_close, "Counter-VWAP + score(vol+body+close)")
compute_composite(df, multi_score_all5, "Counter-VWAP + score(all5)")

# What about: suppress MC entirely at open on VWAP-flipped days?
# i.e., only allow MC when VWAP is clear (one side)
print()
print("=== Strategy: Suppress MC when VWAP is ambiguous ===")
print(f"Clear VWAP (exclusive): 52/126 pairs, accuracy 61.5%")
print(f"Ambiguous (VWAP flipped): 74/126 pairs, suppress")
print(f"Net: take 52 signals at 61.5% accuracy, skip 74 noisy ones")
print(f"BUT: 74/126 = 59% of pairs get NO MC at open")
print()

# What about the 531 solo MC days? Those are unambiguous
# How does the strategy work on total MC days?
print("=== Total MC day coverage ===")
print(f"Solo MC days: 531 (keep all, no opposing pair)")
print(f"Opposing pair days with clear VWAP: 52 (take counter-VWAP, 61.5%)")
print(f"Opposing pair days with flipped VWAP: 74 (suppressed)")
print(f"Total MC days served: 583/657 ({583/657*100:.0f}%)")
print(f"MC days suppressed: 74/657 ({74/657*100:.0f}%)")
print()

# But wait - on 74 suppressed days, the MC is currently burning a slot on noise
# So suppressing IS the benefit: the once-per-session slot is preserved for later use
print("=== Comparison with 9:50 time gate ===")
print(f"9:50 gate: suppresses ALL 126 opposing pair days (100%)")
print(f"  -> waits until 9:50, then 79% accuracy on direction")
print(f"Smart filter: suppresses 74 ambiguous days (59%), takes 52 clear days")
print(f"  -> clear days: 61.5% accuracy at 9:35-9:45")
print(f"  -> ambiguous days: could still use 9:50 gate as fallback")
print()

# HYBRID: Counter-VWAP at open for clear cases, 9:50 gate for ambiguous
print("=== HYBRID Strategy ===")
print(f"1. At open (9:30-9:45): if only ONE MC matches VWAP, take the counter-VWAP MC")
print(f"   Coverage: 52/126 opposing pairs at 61.5%")
print(f"2. For ambiguous cases: wait until 9:50 (existing gate)")
print(f"   Coverage: 74/126 opposing pairs at ~79%")
print(f"3. Solo MC days: no change")
print(f"Expected weighted accuracy: {(52*0.615 + 74*0.79) / 126 * 100:.1f}%")
