#!/usr/bin/env python3
"""Investigate whether TSLA's 79% P&L dominance is structural edge or regime overfitting."""

import pandas as pd
import numpy as np
from io import StringIO

BASE = "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug"

trades = pd.read_csv(f"{BASE}/v28a-trades.csv")
signals = pd.read_csv(f"{BASE}/v28a-signals.csv")
ft = pd.read_csv(f"{BASE}/v28a-follow-through.csv")

# Parse dates (utc=True to handle mixed timezone offsets from DST)
trades['date'] = pd.to_datetime(trades['signal_time'], utc=True).dt.date
trades['month'] = pd.to_datetime(trades['signal_time'], utc=True).dt.to_period('M')

signals['date'] = pd.to_datetime(signals['datetime'], utc=True).dt.date
signals['month'] = pd.to_datetime(signals['datetime'], utc=True).dt.to_period('M')

ft['date'] = pd.to_datetime(ft['datetime'], utc=True).dt.date
ft['month'] = pd.to_datetime(ft['datetime'], utc=True).dt.to_period('M')

out = []
def section(title):
    out.append(f"\n## {title}\n")
def p(text=""):
    out.append(text)

out.append("# TSLA Dominance Analysis: Structural Edge vs Regime Overfitting\n")
p(f"Dataset: {trades['date'].min()} to {trades['date'].max()} | {len(trades)} trades | 10 symbols")
p()

# ============================================================
# 1. Monthly P&L by symbol
# ============================================================
section("1. Monthly P&L by Symbol (ATR units)")

monthly = trades.groupby(['symbol', 'month'])['pnl_atr'].sum().unstack(fill_value=0)
monthly['TOTAL'] = monthly.sum(axis=1)
monthly.loc['ALL'] = monthly.sum()

p("```")
p(monthly.round(2).to_string())
p("```")

# TSLA monthly breakdown
tsla_monthly = trades[trades['symbol'] == 'TSLA'].groupby('month').agg(
    trades=('pnl_atr', 'count'),
    pnl_atr=('pnl_atr', 'sum'),
    wins=('pnl_atr', lambda x: (x > 0).sum()),
    avg_pnl=('pnl_atr', 'mean')
).round(3)
tsla_monthly['wr'] = (tsla_monthly['wins'] / tsla_monthly['trades'] * 100).round(1)

p("\n**TSLA monthly detail:**")
p("```")
p(tsla_monthly.to_string())
p("```")

# Key finding: is TSLA concentrated or consistent?
tsla_months_positive = (tsla_monthly['pnl_atr'] > 0).sum()
tsla_months_total = len(tsla_monthly)
p(f"\nTSLA profitable months: {tsla_months_positive}/{tsla_months_total}")

# ============================================================
# 2. TSLA P&L by direction
# ============================================================
section("2. TSLA P&L by Direction")

tsla_trades = trades[trades['symbol'] == 'TSLA']

for direction in ['bull', 'bear']:
    dt = tsla_trades[tsla_trades['direction'] == direction]
    p(f"**{direction.upper()}:** {len(dt)} trades | P&L: {dt['pnl_atr'].sum():.2f} ATR | "
      f"Win rate: {(dt['pnl_atr'] > 0).sum()}/{len(dt)} ({(dt['pnl_atr'] > 0).mean()*100:.1f}%) | "
      f"Avg: {dt['pnl_atr'].mean():.3f} ATR")

p()
# Monthly direction breakdown for TSLA
tsla_dir_monthly = tsla_trades.groupby(['direction', 'month'])['pnl_atr'].sum().unstack(fill_value=0)
tsla_dir_monthly['TOTAL'] = tsla_dir_monthly.sum(axis=1)
p("**TSLA P&L by direction and month:**")
p("```")
p(tsla_dir_monthly.round(2).to_string())
p("```")

# ============================================================
# 3. TSLA vs others: feature comparison
# ============================================================
section("3. TSLA vs Other Symbols: Signal Characteristics")

# From trades
def symbol_profile(df, sym):
    d = df[df['symbol'] == sym] if sym != 'REST' else df[df['symbol'] != 'TSLA']
    return {
        'trades': len(d),
        'pnl_atr': d['pnl_atr'].sum(),
        'avg_pnl': d['pnl_atr'].mean(),
        'win_rate': (d['pnl_atr'] > 0).mean() * 100,
        'avg_mfe': d['mfe_atr'].mean(),
        'avg_atr': d['atr'].mean(),
        'avg_vol': d['vol'].mean(),
    }

profiles = {}
for sym in sorted(trades['symbol'].unique()):
    profiles[sym] = symbol_profile(trades, sym)
profiles['_REST'] = symbol_profile(trades, 'REST')

prof_df = pd.DataFrame(profiles).T
prof_df = prof_df.round(3)
p("```")
p(prof_df.to_string())
p("```")

p("\n**Key comparisons:**")
tsla_p = profiles['TSLA']
rest_p = profiles['_REST']
p(f"- TSLA win rate: {tsla_p['win_rate']:.1f}% vs REST: {rest_p['win_rate']:.1f}%")
p(f"- TSLA avg P&L/trade: {tsla_p['avg_pnl']:.3f} ATR vs REST: {rest_p['avg_pnl']:.3f} ATR")
p(f"- TSLA avg MFE: {tsla_p['avg_mfe']:.3f} ATR vs REST: {rest_p['avg_mfe']:.3f} ATR")
p(f"- TSLA avg vol mult: {tsla_p['avg_vol']:.1f}x vs REST: {rest_p['avg_vol']:.1f}x")
p(f"- TSLA avg ATR ($): {tsla_p['avg_atr']:.2f} vs REST: {rest_p['avg_atr']:.2f}")

# ============================================================
# 4. System WITHOUT TSLA
# ============================================================
section("4. System Performance WITHOUT TSLA")

rest_trades = trades[trades['symbol'] != 'TSLA'].copy()
rest_trades = rest_trades.sort_values('signal_time')

p(f"Total trades (ex-TSLA): {len(rest_trades)}")
p(f"Total P&L: {rest_trades['pnl_atr'].sum():.2f} ATR")
p(f"Win rate: {(rest_trades['pnl_atr'] > 0).mean()*100:.1f}%")
p(f"Avg P&L/trade: {rest_trades['pnl_atr'].mean():.3f} ATR")
p(f"Profit factor: {rest_trades[rest_trades['pnl_atr'] > 0]['pnl_atr'].sum() / abs(rest_trades[rest_trades['pnl_atr'] < 0]['pnl_atr'].sum()):.2f}")

# Cumulative P&L and drawdown for ex-TSLA
cum = rest_trades['pnl_atr'].cumsum()
peak = cum.cummax()
dd = cum - peak
p(f"Max drawdown: {dd.min():.2f} ATR")
p(f"Peak P&L: {peak.max():.2f} ATR")

# Monthly ex-TSLA
rest_monthly = rest_trades.groupby('month')['pnl_atr'].sum()
p(f"\n**Monthly P&L (ex-TSLA):**")
p("```")
p(rest_monthly.round(2).to_string())
p("```")
rest_positive_months = (rest_monthly > 0).sum()
p(f"Profitable months: {rest_positive_months}/{len(rest_monthly)}")

# Compare with TSLA
p("\n**With vs Without TSLA:**")
all_pnl = trades['pnl_atr'].sum()
tsla_pnl = tsla_trades['pnl_atr'].sum()
rest_pnl = rest_trades['pnl_atr'].sum()
p(f"- Full system: {all_pnl:.2f} ATR")
p(f"- TSLA only:   {tsla_pnl:.2f} ATR ({tsla_pnl/all_pnl*100:.1f}%)")
p(f"- Ex-TSLA:     {rest_pnl:.2f} ATR ({rest_pnl/all_pnl*100:.1f}%)")

# ============================================================
# 5. Per-symbol monthly consistency
# ============================================================
section("5. Per-Symbol Monthly Consistency")

consistency = []
for sym in sorted(trades['symbol'].unique()):
    st = trades[trades['symbol'] == sym]
    sm = st.groupby('month')['pnl_atr'].sum()
    consistency.append({
        'symbol': sym,
        'months_active': len(sm),
        'months_profitable': (sm > 0).sum(),
        'consistency': f"{(sm > 0).sum()}/{len(sm)}",
        'total_pnl': sm.sum(),
        'best_month': sm.max(),
        'worst_month': sm.min(),
        'monthly_std': sm.std(),
        'concentration': sm.max() / sm.sum() * 100 if sm.sum() > 0 else np.nan,
    })

cons_df = pd.DataFrame(consistency).set_index('symbol')
cons_df = cons_df.round(2)
p("```")
p(cons_df.to_string())
p("```")

p("\n**Interpretation:**")
p("- `concentration` = best month as % of total P&L (100% = all profit from one month = very fragile)")
p("- Consistent edge: multiple profitable months, low concentration, low std")

# ============================================================
# 6. TSLA ATR and volatility analysis
# ============================================================
section("6. TSLA ATR/Volatility: Is the Edge Just More Movement?")

# Normalize P&L by ATR — that's already what pnl_atr is.
# So if TSLA has a higher pnl_atr, it's not just "bigger moves"
p("P&L is already ATR-normalized, so pnl_atr controls for move size.")
p("If TSLA's edge were just volatility, its avg pnl_atr would be similar to others.\n")

# Compare raw dollar ATR
p("**Dollar ATR by symbol:**")
atr_by_sym = trades.groupby('symbol')['atr'].mean().sort_values(ascending=False)
p("```")
p(atr_by_sym.round(2).to_string())
p("```")

# pnl_atr distribution
p("\n**ATR-normalized P&L distribution:**")
pnl_stats = trades.groupby('symbol')['pnl_atr'].describe()[['mean', 'std', '25%', '50%', '75%']]
p("```")
p(pnl_stats.round(3).to_string())
p("```")

# TSLA MFE vs MAE from follow-through data
p("\n**Follow-through MFE (30-bar window) by symbol:**")
ft30 = ft[ft['window'] == 30]
ft_mfe = ft30.groupby('symbol').agg(
    signals=('mfe', 'count'),
    avg_mfe=('mfe', 'mean'),
    avg_mae=('mae', 'mean'),
    avg_ratio=('ratio', 'mean'),
).round(3)
p("```")
p(ft_mfe.to_string())
p("```")

# ============================================================
# 7. Verdict
# ============================================================
section("7. Verdict: Structural Edge or Regime Overfitting?")

# Calculate key metrics for the verdict
tsla_bear_pnl = tsla_trades[tsla_trades['direction'] == 'bear']['pnl_atr'].sum()
tsla_bull_pnl = tsla_trades[tsla_trades['direction'] == 'bull']['pnl_atr'].sum()
tsla_bear_pct = tsla_bear_pnl / tsla_trades['pnl_atr'].sum() * 100 if tsla_trades['pnl_atr'].sum() != 0 else 0

# Check if TSLA's ATR-normalized edge is genuinely different
tsla_avg_pnl_atr = tsla_trades['pnl_atr'].mean()
rest_avg_pnl_atr = rest_trades['pnl_atr'].mean()
edge_ratio = tsla_avg_pnl_atr / rest_avg_pnl_atr if rest_avg_pnl_atr != 0 else float('inf')

p("**Evidence for REGIME DEPENDENCY (overfitting to downtrend):**")
p(f"- Bear direction P&L: {tsla_bear_pnl:.2f} ATR ({tsla_bear_pct:.0f}% of TSLA total)")
p(f"- Bull direction P&L: {tsla_bull_pnl:.2f} ATR ({100-tsla_bear_pct:.0f}% of TSLA total)")
if tsla_bear_pct > 70:
    p(f"  --> Bear side dominates = edge is directionally concentrated")
p(f"- Dataset period coincides with TSLA downtrend ($490->$390)")
p(f"- TSLA profitable months: {tsla_months_positive}/{tsla_months_total}")

# Check monthly concentration
tsla_best = tsla_monthly['pnl_atr'].max()
tsla_total = tsla_monthly['pnl_atr'].sum()
if tsla_total > 0:
    p(f"- Best month concentration: {tsla_best:.2f} / {tsla_total:.2f} = {tsla_best/tsla_total*100:.0f}%")

p()
p("**Evidence for STRUCTURAL EDGE:**")
p(f"- TSLA avg pnl_atr: {tsla_avg_pnl_atr:.3f} vs REST: {rest_avg_pnl_atr:.3f} (ratio: {edge_ratio:.1f}x)")
p(f"- ATR-normalized P&L already controls for volatility")
if tsla_p['win_rate'] > rest_p['win_rate']:
    p(f"- Higher win rate: {tsla_p['win_rate']:.1f}% vs {rest_p['win_rate']:.1f}%")
if tsla_p['avg_mfe'] > rest_p['avg_mfe']:
    p(f"- Higher MFE: {tsla_p['avg_mfe']:.3f} vs {rest_p['avg_mfe']:.3f}")

p()
p("**Bottom line:**")
# Auto-generate verdict based on data
if tsla_bear_pct > 65 and tsla_months_positive < tsla_months_total * 0.7:
    p("TSLA's dominance is PRIMARILY REGIME-DEPENDENT. The edge is concentrated in bear-side "
      "trades during a downtrend. When the trend reverses, expect TSLA's contribution to shrink "
      "or flip negative. The system ex-TSLA should be evaluated as the true baseline.")
elif tsla_bear_pct > 55:
    p("TSLA shows MIXED evidence. Bear trades contribute disproportionately (regime factor), "
      "but there is some bull-side edge too. Monitor monthly consistency going forward.")
else:
    p("TSLA's edge appears STRUCTURAL — balanced across directions and consistent over time. "
      "The higher ATR-normalized returns suggest genuine signal quality, not just regime fit.")

p()
p(f"**Recommendation:** Use ex-TSLA P&L ({rest_pnl:.2f} ATR) as the conservative baseline. "
  f"TSLA adds {tsla_pnl:.2f} ATR but carries regime risk. "
  f"If ex-TSLA system is {'profitable' if rest_pnl > 0 else 'NOT profitable'}, "
  f"the strategy has a foundation independent of TSLA's trend.")


# Write report
report = "\n".join(out)
with open(f"{BASE}/v28b-tsla-dominance.md", "w") as f:
    f.write(report)

print(report)
print("\n\n--- Report saved to debug/v28b-tsla-dominance.md ---")
