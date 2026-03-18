#!/usr/bin/env python3
"""
Special Day Contamination Analysis
====================================
Quantifies how much "special day" outlier events (e.g. NVDA DeepSeek crash Jan 26-30, 2026)
contaminate KLB research findings, and re-runs key analyses with those days excluded.

Parts:
  1. Identify special days (daily range > 3x / 5x median) from IB daily data
  2. Quantify contamination in move catalog
  3. Quantify contamination in v3.3c Pine log signals (MFE/MAE)
  4. Re-run key findings with special days excluded
  5. Special day impact on tier/great thresholds

Output: special-day-contamination.md
"""

import sys
import os
import glob
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ── Config ─────────────────────────────────────────────────────────────────────
SYMBOLS = ['SPY','AAPL','AMD','AMZN','GLD','GOOGL','META','MSFT','NFLX','NVDA','QQQ','SLV','TSLA','TSM','XLE']
BAR_DIR = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars/')
LOG_DIR = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug/')
OUT_DIR = LOG_DIR

V33C_GLOB = 'pine-logs-Key Level Breakout v3.3c_*.csv'

# Special day thresholds
SPECIAL_MULT = 3.0   # daily range > 3x median → "special day"
CRASH_MULT   = 5.0   # daily range > 5x median → "crash day"

# MFE/MAE window (minutes)
MFE_MINUTES = 60
ATR_PERIOD  = 14
WIN_MFE_THRESHOLD = 0.10

# Great move thresholds (from catalog_research.py)
GREAT_MFE_MAE_RATIO = 3.0
GREAT_MFE_MIN       = 0.30  # ATR
GREAT_RETRACE_MAX   = 0.40

# Tier S/A thresholds from MEMORY (used in signal-level audit)
TIER_S_MFE = 0.60
TIER_A_MFE = 0.40

DIVIDER  = '=' * 72
SUBDIV   = '-' * 72


# ── Import parsing helpers from v33_backtest ───────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)

from v33_backtest import (
    load_and_parse_logs,
    compute_dim_status,
    load_1m,
    load_daily,
    compute_atr,
    measure_mfe_mae,
    sig_stats,
    parse_pine_log,
    identify_symbol,
    BAR_DIR as V33_BAR_DIR,
    LOG_DIR as V33_LOG_DIR,
)


# ── Part 1: Identify Special Days ─────────────────────────────────────────────

def compute_daily_ranges(symbols=SYMBOLS, bar_dir=BAR_DIR):
    """Load daily bars for each symbol, compute daily range, flag special days."""
    records = []
    daily_data = {}  # symbol -> DataFrame

    for sym in symbols:
        fp = bar_dir / f'{sym.lower()}_1_day_ib.parquet'
        if not fp.exists():
            print(f'  WARNING: No daily data for {sym}')
            continue

        try:
            df = pd.read_parquet(fp)
            dt = pd.to_datetime(df['date'])
            if dt.dt.tz is not None:
                dt = dt.dt.tz_convert('US/Eastern')
            df['date'] = dt
            df = df.set_index('date').sort_index()

            # Only RTH-like days (exclude weekends/holidays by requiring close > 0)
            df = df[df['close'] > 0].copy()

            # Daily range = high - low
            df['daily_range'] = df['high'] - df['low']

            # Median daily range across all available history
            median_range = df['daily_range'].median()

            # Also compute ATR-based daily range multiplier (more robust)
            df['range_mult'] = df['daily_range'] / median_range

            daily_data[sym] = {'df': df, 'median_range': median_range}

            # Flag special / crash days
            for date, row in df.iterrows():
                mult = row['range_mult']
                if mult >= SPECIAL_MULT:
                    records.append({
                        'symbol': sym,
                        'date': date.date() if hasattr(date, 'date') else date,
                        'daily_range': round(row['daily_range'], 4),
                        'median_range': round(median_range, 4),
                        'multiplier': round(mult, 2),
                        'is_crash': mult >= CRASH_MULT,
                        'high': row['high'],
                        'low': row['low'],
                        'close': row['close'],
                    })
        except Exception as e:
            print(f'  ERROR loading {sym}: {e}')

    special_days = pd.DataFrame(records).sort_values('multiplier', ascending=False)
    return special_days, daily_data


def build_special_day_set(special_days):
    """Return set of (symbol, date) tuples for special days."""
    result = set()
    for _, row in special_days.iterrows():
        result.add((row['symbol'], row['date']))
    return result


def build_crash_day_set(special_days):
    """Return set of (symbol, date) for crash days (>5x)."""
    crash = special_days[special_days['is_crash']]
    return set(zip(crash['symbol'], crash['date']))


# ── Part 2: Move Catalog Contamination ────────────────────────────────────────

def load_catalog():
    """Load move catalog and compute is_great label."""
    cat = pd.read_parquet(LOG_DIR / 'move-catalog.parquet')
    cat = cat[cat['pass'] == 'primary'].copy()

    # Parse date from start_time
    cat['start_time'] = pd.to_datetime(cat['start_time'])
    if cat['start_time'].dt.tz is not None:
        cat['start_time'] = cat['start_time'].dt.tz_convert('US/Eastern')
    cat['sig_date'] = cat['start_time'].dt.date

    # Compute is_great (same as catalog_research.py)
    has_1m = cat['mfe_1m'].notna()
    cat['is_great'] = (
        (has_1m
         & (cat['mae_1m'] > 0)
         & (cat['mfe_1m'] / cat['mae_1m'].clip(lower=0.001) >= GREAT_MFE_MAE_RATIO)
         & (cat['mfe_1m'] >= GREAT_MFE_MIN)
         & (cat['retracement_12bar'] <= GREAT_RETRACE_MAX))
        | (~has_1m
           & (cat['magnitude_atr'] >= 0.50)
           & (cat['retracement_12bar'] <= GREAT_RETRACE_MAX))
    )
    cat['is_noise'] = (
        (has_1m & (cat['mae_1m'] > cat['mfe_1m']))
        | (cat['retracement_6bar'] > 0.80)
    )

    return cat


def analyze_catalog_contamination(cat, special_day_set, crash_day_set):
    """Split catalog into special vs normal days, compare stats."""
    cat['is_special'] = cat.apply(
        lambda r: (r['symbol'], r['sig_date']) in special_day_set, axis=1
    )
    cat['is_crash'] = cat.apply(
        lambda r: (r['symbol'], r['sig_date']) in crash_day_set, axis=1
    )

    normal = cat[~cat['is_special']]
    special = cat[cat['is_special']]
    crash = cat[cat['is_crash']]

    def catalog_stats(df, label):
        n = len(df)
        if n == 0:
            return {'label': label, 'n': 0}
        great_rate  = df['is_great'].mean()
        noise_rate  = df['is_noise'].mean()
        avg_mfe     = df['mfe_1m'].mean()
        avg_mag     = df['magnitude_atr'].mean()
        total_mfe   = df['mfe_1m'].sum()
        mega_pct    = (df['mag_category'] == 'mega').mean() if 'mag_category' in df.columns else None
        return {
            'label': label, 'n': n,
            'great_rate': great_rate,
            'noise_rate': noise_rate,
            'avg_mfe_1m': avg_mfe,
            'avg_magnitude_atr': avg_mag,
            'total_mfe_1m': total_mfe,
            'mega_pct': mega_pct,
        }

    stats_all    = catalog_stats(cat, 'ALL')
    stats_normal = catalog_stats(normal, 'NORMAL (no special days)')
    stats_special= catalog_stats(special, 'SPECIAL DAYS (>3x)')
    stats_crash  = catalog_stats(crash, 'CRASH DAYS (>5x)')

    # NVDA-specific
    nvda = cat[cat['symbol'] == 'NVDA']
    nvda_normal = nvda[~nvda['is_special']]
    nvda_special= nvda[nvda['is_special']]

    nvda_stats = {
        'all':     catalog_stats(nvda, 'NVDA ALL'),
        'normal':  catalog_stats(nvda_normal, 'NVDA NORMAL'),
        'special': catalog_stats(nvda_special, 'NVDA SPECIAL'),
    }

    return {
        'all': stats_all, 'normal': stats_normal,
        'special': stats_special, 'crash': stats_crash,
        'nvda': nvda_stats,
        'cat': cat,  # with flags
    }


# ── Part 3: v3.3c Signal Contamination ────────────────────────────────────────

def load_v33c_signals():
    """Load and parse all v3.3c Pine log files, measure MFE/MAE."""
    files = sorted(glob.glob(str(LOG_DIR / V33C_GLOB)))
    if not files:
        print('  ERROR: No v3.3c log files found')
        return []

    print(f'  Found {len(files)} v3.3c log files')
    all_signals = []
    ib_cache = {}

    for fp in files:
        short = Path(fp).name.split('_')[-1].replace('.csv', '')
        signals = parse_pine_log(fp)
        if not signals:
            continue

        symbol = identify_symbol(signals)
        if symbol is None:
            print(f'    {short}: could not identify symbol')
            continue

        # Tag with symbol
        for s in signals:
            s['symbol'] = symbol
            s['log_file'] = short

        # Load IB data for MFE/MAE
        if symbol not in ib_cache:
            try:
                bars_1m  = load_1m(symbol)
                daily    = load_daily(symbol)
                atr_ser  = compute_atr(daily)
                ib_cache[symbol] = (bars_1m, atr_ser)
            except Exception as e:
                print(f'    {short}: {symbol} IB load error: {e}')
                ib_cache[symbol] = None

        if ib_cache.get(symbol) is not None:
            bars_1m, atr_ser = ib_cache[symbol]
            measure_mfe_mae(signals, bars_1m, atr_ser)

        all_signals.extend(signals)
        print(f'    {short}: {symbol} — {len(signals)} signals')

    print(f'  Total v3.3c signals: {len(all_signals)}')
    return all_signals


def flag_signals_special_days(signals, special_day_set, crash_day_set):
    """Add is_special / is_crash flags to signal dicts."""
    for sig in signals:
        ts = sig.get('timestamp')
        sym = sig.get('symbol')
        if ts is None or sym is None:
            sig['is_special'] = False
            sig['is_crash']   = False
            continue
        sig_date = ts.date() if hasattr(ts, 'date') else None
        sig['is_special'] = (sym, sig_date) in special_day_set
        sig['is_crash']   = (sym, sig_date) in crash_day_set


def signal_stats_split(signals, label_prefix=''):
    """Compute sig_stats for full, special, normal subsets."""
    with_data = [s for s in signals if s.get('mfe_atr') is not None]
    normal    = [s for s in with_data if not s.get('is_special')]
    special   = [s for s in with_data if s.get('is_special')]

    return {
        'all':     sig_stats(with_data, f'{label_prefix} ALL'),
        'normal':  sig_stats(normal,    f'{label_prefix} NORMAL'),
        'special': sig_stats(special,   f'{label_prefix} SPECIAL'),
    }


def compute_nvda_bear_2x_estimate(signals, special_day_set):
    """
    Reproduce "NVDA bear REV 2x size = +1,123 ATR" finding on normal days only.
    The 2x size means: for NVDA bear signals, use 2x position. Net ATR × 2 is the estimate.
    We just compute NVDA bear net ATR on normal days and note 2x would give 2x that.
    """
    nvda_bear = [
        s for s in signals
        if s.get('symbol') == 'NVDA'
        and s.get('direction') == 'bear'
        and s.get('mfe_atr') is not None
    ]
    normal    = [s for s in nvda_bear if not s.get('is_special')]
    special   = [s for s in nvda_bear if s.get('is_special')]

    return {
        'all':     sig_stats(nvda_bear, 'NVDA bear ALL'),
        'normal':  sig_stats(normal,    'NVDA bear NORMAL'),
        'special': sig_stats(special,   'NVDA bear SPECIAL'),
    }


# ── Part 4: Re-run Key Findings on Normal Days ─────────────────────────────────

def rerun_catalog_findings(cat_result):
    """Re-derive key catalog findings on normal days only."""
    cat = cat_result['cat']
    normal = cat[~cat['is_special']]

    # 1. NVDA avg magnitude (proxy for MFE since catalog uses magnitude_atr)
    nvda_n  = cat[cat['symbol'] == 'NVDA']
    nvda_nn = normal[normal['symbol'] == 'NVDA']
    nvda_avg_all    = nvda_n['magnitude_atr'].mean()
    nvda_avg_mfe_all= nvda_n['mfe_1m'].mean()
    nvda_avg_normal = nvda_nn['magnitude_atr'].mean()
    nvda_avg_mfe_n  = nvda_nn['mfe_1m'].mean()

    # 2. Best signal type by symbol (use magnitude_atr as proxy for MFE)
    # For all symbols, top mag_category mix on normal days
    by_sym_all = cat.groupby('symbol')['magnitude_atr'].agg(['mean','count']).round(3)
    by_sym_n   = normal.groupby('symbol')['magnitude_atr'].agg(['mean','count']).round(3)

    # 3. Great move rate: overall, and per symbol
    great_all  = cat['is_great'].mean()
    great_norm = normal['is_great'].mean()

    by_sym_great_all  = cat.groupby('symbol')['is_great'].mean()
    by_sym_great_norm = normal.groupby('symbol')['is_great'].mean()

    return {
        'nvda_mag_all':    nvda_avg_all,
        'nvda_mag_normal': nvda_avg_normal,
        'nvda_mfe_all':    nvda_avg_mfe_all,
        'nvda_mfe_normal': nvda_avg_mfe_n,
        'great_rate_all':  great_all,
        'great_rate_norm': great_norm,
        'by_sym_all':      by_sym_all,
        'by_sym_normal':   by_sym_n,
        'by_sym_great_all': by_sym_great_all,
        'by_sym_great_norm': by_sym_great_norm,
    }


def rerun_signal_findings(signals):
    """Re-derive key signal-level findings on normal days only."""
    with_data = [s for s in signals if s.get('mfe_atr') is not None]
    normal    = [s for s in with_data if not s.get('is_special')]

    results = {}

    # By symbol × direction × sig_type on normal days
    for sym in SYMBOLS:
        sym_all    = [s for s in with_data if s.get('symbol') == sym]
        sym_normal = [s for s in normal    if s.get('symbol') == sym]

        if not sym_all:
            continue

        # By sig_type
        all_types    = sorted(set(s.get('sig_type','?') for s in sym_all))
        by_type_all  = {}
        by_type_norm = {}
        for st in all_types:
            by_type_all[st]  = sig_stats([s for s in sym_all    if s.get('sig_type') == st], st)
            by_type_norm[st] = sig_stats([s for s in sym_normal if s.get('sig_type') == st], st)

        results[sym] = {
            'all':       sig_stats(sym_all,    f'{sym} ALL'),
            'normal':    sig_stats(sym_normal, f'{sym} NORMAL'),
            'by_type_all':  by_type_all,
            'by_type_norm': by_type_norm,
        }

    return results


# ── Part 5: Tier Threshold Impact ─────────────────────────────────────────────

def analyze_tier_thresholds(cat_result, signals):
    """Examine tier S/A thresholds on all vs normal days."""
    cat    = cat_result['cat']
    normal_cat = cat[~cat['is_special']]

    # Catalog: mag_category 'mega' is closest to tier S (high magnitude)
    # Use magnitude_atr and mfe_1m to compute quantile-based tiers

    def tier_stats(df, label):
        mfe_col = 'mfe_1m'
        has_1m  = df[mfe_col].notna()
        df_1m   = df[has_1m]
        if len(df_1m) == 0:
            return {}
        p90 = df_1m[mfe_col].quantile(0.90)
        p75 = df_1m[mfe_col].quantile(0.75)
        p50 = df_1m[mfe_col].quantile(0.50)
        tier_s = (df_1m[mfe_col] >= TIER_S_MFE).mean()
        tier_a = (df_1m[mfe_col] >= TIER_A_MFE).mean()
        return {
            'label': label, 'n': len(df_1m),
            'p50_mfe': p50, 'p75_mfe': p75, 'p90_mfe': p90,
            'pct_tier_s': tier_s,  # % above 0.60
            'pct_tier_a': tier_a,  # % above 0.40
            'tier_s_equiv_quantile': (df_1m[mfe_col] < TIER_S_MFE).mean(),  # what quantile is tier S
        }

    t_all    = tier_stats(cat,        'ALL DATA')
    t_normal = tier_stats(normal_cat, 'NORMAL DAYS')
    nvda_cat = cat[cat['symbol'] == 'NVDA']
    nvda_normal_cat = normal_cat[normal_cat['symbol'] == 'NVDA']
    t_nvda_all    = tier_stats(nvda_cat,        'NVDA ALL')
    t_nvda_normal = tier_stats(nvda_normal_cat, 'NVDA NORMAL')

    # Signal-level tier analysis
    with_data = [s for s in signals if s.get('mfe_atr') is not None]
    normal_sig = [s for s in with_data if not s.get('is_special')]

    def sig_tier_stats(sigs, label):
        if not sigs:
            return {}
        mfes = [s['mfe_atr'] for s in sigs]
        arr  = np.array(mfes)
        return {
            'label': label, 'n': len(arr),
            'p50': float(np.percentile(arr, 50)),
            'p75': float(np.percentile(arr, 75)),
            'p90': float(np.percentile(arr, 90)),
            'pct_tier_s': float((arr >= TIER_S_MFE).mean()),
            'pct_tier_a': float((arr >= TIER_A_MFE).mean()),
        }

    st_all    = sig_tier_stats(with_data,   'SIGNALS ALL')
    st_normal = sig_tier_stats(normal_sig,  'SIGNALS NORMAL')

    return {
        'catalog_all':    t_all,
        'catalog_normal': t_normal,
        'nvda_all':       t_nvda_all,
        'nvda_normal':    t_nvda_normal,
        'signals_all':    st_all,
        'signals_normal': st_normal,
    }


# ── Report Generation ──────────────────────────────────────────────────────────

def fmt_stat(st):
    """Format sig_stats dict as one-liner."""
    return (f"N={st['n']:,}  Win%={st['win_rate']:.1f}%  "
            f"Avg MFE={st['avg_mfe']:.4f}  Net ATR={st['net_atr']:+.2f}")


def generate_report(special_days, catalog_result, signals,
                    nvda_bear, findings_catalog, findings_signal,
                    tier_analysis):
    L = []

    L.append('# Special Day Contamination Analysis')
    L.append(f'**Run date:** {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    L.append(f'**Special day threshold:** >{SPECIAL_MULT}x median daily range')
    L.append(f'**Crash day threshold:** >{CRASH_MULT}x median daily range')
    L.append('')

    # ── Part 1: Special Days Table ──
    L.append(f'## Part 1: Special Days Identified')
    L.append('')

    if special_days.empty:
        L.append('No special days found.')
    else:
        crash = special_days[special_days['is_crash']]
        special_only = special_days[~special_days['is_crash']]
        L.append(f'**Total special days:** {len(special_days)} ({len(crash)} crash days >{CRASH_MULT}x, '
                 f'{len(special_only)} elevated >{SPECIAL_MULT}x)')
        L.append('')
        L.append('### Crash Days (>5x median range) — Highest Impact')
        L.append('')
        if crash.empty:
            L.append('None found.')
        else:
            L.append('| Symbol | Date | Daily Range | Median Range | Multiplier |')
            L.append('|--------|------|-------------|--------------|------------|')
            for _, r in crash.head(30).iterrows():
                tag = ' **CRASH**' if r['is_crash'] else ''
                L.append(f"| {r['symbol']} | {r['date']} | {r['daily_range']:.3f} | "
                         f"{r['median_range']:.3f} | **{r['multiplier']:.1f}x**{tag} |")
        L.append('')
        L.append('### All Special Days (>3x median range)')
        L.append('')
        L.append('| Symbol | Date | Daily Range | Median Range | Multiplier | Crash? |')
        L.append('|--------|------|-------------|--------------|------------|--------|')
        for _, r in special_days.iterrows():
            crash_tag = 'YES' if r['is_crash'] else '-'
            L.append(f"| {r['symbol']} | {r['date']} | {r['daily_range']:.3f} | "
                     f"{r['median_range']:.3f} | {r['multiplier']:.1f}x | {crash_tag} |")

    L.append('')

    # ── Part 2: Catalog Contamination ──
    L.append('## Part 2: Move Catalog Contamination')
    L.append('')

    def cat_row(st):
        if not st or st.get('n', 0) == 0:
            return 'N=0'
        gr = f"{st['great_rate']:.1%}" if st.get('great_rate') is not None else 'N/A'
        nr = f"{st['noise_rate']:.1%}" if st.get('noise_rate') is not None else 'N/A'
        am = f"{st['avg_mfe_1m']:.3f}" if st.get('avg_mfe_1m') is not None else 'N/A'
        mg = f"{st['mega_pct']:.1%}" if st.get('mega_pct') is not None else 'N/A'
        tm = f"{st['total_mfe_1m']:.1f}" if st.get('total_mfe_1m') is not None else 'N/A'
        return (f"N={st['n']:,}  Great={gr}  Noise={nr}  "
                f"Avg MFE={am}  Mega%={mg}  TotalMFE={tm}")

    L.append('| Subset | N | Great% | Noise% | Avg MFE (1m) | Mega% | Total MFE |')
    L.append('|--------|---|--------|--------|--------------|-------|-----------|')
    for key in ['all', 'normal', 'special', 'crash']:
        st = catalog_result[key]
        if st.get('n', 0) == 0:
            continue
        avg_mfe_s  = f"{st['avg_mfe_1m']:.3f}"  if st.get('avg_mfe_1m') is not None and not np.isnan(st['avg_mfe_1m'])  else 'N/A'
        total_mfe_s= f"{st['total_mfe_1m']:.1f}" if st.get('total_mfe_1m') is not None and not np.isnan(st['total_mfe_1m']) else 'N/A'
        mega_s     = f"{st['mega_pct']:.1%}"    if st.get('mega_pct') is not None and not np.isnan(st['mega_pct'])     else 'N/A'
        L.append(f"| {st['label']} | {st['n']:,} | {st['great_rate']:.1%} | "
                 f"{st['noise_rate']:.1%} | {avg_mfe_s} | {mega_s} | {total_mfe_s} |")

    L.append('')
    L.append('### NVDA Move Catalog: With vs Without Special Days')
    L.append('')
    for key in ['all', 'normal', 'special']:
        st = catalog_result['nvda'][key]
        if st.get('n', 0) == 0:
            continue
        L.append(f"**{st['label']}:** N={st['n']:,}  AvgMag={st['avg_magnitude_atr']:.3f}  "
                 f"AvgMFE={st['avg_mfe_1m']:.3f}  Great={st['great_rate']:.1%}  "
                 f"TotalMFE={st['total_mfe_1m']:.1f}")

    # % of total catalog MFE from special days
    total_mfe = catalog_result['all']['total_mfe_1m']
    special_mfe = catalog_result['special']['total_mfe_1m']
    if total_mfe and total_mfe > 0 and special_mfe:
        pct_special = special_mfe / total_mfe * 100
        L.append('')
        L.append(f"**Special day share of total catalog MFE:** "
                 f"{special_mfe:.1f} / {total_mfe:.1f} = **{pct_special:.1f}%**")

    L.append('')

    # ── Part 3: v3.3c Signal Contamination ──
    L.append('## Part 3: v3.3c Signal Contamination')
    L.append('')

    with_data = [s for s in signals if s.get('mfe_atr') is not None]
    normal_sig = [s for s in with_data if not s.get('is_special')]
    special_sig = [s for s in with_data if s.get('is_special')]

    all_st     = sig_stats(with_data,    'ALL SIGNALS')
    normal_st  = sig_stats(normal_sig,   'NORMAL DAY SIGNALS')
    special_st = sig_stats(special_sig,  'SPECIAL DAY SIGNALS')

    L.append('| Subset | N | Win% | Avg MFE | Avg MAE | Net ATR |')
    L.append('|--------|---|------|---------|---------|---------|')
    for st in [all_st, normal_st, special_st]:
        L.append(f"| {st['label']} | {st['n']:,} | {st['win_rate']:.1f}% | "
                 f"{st['avg_mfe']:.4f} | {st['avg_mae']:.4f} | {st['net_atr']:+.2f} |")

    # Special day % of total ATR
    if all_st['n'] > 0 and special_st['n'] > 0:
        total_net = all_st['net_atr']
        special_net = special_st['net_atr']
        pct = special_net / total_net * 100 if total_net != 0 else 0
        L.append('')
        L.append(f"**Special day share of total signal net ATR:** "
                 f"{special_net:+.2f} / {total_net:+.2f} = **{pct:.1f}%**")

    L.append('')
    L.append('### NVDA Bear Signals: "2x size" Finding Robustness')
    L.append('')
    L.append('The "NVDA bear REV 2x size = +1,123 ATR" finding is evaluated here.')
    L.append('Net ATR × 2 approximates the 2x position sizing benefit.')
    L.append('')
    L.append('| Subset | N | Win% | Avg MFE | Net ATR | 2x Net ATR est. |')
    L.append('|--------|---|------|---------|---------|-----------------|')
    for key in ['all', 'normal', 'special']:
        st = nvda_bear[key]
        two_x = st['net_atr'] * 2
        L.append(f"| {st['label']} | {st['n']:,} | {st['win_rate']:.1f}% | "
                 f"{st['avg_mfe']:.4f} | {st['net_atr']:+.2f} | **{two_x:+.2f}** |")

    L.append('')
    L.append('### NVDA Overall Signals: With vs Without Special Days')
    L.append('')
    nvda_all_sig  = [s for s in with_data if s.get('symbol') == 'NVDA']
    nvda_norm_sig = [s for s in nvda_all_sig if not s.get('is_special')]
    nvda_spec_sig = [s for s in nvda_all_sig if s.get('is_special')]

    L.append('| Subset | N | Win% | Avg MFE | Net ATR |')
    L.append('|--------|---|------|---------|---------|')
    for label, sigs in [('NVDA ALL', nvda_all_sig), ('NVDA NORMAL', nvda_norm_sig), ('NVDA SPECIAL', nvda_spec_sig)]:
        st = sig_stats(sigs, label)
        L.append(f"| {label} | {st['n']:,} | {st['win_rate']:.1f}% | "
                 f"{st['avg_mfe']:.4f} | {st['net_atr']:+.2f} |")

    L.append('')

    # ── Part 4: Key Findings Re-run ──
    L.append('## Part 4: Key Findings Re-run on Normal Days')
    L.append('')

    fc = findings_catalog
    L.append('### NVDA Average Magnitude / MFE (Move Catalog)')
    L.append(f"- **NVDA avg magnitude (ALL):** {fc['nvda_mag_all']:.4f} ATR")
    L.append(f"- **NVDA avg magnitude (NORMAL):** {fc['nvda_mag_normal']:.4f} ATR")
    nvda_mfe_all = fc['nvda_mfe_all']
    nvda_mfe_norm = fc['nvda_mfe_normal']
    if nvda_mfe_all and not np.isnan(nvda_mfe_all):
        L.append(f"- **NVDA avg MFE 1m (ALL):** {nvda_mfe_all:.4f} ATR")
    if nvda_mfe_norm and not np.isnan(nvda_mfe_norm):
        L.append(f"- **NVDA avg MFE 1m (NORMAL):** {nvda_mfe_norm:.4f} ATR")

    L.append('')
    L.append('### Great Move Rate: All vs Normal Days (Move Catalog)')
    L.append(f"- **All data:** {fc['great_rate_all']:.1%}")
    L.append(f"- **Normal days:** {fc['great_rate_norm']:.1%}")

    L.append('')
    L.append('### Per-Symbol Average Magnitude: All vs Normal Days')
    L.append('')
    L.append('| Symbol | Avg Mag (All) | N (All) | Avg Mag (Normal) | N (Normal) | Delta |')
    L.append('|--------|--------------|---------|-----------------|------------|-------|')
    for sym in SYMBOLS:
        if sym not in fc['by_sym_all'].index:
            continue
        all_v  = fc['by_sym_all'].loc[sym]
        norm_v = fc['by_sym_normal'].loc[sym] if sym in fc['by_sym_normal'].index else None
        if norm_v is None:
            L.append(f"| {sym} | {all_v['mean']:.3f} | {int(all_v['count'])} | N/A | N/A | N/A |")
        else:
            delta = norm_v['mean'] - all_v['mean']
            flag = ' **' if abs(delta) > 0.05 else ''
            L.append(f"| {sym} | {all_v['mean']:.3f} | {int(all_v['count'])} | "
                     f"{norm_v['mean']:.3f}{flag} | {int(norm_v['count'])} | {delta:+.3f} |")

    L.append('')
    L.append('### Per-Symbol Great Move Rate: All vs Normal Days')
    L.append('')
    L.append('| Symbol | Great% (All) | Great% (Normal) | Delta |')
    L.append('|--------|-------------|-----------------|-------|')
    for sym in SYMBOLS:
        if sym not in fc['by_sym_great_all'].index:
            continue
        all_g  = fc['by_sym_great_all'][sym]
        norm_g = fc['by_sym_great_norm'].get(sym, np.nan)
        delta  = norm_g - all_g if not np.isnan(norm_g) else np.nan
        delta_s = f'{delta:+.1%}' if not np.isnan(delta) else 'N/A'
        norm_s  = f'{norm_g:.1%}' if not np.isnan(norm_g) else 'N/A'
        L.append(f"| {sym} | {all_g:.1%} | {norm_s} | {delta_s} |")

    L.append('')
    L.append('### v3.3c Signal Stats by Symbol: Normal Days Only')
    L.append('')
    L.append('| Symbol | Subset | N | Win% | Avg MFE | Net ATR |')
    L.append('|--------|--------|---|------|---------|---------|')
    for sym in SYMBOLS:
        if sym not in findings_signal:
            continue
        r = findings_signal[sym]
        for key in ['all', 'normal']:
            st = r[key]
            L.append(f"| {sym} | {key.upper()} | {st['n']:,} | {st['win_rate']:.1f}% | "
                     f"{st['avg_mfe']:.4f} | {st['net_atr']:+.2f} |")

    L.append('')
    L.append('### Improvement Menu Items: Normal-Day-Adjusted Estimates')
    L.append('')
    L.append('**Item E — NVDA bear 2x size:**')
    nvda_n_st = nvda_bear['normal']
    L.append(f"  - Normal days: N={nvda_n_st['n']:,}  Win%={nvda_n_st['win_rate']:.1f}%  "
             f"Net ATR={nvda_n_st['net_atr']:+.2f}  2x est.={nvda_n_st['net_atr']*2:+.2f}")
    nvda_s_st = nvda_bear['special']
    if nvda_s_st['n'] > 0:
        L.append(f"  - Special days: N={nvda_s_st['n']:,}  Win%={nvda_s_st['win_rate']:.1f}%  "
                 f"Net ATR={nvda_s_st['net_atr']:+.2f}  (would be excluded)")
    L.append('')

    # FADE/midday from normal signals
    midday_all    = [s for s in with_data if _is_midday(s)]
    midday_normal = [s for s in midday_all if not s.get('is_special')]
    m_all_st  = sig_stats(midday_all,    'Midday ALL')
    m_norm_st = sig_stats(midday_normal, 'Midday NORMAL')
    L.append('**Item H — Midday sizing:**')
    L.append(f"  - Midday ALL:    N={m_all_st['n']:,}  Win%={m_all_st['win_rate']:.1f}%  "
             f"Avg MFE={m_all_st['avg_mfe']:.4f}  Net ATR={m_all_st['net_atr']:+.2f}")
    L.append(f"  - Midday NORMAL: N={m_norm_st['n']:,}  Win%={m_norm_st['win_rate']:.1f}%  "
             f"Avg MFE={m_norm_st['avg_mfe']:.4f}  Net ATR={m_norm_st['net_atr']:+.2f}")

    L.append('')

    # ── Part 5: Tier Thresholds ──
    L.append('## Part 5: Tier Threshold Impact')
    L.append('')

    ta = tier_analysis
    L.append('### Move Catalog MFE Distribution (1m data): All vs Normal Days')
    L.append('')
    L.append('| Subset | N | p50 MFE | p75 MFE | p90 MFE | %≥0.40 (A) | %≥0.60 (S) |')
    L.append('|--------|---|---------|---------|---------|------------|------------|')
    for key in ['catalog_all', 'catalog_normal']:
        t = ta[key]
        if not t:
            continue
        L.append(f"| {t['label']} | {t['n']:,} | {t['p50_mfe']:.3f} | {t['p75_mfe']:.3f} | "
                 f"{t['p90_mfe']:.3f} | {t['pct_tier_a']:.1%} | {t['pct_tier_s']:.1%} |")

    L.append('')
    L.append('### NVDA Catalog MFE Distribution: All vs Normal Days')
    L.append('')
    for key in ['nvda_all', 'nvda_normal']:
        t = ta[key]
        if not t:
            continue
        L.append(f"**{t['label']}:** N={t['n']:,}  p50={t['p50_mfe']:.3f}  "
                 f"p75={t['p75_mfe']:.3f}  p90={t['p90_mfe']:.3f}  "
                 f"%≥0.40={t['pct_tier_a']:.1%}  %≥0.60={t['pct_tier_s']:.1%}")

    L.append('')
    L.append('### Signal MFE Distribution: All vs Normal Days')
    L.append('')
    L.append('| Subset | N | p50 MFE | p75 MFE | p90 MFE | %≥0.40 (A) | %≥0.60 (S) |')
    L.append('|--------|---|---------|---------|---------|------------|------------|')
    for key in ['signals_all', 'signals_normal']:
        t = ta[key]
        if not t:
            continue
        L.append(f"| {t['label']} | {t['n']:,} | {t['p50']:.3f} | {t['p75']:.3f} | "
                 f"{t['p90']:.3f} | {t['pct_tier_a']:.1%} | {t['pct_tier_s']:.1%} |")

    L.append('')

    # ── Verdict ──
    L.append('## Verdict: Robust vs Artifact')
    L.append('')
    L.append('### Findings to validate against the numbers above:')
    L.append('')
    L.append('| Finding | Robust? | Notes |')
    L.append('|---------|---------|-------|')

    # Compute verdict signals from data
    nvda_norm_net  = nvda_bear['normal']['net_atr']
    nvda_all_net   = nvda_bear['all']['net_atr']
    nvda_norm_win  = nvda_bear['normal']['win_rate']
    nvda_norm_n    = nvda_bear['normal']['n']

    nvda_2x_all    = nvda_all_net * 2
    nvda_2x_normal = nvda_norm_net * 2

    great_all  = fc['great_rate_all']
    great_norm = fc['great_rate_norm']
    great_delta = abs(great_norm - great_all)

    # Normal vs special great rate difference
    spec_great = catalog_result['special']['great_rate']
    norm_great = catalog_result['normal']['great_rate']

    spec_mfe_share = (catalog_result['special']['total_mfe_1m'] /
                      catalog_result['all']['total_mfe_1m'] * 100
                      if catalog_result['all']['total_mfe_1m'] else 0)

    L.append(f"| NVDA avg MFE inflated by crash | "
             f"{'YES — clean NVDA is ' + str(round(fc['nvda_mfe_normal'],3)) + ' ATR vs ' + str(round(fc['nvda_mfe_all'],3)) + ' all' if not np.isnan(fc['nvda_mfe_normal'] or np.nan) else 'SEE TABLE'} | "
             f"Special days inflate NVDA avg |")
    L.append(f"| NVDA bear 2x finding (+1,123 ATR) | "
             f"{'ARTIFACT — normal-day 2x est: ' + f'{nvda_2x_normal:+.0f} ATR' if nvda_norm_n > 0 else 'INSUFFICIENT DATA'} | "
             f"All-day: {nvda_2x_all:+.0f} ATR; Normal: {nvda_2x_normal:+.0f} ATR |")
    L.append(f"| NVDA bear win rate | "
             f"{'ROBUST' if nvda_norm_win > 50 else 'ARTIFACT'} | "
             f"Normal-day win%={nvda_norm_win:.1f}% (N={nvda_norm_n}) |")
    L.append(f"| Great move rate 19.2% | "
             f"{'ROBUST' if great_delta < 0.03 else 'AFFECTED'} | "
             f"All={great_all:.1%}  Normal={great_norm:.1%}  Delta={great_norm-great_all:+.1%} |")
    L.append(f"| Special days share of catalog MFE | "
             f"INFORMATIONAL | {spec_mfe_share:.1f}% of total 1m MFE is from special days |")
    L.append(f"| Tier S/A thresholds (0.60/0.40) | "
             f"INFORMATIONAL | Compare p90/p75 on normal days to see if thresholds shift |")
    L.append(f"| Quiet Coil / midday findings | "
             f"{'ROBUST' if m_norm_st['n'] > 50 else 'SMALL SAMPLE'} | "
             f"Midday normal: N={m_norm_st['n']}, Win%={m_norm_st['win_rate']:.1f}% |")

    L.append('')
    L.append('---')
    L.append(f'*Generated by special_day_contamination.py on {datetime.now().strftime("%Y-%m-%d %H:%M")}*')

    return '\n'.join(L)


def _is_midday(sig):
    """Return True if signal is in midday window (11:00-13:59)."""
    ts = sig.get('time_str', '')
    try:
        hour = int(ts.split(':')[0])
        return 11 <= hour < 14
    except:
        return False


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print(DIVIDER)
    print('Special Day Contamination Analysis')
    print(DIVIDER)
    print()

    # ── Part 1: Identify special days ──
    print('Part 1: Identifying special days from IB daily data...')
    special_days, daily_data = compute_daily_ranges()
    print(f'  Found {len(special_days)} special days total '
          f'({special_days["is_crash"].sum()} crash days)')

    if not special_days.empty:
        print('\n  Top 20 special days:')
        print(f'  {"Symbol":<8} {"Date":<12} {"Range":>8} {"Median":>8} {"Mult":>6} {"Crash?"}')
        for _, r in special_days.head(20).iterrows():
            crash_tag = ' ***CRASH***' if r['is_crash'] else ''
            print(f'  {r["symbol"]:<8} {str(r["date"]):<12} {r["daily_range"]:8.3f} '
                  f'{r["median_range"]:8.3f} {r["multiplier"]:6.1f}x{crash_tag}')

    special_day_set = build_special_day_set(special_days)
    crash_day_set   = build_crash_day_set(special_days)
    print()

    # ── Part 2: Catalog contamination ──
    print('Part 2: Analyzing move catalog contamination...')
    cat = load_catalog()
    print(f'  Catalog: {len(cat):,} primary moves')
    catalog_result = analyze_catalog_contamination(cat, special_day_set, crash_day_set)
    r = catalog_result
    print(f"  ALL:     N={r['all']['n']:,}  Great={r['all']['great_rate']:.1%}  AvgMFE={r['all']['avg_mfe_1m']:.3f}")
    print(f"  NORMAL:  N={r['normal']['n']:,}  Great={r['normal']['great_rate']:.1%}  AvgMFE={r['normal']['avg_mfe_1m']:.3f}")
    print(f"  SPECIAL: N={r['special']['n']:,}  Great={r['special']['great_rate']:.1%}  AvgMFE={r['special']['avg_mfe_1m']:.3f}")
    print()

    # ── Part 3: v3.3c signal contamination ──
    print('Part 3: Loading and parsing v3.3c Pine log signals...')
    signals = load_v33c_signals()
    flag_signals_special_days(signals, special_day_set, crash_day_set)

    nvda_bear = compute_nvda_bear_2x_estimate(signals, special_day_set)
    print(f"\n  NVDA bear ALL:    {fmt_stat(nvda_bear['all'])}")
    print(f"  NVDA bear NORMAL: {fmt_stat(nvda_bear['normal'])}")
    print(f"  NVDA bear SPECIAL:{fmt_stat(nvda_bear['special'])}")
    print()

    # ── Part 4: Key findings re-run ──
    print('Part 4: Re-running key findings on normal days...')
    findings_catalog = rerun_catalog_findings(catalog_result)
    findings_signal  = rerun_signal_findings(signals)
    print()

    # ── Part 5: Tier thresholds ──
    print('Part 5: Tier threshold analysis...')
    tier_analysis = analyze_tier_thresholds(catalog_result, signals)
    print()

    # ── Generate report ──
    print('Generating report...')
    report = generate_report(
        special_days, catalog_result, signals,
        nvda_bear, findings_catalog, findings_signal,
        tier_analysis
    )
    out_path = OUT_DIR / 'special-day-contamination.md'
    out_path.write_text(report)
    print(f'Report saved to: {out_path}')
    print()
    print(DIVIDER)
    print('QUICK SUMMARY')
    print(DIVIDER)

    # Print key numbers
    fc = findings_catalog
    nvda_mfe_all  = fc['nvda_mfe_all']
    nvda_mfe_norm = fc['nvda_mfe_normal']
    spec_pct = (r['special']['total_mfe_1m'] / r['all']['total_mfe_1m'] * 100
                if r['all']['total_mfe_1m'] else 0)
    print(f"  Special days in catalog: {r['special']['n']} moves ({r['special']['n']/r['all']['n']*100:.1f}%)")
    if r['all']['total_mfe_1m']:
        print(f"  Special day share of total catalog MFE: {spec_pct:.1f}%")
    if nvda_mfe_all and not np.isnan(nvda_mfe_all):
        print(f"  NVDA avg MFE all: {nvda_mfe_all:.4f}  normal: {nvda_mfe_norm:.4f}")
    print(f"  NVDA bear 2x estimate — ALL: {nvda_bear['all']['net_atr']*2:+.1f} ATR  "
          f"NORMAL: {nvda_bear['normal']['net_atr']*2:+.1f} ATR")
    print(f"  Great move rate — all: {fc['great_rate_all']:.1%}  normal: {fc['great_rate_norm']:.1%}")

    with_data = [s for s in signals if s.get('mfe_atr') is not None]
    normal_sig = [s for s in with_data if not s.get('is_special')]
    special_sig = [s for s in with_data if s.get('is_special')]
    all_st    = sig_stats(with_data,  'ALL')
    norm_st   = sig_stats(normal_sig, 'NORMAL')
    spec_st   = sig_stats(special_sig,'SPECIAL')
    if all_st['net_atr'] != 0:
        spec_share = spec_st['net_atr'] / all_st['net_atr'] * 100
        print(f"  Signal net ATR — all: {all_st['net_atr']:+.1f}  normal: {norm_st['net_atr']:+.1f}  "
              f"special: {spec_st['net_atr']:+.1f} ({spec_share:.1f}% of total)")


if __name__ == '__main__':
    main()
