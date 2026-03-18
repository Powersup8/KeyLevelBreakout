#!/usr/bin/env python3
"""
v3.4 Debug Investigation
========================
Three focused analyses on v3.4 Pine logs:
  1. NVDA bull REV leak — which levels still firing?
  2. Bear BRK at PM L / Yest L / Week Open — disappeared?
  3. New signal profitability context (PD LH H BRK, ORB L Reclaim)

Reuses parser/loader logic from v34_comparison.py.
"""

import sys, os, glob, csv, re, warnings
from pathlib import Path
import pandas as pd
import numpy as np

warnings.filterwarnings('ignore')

# ── Config ────────────────────────────────────────────────────────────────────
DEBUG_DIR = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug')
BAR_DIR   = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars/')
SYMBOLS   = ['SPY','AAPL','AMD','AMZN','GLD','GOOGL','META','MSFT','NFLX','NVDA','QQQ','SLV','TSLA','TSM','XLE']

V34_GLOB  = 'pine-logs-Key Level Breakout v3.4_*.csv'
V33C_GLOB = 'pine-logs-Key Level Breakout v3.3c_*.csv'

MFE_MINUTES    = 60
ATR_PERIOD     = 14
WIN_MFE_THRESH = 0.10

DIV  = '=' * 72
SDIV = '-' * 72

# ── Log patterns (identical to v34_comparison.py) ────────────────────────────
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
RNG_PATTERN   = re.compile(r'\[KLB\]\s+(\d+:\d+)\s+([▲▼])\s+RNG\s+range\s+break\s+vol=([0-9.]+)x')
FADE_PATTERN  = re.compile(r'\[KLB\]\s+(\d+:\d+)\s+([▲▼])\s+FADE\s+at\s+([0-9.]+)')
CONF_PATTERN  = re.compile(r'\[KLB\]\s+CONF\s+(\d+:\d+)\s+([▲▼])\s+(BRK|QBS)\s+→\s+(✓★?|✗|✓)\s*\((.+?)\)')
CHECK_PATTERN = re.compile(r'\[KLB\]\s+5m\s+CHECK\s+(\d+:\d+)\s+([▲▼])\s+pnl=([+-]?[0-9.]+)\s+(SPY[✓✗~])\s+→\s+(HOLD|BAIL)')
QBS_PATTERN   = re.compile(
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
        next(reader, None)
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
                    conf=None, check_result=None,
                ))
                continue

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
                    conf=None, check_result=None,
                ))
                continue

            m = CONF_PATTERN.search(message)
            if m:
                t, dc, bt, res, det = m.groups()
                confs.append(dict(timestamp=ts, time_str=t,
                                  direction='bull' if dc=='▲' else 'bear',
                                  type=bt, result=res, detail=det))
                continue

            m = CHECK_PATTERN.search(message)
            if m:
                t, dc, pnl, spy, action = m.groups()
                checks.append(dict(timestamp=ts, time_str=t,
                                   direction='bull' if dc=='▲' else 'bear',
                                   pnl=float(pnl), spy=spy, action=action))
                continue

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
                    conf=None, check_result=None,
                ))
                continue

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
                    conf=None, check_result=None,
                ))

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


def compute_atr(daily_df):
    tr = pd.DataFrame({
        'hl': daily_df['high'] - daily_df['low'],
        'hc': (daily_df['high'] - daily_df['close'].shift(1)).abs(),
        'lc': (daily_df['low']  - daily_df['close'].shift(1)).abs(),
    })
    tr['tr'] = tr.max(axis=1)
    atr = tr['tr'].ewm(span=ATR_PERIOD, adjust=False).mean()
    atr.index = atr.index.date
    return atr


def measure_mfe_mae(signals, bars_1m, atr_series):
    for sig in signals:
        ts        = sig['timestamp']
        direction = sig['direction']
        entry     = sig.get('close')
        atr       = sig.get('atr')

        if atr is None or atr == 0:
            atr = atr_series.get(ts.date())

        if entry is None or atr is None or atr == 0:
            sig.update(mfe=0, mae=0, mfe_atr=0, mae_atr=0,
                       pnl_atr=0, outcome='FLAT', bars_to_mfe=0)
            continue

        ts_et = ts.tz_convert('US/Eastern') if ts.tzinfo else pd.Timestamp(ts, tz='US/Eastern')
        start = ts_et + pd.Timedelta(minutes=1)
        end   = min(ts_et + pd.Timedelta(minutes=MFE_MINUTES),
                    ts_et.normalize() + pd.Timedelta(hours=16))

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


def load_version(version_glob, quiet=False):
    files = sorted(glob.glob(str(DEBUG_DIR / version_glob)))
    if not quiet:
        print(f'  Found {len(files)} files matching {version_glob}')
    all_signals = []
    for fp in files:
        short = Path(fp).name
        sigs  = parse_pine_log(fp)
        if not sigs:
            if not quiet:
                print(f'    {short}: 0 signals')
            continue
        sym = identify_symbol(sigs)
        if sym is None:
            if not quiet:
                print(f'    {short}: could not identify symbol')
            continue
        for s in sigs:
            s['symbol'] = sym
        all_signals.extend(sigs)
        if not quiet:
            print(f'    {short}: {sym} — {len(sigs)} signals')
    return all_signals


def dedup(signals):
    seen = set()
    out  = []
    for s in signals:
        k = (s.get('symbol'), s.get('timestamp'), s.get('sig_type'),
             s.get('levels'), s.get('direction'))
        if k not in seen:
            seen.add(k)
            out.append(s)
    return out


def stats(df):
    if len(df) == 0:
        return dict(n=0, wins=0, win_pct=0.0, net_atr=0.0, per_sig=0.0)
    wins = (df['outcome'] == 'WIN').sum()
    net  = df['pnl_atr'].sum()
    return dict(n=len(df), wins=int(wins),
                win_pct=100 * wins / len(df),
                net_atr=net, per_sig=net / len(df))


def fmt(st):
    return (f"N={st['n']:4d}  Win%={st['win_pct']:5.1f}%  "
            f"Net={st['net_atr']:+8.1f}  /sig={st['per_sig']:+.3f}")


def tod_bucket(time_str):
    try:
        h, m = map(int, time_str.split(':'))
        mins = h * 60 + m
        if mins < 11 * 60:
            return 'morning (9:30-11)'
        elif mins < 14 * 60:
            return 'midday  (11-14)'
        else:
            return 'afternoon (14-16)'
    except:
        return 'unknown'


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print(DIV)
    print('v3.4 Debug Investigation')
    print(DIV)
    print()

    # ── Load logs ──────────────────────────────────────────────────────────
    print('Loading v3.4 logs...')
    raw34 = load_version(V34_GLOB)
    print()
    print('Loading v3.3c logs...')
    raw33c = load_version(V33C_GLOB)
    print()

    sigs34  = dedup(raw34)
    sigs33c = dedup(raw33c)
    print(f'After dedup: v3.4 {len(raw34)} -> {len(sigs34)} | v3.3c {len(raw33c)} -> {len(sigs33c)}')
    print()

    # Date range
    def date_range(sigs):
        ts = [s['timestamp'] for s in sigs if s.get('timestamp') is not None]
        if not ts:
            return 'N/A', 'N/A'
        return min(ts).date(), max(ts).date()

    mn34, mx34 = date_range(sigs34)
    mn33c, mx33c = date_range(sigs33c)
    print(f'v3.4  date range: {mn34} to {mx34}')
    print(f'v3.3c date range: {mn33c} to {mx33c}')
    print()

    # ── Load IB data ──────────────────────────────────────────────────────
    symbols_all = sorted(set(
        s['symbol'] for s in sigs34 + sigs33c
        if s.get('symbol') and s.get('close') is not None
    ))
    print(f'Symbols: {symbols_all}')
    print('Loading IB 1m data and measuring MFE/MAE...')

    ib = {}
    for sym in symbols_all:
        try:
            bars  = load_1m(sym)
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
                measure_mfe_mae(sigs, ib[sym][0], ib[sym][1])
            else:
                for s in sigs:
                    s.update(mfe=0, mae=0, mfe_atr=0, mae_atr=0,
                              pnl_atr=0, outcome='FLAT', bars_to_mfe=0)

    enrich(sigs34)
    enrich(sigs33c)
    print()

    df34  = pd.DataFrame(sigs34)
    df33c = pd.DataFrame(sigs33c)

    # Exclude RNG (no MFE/MAE)
    df34x  = df34[df34['sig_type']  != 'RNG'].copy()
    df33cx = df33c[df33c['sig_type'] != 'RNG'].copy()

    # ══════════════════════════════════════════════════════════════════════
    print(DIV)
    print('TASK 1: NVDA BULL REV LEAK — Which levels still firing in v3.4?')
    print(DIV)
    print()
    print('Suppression block in v3.3d/v3.4 covers: PML, YL, WL, VWAP, PDLH, VWBL, PDMid, TodayOpen, PDClose')
    print('NOT covered (should still fire): OL (ORB Low), PMH, YH, WH, OH')
    print()

    nvda34 = df34x[df34x['symbol'] == 'NVDA']
    nvda_bull_rev = nvda34[
        (nvda34['sig_type'].isin(['REV', 'EXREV'])) &
        (nvda34['direction'] == 'bull')
    ].copy()

    print(f'NVDA bull REV/EXREV signals in v3.4: {len(nvda_bull_rev)}')
    print()

    if len(nvda_bull_rev) > 0:
        # Break down by level
        level_groups = nvda_bull_rev.groupby('levels')
        rows = []
        for lvl, grp in level_groups:
            st = stats(grp)
            rows.append({'level': lvl, **st})
        rows.sort(key=lambda r: r['n'], reverse=True)

        print(f'{"Level":<45} {"N":>4}  {"Win%":>6}  {"Net":>8}  {"/sig":>7}')
        print(SDIV)
        for r in rows:
            flag = ''
            # Flag levels that should have been suppressed
            suppressed_kw = ['PML', 'YL', 'WL', 'VWAP', 'LH', 'VWBL', 'PDMid',
                             'TodayOpen', 'Today O', 'PD Cls', 'PDClose']
            expected_leak = ['OL', 'ORB L', 'PMH', 'PM H', 'YH', 'Yest H', 'WH', 'Week H', 'OH', 'ORB H']
            lvl_str = str(r['level'])
            if any(k in lvl_str for k in suppressed_kw):
                flag = ' ← SHOULD BE SUPPRESSED'
            elif any(k in lvl_str for k in expected_leak):
                flag = ' ← expected (not in suppression)'
            print(f'{r["level"]:<45} {r["n"]:>4}  {r["win_pct"]:>5.1f}%  {r["net_atr"]:>+8.1f}  {r["per_sig"]:>+7.3f}{flag}')
        print()

        # Aggregate: suppressed vs expected
        supp_mask = nvda_bull_rev['levels'].apply(
            lambda l: any(k in str(l) for k in suppressed_kw)
        )
        leak_mask = nvda_bull_rev['levels'].apply(
            lambda l: any(k in str(l) for k in expected_leak)
        )
        other_mask = ~supp_mask & ~leak_mask

        suppressed_still_firing = nvda_bull_rev[supp_mask]
        expected_firing = nvda_bull_rev[leak_mask]
        other_firing = nvda_bull_rev[other_mask]

        print(f'Still firing (should be suppressed): {fmt(stats(suppressed_still_firing))}')
        print(f'Firing as expected (not in suppress): {fmt(stats(expected_firing))}')
        if len(other_firing):
            print(f'Other/unknown: {fmt(stats(other_firing))}')
    else:
        print('  No NVDA bull REV signals in v3.4 — fully suppressed.')
    print()

    # ══════════════════════════════════════════════════════════════════════
    print(DIV)
    print('TASK 2: BEAR BRK SIGNALS DISAPPEARED? PM L / Yest L / Week Open')
    print(DIV)
    print()

    # v3.3c bear BRK
    bear_brk33 = df33cx[(df33cx['sig_type'] == 'BRK') & (df33cx['direction'] == 'bear')]
    bear_brk34 = df34x[(df34x['sig_type'] == 'BRK') & (df34x['direction'] == 'bear')]

    print(f'Total bear BRK: v3.3c={len(bear_brk33)}, v3.4={len(bear_brk34)}')
    print()

    # Level keywords to check
    level_checks = [
        ('PM Low (PML / PM L / pmLow)', ['PML', 'PM L', 'pmLow']),
        ('Yest Low (YL / Yest L)',       ['YL', 'Yest L']),
        ('Week Open (WO / Week O / WeekOpen)', ['WO', 'Week O', 'WeekOpen', 'Week Open']),
    ]

    print(f'{"Level group":<45} {"v3.3c N":>7}  {"v3.4 N":>7}  {"Delta":>7}  {"v3.3c Win%":>10}  {"v3.4 Win%":>10}')
    print(SDIV)
    for label, kws in level_checks:
        def has_kw(levels_val):
            return any(k in str(levels_val) for k in kws)
        grp33 = bear_brk33[bear_brk33['levels'].apply(has_kw)]
        grp34 = bear_brk34[bear_brk34['levels'].apply(has_kw)]
        st33  = stats(grp33)
        st34  = stats(grp34)
        delta = st34['n'] - st33['n']
        print(f'{label:<45} {st33["n"]:>7}  {st34["n"]:>7}  {delta:>+7}  '
              f'{st33["win_pct"]:>9.1f}%  {st34["win_pct"]:>9.1f}%')

    print()
    # Show the actual level strings for PM L to understand naming
    pm_kws = ['PML', 'PM L', 'pmLow']
    pm_lvls33 = bear_brk33[bear_brk33['levels'].apply(lambda l: any(k in str(l) for k in pm_kws))]['levels'].value_counts()
    pm_lvls34 = bear_brk34[bear_brk34['levels'].apply(lambda l: any(k in str(l) for k in pm_kws))]['levels'].value_counts()
    print('Exact level strings for PM Low signals:')
    print(f'  v3.3c: {pm_lvls33.to_dict()}')
    print(f'  v3.4:  {pm_lvls34.to_dict()}')
    print()

    # Also scan for any bear BRK level strings that include the magic keywords
    # in v3.3c to see if they might have been renamed in v3.4
    print('All bear BRK level strings containing "PM" or "Yest" or "Week":')
    def has_any(l):
        return any(k in str(l) for k in ['PM', 'Yest', 'Week'])
    print('  v3.3c top levels:')
    top33 = bear_brk33[bear_brk33['levels'].apply(has_any)]['levels'].value_counts().head(15)
    for lvl, cnt in top33.items():
        print(f'    {cnt:4d}x  {lvl}')
    print('  v3.4 top levels:')
    top34 = bear_brk34[bear_brk34['levels'].apply(has_any)]['levels'].value_counts().head(15)
    for lvl, cnt in top34.items():
        print(f'    {cnt:4d}x  {lvl}')
    print()

    # ══════════════════════════════════════════════════════════════════════
    print(DIV)
    print('TASK 3: NEW SIGNAL PROFITABILITY CONTEXT')
    print(DIV)
    print()

    # ── 3A: PD LH H BRK — bull BRK at PD Last Hour High ─────────────────
    print('--- 3A: PD LH H BRK (bull BRK at PD Last Hour High) ---')
    print()

    LH_KWS = ['PD LH H', 'PD LH', 'PDLastHr', 'Last Hr H', 'LastHr', 'LH H', 'LH']
    bull_brk34 = df34x[(df34x['sig_type'] == 'BRK') & (df34x['direction'] == 'bull')]

    def is_pdlh(levels_val):
        return any(k in str(levels_val) for k in LH_KWS)

    pdlh34 = bull_brk34[bull_brk34['levels'].apply(is_pdlh)].copy()
    print(f'Total PD LH H bull BRK signals (v3.4): {len(pdlh34)}')
    if len(pdlh34) > 0:
        print(f'Unique level strings: {sorted(pdlh34["levels"].unique())}')
    print()

    if len(pdlh34) > 0:
        pdlh34 = pdlh34.copy()
        pdlh34['tod'] = pdlh34['time_str'].apply(tod_bucket)

        print(f'{"Time bucket":<25} {"N":>4}  {"Win%":>6}  {"Net":>8}  {"/sig":>7}')
        print(SDIV)
        for bucket in ['morning (9:30-11)', 'midday  (11-14)', 'afternoon (14-16)']:
            grp = pdlh34[pdlh34['tod'] == bucket]
            st = stats(grp)
            marker = ' ★' if st['win_pct'] >= 55 else ''
            print(f'{bucket:<25} {st["n"]:>4}  {st["win_pct"]:>5.1f}%  '
                  f'{st["net_atr"]:>+8.1f}  {st["per_sig"]:>+7.3f}{marker}')
        print()
        print(f'Overall: {fmt(stats(pdlh34))}')
    else:
        print('  No PD LH H bull BRK signals found. Checking all LH-related level strings...')
        all_levels = df34x['levels'].dropna().unique()
        lh_related = [l for l in all_levels if 'LH' in str(l) or 'Last Hr' in str(l) or 'LastHr' in str(l)]
        print(f'  All level strings with LH/LastHr: {sorted(lh_related)[:20]}')
    print()

    # ── 3B: ORB L Reclaim — bull REV/BRK at ORB Low ──────────────────────
    print('--- 3B: ORB L Reclaim (bull at ORB Low) ---')
    print()

    ORB_KWS = ['OL', 'ORB L', 'ORB Low']
    orb_bull34 = df34x[
        (df34x['sig_type'].isin(['REV', 'EXREV', 'BRK'])) &
        (df34x['direction'] == 'bull') &
        (df34x['levels'].apply(lambda l: any(k in str(l) for k in ORB_KWS)))
    ].copy()

    print(f'Total ORB L bull signals (v3.4): {len(orb_bull34)}')
    if len(orb_bull34) > 0:
        print(f'Unique level strings: {sorted(orb_bull34["levels"].unique())}')
        print(f'Signal types: {orb_bull34["sig_type"].value_counts().to_dict()}')
    print()

    if len(orb_bull34) > 0:
        orb_bull34['tod'] = orb_bull34['time_str'].apply(tod_bucket)

        print('By time-of-day:')
        print(f'{"Time bucket":<25} {"N":>4}  {"Win%":>6}  {"Net":>8}  {"/sig":>7}')
        print(SDIV)
        for bucket in ['morning (9:30-11)', 'midday  (11-14)', 'afternoon (14-16)']:
            grp = orb_bull34[orb_bull34['tod'] == bucket]
            st = stats(grp)
            marker = ' ★' if st['win_pct'] >= 55 else ''
            print(f'{bucket:<25} {st["n"]:>4}  {st["win_pct"]:>5.1f}%  '
                  f'{st["net_atr"]:>+8.1f}  {st["per_sig"]:>+7.3f}{marker}')
        print()

        print('By symbol:')
        print(f'{"Symbol":<10} {"N":>4}  {"Win%":>6}  {"Net":>8}  {"/sig":>7}')
        print(SDIV)
        sym_grps = orb_bull34.groupby('symbol')
        rows = []
        for sym, grp in sym_grps:
            st = stats(grp)
            rows.append({'sym': sym, **st})
        rows.sort(key=lambda r: r['net_atr'], reverse=True)
        for r in rows:
            marker = ' ★' if r['win_pct'] >= 55 else ''
            print(f'{r["sym"]:<10} {r["n"]:>4}  {r["win_pct"]:>5.1f}%  '
                  f'{r["net_atr"]:>+8.1f}  {r["per_sig"]:>+7.3f}{marker}')
        print()
        print(f'Overall: {fmt(stats(orb_bull34))}')
    else:
        print('  No ORB L bull signals found. Checking all ORB-related level strings...')
        all_levels = df34x['levels'].dropna().unique()
        orb_related = [l for l in all_levels if 'ORB' in str(l) or 'OL' in str(l)]
        print(f'  All level strings with ORB/OL: {sorted(orb_related)[:20]}')
    print()

    print(DIV)
    print('Investigation complete.')
    print(DIV)


if __name__ == '__main__':
    main()
