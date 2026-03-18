#!/usr/bin/env python3
"""
VWAP Counter-Trend BRK Analysis
Goal: Validate the n=36 finding (83% win, 1.154 MFE) with full dataset
"""
import pandas as pd
import numpy as np
from pathlib import Path

DEBUG = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug")

# ── Load signals ──
signals = pd.read_csv(DEBUG / "v28a-signals.csv")
signals['datetime'] = pd.to_datetime(signals['datetime'])

# ── Load follow-through (30m window only) ──
ft = pd.read_csv(DEBUG / "v28a-follow-through.csv")
ft['datetime'] = pd.to_datetime(ft['datetime'])
ft30 = ft[ft['window'] == 30].copy()

print(f"Total signals: {len(signals)}")
print(f"Follow-through rows (30m): {len(ft30)}")

# ── BRK signals only ──
brk = signals[signals['line_type'] == 'BRK'].copy()
print(f"\nBRK signals: {len(brk)}")

# ── Define VWAP alignment ──
# Aligned: bull+above OR bear+below
# Counter: bull+below OR bear+above
def vwap_align(row):
    if pd.isna(row['vwap']) or row['vwap'] == '':
        return 'unknown'
    if row['direction'] == 'bull':
        return 'aligned' if row['vwap'] == 'above' else 'counter'
    else:  # bear
        return 'aligned' if row['vwap'] == 'below' else 'counter'

brk['vwap_align'] = brk.apply(vwap_align, axis=1)
print(f"\nVWAP alignment distribution:")
print(brk['vwap_align'].value_counts())

# ── Merge with follow-through ──
merged = brk.merge(ft30, on=['symbol', 'datetime', 'direction'], how='inner', suffixes=('', '_ft'))
print(f"\nMerged BRK+FT30: {len(merged)}")

# ── Core comparison ──
print("\n" + "="*60)
print("VWAP ALIGNMENT vs COUNTER — 30m Follow-Through")
print("="*60)

for align in ['aligned', 'counter', 'unknown']:
    sub = merged[merged['vwap_align'] == align]
    if len(sub) == 0:
        continue
    win = (sub['mfe'] > sub['mae']).mean() * 100
    print(f"\n{align.upper()} (n={len(sub)}):")
    print(f"  MFE: {sub['mfe'].mean():.3f}  MAE: {sub['mae'].mean():.3f}  Ratio: {sub['mfe'].mean()/sub['mae'].mean():.2f}")
    print(f"  Win%: {win:.1f}%")
    print(f"  Median MFE: {sub['mfe'].median():.3f}  Median MAE: {sub['mae'].median():.3f}")

# ── Counter-trend detail ──
counter = merged[merged['vwap_align'] == 'counter'].copy()
print(f"\n{'='*60}")
print(f"COUNTER-TREND BRK DETAIL (n={len(counter)})")
print("="*60)

if len(counter) > 0:
    # By symbol
    print("\nBy Symbol:")
    for sym in sorted(counter['symbol'].unique()):
        sub = counter[counter['symbol'] == sym]
        win = (sub['mfe'] > sub['mae']).mean() * 100
        print(f"  {sym}: n={len(sub)}, MFE={sub['mfe'].mean():.3f}, Win={win:.0f}%")

    # By hour — use 'time' column (string like "9:45")
    counter['hour'] = counter['time'].astype(str).str.split(':').str[0].astype(int)
    print("\nBy Hour:")
    for h in sorted(counter['hour'].unique()):
        sub = counter[counter['hour'] == h]
        win = (sub['mfe'] > sub['mae']).mean() * 100
        print(f"  {h}:xx: n={len(sub)}, MFE={sub['mfe'].mean():.3f}, Win={win:.0f}%")

    # By direction
    print("\nBy Direction:")
    for d in ['bull', 'bear']:
        sub = counter[counter['direction'] == d]
        if len(sub) == 0:
            continue
        win = (sub['mfe'] > sub['mae']).mean() * 100
        print(f"  {d}: n={len(sub)}, MFE={sub['mfe'].mean():.3f}, Win={win:.0f}%")

    # By big-move flag
    print("\nBy Big-Move Flag:")
    for bm in [True, False]:
        sub = counter[counter['is_bigmove'] == bm]
        if len(sub) == 0:
            continue
        label = "⚡ Big-move" if bm else "Normal"
        win = (sub['mfe'] > sub['mae']).mean() * 100
        print(f"  {label}: n={len(sub)}, MFE={sub['mfe'].mean():.3f}, Win={win:.0f}%")

    # By volume bucket
    print("\nBy Volume:")
    bins = [0, 2, 5, 10, 999]
    labels = ['<2x', '2-5x', '5-10x', '10x+']
    counter['vol_bucket'] = pd.cut(counter['vol'], bins=bins, labels=labels)
    for vb in labels:
        sub = counter[counter['vol_bucket'] == vb]
        if len(sub) == 0:
            continue
        win = (sub['mfe'] > sub['mae']).mean() * 100
        print(f"  {vb}: n={len(sub)}, MFE={sub['mfe'].mean():.3f}, Win={win:.0f}%")

    # List all counter signals
    print(f"\n{'='*60}")
    print("ALL COUNTER-TREND BRK SIGNALS")
    print("="*60)
    cols = ['symbol', 'datetime', 'direction', 'vwap', 'levels', 'vol', 'close_pos',
            'ema', 'body', 'range_atr', 'is_bigmove', 'mfe', 'mae']
    available_cols = [c for c in cols if c in counter.columns]
    counter_sorted = counter.sort_values('datetime')
    for _, row in counter_sorted.iterrows():
        win = "WIN" if row['mfe'] > row['mae'] else "LOSS"
        dt = row['datetime'].strftime('%Y-%m-%d %H:%M')
        bm = "⚡" if row.get('is_bigmove', False) else ""
        levels = row.get('levels', '')
        print(f"  {dt} {row['symbol']:5s} {row['direction']:4s} vwap={row['vwap']} "
              f"vol={row.get('vol', '?')}x ema={row.get('ema', '?')} "
              f"MFE={row['mfe']:.3f} MAE={row['mae']:.3f} {win} {bm} {levels}")

# ── Also check REV signals with VWAP alignment ──
print(f"\n{'='*60}")
print("BONUS: ALL SIGNAL TYPES — VWAP Counter vs Aligned")
print("="*60)

for stype in ['BRK', 'REV', 'VWAP']:
    type_sigs = signals[signals['line_type'] == stype].copy()
    type_sigs['vwap_align'] = type_sigs.apply(vwap_align, axis=1)
    type_merged = type_sigs.merge(ft30, on=['symbol', 'datetime', 'direction'], how='inner', suffixes=('', '_ft'))

    print(f"\n{stype}:")
    for align in ['aligned', 'counter']:
        sub = type_merged[type_merged['vwap_align'] == align]
        if len(sub) == 0:
            continue
        win = (sub['mfe'] > sub['mae']).mean() * 100
        print(f"  {align:8s}: n={len(sub):4d}, MFE={sub['mfe'].mean():.3f}, MAE={sub['mae'].mean():.3f}, Win={win:.1f}%")

# ── Extended: check v28 (older, possibly larger dataset) ──
print(f"\n{'='*60}")
print("CHECKING OLDER v28 DATASET FOR MORE DATA")
print("="*60)

v28_ft_path = DEBUG / "v28-follow-through.csv"
v28_sig_path = DEBUG / "v28-signals-parsed.csv"

if v28_ft_path.exists() and v28_sig_path.exists():
    v28_sigs = pd.read_csv(v28_sig_path)
    v28_ft = pd.read_csv(v28_ft_path)
    v28_ft['datetime'] = pd.to_datetime(v28_ft['datetime'])
    print(f"v28 signals: {len(v28_sigs)}")
    print(f"v28 follow-through: {len(v28_ft)}")

    # Check columns
    print(f"v28 signal columns: {list(v28_sigs.columns[:10])}")
    print(f"v28 FT columns: {list(v28_ft.columns[:10])}")

    if 'vwap' in v28_sigs.columns and 'line_type' in v28_sigs.columns:
        v28_brk = v28_sigs[v28_sigs['line_type'] == 'BRK'].copy()
        v28_brk['datetime'] = pd.to_datetime(v28_brk['datetime'])
        v28_brk['vwap_align'] = v28_brk.apply(vwap_align, axis=1)
        print(f"\nv28 BRK VWAP alignment:")
        print(v28_brk['vwap_align'].value_counts())

        v28_ft30 = v28_ft[v28_ft['window'] == 30]
        v28_merged = v28_brk.merge(v28_ft30, on=['symbol', 'datetime', 'direction'], how='inner', suffixes=('', '_ft'))

        for align in ['aligned', 'counter']:
            sub = v28_merged[v28_merged['vwap_align'] == align]
            if len(sub) == 0:
                continue
            win = (sub['mfe'] > sub['mae']).mean() * 100
            print(f"  {align:8s}: n={len(sub):4d}, MFE={sub['mfe'].mean():.3f}, MAE={sub['mae'].mean():.3f}, Win={win:.1f}%")
else:
    print("v28 files not found")

# ── Also check enriched-signals.csv ──
enriched_path = DEBUG / "enriched-signals.csv"
if enriched_path.exists():
    print(f"\n{'='*60}")
    print("ENRICHED SIGNALS DATASET")
    print("="*60)
    enriched = pd.read_csv(enriched_path)
    print(f"Rows: {len(enriched)}")
    print(f"Columns: {list(enriched.columns)}")
    print(f"Date range: {enriched['date'].min()} to {enriched['date'].max()}")

    if 'vwap' in enriched.columns and 'type' in enriched.columns:
        e_brk = enriched[enriched['type'] == 'BRK'].copy()
        e_brk['vwap_align'] = e_brk.apply(lambda r:
            'counter' if (r['direction'] == 'bull' and r['vwap'] == 'below') or
                         (r['direction'] == 'bear' and r['vwap'] == 'above')
            else 'aligned' if pd.notna(r['vwap']) and r['vwap'] != ''
            else 'unknown', axis=1)

        print(f"\nEnriched BRK VWAP alignment:")
        print(e_brk['vwap_align'].value_counts())

        if 'mfe' in enriched.columns:
            for align in ['aligned', 'counter']:
                sub = e_brk[e_brk['vwap_align'] == align]
                if len(sub) == 0:
                    continue
                win = (sub['mfe'] > sub['mae']).mean() * 100
                print(f"  {align:8s}: n={len(sub):4d}, MFE={sub['mfe'].mean():.3f}, MAE={sub['mae'].mean():.3f}, Win={win:.1f}%")

# ── Also check big-moves.csv ──
bm_path = DEBUG / "big-moves.csv"
if bm_path.exists():
    print(f"\n{'='*60}")
    print("BIG-MOVES DATASET")
    print("="*60)
    bm = pd.read_csv(bm_path)
    print(f"Rows: {len(bm)}")
    print(f"Symbols: {bm['symbol'].unique() if 'symbol' in bm.columns else 'N/A'}")
    print(f"Date range: {bm['date'].min() if 'date' in bm.columns else 'N/A'} to {bm['date'].max() if 'date' in bm.columns else 'N/A'}")

    if 'vwap_aligned' in bm.columns and 'mfe' in bm.columns:
        print(f"\nVWAP alignment in big-moves:")
        for va in bm['vwap_aligned'].unique():
            sub = bm[bm['vwap_aligned'] == va]
            print(f"  vwap_aligned={va}: n={len(sub)}, MFE={sub['mfe'].mean():.3f}, MAE={sub['mae'].mean():.3f}")
