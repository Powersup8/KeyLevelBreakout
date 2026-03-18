# AutoKLB Session Handover — 2026-03-11

## Current State

**Branch**: `autoklb/v38-realdata`
**Best score**: `rd_val=1472.4`, `rd_train=199.4`, `rd_val_n=9,356` (Phase 4e)
**Baseline**: `rd_val=620.4`, `rd_train=83.1`, `rd_val_n=3,068` (v3.8)

## Loop Status

Loop is **running in background on the other Mac** (PID 55995, started 2:14).
Output: `debug/autoklb_loop_run.log` | Results: `debug/autoklb_results.tsv`

It will re-run some Phase 1-2 experiments (mostly neutral/skip, ~30 min wasted),
then reach **Phase 5 (VOL sweet-spot scan)** which is the real target.

After this Mac's loop finishes, **pull via Google Drive + git and check results**.

## Key Findings (This Session)

### What WORKED
| Change | Val Score | Train | Effect |
|---|---|---|---|
| ADX_MIN 20 → 0 | 882 | 97.8 | **+42%** — ADX gate was blocking good signals |
| LEVEL_PROXIMITY_ATR 0.10 → 0.15 | 1175 | 139 | **+33%** — wider proximity = more signals |
| LEVEL_PROXIMITY_ATR 0.15 → 0.20 | **1472** | 199 | **+25%** — keep pushing |

### What DIDN'T work
| Change | Val Score | Why |
|---|---|---|
| Midday suppress (11-14 ET) | 505 (-19%) | Midday signals are GOOD in v3.8 |
| BODY_PCT_MIN → 0 | 547 (-63%) | Body filter is protecting train quality |
| VOL_RATIO_MIN → 0 | 1219 (val +97%) | But train = -140 (crash). Needs sweet spot |
| Afternoon suppress | 1472 (neutral) | No effect |
| REV routing (Phase 2) | 1472 (neutral) | Bear REV already filtered by EMA/VWAP gates |
| BRK level expansion | 1472 (neutral) | VWAP not in levels DB; other levels already routing |

### Current signals.py state (after all kept changes)
- `ADX_MIN = 0.0`
- `LEVEL_PROXIMITY_ATR = 0.20`
- `DISABLED_SIGNALS` += bear REV at PM High, ORB High, Week High
- `BRK_BULL_LEVELS` += VWAP, Today Open, PD Close, PD High, Yest High
- Everything else at v3.8 baseline

## Phase 5 (Running Now)

**Goal**: VOL_RATIO_MIN sweet spot. Phase 4a showed:
- VOL=0.0 → val=1219 (great!) but train=-140 (crash) → DISCARD
- Push from 1.0 down in steps: **0.7 → 0.5 → 0.3 → 0.2 → 0.1**
- Loop stops when train drops below 66.5 (83.1 × 0.80)

BASELINE_VAL updated to 1472.4 so Phase 5 must beat the current best.

## What To Do On Other Mac

1. **Check if loop finished**: `tail -20 debug/autoklb_results.tsv`
2. **See current best**: look for highest `rd_val_score` in TSV
3. **Check git**: `git log --oneline -10`
4. **If loop still running**: let it run — it auto-commits results
5. **If loop finished**: check Phase 5 results, then think about next experiments

### If Phase 5 found a VOL sweet spot:
Run a final catalog eval to see cumulative impact:
```bash
cd debug && python3 autoklb_prepare.py
```

### If Phase 5 all discarded (VOL can't help at 1472.4 baseline):
The v3.8 system may be near optimal for current signal logic. Next directions:
- **SL by signal type**: BRK SL=0.25 ATR, REV SL=0.10 ATR (needs harness change)
- **Val window expansion**: extend val to Feb 2026 to include more data
- **New signal types**: VRC, SPY reclaim DIM are already in v3.7 — integrate into v3.8 harness

## Data Architecture (v3.8)
- **Signal detection**: native 5m bars, Jan 2024–Mar 2026 (2yr, 120 syms)
- **Val MFE/MAE**: 15sec bars (Sep 2025+, 240 bars = 60min)
- **Train MFE/MAE**: 1m bars (Feb 2025+, 60 bars), 5m fallback (pre-Feb 2025)
- **Split**: Train ≤ Sep 30 2025 | Val Oct–Jan 2026 | Holdout Feb–Mar 2026
- **Catalog enriched**: 100% mfe_1m coverage + mfe_15sec for val period + VIX daily

## Cache Status
- VIX collecting: `vix_1_day_ib.parquet`, `vix_5_mins_ib.parquet`, `vix_1_hour_ib.parquet`
- Bar sizes: 1s (28 syms, Feb+), 5s (119 syms, Sep+), 15s/30s (44 syms, Sep+), 1m/5m (120 syms, Jan 2024+)
- DST note: US EDT since Mar 8 (UTC-4). Europe CEST starts Mar 29. Code handles automatically via `tz_convert("US/Eastern")`. Verified correct on Mar 10 bars.

## Files Changed This Session
- `debug/autoklb_loop.py` — v2 (score detection fix, Phase 1a combined, Phase 5 added)
- `debug/autoklb_prepare.py` — uses mfe_15sec for val period scoring
- `debug/autoklb_realdata.py` — v3.8 (native 5m, tiered MFE, 2yr range)
- `debug/enrich_catalog.py` — fills mfe_1m gaps + adds mfe_15sec column
- `debug/enrich_vix.py` — adds vix_close + vix_regime to catalog (IB cache + yfinance)
- `debug/move-catalog.parquet` — enriched (mfe_1m 100%, mfe_15sec, vix_close, vix_regime)
