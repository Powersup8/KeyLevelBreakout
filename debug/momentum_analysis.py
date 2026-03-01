#!/usr/bin/env python3
"""
Bar-by-bar momentum analysis: when does MFE peak? How much giveback?
What does a trailing stop actually capture? When does momentum die?

Uses 5-second candle data to trace the full price path of each signal.
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from v24_gap_analysis import (load_pine_logs, load_candles, classify_signal,
                               compute_excursions, time_bucket, ALL_SYMBOLS)
from datetime import timedelta
import numpy as np
import pytz

ET = pytz.timezone('US/Eastern')
HOLD_SECS = 1800  # 30 minutes


def trace_price_path(sig, candles_df, bar_secs):
    """
    Walk bar-by-bar from entry to +30m.
    Returns list of dicts: [{secs_after, pnl_atr, running_mfe_atr, running_mae_atr}, ...]
    """
    ts = sig['timestamp']
    entry = sig['close']
    atr = sig['atr']
    direction = sig['direction']

    if atr <= 0:
        return None

    ts_tz = ET.localize(ts) if ts.tzinfo is None else ts
    end_ts = ts_tz + timedelta(seconds=HOLD_SECS)

    window_df = candles_df.loc[
        (candles_df.index > ts_tz) & (candles_df.index <= end_ts)
    ]

    if len(window_df) < 6:  # need at least 30s of data
        return None

    path = []
    running_mfe = 0.0
    running_mae = 0.0

    for idx, row in window_df.iterrows():
        secs = (idx - ts_tz).total_seconds()

        if direction == 'bull':
            pnl = row['close'] - entry
            bar_mfe = row['high'] - entry
            bar_mae = entry - row['low']
        else:
            pnl = entry - row['close']
            bar_mfe = entry - row['low']
            bar_mae = row['high'] - entry

        running_mfe = max(running_mfe, bar_mfe)
        running_mae = max(running_mae, bar_mae)

        path.append({
            'secs': secs,
            'pnl_atr': pnl / atr,
            'mfe_atr': running_mfe / atr,
            'mae_atr': running_mae / atr,
            'giveback_atr': (running_mfe - pnl) / atr,  # how much given back from peak
        })

    return path


def trailing_stop_exit(path, stop_atr):
    """
    Simulate a trailing stop on a price path.
    Stop trails below the running high-water mark by stop_atr.
    Returns: (exit_secs, exit_pnl_atr, peak_before_exit_atr)
    """
    hwm = 0.0  # high water mark of P&L

    for p in path:
        pnl = p['pnl_atr']
        hwm = max(hwm, pnl)

        # Trailing stop: exit if price drops stop_atr below high water mark
        drawdown_from_peak = hwm - pnl
        if drawdown_from_peak >= stop_atr:
            exit_pnl = hwm - stop_atr  # exit at stop level
            return p['secs'], exit_pnl, hwm

    # Never stopped — exit at end of window
    return path[-1]['secs'], path[-1]['pnl_atr'], hwm


def fixed_stop_exit(path, stop_atr):
    """
    Simulate a fixed stop loss (no trailing).
    Returns: (exit_secs, exit_pnl_atr, was_stopped)
    """
    for p in path:
        if p['pnl_atr'] <= -stop_atr:
            return p['secs'], -stop_atr, True

    return path[-1]['secs'], path[-1]['pnl_atr'], False


def main():
    print("Loading pine logs...")
    signals, confs = load_pine_logs()

    print("Loading candle data...")
    candles_cache = {}
    bar_secs_cache = {}
    for sym in ALL_SYMBOLS:
        df, bsecs = load_candles(sym)
        if df is not None and len(df) > 0:
            candles_cache[sym] = df
            bar_secs_cache[sym] = bsecs

    # Only use 5s data (skip 1m symbols for bar-by-bar accuracy)
    print("Tracing price paths (5s bars, ~30 min each)...")
    traced = []
    for s in signals:
        sym = s['symbol']
        if sym not in candles_cache or bar_secs_cache.get(sym) != 5:
            continue  # skip symbols without 5s data

        bsecs = bar_secs_cache[sym]
        exc = compute_excursions(s, candles_cache[sym], bsecs)
        if exc.get('30m') is None:
            continue

        path = trace_price_path(s, candles_cache[sym], bsecs)
        if path is None or len(path) < 60:  # need at least 5 min of 5s bars
            continue

        cls = classify_signal(exc, s['atr'])
        vwap = s.get('vwap')
        direction = s['direction']

        # Find peak MFE time
        peak_idx = max(range(len(path)), key=lambda i: path[i]['mfe_atr'])
        peak_secs = path[peak_idx]['secs']
        peak_mfe = path[peak_idx]['mfe_atr']
        end_pnl = path[-1]['pnl_atr']
        giveback = peak_mfe - end_pnl  # how much lost from peak to exit

        traced.append({
            'symbol': sym,
            'type': s['type'],
            'direction': direction,
            'cls': cls,
            'conf': s.get('conf'),
            'conf_star': s.get('conf_star', False),
            'time_bucket': time_bucket(s['timestamp']),
            'vol': s.get('vol_ratio', s.get('vol', 0)),
            'levels': s.get('levels', []),
            'vwap_aligned': (direction == 'bull' and vwap == 'above') or
                            (direction == 'bear' and vwap == 'below'),
            'atr': s['atr'],
            'peak_mfe_atr': peak_mfe,
            'peak_secs': peak_secs,
            'end_pnl_atr': end_pnl,
            'giveback_atr': giveback,
            'giveback_pct': (giveback / peak_mfe * 100) if peak_mfe > 0.01 else 0,
            'path': path,
        })

    print(f"  Traced {len(traced)} signals with 5s bar-by-bar paths")
    good = [t for t in traced if t['cls'] == 'GOOD']
    bad = [t for t in traced if t['cls'] == 'BAD']
    neut = [t for t in traced if t['cls'] == 'NEUTRAL']
    print(f"  GOOD: {len(good)}, BAD: {len(bad)}, NEUTRAL: {len(neut)}")

    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("1. WHEN DOES MFE PEAK? (time of maximum favorable excursion)")
    print("=" * 70)

    for label, subset in [("All signals", traced), ("GOOD only", good), ("BAD only", bad)]:
        if not subset:
            continue
        peak_times = np.array([t['peak_secs'] for t in subset])
        print(f"\n  {label} (n={len(subset)}):")
        print(f"    Median peak time: {peak_times.mean()/60:.1f} min")
        for mins in [0.5, 1, 2, 5, 10, 15, 20, 30]:
            pct = 100 * np.sum(peak_times <= mins * 60) / len(peak_times)
            print(f"      Peak within {mins:>4.1f}m: {pct:>5.1f}%")

    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("2. HOW MUCH GIVEBACK FROM PEAK? (MFE - end P&L)")
    print("=" * 70)

    for label, subset in [("All signals", traced), ("GOOD only", good)]:
        if not subset:
            continue
        givebacks = np.array([t['giveback_atr'] for t in subset])
        giveback_pcts = np.array([t['giveback_pct'] for t in subset])
        peaks = np.array([t['peak_mfe_atr'] for t in subset])
        ends = np.array([t['end_pnl_atr'] for t in subset])
        print(f"\n  {label} (n={len(subset)}):")
        print(f"    Peak MFE:    mean={peaks.mean():.3f}  median={np.median(peaks):.3f} ATR")
        print(f"    End P&L:     mean={ends.mean():.3f}  median={np.median(ends):.3f} ATR")
        print(f"    Giveback:    mean={givebacks.mean():.3f}  median={np.median(givebacks):.3f} ATR")
        print(f"    Giveback %:  mean={giveback_pcts.mean():.1f}%  median={np.median(giveback_pcts):.1f}%")
        print(f"    Capture rate (end/peak): {100*ends.mean()/peaks.mean():.1f}%")

    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("3. TRAILING STOP SIMULATION (bar-by-bar)")
    print("=" * 70)

    print("\n  Testing trailing stop levels on ALL signals:")
    print(f"  {'Stop':>10s}  {'Avg P&L':>8s}  {'Med P&L':>8s}  {'WinR':>6s}  {'AvgHold':>8s}  {'Captured':>9s}  {'vs NoStop':>9s}")

    # No-stop baseline
    base_pnls = np.array([t['end_pnl_atr'] for t in traced])
    base_avg = base_pnls.mean()

    for stop in [0.05, 0.08, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30, 0.50]:
        exits = [trailing_stop_exit(t['path'], stop) for t in traced]
        pnls = np.array([e[1] for e in exits])
        hold_secs = np.array([e[0] for e in exits])
        peaks = np.array([e[2] for e in exits])
        wins = np.sum(pnls > 0.02)
        captured = pnls.mean() / base_avg * 100 if base_avg != 0 else 0
        print(f"  {stop:.2f} ATR  {pnls.mean():>+8.4f}  {np.median(pnls):>+8.4f}  {100*wins/len(pnls):>5.1f}%  {hold_secs.mean()/60:>6.1f}m  {captured:>8.1f}%  {pnls.mean()-base_avg:>+9.4f}")

    # Same for GOOD signals only
    if good:
        print(f"\n  Testing trailing stop levels on GOOD signals only:")
        print(f"  {'Stop':>10s}  {'Avg P&L':>8s}  {'Med P&L':>8s}  {'AvgHold':>8s}  {'Peak':>8s}  {'Captured%':>9s}")
        good_base = np.array([t['end_pnl_atr'] for t in good]).mean()
        for stop in [0.05, 0.08, 0.10, 0.15, 0.20, 0.25, 0.30, 0.50]:
            exits = [trailing_stop_exit(t['path'], stop) for t in good]
            pnls = np.array([e[1] for e in exits])
            hold_secs = np.array([e[0] for e in exits])
            peaks = np.array([e[2] for e in exits])
            captured_pct = pnls.mean() / peaks.mean() * 100 if peaks.mean() > 0 else 0
            print(f"  {stop:.2f} ATR  {pnls.mean():>+8.4f}  {np.median(pnls):>+8.4f}  {hold_secs.mean()/60:>6.1f}m  {peaks.mean():>+8.4f}  {captured_pct:>8.1f}%")

    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("4. FIXED STOP + TIME EXIT (most realistic simple strategy)")
    print("=" * 70)

    print("\n  Fixed stop loss, hold until 30m or stopped:")
    print(f"  {'Stop':>10s}  {'Avg P&L':>8s}  {'WinR':>6s}  {'Stopped%':>9s}  {'AvgHold':>8s}")
    for stop in [0.10, 0.15, 0.20, 0.25, 0.30]:
        exits = [fixed_stop_exit(t['path'], stop) for t in traced]
        pnls = np.array([e[1] for e in exits])
        hold_secs = np.array([e[0] for e in exits])
        stopped = sum(1 for e in exits if e[2])
        wins = np.sum(pnls > 0.02)
        print(f"  {stop:.2f} ATR  {pnls.mean():>+8.4f}  {100*wins/len(pnls):>5.1f}%  {100*stopped/len(exits):>8.1f}%  {hold_secs.mean()/60:>6.1f}m")

    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("5. MOMENTUM DEATH — when does direction become invalid?")
    print("=" * 70)

    # Define "momentum death" as first time P&L goes below -0.1 ATR after being positive
    print("\n  Momentum death = first time P&L drops below -0.10 ATR after being positive")
    for label, subset in [("All signals", traced), ("GOOD only", good), ("NEUTRAL only", neut)]:
        if not subset:
            continue
        death_times = []
        never_died = 0
        never_positive = 0
        for t in subset:
            was_positive = False
            died = False
            for p in t['path']:
                if p['pnl_atr'] > 0.02:
                    was_positive = True
                if was_positive and p['pnl_atr'] < -0.10:
                    death_times.append(p['secs'])
                    died = True
                    break
            if not died:
                if was_positive:
                    never_died += 1
                else:
                    never_positive += 1

        if death_times:
            dt = np.array(death_times)
            print(f"\n  {label} (n={len(subset)}):")
            print(f"    Momentum survived full 30m: {never_died} ({100*never_died/len(subset):.1f}%)")
            print(f"    Never went positive:        {never_positive} ({100*never_positive/len(subset):.1f}%)")
            print(f"    Died (n={len(death_times)}): median={np.median(dt)/60:.1f}m  mean={dt.mean()/60:.1f}m")
            for mins in [1, 2, 5, 10, 15]:
                pct = 100 * np.sum(dt <= mins * 60) / len(dt)
                print(f"      Dead within {mins:>2d}m: {pct:.1f}%")

    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("6. AVERAGE PRICE PATH (P&L over time, sampled every 30s)")
    print("=" * 70)

    # Sample the path at regular intervals and average
    sample_points = [30, 60, 120, 180, 300, 600, 900, 1200, 1500, 1800]
    for label, subset in [("All signals", traced), ("GOOD only", good), ("BAD only", bad)]:
        if not subset:
            continue
        print(f"\n  {label} — average P&L trajectory (ATR):")
        print(f"  {'Time':>6s}  {'Avg P&L':>8s}  {'Med P&L':>8s}  {'%Positive':>9s}  {'AvgMFE':>8s}")
        for target_secs in sample_points:
            pnls_at_t = []
            mfes_at_t = []
            for t in subset:
                # Find closest bar to target time
                best = None
                for p in t['path']:
                    if best is None or abs(p['secs'] - target_secs) < abs(best['secs'] - target_secs):
                        best = p
                if best and abs(best['secs'] - target_secs) < 30:
                    pnls_at_t.append(best['pnl_atr'])
                    mfes_at_t.append(best['mfe_atr'])
            if pnls_at_t:
                arr = np.array(pnls_at_t)
                mfe_arr = np.array(mfes_at_t)
                pos_pct = 100 * np.sum(arr > 0) / len(arr)
                mins = target_secs / 60
                print(f"  {mins:>5.1f}m  {arr.mean():>+8.4f}  {np.median(arr):>+8.4f}  {pos_pct:>8.1f}%  {mfe_arr.mean():>8.4f}")

    # ═══════════════════════════════════════════════════════════════
    # Write summary to file
    # ═══════════════════════════════════════════════════════════════
    outpath = os.path.join(os.path.dirname(__file__), "momentum-analysis-results.md")
    with open(outpath, 'w') as f:
        f.write("# Momentum & Exit Timing Analysis\n\n")
        f.write(f"> Bar-by-bar analysis of {len(traced)} signals using 5-second candle data\n")
        f.write(f"> GOOD: {len(good)}, BAD: {len(bad)}, NEUTRAL: {len(neut)}\n\n")

        # Peak timing
        f.write("## When Does MFE Peak?\n\n")
        for label, subset in [("All", traced), ("GOOD", good)]:
            if not subset:
                continue
            peaks = np.array([t['peak_secs'] for t in subset])
            f.write(f"**{label}** (n={len(subset)}): mean={peaks.mean()/60:.1f}m, median={np.median(peaks)/60:.1f}m\n\n")

        # Giveback
        f.write("## Giveback from Peak\n\n")
        for label, subset in [("All", traced), ("GOOD", good)]:
            if not subset:
                continue
            peaks = np.array([t['peak_mfe_atr'] for t in subset])
            ends = np.array([t['end_pnl_atr'] for t in subset])
            capture = 100 * ends.mean() / peaks.mean() if peaks.mean() > 0 else 0
            f.write(f"**{label}**: Peak MFE={peaks.mean():.3f}, End P&L={ends.mean():.3f}, ")
            f.write(f"Capture={capture:.0f}%\n\n")

        # Best trailing stop
        f.write("## Trailing Stop Results\n\n")
        f.write("| Stop (ATR) | Avg P&L | Win Rate | Avg Hold |\n")
        f.write("|------------|---------|----------|----------|\n")
        for stop in [0.08, 0.10, 0.15, 0.20, 0.25, 0.30]:
            exits = [trailing_stop_exit(t['path'], stop) for t in traced]
            pnls = np.array([e[1] for e in exits])
            hold_secs = np.array([e[0] for e in exits])
            wins = np.sum(pnls > 0.02)
            f.write(f"| {stop:.2f} | {pnls.mean():+.4f} | {100*wins/len(pnls):.1f}% | {hold_secs.mean()/60:.1f}m |\n")

        f.write("\n")

    print(f"\nResults written to {outpath}")


if __name__ == '__main__':
    main()
