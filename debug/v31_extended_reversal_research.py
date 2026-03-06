"""
v3.1 Extended Reversal Research
Investigate counter-EMA reversals to find discriminating patterns for high-quality setups like TSLA 10:16 on March 5.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Paths
TV_DIR = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug")
IB_DIR = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars")

def load_ib(symbol, tf):
    """Load IB parquet, set date as index."""
    f = IB_DIR / f"{symbol.lower()}_{tf}_ib.parquet"
    df = pd.read_parquet(f)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    if df.index.tz is not None:
        df.index = df.index.tz_convert('US/Eastern')
    else:
        df.index = df.index.tz_localize('US/Eastern')
    return df

# ============================================================
# PART 1: Characterize TSLA 10:16 setup from IB data
# ============================================================
print("=" * 80)
print("PART 1: TSLA 10:16 SETUP CHARACTERIZATION (IB DATA)")
print("=" * 80)

tsla_1m = load_ib('TSLA', '1_min')
tsla_5m = load_ib('TSLA', '5_mins')
tsla_1d = load_ib('TSLA', '1_day')

print(f"TSLA 1m: {tsla_1m.index.min()} to {tsla_1m.index.max()}, {len(tsla_1m)} rows")
print(f"TSLA 5m: {tsla_5m.index.min()} to {tsla_5m.index.max()}, {len(tsla_5m)} rows")

# Check if March 5 exists
has_mar5 = tsla_1m.index.normalize() == pd.Timestamp('2026-03-05', tz='US/Eastern')
if has_mar5.any():
    mar5_1m = tsla_1m[has_mar5]
    print(f"\nMarch 5 TSLA 1m candles: {len(mar5_1m)}")
else:
    print(f"\nMarch 5 NOT in IB data. Latest date: {tsla_1m.index.max()}")
    # Use the latest available trading day with similar pattern for calibration
    # Instead, proceed with enriched signals analysis

# Compute TSLA ATR from IB daily
tsla_1d_recent = tsla_1d.tail(30)
tsla_1d_recent['tr'] = tsla_1d_recent['high'] - tsla_1d_recent['low']
tsla_atr = tsla_1d_recent['tr'].mean()
print(f"TSLA ATR (30-day avg daily range): {tsla_atr:.2f}")

# The TSLA 10:16 setup from investigation report:
# - Rally from 401 to ~408 (7 points = 0.48 ATR)
# - Hit Yest H = 408.33
# - EMA(20) on 5m flipped bull during rally
# - Reversed hard after touching Yest H
TSLA_RALLY = 7.0  # points
TSLA_RALLY_ATR = TSLA_RALLY / tsla_atr
print(f"\nTSLA 10:16 rally: {TSLA_RALLY} pts = {TSLA_RALLY_ATR:.2f} ATR")
print(f"Level: Yesterday's High (408.33)")
print(f"Setup: Price rallied to resistance, EMA flipped bull (counter-EMA for bear REV)")
print(f"This is a COUNTER-EMA + COUNTER-VWAP setup (price above VWAP after rally)")

# Find similar patterns in IB TSLA history
print("\n--- Finding similar TSLA reversals at Yest H in IB data ---")
tsla_5m_rth = tsla_5m.between_time('09:30', '16:00').copy()
tsla_5m_rth['ema20'] = tsla_5m_rth['close'].ewm(span=20, adjust=False).mean()
tsla_5m_rth['date_only'] = tsla_5m_rth.index.date

dates = sorted(tsla_5m_rth['date_only'].unique())
tsla_setups = []

for i in range(1, len(dates)):
    prev_date = dates[i-1]
    curr_date = dates[i]

    prev_day = tsla_5m_rth[tsla_5m_rth['date_only'] == prev_date]
    curr_day = tsla_5m_rth[tsla_5m_rth['date_only'] == curr_date]

    if len(prev_day) < 5 or len(curr_day) < 5:
        continue

    yest_h = prev_day['high'].max()
    yest_l = prev_day['low'].min()
    atr = yest_h - yest_l
    if atr <= 0:
        continue

    for j in range(3, min(len(curr_day) - 3, 30)):  # first ~2.5 hrs
        bar = curr_day.iloc[j]
        bar_time = curr_day.index[j]

        # Touch or exceed yesterday's high
        if bar['high'] >= yest_h * 0.999:
            # EMA bullish (aligned with rally)
            ema_bull = bar['close'] > bar['ema20']

            # Check for subsequent reversal (next 6 bars = 30 min)
            future = curr_day.iloc[j+1:j+7]
            if len(future) >= 3:
                drop = bar['high'] - future['low'].min()
                drop_atr = drop / atr

                if drop_atr >= 0.2:  # meaningful reversal
                    # Compute how far the bar overextended past yest H
                    overext = (bar['high'] - yest_h) / atr

                    # Pre-move: rally from session open/low to this bar
                    pre_bars = curr_day.iloc[:j+1]
                    rally = bar['high'] - pre_bars['low'].min()
                    rally_atr = rally / atr

                    tsla_setups.append({
                        'date': str(curr_date),
                        'time': bar_time.strftime('%H:%M'),
                        'yest_h': yest_h,
                        'bar_high': bar['high'],
                        'overext_atr': overext,
                        'rally_atr': rally_atr,
                        'drop_atr': drop_atr,
                        'ema_bull': ema_bull,
                        'volume': bar.get('volume', 0),
                    })
                    break  # one per day

if tsla_setups:
    df_setups = pd.DataFrame(tsla_setups)
    print(f"Found {len(df_setups)} TSLA reversals at Yest H")
    print(f"\nEMA-aligned (counter-EMA reversal, like 10:16): {df_setups['ema_bull'].sum()}")
    ema_aligned = df_setups[df_setups['ema_bull']]
    ema_not = df_setups[~df_setups['ema_bull']]
    print(f"  With EMA bull (counter-EMA REV): avg drop={ema_aligned['drop_atr'].mean():.3f} ATR, avg rally={ema_aligned['rally_atr'].mean():.3f}")
    if len(ema_not) > 0:
        print(f"  Without EMA bull: avg drop={ema_not['drop_atr'].mean():.3f} ATR, avg rally={ema_not['rally_atr'].mean():.3f}")
    print(f"\nAll TSLA Yest H reversals:")
    print(df_setups.to_string(index=False))


# ============================================================
# PART 2: Counter-EMA REV analysis from enriched signals
# ============================================================
print("\n" + "=" * 80)
print("PART 2: COUNTER-EMA REV SIGNAL ANALYSIS (ENRICHED SIGNALS)")
print("=" * 80)

signals = pd.read_csv(TV_DIR / "enriched-signals.csv")
print(f"Total signals: {len(signals)}")

rev_signals = signals[signals['type'] == 'REV'].copy()
print(f"Total REV signals: {len(rev_signals)}")

# Counter-EMA: signal direction opposes EMA
rev_signals['counter_ema'] = (
    ((rev_signals['direction'] == 'bull') & (rev_signals['ema'] == 'bear')) |
    ((rev_signals['direction'] == 'bear') & (rev_signals['ema'] == 'bull'))
)
# Also include 'mixed' EMA as counter-EMA (not clearly aligned)
rev_signals['counter_ema_or_mixed'] = rev_signals['counter_ema'] | (rev_signals['ema'] == 'mixed')

counter_ema_rev = rev_signals[rev_signals['counter_ema']].copy()
counter_ema_mixed = rev_signals[rev_signals['counter_ema_or_mixed']].copy()
aligned_ema_rev = rev_signals[~rev_signals['counter_ema'] & (rev_signals['ema'] != 'mixed')].copy()

print(f"Counter-EMA REVs (strict): {len(counter_ema_rev)}")
print(f"Counter-EMA + mixed: {len(counter_ema_mixed)}")
print(f"EMA-aligned REVs: {len(aligned_ema_rev)}")

# Define win/loss
for df in [counter_ema_rev, aligned_ema_rev, counter_ema_mixed]:
    df['winner'] = df['mfe'] > abs(df['mae'])
    df['net_pnl'] = df['mfe'] + df['mae']  # mae is negative

print(f"\n--- Counter-EMA REV Summary ---")
print(f"Win rate: {counter_ema_rev['winner'].mean():.1%} (N={len(counter_ema_rev)})")
print(f"Avg MFE: {counter_ema_rev['mfe'].mean():.3f}, Avg MAE: {counter_ema_rev['mae'].mean():.3f}")
print(f"Avg net P&L: {counter_ema_rev['net_pnl'].mean():.3f}, Total: {counter_ema_rev['net_pnl'].sum():.1f}")

print(f"\n--- EMA-Aligned REV Summary ---")
print(f"Win rate: {aligned_ema_rev['winner'].mean():.1%} (N={len(aligned_ema_rev)})")
print(f"Avg MFE: {aligned_ema_rev['mfe'].mean():.3f}, Avg MAE: {aligned_ema_rev['mae'].mean():.3f}")
print(f"Avg net P&L: {aligned_ema_rev['net_pnl'].mean():.3f}, Total: {aligned_ema_rev['net_pnl'].sum():.1f}")

# ============================================================
# PART 2b: Deep factor analysis
# ============================================================
print("\n" + "=" * 80)
print("PART 2b: FACTOR ANALYSIS — WINNERS vs LOSERS")
print("=" * 80)

winners = counter_ema_rev[counter_ema_rev['winner']].copy()
losers = counter_ema_rev[~counter_ema_rev['winner']].copy()

print(f"Winners: {len(winners)}, Losers: {len(losers)}")

# Counter-VWAP
counter_ema_rev['counter_vwap'] = (
    ((counter_ema_rev['direction'] == 'bear') & (counter_ema_rev['vwap'] == 'above')) |
    ((counter_ema_rev['direction'] == 'bull') & (counter_ema_rev['vwap'] == 'below'))
)

def print_factor(name, col, df=counter_ema_rev):
    """Print factor split."""
    print(f"\n--- {name} ---")
    for val in sorted(df[col].unique()):
        subset = df[df[col] == val]
        if len(subset) >= 2:
            wr = subset['winner'].mean()
            pnl = subset['net_pnl'].mean()
            mfe = subset['mfe'].mean()
            print(f"  {val}: N={len(subset)}, Win={wr:.1%}, MFE={mfe:.3f}, P&L={pnl:.3f}")

print_factor("Level Type", 'level_type')
print_factor("Time Bucket", 'time_bucket')
print_factor("Volume Bucket", 'vol_bucket')
print_factor("VWAP Position", 'vwap')
print_factor("Direction", 'direction')
print_factor("Multi-Level", 'multi_level')

# Counter-VWAP
print(f"\n--- Counter-VWAP ---")
for grp, label in [(True, 'Counter-VWAP'), (False, 'With-VWAP')]:
    subset = counter_ema_rev[counter_ema_rev['counter_vwap'] == grp]
    if len(subset) >= 2:
        wr = subset['winner'].mean()
        mfe = subset['mfe'].mean()
        pnl = subset['net_pnl'].mean()
        total = subset['net_pnl'].sum()
        print(f"  {label}: N={len(subset)}, Win={wr:.1%}, MFE={mfe:.3f}, P&L={pnl:.3f}, Total={total:.1f}")

# ADX thresholds
print(f"\n--- ADX Thresholds ---")
for thresh in [20, 25, 30, 35, 40]:
    above = counter_ema_rev[counter_ema_rev['adx'] >= thresh]
    below = counter_ema_rev[counter_ema_rev['adx'] < thresh]
    if len(above) >= 3:
        wr = above['winner'].mean()
        pnl = above['net_pnl'].mean()
        print(f"  ADX >= {thresh}: N={len(above)}, Win={wr:.1%}, P&L={pnl:.3f}")

# Volume thresholds
print(f"\n--- Volume Thresholds ---")
for thresh in [1.5, 2.0, 3.0, 5.0]:
    above = counter_ema_rev[counter_ema_rev['vol'] >= thresh]
    if len(above) >= 3:
        wr = above['winner'].mean()
        pnl = above['net_pnl'].mean()
        print(f"  Vol >= {thresh}x: N={len(above)}, Win={wr:.1%}, P&L={pnl:.3f}")

# Body size
print(f"\n--- Body Size ---")
for thresh in [30, 50, 60, 70]:
    above = counter_ema_rev[counter_ema_rev['body'] >= thresh]
    if len(above) >= 3:
        wr = above['winner'].mean()
        pnl = above['net_pnl'].mean()
        print(f"  Body >= {thresh}%: N={len(above)}, Win={wr:.1%}, P&L={pnl:.3f}")

# Level names
print(f"\n--- By Specific Level ---")
for lvl in counter_ema_rev['levels'].value_counts().head(15).index:
    subset = counter_ema_rev[counter_ema_rev['levels'] == lvl]
    wr = subset['winner'].mean()
    pnl = subset['net_pnl'].mean()
    total = subset['net_pnl'].sum()
    print(f"  {lvl}: N={len(subset)}, Win={wr:.1%}, P&L={pnl:.3f}, Total={total:.1f}")

# Level categories
print(f"\n--- By Level Category ---")
for pattern, label in [('Yest H', 'Yest High'), ('Yest L', 'Yest Low'), ('PM H', 'PM High'), ('PM L', 'PM Low'),
                        ('Week H', 'Week High'), ('Week L', 'Week Low'), ('ORB H', 'ORB High'), ('ORB L', 'ORB Low'),
                        ('PD Mid', 'PD Mid'), ('PD LH', 'PD Last Hr')]:
    subset = counter_ema_rev[counter_ema_rev['levels'].str.contains(pattern, na=False)]
    if len(subset) >= 2:
        wr = subset['winner'].mean()
        pnl = subset['net_pnl'].mean()
        total = subset['net_pnl'].sum()
        print(f"  {label}: N={len(subset)}, Win={wr:.1%}, P&L={pnl:.3f}, Total={total:.1f}")

# Symbol
print(f"\n--- By Symbol ---")
for sym in sorted(counter_ema_rev['symbol'].unique()):
    subset = counter_ema_rev[counter_ema_rev['symbol'] == sym]
    wr = subset['winner'].mean()
    pnl = subset['net_pnl'].mean()
    print(f"  {sym}: N={len(subset)}, Win={wr:.1%}, P&L={pnl:.3f}")

# ============================================================
# PART 2c: Combination filters — the search for edge
# ============================================================
print("\n" + "=" * 80)
print("PART 2c: COMBINATION FILTERS — FINDING THE EDGE")
print("=" * 80)

combos = [
    ("ALL counter-EMA REV (baseline)", pd.Series(True, index=counter_ema_rev.index)),
    # Direction + Level type
    ("Bear + HIGH level", (counter_ema_rev['direction'] == 'bear') & (counter_ema_rev['level_type'] == 'HIGH')),
    ("Bull + LOW level", (counter_ema_rev['direction'] == 'bull') & (counter_ema_rev['level_type'] == 'LOW')),
    # Counter-VWAP combos (the TSLA 10:16 fingerprint)
    ("Counter-VWAP", counter_ema_rev['counter_vwap']),
    ("Counter-VWAP + HIGH level", counter_ema_rev['counter_vwap'] & (counter_ema_rev['level_type'] == 'HIGH')),
    ("Counter-VWAP + LOW level", counter_ema_rev['counter_vwap'] & (counter_ema_rev['level_type'] == 'LOW')),
    ("Counter-VWAP + HIGH/LOW", counter_ema_rev['counter_vwap'] & counter_ema_rev['level_type'].isin(['HIGH', 'LOW'])),
    ("Counter-VWAP + Morning (<10:30)", counter_ema_rev['counter_vwap'] & counter_ema_rev['time_bucket'].isin(['9:30-10:00', '10:00-10:30'])),
    # High/Low level combos
    ("HIGH/LOW level only", counter_ema_rev['level_type'].isin(['HIGH', 'LOW'])),
    ("HIGH/LOW + Morning", counter_ema_rev['level_type'].isin(['HIGH', 'LOW']) & counter_ema_rev['time_bucket'].isin(['9:30-10:00', '10:00-10:30'])),
    ("HIGH/LOW + Vol >= 2x", counter_ema_rev['level_type'].isin(['HIGH', 'LOW']) & (counter_ema_rev['vol'] >= 2.0)),
    ("HIGH/LOW + ADX >= 25", counter_ema_rev['level_type'].isin(['HIGH', 'LOW']) & (counter_ema_rev['adx'] >= 25)),
    ("HIGH/LOW + ADX >= 30", counter_ema_rev['level_type'].isin(['HIGH', 'LOW']) & (counter_ema_rev['adx'] >= 30)),
    # Specific level combos
    ("Yest H/L levels", counter_ema_rev['levels'].str.contains('Yest', na=False)),
    ("Yest H/L + Counter-VWAP", counter_ema_rev['levels'].str.contains('Yest', na=False) & counter_ema_rev['counter_vwap']),
    ("PM H/L levels", counter_ema_rev['levels'].str.contains('PM ', na=False)),
    ("PM H/L + Counter-VWAP", counter_ema_rev['levels'].str.contains('PM ', na=False) & counter_ema_rev['counter_vwap']),
    ("Week H/L levels", counter_ema_rev['levels'].str.contains('Week', na=False)),
    ("ORB H/L levels", counter_ema_rev['levels'].str.contains('ORB', na=False)),
    # ADX combos
    ("ADX >= 30", counter_ema_rev['adx'] >= 30),
    ("ADX >= 30 + Counter-VWAP", (counter_ema_rev['adx'] >= 30) & counter_ema_rev['counter_vwap']),
    ("ADX >= 25 + Counter-VWAP", (counter_ema_rev['adx'] >= 25) & counter_ema_rev['counter_vwap']),
    # Body size combos
    ("Body >= 60%", counter_ema_rev['body'] >= 60),
    ("Body >= 60% + HIGH/LOW", (counter_ema_rev['body'] >= 60) & counter_ema_rev['level_type'].isin(['HIGH', 'LOW'])),
    # The TSLA 10:16 exact fingerprint
    ("TSLA-like: Bear+Resist+CtrVWAP+Morning",
     (counter_ema_rev['direction'] == 'bear') &
     counter_ema_rev['levels'].str.contains('Yest H|PM H|Week H', na=False, regex=True) &
     counter_ema_rev['counter_vwap'] &
     counter_ema_rev['time_bucket'].isin(['9:30-10:00', '10:00-10:30'])),
    # Relaxed TSLA-like
    ("Bear + Resistance + CtrVWAP",
     (counter_ema_rev['direction'] == 'bear') &
     counter_ema_rev['levels'].str.contains('Yest H|PM H|Week H', na=False, regex=True) &
     counter_ema_rev['counter_vwap']),
    ("Bull + Support + CtrVWAP",
     (counter_ema_rev['direction'] == 'bull') &
     counter_ema_rev['levels'].str.contains('Yest L|PM L|Week L', na=False, regex=True) &
     counter_ema_rev['counter_vwap']),
    # Daily+ levels (exclude ORB)
    ("Daily+ level (not ORB)", counter_ema_rev['levels'].str.contains('Yest|Week|PM ', na=False, regex=True) & ~counter_ema_rev['levels'].str.contains('ORB', na=False)),
    ("Daily+ + Counter-VWAP", counter_ema_rev['levels'].str.contains('Yest|Week|PM ', na=False, regex=True) & ~counter_ema_rev['levels'].str.contains('ORB', na=False) & counter_ema_rev['counter_vwap']),
    # Vol >= 3x
    ("Vol >= 3x", counter_ema_rev['vol'] >= 3.0),
    ("Vol >= 3x + HIGH/LOW", (counter_ema_rev['vol'] >= 3.0) & counter_ema_rev['level_type'].isin(['HIGH', 'LOW'])),
    # Multi-level
    ("Multi-level", counter_ema_rev['multi_level'] == True),
    ("Multi-level + Counter-VWAP", (counter_ema_rev['multi_level'] == True) & counter_ema_rev['counter_vwap']),
]

print(f"\n{'Filter':<55} {'N':>4} {'Win%':>6} {'MFE':>7} {'MAE':>7} {'P&L':>7} {'Total':>7}")
print("-" * 100)
for name, mask in combos:
    subset = counter_ema_rev[mask]
    if len(subset) >= 2:
        wr = subset['winner'].mean()
        avg_mfe = subset['mfe'].mean()
        avg_mae = subset['mae'].mean()
        avg_pnl = subset['net_pnl'].mean()
        total_pnl = subset['net_pnl'].sum()
        marker = " ***" if wr >= 0.50 and len(subset) >= 5 else (" **" if wr >= 0.45 and len(subset) >= 5 else "")
        print(f"{name:<55} {len(subset):>4} {wr:>5.1%} {avg_mfe:>7.3f} {avg_mae:>7.3f} {avg_pnl:>7.3f} {total_pnl:>7.1f}{marker}")
    elif len(subset) >= 1:
        print(f"{name:<55} {len(subset):>4} (too few)")

# ============================================================
# PART 2d: All winners detail
# ============================================================
print("\n" + "=" * 80)
print("PART 2d: ALL WINNING COUNTER-EMA REVs (sorted by P&L)")
print("=" * 80)

cols = ['symbol', 'date', 'time', 'direction', 'levels', 'vol', 'body', 'adx', 'vwap', 'ema', 'mfe', 'mae', 'net_pnl', 'level_type']
w_sorted = winners.sort_values('net_pnl', ascending=False)
print(w_sorted[cols].to_string(index=False))

print(f"\n--- ALL LOSING COUNTER-EMA REVs (sorted by P&L, worst first) ---")
l_sorted = losers.sort_values('net_pnl', ascending=True)
print(l_sorted[cols].to_string(index=False))

# ============================================================
# PART 3: IB data — find similar extended reversal setups
# ============================================================
print("\n" + "=" * 80)
print("PART 3: IB DATA — EXTENDED REVERSAL SETUPS ACROSS SYMBOLS")
print("=" * 80)

SYMBOLS = ['TSLA', 'NVDA', 'AMD', 'AAPL', 'AMZN', 'META', 'MSFT', 'GOOGL', 'SPY', 'QQQ']

all_setups = []

for sym in SYMBOLS:
    try:
        df_5m = load_ib(sym, '5_mins')
        df_1d = load_ib(sym, '1_day')
    except Exception as e:
        print(f"  {sym}: load error: {e}")
        continue

    df_5m_rth = df_5m.between_time('09:30', '16:00').copy()
    df_5m_rth['ema20'] = df_5m_rth['close'].ewm(span=20, adjust=False).mean()
    df_5m_rth['date_only'] = df_5m_rth.index.date

    dates = sorted(df_5m_rth['date_only'].unique())
    sym_count = 0

    for i in range(1, len(dates)):
        prev_date = dates[i-1]
        curr_date = dates[i]

        prev_day = df_5m_rth[df_5m_rth['date_only'] == prev_date]
        curr_day = df_5m_rth[df_5m_rth['date_only'] == curr_date]

        if len(prev_day) < 5 or len(curr_day) < 5:
            continue

        yest_h = prev_day['high'].max()
        yest_l = prev_day['low'].min()
        atr = yest_h - yest_l
        if atr <= 0:
            continue

        found_today = False

        # Look for bearish reversals at resistance
        for j in range(2, min(len(curr_day) - 3, 36)):  # first ~3 hrs
            if found_today:
                break
            bar = curr_day.iloc[j]
            bar_time = curr_day.index[j]

            # Only 9:45 to 12:00
            if bar_time.hour < 9 or (bar_time.hour == 9 and bar_time.minute < 45):
                continue
            if bar_time.hour >= 12:
                break

            # Touch or exceed yesterday's high
            if bar['high'] >= yest_h * 0.998:
                # EMA bullish (counter-EMA for bearish reversal)
                ema_bull = bar['close'] > bar['ema20']

                # Check for reversal in next 6 bars (30 min)
                future = curr_day.iloc[j+1:min(j+7, len(curr_day))]
                if len(future) < 2:
                    continue

                drop = bar['high'] - future['low'].min()
                drop_atr = drop / atr

                if drop_atr >= 0.15:
                    overext = (bar['high'] - yest_h) / atr
                    pre_bars = curr_day.iloc[:j+1]
                    rally = bar['high'] - pre_bars['low'].min()
                    rally_atr = rally / atr

                    # VWAP proxy: is price above mid-range?
                    day_range = curr_day.iloc[:j+1]
                    mid_price = (day_range['high'].max() + day_range['low'].min()) / 2
                    above_mid = bar['close'] > mid_price

                    all_setups.append({
                        'symbol': sym,
                        'date': str(curr_date),
                        'time': bar_time.strftime('%H:%M'),
                        'direction': 'bear',
                        'level': 'Yest H',
                        'level_val': yest_h,
                        'bar_high': bar['high'],
                        'overext_atr': overext,
                        'rally_atr': rally_atr,
                        'drop_atr': drop_atr,
                        'ema_counter': ema_bull,  # True = counter-EMA
                        'above_mid': above_mid,
                        'volume': bar.get('volume', 0),
                        'atr': atr,
                    })
                    sym_count += 1
                    found_today = True

        # Look for bullish reversals at support
        found_today_bull = False
        for j in range(2, min(len(curr_day) - 3, 36)):
            if found_today_bull:
                break
            bar = curr_day.iloc[j]
            bar_time = curr_day.index[j]

            if bar_time.hour < 9 or (bar_time.hour == 9 and bar_time.minute < 45):
                continue
            if bar_time.hour >= 12:
                break

            if bar['low'] <= yest_l * 1.002:
                ema_bear = bar['close'] < bar['ema20']

                future = curr_day.iloc[j+1:min(j+7, len(curr_day))]
                if len(future) < 2:
                    continue

                bounce = future['high'].max() - bar['low']
                bounce_atr = bounce / atr

                if bounce_atr >= 0.15:
                    overext = (yest_l - bar['low']) / atr
                    pre_bars = curr_day.iloc[:j+1]
                    selloff = pre_bars['high'].max() - bar['low']
                    selloff_atr = selloff / atr

                    day_range = curr_day.iloc[:j+1]
                    mid_price = (day_range['high'].max() + day_range['low'].min()) / 2
                    below_mid = bar['close'] < mid_price

                    all_setups.append({
                        'symbol': sym,
                        'date': str(curr_date),
                        'time': bar_time.strftime('%H:%M'),
                        'direction': 'bull',
                        'level': 'Yest L',
                        'level_val': yest_l,
                        'bar_low': bar['low'],
                        'overext_atr': overext,
                        'rally_atr': selloff_atr,
                        'drop_atr': bounce_atr,
                        'ema_counter': ema_bear,
                        'above_mid': below_mid,
                        'volume': bar.get('volume', 0),
                        'atr': atr,
                    })
                    sym_count += 1
                    found_today_bull = True

    print(f"  {sym}: {sym_count} level reversal setups found")

if all_setups:
    setup_df = pd.DataFrame(all_setups)
    print(f"\nTotal reversal setups: {len(setup_df)}")

    # Counter-EMA vs with-EMA
    counter = setup_df[setup_df['ema_counter']]
    with_ema = setup_df[~setup_df['ema_counter']]

    print(f"\n--- Counter-EMA setups (EMA aligned WITH move, AGAINST reversal) ---")
    print(f"  N={len(counter)}, Avg drop/bounce={counter['drop_atr'].mean():.3f} ATR")
    print(f"  Avg pre-move={counter['rally_atr'].mean():.3f} ATR")
    print(f"  Avg overextension={counter['overext_atr'].mean():.3f} ATR")

    print(f"\n--- With-EMA setups (EMA aligned WITH reversal) ---")
    print(f"  N={len(with_ema)}, Avg drop/bounce={with_ema['drop_atr'].mean():.3f} ATR")
    print(f"  Avg pre-move={with_ema['rally_atr'].mean():.3f} ATR")
    print(f"  Avg overextension={with_ema['overext_atr'].mean():.3f} ATR")

    # Are counter-EMA setups actually BIGGER reversals?
    print(f"\n--- Key insight: counter-EMA vs with-EMA reversal magnitude ---")
    if len(counter) > 0 and len(with_ema) > 0:
        print(f"  Counter-EMA avg reversal: {counter['drop_atr'].mean():.3f} ATR (N={len(counter)})")
        print(f"  With-EMA avg reversal: {with_ema['drop_atr'].mean():.3f} ATR (N={len(with_ema)})")
        print(f"  Counter-EMA has {'LARGER' if counter['drop_atr'].mean() > with_ema['drop_atr'].mean() else 'SMALLER'} reversals")

    # Pre-move size distribution
    print(f"\n--- Pre-move size (how far price ran before reversing) ---")
    for low, high, label in [(0, 0.2, '0-0.2 ATR'), (0.2, 0.4, '0.2-0.4'), (0.4, 0.6, '0.4-0.6'), (0.6, 1.0, '0.6-1.0'), (1.0, 5.0, '1.0+')]:
        subset = counter[counter['rally_atr'].between(low, high)]
        if len(subset) > 0:
            print(f"  {label}: N={len(subset)}, avg reversal={subset['drop_atr'].mean():.3f} ATR")

    # By time
    print(f"\n--- Counter-EMA setups by time ---")
    for h in range(9, 12):
        for m_start, m_end in [(0, 30), (30, 60)]:
            time_str = f"{h}:{m_start:02d}"
            subset = counter[counter['time'].apply(lambda t: int(t.split(':')[0]) == h and int(t.split(':')[1]) >= m_start and int(t.split(':')[1]) < m_end)]
            if len(subset) > 0:
                print(f"  {h}:{m_start:02d}-{h}:{m_end if m_end < 60 else 0:02d}: N={len(subset)}, avg rev={subset['drop_atr'].mean():.3f}")

    # Above mid (proxy for counter-VWAP)
    print(f"\n--- Counter-EMA + Above-mid (counter-VWAP proxy) ---")
    cm_above = counter[counter['above_mid']]
    cm_below = counter[~counter['above_mid']]
    if len(cm_above) > 0:
        print(f"  Above mid: N={len(cm_above)}, avg rev={cm_above['drop_atr'].mean():.3f} ATR")
    if len(cm_below) > 0:
        print(f"  Below mid: N={len(cm_below)}, avg rev={cm_below['drop_atr'].mean():.3f} ATR")

    # Top 20 biggest reversals
    print(f"\n--- Top 20 counter-EMA reversals by magnitude ---")
    top20 = counter.sort_values('drop_atr', ascending=False).head(20)
    print(top20[['symbol', 'date', 'time', 'direction', 'level', 'overext_atr', 'rally_atr', 'drop_atr', 'above_mid']].to_string(index=False))


# ============================================================
# PART 4: TV candle data — overextension and pre-move analysis
# ============================================================
print("\n" + "=" * 80)
print("PART 4: OVEREXTENSION & PRE-MOVE FROM TV 1-MIN DATA")
print("=" * 80)

# Load TV CSVs (Jan 26 - Feb 27)
import glob
tv_files = glob.glob(str(TV_DIR / "BATS_*, 1_*.csv"))
sym_to_file = {}
for f in tv_files:
    fname = Path(f).name
    for sym in ['SPY', 'AAPL', 'AMD', 'AMZN', 'GLD', 'GOOGL', 'META', 'MSFT', 'NVDA', 'QQQ', 'SLV', 'TSLA', 'TSM']:
        if sym in fname:
            sym_to_file[sym] = f
            break

tv_data = {}
for sym, fpath in sym_to_file.items():
    df = pd.read_csv(fpath)
    df['time'] = pd.to_datetime(df['time'])
    df = df.set_index('time')
    tv_data[sym] = df

# For each counter-EMA REV, compute pre-move (how far price ran in the direction that made EMA flip)
def compute_pre_move_1m(row):
    """Compute the price run INTO the level before the reversal signal."""
    sym = row['symbol']
    if sym not in tv_data:
        return np.nan, np.nan, np.nan

    df = tv_data[sym]
    try:
        sig_dt = pd.Timestamp(f"{row['date']} {row['time']}")
    except:
        return np.nan, np.nan, np.nan

    day_data = df[df.index.date == sig_dt.date()]
    if len(day_data) == 0:
        return np.nan, np.nan, np.nan

    rth = day_data.between_time('09:30', '16:00')
    pre = rth[rth.index <= sig_dt]
    if len(pre) < 5:
        return np.nan, np.nan, np.nan

    atr = row['atr'] if row['atr'] > 0 else 1
    vol_col = 'Volume' if 'Volume' in rth.columns else None

    if row['direction'] == 'bear':
        # Bear REV: price rallied up to resistance. Measure rally from local min
        lows = pre['low'].values
        # Find last significant local minimum (at least 3 bars back)
        min_idx = len(lows) - 1
        for k in range(len(lows)-1, max(0, len(lows)-60), -1):
            if lows[k] < lows[min_idx]:
                min_idx = k

        rally = pre.iloc[-1]['high'] - lows[min_idx]
        rally_atr = rally / atr
        bars_in_run = len(lows) - min_idx

        # Volume at signal vs average
        if vol_col:
            sig_vol = pre.iloc[-1][vol_col]
            avg_vol = pre.iloc[:-1][vol_col].mean() if len(pre) > 1 else sig_vol
            vol_ratio = sig_vol / avg_vol if avg_vol > 0 else 1
        else:
            vol_ratio = np.nan

        return rally_atr, bars_in_run, vol_ratio
    else:
        # Bull REV: price sold off to support
        highs = pre['high'].values
        max_idx = len(highs) - 1
        for k in range(len(highs)-1, max(0, len(highs)-60), -1):
            if highs[k] > highs[max_idx]:
                max_idx = k

        selloff = highs[max_idx] - pre.iloc[-1]['low']
        selloff_atr = selloff / atr
        bars_in_run = len(highs) - max_idx

        if vol_col:
            sig_vol = pre.iloc[-1][vol_col]
            avg_vol = pre.iloc[:-1][vol_col].mean() if len(pre) > 1 else sig_vol
            vol_ratio = sig_vol / avg_vol if avg_vol > 0 else 1
        else:
            vol_ratio = np.nan

        return selloff_atr, bars_in_run, vol_ratio

# Compute for all counter-EMA REVs
pre_data = counter_ema_rev.apply(lambda r: pd.Series(compute_pre_move_1m(r), index=['pre_move_atr', 'pre_move_bars', 'vol_spike_1m']), axis=1)
counter_ema_rev['pre_move_atr'] = pre_data['pre_move_atr']
counter_ema_rev['pre_move_bars'] = pre_data['pre_move_bars']
counter_ema_rev['vol_spike_1m'] = pre_data['vol_spike_1m']

valid = counter_ema_rev[counter_ema_rev['pre_move_atr'].notna()]
print(f"Signals with pre-move computed: {len(valid)} / {len(counter_ema_rev)}")

if len(valid) > 5:
    w = valid[valid['winner']]
    l = valid[~valid['winner']]
    print(f"\n--- Pre-Move Analysis ---")
    print(f"Winners: avg pre-move={w['pre_move_atr'].mean():.3f} ATR, bars={w['pre_move_bars'].mean():.0f}")
    print(f"Losers:  avg pre-move={l['pre_move_atr'].mean():.3f} ATR, bars={l['pre_move_bars'].mean():.0f}")

    print(f"\n--- By Pre-Move Size ---")
    for low, high, label in [(0, 0.2, '0-0.2 ATR'), (0.2, 0.4, '0.2-0.4'), (0.4, 0.6, '0.4-0.6'), (0.6, 1.0, '0.6-1.0'), (1.0, 10.0, '1.0+')]:
        subset = valid[(valid['pre_move_atr'] >= low) & (valid['pre_move_atr'] < high)]
        if len(subset) >= 2:
            wr = subset['winner'].mean()
            pnl = subset['net_pnl'].mean()
            print(f"  {label}: N={len(subset)}, Win={wr:.1%}, P&L={pnl:.3f}")

if len(valid) > 5 and 'vol_spike_1m' in valid.columns:
    v = valid[valid['vol_spike_1m'].notna()]
    if len(v) > 5:
        w = v[v['winner']]
        l = v[~v['winner']]
        print(f"\n--- Volume Spike at Signal ---")
        print(f"Winners: avg vol spike={w['vol_spike_1m'].mean():.2f}x")
        print(f"Losers:  avg vol spike={l['vol_spike_1m'].mean():.2f}x")

        for low, high, label in [(0, 1, '<1x'), (1, 2, '1-2x'), (2, 3, '2-3x'), (3, 5, '3-5x'), (5, 100, '5x+')]:
            subset = v[(v['vol_spike_1m'] >= low) & (v['vol_spike_1m'] < high)]
            if len(subset) >= 2:
                wr = subset['winner'].mean()
                pnl = subset['net_pnl'].mean()
                print(f"  {label}: N={len(subset)}, Win={wr:.1%}, P&L={pnl:.3f}")

# ============================================================
# PART 4b: Combined pre-move + other factors
# ============================================================
print("\n" + "=" * 80)
print("PART 4b: PRE-MOVE COMBINED WITH OTHER FACTORS")
print("=" * 80)

if len(valid) > 5:
    pm_combos = [
        ("Pre-move >= 0.3 ATR", valid['pre_move_atr'] >= 0.3),
        ("Pre-move >= 0.5 ATR", valid['pre_move_atr'] >= 0.5),
        ("Pre-move >= 0.3 + Counter-VWAP", (valid['pre_move_atr'] >= 0.3) & valid['counter_vwap']),
        ("Pre-move >= 0.5 + Counter-VWAP", (valid['pre_move_atr'] >= 0.5) & valid['counter_vwap']),
        ("Pre-move >= 0.3 + HIGH/LOW", (valid['pre_move_atr'] >= 0.3) & valid['level_type'].isin(['HIGH', 'LOW'])),
        ("Pre-move >= 0.5 + HIGH/LOW", (valid['pre_move_atr'] >= 0.5) & valid['level_type'].isin(['HIGH', 'LOW'])),
        ("Pre-move >= 0.3 + CtrVWAP + HIGH/LOW", (valid['pre_move_atr'] >= 0.3) & valid['counter_vwap'] & valid['level_type'].isin(['HIGH', 'LOW'])),
        ("Pre-move >= 0.5 + CtrVWAP + HIGH/LOW", (valid['pre_move_atr'] >= 0.5) & valid['counter_vwap'] & valid['level_type'].isin(['HIGH', 'LOW'])),
        ("Pre-move >= 0.5 + CtrVWAP + Morning", (valid['pre_move_atr'] >= 0.5) & valid['counter_vwap'] & valid['time_bucket'].isin(['9:30-10:00', '10:00-10:30'])),
        ("Pre-move >= 0.3 + ADX >= 25", (valid['pre_move_atr'] >= 0.3) & (valid['adx'] >= 25)),
        ("Pre-move >= 0.5 + Vol >= 2x", (valid['pre_move_atr'] >= 0.5) & (valid['vol'] >= 2.0)),
    ]

    print(f"\n{'Filter':<55} {'N':>4} {'Win%':>6} {'MFE':>7} {'P&L':>7} {'Total':>7}")
    print("-" * 95)
    for name, mask in pm_combos:
        subset = valid[mask]
        if len(subset) >= 2:
            wr = subset['winner'].mean()
            avg_mfe = subset['mfe'].mean()
            avg_pnl = subset['net_pnl'].mean()
            total = subset['net_pnl'].sum()
            marker = " ***" if wr >= 0.50 and len(subset) >= 5 else (" **" if wr >= 0.45 and len(subset) >= 5 else "")
            print(f"{name:<55} {len(subset):>4} {wr:>5.1%} {avg_mfe:>7.3f} {avg_pnl:>7.3f} {total:>7.1f}{marker}")
        elif len(subset) >= 1:
            print(f"{name:<55} {len(subset):>4} (too few)")

# ============================================================
# PART 5: EXECUTIVE SUMMARY
# ============================================================
print("\n" + "=" * 80)
print("PART 5: EXECUTIVE SUMMARY")
print("=" * 80)

print(f"""
COUNTER-EMA REV ANALYSIS SUMMARY
=================================
Total counter-EMA REVs: {len(counter_ema_rev)}
Overall win rate: {counter_ema_rev['winner'].mean():.1%}
Overall avg P&L: {counter_ema_rev['net_pnl'].mean():.3f} ATR
Total P&L: {counter_ema_rev['net_pnl'].sum():.1f} ATR

For comparison, EMA-aligned REVs:
  N={len(aligned_ema_rev)}, Win={aligned_ema_rev['winner'].mean():.1%}, Avg P&L={aligned_ema_rev['net_pnl'].mean():.3f}

Counter-VWAP analysis:
  Counter-VWAP REVs: N={len(counter_ema_rev[counter_ema_rev['counter_vwap']])}, Win={counter_ema_rev[counter_ema_rev['counter_vwap']]['winner'].mean():.1%}
  With-VWAP REVs:    N={len(counter_ema_rev[~counter_ema_rev['counter_vwap']])}, Win={counter_ema_rev[~counter_ema_rev['counter_vwap']]['winner'].mean():.1%}
""")

print("Done!")
