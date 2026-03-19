"""
TSLA Always-Long Backtest
=========================
Buy TSLA at 9:30 open every day. Test different holding periods.
Compare with 5-min rule from scalp research.

Data: 1m IB parquet (280 days, Feb 2025 - Mar 2026)
"""

import pandas as pd
import numpy as np
from pathlib import Path

CACHE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache")
DATA_FILE = CACHE / "bars/tsla_1_min_ib.parquet"

# Hold durations to test (in minutes from 9:30)
HOLD_MINUTES = [1, 2, 3, 5, 7, 10, 15, 20, 30, 45, 60, 90, 120, 150, 180, 210, 240, 270, 360]

def load_market_hours(df):
    """Filter to regular market hours 9:30-16:00 ET."""
    d = df.copy()
    d['date'] = pd.to_datetime(d['date'])
    d = d.set_index('date')
    d = d.tz_convert('America/New_York') if d.index.tz is not None else d
    # Keep 9:30 - 15:59
    d = d.between_time('09:30', '15:59')
    return d

def build_daily_grid(df):
    """Build per-day entry/exit grid."""
    rows = []
    for day, grp in df.groupby(df.index.date):
        grp = grp.sort_index()

        # Entry: open price of 9:30 bar
        open_bars = grp.between_time('09:30', '09:30')
        if open_bars.empty:
            continue
        entry_price = open_bars.iloc[0]['open']
        entry_time = open_bars.index[0]

        row = {
            'day': day,
            'entry': entry_price,
        }

        # Exit at each hold period
        for hold_m in HOLD_MINUTES:
            target_time = entry_time + pd.Timedelta(minutes=hold_m)
            # Find the bar at or just after target_time
            future = grp[grp.index >= target_time]
            if future.empty:
                # Use last available bar (EOD)
                exit_price = grp.iloc[-1]['close']
            else:
                exit_price = future.iloc[0]['close']
            row[f'exit_{hold_m}m'] = exit_price

        # EOD close (last bar of day)
        row['exit_eod'] = grp.iloc[-1]['close']

        # 5m close for the 5-min rule
        bar_9_35 = grp.between_time('09:35', '09:35')
        row['close_5m'] = bar_9_35.iloc[0]['close'] if not bar_9_35.empty else np.nan

        # Day high and low (for reference)
        row['day_high'] = grp['high'].max()
        row['day_low'] = grp['low'].min()

        rows.append(row)

    return pd.DataFrame(rows)

def stats(pnl_series):
    """Compute stats for a P&L series."""
    n = len(pnl_series)
    wins = (pnl_series > 0).sum()
    win_rate = wins / n * 100
    avg_pnl = pnl_series.mean()
    med_pnl = pnl_series.median()
    std_pnl = pnl_series.std()
    sharpe = avg_pnl / std_pnl * np.sqrt(252) if std_pnl > 0 else 0
    worst = pnl_series.min()
    best = pnl_series.max()
    return {
        'n': n, 'win%': round(win_rate, 1),
        'avg': round(avg_pnl, 2), 'med': round(med_pnl, 2),
        'std': round(std_pnl, 2), 'sharpe': round(sharpe, 2),
        'worst': round(worst, 2), 'best': round(best, 2),
    }

def main():
    print("Loading TSLA 1m data...")
    df = pd.read_parquet(DATA_FILE)
    df = load_market_hours(df)

    print(f"Date range: {df.index.min().date()} → {df.index.max().date()}")
    n_days = df.index.normalize().nunique()
    print(f"Trading days: {n_days}")

    print("\nBuilding daily grid...")
    grid = build_daily_grid(df)
    print(f"Days with valid open bar: {len(grid)}")

    # ── SECTION 1: Always-Long at 9:30 ─────────────────────────────
    print("\n" + "=" * 70)
    print("SECTION 1: ALWAYS LONG AT 9:30 — Holding Period Analysis")
    print("=" * 70)

    results = []
    for hold_m in HOLD_MINUTES:
        col = f'exit_{hold_m}m'
        pnl = grid[col] - grid['entry']
        s = stats(pnl)
        s['hold'] = f'{hold_m}m'
        results.append(s)

    # EOD
    pnl_eod = grid['exit_eod'] - grid['entry']
    s = stats(pnl_eod)
    s['hold'] = 'EOD'
    results.append(s)

    res_df = pd.DataFrame(results).set_index('hold')
    print(res_df[['n', 'win%', 'avg', 'med', 'std', 'sharpe', 'worst', 'best']].to_string())

    # ── SECTION 2: 5-Min Rule Filter ───────────────────────────────
    print("\n" + "=" * 70)
    print("SECTION 2: WITH 5-MIN RULE (hold only if 9:35 close > open)")
    print("=" * 70)

    hold_mask = grid['close_5m'] > grid['entry']
    bail_mask = grid['close_5m'] <= grid['entry']

    print(f"\nHOLD days (5m above open): {hold_mask.sum()} ({hold_mask.mean()*100:.0f}%)")
    print(f"BAIL days (5m below open): {bail_mask.sum()} ({bail_mask.mean()*100:.0f}%)")

    # HOLD days — various hold times
    print("\n--- HOLD days: stats per exit time ---")
    hold_results = []
    for hold_m in [10, 20, 30, 45, 60, 90, 120, 180, 240]:
        col = f'exit_{hold_m}m'
        if col not in grid.columns:
            continue
        pnl = (grid.loc[hold_mask, col] - grid.loc[hold_mask, 'entry'])
        s = stats(pnl)
        s['hold'] = f'{hold_m}m'
        hold_results.append(s)
    pnl_eod_hold = grid.loc[hold_mask, 'exit_eod'] - grid.loc[hold_mask, 'entry']
    s = stats(pnl_eod_hold)
    s['hold'] = 'EOD'
    hold_results.append(s)

    hold_df = pd.DataFrame(hold_results).set_index('hold')
    print(hold_df[['n', 'win%', 'avg', 'med', 'std', 'sharpe', 'worst', 'best']].to_string())

    # BAIL days — compare immediate bail vs holding anyway
    print("\n--- BAIL days: what happens if you hold anyway? ---")
    bail_results = []
    for hold_m in [10, 30, 60, 120]:
        col = f'exit_{hold_m}m'
        if col not in grid.columns:
            continue
        pnl = (grid.loc[bail_mask, col] - grid.loc[bail_mask, 'entry'])
        s = stats(pnl)
        s['hold'] = f'{hold_m}m'
        bail_results.append(s)
    pnl_eod_bail = grid.loc[bail_mask, 'exit_eod'] - grid.loc[bail_mask, 'entry']
    s = stats(pnl_eod_bail)
    s['hold'] = 'EOD'
    bail_results.append(s)

    bail_df = pd.DataFrame(bail_results).set_index('hold')
    print(bail_df[['n', 'win%', 'avg', 'med', 'sharpe', 'worst']].to_string())

    # ── SECTION 3: Max Favorable Excursion over time ────────────────
    print("\n" + "=" * 70)
    print("SECTION 3: EXPECTED UNREALIZED P&L OVER TIME (all 280 days)")
    print("= How far above entry are you on average at each minute? =")
    print("=" * 70)

    mfe_by_minute = []
    for hold_m in [1, 3, 5, 10, 15, 20, 30, 45, 60, 90, 120, 180, 240]:
        col = f'exit_{hold_m}m'
        if col not in grid.columns:
            continue
        pnl = grid[col] - grid['entry']
        pct_positive = (pnl > 0).mean() * 100
        avg = pnl.mean()
        # % days still above entry
        mfe_by_minute.append({
            'minute': hold_m,
            'above_entry_%': round(pct_positive, 1),
            'avg_pnl': round(avg, 2),
            'pct_days_up_$1': round((pnl > 1.0).mean() * 100, 1),
            'pct_days_up_$3': round((pnl > 3.0).mean() * 100, 1),
            'pct_days_up_$5': round((pnl > 5.0).mean() * 100, 1),
            'pct_days_down_$3': round((pnl < -3.0).mean() * 100, 1),
        })

    mfe_df = pd.DataFrame(mfe_by_minute).set_index('minute')
    print(mfe_df.to_string())

    # ── SECTION 4: Summary comparison ──────────────────────────────
    print("\n" + "=" * 70)
    print("SECTION 4: KEY COMPARISON — Always Long vs 5-Min Rule")
    print("=" * 70)

    best_blind = res_df['avg'].idxmax()
    best_blind_val = res_df['avg'].max()
    best_blind_wr = res_df.loc[best_blind, 'win%']

    print(f"\nBest blind hold time:  {best_blind} → avg P&L={best_blind_val:+.2f}, win%={best_blind_wr}%")
    print(f"EOD blind:  avg P&L={res_df.loc['EOD', 'avg']:+.2f}, win%={res_df.loc['EOD', 'win%']}%")

    best_rule = hold_df['avg'].idxmax()
    best_rule_val = hold_df['avg'].max()
    best_rule_wr = hold_df.loc[best_rule, 'win%']

    print(f"\nWith 5-min rule (HOLD days only):")
    print(f"  Best hold time: {best_rule} → avg P&L={best_rule_val:+.2f}, win%={best_rule_wr}%")
    print(f"  EOD: avg P&L={hold_df.loc['EOD', 'avg']:+.2f}, win%={hold_df.loc['EOD', 'win%']}%")

    # The scalp research baseline to compare against
    print("\n--- From prior scalp research (open-scalp-learnings.md) ---")
    print("  5-min rule HOLD baseline: avg day close = +$3.22, win% = 67%")
    print("  5-min rule BAIL baseline: avg day close = -$3.64, win% = 32%")
    print("  No direction filter (blind): avg day close = -$0.09, win% = 50%")

    # Save
    out = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug/tsla_always_long_results.md")
    print(f"\nSaving detailed results to {out.name}...")

    with open(out, 'w') as f:
        f.write("# TSLA Always-Long Backtest Results\n")
        f.write(f"*Generated {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}*\n\n")
        f.write(f"Data: {n_days} trading days, 1m bars\n\n")
        f.write("## Section 1: Always Long — Holding Period P&L\n\n")
        f.write(res_df[['n','win%','avg','med','std','sharpe','worst','best']].to_markdown())
        f.write("\n\n## Section 2a: HOLD Days (5m > open)\n\n")
        f.write(hold_df[['n','win%','avg','med','std','sharpe','worst','best']].to_markdown())
        f.write("\n\n## Section 2b: BAIL Days (5m ≤ open) — if held anyway\n\n")
        f.write(bail_df[['n','win%','avg','med','sharpe','worst']].to_markdown())
        f.write("\n\n## Section 3: % of Days Above Entry Over Time\n\n")
        f.write(mfe_df.to_markdown())

    print("Done.")

if __name__ == '__main__':
    main()
