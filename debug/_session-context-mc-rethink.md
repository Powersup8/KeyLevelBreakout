# MC Rethink Session Context
**Date:** 2026-03-04
**Status:** Research complete, ready for implementation

## What We Did
8 rounds of data-driven optimization to redesign/replace the MC (Momentum Cascade) system.

## Key Conclusion
**Kill MC + EMA hard gate (all-day) + auto-confirm (EMA + time<10:30)**

- Current total PnL: +70.3 ATR (1,841 signals)
- After changes: +115.9 ATR (1,350 signals, +65% improvement)
- Net code: -65 lines (remove ~80 lines MC, add ~15 lines gate+auto-confirm)

## The Three Changes (ranked by impact)

### 1. EMA Hard Gate All-Day (+45.6 ATR recovered)
- Non-EMA signals are NET NEGATIVE both pre-9:50 (-32.3 ATR, N=283) and post-9:50 (-13.3 ATR, N=208)
- Removing them all-day: N drops 1841→1350, PnL jumps +70.3→+115.9
- Implementation: after 9:50 → suppress entirely. Before 9:50 → dim (EMA not established at open)
- Validation: 12/13 symbols positive, both time-halves positive

### 2. Kill MC Entirely (~0 ATR impact, but removes complexity)
- MC fires 99.4% before 9:50 on opening noise
- Opposing pairs (both bull+bear MC fire) = coin flip (45/55%)
- Volume ramp >5x almost never occurs after 9:50
- Only 7 MC signals would fire after 9:50 even with open slots
- Remove: signal generation, auto-confirm mechanism, orange labels, 🔊 glyphs, alerts

### 3. Auto-Confirm R1: EMA + Time<10:30 (+3.8 ATR, faster entry)
- N=389, +0.106/signal, 58.6% win, MFE/MAE 1.60
- 12/13 symbols positive
- Replaces MC's two-step process (MC fires → confirms later signal) with one-step (signal meets criteria → auto-confirmed)
- 2nd half degrades to +0.030/sig (from +0.179) — runner-dependent, expected

## Round-by-Round Findings

| Round | Focus | Key Finding |
|-------|-------|-------------|
| 1 | Original Option C (11AM, REV, A-tier) | All theorized factors had NEGATIVE delta. Scrapped. |
| 2 | Clean up: remove CONF (cheating), redundancy | Bear/VWAP=below 94% redundant (phi=0.90). Clean 7 factors. |
| 3 | Optimize thresholds + weights | Best cutoffs: time<10:30, ADX>40, body>40, vol≥2x |
| 4 | Validation: time-split + symbol-split | Both halves positive, 12/13 symbols profitable. Robust. |
| 5 | Simplify | **EMA Aligned alone = 92% of full 9-factor model.** |
| 6 | EMA gate: hard suppress vs dim | Non-EMA net negative EVERYWHERE. EMA gate all-day = +65% PnL. |
| 7 | Auto-confirm rules (MC replacement) | R1 (EMA+time<10:30) best broad rule. R4 (bear) sharper. |
| 8 | Robustness + final config | 12/13 symbols ✓, both halves ✓, smooth gradient. |

## Factor Ranking (final, validated)

| Rank | Factor | MFE Δ | Status |
|------|--------|------:|--------|
| 1 | EMA Aligned | +0.128 | **Dominant** — 92% of edge |
| 2 | ADX > 40 | +0.086 | Sharp per-signal, rare (N=95) |
| 3 | Counter-VWAP | +0.060 | High quality, very rare (N=52) |
| 4 | Dir = Bear | +0.050 | Broad, independent |
| 5 | Time < 10:30 | +0.047 | Morning advantage |
| 6 | Body > 40 | +0.033 | Modest |
| 7 | Vol ≥ 2x | +0.021 | Weak |
| 8 | Level = LOW | +0.019 | Weak |
| 9 | Type = BRK | +0.016 | Weak |

## Dead Ends (do NOT revisit)
- Counter-VWAP as primary signal (N=52, too rare for system)
- 11 AM window as factor (negative delta when properly tested)
- A-tier symbol filter (negative delta -0.026)
- Volume surges after 9:50 (exhaustion, not continuation)
- Complex 9-factor scoring (marginal +4.4 ATR over EMA alone)
- Smart filtering of opposing MC pairs at open (nothing works)
- Consecutive bar streaks (+2% edge, not worth complexity)
- VWAP crosses after 9:50 (no edge vs baseline)

## Analysis Files Created This Session

| File | Contents |
|------|----------|
| `debug/v29-mc-rethink-knowledge.md` | Comprehensive MC knowledge base from 10 analysis files |
| `debug/v29-momentum-patterns.md` | Intraday momentum pattern analysis (11K signals) |
| `debug/v29-mc-compare-ac.md` | Option A vs Option C (original) comparison |
| `debug/v29-mc-factor-screen.md` | Full factor screen (23 features ranked) |
| `debug/v29-mc-optimize.md` | Rounds 2-5: cleanup, thresholds, weights, validation |
| `debug/v29-mc-rounds678.md` | Rounds 6-8: EMA gate, auto-confirm rules, robustness |
| `debug/v29_mc_compare_ac.py` | Script: Option A vs C |
| `debug/v29_mc_factor_screen.py` | Script: factor screen |
| `debug/v29_mc_optimize.py` | Script: multi-round optimization |
| `debug/v29_mc_rounds678.py` | Script: rounds 6-8 analysis |
| `debug/v29_momentum_patterns.py` | Script: momentum pattern analysis |
| `debug/v29-mc-gate-analysis.md` | MC 9:50 gate P&L analysis (from earlier session) |
| `debug/v29-mc-slot-recovery.md` | MC slot recovery analysis (from earlier session) |

## Implementation Roadmap (for next session)

1. **EMA hard gate**: After 9:50 → suppress non-EMA signals. Before 9:50 → dim only.
2. **Kill MC**: Remove MC signal generation, auto-confirm, orange labels, 🔊, alerts.
3. **New auto-confirm**: EMA aligned + time < 10:30 → CONF ✓ without follow-through.
4. **Keep QBS** (🔇): Evaluate separately.
5. **Version → v3.0** (philosophy shift).
6. **Update docs**: KLB_PLAYBOOK.md, KLB_Reference.md, KLB_DESIGN-JOURNAL.md, MEMORY.md.
