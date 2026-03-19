#!/usr/bin/env python3
"""AutoKLB Supervisor — Batch AU: VOL_EXHAUSTION re-enable + COIL_VOL_RAMP + GATED circular removals.
Baseline: val=2104.3 (AT: Week Open bull=DISCARD, PD Mid removal=DISCARD, FRESHNESS→0=neutral).

Batch AT findings:
  AT1 DISCARD: Add Week Open → REV_BULL_LEVELS (Week Open bull direction = noise, only bear direction valuable)
  AT2 DISCARD: Remove PD Mid from REV_BEAR individually (PD Mid IS individually valuable — AG3 group DISCARD was collective)
  AT3/AT4 SKIP: Cascade of AT2 not reached (AT2 discarded)
  AT5 KEEP neutral: FRESHNESS_MAX_TESTS 3 → 0 (FRESHNESS gate now REDUNDANT at current composition!)

Key insight: FRESHNESS gate was compensating for direction routing noise. After cleaning REV_BEAR
direction (AR-AS removed 8 noisy direction entries), the pool of repeat-tests being dimmed collapsed
to near-zero. Gate became redundant: FRESHNESS=0 = FRESHNESS=3. Score stuck at 2104.3 for 4 batches.

New strategy: re-test VOL/COIL suppression constants (disabled at much lower baseline) + re-test
"circularly added" neutral GATED levels that may be removable at 2104.3 vs. their neutral add at 2089.
PD High in GATED was AE4 removal = +1.8 at 2085, then AK4 re-added neutral at 2089. At 2104.3, removal
might win again (same mechanism, new composition).

Batch AU experiments:
  AU1: VOL_EXHAUSTION_MAX 0.0 → 2.0 (re-enable at moderate value — disabled at ~1569 baseline for +41.5.
       At 2104.3 with BODY=60/prox=0.65, extreme-vol signals already filtered. Test if small re-enable
       dims remaining high-vol noise while preserving quality core.)
  AU2: QUIET_COIL_VOL_RAMP 0.0 → 0.5 (D7 disabled at early baseline. At 2104.3 composition, coil signals
       may benefit from light vol ramp requirement to separate weak coils from strong setups.)
  AU3: Remove Yest Low from BRK_BULL (AH3 re-added neutral at 2089 — AA3 originally removed neutral at 2073.
       At 2104.3 with tighter composition, test if Yest Low BRK_BULL is finally removable with gain.
       "Floor reclaim" pattern — memory confirms reclaim patterns = noise.)
  AU4: Remove PD High from REV_LEVELS_GATED (AK4 re-added neutral at 2089 — AE4 removal was +1.8 at 2085!
       Circular test: AK4 re-added with no gain, now remove at higher baseline. AE4 mechanism: PD High in
       GATED fires as bear-only EMA-gated REV, but PD High is an older level reference — may be noise.)
  AU5: Remove Yest High from REV_LEVELS_GATED (AJ2 re-added neutral at 2089 — Z1 removed neutral at 2073.
       Yest High in GATED = bear-only gated REV at prior-session high. Circular test at 2104.3.)
"""
import subprocess, sys, time
from pathlib import Path

DEBUG_DIR = Path(__file__).parent
REPO_DIR  = DEBUG_DIR.parent
SIGNALS   = DEBUG_DIR / "autoklb_signals.py"
RESULTS   = DEBUG_DIR / "autoklb_results.tsv"
LOG       = DEBUG_DIR / "autoklb_loop_run.log"
NOTIFY    = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/personal_assistant/scripts/notify.py")

BASELINE_VAL   = 2104.3
BASELINE_TRAIN = 83.1
MAX_TRAIN_DROP = 0.20
MAX_ROUNDS     = 6
MIN_IMPROVEMENT = 0.5

EXPERIMENTS = [

    # ── AU1: VOL_EXHAUSTION_MAX 0.0 → 2.0 ────────────────────────────────────
    # VOL_EXHAUSTION dims signals where volume ratio exceeds threshold.
    # Disabled at ~1569 baseline for +41.5 (removing dim = more signals pass full quality).
    # At 2104.3 with BODY=60/prox=0.65/BIG=0.15, signals are already tight. A large portion
    # of the filtered pool is now high-quality. But extreme-vol events (vol_ratio > 2.0)
    # may still represent "exhaustion" = chasing a move that's already extended.
    # Re-enabling at 2.0 (moderate dim) = only the most extreme-vol signals get dimmed.
    # Anchor: unique "loop Z1: dim-all extreme test" VOL_EXHAUSTION line.
    (
        "Phase AU1: VOL_EXHAUSTION_MAX 0.0 → 2.0 (re-enable moderate vol exhaustion — disabled at 1569, test at 2104.3 tight composition)",
        [('VOL_EXHAUSTION_MAX = 0.0       # loop Z1: dim-all extreme test',
          'VOL_EXHAUSTION_MAX = 2.0       # loop AU1: re-enable vol exhaustion at moderate value (0→2 — disabled at 1569 for +41.5; test at 2104.3 composition)')],
    ),

    # ── AU2: QUIET_COIL_VOL_RAMP 0.0 → 0.5 ───────────────────────────────────
    # QUIET_COIL_VOL_RAMP requires volume to be ramping for coil setups to fire.
    # D7 disabled it (0.0 = no vol ramp requirement for coils).
    # At tight composition, coil setups that fire without vol ramp = potentially weak.
    # Testing light re-enable at 0.5 (50% vol ramp vs. prev bar required for coils).
    # If coil signals are already few and high-quality at current composition, enabling
    # this might preserve quality while slightly reducing coil-noise count.
    # Anchor: unique "loop D7: disable quiet coil vol ramp" line.
    (
        "Phase AU2: QUIET_COIL_VOL_RAMP 0.0 → 0.5 (re-enable light coil vol ramp — D7 disabled at early baseline, test at 2104.3)",
        [('QUIET_COIL_VOL_RAMP = 0.0     # loop D7: disable quiet coil vol ramp',
          'QUIET_COIL_VOL_RAMP = 0.5     # loop AU2: re-enable light coil vol ramp (D7 disabled at early baseline — test quality improvement at 2104.3)')],
    ),

    # ── AU3: Remove Yest Low from BRK_BULL ────────────────────────────────────
    # Yest Low BRK_BULL = stock breaks above prior day's low from below (floor reclaim).
    # Memory: "BRK_BULL 'reclaim' patterns = noise" (AA3 neutral at 2073 = originally removed).
    # AH3 re-added at 2089 as neutral (inverse of AA3 — came back neutral).
    # At 2104.3 with tighter prox=0.65/BODY=60, the "floor reclaim" signal at Yest Low
    # fires only on very clean setups. Test if it's now removable with gain (noise confirmed).
    # Anchor: unique "loop AH3: re-add Yest Low to BRK_BULL" line.
    (
        "Phase AU3: Remove Yest Low from BRK_BULL (AH3 re-added neutral at 2089 — floor reclaim pattern, test removal at 2104.3)",
        [('    "Yest Low",                  # loop AH3: re-add Yest Low to BRK_BULL (AA3 inverse — prior-day floor reclaim at 2089)',
          '    # loop AU3: removed Yest Low from BRK_BULL (AH3 re-added neutral at 2089; AA3 originally removed neutral at 2073 — floor reclaim pattern)')],
    ),

    # ── AU4: Remove PD High from REV_LEVELS_GATED ─────────────────────────────
    # AE4 removed PD High from GATED at baseline 2083.4 → val 2085.2 (+1.8 win!).
    # AK4 re-added PD High to GATED at baseline 2089.2 → val 2089.2 (neutral, no harm).
    # The composition has significantly changed since AK4 (REV_BEAR cleaned, prox tightened,
    # BODY raised to 60, FRESHNESS now disabled). Test if removing PD High from GATED again
    # yields the same +1.8 improvement at 2104.3 or has become neutral/negative.
    # Mechanism: PD High in GATED fires as bear-only EMA-gated REV when stock near PD High.
    # At tight prox=0.65, only signals very close to PD High fire — may be quality or noise.
    # Anchor: unique "loop AK4: re-add PD High to REV_LEVELS_GATED" line.
    (
        "Phase AU4: Remove PD High from REV_LEVELS_GATED (AK4 re-added neutral; AE4 removal was +1.8 — test at 2104.3)",
        [('    "PD High",                   # loop AK4: re-add PD High to REV_LEVELS_GATED (AE4 inverse — bear-only gated REV at prior-day high)',
          '    # loop AU4: removed PD High from REV_LEVELS_GATED (AK4 re-added neutral at 2089; AE4 removal was +1.8 at 2085 — test at 2104.3)')],
    ),

    # ── AU5: Remove Yest High from REV_LEVELS_GATED ───────────────────────────
    # AJ2 re-added Yest High to GATED at baseline 2089.2 → neutral (Z1 inverse).
    # Z1 originally removed Yest High from GATED → neutral at 2073.6.
    # Circular test: now at 2104.3, Yest High in GATED = bear-only EMA-gated REV at
    # prior-session high. Yest High = an older session reference level, potentially
    # less reliable than intraday levels. With FRESHNESS disabled and prox at 0.65,
    # test if Yest High GATED is genuinely contributing or is lingering dead weight.
    # Anchor: unique "loop AJ2: re-add Yest High to REV_LEVELS_GATED" line.
    (
        "Phase AU5: Remove Yest High from REV_LEVELS_GATED (AJ2 re-added neutral at 2089 — test removal at 2104.3)",
        [('    "Yest High",                 # loop AJ2: re-add Yest High to REV_LEVELS_GATED (Z1 inverse — bear-only gated REV at prior session high)',
          '    # loop AU5: removed Yest High from REV_LEVELS_GATED (AJ2 re-added neutral at 2089; Z1 removed neutral at 2073 — circular test at 2104.3)')],
    ),

]


def run(cmd, cwd=None):
    return subprocess.run(cmd, shell=True, cwd=str(cwd or REPO_DIR), capture_output=True, text=True, timeout=600)

def notify(msg):
    if NOTIFY.exists():
        subprocess.run([sys.executable, str(NOTIFY), msg], capture_output=True, timeout=15)
    print(f"[notify] {msg}")

def git_commit(msg):
    run('git add debug/autoklb_signals.py')
    r = run(f'git commit -m "autoklb: {msg}"')
    if r.returncode != 0: return None
    for line in r.stdout.splitlines():
        if line.startswith("["): return line.split()[1].rstrip("]")
    return "unknown"

def git_reset():
    run("git reset --hard HEAD~1")

def run_eval():
    try:
        r = subprocess.run([sys.executable, "autoklb_realdata.py"],
                           capture_output=True, text=True, cwd=str(DEBUG_DIR), timeout=600)
    except subprocess.TimeoutExpired:
        return None
    log = r.stdout + r.stderr
    LOG.write_text(log)
    scores = {}
    for line in log.splitlines():
        for key in ["rd_val_score", "rd_train_score", "rd_val_n", "rd_train_n"]:
            if line.startswith(f"{key}:"):
                try: scores[key] = float(line.split(":")[1].strip())
                except ValueError: pass
    return scores if "rd_val_score" in scores else None

def append_result(commit, desc, scores, status):
    val, train = scores.get("rd_val_score", 0), scores.get("rd_train_score", 0)
    val_n, trn_n = int(scores.get("rd_val_n", 0)), int(scores.get("rd_train_n", 0))
    with open(RESULTS, "a") as f:
        f.write(f"{commit}\t—\t—\t—\t—\t{train:.1f}\t{val:.1f}\t{trn_n}\t{val_n}\t{status}\t{desc}\n")
    print(f"  → logged: val={val:.1f}  train={train:.1f}  N={val_n}  [{status}]")

def apply_patches(patches):
    text = SIGNALS.read_text()
    new_text = text
    for old, new in patches:
        if old not in new_text: return False
        new_text = new_text.replace(old, new, 1)
    SIGNALS.write_text(new_text)
    return True

def revert_patches(patches):
    text = SIGNALS.read_text()
    for old, new in reversed(patches):
        text = text.replace(new, old, 1)
    SIGNALS.write_text(text)

def run_round(round_num, best_val):
    kept, discarded, skipped = [], [], []
    for i, (desc, patches) in enumerate(EXPERIMENTS):
        print(f"\n{'='*60}")
        print(f"[Round {round_num}] Exp {i+1}/{len(EXPERIMENTS)}: {desc}")
        if not apply_patches(patches):
            print("  [skip] patch not found")
            skipped.append(desc)
            continue
        commit = git_commit(desc)
        if commit is None:
            revert_patches(patches)
            skipped.append(desc)
            continue
        print(f"  commit: {commit}  running eval...")
        t0 = time.time()
        scores = run_eval()
        print(f"  eval done in {time.time()-t0:.0f}s")
        if scores is None:
            git_reset()
            append_result(commit, desc + " [CRASH]", {}, "discard")
            discarded.append(f"[CRASH] {desc}")
            continue
        val, train = scores["rd_val_score"], scores["rd_train_score"]
        val_ok   = val >= best_val
        train_ok = train >= BASELINE_TRAIN * (1 - MAX_TRAIN_DROP)
        if val_ok and train_ok:
            best_val = val
            kept.append(f"{desc} → {val:.1f}")
            append_result(commit, desc, scores, "keep")
            print(f"  KEEP ✓  val={val:.1f}  train={train:.1f}")
        else:
            reason = []
            if not val_ok: reason.append(f"val {val:.1f}<{best_val:.1f}")
            if not train_ok: reason.append(f"train dropped")
            discarded.append(desc)
            git_reset()
            append_result(commit, desc, scores, "discard")
            print(f"  DISCARD ✗  {' | '.join(reason)}")
    return best_val, kept, discarded, skipped

def main():
    best_val = BASELINE_VAL
    total_kept = []
    notify(f"AutoKLB Batch AU starting: {len(EXPERIMENTS)} exps/round, up to {MAX_ROUNDS} rounds. Baseline={BASELINE_VAL}. AU1=VOL_EXHAUST→2, AU2=COIL_VOL_RAMP→0.5, AU3=rm Yest Low BRK_BULL, AU4=rm PD High GATED (was +1.8), AU5=rm Yest High GATED.")
    for round_num in range(1, MAX_ROUNDS + 1):
        round_start = best_val
        print(f"\n\n{'#'*60}\nROUND {round_num}/{MAX_ROUNDS} — baseline={best_val:.1f}\n{'#'*60}")
        best_val, kept, discarded, skipped = run_round(round_num, best_val)
        improvement = best_val - round_start
        total_kept.extend(kept)
        kept_str = "; ".join(kept[:2]) + (f" +{len(kept)-2} more" if len(kept) > 2 else "") if kept else "none"
        print(f"\nRound {round_num} done. +{improvement:.1f}  Kept:{len(kept)}  Discarded:{len(discarded)}")
        if improvement < MIN_IMPROVEMENT:
            notify(f"AutoKLB Batch AU converged after round {round_num}. Final={best_val:.1f} (+{best_val-BASELINE_VAL:.1f}). Kept:{len(total_kept)}. Continuing autonomously...")
            break
        notify(f"AutoKLB Batch AU round {round_num} done! Best={best_val:.1f} (+{improvement:.1f}). Kept: {kept_str}. Starting round {round_num+1}...")
        time.sleep(5)
    else:
        notify(f"AutoKLB Batch AU: {MAX_ROUNDS} rounds done. Final={best_val:.1f} (+{best_val-BASELINE_VAL:.1f}). Kept:{len(total_kept)}. Continuing autonomously...")

if __name__ == "__main__":
    main()
