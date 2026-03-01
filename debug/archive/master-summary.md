# KeyLevelBreakout v2.3 — Master Analysis Summary

**Date:** Feb 28, 2026
**Data:** 13 symbols, Jan 20 - Feb 27 (~6 weeks), 3,753 signals, 525 with candle follow-through
**Version:** v2.3 (post all 4 fixes)

---

## 1. v2.2 → v2.3 Fix Verification: ALL FIXES WORKING

| Fix | What Changed | Impact | Status |
|-----|-------------|--------|--------|
| **Diamond count** | sigBarIdx → bar_index | 55 retests relabeled from ◆⁰ to correct 1m count | ✅ Display fix, no signal change |
| **Reclaim CONF gate** | ~~ only after CONF ✗ | 11 reclaims eliminated (6→reversals, 5 removed) | ✅ Working as designed |
| **VWAP filter ON** | Default false→true | 25 counter-trend reversals suppressed | ✅ No breakouts affected |
| **CONF race fix** | elapsed > 0 guard | 2 race conditions eliminated | ✅ Bug fix, zero risk |

**Overall impact:** 390 → 366 signals (-6.2%), GOOD rate ~28% → ~30-32%, BAD rate ~33% → ~26-28%.
Breakout count unchanged at 109 (Feb 25-27 window). All reductions targeted weak signals only.

---

## 2. Follow-Through Analysis (525 signals with candle data)

### Best Signal Filters (Soft Classification: MFE>0.2 ATR, MFE>1.5x MAE = GOOD)

| Filter | GOOD% | BAD% | n | Key Insight |
|--------|-------|------|---|-------------|
| **BRK + CONF Pass + >5x vol** | **54.1%** | **0.0%** | 37 | Gold standard setup |
| CONF Pass (any signal) | 53.3% | 0.0% | 75 | CONF Pass = 0% BAD |
| CONF Pass + extreme pos (≥80) | 47.8% | 0.0% | 46 | Position filter adds safety |
| Week L level | 33.3% | 3.3% | 30 | Rare but powerful |
| Reversals (~) overall | 33.5% | 13.2% | 167 | High reward but high risk |
| >5x volume (any) | 33.2% | 13.5% | 229 | Volume = conviction |
| 9:30-10:00 window | 31.3% | 13.8% | 319 | Most energy, both directions |
| BRK + Yest/Week levels | 29.2% | 7.3% | 96 | Higher timeframe = stronger |
| **Reclaims (~~)** | **8.1%** | **8.1%** | 62 | Weakest signal type |
| 11:00-16:00 window | 6.9% | 0.0% | 116 | Dead zone — low energy |

### Signal Quality Hierarchy
1. **CONF Pass signals** — Trade with confidence (53% win, 0% loss)
2. **High-vol morning BRKs** — Good odds but manage risk (31% win, 14% loss)
3. **Reversals at Yest/Week levels** — Selective, worth the risk
4. **Afternoon signals** — Skip entirely unless extraordinary setup
5. **Reclaims** — Only trade if CONF ✗ preceded it (which v2.3 now enforces)

---

## 3. Pattern Mining (3,605 records, 6 weeks)

### Critical Architecture Finding
**ALL CONF passes are auto-promotes (100%).** Zero "slow confirmation" exists. If price doesn't immediately follow through, the signal ALWAYS fails. Implications:
- Auto-promote IS the entire CONF system
- 40% overall CONF rate = "instant momentum continuation rate"
- High volume → more auto-promotes → higher CONF rate

### CONF Success Rate by Factor

| Factor | Pass Rate | Notes |
|--------|-----------|-------|
| Volume ≥10x | **59.6%** | Strongest single predictor |
| Volume 2-4x | 37.7% | Baseline |
| Volume <2x | 32.2% | Weakest |
| Morning (9:30-10:00) | **48.3%** | High volume window |
| Lunch (11:30-13:30) | 25.0% | Dead zone |
| Afternoon (13:30-16:00) | 30.3% | Modest |
| Multi-level confluence | 43.9% | +4.7pp over single-level |
| Single level | 39.2% | Baseline |
| Yest H | 44.0% | Best individual level |
| PM L | 42.9% | Second best |
| Week L | **17.2%** | Worst CONF rate — but best follow-through! |

### Post-CONF-Fail Patterns
After BRK → CONF ✗, the next signal is:
- BRK (new breakout attempt): 52.1%
- **RCL (reclaim)**: 40.5% — highly repeatable pattern
- REV or second CONF fail: 7.4%

### Day-Type Classification (28 days analyzed)
- **Trend days (>70% CONF):** 0 days (0%) — No pure trend days in sample!
- **Chop days (<30% CONF):** 5 days (18%)
- **Mixed (30-70% CONF):** 23 days (82%)

**Early warning:** If first 2-3 CONFs all fail, chop day probability increases significantly. Chop day early CONF rate: 27.6% vs Mixed: 51.1%.

### Same-Bar Multi-Signals
- 242 bars have BRK + REV or BRK + RCL simultaneously (15% of signal bars)
- BRK + REV on same bar: 205 times (85%) — this is the "breakout one level + reverse another" pattern
- 60% of reversals fire on same bar as a breakout (median timing: 0 min)

---

## 4. Trading Rule Validation (6-week evidence)

| Rule | Verdict | Evidence |
|------|---------|----------|
| **1. Vol >2x BRK, >3x REV** | ✅ CONFIRMED | 42.4% CONF for ≥2x vs 32.2% for <2x |
| **2. First BRK strongest** | ✅ CONFIRMED | Retests show declining volume (408/885 below 0.5x vol ratio) |
| **3. Confluence stronger** | ✅ CONFIRMED | 43.9% vs 39.2% CONF (+4.7pp), multi-level vol 7.8x vs single 5.4x |
| **4. CONF ✗ → reversals** | ✅ CONFIRMED | 39.8% of post-fail signals are REV/RCL |
| **5. Avoid chop days** | ✅ CONFIRMED | 5/28 chop days identifiable by early CONF failures |
| **6. Early signals less reliable** | ❌ REFUTED | 48.3% CONF vs 29.7% rest — BETTER, not worse (driven by volume) |
| **7. Week H/L strongest** | ⚠️ NUANCED | Worst CONF rate (35.4%) but best follow-through (33.3% GOOD). Trade less, win more. |
| **8. Counter-trend needs VWAP** | ❓ UNVALIDATABLE | VWAP not in log data. Consider adding `vwap=above/below` to logs. |

### Updated Rules (Revised)
1. Volume >2x for BRK, >3x for REV — **keep**
2. First BRK of level is strongest — **keep**
3. Multi-level confluence is a quality boost — **keep, but effect is modest (+4.7pp)**
4. After CONF ✗, watch for reclaim (40% probability) — **keep, enhanced**
5. Avoid chop days — watch early CONF failures as predictor — **keep, enhanced**
6. ~~Early signals less reliable~~ → **REVISED: Morning signals (9:30-10:00) are MOST reliable for CONF but carry higher MAE risk. Focus trading energy here.**
7. ~~Week H/L strongest~~ → **REVISED: Yest H (44.0%) and PM L (42.9%) have best CONF rates. Week L has best follow-through but lowest CONF rate. Week levels = selective, high-conviction plays only.**
8. Counter-trend needs VWAP — **keep, but add VWAP position to log output for validation**

---

## 5. Symbol Performance

### Best CONF Rates
| Symbol | CONF% | Notes |
|--------|-------|-------|
| SPY | 51.0% | Best overall, most follow-through |
| QQQ | 49.0% | Second best |
| TSLA | 46.2% | Most trend days (6/24) |
| NVDA | 43.9% | Strong individual stock |

### Weakest CONF Rates
| Symbol | CONF% | Notes |
|--------|-------|-------|
| GLD | 30.2% | Commodity ETF — more chop |
| AMD | 31.2% | Most chop days (10/24) |
| SLV | 36.8% | Commodity ETF |

### ETF vs Stocks: Essentially equal
- ETFs (SPY, QQQ, GLD, SLV): 39.8% CONF
- Individual stocks: 40.1% CONF

---

## 6. Recommendations for v2.4

### High Priority (evidence-based, low risk)
1. **Add VWAP position to log output** — Cannot validate Rule 8 without it. Add `vwap=above/below` to signal log messages.
2. **Dim/label signals after 11:00** — Follow-through drops to near-zero. Visual dimming already exists; consider making the lull cutoff more visible.
3. **Day-type early warning** — After 2-3 consecutive CONF ✗, show a "CHOP" label on chart. Simple counter reset at session open.

### Medium Priority (evidence-based, moderate risk)
4. **High-conviction tier** — Highlight signals with CONF Pass + >5x volume + extreme position. These have 54.1% GOOD with 0% BAD.
5. **Reclaim quality tracking** — Reclaims are still the weakest signal (8.1% GOOD). Consider adding a hold-time requirement: only show ~~ if price stays on the reclaim side for N signal bars.

### Monitor / Low Priority
6. **Volume threshold experiment** — Current 2x minimum is well-calibrated. A 5x "high-conviction" threshold gives +14.5pp lift but would miss many valid signals.
7. **Position quality filter** — pos≥80 gives +9.9pp lift in CONF rate. Could add as optional filter but may be over-fitting.

### NOT Recommended (over-optimization risk)
- ❌ Raising volume minimum above 2x — would lose too many valid signals
- ❌ Suppressing afternoon signals entirely — rare but some run well (15:00 CONF rate = 42.9%)
- ❌ Symbol-specific tuning — the spread is too narrow (30-51%) to justify per-symbol rules
- ❌ Changing CONF timeout — current auto-promote mechanism works perfectly (100% of passes)

---

## 7. Over-Optimization Tracking

### Benchmarks for Future Comparison

| Metric | v2.2 (3 days) | v2.3 (3 days) | v2.3 (6 weeks) |
|--------|---------------|---------------|-----------------|
| Total signals (per day per symbol) | ~6.5 | ~6.1 | **5.8** |
| Breakout count | 109 | 109 | 1064 (5.1/day) |
| Reversal count | 90 | 73 | 545 (2.6/day) |
| Reclaim count | 29 | 19 | 232 (1.1/day) |
| Overall CONF rate | ~28% | ~30-32% | **40.0%** |
| CONF Pass + >5x: GOOD% | N/A | N/A | **54.1%** |
| CONF Fail: GOOD% | N/A | N/A | **12.1%** |
| Reclaim GOOD% | 13% | N/A | **8.1%** |

**Warning signs of over-optimization to watch for:**
- If CONF rate drops below 35% over a 2-week sample → fixes may have been too aggressive
- If signal count drops below 4/day/symbol on average → too much suppression
- If reclaim count drops to near zero → CONF gate may be too strict
- If reversal count drops significantly → VWAP filter may be too aggressive on mixed days

### What Was Fixed and Why (for future verification)
1. **Diamond count (display)**: Showed wrong bar count. Fixed to show correct 1m distance. ZERO impact on signals.
2. **Reclaim CONF gate (label)**: Changed ~~ to ~ when no CONF ✗ preceded it. 11 labels changed. 5 signals also suppressed by VWAP filter.
3. **VWAP filter (suppression)**: 25 counter-trend reversals suppressed. These scored ~10% GOOD in testing.
4. **CONF race (bug fix)**: 2 premature CONF ✗ eliminated. Pure logic bug — should never fire on setup bar.

---

## 8. Files Generated in This Analysis

| File | Contents |
|------|----------|
| `debug/data-inventory.md` | Complete file mapping (52 candle CSVs, 51 pine logs, 13 symbols) |
| `debug/2026-02-28-signal-analysis.md` | Feb 27 v2.3 signal analysis, all 4 fixes verified |
| `debug/v22-vs-v23-comparison.md` | v2.2↔v2.3 diff: 12 symbols, per-fix impact quantified |
| `debug/follow-through-analysis.md` | 525 signals with MFE/MAE at 5m/15m/30m/60m windows |
| `debug/pattern-mining-analysis.md` | 3,605 records: CONF rates, day types, sequences, rule validation |
| `debug/master-summary.md` | This file — consolidated findings |
