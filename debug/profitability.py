#!/usr/bin/env python3
"""Profitability analysis: how far do GOOD signals run? Expected value per signal."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from v24_gap_analysis import (load_pine_logs, load_candles, compute_excursions,
                               classify_signal, time_bucket, ALL_SYMBOLS)
import numpy as np

def main():
    print("Loading pine logs...")
    signals, confs = load_pine_logs()
    print(f"  {len(signals)} signals")

    print("Loading candle data...")
    candles_cache = {}
    bar_secs_cache = {}
    for sym in ALL_SYMBOLS:
        df, bsecs = load_candles(sym)
        if df is not None and len(df) > 0:
            candles_cache[sym] = df
            bar_secs_cache[sym] = bsecs

    # Compute excursions for all signals
    print("Computing excursions (this takes a minute)...")
    results = []  # list of dicts with signal info + excursion data
    for s in signals:
        sym = s['symbol']
        if sym not in candles_cache:
            continue
        bsecs = bar_secs_cache.get(sym, 5)
        exc = compute_excursions(s, candles_cache[sym], bsecs)
        if exc.get('30m') is None:
            continue
        cls = classify_signal(exc, s['atr'])
        results.append({
            'type': s['type'],
            'direction': s['direction'],
            'levels': s.get('levels', ''),
            'vol': s.get('vol', 0),
            'conf': s.get('conf'),
            'conf_star': s.get('conf_star', False),
            'atr': s['atr'],
            'time_bucket': time_bucket(s['timestamp']),
            'symbol': sym,
            'cls': cls,
            # MFE at each window (ATR-normalized)
            'mfe_30s': exc['30s']['mfe_atr'] if exc.get('30s') else None,
            'mfe_1m':  exc['1m']['mfe_atr']  if exc.get('1m')  else None,
            'mfe_2m':  exc['2m']['mfe_atr']  if exc.get('2m')  else None,
            'mfe_5m':  exc['5m']['mfe_atr']  if exc.get('5m')  else None,
            'mfe_15m': exc['15m']['mfe_atr'] if exc.get('15m') else None,
            'mfe_30m': exc['30m']['mfe_atr'] if exc.get('30m') else None,
            # MAE at each window
            'mae_5m':  exc['5m']['mae_atr']  if exc.get('5m')  else None,
            'mae_15m': exc['15m']['mae_atr'] if exc.get('15m') else None,
            'mae_30m': exc['30m']['mae_atr'] if exc.get('30m') else None,
        })

    good = [r for r in results if r['cls'] == 'GOOD']
    bad  = [r for r in results if r['cls'] == 'BAD']
    neut = [r for r in results if r['cls'] == 'NEUTRAL']
    print(f"  Matched: {len(results)}, GOOD: {len(good)}, BAD: {len(bad)}, NEUTRAL: {len(neut)}")

    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("HOW FAR DO GOOD SIGNALS RUN? (MFE in ATR units)")
    print("=" * 70)
    for field, label in [('mfe_30s','30s'), ('mfe_1m','1m'), ('mfe_2m','2m'),
                         ('mfe_5m','5m'), ('mfe_15m','15m'), ('mfe_30m','30m')]:
        vals = [r[field] for r in good if r[field] is not None]
        if not vals:
            continue
        a = np.array(vals)
        print(f"\n  {label:>4s} (n={len(a)}):")
        print(f"    Min={a.min():.3f}  25th={np.percentile(a,25):.3f}  Median={np.median(a):.3f}  75th={np.percentile(a,75):.3f}  90th={np.percentile(a,90):.3f}  Max={a.max():.3f}  Mean={a.mean():.3f}")

    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("HOW FAST DO BAD SIGNALS HURT? (MAE in ATR)")
    print("=" * 70)
    for field, label in [('mae_5m','5m'), ('mae_15m','15m'), ('mae_30m','30m')]:
        vals = [r[field] for r in bad if r[field] is not None]
        if not vals:
            continue
        a = np.array(vals)
        print(f"\n  {label:>4s} (n={len(a)}):")
        print(f"    Min={a.min():.3f}  Median={np.median(a):.3f}  75th={np.percentile(a,75):.3f}  Max={a.max():.3f}  Mean={a.mean():.3f}")

    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("EXPECTED VALUE PER SIGNAL (30-min horizon)")
    print("=" * 70)

    def ev_stats(subset, label):
        g = [r for r in subset if r['cls'] == 'GOOD']
        b = [r for r in subset if r['cls'] == 'BAD']
        n = len(subset)
        if n == 0:
            return
        g_mfe = np.mean([r['mfe_30m'] for r in g]) if g else 0
        b_mae = np.mean([r['mae_15m'] for r in b if r['mae_15m'] is not None]) if b else 0
        ev = (len(g)/n) * g_mfe - (len(b)/n) * b_mae
        print(f"  {label:>20s}: n={n:>4d}  GOOD={100*len(g)/n:>5.1f}% (avg MFE {g_mfe:.3f})  BAD={100*len(b)/n:>5.1f}% (avg MAE {b_mae:.3f})  EV={ev:+.4f} ATR")
        return ev

    ev_stats(results, "All signals")
    ev_stats([r for r in results if r['type'] == 'BRK'], "BRK only")
    ev_stats([r for r in results if r['type'] in ('~', '~~')], "Reversal/Reclaim")

    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("EV BY CONF STATUS")
    print("=" * 70)
    ev_stats([r for r in results if r['conf'] in ('pass',) and not r['conf_star']], "CONF ✓")
    ev_stats([r for r in results if r['conf_star']], "CONF ✓★")
    ev_stats([r for r in results if r['conf'] == 'fail'], "CONF ✗")

    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("EV BY TIME WINDOW")
    print("=" * 70)
    for tb in ['9:30-10', '10-11', '11-13', '13-16']:
        ev_stats([r for r in results if r['time_bucket'] == tb], tb)

    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("EV BY LEVEL (GOOD signals: how far they run)")
    print("=" * 70)
    for level in ['PM H', 'PM L', 'Yest H', 'Yest L', 'Week H', 'Week L', 'ORB H', 'ORB L']:
        lvl_good = [r for r in good if level in r['levels']]
        if len(lvl_good) < 2:
            print(f"  {level:>7s}: n={len(lvl_good)} (too few)")
            continue
        mfes = np.array([r['mfe_30m'] for r in lvl_good])
        print(f"  {level:>7s}: n={len(lvl_good):>3d}  median MFE={np.median(mfes):.3f}  mean={mfes.mean():.3f}  max={mfes.max():.3f} ATR")

    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("EV BY SYMBOL")
    print("=" * 70)
    for sym in sorted(ALL_SYMBOLS):
        ev_stats([r for r in results if r['symbol'] == sym], sym)

    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("DOLLAR EXAMPLES (assuming $3 ATR = typical AAPL/SPY)")
    print("=" * 70)
    g_mfe_30m = np.mean([r['mfe_30m'] for r in good])
    g_mfe_median = np.median([r['mfe_30m'] for r in good])
    g_mfe_90th = np.percentile([r['mfe_30m'] for r in good], 90)
    print(f"  GOOD signal avg move:    {g_mfe_30m:.3f} ATR = ${g_mfe_30m * 3:.2f}")
    print(f"  GOOD signal median move: {g_mfe_median:.3f} ATR = ${g_mfe_median * 3:.2f}")
    print(f"  GOOD signal 90th pctile: {g_mfe_90th:.3f} ATR = ${g_mfe_90th * 3:.2f}")
    print(f"  GOOD signal max move:    {max(r['mfe_30m'] for r in good):.3f} ATR = ${max(r['mfe_30m'] for r in good) * 3:.2f}")


if __name__ == '__main__':
    main()
