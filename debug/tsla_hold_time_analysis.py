"""
P2: Hold Time Optimization — Deep Analysis
Runs backtest with sl_fallback=999 (no fallback SL) to isolate pure hold-time effect.
Compares exit prices at hold=3 vs hold=10 per trade.
"""

import sys
sys.path.insert(0, '/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug')

import pandas as pd
import numpy as np
from tsla_scalp_backtest import Config, load_data, run_backtest, score_trades

def main():
    print("Loading data...")
    df1m, df15, dfvix, dfspy, dfqqq = load_data()

    hold_times = [3, 5, 8, 10, 15, 20]
    results = {}

    # ── Part 1: No-fallback sweep ──
    print("\n" + "="*80)
    print("PART 1: HOLD TIME SWEEP — NO FALLBACK SL (sl_fallback=999)")
    print("="*80)

    for h in hold_times:
        cfg = Config(hold_bars=h, sl_fallback=999.0)
        trades = run_backtest(cfg, df1m, df15, dfvix, dfspy, dfqqq)
        results[h] = trades
        m = score_trades(trades)

        print(f"\n--- HOLD={h} bars ---")
        print(f"  n={m['n']}  win={m['win_pct']}%  avg=${m['avg_pnl']}  total=${m['total_pnl']}  "
              f"sharpe={m['sharpe']}  score={m['score']}")

        # Exit reason breakdown
        print(f"  Exit reasons:")
        for reason, group in trades.groupby('exit_reason'):
            gm = score_trades(group)
            print(f"    {reason:<20} n={gm['n']:>3}  win={gm['win_pct']:>5.1f}%  avg=${gm['avg_pnl']:>7.2f}")

    # ── Part 2: Bull breakout deep dive ──
    print("\n" + "="*80)
    print("PART 2: BULL BREAKOUT TRADES ONLY — NO FALLBACK SL")
    print("="*80)

    for h in hold_times:
        trades = results[h]
        bulls = trades[trades['breakout_type'] == 'BULL']
        if len(bulls) == 0:
            continue
        m = score_trades(bulls)
        wins = (bulls['pnl'] > 0).sum()
        print(f"\n  HOLD={h:>2}  bull_n={len(bulls):>3}  win={m['win_pct']:>5.1f}%  "
              f"avg=${m['avg_pnl']:>7.2f}  min=${bulls['pnl'].min():>7.2f}  max=${bulls['pnl'].max():>7.2f}  "
              f"median=${bulls['pnl'].median():>7.2f}")

    # ── Part 3: Trade-by-trade comparison (hold=3 vs hold=10) ──
    print("\n" + "="*80)
    print("PART 3: TRADE-BY-TRADE — HOLD=3 vs HOLD=10 (no fallback SL)")
    print("="*80)

    t3 = results[3].set_index('date')
    t10 = results[10].set_index('date')

    # Only compare bull breakout trades that exist in both
    common = t3.index.intersection(t10.index)
    bulls3 = t3.loc[common]
    bulls10 = t10.loc[common]

    # Filter to bull breakouts in BOTH
    bull_mask = (bulls3['breakout_type'] == 'BULL') & (bulls10['breakout_type'] == 'BULL')
    b3 = bulls3[bull_mask]
    b10 = bulls10[bull_mask]

    print(f"\n{'Date':<14} {'Entry':>8} {'Exit@3':>8} {'PnL@3':>7} {'Exit@10':>8} {'PnL@10':>7} {'Delta':>7} {'Left$':>7}")
    print("-" * 80)

    left_on_table = []
    for dt in b3.index:
        e = b3.loc[dt, 'entry_price']
        ex3 = b3.loc[dt, 'exit_price']
        ex10 = b10.loc[dt, 'exit_price']
        p3 = b3.loc[dt, 'pnl']
        p10 = b10.loc[dt, 'pnl']
        delta = p10 - p3
        left_on_table.append(delta)

        marker = " ***" if abs(delta) > 1.0 else ""
        d_str = str(dt.date()) if hasattr(dt, 'date') else str(dt)[:10]
        print(f"  {d_str:<12} {e:>8.2f} {ex3:>8.2f} {p3:>7.2f} {ex10:>8.2f} {p10:>7.2f} {delta:>+7.2f}{marker}")

    left = np.array(left_on_table)
    print(f"\n  Summary of 'left on table' (PnL@10 - PnL@3):")
    print(f"    Mean: ${left.mean():+.2f}")
    print(f"    Median: ${np.median(left):+.2f}")
    print(f"    Cases where 10 > 3: {(left > 0).sum()} / {len(left)}")
    print(f"    Cases where 3 > 10: {(left < 0).sum()} / {len(left)}")
    print(f"    Max upside missed: ${left.max():+.2f}")
    print(f"    Max downside avoided: ${left.min():+.2f}")

    # ── Part 4: Bar-by-bar decay curve for bull breakouts ──
    print("\n" + "="*80)
    print("PART 4: BAR-BY-BAR P&L DECAY CURVE (bull breakouts, no fallback SL)")
    print("="*80)

    # Run hold=1 through hold=20 for bull-only stats
    print(f"\n{'Hold':>6} {'Bull_n':>7} {'Win%':>6} {'AvgPnL':>8} {'MedianPnL':>10}")
    print("-" * 42)
    for h in range(1, 21):
        cfg = Config(hold_bars=h, sl_fallback=999.0)
        trades = run_backtest(cfg, df1m, df15, dfvix, dfspy, dfqqq)
        bulls = trades[trades['breakout_type'] == 'BULL']
        if len(bulls) == 0:
            continue
        w = (bulls['pnl'] > 0).mean() * 100
        print(f"  {h:>4}   {len(bulls):>5}   {w:>5.1f}  ${bulls['pnl'].mean():>7.2f}   ${bulls['pnl'].median():>7.2f}")

    # ── Part 5: Options perspective ──
    print("\n" + "="*80)
    print("PART 5: OPTIONS PERSPECTIVE — FIRST-MOVE CAPTURE RATIO")
    print("="*80)

    # For each bull breakout in hold=20 result, compute MFE at bar 3, 5, 10, 15, 20
    cfg20 = Config(hold_bars=20, sl_fallback=999.0)
    trades20 = run_backtest(cfg20, df1m, df15, dfvix, dfspy, dfqqq)
    bulls20 = trades20[trades20['breakout_type'] == 'BULL']

    # We need per-trade MFE at different hold points — re-simulate
    mfe_at = {h: [] for h in [3, 5, 8, 10, 15, 20]}
    pnl_at = {h: [] for h in [3, 5, 8, 10, 15, 20]}

    market_days = sorted(df1m.between_time('09:30', '16:00').index.normalize().unique())

    for _, trade in bulls20.iterrows():
        d = trade['date']
        mkt = df1m[df1m.index.normalize() == d].between_time('09:30', '16:00')
        if len(mkt) < 10:
            continue

        orb_bars_data = mkt.between_time('09:30', '09:34')
        orb_high = orb_bars_data['high'].max()
        entry = trade['entry_price']

        # Find breakout bar
        post_orb = mkt[mkt.index.map(lambda x: 935 <= x.hour * 100 + x.minute)]
        bo_idx = None
        for i, (idx, bar) in enumerate(post_orb.iterrows()):
            if bar['close'] > orb_high:
                bo_idx = i
                break

        if bo_idx is None:
            continue

        for h in [3, 5, 8, 10, 15, 20]:
            end_idx = bo_idx + h
            if end_idx < len(post_orb):
                window = post_orb.iloc[bo_idx:end_idx + 1]
                mfe_val = window['high'].max() - entry
                pnl_val = post_orb.iloc[end_idx]['close'] - entry
            else:
                window = post_orb.iloc[bo_idx:]
                mfe_val = window['high'].max() - entry
                pnl_val = post_orb.iloc[-1]['close'] - entry

            mfe_at[h].append(mfe_val)
            pnl_at[h].append(pnl_val)

    print(f"\n  Bull breakout MFE and realized P&L at different hold points:")
    print(f"  {'Hold':>6} {'Avg MFE':>9} {'Avg PnL':>9} {'Capture%':>10}  (PnL/MFE@20)")
    print(f"  " + "-" * 42)

    mfe20_avg = np.mean(mfe_at[20]) if mfe_at[20] else 1
    for h in [3, 5, 8, 10, 15, 20]:
        if not mfe_at[h]:
            continue
        avg_mfe = np.mean(mfe_at[h])
        avg_pnl = np.mean(pnl_at[h])
        # Capture ratio: avg realized PnL at this hold vs MFE at hold=20
        capture = (avg_pnl / mfe20_avg * 100) if mfe20_avg > 0 else 0
        print(f"  {h:>4}   ${avg_mfe:>7.2f}  ${avg_pnl:>7.2f}   {capture:>8.1f}%")

    # Options delta/gamma insight
    print(f"\n  Options insight (0DTE TSLA ATM call):")
    print(f"  - Delta ~0.50 at entry, gamma ~0.03-0.05 per $1 move")
    print(f"  - First $1 move: option gains ~$0.50-0.55 (delta + gamma pickup)")
    print(f"  - Second $1 move: option gains ~$0.55-0.65 (higher delta now)")
    print(f"  - Theta decay: ~$0.15-0.30/hr for 0DTE near open")
    print(f"  - 3 bars (3 min) theta cost: ~$0.01 (negligible)")
    print(f"  - 10 bars (10 min) theta cost: ~$0.03-0.05 (still small)")
    print(f"  - Key: gamma makes early move MOST valuable per $ of stock move")
    print(f"  - A $1 stock gain in first 3 min ≈ $0.52 option gain")
    print(f"  - Holding 7 more min for $0.20 more stock ≈ $0.12 more option")
    print(f"  - Risk: reversal after bar 3 costs MORE in options (higher delta now)")

    # ── Part 6: With-SL comparison ──
    print("\n" + "="*80)
    print("PART 6: COMPARISON — WITH vs WITHOUT FALLBACK SL")
    print("="*80)

    print(f"\n  {'Config':<30} {'n':>4} {'Win%':>6} {'AvgPnL':>8} {'Score':>7} {'Sharpe':>7}")
    print("  " + "-" * 65)

    for h in [3, 5, 10, 15]:
        # With SL
        cfg_sl = Config(hold_bars=h, sl_fallback=1.50)
        t_sl = run_backtest(cfg_sl, df1m, df15, dfvix, dfspy, dfqqq)
        m_sl = score_trades(t_sl)

        # Without SL
        cfg_no = Config(hold_bars=h, sl_fallback=999.0)
        t_no = run_backtest(cfg_no, df1m, df15, dfvix, dfspy, dfqqq)
        m_no = score_trades(t_no)

        print(f"  {'HOLD='+str(h)+' +SL=1.50':<30} {m_sl['n']:>4} {m_sl['win_pct']:>5.1f}% ${m_sl['avg_pnl']:>7.2f} {m_sl['score']:>7.1f} {m_sl['sharpe']:>7.2f}")
        print(f"  {'HOLD='+str(h)+' NO_SL':<30} {m_no['n']:>4} {m_no['win_pct']:>5.1f}% ${m_no['avg_pnl']:>7.2f} {m_no['score']:>7.1f} {m_no['sharpe']:>7.2f}")

    print("\nDone.")


if __name__ == '__main__':
    main()
