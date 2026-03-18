#!/usr/bin/env python3
"""
v2.8a Signal Audit — Comprehensive analysis of KeyLevelBreakout Pine logs.

Uses ONLY v2.8a logs (with ramp=, QBS/MC, ⚡, ⚠ markers).
Cross-references with 1m/5m parquet cache for follow-through.
"""

import pandas as pd
import numpy as np
import re
import os
from datetime import datetime, timedelta
from pathlib import Path

# ─── Paths ──────────────────────────────────────────────
PROJ = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView")
DEBUG = PROJ / "debug"
CACHE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache")

# ─── v2.8a Log → Symbol Mapping (verified by Jan 26 BATS cross-reference) ───
V28A_FILES = {
    '1443e': 'GOOGL',
    'eefe5': 'SPY',
    '76bbd': 'QQQ',
    '768d3': 'TSLA',
    '67208': 'AMD',
    'a2495': 'AAPL',
    'cf9a2': 'META',
    '6f969': 'AMZN',
    '49428': 'MSFT',
    '35900': 'NVDA',
}

SYMBOLS = list(set(V28A_FILES.values()))
OUTPUT_FILE = DEBUG / "v28a-signal-audit.md"


def load_parquet(symbol, tf='1m'):
    """Load cached parquet data."""
    sym = symbol.lower()
    suffixes = {'5s': '5_secs_ib', '1m': '1_min_ib', '5m': '5_mins_ib'}
    if tf == '5s':
        path = CACHE / "bars_highres" / "5sec" / f"{sym}_{suffixes[tf]}.parquet"
    else:
        path = CACHE / "bars" / f"{sym}_{suffixes[tf]}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], utc=True)
        df = df.set_index('date').sort_index()
    return df


# ─── Signal Parsing ─────────────────────────────────────

def parse_all_logs():
    """Parse all v2.8a Pine log files."""
    all_rows = []

    for file_hash, symbol in V28A_FILES.items():
        fpath = DEBUG / f"pine-logs-Key Level Breakout_{file_hash}.csv"
        if not fpath.exists():
            print(f"  WARNING: {fpath.name} not found")
            continue

        df = pd.read_csv(fpath)
        for _, row in df.iterrows():
            msg = str(row.get('Message', ''))
            date_str = str(row.get('Date', ''))
            parsed = parse_line(msg, date_str, symbol, file_hash)
            if parsed:
                all_rows.append(parsed)

    result = pd.DataFrame(all_rows)
    print(f"  Parsed {len(result)} log lines from {len(V28A_FILES)} files")
    return result


def parse_line(msg, date_str, symbol, file_hash):
    """Parse a single log line into a structured dict."""
    if not msg.startswith('[KLB]'):
        return None

    # ── CONF lines ──
    if '[KLB] CONF' in msg:
        time_m = re.search(r'CONF\s+(\d+:\d+)', msg)
        direction = 'bull' if '▲' in msg else 'bear'
        if '✓★' in msg:
            result = 'star'
        elif '✓' in msg and '✗' not in msg:
            result = 'pass'
        elif '✗' in msg:
            result = 'fail'
        else:
            result = 'unknown'
        conf_type = 'QBS/MC' if 'QBS/MC' in msg else 'BRK'
        return {
            'symbol': symbol, 'hash': file_hash, 'datetime': date_str,
            'time': time_m.group(1) if time_m else None,
            'line_type': 'CONF', 'direction': direction,
            'conf_result': result, 'conf_source': conf_type,
        }

    # ── 5m CHECK lines ──
    if '5m CHECK' in msg:
        time_m = re.search(r'5m CHECK\s+(\d+:\d+)', msg)
        direction = 'bull' if '▲' in msg else 'bear'
        pnl_m = re.search(r'pnl=([-\d.]+)', msg)
        verdict_m = re.search(r'→\s*(HOLD|BAIL)', msg)
        return {
            'symbol': symbol, 'hash': file_hash, 'datetime': date_str,
            'time': time_m.group(1) if time_m else None,
            'line_type': '5mCHECK', 'direction': direction,
            'check_pnl': float(pnl_m.group(1)) if pnl_m else None,
            'check_verdict': verdict_m.group(1) if verdict_m else None,
        }

    # ── QBS/MC signal lines ──
    if '🔇 QBS' in msg or '🔊 MC' in msg:
        is_qbs = '🔇 QBS' in msg
        time_m = re.search(r'\[KLB\]\s+(\d+:\d+)', msg)
        direction = 'bull' if '▲' in msg else 'bear'
        return {
            'symbol': symbol, 'hash': file_hash, 'datetime': date_str,
            'time': time_m.group(1) if time_m else None,
            'line_type': 'QBS' if is_qbs else 'MC',
            'direction': direction,
            **extract_fields(msg),
        }

    # ── Retest ◆ lines ──
    if '◆' in msg and 'BRK' not in msg and '~ ~' not in msg:
        time_m = re.search(r'\[KLB\]\s+(\d+:\d+)', msg)
        direction = 'bull' if '▲' in msg else 'bear'
        return {
            'symbol': symbol, 'hash': file_hash, 'datetime': date_str,
            'time': time_m.group(1) if time_m else None,
            'line_type': 'RETEST', 'direction': direction,
        }

    # ── BRK / REV / VWAP signal lines ──
    if 'BRK' in msg or '~ ~' in msg:
        time_m = re.search(r'\[KLB\]\s+(\d+:\d+)', msg)
        direction = 'bull' if '▲' in msg else 'bear'

        if 'BRK' in msg:
            sig_type = 'BRK'
        elif '~ ~ VWAP' in msg:
            sig_type = 'VWAP'
        elif '~ ~' in msg:
            sig_type = 'REV'
        else:
            return None

        levels_m = re.search(r'(?:BRK|~ ~)\s+(.*?)(?:\s+vol=)', msg)
        levels = levels_m.group(1).strip() if levels_m else ''

        return {
            'symbol': symbol, 'hash': file_hash, 'datetime': date_str,
            'time': time_m.group(1) if time_m else None,
            'line_type': sig_type, 'direction': direction,
            'levels': levels,
            **extract_fields(msg),
        }

    return None


def extract_fields(msg):
    """Extract key=value fields from a log message."""
    fields = {}
    for key, pattern in [
        ('vol', r'vol=([\d.]+)x'), ('close_pos', r'pos=[v^](\d+)'),
        ('vwap', r'vwap=(above|below|na)'), ('ema', r'ema=(bull|bear|na)'),
        ('rs', r'rs=([+-]?\d+\.?\d*)%'), ('adx', r'adx=(\d+)'),
        ('body', r'body=(\d+)%'), ('ramp', r'ramp=([\d.]+)x'),
        ('range_atr', r'rangeATR=([\d.]+)'),
        ('sig_o', r'O([\d.]+)'), ('sig_h', r'H([\d.]+)'),
        ('sig_l', r'L([\d.]+)'), ('sig_c', r'C([\d.]+)'),
        ('atr', r'ATR=([\d.]+)'), ('raw_vol', r'rawVol=(\d+)'),
    ]:
        m = re.search(pattern, msg)
        if m:
            val = m.group(1)
            if key in ('vol', 'rs', 'ramp', 'range_atr', 'sig_o', 'sig_h', 'sig_l', 'sig_c', 'atr'):
                fields[key] = float(val)
            elif key in ('close_pos', 'adx', 'body', 'raw_vol'):
                fields[key] = int(val)
            else:
                fields[key] = val

    # Flags
    fields['is_bigmove'] = '⚡' in msg
    fields['is_bodywarn'] = '⚠' in msg
    fields['is_vol_dry'] = '🔇' in msg and 'QBS' not in msg  # 🔇 on BRK = vol drying glyph
    fields['is_vol_exp'] = '🔊' in msg and 'MC' not in msg   # 🔊 on BRK = vol explosive glyph
    fields['is_dim'] = ' dim' in msg or ' moddim' in msg or '?' in msg.split('ATR=')[-1] if 'ATR=' in msg else False

    return fields


# ─── Follow-Through ─────────────────────────────────────

def measure_follow_through(signals):
    """Measure MFE/MAE for BRK/REV/VWAP signals using 1m data."""
    sig_types = ['BRK', 'REV', 'VWAP']
    sigs = signals[signals['line_type'].isin(sig_types)].copy()

    results = []
    for sym in SYMBOLS:
        sym_sigs = sigs[sigs['symbol'] == sym]
        if len(sym_sigs) == 0:
            continue

        df_1m = load_parquet(sym, '1m')
        if df_1m is None:
            print(f"  No 1m data for {sym}")
            continue

        for _, sig in sym_sigs.iterrows():
            entry = sig.get('sig_c')
            atr = sig.get('atr')
            direction = sig.get('direction')
            if pd.isna(entry) or pd.isna(atr) or atr == 0:
                continue

            try:
                sig_dt = pd.to_datetime(sig['datetime'], utc=True)
                future = df_1m[df_1m.index > sig_dt].head(60)
                if len(future) < 3:
                    continue

                for window in [5, 15, 30]:
                    w = future.head(window)
                    if len(w) == 0:
                        continue
                    if direction == 'bull':
                        mfe = (w['high'].max() - entry) / atr
                        mae = (entry - w['low'].min()) / atr
                    else:
                        mfe = (entry - w['low'].min()) / atr
                        mae = (w['high'].max() - entry) / atr

                    results.append({
                        'symbol': sym, 'datetime': sig['datetime'],
                        'time': sig.get('time'), 'type': sig['line_type'],
                        'direction': direction, 'levels': sig.get('levels', ''),
                        'vol': sig.get('vol'), 'ema': sig.get('ema'),
                        'vwap': sig.get('vwap'), 'adx': sig.get('adx'),
                        'body': sig.get('body'), 'ramp': sig.get('ramp'),
                        'range_atr': sig.get('range_atr'),
                        'is_bigmove': sig.get('is_bigmove', False),
                        'is_bodywarn': sig.get('is_bodywarn', False),
                        'atr': atr, 'entry': entry,
                        'window': window,
                        'mfe': round(mfe, 4), 'mae': round(mae, 4),
                        'ratio': round(mfe / mae, 2) if mae > 0.001 else 99.9,
                    })
            except Exception:
                continue

    return pd.DataFrame(results)


# ─── Trade Simulation ────────────────────────────────────

def simulate_trades(signals):
    """Simulate for CONF ✓/✓★ BRK signals."""
    confs = signals[(signals['line_type'] == 'CONF') &
                    (signals['conf_result'].isin(['pass', 'star']))].copy()
    brks = signals[signals['line_type'] == 'BRK'].copy()

    trades = []
    for _, conf in confs.iterrows():
        sym = conf['symbol']
        try:
            conf_dt = pd.to_datetime(conf['datetime'], utc=True)
            conf_date = conf_dt.strftime('%Y-%m-%d')

            # Find most recent BRK before this CONF, same day+direction
            day_brks = brks[
                (brks['symbol'] == sym) &
                (brks['direction'] == conf['direction']) &
                (brks['datetime'].apply(lambda x: pd.to_datetime(x, utc=True).strftime('%Y-%m-%d')) == conf_date)
            ]
            if len(day_brks) == 0:
                continue

            brk = day_brks.iloc[-1]
            entry = brk.get('sig_c')
            atr = brk.get('atr')
            direction = brk['direction']
            if pd.isna(entry) or pd.isna(atr) or atr == 0:
                continue

            df_1m = load_parquet(sym, '1m')
            if df_1m is None:
                continue

            sig_dt = pd.to_datetime(brk['datetime'], utc=True)
            future = df_1m[df_1m.index > sig_dt].head(30)
            if len(future) < 2:
                continue

            # Strategy: SL 0.15 ATR, trail 0.25 ATR after +0.05 ATR, max 30m
            sl = 0.15 * atr
            trail_start_threshold = 0.05 * atr
            trail_dist = 0.25 * atr
            exit_price = None
            exit_reason = 'timeout'
            exit_bar = len(future)
            max_fav = 0
            trailing = False
            trail_stop = None

            for i, (_, bar) in enumerate(future.iterrows()):
                if direction == 'bull':
                    fav = bar['high'] - entry
                    adv = entry - bar['low']
                    max_fav = max(max_fav, fav)
                    if adv >= sl:
                        exit_price = entry - sl
                        exit_reason = 'stop_loss'
                        exit_bar = i + 1
                        break
                    if fav >= trail_start_threshold:
                        trailing = True
                        ns = bar['high'] - trail_dist
                        trail_stop = max(trail_stop or 0, ns)
                    if trailing and trail_stop and bar['low'] <= trail_stop:
                        exit_price = trail_stop
                        exit_reason = 'trail_stop'
                        exit_bar = i + 1
                        break
                else:
                    fav = entry - bar['low']
                    adv = bar['high'] - entry
                    max_fav = max(max_fav, fav)
                    if adv >= sl:
                        exit_price = entry + sl
                        exit_reason = 'stop_loss'
                        exit_bar = i + 1
                        break
                    if fav >= trail_start_threshold:
                        trailing = True
                        ns = bar['low'] + trail_dist
                        trail_stop = min(trail_stop or 9999, ns)
                    if trailing and trail_stop and bar['high'] >= trail_stop:
                        exit_price = trail_stop
                        exit_reason = 'trail_stop'
                        exit_bar = i + 1
                        break

            if exit_price is None:
                exit_price = future.iloc[-1]['close']

            pnl = (exit_price - entry) if direction == 'bull' else (entry - exit_price)
            pnl_atr = pnl / atr

            trades.append({
                'symbol': sym, 'signal_time': brk['datetime'],
                'conf_time': conf['datetime'], 'conf_result': conf['conf_result'],
                'conf_source': conf.get('conf_source', 'BRK'),
                'direction': direction, 'levels': brk.get('levels', ''),
                'entry': entry, 'exit': round(exit_price, 2),
                'pnl': round(pnl, 2), 'pnl_atr': round(pnl_atr, 4),
                'mfe_atr': round(max_fav / atr, 4),
                'exit_reason': exit_reason, 'exit_bar': exit_bar,
                'atr': atr, 'vol': brk.get('vol'), 'ema': brk.get('ema'),
                'time': brk.get('time'),
            })
        except Exception:
            continue

    return pd.DataFrame(trades)


# ─── Missed Signals ─────────────────────────────────────

def find_missed_runs(signals):
    """Find stretches ≥1 ATR move with no signal, using 5m data."""
    all_runs = []

    for sym in SYMBOLS:
        df_5m = load_parquet(sym, '5m')
        if df_5m is None:
            continue

        df = df_5m.copy()
        df['range'] = df['high'] - df['low']
        df['atr14'] = df['range'].rolling(14).mean()

        # Market hours only
        if hasattr(df.index, 'hour'):
            market = df[(df.index.hour >= 9) & (df.index.hour < 16)].copy()
        else:
            continue

        # Signal times for this symbol (±5 min tolerance)
        sym_sigs = signals[(signals['symbol'] == sym) &
                           (signals['line_type'].isin(['BRK', 'REV', 'VWAP', 'QBS', 'MC']))]
        signal_times = set()
        sig_dates = set()
        for _, sig in sym_sigs.iterrows():
            try:
                sdt = pd.to_datetime(sig['datetime'], utc=True)
                sig_dates.add(sdt.date())
                for off in range(-5, 6):
                    signal_times.add((sdt + timedelta(minutes=off)).strftime('%Y-%m-%d %H:%M'))
            except:
                pass

        # Only scan dates covered by Pine logs
        if not sig_dates:
            continue
        min_date, max_date = min(sig_dates), max(sig_dates)

        # Scan for signal-free runs
        for date, day_df in market.groupby(market.index.date):
            if date < min_date or date > max_date:
                continue
            if len(day_df) < 5:
                continue
            atr = day_df['atr14'].dropna().mean()
            if pd.isna(atr) or atr == 0:
                continue

            run_start = None
            run_high = run_low = None
            count = 0

            for idx, row in day_df.iterrows():
                bt = idx.strftime('%Y-%m-%d %H:%M')
                if bt in signal_times:
                    if run_start and count >= 3:
                        rng = (run_high - run_low) / atr
                        if rng >= 1.0:
                            all_runs.append({
                                'symbol': sym, 'date': str(date),
                                'start': run_start.strftime('%H:%M'),
                                'end': idx.strftime('%H:%M'),
                                'bars': count, 'range_atr': round(rng, 2),
                                'high': run_high, 'low': run_low, 'atr': round(atr, 2),
                            })
                    run_start = run_high = run_low = None
                    count = 0
                else:
                    if run_start is None:
                        run_start = idx
                        run_high = row['high']
                        run_low = row['low']
                    else:
                        run_high = max(run_high, row['high'])
                        run_low = min(run_low, row['low'])
                    count += 1

            # End-of-day check
            if run_start and count >= 3:
                rng = (run_high - run_low) / atr
                if rng >= 1.0:
                    all_runs.append({
                        'symbol': sym, 'date': str(date),
                        'start': run_start.strftime('%H:%M'),
                        'end': day_df.index[-1].strftime('%H:%M'),
                        'bars': count, 'range_atr': round(rng, 2),
                        'high': run_high, 'low': run_low, 'atr': round(atr, 2),
                    })

    return pd.DataFrame(all_runs)


# ─── Report ─────────────────────────────────────────────

def generate_report(signals, ft, trades, runs):
    """Generate markdown report."""
    L = ["# v2.8a Signal Audit Report\n"]
    L.append(f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    L.append(f"> Files: {len(V28A_FILES)} v2.8a logs, 10 symbols")
    L.append(f"> Total log lines: {len(signals)}\n")

    # ── 1. Signal Overview ──
    L.append("## 1. Signal Overview\n")
    sigs = signals[signals['line_type'].isin(['BRK', 'REV', 'VWAP', 'QBS', 'MC'])]
    if len(sigs) > 0:
        ct = sigs.groupby(['symbol', 'line_type']).size().unstack(fill_value=0)
        L.append("| Symbol | BRK | REV | VWAP | QBS | MC | Total |")
        L.append("|--------|-----|-----|------|-----|-----|-------|")
        for sym in sorted(SYMBOLS):
            if sym in ct.index:
                r = ct.loc[sym]
                t = r.sum()
                L.append(f"| {sym} | {r.get('BRK',0)} | {r.get('REV',0)} | {r.get('VWAP',0)} | {r.get('QBS',0)} | {r.get('MC',0)} | {t} |")
        L.append(f"\n**Total signals:** {len(sigs)}")

        # By hour
        sigs_h = sigs.copy()
        sigs_h['hour'] = sigs_h['time'].apply(lambda x: int(str(x).split(':')[0]) if pd.notna(x) and ':' in str(x) else None)
        hc = sigs_h.groupby('hour').size()
        L.append("\n### By Hour\n| Hour | Count | % |")
        L.append("|------|-------|---|")
        for h in sorted(hc.index.dropna()):
            L.append(f"| {int(h)}:xx | {hc[h]} | {hc[h]/len(sigs)*100:.0f}% |")
        L.append("")

    # ── 2. QBS/MC Analysis ──
    L.append("## 2. QBS/MC Signals\n")
    qbs = signals[signals['line_type'] == 'QBS']
    mc = signals[signals['line_type'] == 'MC']
    L.append(f"- **QBS (🔇 Quiet Before Storm):** {len(qbs)} signals")
    L.append(f"- **MC (🔊 Momentum Cascade):** {len(mc)} signals\n")

    if len(mc) > 0:
        L.append("### MC Signals Near Open (9:30-9:45) — SPY/QQQ/AMD/AAPL\n")
        focus = ['SPY', 'QQQ', 'AMD', 'AAPL']
        mc_open = mc[mc['symbol'].isin(focus)].copy()
        mc_open['hour'] = mc_open['time'].apply(lambda x: int(str(x).split(':')[0]) if pd.notna(x) else 99)
        mc_open['minute'] = mc_open['time'].apply(lambda x: int(str(x).split(':')[1]) if pd.notna(x) and ':' in str(x) else 99)
        mc_open = mc_open[(mc_open['hour'] == 9) & (mc_open['minute'] <= 45)]

        if len(mc_open) > 0:
            L.append("| Symbol | Date | Time | Dir | Ramp | Vol | RangeATR | Body | Dim? |")
            L.append("|--------|------|------|-----|------|-----|----------|------|------|")
            mc_open['date_str'] = mc_open['datetime'].apply(lambda x: str(x)[:10])
            for _, r in mc_open.sort_values('datetime').iterrows():
                dim = "dim" if r.get('is_dim') else ""
                L.append(f"| {r['symbol']} | {r['date_str']} | {r['time']} | {r['direction']} | {r.get('ramp','')}x | {r.get('vol','')}x | {r.get('range_atr','')} | {r.get('body','')}% | {dim} |")

            # Check for opposing pairs on same day
            L.append("\n### Opposing MC Pairs at Open\n")
            found_opposing = False
            for sym in focus:
                sym_open = mc_open[mc_open['symbol'] == sym]
                for date in sym_open['date_str'].unique():
                    day_ev = sym_open[sym_open['date_str'] == date]
                    dirs = day_ev['direction'].unique()
                    if 'bull' in dirs and 'bear' in dirs:
                        found_opposing = True
                        L.append(f"**{sym} {date}:** Bull AND Bear MC at open!")
                        for _, ev in day_ev.iterrows():
                            L.append(f"  - {ev['time']} {ev['direction']} ramp={ev.get('ramp','')}x vol={ev.get('vol','')}x rangeATR={ev.get('range_atr','')}")
                        L.append("")
            if not found_opposing:
                L.append("No opposing MC pairs found at open.\n")
        else:
            L.append("No MC signals near open for SPY/QQQ/AMD/AAPL.\n")

    # QBS/MC CONF results
    qmc_confs = signals[(signals['line_type'] == 'CONF') & (signals['conf_source'] == 'QBS/MC')]
    if len(qmc_confs) > 0:
        L.append("### QBS/MC Confirmation Results\n")
        for res in ['star', 'pass', 'fail']:
            n = len(qmc_confs[qmc_confs['conf_result'] == res])
            label = {'star': '✓★', 'pass': '✓', 'fail': '✗'}[res]
            L.append(f"- {label}: {n}")
        total_qmc = len(qmc_confs)
        pass_qmc = len(qmc_confs[qmc_confs['conf_result'].isin(['pass', 'star'])])
        L.append(f"- **CONF rate:** {pass_qmc/total_qmc*100:.0f}% ({pass_qmc}/{total_qmc})\n")

    # ── 3. v2.8 Flags Analysis ──
    L.append("## 3. v2.8 Flag Analysis\n")
    brk_sigs = signals[signals['line_type'] == 'BRK']
    if len(brk_sigs) > 0:
        bigmove = brk_sigs[brk_sigs.get('is_bigmove', False) == True]
        bodywarn = brk_sigs[brk_sigs.get('is_bodywarn', False) == True]
        L.append(f"- **⚡ Big-move BRKs:** {len(bigmove)} / {len(brk_sigs)} ({len(bigmove)/len(brk_sigs)*100:.0f}%)")
        L.append(f"- **⚠ Body-warn BRKs:** {len(bodywarn)} / {len(brk_sigs)} ({len(bodywarn)/len(brk_sigs)*100:.0f}%)\n")

    # ── 4. CONF Analysis ──
    L.append("## 4. Confirmation Analysis\n")
    confs = signals[signals['line_type'] == 'CONF']
    if len(confs) > 0:
        brk_confs = confs[confs['conf_source'] == 'BRK']
        for res in ['star', 'pass', 'fail']:
            n = len(brk_confs[brk_confs['conf_result'] == res])
            label = {'star': '✓★', 'pass': '✓', 'fail': '✗'}[res]
            L.append(f"- BRK {label}: {n}")
        total_brk = len(brk_confs)
        pass_brk = len(brk_confs[brk_confs['conf_result'].isin(['pass', 'star'])])
        if total_brk > 0:
            L.append(f"- **BRK CONF rate:** {pass_brk/total_brk*100:.0f}% ({pass_brk}/{total_brk})")

        L.append("\n### CONF Rate by Symbol\n")
        L.append("| Symbol | ✓★ | ✓ | ✗ | Total | Pass% |")
        L.append("|--------|-----|---|---|-------|-------|")
        for sym in sorted(SYMBOLS):
            sc = brk_confs[brk_confs['symbol'] == sym]
            if len(sc) > 0:
                star = len(sc[sc['conf_result'] == 'star'])
                p = len(sc[sc['conf_result'] == 'pass'])
                f = len(sc[sc['conf_result'] == 'fail'])
                t = len(sc)
                L.append(f"| {sym} | {star} | {p} | {f} | {t} | {(star+p)/t*100:.0f}% |")
        L.append("")

    # ── 5. 5m Checkpoint ──
    L.append("## 5. Five-Minute Checkpoint\n")
    checks = signals[signals['line_type'] == '5mCHECK']
    if len(checks) > 0:
        hold = len(checks[checks['check_verdict'] == 'HOLD'])
        bail = len(checks[checks['check_verdict'] == 'BAIL'])
        t = hold + bail
        if t > 0:
            L.append(f"- HOLD: {hold} ({hold/t*100:.0f}%)")
            L.append(f"- BAIL: {bail} ({bail/t*100:.0f}%)")
            avg_hold = checks[checks['check_verdict'] == 'HOLD']['check_pnl'].mean()
            avg_bail = checks[checks['check_verdict'] == 'BAIL']['check_pnl'].mean()
            L.append(f"- Avg P&L at 5m (HOLD): {avg_hold:.3f} ATR")
            L.append(f"- Avg P&L at 5m (BAIL): {avg_bail:.3f} ATR\n")

    # ── 6. Follow-Through ──
    L.append("## 6. Follow-Through (MFE/MAE)\n")
    if len(ft) > 0:
        L.append("### By Window\n| Window | N | MFE | MAE | MFE/MAE | Win% |")
        L.append("|--------|---|-----|-----|---------|------|")
        for w in [5, 15, 30]:
            wd = ft[ft['window'] == w]
            if len(wd) > 0:
                L.append(f"| {w}m | {len(wd)} | {wd['mfe'].mean():.3f} | {wd['mae'].mean():.3f} | {wd['mfe'].mean()/wd['mae'].mean():.2f} | {(wd['mfe']>wd['mae']).mean()*100:.0f}% |")

        ft30 = ft[ft['window'] == 30]
        if len(ft30) > 0:
            L.append("\n### 30m by Type\n| Type | N | MFE | MAE | Win% |")
            L.append("|------|---|-----|-----|------|")
            for t in ['BRK', 'REV', 'VWAP']:
                td = ft30[ft30['type'] == t]
                if len(td) > 0:
                    L.append(f"| {t} | {len(td)} | {td['mfe'].mean():.3f} | {td['mae'].mean():.3f} | {(td['mfe']>td['mae']).mean()*100:.0f}% |")

            L.append("\n### 30m by Symbol\n| Symbol | N | MFE | MAE | Win% |")
            L.append("|--------|---|-----|-----|------|")
            for sym in sorted(SYMBOLS):
                sd = ft30[ft30['symbol'] == sym]
                if len(sd) > 0:
                    L.append(f"| {sym} | {len(sd)} | {sd['mfe'].mean():.3f} | {sd['mae'].mean():.3f} | {(sd['mfe']>sd['mae']).mean()*100:.0f}% |")

            # Evidence stack filters at 30m (BRK only)
            brk30 = ft30[ft30['type'] == 'BRK']
            if len(brk30) > 0:
                L.append("\n### 30m BRK by Filter\n| Filter | N | MFE | Win% |")
                L.append("|--------|---|-----|------|")
                aligned = brk30[((brk30['direction']=='bull')&(brk30['ema']=='bull'))|((brk30['direction']=='bear')&(brk30['ema']=='bear'))]
                counter = brk30[((brk30['direction']=='bull')&(brk30['ema']=='bear'))|((brk30['direction']=='bear')&(brk30['ema']=='bull'))]
                if len(aligned): L.append(f"| EMA aligned | {len(aligned)} | {aligned['mfe'].mean():.3f} | {(aligned['mfe']>aligned['mae']).mean()*100:.0f}% |")
                if len(counter): L.append(f"| EMA counter | {len(counter)} | {counter['mfe'].mean():.3f} | {(counter['mfe']>counter['mae']).mean()*100:.0f}% |")

                valigned = brk30[((brk30['direction']=='bull')&(brk30['vwap']=='above'))|((brk30['direction']=='bear')&(brk30['vwap']=='below'))]
                vcounter = brk30[((brk30['direction']=='bull')&(brk30['vwap']=='below'))|((brk30['direction']=='bear')&(brk30['vwap']=='above'))]
                if len(valigned): L.append(f"| VWAP aligned | {len(valigned)} | {valigned['mfe'].mean():.3f} | {(valigned['mfe']>valigned['mae']).mean()*100:.0f}% |")
                if len(vcounter): L.append(f"| VWAP counter | {len(vcounter)} | {vcounter['mfe'].mean():.3f} | {(vcounter['mfe']>vcounter['mae']).mean()*100:.0f}% |")

                for vl, lo, hi in [('<2x', 0, 2), ('2-5x', 2, 5), ('5-10x', 5, 10), ('10x+', 10, 999)]:
                    vd = brk30[(brk30['vol'] >= lo) & (brk30['vol'] < hi)]
                    if len(vd): L.append(f"| Vol {vl} | {len(vd)} | {vd['mfe'].mean():.3f} | {(vd['mfe']>vd['mae']).mean()*100:.0f}% |")

                # ⚡ big-move vs normal
                bm = brk30[brk30['is_bigmove'] == True]
                nm = brk30[brk30['is_bigmove'] != True]
                if len(bm): L.append(f"| ⚡ Big-move | {len(bm)} | {bm['mfe'].mean():.3f} | {(bm['mfe']>bm['mae']).mean()*100:.0f}% |")
                if len(nm): L.append(f"| Normal move | {len(nm)} | {nm['mfe'].mean():.3f} | {(nm['mfe']>nm['mae']).mean()*100:.0f}% |")

                # ⚠ body warn
                bw = brk30[brk30['is_bodywarn'] == True]
                nw = brk30[brk30['is_bodywarn'] != True]
                if len(bw): L.append(f"| ⚠ Body≥80% | {len(bw)} | {bw['mfe'].mean():.3f} | {(bw['mfe']>bw['mae']).mean()*100:.0f}% |")
                if len(nw): L.append(f"| Body<80% | {len(nw)} | {nw['mfe'].mean():.3f} | {(nw['mfe']>nw['mae']).mean()*100:.0f}% |")

        L.append("")

    # ── 7. Trade Simulation ──
    L.append("## 7. Trade Simulation (CONF ✓/✓★)\n")
    if len(trades) > 0:
        total_pnl = trades['pnl_atr'].sum()
        win = (trades['pnl_atr'] > 0).mean() * 100
        L.append(f"- **Trades:** {len(trades)}")
        L.append(f"- **Win rate:** {win:.0f}%")
        L.append(f"- **Total P&L:** {total_pnl:.2f} ATR")
        L.append(f"- **Avg P&L:** {trades['pnl_atr'].mean():.3f} ATR")
        winners = trades[trades['pnl_atr'] > 0]
        losers = trades[trades['pnl_atr'] <= 0]
        if len(winners): L.append(f"- **Avg winner:** +{winners['pnl_atr'].mean():.3f} ATR")
        if len(losers): L.append(f"- **Avg loser:** {losers['pnl_atr'].mean():.3f} ATR\n")

        L.append("### By Exit Reason\n| Reason | N | Avg P&L | Win% |")
        L.append("|--------|---|---------|------|")
        for reason in ['trail_stop', 'stop_loss', 'timeout']:
            rd = trades[trades['exit_reason'] == reason]
            if len(rd): L.append(f"| {reason} | {len(rd)} | {rd['pnl_atr'].mean():.3f} | {(rd['pnl_atr']>0).mean()*100:.0f}% |")

        L.append("\n### By Symbol\n| Symbol | N | Win% | Avg P&L | Total |")
        L.append("|--------|---|------|---------|-------|")
        for sym in sorted(SYMBOLS):
            sd = trades[trades['symbol'] == sym]
            if len(sd): L.append(f"| {sym} | {len(sd)} | {(sd['pnl_atr']>0).mean()*100:.0f}% | {sd['pnl_atr'].mean():.3f} | {sd['pnl_atr'].sum():.2f} |")

        L.append("\n### By Hour\n| Hour | N | Win% | Avg P&L |")
        L.append("|------|---|------|---------|")
        trades['hour'] = trades['time'].apply(lambda x: int(str(x).split(':')[0]) if pd.notna(x) else None)
        for h in sorted(trades['hour'].dropna().unique()):
            hd = trades[trades['hour'] == h]
            L.append(f"| {int(h)}:xx | {len(hd)} | {(hd['pnl_atr']>0).mean()*100:.0f}% | {hd['pnl_atr'].mean():.3f} |")

        # By CONF type
        L.append("\n### By CONF Type\n| Type | N | Win% | Total P&L |")
        L.append("|------|---|------|-----------|")
        for ct in ['star', 'pass']:
            cd = trades[trades['conf_result'] == ct]
            if len(cd):
                label = '✓★' if ct == 'star' else '✓'
                L.append(f"| {label} | {len(cd)} | {(cd['pnl_atr']>0).mean()*100:.0f}% | {cd['pnl_atr'].sum():.2f} |")
        L.append("")

    # ── 8. Missed Signals ──
    L.append("## 8. Missed Signals (≥1 ATR runs without signal)\n")
    if len(runs) > 0:
        L.append(f"**Total missed runs:** {len(runs)}\n")

        L.append("### Top 25 Missed Runs\n| Symbol | Date | Start | End | Bars | Range (ATR) |")
        L.append("|--------|------|-------|-----|------|-------------|")
        for _, r in runs.nlargest(25, 'range_atr').iterrows():
            L.append(f"| {r['symbol']} | {r['date']} | {r['start']} | {r['end']} | {r['bars']} | {r['range_atr']} |")

        L.append("\n### By Symbol\n| Symbol | Runs | Avg Range | Max Range |")
        L.append("|--------|------|-----------|-----------|")
        for sym in sorted(SYMBOLS):
            sr = runs[runs['symbol'] == sym]
            if len(sr): L.append(f"| {sym} | {len(sr)} | {sr['range_atr'].mean():.2f} | {sr['range_atr'].max():.2f} |")

        # User-mentioned areas
        L.append("\n### User-Mentioned Areas\n")
        areas = [('SPY','10:30','13:40'), ('QQQ','10:30','13:40'), ('NVDA','10:55','11:05'),
                 ('AAPL','10:10','12:30'), ('AAPL','12:30','14:40'), ('TSLA','10:44','11:25')]
        for sym, s, e in areas:
            overlap = runs[(runs['symbol']==sym) & (runs['start']<=e) & (runs['end']>=s)]
            if len(overlap) > 0:
                for _, r in overlap.iterrows():
                    L.append(f"- **{sym} {r['date']} {r['start']}-{r['end']}:** {r['range_atr']} ATR, {r['bars']} bars — NO SIGNAL")
            else:
                L.append(f"- {sym} {s}-{e}: No missed runs found")
        L.append("")

    return '\n'.join(L)


# ─── MAIN ────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("v2.8a Signal Audit")
    print("=" * 60)

    print("\n[1/5] Parsing v2.8a Pine logs...")
    signals = parse_all_logs()

    print("\n[2/5] Measuring follow-through...")
    ft = measure_follow_through(signals)
    print(f"  {len(ft)} measurements")

    print("\n[3/5] Simulating trades...")
    trades = simulate_trades(signals)
    print(f"  {len(trades)} trades simulated")

    print("\n[4/5] Scanning for missed signals...")
    runs = find_missed_runs(signals)
    print(f"  {len(runs)} missed runs found")

    print("\n[5/5] Saving results...")
    signals.to_csv(DEBUG / "v28a-signals.csv", index=False)
    ft.to_csv(DEBUG / "v28a-follow-through.csv", index=False)
    trades.to_csv(DEBUG / "v28a-trades.csv", index=False)
    runs.to_csv(DEBUG / "v28a-missed-runs.csv", index=False)

    report = generate_report(signals, ft, trades, runs)
    with open(OUTPUT_FILE, 'w') as f:
        f.write(report)

    print(f"\nReport: {OUTPUT_FILE}")
    print("CSVs: debug/v28a-*.csv")
    print("Done!")


if __name__ == '__main__':
    main()
