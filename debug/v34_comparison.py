#!/usr/bin/env python3
"""
KLB v3.4 vs v3.3c Comparison
==============================
Parses Pine log CSVs for both versions, measures MFE/MAE from IB 1m data,
and produces a structured comparison report.

v3.4 changes vs v3.3c:
  1. NVDA bull REV fully suppressed (v3.3d)
  2. Bull BRK at PD Last Hr High added — new signal type (non-NVDA)
  3. ORB Low Reclaim re-enabled for midday only, no EMA gate
  4. BAIL positive guard — pnl>=0 at 5m check -> force HOLD
  5. NVDA bear ★2x label (visual only)
  6. Special day detection (visual only)
"""

import sys, os, glob, csv, re, warnings
from pathlib import Path
from datetime import timedelta

import pandas as pd
import numpy as np

warnings.filterwarnings('ignore')

# ── Config ────────────────────────────────────────────────────────────────────
DEBUG_DIR = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug')
BAR_DIR   = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars/')
SYMBOLS   = ['SPY','AAPL','AMD','AMZN','GLD','GOOGL','META','MSFT','NFLX','NVDA','QQQ','SLV','TSLA','TSM','XLE']

V34_GLOB  = 'pine-logs-Key Level Breakout v3.4_*.csv'
V33C_GLOB = 'pine-logs-Key Level Breakout v3.3c_*.csv'

MFE_MINUTES     = 60
ATR_PERIOD      = 14
WIN_MFE_THRESH  = 0.10   # MFE >= 0.10 ATR AND MFE > MAE -> WIN

DIV  = '=' * 72
SDIV = '-' * 72

# ── Log patterns (reused from v33_backtest.py) ─────────────────────────────
SIG_PATTERN = re.compile(
    r'\[KLB\]\s+'
    r'(\d+:\d+)\s+'
    r'([▲▼])\s+'
    r'(.+?)\s+'
    r'vol=([0-9.]+)x\s+'
    r'pos=([v^]\d+)\s+'
    r'vwap=(above|below|na)\s+'
    r'ema=(bull|bear|na)\s+'
    r'rs=([+-]?[0-9.]+%?)\s+'
    r'adx=(\d+|na)\s+'
    r'body=(\d+)%\s+'
    r'ramp=([0-9.]+)x\s+'
    r'rangeATR=([0-9.]+)\s*'
    r'(.*?)\s*'
    r'O([0-9.]+)\s+'
    r'H([0-9.]+)\s+'
    r'L([0-9.]+)\s+'
    r'C([0-9.]+)\s+'
    r'ATR=([0-9.]+)'
)

RNG_PATTERN  = re.compile(r'\[KLB\]\s+(\d+:\d+)\s+([▲▼])\s+RNG\s+range\s+break\s+vol=([0-9.]+)x')
FADE_PATTERN = re.compile(r'\[KLB\]\s+(\d+:\d+)\s+([▲▼])\s+FADE\s+at\s+([0-9.]+)')
CONF_PATTERN = re.compile(r'\[KLB\]\s+CONF\s+(\d+:\d+)\s+([▲▼])\s+(BRK|QBS)\s+→\s+(✓★?|✗|✓)\s*\((.+?)\)')
CHECK_PATTERN = re.compile(r'\[KLB\]\s+5m\s+CHECK\s+(\d+:\d+)\s+([▲▼])\s+pnl=([+-]?[0-9.]+)\s+(SPY[✓✗~])\s+→\s+(HOLD|BAIL)')
QBS_PATTERN = re.compile(
    r'\[KLB\]\s+(\d+:\d+)\s+([▲▼])\s+🔇\s+QBS\s+'
    r'ramp=([0-9.]+)x\s+'
    r'vol=([0-9.]+)x\s+'
    r'pos=([v^]\d+)\s+'
    r'vwap=(above|below|na)\s+'
    r'ema=(bull|bear|na)\s+'
    r'adx=(\d+|na)\s+'
    r'body=(\d+)%\s+'
    r'rangeATR=([0-9.]+)\s*'
    r'(.*?)\s*'
    r'O([0-9.]+)\s+'
    r'H([0-9.]+)\s+'
    r'L([0-9.]+)\s+'
    r'C([0-9.]+)\s+'
    r'ATR=([0-9.]+)'
)


def parse_type_and_levels(s):
    s = s.strip()
    is_counter_ema = False
    if s.startswith('BRK '):
        sig_type, levels_str = 'BRK', s[4:].strip()
    elif s.startswith('~ x~ '):
        sig_type, levels_str, is_counter_ema = 'REV', s[5:].strip(), True
    elif s.startswith('~ ~~ '):
        sig_type, levels_str = 'EXREV', s[5:].strip()
    elif s.startswith('~~ '):
        sig_type, levels_str = 'EXREV', s[3:].strip()
    elif s.startswith('~ ~ '):
        sig_type, levels_str = 'REV', s[4:].strip()
    elif s.startswith('~ '):
        sig_type, levels_str = 'REV', s[2:].strip()
    else:
        sig_type, levels_str = 'UNK', s
    parts = []
    for part in levels_str.split(' + '):
        part = part.strip()
        while part.startswith('~ '):
            part = part[2:]
        if part:
            parts.append(part)
    return sig_type, ' + '.join(parts), is_counter_ema


def parse_pine_log(filepath):
    signals, confs, checks = [], [], []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) < 2:
                continue
            timestamp_str = row[0]
            message = ' '.join(row[1:]).strip()
            try:
                ts = pd.Timestamp(timestamp_str)
            except:
                continue
            if '[KLB]' not in message:
                continue

            # RNG
            m = RNG_PATTERN.search(message)
            if m:
                t, d, vol = m.groups()
                signals.append(dict(
                    timestamp=ts, time_str=t,
                    direction='bull' if d=='▲' else 'bear',
                    sig_type='RNG', levels='range',
                    vol_ratio=float(vol), close_pos=None,
                    vwap=None, ema=None, rs=None, adx=None,
                    body_pct=None, ramp=None, range_atr=None,
                    is_big_move=False, is_vol_drying=False, is_body_warn=False,
                    open=None, high=None, low=None, close=None, atr=None,
                    is_counter_ema=False, is_dim=False, dim_reason=None,
                    conf=None, check_result=None, bail_pnl=None,
                ))
                continue

            # FADE
            m = FADE_PATTERN.search(message)
            if m:
                t, d, lp = m.groups()
                signals.append(dict(
                    timestamp=ts, time_str=t,
                    direction='bull' if d=='▲' else 'bear',
                    sig_type='FADE', levels=f'at {lp}',
                    vol_ratio=None, close_pos=None,
                    vwap=None, ema=None, rs=None, adx=None,
                    body_pct=None, ramp=None, range_atr=None,
                    is_big_move=False, is_vol_drying=False, is_body_warn=False,
                    open=None, high=None, low=None, close=float(lp), atr=None,
                    is_counter_ema=False, is_dim=False, dim_reason=None,
                    conf=None, check_result=None, bail_pnl=None,
                ))
                continue

            # CONF
            m = CONF_PATTERN.search(message)
            if m:
                t, dc, bt, res, det = m.groups()
                confs.append(dict(timestamp=ts, time_str=t,
                                  direction='bull' if dc=='▲' else 'bear',
                                  type=bt, result=res, detail=det))
                continue

            # 5m CHECK
            m = CHECK_PATTERN.search(message)
            if m:
                t, dc, pnl, spy, action = m.groups()
                checks.append(dict(timestamp=ts, time_str=t,
                                   direction='bull' if dc=='▲' else 'bear',
                                   pnl=float(pnl), spy=spy, action=action))
                continue

            # QBS
            m = QBS_PATTERN.search(message)
            if m:
                (t, d, ramp, vol, pos, vwap, ema, adx, body, ratr,
                 flags, o, h, l, c, atr) = m.groups()
                is_dim = 'dim' in flags or 'moddim' in flags
                signals.append(dict(
                    timestamp=ts, time_str=t,
                    direction='bull' if d=='▲' else 'bear',
                    sig_type='QBS', levels='QBS',
                    vol_ratio=float(vol), close_pos=pos,
                    vwap=vwap, ema=ema, rs=None,
                    adx=int(adx) if adx != 'na' else None,
                    body_pct=int(body), ramp=float(ramp),
                    range_atr=float(ratr),
                    is_big_move='⚡' in flags,
                    is_vol_drying=True, is_body_warn='⚠' in flags,
                    open=float(o), high=float(h), low=float(l),
                    close=float(c), atr=float(atr),
                    is_counter_ema=False,
                    is_dim=is_dim,
                    dim_reason='qbs_dim' if 'dim' in flags else None,
                    conf=None, check_result=None, bail_pnl=None,
                ))
                continue

            # Main BRK/REV
            m = SIG_PATTERN.search(message)
            if m:
                (t, d, tl, vol, pos, vwap, ema, rs, adx, body,
                 ramp, ratr, flags, o, h, l, c, atr) = m.groups()
                sig_type, levels_str, is_ce = parse_type_and_levels(tl)
                signals.append(dict(
                    timestamp=ts, time_str=t,
                    direction='bull' if d=='▲' else 'bear',
                    sig_type=sig_type, levels=levels_str,
                    vol_ratio=float(vol), close_pos=pos,
                    vwap=vwap, ema=ema, rs=rs,
                    adx=int(adx) if adx != 'na' else None,
                    body_pct=int(body), ramp=float(ramp),
                    range_atr=float(ratr),
                    is_big_move='⚡' in flags,
                    is_vol_drying='🔇' in message,
                    is_body_warn='⚠' in flags,
                    open=float(o), high=float(h), low=float(l),
                    close=float(c), atr=float(atr),
                    is_counter_ema=is_ce,
                    is_dim=False, dim_reason=None,
                    conf=None, check_result=None, bail_pnl=None,
                ))

    # Attach CONF
    for conf in confs:
        best = None
        for sig in signals:
            if sig['direction'] != conf['direction']:
                continue
            if sig['sig_type'] not in ('BRK', 'QBS'):
                continue
            dt = abs((conf['timestamp'] - sig['timestamp']).total_seconds())
            if dt <= 300:
                if best is None or dt < abs((conf['timestamp'] - best['timestamp']).total_seconds()):
                    best = sig
        if best is not None:
            best['conf'] = conf['result']

    # Attach 5m CHECK (including bail_pnl for BAIL analysis)
    for chk in checks:
        best = None
        for sig in signals:
            if sig['direction'] != chk['direction']:
                continue
            if sig['conf'] is None:
                continue
            dt = (chk['timestamp'] - sig['timestamp']).total_seconds()
            if 0 <= dt <= 600:
                if best is None or dt < (chk['timestamp'] - best['timestamp']).total_seconds():
                    best = sig
        if best is not None:
            best['check_result'] = chk['action']
            best['bail_pnl'] = chk['pnl']

    return signals


def identify_symbol(signals):
    samples = [s for s in signals if s.get('close') is not None and s.get('atr') is not None][:10]
    if not samples:
        return None
    best_sym, best_score = None, float('inf')
    for sym in SYMBOLS:
        fp = BAR_DIR / f'{sym.lower()}_1_day_ib.parquet'
        if not fp.exists():
            continue
        try:
            daily = pd.read_parquet(fp)
            dt = pd.to_datetime(daily['date'])
            if dt.dt.tz is not None:
                dt = dt.dt.tz_convert('US/Eastern')
            daily['date'] = dt
            daily = daily.set_index('date').sort_index()
        except:
            continue
        total_err, matched = 0, 0
        for sig in samples:
            sig_date = sig['timestamp'].date()
            day_bars = daily[daily.index.date == sig_date]
            if len(day_bars) == 0:
                continue
            daily_close = day_bars['close'].iloc[0]
            if daily_close > 0:
                total_err += abs(sig['close'] - daily_close) / daily_close
                matched += 1
        if matched > 0:
            avg_err = total_err / matched
            if avg_err < best_score:
                best_score = avg_err
                best_sym = sym
    if best_score > 0.05:
        return None
    return best_sym


def load_1m(symbol):
    fp = BAR_DIR / f'{symbol.lower()}_1_min_ib.parquet'
    df = pd.read_parquet(fp)
    dt = pd.to_datetime(df['date'])
    if dt.dt.tz is None:
        dt = dt.dt.tz_localize('US/Eastern')
    elif str(dt.dt.tz) != 'US/Eastern':
        dt = dt.dt.tz_convert('US/Eastern')
    df['date'] = dt
    df = df.set_index('date').sort_index()
    return df.between_time('09:30', '15:59')


def load_daily(symbol):
    fp = BAR_DIR / f'{symbol.lower()}_1_day_ib.parquet'
    df = pd.read_parquet(fp)
    dt = pd.to_datetime(df['date'])
    if dt.dt.tz is not None:
        dt = dt.dt.tz_convert('US/Eastern')
    df['date'] = dt
    return df.set_index('date').sort_index()


def compute_atr(daily_df, period=ATR_PERIOD):
    tr = pd.DataFrame({
        'hl': daily_df['high'] - daily_df['low'],
        'hc': (daily_df['high'] - daily_df['close'].shift(1)).abs(),
        'lc': (daily_df['low']  - daily_df['close'].shift(1)).abs(),
    })
    tr['tr'] = tr.max(axis=1)
    atr = tr['tr'].ewm(span=period, adjust=False).mean()
    atr.index = atr.index.date
    return atr


def measure_mfe_mae(signals, bars_1m, atr_series):
    for sig in signals:
        ts        = sig['timestamp']
        direction = sig['direction']
        entry     = sig.get('close')
        atr       = sig.get('atr')

        if atr is None or atr == 0:
            sig_date = ts.date()
            atr = atr_series.get(sig_date)

        if entry is None or atr is None or atr == 0:
            sig.update(mfe=0, mae=0, mfe_atr=0, mae_atr=0,
                       pnl_atr=0, outcome='FLAT', bars_to_mfe=0)
            continue

        if ts.tzinfo is None:
            ts_et = pd.Timestamp(ts, tz='US/Eastern')
        else:
            ts_et = ts.tz_convert('US/Eastern')

        start = ts_et + pd.Timedelta(minutes=1)
        end   = ts_et + pd.Timedelta(minutes=MFE_MINUTES)
        eod   = ts_et.normalize() + pd.Timedelta(hours=16)
        end   = min(end, eod)

        fwd = bars_1m[(bars_1m.index >= start) & (bars_1m.index <= end)]
        if len(fwd) == 0:
            sig.update(mfe=0, mae=0, mfe_atr=0, mae_atr=0,
                       pnl_atr=0, outcome='FLAT', bars_to_mfe=0)
            continue

        if direction == 'bull':
            fav = fwd['high'] - entry
            adv = entry - fwd['low']
        else:
            fav = entry - fwd['low']
            adv = fwd['high'] - entry

        mfe = max(0, fav.max())
        mae = max(0, adv.max())
        mfe_atr = mfe / atr
        mae_atr = mae / atr
        pnl_atr = mfe_atr - mae_atr

        if mfe_atr >= WIN_MFE_THRESH and mfe > mae:
            outcome = 'WIN'
        elif mae_atr > mfe_atr and mae_atr >= WIN_MFE_THRESH:
            outcome = 'LOSS'
        else:
            outcome = 'FLAT'

        bars_to_mfe = int((fav.idxmax() - start).total_seconds() / 60) + 1 if mfe > 0 else 0
        sig.update(mfe=mfe, mae=mae, mfe_atr=mfe_atr, mae_atr=mae_atr,
                   pnl_atr=pnl_atr, outcome=outcome, bars_to_mfe=bars_to_mfe)


def load_version(version_glob):
    """Parse all log files for a version glob, return list of signal dicts with symbol."""
    files = sorted(glob.glob(str(DEBUG_DIR / version_glob)))
    print(f'  Found {len(files)} files matching {version_glob}')
    all_signals = []
    for fp in files:
        short = Path(fp).name
        sigs  = parse_pine_log(fp)
        if not sigs:
            print(f'    {short}: 0 signals')
            continue
        sym = identify_symbol(sigs)
        if sym is None:
            print(f'    {short}: could not identify symbol')
            continue
        for s in sigs:
            s['symbol'] = sym
        all_signals.extend(sigs)
        print(f'    {short}: {sym} — {len(sigs)} signals')
    return all_signals


def dedup(signals, keys=('symbol', 'timestamp', 'sig_type', 'levels', 'direction')):
    seen = set()
    out  = []
    for s in signals:
        k = tuple(s.get(x) for x in keys)
        if k not in seen:
            seen.add(k)
            out.append(s)
    return out


def df_from(signals):
    return pd.DataFrame(signals)


def pct(n, d):
    return 100 * n / d if d else 0


# ── Stats helpers ─────────────────────────────────────────────────────────────
def stats(df):
    if len(df) == 0:
        return dict(n=0, wins=0, win_pct=0.0, net_atr=0.0, per_sig_atr=0.0)
    wins = (df['outcome'] == 'WIN').sum()
    net  = df['pnl_atr'].sum()
    return dict(
        n=len(df),
        wins=int(wins),
        win_pct=pct(wins, len(df)),
        net_atr=net,
        per_sig_atr=net / len(df),
    )


def fmt(st):
    return (f"N={st['n']:4d}  Win%={st['win_pct']:4.1f}%  "
            f"Net={st['net_atr']:+7.1f}  /sig={st['per_sig_atr']:+.3f}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(DIV)
    print('KLB v3.4 vs v3.3c Comparison')
    print(DIV)
    print()

    # ── 1. Load logs ──────────────────────────────────────────────────────────
    print('=== LOADING LOGS ===')
    print('v3.3c:')
    raw_33c = load_version(V33C_GLOB)
    print('v3.4:')
    raw_34  = load_version(V34_GLOB)
    print()

    # Print schema from first file
    first_file = sorted(glob.glob(str(DEBUG_DIR / V34_GLOB)))[0]
    print(f'Schema check (first v3.4 file: {Path(first_file).name}):')
    with open(first_file) as f:
        print(f'  Header: {f.readline().strip()}')
        print(f'  Row 1:  {f.readline().strip()[:120]}...')
    print()

    # Dedup
    sigs_33c = dedup(raw_33c)
    sigs_34  = dedup(raw_34)
    print(f'After dedup: v3.3c {len(raw_33c)} -> {len(sigs_33c)} | v3.4 {len(raw_34)} -> {len(sigs_34)}')
    print()

    # ── 2. Load IB data and measure MFE/MAE ──────────────────────────────────
    symbols_all = sorted(set(
        s['symbol'] for s in sigs_33c + sigs_34
        if s.get('symbol') and s.get('close') is not None
    ))
    print(f'Symbols found: {symbols_all}')
    print('Loading IB 1m data and measuring MFE/MAE...')

    ib = {}
    for sym in symbols_all:
        try:
            bars = load_1m(sym)
            daily = load_daily(sym)
            atr_s = compute_atr(daily)
            ib[sym] = (bars, atr_s)
            print(f'  {sym}: {len(bars)} 1m bars')
        except Exception as e:
            print(f'  {sym}: FAILED ({e})')

    def enrich(signals):
        by_sym = {}
        for s in signals:
            by_sym.setdefault(s.get('symbol'), []).append(s)
        for sym, sigs in by_sym.items():
            if sym in ib:
                bars, atr_s = ib[sym]
                measure_mfe_mae(sigs, bars, atr_s)
            else:
                for s in sigs:
                    s.update(mfe=0, mae=0, mfe_atr=0, mae_atr=0,
                              pnl_atr=0, outcome='FLAT', bars_to_mfe=0)

    enrich(sigs_33c)
    enrich(sigs_34)
    print()

    df33 = df_from(sigs_33c)
    df34 = df_from(sigs_34)

    # Exclude RNG from P&L (MFE/MAE unreliable for RNG signals — no entry price)
    df33x = df33[df33['sig_type'] != 'RNG'].copy()
    df34x = df34[df34['sig_type'] != 'RNG'].copy()

    # ── 3. HIGH-LEVEL SUMMARY ────────────────────────────────────────────────
    print(DIV)
    print('SECTION 1: HIGH-LEVEL SUMMARY (excl. RNG)')
    print(DIV)
    st33 = stats(df33x)
    st34 = stats(df34x)
    print(f'v3.3c: {fmt(st33)}')
    print(f'v3.4:  {fmt(st34)}')
    delta_n   = st34['n']   - st33['n']
    delta_wp  = st34['win_pct'] - st33['win_pct']
    delta_net = st34['net_atr'] - st33['net_atr']
    delta_ps  = st34['per_sig_atr'] - st33['per_sig_atr']
    print(f'Delta: N={delta_n:+d}  Win%={delta_wp:+.1f}pp  Net={delta_net:+.1f}  /sig={delta_ps:+.3f}')
    print()

    # RNG separately (no MFE/MAE)
    print('RNG signals (no MFE/MAE — not in summary):')
    print(f'  v3.3c RNG: {(df33["sig_type"]=="RNG").sum()}')
    print(f'  v3.4  RNG: {(df34["sig_type"]=="RNG").sum()}')
    print()

    # Breakdown by signal type
    print('By signal_type:')
    sig_types = ['BRK', 'REV', 'EXREV', 'FADE', 'QBS', 'UNK']
    print(f'{"Type":<8} {"v3.3c":>40}  {"v3.4":>40}  {"Delta N":>8}  {"Delta Net":>10}')
    print(SDIV)
    for st_type in sig_types:
        s33 = stats(df33x[df33x['sig_type'] == st_type])
        s34 = stats(df34x[df34x['sig_type'] == st_type])
        if s33['n'] == 0 and s34['n'] == 0:
            continue
        dn = s34['n'] - s33['n']
        dnet = s34['net_atr'] - s33['net_atr']
        marker = ' ★' if abs(dnet) > 50 or abs(dn) > 50 else ''
        print(f'{st_type:<8} {fmt(s33)}  {fmt(s34)}  {dn:>+8d}  {dnet:>+10.1f}{marker}')
    print()

    # ── 4. NVDA-SPECIFIC ANALYSIS ────────────────────────────────────────────
    print(DIV)
    print('SECTION 2: NVDA-SPECIFIC ANALYSIS')
    print(DIV)

    nvda33 = df33x[df33x['symbol'] == 'NVDA']
    nvda34 = df34x[df34x['symbol'] == 'NVDA']

    # Bull REV
    nvda33_bull_rev = nvda33[(nvda33['sig_type'].isin(['REV','EXREV'])) & (nvda33['direction']=='bull')]
    nvda34_bull_rev = nvda34[(nvda34['sig_type'].isin(['REV','EXREV'])) & (nvda34['direction']=='bull')]
    print('NVDA bull REV/EXREV:')
    print(f'  v3.3c: {fmt(stats(nvda33_bull_rev))}')
    print(f'  v3.4:  {fmt(stats(nvda34_bull_rev))}')
    if stats(nvda33_bull_rev)['win_pct'] > 50:
        print('  ★ WARNING: NVDA bull REV was >50% win in v3.3c — potentially bad cut!')
    else:
        print('  → Cut is justified (win% was <=50% in v3.3c)')
    print()

    # Bear REV (should remain)
    nvda33_bear_rev = nvda33[(nvda33['sig_type'].isin(['REV','EXREV'])) & (nvda33['direction']=='bear')]
    nvda34_bear_rev = nvda34[(nvda34['sig_type'].isin(['REV','EXREV'])) & (nvda34['direction']=='bear')]
    print('NVDA bear REV/EXREV:')
    print(f'  v3.3c: {fmt(stats(nvda33_bear_rev))}')
    print(f'  v3.4:  {fmt(stats(nvda34_bear_rev))}')
    print()

    # NVDA overall vs non-NVDA
    non_nvda34 = df34x[df34x['symbol'] != 'NVDA']
    print('NVDA overall (v3.4):')
    print(f'  NVDA:     {fmt(stats(nvda34))}')
    print(f'  Non-NVDA: {fmt(stats(non_nvda34))}')
    print()

    # ── 5. NEW SIGNAL TYPES IN v3.4 ─────────────────────────────────────────
    print(DIV)
    print('SECTION 3: NEW SIGNAL TYPES IN v3.4')
    print(DIV)

    # PD Last Hr High BRK
    PDLH_KEYWORDS = ['PD LH H', 'PDLastHrHigh', 'Last Hr H', 'PD LH', 'PDLHH']
    def is_pdlh(row):
        levels = str(row.get('levels', ''))
        return any(k in levels for k in PDLH_KEYWORDS)

    pdlh_mask34 = df34.apply(is_pdlh, axis=1)
    pdlh_mask33 = df33.apply(is_pdlh, axis=1)
    pdlh34 = df34x[df34x.apply(is_pdlh, axis=1)]
    pdlh33 = df33x[df33x.apply(is_pdlh, axis=1)]

    print(f'PD Last Hr High signals (keywords: {PDLH_KEYWORDS}):')
    print(f'  v3.3c: {fmt(stats(pdlh33))}')
    print(f'  v3.4:  {fmt(stats(pdlh34))}')
    if len(pdlh34) > 0:
        print(f'  Unique levels seen in v3.4: {sorted(pdlh34["levels"].unique())}')
    print()

    # Check for all "PD LH" occurrences in levels to understand naming
    all_levels_34 = df34['levels'].dropna().unique()
    pdlh_levels = [l for l in all_levels_34 if 'LH' in str(l) or 'Last Hr' in str(l)]
    print(f'  All v3.4 level strings containing LH/Last Hr: {sorted(pdlh_levels)[:20]}')
    print()

    # ORB Low Reclaim midday
    def is_orbl_reclaim(row):
        levels = str(row.get('levels', ''))
        sig_type = str(row.get('sig_type', ''))
        direction = str(row.get('direction', ''))
        time_str = str(row.get('time_str', ''))
        # ORB L signals going bull (reclaim = price going up through ORB low)
        has_orbl = 'ORB L' in levels
        is_bull  = direction == 'bull'
        # Midday: 11:00-14:00
        try:
            h = int(time_str.split(':')[0])
            is_midday = 11 <= h < 14
        except:
            is_midday = False
        return has_orbl and is_bull and is_midday

    orbl_mid34 = df34x[df34x.apply(is_orbl_reclaim, axis=1)]
    orbl_mid33 = df33x[df33x.apply(is_orbl_reclaim, axis=1)]
    print('ORB Low Reclaim (bull + midday 11-14h):')
    print(f'  v3.3c: {fmt(stats(orbl_mid33))}')
    print(f'  v3.4:  {fmt(stats(orbl_mid34))}')
    print()

    # ── 6. BAIL ANALYSIS ────────────────────────────────────────────────────
    print(DIV)
    print('SECTION 4: BAIL ANALYSIS (change 4: positive guard)')
    print(DIV)

    # Check if bail_pnl column exists and has data
    bail_cols = ['check_result', 'bail_pnl']
    for col in bail_cols:
        if col not in df33.columns:
            df33[col] = None
        if col not in df34.columns:
            df34[col] = None

    # BAIL decisions
    bail33 = df33[df33['check_result'] == 'BAIL']
    bail34 = df34[df34['check_result'] == 'BAIL']
    hold33 = df33[df33['check_result'] == 'HOLD']
    hold34 = df34[df34['check_result'] == 'HOLD']

    print(f'5m CHECK decisions:')
    print(f'  v3.3c — BAIL: {len(bail33)}, HOLD: {len(hold33)}')
    print(f'  v3.4  — BAIL: {len(bail34)}, HOLD: {len(hold34)}')
    print()

    # BAIL with pnl>=0 (would be prevented by v3.4 positive guard)
    if 'bail_pnl' in df33.columns and df33['bail_pnl'].notna().any():
        bail33_pos = bail33[bail33['bail_pnl'] >= 0]
        bail34_pos = bail34[bail34['bail_pnl'] >= 0]
        print(f'  v3.3c BAILs with pnl>=0 (now forced HOLD): {len(bail33_pos)} / {len(bail33)}')
        print(f'  v3.4  BAILs with pnl>=0 (should be 0):     {len(bail34_pos)} / {len(bail34)}')
        if len(bail33_pos) > 0:
            print(f'  ★ v3.3c BAILed {len(bail33_pos)} signals at pnl>=0 — these should benefit from HOLD')
        print()
        # Distribution of bail pnl
        if len(bail33) > 0:
            print(f'  v3.3c bail pnl distribution: min={bail33["bail_pnl"].min():.2f} '
                  f'median={bail33["bail_pnl"].median():.2f} max={bail33["bail_pnl"].max():.2f}')
        if len(bail34) > 0:
            print(f'  v3.4  bail pnl distribution: min={bail34["bail_pnl"].min():.2f} '
                  f'median={bail34["bail_pnl"].median():.2f} max={bail34["bail_pnl"].max():.2f}')
    else:
        print('  bail_pnl column: no data captured (BAIL pnl not logged separately)')
        print('  → Use check_result counts as proxy. Fewer BAILs in v3.4 = positive guard working.')
    print()

    # ── 7. SIGNAL CUTS — POTENTIAL REGRESSIONS ──────────────────────────────
    print(DIV)
    print('SECTION 5: SIGNAL TYPE+LEVEL COMBOS — CUTS & ADDITIONS')
    print(DIV)

    def combo_stats(df, top_n=30):
        df = df.copy()
        df['combo'] = df['sig_type'] + '|' + df['direction'] + '|' + df['levels'].fillna('?')
        grp = df.groupby('combo').apply(lambda g: pd.Series({
            'n': len(g),
            'wins': (g['outcome'] == 'WIN').sum(),
            'win_pct': pct((g['outcome'] == 'WIN').sum(), len(g)),
            'net_atr': g['pnl_atr'].sum(),
        })).reset_index()
        return grp.sort_values('n', ascending=False).head(top_n)

    grp33 = combo_stats(df33x)
    grp34 = combo_stats(df34x)

    # Merge to find changes
    merged = grp33.merge(grp34, on='combo', how='outer', suffixes=('_33', '_34'))
    merged = merged.fillna(0)
    merged['delta_n']   = merged['n_34'] - merged['n_33']
    merged['delta_net'] = merged['net_atr_34'] - merged['net_atr_33']

    # Combos that DECREASED
    cuts = merged[merged['delta_n'] < 0].sort_values('delta_n')
    print(f'Combos with DECREASED counts (potential cuts):')
    print(f'{"Combo":<45} {"N_33":>6} {"N_34":>6} {"Delta":>6} {"Win%_33":>8} {"Win%_34":>8} {"ΔNet":>8}')
    print(SDIV)
    for _, row in cuts.iterrows():
        flag = ' ★' if row['win_pct_33'] > 50 else ''
        print(f'{str(row["combo"])[:44]:<45} {int(row["n_33"]):>6} {int(row["n_34"]):>6} '
              f'{int(row["delta_n"]):>+6} {row["win_pct_33"]:>7.1f}% {row["win_pct_34"]:>7.1f}% '
              f'{row["delta_net"]:>+8.1f}{flag}')
    print()

    # Combos that INCREASED or are NEW
    adds = merged[merged['delta_n'] > 0].sort_values('delta_n', ascending=False)
    print(f'Combos with INCREASED/NEW counts (additions):')
    print(f'{"Combo":<45} {"N_33":>6} {"N_34":>6} {"Delta":>6} {"Win%_34":>8} {"ΔNet":>8}')
    print(SDIV)
    for _, row in adds.head(20).iterrows():
        flag = ' ★' if row['win_pct_34'] > 55 else ''
        print(f'{str(row["combo"])[:44]:<45} {int(row["n_33"]):>6} {int(row["n_34"]):>6} '
              f'{int(row["delta_n"]):>+6} {row["win_pct_34"]:>7.1f}%{"":<8} '
              f'{row["delta_net"]:>+8.1f}{flag}')
    print()

    # ── 8. SYMBOL BREAKDOWN ──────────────────────────────────────────────────
    print(DIV)
    print('SECTION 6: SYMBOL BREAKDOWN')
    print(DIV)
    print(f'{"Symbol":<8} {"v3.3c":>40}  {"v3.4":>40}  {"ΔNet":>8}')
    print(SDIV)
    syms = sorted(set(df33x['symbol'].dropna()) | set(df34x['symbol'].dropna()))
    for sym in syms:
        s33 = stats(df33x[df33x['symbol'] == sym])
        s34 = stats(df34x[df34x['symbol'] == sym])
        dnet = s34['net_atr'] - s33['net_atr']
        flag = ' ★' if dnet < -20 else (' ★+' if dnet > 20 else '')
        print(f'{sym:<8} {fmt(s33)}  {fmt(s34)}  {dnet:>+8.1f}{flag}')
    print()

    # ── 9. NVDA BULL REV WIN% CHECK ─────────────────────────────────────────
    print(DIV)
    print('SECTION 7: CRITICAL CHECK — Was v3.3c NVDA bull REV worth keeping?')
    print(DIV)
    st = stats(nvda33_bull_rev)
    print(f'v3.3c NVDA bull REV: N={st["n"]}  Win%={st["win_pct"]:.1f}%  Net={st["net_atr"]:+.1f}  /sig={st["per_sig_atr"]:+.3f}')
    if st['n'] == 0:
        print('  → No NVDA bull REV in v3.3c logs (already suppressed or not present)')
    elif st['win_pct'] > 50 and st['net_atr'] > 0:
        print('  ★ WARNING: NVDA bull REV was profitable in v3.3c — cutting it may be a mistake.')
    elif st['win_pct'] <= 50 or st['net_atr'] <= 0:
        print(f'  → Cutting NVDA bull REV is CORRECT (win%={st["win_pct"]:.1f}%, net={st["net_atr"]:+.1f})')
    print()

    # ── 10. SUMMARY OF KEY FINDINGS ─────────────────────────────────────────
    print(DIV)
    print('SECTION 8: KEY FINDINGS SUMMARY')
    print(DIV)
    print(f'1. Overall: N {st33["n"]}->{st34["n"]} ({st34["n"]-st33["n"]:+d}), '
          f'Win% {st33["win_pct"]:.1f}%->{st34["win_pct"]:.1f}% ({st34["win_pct"]-st33["win_pct"]:+.1f}pp), '
          f'Net {st33["net_atr"]:+.1f}->{st34["net_atr"]:+.1f} ({st34["net_atr"]-st33["net_atr"]:+.1f})')
    print(f'2. NVDA bull REV: v3.3c N={stats(nvda33_bull_rev)["n"]}, win%={stats(nvda33_bull_rev)["win_pct"]:.1f}% → v3.4 N={stats(nvda34_bull_rev)["n"]}')
    print(f'3. NVDA bear REV: v3.3c N={stats(nvda33_bear_rev)["n"]}, win%={stats(nvda33_bear_rev)["win_pct"]:.1f}% → v3.4 N={stats(nvda34_bear_rev)["n"]}, win%={stats(nvda34_bear_rev)["win_pct"]:.1f}%')
    print(f'4. PD Last Hr H BRK (new): N={len(pdlh34)}, {fmt(stats(pdlh34))}')
    print(f'5. ORB L Reclaim midday (new): N={len(orbl_mid34)}, {fmt(stats(orbl_mid34))}')
    print(f'6. BAIL counts: v3.3c={len(bail33)} vs v3.4={len(bail34)} ({len(bail34)-len(bail33):+d})')
    print()
    print(DIV)
    print('Done.')


if __name__ == '__main__':
    main()
