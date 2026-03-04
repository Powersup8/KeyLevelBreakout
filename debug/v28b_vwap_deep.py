#!/usr/bin/env python3
"""Deep dive into VWAP counter-trend filter for MC signals."""
import pandas as pd
import numpy as np

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
    if len(first_mc) == 0 or len(second_mc) == 0:
        continue
    f, s = first_mc.iloc[0], second_mc.iloc[0]
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
        'symbol': sym, 'date': date,
    })
df = pd.DataFrame(enriched)

def dir_matches_vwap(d, v):
    return (d == 'bull' and v == 'above') or (d == 'bear' and v == 'below')

# VWAP same vs different
vwap_same = df[df['first_vwap'] == df['second_vwap']]
vwap_diff = df[df['first_vwap'] != df['second_vwap']]
print(f"VWAP same on both signals: {len(vwap_same)}/126")
print(f"VWAP changed between signals: {len(vwap_diff)}/126")
print()

# Same VWAP analysis
with_vwap_correct = 0
counter_vwap_correct = 0
for _, row in vwap_same.iterrows():
    f_m = dir_matches_vwap(row['first_dir'], row['first_vwap'])
    if f_m:
        if row['second_correct']: counter_vwap_correct += 1
        if row['first_correct']: with_vwap_correct += 1
    else:
        if row['first_correct']: counter_vwap_correct += 1
        if row['second_correct']: with_vwap_correct += 1

print(f"=== Same VWAP (n={len(vwap_same)}) ===")
print(f"Counter-VWAP correct: {counter_vwap_correct}/{len(vwap_same)} ({counter_vwap_correct/len(vwap_same)*100:.0f}%)")
print(f"With-VWAP correct: {with_vwap_correct}/{len(vwap_same)} ({with_vwap_correct/len(vwap_same)*100:.0f}%)")
print()

# Check who matches VWAP when VWAP is same
first_matches = 0
for _, row in vwap_same.iterrows():
    if dir_matches_vwap(row['first_dir'], row['first_vwap']):
        first_matches += 1
print(f"First MC matches VWAP: {first_matches}/{len(vwap_same)} ({first_matches/len(vwap_same)*100:.0f}%)")
print()

# Different VWAP analysis
if len(vwap_diff) > 0:
    both_match = 0
    neither_match = 0
    for _, row in vwap_diff.iterrows():
        f_m = dir_matches_vwap(row['first_dir'], row['first_vwap'])
        s_m = dir_matches_vwap(row['second_dir'], row['second_vwap'])
        if f_m and s_m: both_match += 1
        if not f_m and not s_m: neither_match += 1
    second_right = vwap_diff['second_correct'].sum()
    print(f"=== Different VWAP (n={len(vwap_diff)}) ===")
    print(f"Both match their VWAP: {both_match}")
    print(f"Neither matches their VWAP: {neither_match}")
    print(f"Second correct: {second_right}/{len(vwap_diff)}")
    print()

# Now the KEY question: the original filter had n=52 exclusive cases
# The exclusive filter is: first matches VWAP XOR second matches VWAP
# When VWAP is same AND directions are opposite, exactly one matches
# So the exclusive filter should be = same VWAP cases
# But wait, the filter found n=52 not all same-VWAP cases
# Let me recheck the filter logic

print("=== Recheck exclusive VWAP filter ===")
exclusive_first = 0
exclusive_second = 0
both_match_count = 0
neither_match_count = 0

for _, row in df.iterrows():
    f_m = dir_matches_vwap(row['first_dir'], row['first_vwap'])
    s_m = dir_matches_vwap(row['second_dir'], row['second_vwap'])
    if f_m and not s_m:
        exclusive_first += 1
    elif s_m and not f_m:
        exclusive_second += 1
    elif f_m and s_m:
        both_match_count += 1
    else:
        neither_match_count += 1

print(f"First matches VWAP exclusively: {exclusive_first}")
print(f"Second matches VWAP exclusively: {exclusive_second}")
print(f"Both match VWAP: {both_match_count}")
print(f"Neither matches VWAP: {neither_match_count}")
print(f"Exclusive total: {exclusive_first + exclusive_second} (this is the n=52)")
print()

# So the counter-VWAP filter only works when exactly one MC matches VWAP
# The other 74 cases (both or neither) are undecided
# Let's see how those 74 break down

print("=== Both-match cases ===")
both_rows = []
neither_rows = []
for _, row in df.iterrows():
    f_m = dir_matches_vwap(row['first_dir'], row['first_vwap'])
    s_m = dir_matches_vwap(row['second_dir'], row['second_vwap'])
    if f_m and s_m:
        both_rows.append(row)
    elif not f_m and not s_m:
        neither_rows.append(row)

if both_rows:
    br = pd.DataFrame(both_rows)
    print(f"Both match VWAP: n={len(br)}")
    print(f"  First correct: {br['first_correct'].sum()}")
    print(f"  Second correct: {br['second_correct'].sum()}")
    # This means VWAP flipped between signals - price crossed VWAP
    print(f"  VWAP flipped: first={br['first_vwap'].value_counts().to_dict()}, second={br['second_vwap'].value_counts().to_dict()}")

if neither_rows:
    nr = pd.DataFrame(neither_rows)
    print(f"Neither matches VWAP: n={len(nr)}")
    print(f"  First correct: {nr['first_correct'].sum()}")
    print(f"  Second correct: {nr['second_correct'].sum()}")
    print(f"  VWAP: first={nr['first_vwap'].value_counts().to_dict()}, second={nr['second_vwap'].value_counts().to_dict()}")

print()

# Now let's try composite strategies for the undecided cases
print("=== Composite Strategy: Counter-VWAP + fallback ===")
# For the 52 exclusive cases: use counter-VWAP (61.5%)
# For the 74 undecided: try various fallbacks

# Fallback: pick lower volume
# Fallback: pick second
# Fallback: pick higher body%

for fallback_name, fallback_pick_first in [
    ("pick second", pd.Series([False] * len(df))),
    ("pick lower vol", df['first_vol'] < df['second_vol']),
    ("pick higher body", df['first_body'] > df['second_body']),
    ("pick lower close_pos", df['first_close_pos'] < df['second_close_pos']),
    ("pick higher ADX", df['first_adx'] > df['second_adx']),
]:
    correct = 0
    total = len(df)
    for i, (_, row) in enumerate(df.iterrows()):
        f_m = dir_matches_vwap(row['first_dir'], row['first_vwap'])
        s_m = dir_matches_vwap(row['second_dir'], row['second_vwap'])

        if f_m and not s_m:
            # Counter-VWAP = pick second
            if row['second_correct']: correct += 1
        elif s_m and not f_m:
            # Counter-VWAP = pick first
            if row['first_correct']: correct += 1
        else:
            # Undecided: use fallback
            if fallback_pick_first.iloc[i]:
                if row['first_correct']: correct += 1
            else:
                if row['second_correct']: correct += 1

    print(f"Counter-VWAP + fallback({fallback_name}): {correct}/{total} ({correct/total*100:.1f}%)")

print()

# Try a 3-level strategy
# Level 1: Counter-VWAP (52 cases)
# Level 2: For undecided, use lower volume
# Level 3: For undecided volume ties, pick second
print("=== Multi-level strategy ===")
correct = 0
for _, row in df.iterrows():
    f_m = dir_matches_vwap(row['first_dir'], row['first_vwap'])
    s_m = dir_matches_vwap(row['second_dir'], row['second_vwap'])

    if f_m and not s_m:
        if row['second_correct']: correct += 1
    elif s_m and not f_m:
        if row['first_correct']: correct += 1
    else:
        # Fallback: lower volume + higher body
        score_first = 0
        score_second = 0
        if row['first_vol'] < row['second_vol']: score_first += 1
        else: score_second += 1
        if row['first_body'] > row['second_body']: score_first += 1
        else: score_second += 1
        if row['first_close_pos'] < row['second_close_pos']: score_first += 1
        else: score_second += 1

        if score_first > score_second:
            if row['first_correct']: correct += 1
        else:
            if row['second_correct']: correct += 1

print(f"Counter-VWAP + multi-score fallback: {correct}/126 ({correct/126*100:.1f}%)")

# What if we DON'T TAKE any MC when VWAP is ambiguous?
# Only fire MC when counter-VWAP is clear
print(f"\n=== Selective Strategy: Only fire MC when counter-VWAP clear ===")
print(f"n=52, accuracy=61.5%, skip 74 undecided pairs")
print(f"This saves the MC slot for 74/126=59% of opposing-pair days")
print(f"Combined with solo MC days: those 531 solo MCs are unaffected")
