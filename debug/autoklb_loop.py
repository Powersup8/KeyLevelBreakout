#!/usr/bin/env python3
"""
AutoKLB Autonomous Experiment Loop
====================================
Runs pre-defined signal-logic experiments in sequence.
Each experiment: patch signals.py → commit → eval → keep/discard → log.

Usage: python3 autoklb_loop.py
Logs:  ../debug/autoklb_results.tsv  (appended after every run)

Fixes vs v1:
  - run_eval() uses direct subprocess capture (no shell redirect bug)
  - Phase 1a: constant + gate applied as one combined experiment
  - EXPERIMENTS format: (desc, [(old1, new1), ...]) — multi-patch per step
"""

import subprocess
import sys
import time
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_DIR    = Path(__file__).parent.parent
DEBUG_DIR   = REPO_DIR / "debug"
SIGNALS     = DEBUG_DIR / "autoklb_signals.py"
RESULTS     = DEBUG_DIR / "autoklb_results.tsv"
LOG         = DEBUG_DIR / "autoklb_run.log"

BASELINE_VAL   = 1472.4   # updated: Phase 4e best (ADX=0, proximity=0.20)
BASELINE_TRAIN = 83.1
MAX_TRAIN_DROP = 0.20   # discard if train drops >20%


# ══════════════════════════════════════════════════════════════════════════════
# EXPERIMENT DEFINITIONS
# Each experiment: (description, [(old_str, new_str), ...])
# All patches must match for the experiment to run.
# ══════════════════════════════════════════════════════════════════════════════

EXPERIMENTS = [

    # ── Phase 5 (rerun): VOL sweet spot — standalone, not cascade ─────────────
    # Phase 5a (0.7) crashed train to -48.2 → discard. Start from 1.0 again.
    # Skip 0.7 (known bad). Test 0.5 directly — may have different train profile.

    (
        "Phase 5r-a: VOL_RATIO_MIN 1.0 → 0.5",
        [
            (
                'VOL_RATIO_MIN = 1.0           # v3.3: lowered from 1.5',
                'VOL_RATIO_MIN = 0.5           # loop: vol 0.5',
            ),
        ],
    ),

    (
        "Phase 5r-b: VOL_RATIO_MIN 0.5 → 0.3",
        [
            (
                'VOL_RATIO_MIN = 0.5           # loop: vol 0.5',
                'VOL_RATIO_MIN = 0.3           # loop: vol 0.3',
            ),
        ],
    ),

    (
        "Phase 5r-c: VOL_RATIO_MIN 0.3 → 0.1",
        [
            (
                'VOL_RATIO_MIN = 0.3           # loop: vol 0.3',
                'VOL_RATIO_MIN = 0.1           # loop: vol 0.1',
            ),
        ],
    ),

    # ── Phase 6: BODY_PCT_MIN incremental ─────────────────────────────────────
    # v3.7 showed 30→20→10→0 all KEPT incrementally.
    # Phase 4b (direct 30→0 jump) failed. Incremental may work at current baseline.

    (
        "Phase 6a: BODY_PCT_MIN 30.0 → 20.0",
        [
            (
                'BODY_PCT_MIN = 30.0',
                'BODY_PCT_MIN = 20.0  # loop: reduce body filter',
            ),
        ],
    ),

    (
        "Phase 6b: BODY_PCT_MIN 20.0 → 10.0",
        [
            (
                'BODY_PCT_MIN = 20.0  # loop: reduce body filter',
                'BODY_PCT_MIN = 10.0  # loop: reduce body filter',
            ),
        ],
    ),

    (
        "Phase 6c: BODY_PCT_MIN 10.0 → 0.0",
        [
            (
                'BODY_PCT_MIN = 10.0  # loop: reduce body filter',
                'BODY_PCT_MIN = 0.0   # loop: remove body filter',
            ),
        ],
    ),

    # ── Phase 7: Proximity wider ───────────────────────────────────────────────
    # Each 0.05 ATR step gained ~25-33%. Keep pushing beyond 0.20.

    (
        "Phase 7a: LEVEL_PROXIMITY_ATR 0.20 → 0.25",
        [
            (
                'LEVEL_PROXIMITY_ATR = 0.20     # loop: widen proximity further',
                'LEVEL_PROXIMITY_ATR = 0.25     # loop: widen proximity further',
            ),
        ],
    ),

    (
        "Phase 7b: LEVEL_PROXIMITY_ATR 0.25 → 0.30",
        [
            (
                'LEVEL_PROXIMITY_ATR = 0.25     # loop: widen proximity further',
                'LEVEL_PROXIMITY_ATR = 0.30     # loop: widen proximity further',
            ),
        ],
    ),

    # ── Phase 8: Freshness gate ────────────────────────────────────────────────
    # Allow more retests at same level before dimming.

    (
        "Phase 8a: FRESHNESS_MAX_TESTS 3 → 5",
        [
            (
                'FRESHNESS_MAX_TESTS = 3        # v3.3: 3rd+ test at same level → dim',
                'FRESHNESS_MAX_TESTS = 5        # loop: allow more retests',
            ),
        ],
    ),

]


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def run(cmd, cwd=None, timeout=600):
    return subprocess.run(
        cmd, shell=True, cwd=str(cwd or REPO_DIR),
        capture_output=True, text=True, timeout=timeout,
    )


def git_commit(msg):
    run('git add debug/autoklb_signals.py')
    r = run(f'git commit -m "autoklb: {msg}"')
    if r.returncode != 0:
        print(f"  [warn] commit failed: {r.stderr.strip()}")
        return None
    for line in r.stdout.splitlines():
        if line.startswith("["):
            return line.split()[1].rstrip("]")
    return "unknown"


def git_reset():
    run("git reset --hard HEAD~1")


def run_eval():
    """Run realdata eval, return scores dict or None on crash."""
    # Use direct capture (no shell redirect) to avoid Google Drive flush lag
    r = subprocess.run(
        [sys.executable, "autoklb_realdata.py"],
        capture_output=True, text=True,
        cwd=str(DEBUG_DIR), timeout=600,
    )
    log = r.stdout + r.stderr
    LOG.write_text(log)  # save for inspection

    scores = {}
    for line in log.splitlines():
        for key in ["rd_val_score", "rd_train_score", "rd_val_n", "rd_train_n"]:
            if line.startswith(f"{key}:"):
                try:
                    scores[key] = float(line.split(":")[1].strip())
                except ValueError:
                    pass
    if "rd_val_score" not in scores:
        print("  [error] no score in output — crash?")
        print(log[-2000:])
        return None
    return scores


def append_result(commit, desc, scores, status):
    val   = scores.get("rd_val_score", 0)
    train = scores.get("rd_train_score", 0)
    val_n  = int(scores.get("rd_val_n", 0))
    trn_n  = int(scores.get("rd_train_n", 0))
    line = f"{commit}\t—\t—\t—\t—\t{train:.1f}\t{val:.1f}\t{trn_n}\t{val_n}\t{status}\t{desc}\n"
    with open(RESULTS, "a") as f:
        f.write(line)
    print(f"  → logged: val={val:.1f}  train={train:.1f}  N={val_n}  [{status}]")


def apply_patches(patches):
    """Apply all patches to signals.py. Returns True if all matched."""
    text = SIGNALS.read_text()
    new_text = text
    for old_str, new_str in patches:
        if old_str not in new_text:
            return False
        new_text = new_text.replace(old_str, new_str, 1)
    SIGNALS.write_text(new_text)
    return True


def revert_patches(patches):
    """Undo all patches (new→old) in reverse order."""
    text = SIGNALS.read_text()
    for old_str, new_str in reversed(patches):
        text = text.replace(new_str, old_str, 1)
    SIGNALS.write_text(text)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN LOOP
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print(f"AutoKLB Loop — {len(EXPERIMENTS)} experiments queued")
    print(f"Baseline: rd_val={BASELINE_VAL}  rd_train={BASELINE_TRAIN}")
    print()

    best_val = BASELINE_VAL

    for i, (desc, patches) in enumerate(EXPERIMENTS):
        print(f"\n{'='*60}")
        print(f"Experiment {i+1}/{len(EXPERIMENTS)}: {desc}")

        # Apply all patches
        if not apply_patches(patches):
            print(f"  [skip] one or more patch strings not found")
            continue

        # Commit
        commit = git_commit(desc)
        if commit is None:
            revert_patches(patches)
            continue

        print(f"  commit: {commit}")
        print(f"  running eval (~5 min)...")
        t0 = time.time()

        # Evaluate
        scores = run_eval()
        elapsed = time.time() - t0
        print(f"  eval done in {elapsed:.0f}s")

        if scores is None:
            git_reset()
            append_result(commit, desc + " [CRASH]", {}, "discard")
            continue

        val   = scores["rd_val_score"]
        train = scores["rd_train_score"]

        # Keep/discard decision
        val_ok   = val >= best_val
        train_ok = train >= BASELINE_TRAIN * (1 - MAX_TRAIN_DROP)
        keep     = val_ok and train_ok

        if keep:
            best_val = val
            status = "keep"
            print(f"  KEEP ✓  val={val:.1f} (best={best_val:.1f})  train={train:.1f}")
        else:
            status = "discard"
            reason = []
            if not val_ok:   reason.append(f"val {val:.1f} < {best_val:.1f}")
            if not train_ok: reason.append(f"train {train:.1f} dropped >{MAX_TRAIN_DROP*100:.0f}%")
            print(f"  DISCARD ✗  {' | '.join(reason)}")
            git_reset()

        append_result(commit, desc, scores, status)

    print("\n\nLoop complete — all experiments done.")


if __name__ == "__main__":
    main()
