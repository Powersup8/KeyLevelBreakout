# v2.8b Audit — Action Items & Handover

> **For Claude:** This is a handover doc. Read this first, then `MEMORY.md`, then the referenced analysis files before working. **RULE: Always read all available knowledge before starting any work.**

**Current version:** v2.8b (`KeyLevelBreakout.pine`)
**Last commit:** `d547ad0` (pushed to GitHub) — v2.8b has ⚡ size.large removal only, not yet committed
**Uncommitted changes:** `KeyLevelBreakout.pine` (⚡ fix), this doc, `debug/v28b-*.md` reports

---

## ALL ITEMS INVESTIGATED — Ready for Implementation Batch

### 1. MC Time Gate + Counter-VWAP Boost — ✅ INVESTIGATED

**Problem:** MC fires both bull AND bear at open on 126/167 days. 45% coin flip.

**Smart filter research (14 dimensions tested):**
- Best filter: counter-VWAP (MC opposing VWAP = 61.5% correct) — the "obvious" with-VWAP MC is a trap
- Best composite: counter-VWAP + multi-score fallback = 64.3%
- **BUT: Even with 64.3% accuracy, pre-9:50 trades have negative expectancy** — opening auction whipsaws kill stops regardless of direction

**Decision: Simple 9:50 gate + counter-VWAP quality boost after 9:50**
- Lines 770-773: add `hour(sigTime) >= 10 or (hour(sigTime) == 9 and minute(sigTime) >= 50)` to `rMC_bull`/`rMC_bear`
- After 9:50, counter-VWAP MC trades have +0.118 ATR expectancy (10x better than aligned)
- Consider counter-VWAP as confidence marker on post-9:50 MC labels

**Full analysis:** `debug/v28b-mc-smart-filter.md`, `debug/v28a-mc-analysis.md`

### 2. ⚡ Big-Move size.large Removal — ✅ DONE (v2.8b)

**Implemented:** Removed `isBigMove` from `size.large` in 4 places (lines 925, 962, 1024, 1172). ⚡ glyph stays as informational marker. Multi-level confluence still gets `size.large`.

**Full analysis:** `debug/v28a-bigmove-analysis.md`

### 3. Runner Score Vol Factor — ✅ INVESTIGATED

**Finding:** ⚡ contamination explains "inverted volume." 84% of 5-10x and 98% of 10x+ are ⚡.
Non-⚡ sweet spot: **2-3x volume** (MFE 1.252, 54% win, MFE/MAE 1.42).

**Change:** Line ~480, Runner Score vol factor: `vol >= 5.0` → `vol >= 2.0 and vol < 5.0`

**Full analysis:** `debug/v28b-volume-investigation.md`

### 4. ✓★ Gold Criteria Rework — ✅ INVESTIGATED

**Root cause:** Both criteria broken:
- `≥5x vol` = worst MFE bucket (0.859 vs 1.178 for <5x)
- `≥80% close pos` = Dead End (overfitting, didn't replicate, cuts 70% of signals)
- QBS/MC ✓★ is net negative (-1.47 ATR)

**New ✓★ definition: BRK source + vol < 5x + hour ≤ 10**

| Metric | Old ✓★ | New ✓★ |
|--------|--------|--------|
| Total P&L | +2.74 ATR | **+23.10 ATR** |
| Avg/trade | 0.007 | **0.097** |
| Win% | 32% | **42%** |
| Max Drawdown | — | **-1.95 ATR** |
| Recovery Ratio | — | **11.9x** |
| TSLA dependency | — | **35%** |
| Profitable symbols | — | **8/10** |

**Implementation:**
- Lines 1081, 1229 (BRK CONF): change `highConv` from `vol >= 5.0 and closePos >= 80` to `vol < 5.0 and (hour(time) == 9 or hour(time) == 10)`
- Line 1321 (QBS/MC CONF): remove ✓★ entirely — always plain ✓ (`highConv = false`)

**Full analysis:** `debug/v28b-volume-investigation.md`

### 5. TSLA Dominance — ✅ INVESTIGATED

**Findings:**
- NOT purely downtrend artifact — bull trades made +8.45 ATR (42% of TSLA trades)
- Severe concentration: Nov 2025 alone = 51% of TSLA P&L, two months = 89%
- TSLA has genuinely better signal quality: MFE/MAE 1.23 (best), win rate 43.9% (best)
- Without TSLA: barely profitable (+5.39 ATR, PF 1.08, -14.09 max DD)
- Recent fade: Feb -0.12, Mar -0.60

**No code change needed.** Awareness item for trading:
- Don't size up on TSLA just because of past performance
- Monitor monthly — edge may already be eroding
- AAPL, AMZN, SPY, QQQ are net losers — consider filtering or reduced sizing

**Full analysis:** `debug/v28b-tsla-dominance.md`

### 6. VWAP Counter-Trend Special Treatment — ✅ VALIDATED

**The golden signal:** 83.3% win, MFE/MAE 5.17x, p=0.000019.
Bear counter at Yest Low = 92% win. Vol <2x best. 10:xx hour best.

**Implementation needed:** Special label/alert treatment (TBD in implementation session).

**Full analysis:** `debug/v28a-vwap-counter-analysis.md`

---

## Implementation Batch (do all at once, bump to v2.9)

| # | Change | Where | Complexity |
|---|--------|-------|------------|
| 1 | MC 9:50 time gate | Lines ~770-773 (`rMC_bull`/`rMC_bear`) | Simple |
| 3 | Runner Score vol: `≥5x` → `≥2x and <5x` | Line ~480 | Simple |
| 4a | ✓★ BRK: `vol≥5+pos≥80` → `vol<5+hour≤10` | Lines 1081, 1229 | Simple |
| 4b | ✓★ QBS/MC: always plain ✓ | Line 1321 | Simple |
| 6 | VWAP counter-trend label/alert | TBD | Medium |
| — | Counter-VWAP boost on MC labels (optional) | Near MC label creation | Medium |

**After implementation:** Update KLB_Reference.md, KLB_TV.md, KLB_DESIGN-JOURNAL.md, KLB_PLAYBOOK.md. Bump version to v2.9.

---

## CONFIRMED WORKING (no action needed)

- **#7: 5m checkpoint** — HOLD +0.120 ATR, BAIL -0.058 ATR
- **#8: Body ⚠** — 0.716 MFE vs 0.907 without. Fakeout detection confirmed.
- **#9: BRK CONF rate** — 35% overall

---

## DEFERRED

### Label Overlap at Open
- Unreadable label pile at 9:30-9:35 when 3-5 signals fire on same bar
- Observed on NVDA, TSLA (Mar 4 verification)

### Grinding Trend Detection
- Fundamentally different signal type, not a fix
- Analysis: `debug/2026-03-03-missed-moves.md`

---

## File Map

| File | Contents |
|------|----------|
| `debug/v28_signal_audit.py` | Main audit script |
| `debug/v28a-signal-audit.md` | Full audit report (8 sections) |
| `debug/v28a-mc-analysis.md` | MC opposing pairs deep dive |
| `debug/v28a-bigmove-analysis.md` | ⚡ big-move flag analysis |
| `debug/v28a-vwap-counter-analysis.md` | VWAP counter-trend deep dive |
| `debug/v28b-volume-investigation.md` | Volume + ✓★ investigation (v2.8b session) |
| `debug/v28b-mc-smart-filter.md` | MC smart filter research (14 dimensions) |
| `debug/v28b-tsla-dominance.md` | TSLA concentration analysis |
| `debug/v28b_tsla_dominance.py` | TSLA analysis script |
| `debug/v28a-signals.csv` | 7,044 parsed signals |
| `debug/v28a-follow-through.csv` | 17,244 MFE/MAE measurements |
| `debug/v28a-trades.csv` | 870 simulated trades |
| `debug/v28a-mc-opposing-pairs.csv` | 126 MC opposing pairs |
