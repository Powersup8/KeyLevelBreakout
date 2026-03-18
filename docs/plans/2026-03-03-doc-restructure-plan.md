# Documentation Restructure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace 6 overlapping docs (2,135 lines) with 3 lean, purpose-driven files (~650 lines total).

**Architecture:** 3 files for 3 use cases: PLAYBOOK (trade decisions), Reference (what things mean), Journal (why we built it). Master TOC at top of every file as file inventory. Old docs archived.

**Tech Stack:** Markdown only. No code changes.

---

### Task 1: Archive Old Docs

**Files:**
- Move: `_TRADING-PLAYBOOK.md` → `docs/archive/_TRADING-PLAYBOOK.md`
- Move: `KeyLevelBreakout_Labels.md` → `docs/archive/KeyLevelBreakout_Labels.md`
- Move: `KeyLevelBreakout_Improvements.md` → `docs/archive/KeyLevelBreakout_Improvements.md`
- Move: `KeyLevelBreakout_Labels.pdf` → `docs/archive/KeyLevelBreakout_Labels.pdf`
- Keep: `KeyLevelBreakout_TV.md` (unchanged, TradingView-specific)

**Step 1:** Create `docs/archive/` directory and move files

**Step 2:** Verify files exist in new location

---

### Task 2: Write PLAYBOOK.md

**File:** Create `PLAYBOOK.md` (root level, ~150 lines)

**Content structure** (every section sorted best→worst):

1. **Master TOC** — file inventory linking all 3 docs
2. **Signal Catalog** — ranked table, 12 rows (CONF ✓★ → CONF ✗), columns: Rank, Signal, Look (how to spot), Edge (data), Action
3. **Time Windows** — 4 rows: 10:00-11:00 (best) → 13:00-16:00 (skip)
4. **Levels** — ranked: Yest L (best) → ORB H (worst), LOW >> HIGH rule
5. **Avoid List** — compact table of traps (afternoon, ORB H, <2x vol, reclaims, D-tier symbols, Wed/Fri)
6. **Decision Flowchart** — ASCII tree from current playbook §4
7. **Execution** — stop loss (0.10/0.15 ATR), hold 30 min, trailing stop at 5 min, VWAP exit
8. **Sizing** — 6 rows: ✓★ full → ✗ exit
9. **Symbol Tiers** — A/B/C/D with best windows
10. **Day of Week** — Mon→Fri ranked

**Source data:** Pull all stats from `_TRADING-PLAYBOOK.md`. QBS/MC data from v2.8 additions. Runner Score factors updated (vol ≥5x, time 9:30-10, +TSM D-tier).

---

### Task 3: Rewrite KeyLevelBreakout.md

**File:** Rewrite `KeyLevelBreakout.md` in place (~300 lines)

**Content structure:**

1. **Master TOC** — same file inventory as PLAYBOOK
2. **Setup** — 3 steps (paste, extended hours, alert)
3. **Signal Types** — 6 types, each with: trigger, label color, direction rule. Order: Breakout → Reversal → Reclaim → Retest → QBS/MC → VWAP Zone
4. **Label Anatomy** — ONE annotated example: `⚡🔇 ORB L + PM L \n 5.5x ^92 ④ ⚠` with arrows to each part. Then compact metrics table (~12 rows).
5. **Confirmation System** — CONF ✓/✓★/✗, auto-promote only, 5-min checkpoint, VWAP exit alert
6. **Levels** — 4 types (PM/Yest/ORB/Week) + VWAP zone, zone widths, computation source
7. **Filters** — Evidence Stack (4 filters) + VWAP + Volume. Table: filter, what it does, default, when to override
8. **Visual Elements** — VWAP line, SL lines, Runner Score, glyphs (⚡🔇🔊⚠), afternoon dimming, cooldown. Visual overlays table from Labels doc.
9. **Alerts** — programmatic + 9 alertconditions, message format examples
10. **Settings Reference** — ALL ~25 inputs in one table: setting, default, when to change
11. **Direction Reference** — the 4-setup direction table + ASCII visual from current doc

**Source data:** Merge `KeyLevelBreakout.md` features/inputs/setup + `KeyLevelBreakout_Labels.md` label anatomy + metrics + visual overlays. Drop changelog (→ archive).

---

### Task 4: Write DESIGN-JOURNAL.md

**File:** Create `DESIGN-JOURNAL.md` (root level, ~200 lines)

**Content structure:**

1. **Master TOC** — same file inventory
2. **The Idea** — what problem (level-based breakout detection for US equities), what edge (institutional levels + volume + confirmation)
3. **Data Foundation** — datasets: 1,841 signals (13 symbols, 28 days), 9,596 big moves (5m bars), 2,069 big moves (2x ATR), 5s/1m/5m candle data. Scripts in `debug/`.
4. **Key Discoveries** — ranked by impact on indicator code:
   - EMA alignment = strongest filter (+13% gap)
   - LOW levels >> HIGH levels (+17%)
   - VWAP proximity = best zone (89% runner, 1.98 MFE)
   - 5-minute gate (93% runner, 0% fakeout when positive)
   - Volume ramp U-shape (drying 68%, explosive 64%, moderate 56% worst)
   - Body ≥80% = INVERSE fakeout indicator (55% fakeout vs 36% runner)
   - CONF ✓ = 0% BAD (golden rule, 110 signals)
   - 10x+ volume = best CONF + MFE (corrects "2-5x sweet spot" myth)
5. **Filter Validation** — table: EMA YES, VWAP YES, ADX>20 YES, Body% NO (lowered), RS WEAK
6. **Evolution** — v1.0→v2.8 in brief (2-3 lines per version, what + why)
7. **Dead Ends** — what didn't work: body% filter, 2-5x volume, ADX fine-tuning, afternoon CONF (looks good, 0% follow-through), reclaims (3% GOOD)
8. **Three Pillars** — direction+level, VWAP location, momentum confirmation
9. **Future Ideas** — bullet list (max 10): HIGH-level dimming, GLD handling, FVG retests, weekly zone from 15m, level proximity warning, etc.

**Source data:** `KeyLevelBreakout_Improvements.md` §Multi-Symbol + §Big Move + §v2.4 proposals + changelog. Extract insights, discard implementation details.

---

### Task 5: Update README.md

**File:** Modify `README.md` (~20 lines)

Add KeyLevelBreakout file inventory at top, keep existing indicator table below.

---

### Task 6: Update MEMORY.md

**File:** Update doc structure references, add new file paths.
