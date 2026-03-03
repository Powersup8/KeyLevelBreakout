# Documentation Restructure Design

## Goal
Replace 6 overlapping docs (2,135 lines) with 3 lean, purpose-driven files (~650 lines total) plus an archive.

## Architecture
3 files, each for a different use case. Master TOC at the top of every file doubles as a file inventory — you see all files and their sections at a glance, then jump to the right one.

## File Inventory

| File | Use Case | ~Lines |
|------|----------|--------|
| **PLAYBOOK.md** | "What do I trade?" — open before market | ~150 |
| **KeyLevelBreakout.md** | "What does this mean?" — reference while trading | ~300 |
| **DESIGN-JOURNAL.md** | "Why did we build it this way?" — understanding the thinking | ~200 |
| KeyLevelBreakout_TV.md | TradingView description (unchanged) | 90 |
| docs/archive/ | Old docs preserved | moved |

## Master TOC (appears at top of each file)

```
## KeyLevelBreakout v2.8 — Documentation

| Doc | What's Inside |
|-----|---------------|
| [PLAYBOOK.md](PLAYBOOK.md) | Signal Catalog (best→worst), Time Windows, Avoid List, Decision Flowchart, Execution, Symbols |
| [KeyLevelBreakout.md](KeyLevelBreakout.md) | Setup, Signal Types, Label Anatomy, CONF System, Levels, Filters, Visuals, Alerts, Settings |
| [DESIGN-JOURNAL.md](DESIGN-JOURNAL.md) | The Idea, Data Foundation, Key Discoveries, Filter Validation, Evolution v2.3→v2.8, Dead Ends |
```

## File 1: PLAYBOOK.md

Everything ranked best-to-worst. Signal Catalog is the core — every signal type in one table, ordered by edge.

Sections:
1. **Signal Catalog** — ranked table: signal, how it looks, edge data, action
2. **Time Windows** — best→worst hours with CONF% and GOOD%
3. **Avoid List** — traps, bad levels, bad symbols, bad times
4. **Decision Flowchart** — signal fires → check time → check CONF → size
5. **Execution** — entry, stop loss (0.10/0.15 ATR), hold time (30 min), trailing stop
6. **Symbol Tiers** — A/B/C/D with best windows

Design rules:
- Every list/table sorted by value (best first)
- No explanations of "why" — that's the Journal
- No label format details — that's the Reference
- Actionable: every row tells you what to DO

## File 2: KeyLevelBreakout.md (rewrite)

The complete reference. Merges in Labels doc. Drops changelog.

Sections:
1. **Setup** — add to chart, extended hours, alert setup (3 steps)
2. **Signal Types** — breakout, reversal, reclaim, retest, QBS/MC, VWAP zone (each: trigger condition, label color, when it fires)
3. **Label Anatomy** — one annotated example breaking down every piece
4. **Confirmation System** — CONF ✓/✓★/✗, auto-promote, 5-min checkpoint, VWAP exit
5. **Levels** — PM/Yest/ORB/Week H/L + VWAP zone, zone widths, how computed
6. **Filters** — Evidence Stack (EMA, RS, ADX, Body) + VWAP + Volume, Suppress vs Dim
7. **Visual Elements** — VWAP line, SL lines, Runner Score ①-⑤, glyphs (⚡🔇🔊⚠), afternoon dimming, cooldown dimming
8. **Alerts** — programmatic alerts + 9 alertconditions, setup instructions
9. **Settings Reference** — all ~25 inputs in one table: setting, default, when to change

Design rules:
- Factual, not opinionated (no "trade this" / "avoid that")
- Complete: if it's on the chart, it's documented here
- Label Anatomy = single annotated example, not 445 lines of examples

## File 3: DESIGN-JOURNAL.md

The story of how data shaped the indicator. Absorbs insights from Improvements doc (719→~60 lines of real findings).

Sections:
1. **The Idea** — what problem, what market, what edge
2. **Data Foundation** — 1,841 signals, 9,596 big moves, 13 symbols, 28+ days, 5s/1m/5m candles
3. **Key Discoveries** — ranked by impact: EMA alignment, LOW>HIGH levels, VWAP proximity, body% inverse, volume ramp U-shape, 5-min gate
4. **Filter Validation** — what works (EMA, VWAP, ADX), what doesn't (body% noise), what surprised us
5. **Evolution** — v2.3→v2.8 in brief paragraphs, what changed and why at each step
6. **Dead Ends** — things we tried that didn't work (valuable for not repeating)

Design rules:
- Narrative, not tables (this is a story)
- No action items — everything is done
- Future ideas: simple bullet list at the end, max 10 items

## Migration Plan

| Current File | Action |
|---|---|
| `_TRADING-PLAYBOOK.md` | Content → `PLAYBOOK.md`, original → `docs/archive/` |
| `KeyLevelBreakout.md` | Rewritten in place |
| `KeyLevelBreakout_TV.md` | Unchanged |
| `KeyLevelBreakout_Labels.md` | Content → Reference Label Anatomy, original → `docs/archive/` |
| `KeyLevelBreakout_Improvements.md` | Insights → Journal, original → `docs/archive/` |
| `README.md` | Updated with new file inventory |
