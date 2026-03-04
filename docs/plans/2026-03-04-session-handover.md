# Session Handover — 2026-03-04 (Mac 2 → Mac 1)

> **For Claude:** Read this first, then `docs/plans/2026-03-04-v28a-audit-action-items.md`, then `MEMORY.md`.

**On the other Mac, run:** `git fetch && git reset --hard origin/main`

**Commit:** `2feb775` (pushed to GitHub)
**Current version:** v2.8b

---

## What Was Done This Session

### 1. v2.8b Implemented: ⚡ size.large Removal
- Removed `isBigMove` from `size.large` conditions in 4 places (lines 925, 962, 1024, 1172)
- ⚡ glyph stays as informational marker, multi-level confluence still gets `size.large`
- Docs updated: KLB_Reference.md, KLB_TV.md, KLB_DESIGN-JOURNAL.md

### 2. All 6 Audit Items Investigated

| # | Item | Key Finding |
|---|------|-------------|
| 1 | MC time gate | 9:50 gate confirmed. 14 smart filters tested — none beat negative expectancy pre-9:50. Counter-VWAP = quality boost after 9:50 (+0.118 ATR, 10x better) |
| 2 | ⚡ size.large | ✅ Implemented. -48% MFE = exhaustion entry |
| 3 | Volume filter | ⚡ contamination (84-98% of high-vol). Non-⚡ sweet spot: **2-3x** (MFE 1.252, 54% win) |
| 4 | ✓★ criteria | Both broken (≥5x vol = worst bucket, ≥80% pos = Dead End). New: **BRK+vol<5x+morning** → +23.10 ATR, 42% win, -1.95 DD, 11.9x recovery |
| 5 | TSLA dominance | Real but concentrated (Nov=51% of TSLA P&L). Without TSLA: barely profitable (+5.39 ATR, PF 1.08). Edge may be fading. |
| 6 | VWAP counter-trend | Golden signal: 83% win, p<0.0002, MFE/MAE 5.17x |

### 3. Infrastructure
- Fixed Git lock file from Google Drive sync (memorized procedure)
- Added versioning rule to MEMORY.md (every change bumps version, minor = letter suffix)
- Added doc update rule (every code change must update affected docs)
- Added workflow rule (always read all knowledge before starting work)
- Switched from claude-mem to file-based memory only (syncs via Google Drive)
- Updated project bash allowlist in `.claude/settings.local.json`

---

## What's Next: Implementation Batch → v2.9

All items are investigated, documented, and ready. Do them all at once.

| # | Change | Where | What |
|---|--------|-------|------|
| 1 | MC 9:50 time gate | Lines ~770-773 | Add time check to `rMC_bull`/`rMC_bear` |
| 3 | Runner Score vol factor | Line ~480 | `vol >= 5.0` → `vol >= 2.0 and vol < 5.0` |
| 4a | ✓★ BRK criteria | Lines 1081, 1229 | `vol >= 5.0 and closePos >= 80` → `vol < 5.0 and hour ≤ 10` |
| 4b | ✓★ QBS/MC | Line 1321 | `highConv = false` (always plain ✓) |
| 6 | VWAP counter-trend | TBD | Special label/alert for the golden signal |
| — | Counter-VWAP MC boost | Near MC labels | Optional confidence marker post-9:50 |
| — | Update all docs | KLB_Reference, KLB_TV, KLB_DESIGN-JOURNAL, KLB_PLAYBOOK | |
| — | Version bump | Line 2 | v2.8b → v2.9 |

---

## Analysis Reports (read before implementing)

| File | What |
|------|------|
| `debug/v28b-volume-investigation.md` | Volume + ✓★ deep dive with P&L validation |
| `debug/v28b-mc-smart-filter.md` | MC 14-dimension filter research |
| `debug/v28b-tsla-dominance.md` | TSLA concentration risk analysis |
| `debug/v28a-vwap-counter-analysis.md` | VWAP counter-trend validation |
| `docs/plans/2026-03-04-v28a-audit-action-items.md` | Master tracking doc (full details) |
