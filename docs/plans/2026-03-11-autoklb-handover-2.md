# AutoKLB Session Handover — 2026-03-11 (Evening)

## Current State

**Branch**: `autoklb/v38-realdata`
**Best score**: `rd_val=1472.4`, `rd_train=199.4` (Phase 4e)
**Baseline**: `rd_val=620.4`, `rd_train=83.1` (v3.8)

## Signals.py (clean, ready to run)

```
ADX_MIN = 0.0                    (Phase 4c kept)
LEVEL_PROXIMITY_ATR = 0.20       (Phase 4e kept)
BODY_PCT_MIN = 30.0              (baseline — NOT yet lowered)
VOL_RATIO_MIN = 1.0              (baseline — Phase 5a 0.7 was DISCARD)
DISABLED_SIGNALS += bear REV at PM High / ORB High / Week High
BRK_BULL_LEVELS += VWAP, Today Open, PD Close, PD High, Yest High
```

## What Happened This Session

Phase 5 (VOL cascade 1.0→0.7→0.5…) FAILED:
- Phase 5a (VOL=0.7): val=**1954.4** but train=**-48.2** → DISCARD (train crashed)
- Phases 5b-5e: all SKIP (cascade design — looked for 0.7 which was reset)

## Loop Ready to Run

9 experiments queued in `debug/autoklb_loop.py`:

| Phase | Description | Rationale |
|---|---|---|
| 5r-a | VOL 1.0 → 0.5 | Standalone restart; skip 0.7 (known bad) |
| 5r-b | VOL 0.5 → 0.3 | If 5r-a kept |
| 5r-c | VOL 0.3 → 0.1 | If 5r-b kept |
| 6a | BODY 30 → 20 | Incremental (v3.7: all 3 steps were KEPT) |
| 6b | BODY 20 → 10 | If 6a kept |
| 6c | BODY 10 → 0 | If 6b kept |
| 7a | Proximity 0.20 → 0.25 | Trend: each +0.05 gains ~25-33% |
| 7b | Proximity 0.25 → 0.30 | If 7a kept |
| 8a | FRESHNESS 3 → 5 | Allow more retests before dimming |

**Estimated time**: ~45-90 min (9 experiments × ~6 min each, minus skips)

## How to Run

```bash
cd debug && python3 autoklb_loop.py
```

Monitor: `tail -f autoklb_loop_run.log`
Results: `tail -5 autoklb_results.tsv`

## If Loop Finds New Bests

Run a final eval to see cumulative state:
```bash
cd debug && python3 autoklb_realdata.py
```

## If All 9 Experiments Fail/Skip

Next directions (not yet tried):
- **Val window expansion**: extend val to Feb 2026 (more data)
- **SL by signal type**: BRK SL=0.25 ATR, REV SL=0.10 ATR (needs harness change)
- **New signal variants**: more level types in REV_BULL_LEVELS

## Data Architecture (unchanged)

- Signal detection: native 5m bars, Jan 2024–Mar 2026 (2yr, 120 syms)
- Val MFE/MAE: 15sec bars (Sep 2025+)
- Train MFE/MAE: 1m bars (Feb 2025+), 5m fallback
- Split: Train ≤ Sep 30 2025 | Val Oct–Jan 2026 | Holdout Feb–Mar 2026
