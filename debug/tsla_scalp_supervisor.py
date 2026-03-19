"""
TSLA Open Scalp Supervisor
Runs parameter sweeps, scores each config, reports findings.
Notifies via Telegram at milestones.
"""

import sys
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime
from dataclasses import asdict

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent))
from tsla_scalp_backtest import Config, load_data, run_backtest, score_trades

NOTIFY = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/personal_assistant/scripts/notify.py')
OUT = Path(__file__).parent
RESULTS_FILE = OUT / 'tsla_scalp_results.tsv'
REPORT_FILE = OUT / 'tsla-scalp-optimization-report.md'

# ─────────────────────────────────────────────
# EXPERIMENT DEFINITIONS
# ─────────────────────────────────────────────

def build_experiments():
    """Build all experiment configurations."""
    experiments = []

    # ── Baseline ──
    experiments.append(('BASELINE: v1.2c defaults', Config()))

    # ── Phase 1: ORB Width Sweep ──
    for w in [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]:
        experiments.append((f'ORB_WIDTH={w}', Config(min_orb_width=w)))

    # ── Phase 2: Hold Time Sweep (the big one — much longer holds) ──
    for h in [3, 5, 8, 10, 12, 15, 20, 25, 30, 45, 60, 90, 120, 180, 0]:
        # 0 = EOD
        label = f'HOLD={h}bars' if h > 0 else 'HOLD=EOD'
        experiments.append((label, Config(hold_bars=h)))

    # ── Phase 3: SL Mode ──
    for mode in ['orb_low', 'orb_low_025', 'orb_low_050', 'fixed_2']:
        experiments.append((f'SL={mode}', Config(sl_mode=mode)))

    # ── Phase 4: Fallback SL ──
    for fb in [1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]:
        experiments.append((f'FALLBACK_SL={fb}', Config(sl_fallback=fb)))

    # ── Phase 5: Accel Window ──
    experiments.append(('ACCEL=4m', Config(accel_window='4m')))
    experiments.append(('ACCEL=2m (baseline)', Config(accel_window='2m')))

    # ── Phase 6: Path Efficiency Filter ──
    experiments.append(('PATH_EFF=on', Config(use_path_eff=True)))
    experiments.append(('PATH_EFF=on_wide', Config(use_path_eff=True, path_eff_lo=0.05, path_eff_hi=0.30)))

    # ── Phase 7: Fakeout Definition ──
    experiments.append(('FAKEOUT=new_low_required (v1.2c)', Config(fakeout_require_new_low=True)))
    experiments.append(('FAKEOUT=any_updn (v1.1k)', Config(fakeout_require_new_low=False)))

    # ── Phase 8: Combined Best — test promising combos ──
    # These are filled after Phase 1-7 results, but we can pre-define likely winners
    for h in [10, 15, 20, 30, 45, 60, 0]:
        for sl in ['orb_low', 'orb_low_025']:
            label = f'COMBO: hold={h if h > 0 else "EOD"} sl={sl}'
            experiments.append((label, Config(hold_bars=h, sl_mode=sl)))

    # ── Phase 9: Hold time + path efficiency combos ──
    for h in [15, 20, 30, 45, 60, 0]:
        experiments.append((f'COMBO: hold={h if h > 0 else "EOD"} path_eff=on',
                           Config(hold_bars=h, use_path_eff=True)))

    return experiments


def notify(msg):
    """Send Telegram notification."""
    try:
        subprocess.run([sys.executable, str(NOTIFY), msg],
                      capture_output=True, timeout=15)
    except Exception as e:
        print(f"  Notify failed: {e}")


def run_experiment(name, cfg, df1m, df15, dfvix, dfspy, dfqqq, train_end, val_end):
    """Run one experiment, return train/val metrics."""
    # Train period
    trades_train = run_backtest(cfg, df1m, df15, dfvix, dfspy, dfqqq,
                                end_date=train_end)
    m_train = score_trades(trades_train)

    # Val period
    trades_val = run_backtest(cfg, df1m, df15, dfvix, dfspy, dfqqq,
                              start_date=train_end)
    m_val = score_trades(trades_val)

    # Full period
    trades_all = run_backtest(cfg, df1m, df15, dfvix, dfspy, dfqqq)
    m_all = score_trades(trades_all)

    return m_train, m_val, m_all, trades_all


def main():
    print("=" * 70)
    print("TSLA OPEN SCALP OPTIMIZATION SUPERVISOR")
    print("=" * 70)
    start_time = time.time()

    # Load data once
    print("\nLoading data...")
    df1m, df15, dfvix, dfspy, dfqqq = load_data()
    print("Data loaded.")

    # Train/val split: train through Sep 2025, val Oct 2025+
    TRAIN_END = '2025-09-30'
    VAL_END = None  # all remaining

    experiments = build_experiments()
    print(f"\nTotal experiments: {len(experiments)}")

    notify(f"TSLA Scalp Optimizer starting: {len(experiments)} experiments. "
           f"Baseline=v1.2c. Train<=Sep2025, Val=Oct2025+.")

    # Results storage
    results = []
    header = "name\ttrain_n\ttrain_win\ttrain_avg\ttrain_score\tval_n\tval_win\tval_avg\tval_score\tall_n\tall_win\tall_avg\tall_score\tall_sharpe\tall_worst\n"

    with open(RESULTS_FILE, 'w') as f:
        f.write(header)

    # Run all experiments
    best_val_score = -999
    best_name = ''
    best_cfg = None

    for i, (name, cfg) in enumerate(experiments):
        print(f"\n[{i+1}/{len(experiments)}] {name}")
        try:
            m_train, m_val, m_all, trades = run_experiment(
                name, cfg, df1m, df15, dfvix, dfspy, dfqqq, TRAIN_END, VAL_END)

            line = (f"{name}\t{m_train['n']}\t{m_train['win_pct']}\t{m_train['avg_pnl']}\t{m_train['score']}\t"
                    f"{m_val['n']}\t{m_val['win_pct']}\t{m_val['avg_pnl']}\t{m_val['score']}\t"
                    f"{m_all['n']}\t{m_all['win_pct']}\t{m_all['avg_pnl']}\t{m_all['score']}\t"
                    f"{m_all['sharpe']}\t{m_all['worst_pct']}\n")

            with open(RESULTS_FILE, 'a') as f:
                f.write(line)

            results.append({
                'name': name,
                'train': m_train,
                'val': m_val,
                'all': m_all,
                'cfg': asdict(cfg),
            })

            # Track best
            if m_val['score'] > best_val_score:
                best_val_score = m_val['score']
                best_name = name
                best_cfg = cfg

            print(f"  Train: n={m_train['n']} win={m_train['win_pct']}% avg=${m_train['avg_pnl']} score={m_train['score']}")
            print(f"  Val:   n={m_val['n']} win={m_val['win_pct']}% avg=${m_val['avg_pnl']} score={m_val['score']}")
            print(f"  All:   n={m_all['n']} win={m_all['win_pct']}% avg=${m_all['avg_pnl']} sharpe={m_all['sharpe']} worst={m_all['worst_pct']}%")

        except Exception as e:
            print(f"  ERROR: {e}")
            with open(RESULTS_FILE, 'a') as f:
                f.write(f"{name}\tERROR\t{str(e)}\n")

        # Milestone notifications every 20 experiments
        if (i + 1) % 20 == 0:
            elapsed = (time.time() - start_time) / 60
            notify(f"TSLA Scalp: {i+1}/{len(experiments)} done ({elapsed:.0f}min). "
                   f"Best so far: {best_name} (val_score={best_val_score:.1f})")

    # ─────────────────────────────────────────────
    # GENERATE REPORT
    # ─────────────────────────────────────────────

    elapsed = (time.time() - start_time) / 60
    print(f"\n{'='*70}")
    print(f"ALL EXPERIMENTS COMPLETE in {elapsed:.1f} minutes")
    print(f"{'='*70}")

    report = []
    report.append("# TSLA Open Scalp — Optimization Report")
    report.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
                  f"{len(experiments)} experiments | {elapsed:.0f} min runtime*\n")

    # Sort by val score
    results_sorted = sorted(results, key=lambda x: x['val']['score'], reverse=True)

    # ── Top 10 by val score ──
    report.append("## Top 10 Configurations (by validation score)\n")
    report.append("| Rank | Config | Val Trades | Val Win% | Val Avg | Val Score | All Sharpe | All Worst% |")
    report.append("|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(results_sorted[:10]):
        report.append(f"| {i+1} | {r['name']} | {r['val']['n']} | {r['val']['win_pct']}% | "
                      f"${r['val']['avg_pnl']} | {r['val']['score']} | {r['all']['sharpe']} | {r['all']['worst_pct']}% |")

    # ── Phase results ──
    phases = {
        'ORB_WIDTH': [r for r in results if r['name'].startswith('ORB_WIDTH')],
        'HOLD': [r for r in results if r['name'].startswith('HOLD=')],
        'SL': [r for r in results if r['name'].startswith('SL=')],
        'FALLBACK_SL': [r for r in results if r['name'].startswith('FALLBACK_SL')],
        'ACCEL': [r for r in results if r['name'].startswith('ACCEL')],
        'PATH_EFF': [r for r in results if r['name'].startswith('PATH_EFF')],
        'FAKEOUT': [r for r in results if r['name'].startswith('FAKEOUT')],
        'COMBO': [r for r in results if r['name'].startswith('COMBO')],
    }

    for phase_name, phase_results in phases.items():
        if not phase_results:
            continue
        report.append(f"\n## Phase: {phase_name}\n")
        report.append("| Config | All n | All Win% | All Avg | All Score | All Sharpe | All Worst% |")
        report.append("|---|---|---|---|---|---|---|")
        phase_sorted = sorted(phase_results, key=lambda x: x['all']['score'], reverse=True)
        for r in phase_sorted:
            report.append(f"| {r['name']} | {r['all']['n']} | {r['all']['win_pct']}% | "
                          f"${r['all']['avg_pnl']} | {r['all']['score']} | {r['all']['sharpe']} | {r['all']['worst_pct']}% |")

    # ── Best config details ──
    if best_cfg:
        report.append(f"\n## Best Configuration: {best_name}\n")
        report.append("```json")
        best_dict = asdict(best_cfg)
        # Only show non-default values
        default_cfg = Config()
        default_dict = asdict(default_cfg)
        diff = {k: v for k, v in best_dict.items() if v != default_dict[k]}
        report.append(json.dumps(diff, indent=2))
        report.append("```")

    # ── Recommendations ──
    report.append("\n## Recommendations\n")
    report.append("*(Based on validation performance — configs that generalize beyond training data)*\n")

    # Find best per phase
    for phase_name, phase_results in phases.items():
        if not phase_results:
            continue
        best_phase = max(phase_results, key=lambda x: x['val']['score'])
        report.append(f"- **{phase_name}:** {best_phase['name']} "
                      f"(val_score={best_phase['val']['score']}, "
                      f"all_sharpe={best_phase['all']['sharpe']})")

    report_text = '\n'.join(report)
    REPORT_FILE.write_text(report_text)
    print(f"\nReport: {REPORT_FILE}")
    print(f"Results TSV: {RESULTS_FILE}")

    # Final notification
    baseline = next((r for r in results if r['name'].startswith('BASELINE')), None)
    bl_score = baseline['val']['score'] if baseline else 0
    notify(f"TSLA Scalp Optimizer DONE! {len(experiments)} experiments in {elapsed:.0f}min.\n"
           f"Best: {best_name} (val={best_val_score:.1f} vs baseline={bl_score:.1f}).\n"
           f"Report: tsla-scalp-optimization-report.md")

    # Print top 5
    print("\n" + "=" * 70)
    print("TOP 5 BY VALIDATION SCORE:")
    for i, r in enumerate(results_sorted[:5]):
        print(f"  {i+1}. {r['name']}: val_score={r['val']['score']}, "
              f"val_win={r['val']['win_pct']}%, val_avg=${r['val']['avg_pnl']}, "
              f"sharpe={r['all']['sharpe']}")


if __name__ == '__main__':
    main()
