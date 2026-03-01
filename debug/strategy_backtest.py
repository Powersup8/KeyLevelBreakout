#!/usr/bin/env python3
"""
Strategy backtest: test research recommendations against 5s candle data.

Tests:
  1. Runner Score filter (0-5 stacking factors)
  2. 5-minute stop rule (0.15 ATR)
  3. CONF-only strategies
  4. Combined best filters

Output: printed results + debug/strategy-backtest-results.md
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from v24_gap_analysis import (load_pine_logs, load_candles, compute_excursions,
                               classify_signal, time_bucket, ALL_SYMBOLS)
import numpy as np

# ── Tier classification ─────────────────────────────────────────────────────
A_TIER = {'AMZN', 'QQQ', 'SPY'}
B_TIER = {'AAPL', 'GOOGL', 'META', 'NVDA', 'TSLA'}
D_TIER = {'AMD', 'MSFT', 'GLD'}
LOW_LEVELS = {'Yest L', 'PM L', 'ORB L', 'Week L'}
HIGH_LEVELS = {'Yest H', 'PM H', 'ORB H', 'Week H'}


def runner_score(r):
    """Compute Runner Score (0-5) based on research factors."""
    score = 0
    # 1. With-trend VWAP
    if r.get('vwap_aligned'):
        score += 1
    # 2. Volume 2-5x sweet spot
    if 2.0 <= r['vol'] <= 5.0:
        score += 1
    # 3. Time 10:00-11:00
    if r['time_bucket'] == '10-11':
        score += 1
    # 4. LOW level (any)
    levels_set = set(r['levels']) if isinstance(r['levels'], list) else set(r['levels'].split(', ')) if r['levels'] else set()
    if levels_set & LOW_LEVELS:
        score += 1
    # 5. A/B-tier symbol (not D-tier)
    if r['symbol'] not in D_TIER:
        score += 1
    return score


def simulate_trade(r, stop_atr=None):
    """
    Simulate a single trade using excursion data.

    Returns dict with:
      - pnl_atr: realized P&L in ATR units
      - stopped: whether the 5-min stop was hit
      - outcome: 'win', 'loss', or 'flat'

    Strategy:
      - If stop_atr is set and mae_5m > stop_atr: exit at -stop_atr (stopped out)
      - Otherwise: use mfe_30m minus some slippage (realistic exit = 70% of MFE)
        minus mae contribution (since MAE happened along the way)
    """
    mfe_5m = r.get('mfe_5m')
    mae_5m = r.get('mae_5m')
    mfe_30m = r.get('mfe_30m')
    mae_30m = r.get('mae_30m')

    if mfe_30m is None:
        return {'pnl_atr': 0, 'stopped': False, 'outcome': 'flat'}

    # 5-minute stop check
    if stop_atr is not None and mae_5m is not None and mae_5m > stop_atr:
        return {'pnl_atr': -stop_atr, 'stopped': True, 'outcome': 'loss'}

    # Realistic exit: capture ~60% of MFE (can't pick the exact top)
    # Adjusted by the average drawdown experienced
    capture_rate = 0.60
    realistic_pnl = mfe_30m * capture_rate
    # Subtract a fraction of MAE as cost-of-being-in-the-trade
    if mae_30m is not None:
        realistic_pnl -= mae_30m * 0.3  # MAE doesn't fully hit P&L if we hold through it

    if realistic_pnl > 0.02:  # above noise threshold
        return {'pnl_atr': realistic_pnl, 'stopped': False, 'outcome': 'win'}
    elif realistic_pnl < -0.02:
        return {'pnl_atr': realistic_pnl, 'stopped': False, 'outcome': 'loss'}
    else:
        return {'pnl_atr': realistic_pnl, 'stopped': False, 'outcome': 'flat'}


def strategy_stats(results, label, stop_atr=None):
    """Run a strategy over a subset and return stats dict."""
    n = len(results)
    if n == 0:
        return None

    trades = [simulate_trade(r, stop_atr=stop_atr) for r in results]
    pnls = np.array([t['pnl_atr'] for t in trades])
    wins = sum(1 for t in trades if t['outcome'] == 'win')
    losses = sum(1 for t in trades if t['outcome'] == 'loss')
    stops = sum(1 for t in trades if t['stopped'])
    goods = sum(1 for r in results if r['cls'] == 'GOOD')
    bads = sum(1 for r in results if r['cls'] == 'BAD')

    return {
        'label': label,
        'n': n,
        'goods': goods,
        'bads': bads,
        'good_pct': 100 * goods / n,
        'bad_pct': 100 * bads / n,
        'wins': wins,
        'losses': losses,
        'stops': stops,
        'win_rate': 100 * wins / n,
        'total_pnl': float(pnls.sum()),
        'avg_pnl': float(pnls.mean()),
        'median_pnl': float(np.median(pnls)),
        'max_win': float(pnls.max()),
        'max_loss': float(pnls.min()),
        'sharpe': float(pnls.mean() / pnls.std()) if pnls.std() > 0 else 0,
        'profit_factor': float(pnls[pnls > 0].sum() / abs(pnls[pnls < 0].sum())) if pnls[pnls < 0].sum() != 0 else float('inf'),
    }


def print_strategy(s):
    if s is None:
        return
    print(f"\n  {s['label']}")
    print(f"    Signals: {s['n']:>5d}   GOOD: {s['good_pct']:.1f}%   BAD: {s['bad_pct']:.1f}%")
    print(f"    Wins: {s['wins']:>4d}  Losses: {s['losses']:>4d}  Win Rate: {s['win_rate']:.1f}%  Stopped: {s['stops']}")
    print(f"    Total P&L: {s['total_pnl']:+.2f} ATR   Avg: {s['avg_pnl']:+.4f}   Median: {s['median_pnl']:+.4f}")
    print(f"    Max Win: {s['max_win']:+.3f}   Max Loss: {s['max_loss']:+.3f}   Sharpe: {s['sharpe']:.3f}   PF: {s['profit_factor']:.2f}")


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
    results = []
    for s in signals:
        sym = s['symbol']
        if sym not in candles_cache:
            continue
        bsecs = bar_secs_cache.get(sym, 5)
        exc = compute_excursions(s, candles_cache[sym], bsecs)
        if exc.get('30m') is None:
            continue
        cls = classify_signal(exc, s['atr'])

        # Determine VWAP alignment
        vwap = s.get('vwap')
        direction = s['direction']
        vwap_aligned = (direction == 'bull' and vwap == 'above') or \
                       (direction == 'bear' and vwap == 'below')

        results.append({
            'type': s['type'],
            'direction': direction,
            'levels': s.get('levels', []),
            'vol': s.get('vol_ratio', s.get('vol', 0)),
            'conf': s.get('conf'),
            'conf_star': s.get('conf_star', False),
            'atr': s['atr'],
            'time_bucket': time_bucket(s['timestamp']),
            'symbol': sym,
            'vwap': vwap,
            'vwap_aligned': vwap_aligned,
            'cls': cls,
            'mfe_5m':  exc['5m']['mfe_atr']  if exc.get('5m')  else None,
            'mfe_15m': exc['15m']['mfe_atr'] if exc.get('15m') else None,
            'mfe_30m': exc['30m']['mfe_atr'] if exc.get('30m') else None,
            'mae_5m':  exc['5m']['mae_atr']  if exc.get('5m')  else None,
            'mae_15m': exc['15m']['mae_atr'] if exc.get('15m') else None,
            'mae_30m': exc['30m']['mae_atr'] if exc.get('30m') else None,
        })

    # Add runner score to each
    for r in results:
        r['score'] = runner_score(r)

    print(f"  Matched: {len(results)} signals with excursion data")

    # ═══════════════════════════════════════════════════════════════
    # SECTION 1: BASELINE
    # ═══════════════════════════════════════════════════════════════
    output_lines = []
    def section(title):
        print(f"\n{'=' * 70}")
        print(title)
        print('=' * 70)
        output_lines.append(f"\n## {title}\n")

    section("1. BASELINE — All Signals (no filter, no stop)")
    base = strategy_stats(results, "All signals (baseline)")
    base_stop = strategy_stats(results, "All signals + 0.15 ATR stop", stop_atr=0.15)
    print_strategy(base)
    print_strategy(base_stop)

    # ═══════════════════════════════════════════════════════════════
    # SECTION 2: RUNNER SCORE FILTER
    # ═══════════════════════════════════════════════════════════════
    section("2. RUNNER SCORE FILTER (0-5 factors)")

    # Score distribution
    print("\n  Score distribution:")
    for sc in range(6):
        subset = [r for r in results if r['score'] == sc]
        goods = sum(1 for r in subset if r['cls'] == 'GOOD')
        bads = sum(1 for r in subset if r['cls'] == 'BAD')
        n = len(subset)
        print(f"    Score {sc}: n={n:>4d}  GOOD={100*goods/n if n else 0:.1f}%  BAD={100*bads/n if n else 0:.1f}%")

    for threshold in [2, 3, 4]:
        subset = [r for r in results if r['score'] >= threshold]
        s = strategy_stats(subset, f"Score >= {threshold}", stop_atr=0.15)
        print_strategy(s)

    # ═══════════════════════════════════════════════════════════════
    # SECTION 3: CONF STATUS STRATEGIES
    # ═══════════════════════════════════════════════════════════════
    section("3. CONF STATUS STRATEGIES")

    conf_pass = [r for r in results if r['conf'] in ('pass', 'pass_star')]
    conf_star = [r for r in results if r['conf_star']]
    conf_fail = [r for r in results if r['conf'] == 'fail']
    no_conf = [r for r in results if r['conf'] is None]

    print_strategy(strategy_stats(conf_pass, "CONF ✓ (any)", stop_atr=0.15))
    print_strategy(strategy_stats(conf_star, "CONF ✓★ only", stop_atr=0.15))
    print_strategy(strategy_stats(conf_fail, "CONF ✗ (would you exit?)", stop_atr=0.15))
    print_strategy(strategy_stats(no_conf, "No CONF yet (unmatched)", stop_atr=0.15))

    # ═══════════════════════════════════════════════════════════════
    # SECTION 4: TIME WINDOW STRATEGIES
    # ═══════════════════════════════════════════════════════════════
    section("4. TIME WINDOW STRATEGIES")
    for tb in ['9:30-10', '10-11', '11-13', '13-16']:
        subset = [r for r in results if r['time_bucket'] == tb]
        print_strategy(strategy_stats(subset, f"Time {tb}", stop_atr=0.15))

    # ═══════════════════════════════════════════════════════════════
    # SECTION 5: LOW vs HIGH LEVELS
    # ═══════════════════════════════════════════════════════════════
    section("5. LOW vs HIGH LEVELS")

    def has_level_type(r, level_set):
        lvls = r['levels']
        if isinstance(lvls, list):
            return any(l in level_set for l in lvls)
        return any(l in (lvls or '') for l in level_set)

    low_signals = [r for r in results if has_level_type(r, LOW_LEVELS)]
    high_signals = [r for r in results if has_level_type(r, HIGH_LEVELS) and not has_level_type(r, LOW_LEVELS)]
    print_strategy(strategy_stats(low_signals, "LOW levels only", stop_atr=0.15))
    print_strategy(strategy_stats(high_signals, "HIGH levels only", stop_atr=0.15))

    # ═══════════════════════════════════════════════════════════════
    # SECTION 6: COMBINED BEST STRATEGIES
    # ═══════════════════════════════════════════════════════════════
    section("6. COMBINED BEST STRATEGIES")

    # Strategy A: Score >= 3 + 0.15 stop + BRK only
    brk_score3 = [r for r in results if r['score'] >= 3 and r['type'] == 'BRK']
    print_strategy(strategy_stats(brk_score3, "BRK + Score>=3 + 0.15 stop", stop_atr=0.15))

    # Strategy B: Score >= 3 + CONF pass + stop
    score3_conf = [r for r in results if r['score'] >= 3 and r['conf'] in ('pass', 'pass_star')]
    print_strategy(strategy_stats(score3_conf, "Score>=3 + CONF ✓ + 0.15 stop", stop_atr=0.15))

    # Strategy C: 10-11 window + LOW level + stop
    sweet_spot = [r for r in results
                  if r['time_bucket'] == '10-11'
                  and has_level_type(r, LOW_LEVELS)]
    print_strategy(strategy_stats(sweet_spot, "10-11 + LOW level + 0.15 stop", stop_atr=0.15))

    # Strategy D: CONF ✓★ only (gold labels)
    print_strategy(strategy_stats(conf_star, "CONF ✓★ + 0.15 stop", stop_atr=0.15))

    # Strategy E: The research "ideal trade"
    # 10-11, LOW level, 2-5x vol, with-VWAP, A/B-tier
    ideal = [r for r in results
             if r['time_bucket'] == '10-11'
             and has_level_type(r, LOW_LEVELS)
             and 2.0 <= r['vol'] <= 5.0
             and r['vwap_aligned']
             and r['symbol'] not in D_TIER]
    print_strategy(strategy_stats(ideal, "IDEAL (all 5 factors = Score 5) + stop", stop_atr=0.15))

    # ═══════════════════════════════════════════════════════════════
    # SECTION 7: STOP LEVEL SENSITIVITY
    # ═══════════════════════════════════════════════════════════════
    section("7. STOP LEVEL SENSITIVITY (all signals)")
    for stop in [0.10, 0.15, 0.20, 0.25, 0.30, None]:
        label = f"Stop={stop:.2f} ATR" if stop else "No stop"
        s = strategy_stats(results, label, stop_atr=stop)
        if s:
            stops_pct = 100 * s['stops'] / s['n'] if s['n'] > 0 else 0
            print(f"    {label:>16s}: avg={s['avg_pnl']:+.4f}  total={s['total_pnl']:+.1f}  winR={s['win_rate']:.1f}%  PF={s['profit_factor']:.2f}  stopped={stops_pct:.1f}%")

    # ═══════════════════════════════════════════════════════════════
    # SECTION 8: INDIVIDUAL FACTOR IMPACT
    # ═══════════════════════════════════════════════════════════════
    section("8. INDIVIDUAL FACTOR IMPACT (isolate each factor)")
    factors = [
        ("VWAP aligned", lambda r: r['vwap_aligned']),
        ("VWAP not aligned", lambda r: not r['vwap_aligned']),
        ("Vol 2-5x", lambda r: 2.0 <= r['vol'] <= 5.0),
        ("Vol <2x", lambda r: r['vol'] < 2.0),
        ("Vol 5-10x", lambda r: 5.0 < r['vol'] <= 10.0),
        ("Vol 10x+", lambda r: r['vol'] > 10.0),
        ("Time 10-11", lambda r: r['time_bucket'] == '10-11'),
        ("Time 9:30-10", lambda r: r['time_bucket'] == '9:30-10'),
        ("LOW level", lambda r: has_level_type(r, LOW_LEVELS)),
        ("HIGH level", lambda r: has_level_type(r, HIGH_LEVELS)),
        ("A-tier sym", lambda r: r['symbol'] in A_TIER),
        ("D-tier sym", lambda r: r['symbol'] in D_TIER),
        ("BRK only", lambda r: r['type'] == 'BRK'),
        ("Reversal ~", lambda r: r['type'] == '~'),
        ("Reclaim ~~", lambda r: r['type'] == '~~'),
    ]
    for label, filt in factors:
        subset = [r for r in results if filt(r)]
        s = strategy_stats(subset, label, stop_atr=0.15)
        if s and s['n'] >= 10:
            print(f"    {label:>20s}: n={s['n']:>4d}  avg={s['avg_pnl']:+.4f}  GOOD={s['good_pct']:.1f}%  BAD={s['bad_pct']:.1f}%  PF={s['profit_factor']:.2f}")

    # ═══════════════════════════════════════════════════════════════
    # SECTION 9: DOLLAR EXAMPLES
    # ═══════════════════════════════════════════════════════════════
    section("9. DOLLAR EXAMPLES (assuming $3 ATR)")
    for label, subset, stop in [
        ("Baseline (all)", results, None),
        ("Baseline + stop", results, 0.15),
        ("Score>=3 + stop", [r for r in results if r['score'] >= 3], 0.15),
        ("BRK + Score>=3 + stop", brk_score3, 0.15),
        ("CONF ✓★ + stop", conf_star, 0.15),
    ]:
        s = strategy_stats(subset, label, stop_atr=stop)
        if s:
            avg_dollar = s['avg_pnl'] * 3
            total_dollar = s['total_pnl'] * 3
            print(f"    {label:>25s}: n={s['n']:>4d}  avg=${avg_dollar:+.2f}/trade  total=${total_dollar:+.1f} (28 days)")

    # ═══════════════════════════════════════════════════════════════
    # Write results to file
    # ═══════════════════════════════════════════════════════════════
    outpath = os.path.join(os.path.dirname(__file__), "strategy-backtest-results.md")
    with open(outpath, 'w') as f:
        f.write("# Strategy Backtest Results\n\n")
        f.write("> Backtest of research recommendations against 5s candle data\n")
        f.write(f"> {len(results)} signals, 13 symbols, 28 days (Jan 20 – Feb 27 2026)\n\n")

        # Summary table
        f.write("## Key Findings\n\n")
        f.write("| Strategy | Signals | Avg P&L (ATR) | Win Rate | Profit Factor | GOOD% | BAD% |\n")
        f.write("|----------|---------|---------------|----------|---------------|-------|------|\n")

        for label, subset, stop in [
            ("Baseline (no filter, no stop)", results, None),
            ("Baseline + 0.15 stop", results, 0.15),
            ("Score >= 3 + stop", [r for r in results if r['score'] >= 3], 0.15),
            ("BRK + Score>=3 + stop", brk_score3, 0.15),
            ("Score>=3 + CONF ✓ + stop", score3_conf, 0.15),
            ("10-11 + LOW level + stop", sweet_spot, 0.15),
            ("CONF ✓★ + stop", conf_star, 0.15),
            ("IDEAL (Score 5) + stop", ideal, 0.15),
        ]:
            s = strategy_stats(subset, label, stop_atr=stop)
            if s and s['n'] > 0:
                f.write(f"| {label} | {s['n']} | {s['avg_pnl']:+.4f} | {s['win_rate']:.1f}% | {s['profit_factor']:.2f} | {s['good_pct']:.1f}% | {s['bad_pct']:.1f}% |\n")

        f.write("\n## Score Distribution\n\n")
        f.write("| Score | Signals | GOOD% | BAD% | Avg P&L (ATR) |\n")
        f.write("|-------|---------|-------|------|---------------|\n")
        for sc in range(6):
            subset = [r for r in results if r['score'] == sc]
            s = strategy_stats(subset, f"Score {sc}", stop_atr=0.15)
            if s and s['n'] > 0:
                f.write(f"| {sc} | {s['n']} | {s['good_pct']:.1f}% | {s['bad_pct']:.1f}% | {s['avg_pnl']:+.4f} |\n")

        f.write("\n## Individual Factor Impact\n\n")
        f.write("| Factor | Signals | Avg P&L | GOOD% | BAD% | PF |\n")
        f.write("|--------|---------|---------|-------|------|----|\n")
        for label, filt in factors:
            subset = [r for r in results if filt(r)]
            s = strategy_stats(subset, label, stop_atr=0.15)
            if s and s['n'] >= 10:
                f.write(f"| {label} | {s['n']} | {s['avg_pnl']:+.4f} | {s['good_pct']:.1f}% | {s['bad_pct']:.1f}% | {s['profit_factor']:.2f} |\n")

        f.write("\n## Dollar Examples ($3 ATR stock)\n\n")
        f.write("| Strategy | Trades | Avg $/trade | Total $ (28 days) |\n")
        f.write("|----------|--------|-------------|-------------------|\n")
        for label, subset, stop in [
            ("Baseline (all)", results, None),
            ("Baseline + stop", results, 0.15),
            ("Score>=3 + stop", [r for r in results if r['score'] >= 3], 0.15),
            ("BRK + Score>=3 + stop", brk_score3, 0.15),
            ("CONF ✓★ + stop", conf_star, 0.15),
        ]:
            s = strategy_stats(subset, label, stop_atr=stop)
            if s:
                f.write(f"| {label} | {s['n']} | ${s['avg_pnl']*3:+.2f} | ${s['total_pnl']*3:+.1f} |\n")

    print(f"\n\nResults written to {outpath}")


if __name__ == '__main__':
    main()
