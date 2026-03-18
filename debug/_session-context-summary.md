# Session Context Summary (v2.8a-v2.8b Analysis)
**Date:** 2026-03-04

---

## 1. v28a-mc-analysis.md
**Problem:** MC signals fire both bull AND bear at open (126 opposing pairs), each side correct 45-55% (coin flip).
**Key Finding:** Direction at 9:50 ET matches 30-min outcome 79% of the time. Opening (9:30-9:45) is noise.
**Recommendation:** Suppress MC before 9:50 ET. Preserves once-per-session slot for real move (79% accuracy after 9:50).
**Data:** 126 opposing pairs (Sep 2025–Mar 2026), first signal correct 45%, second 55%.

---

## 2. v28a-bigmove-analysis.md
**Problem:** ⚡ flag (range ≥2x ATR) yields 0.598 MFE vs normal 1.152 — entry at exhaustion.
**Key Finding:** MFE drops monotonically: <1.5x ATR (MFE 1.33) → 5.0+ ATR (MFE 0.43). Bigger bar = worse follow-through.
**Recommendation:** Remove `size.large` from ⚡. Keep glyph as info. Optional: dim ⚡ signals. Range 5.0+ is "hold" not "entry."
**Consistency:** Pattern confirmed across all symbols. TSLA gap worst (-53%), AMD (-65%).

---

## 3. v28b-volume-investigation.md
**Problem:** BRK volume inverted — higher vol = worse MFE. ✓★ underperforms ✓ because ≥5x vol is worst bucket.
**Root Cause:** ⚡ contamination (84-98% of high-vol buckets). Non-⚡ sweet spot: 2-3x (MFE 1.252, 54% win).
**Fix #1:** Runner Score vol factor: ≥5x → 2-3x (or simply 2.0).
**Fix #2:** Redefine ✓★: `BRK AND vol<5.0 AND hour≤10` (not ≥5x vol). New ✓★ backtests +23.10 ATR (+8.4x), 42% win.
**QBS/MC Issue:** ✓★ for QBS/MC is net negative (-1.47 ATR) — remove, keep only ✓.

---

## 4. v28b-mc-smart-filter.md
**Problem:** Can smart filters beat 9:50 gate for opening MC pairs (126 opposing)?
**Options Tested:**
- Counter-VWAP only: 61.5% accuracy (52 pairs)
- Composite (VWAP + score): 64.3% accuracy (n=126)
- **9:50 gate: 79% accuracy, trivial complexity** ← BEST
**Key Insight:** Counter-VWAP MC after 9:50 = +0.118 ATR/trade (best subgroup). Before 9:50, all MC trades have negative expectancy regardless of filter.
**Recommendation:** Implement 9:50 gate + use counter-VWAP as quality bonus after 9:50 (not suppression filter).

---

## 5. v28b-tsla-dominance.md
**TSLA P&L:** 20.11 ATR = 78.9% of total 25.51 ATR. Rest of symbols: 5.39 ATR.
**Structural vs Regime:** TSLA's edge is PARTIALLY structural (1.575 MFE vs REST 0.242, 43.9% win vs 33.2%) and PARTIALLY concentration (Nov alone 10.21 = 51% of total).
**Consistency Risk:** Nov 2025 + Jan 2026 = 89% of TSLA's P&L. Recent fade (Feb -0.12, Mar -0.60).
**Without TSLA:** System barely profitable (0.007 ATR/trade, PF 1.08, -14.09 max drawdown). Only META shows real consistency (5/7 months).
**Recommendation:** Use ex-TSLA as floor, cap position concentration ~40%, monitor for 3+ consecutive flat/negative months.

---

## 6. v28a-vwap-counter-analysis.md
**Discovery:** BRK signals opposite VWAP side from direction (pullback-to-level pattern) have 83.3% win, 5.17x MFE/MAE ratio.
**Stats:** n=36, MFE 1.154 vs aligned 0.783, MAE 0.223 vs aligned 0.791. Binomial p=0.000019 (highly significant).
**By Type:** Yest H/L 89% win, Bear counter 92%, Bull counter 78%. Consistent across all symbols.
**Frequency:** ~1-2 per week (~22% of days). EMA-aligned prerequisite, VWAP position is differentiator.
**Insight:** Trend resumption (EMA) after VWAP overshoot creates low-MAE, high-MFE entries.

---

## 7. 2026-03-03-missed-moves.md
**Scope:** 6 large impulsive moves on 1 day, no signals fired (SPY up 11.24, QQQ up 10.75, NVDA up 2.58, AAPL down/up, TSLA up 6.30).
**Pattern:** All moves >1.5x ATR, all had VWAP crosses, avg 7.57x ATR. Max single 5m bar hit 2x+ ATR (should trigger big-move).
**Possible Reasons:** (1) Grinding drift past levels, (2) Already past key levels, (3) Afternoon dimming, (4) Once-per-session VWAP fired, (5) Evidence stack filters blocked.
**Gap Analysis:** No actionable fix suggested yet — likely combination of timing + already-fired signals.

---

## 8. v28a-signal-audit.md (first 100 lines)
**Total signals:** 7,044 (BRK 1,575, REV ~3,200, VWAP ~1,100, QBS 87, MC 1,209).
**Distribution:** 53% in 9:xx, 23% in 10:xx, 24% rest of day.
**QBS/MC Detail:** 87 QBS (Quiet Before Storm), 1,209 MC (Momentum Cascade).
**Opening Chaos:** 90/126 first MC signals at 9:35 (opening explosion). Frequent opposing pairs (126 days with both bull/bear within 10min).
**Audit scope:** 10 symbols, ~100 days Sep 2025–Mar 2026.

---

## Cross-File Action Items

| Item | Implication | Status |
|------|-------------|--------|
| MC 9:50 gate | Suppress all MC before 9:50 ET | Ready to implement |
| ⚡ size.large removal | Remove from big-move flag | Ready to implement |
| Runner Score vol | Change ≥5x to 2-3x | Ready to implement |
| ✓★ redefinition | `BRK AND vol<5.0 AND hour≤10` | Ready to implement |
| QBS/MC ✓★ removal | Keep only ✓ for QBS/MC | Ready to implement |
| Counter-VWAP bonus | Use for quality ranking post-9:50 (not suppression) | Research done, ready |
| TSLA concentration | Monitor 3+ months, cap at ~40% | Ongoing monitoring |
| Missed moves gap | Likely afternoon dimming or already-fired signals | Needs deeper dig |

---

## Est. Code Impact
- **High confidence fixes:** MC gate, ⚡ size, vol factor, ✓★ redefinition = ~50 lines total
- **Medium confidence:** Counter-VWAP bonus, QBS/MC ✓ removal = ~30 lines
- **Monitoring:** TSLA cap, missed moves deep dive = setup/logging only
