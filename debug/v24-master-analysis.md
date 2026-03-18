# v2.4 Master Analysis — KeyLevelBreakout

> **2,588 signals, 1,059 BRK, 13 symbols, 28 trading days (Jan 20 – Feb 27 2026)**
> Cross-referenced: Pine Log CONF data + 1m candle follow-through (MFE/MAE)

---

## Executive Summary

v2.4 data validates most previous findings but reveals **5 major corrections** to our trading rules. The VWAP filter is decisively validated (+43pp CONF delta). The biggest surprise: **10:00–11:00 is the real sweet spot** (not 9:30–10:00), and **2–5x volume beats 10x+** for CONF rate.

---

## 1. What Changed From v2.2 Analysis

| Rule | v2.2 Finding | v2.4 Finding | Action |
|------|-------------|-------------|--------|
| **Best time** | 9:30-10 (48% CONF) | 10:00-11:00 (60% CONF, 1.29 MFE/MAE) | **SHIFT focus to 10-11** |
| **Volume sweet spot** | 10x+ (60% CONF) | 2-5x (58% CONF); 10x+ dropped to 32% | **Target 2-5x volume** |
| **Afternoon signals** | "Near-zero follow-through" | 49% CONF but 0% GOOD follow-through | **Nuance: CONF ≠ profit** |
| **VWAP filter** | Couldn't validate | 54% with-trend vs 10% counter-trend | **Confirmed: keep ON** |
| **Low volume** | 32% CONF | 47% CONF (+15pp) | **Less bad than thought** |

### Contradictions Resolved

**CONF rate ≠ follow-through.** This is the single most important insight from v2.4:
- Afternoon CONF = 49% (looks good!) but GOOD follow-through = 0% and MFE/MAE = 0.90 (negative expectancy)
- VWAP predicts CONF (54% vs 10%) but NOT follow-through magnitude (7.6% vs 7.1% GOOD)
- 10x+ volume has worst CONF (32%) but best follow-through when it does confirm (17.1% GOOD)

**Lesson:** Use CONF to filter, use follow-through to size.

---

## 2. VWAP Filter — First-Time Validation

| Alignment | BRK | CONF Rate | GOOD% (follow-through) |
|-----------|-----|-----------|----------------------|
| With-trend (bull+above, bear+below) | 984 | **54%** | 7.6% |
| Counter-trend (bull+below, bear+above) | 75 | **10%** | 7.1% |

**Verdict: VWAP filter is valuable.** Counter-trend BRK confirms only 10% of the time. The filter correctly suppresses these.

However, VWAP does NOT predict follow-through magnitude — among confirmed signals, with-trend and counter-trend move similarly. VWAP is a **gatekeeper**, not a **quality signal**.

### VWAP × Volume interaction
| Alignment | 2-5x vol CONF | 10x+ vol CONF |
|-----------|--------------|--------------|
| With-trend | 62% | 31% |
| Counter-trend | 6% | 100% (n=2) |

The 2-5x + with-trend combination is the highest-CONF bucket at **62%**.

---

## 3. Signal Quality Tiers (Updated)

### CONF Status
| Status | N | MFE_30 (ATR) | MAE_30 (ATR) | GOOD% | BAD% | Verdict |
|--------|---|-------------|-------------|-------|------|---------|
| **✓★** | 44* | 0.343 | 0.084 | 27.3% | 4.5% | Best signal — big moves |
| **✓** | 110 | 0.293 | 0.075 | 10.0% | **0.0%** | Golden rule holds — zero BAD |
| **✗** | 527 | 0.115 | 0.256 | 2.3% | 9.9% | Avoid completely |
| unknown | 383 | 0.265 | 0.097 | 12.0% | 2.1% | Pending (end-of-day artifacts) |

*✓★ has 4.5% BAD (new finding) — can happen when auto-promote fires but new BRK then fails too. Still overwhelmingly positive.*

### Volume Buckets
| Volume | CONF Rate | GOOD% | BAD% | Best for |
|--------|-----------|-------|------|----------|
| <2x | 47% | 1.5% | 1.2% | Flat — skip |
| **2-5x** | **58%** | **7.1%** | **3.4%** | **SWEET SPOT** |
| 5-10x | 50% | 9.1% | 13.9% | Mixed — needs filter |
| 10x+ | 32% | 17.1% | 9.5% | High reward IF confirmed |

### Time Buckets
| Time | CONF Rate | MFE/MAE | GOOD% | BAD% | Verdict |
|------|-----------|---------|-------|------|---------|
| **9:30-10:00** | 45% | 1.13 | 12.7% | 10.6% | High volume, high variance |
| **10:00-11:00** | **60%** | **1.29** | **4.3%** | **1.6%** | **BEST risk/reward** |
| 11:00-13:00 | 45% | 1.08 | 3.8% | 0.0% | Low activity, breakeven |
| 13:00-16:00 | 52% | **0.90** | **0.0%** | 1.0% | **AVOID — negative expectancy** |

### Levels
| Level | CONF Rate | GOOD% | BAD% | Verdict |
|-------|-----------|-------|------|---------|
| **Yest L** | **60%** | **12.7%** | 3.3% | **#1 overall** |
| **Yest H** | **59%** | 4.3% | 6.9% | High CONF, weak follow-through |
| **Week L** | 55% | 10.8% | 1.5% | Strong when it fires (rare) |
| PM H | 53% | 6.2% | 8.4% | Okay CONF, risky |
| PM L | 47% | 10.7% | 3.4% | Great follow-through |
| ORB L | 45% | 9.0% | 3.4% | Solid |
| ORB H | 43% | 3.5% | 8.5% | Worst — high BAD rate |
| Week H | 43% | 5.2% | 8.6% | Risky |

**Pattern: LOW levels massively outperform HIGH levels in follow-through.** Yest L has 12.7% GOOD vs Yest H 4.3%. ORB L has 9.0% GOOD vs ORB H 3.5%. HIGH levels have higher BAD rates.

---

## 4. Symbol Rankings (Updated)

| Rank | Symbol | CONF Rate | GOOD% | BAD% | MFE/MAE | Tier |
|------|--------|-----------|-------|------|---------|------|
| 1 | **AMZN** | 62% | 8.7% | 4.3% | 1.06 | A |
| 2 | **QQQ** | 59% | 12.3% | 6.2% | 1.34 | A |
| 3 | **SPY** | 59% | 9.8% | 6.5% | 1.11 | A |
| 4 | **TSM** | 56% | 7.1% | 12.2% | 0.99 | B- (high BAD) |
| 5 | **META** | 53% | 5.1% | 3.0% | 1.31 | B |
| 6 | **NVDA** | 53% | 12.0% | 7.2% | 1.08 | B |
| 7 | **GOOGL** | 52% | 8.0% | 3.4% | 1.31 | B |
| 8 | **AAPL** | 51% | 6.4% | 6.4% | 1.17 | B |
| 9 | **TSLA** | 50% | 5.3% | 1.3% | 1.17 | B (safest) |
| 10 | **SLV** | 48% | 5.8% | 4.3% | 1.44 | C |
| 11 | **AMD** | 41% | 5.2% | 10.4% | 0.81 | D (avoid) |
| 12 | **GLD** | 40% | 8.0% | 5.3% | 1.25 | C |
| 13 | **MSFT** | 40% | 5.0% | 3.8% | 0.88 | D (avoid) |

**Changes:** AMZN jumped from B-tier to #1. TSM dropped due to high BAD rate (12.2%). TSLA has lowest BAD rate (1.3%) — safest to trade.

---

## 5. High-Conviction ✓★ Profile

- **95 total ✓★** across 28 days (~3.4/day)
- **Average volume:** 5.9x (not necessarily 10x+ — most are 2-10x range)
- **98% with-trend** (only 2 counter-trend)
- **95% before 11:00** (69 in 9:30-10, 21 in 10-11)
- **Top levels:** ORB H (33), ORB L (22), Yest L (14)
- **Top symbols:** TSM (13), NVDA (10), AAPL (9), META (9)

### ✓★ Follow-Through
- MFE_30 = 0.343 ATR (vs 0.197 overall)
- 27.3% GOOD rate (vs 7.6% overall)
- 4.5% BAD rate (small risk exists)

---

## 6. Day Patterns

### Best Days (>60% CONF)
| Date | CONF Rate | BRK | Note |
|------|-----------|-----|------|
| Feb 2 | **81%** | 48 | Best day — strong trend |
| Jan 22 | 75% | 7 | Small sample |
| Jan 23 | 75% | 6 | Small sample |
| Jan 29 | 71% | 43 | Monster trend day (14 of top-20 signals) |
| Feb 6 | 67% | 36 | Clean trend |
| Feb 10 | 65% | 42 | Solid |
| Feb 9 | 64% | 26 | Clean |

### Worst Days (<35% CONF)
| Date | CONF Rate | BRK | Note |
|------|-----------|-----|------|
| Feb 19 | **25%** | 36 | Worst day — avoid |
| Jan 28 | 33% | 51 | High volume chop |
| Feb 27 | 34% | 40 | Recent — weak |
| Feb 13 | 35% | 30 | Choppy |

### Chop Detection (first 3 BRK all fail)
Only 2/28 days flagged (7%). One (Jan 29) was actually a 71% day — **false positive**. The chop detector needs tuning.

---

## 7. Reclaim (~~ ~~) Deep Dive

- **239 reclaims** — 89% follow a prior CONF ✗ (validates the gate logic)
- Reclaims don't have their own CONF tracking (they're reversal-type signals)
- **91 reclaims (38%) fire in the afternoon** — the most time-concentrated signal type
- All 239 are with-trend VWAP — the filter correctly suppresses counter-trend reclaims

---

## 8. Optimal Trade Execution

### Entry
- **Wait for 10:00–11:00 window** (60% CONF, best risk/reward)
- If trading 9:30–10:00, use tighter stops (high BAD rate 10.6%)
- **Target 2-5x volume** — avoid <2x (flat) and be cautious with 10x+ (often first-bar noise)

### Level Selection
- **Prefer LOW levels** (Yest L, PM L, ORB L, Week L) — much better follow-through
- **Be cautious with HIGH levels** (ORB H, PM H, Week H) — higher BAD rates
- **Yest L is the #1 level** — 60% CONF, 12.7% GOOD

### Hold Time
- MFE/MAE ratio peaks at **30 minutes** for GOOD signals (12.61 ratio)
- For GOOD signals: avg MFE_30 = 0.744 ATR with only 0.059 ATR adverse
- 60 min adds marginal gain (0.907 ATR) but risk increases slightly

### Stop Loss
- For GOOD signals: average MAE = 0.059 ATR at 30 min
- Suggests a **0.15 ATR stop** would capture most winners while cutting losers

### Position Sizing
- CONF ✓ signals: size up (0% BAD)
- ✓★ signals: aggressive size (27.3% GOOD) but acknowledge 4.5% BAD risk
- Unconfirmed signals: standard size until CONF resolves
- CONF ✗: exit immediately

---

## 9. What We Might Have Missed

1. **Jan 29 dominance** — 14 of top-20 signals are from ONE day. Need to verify patterns hold on other days.
2. **Counter-trend sample size** — only 75 counter-trend BRK. VWAP filter conclusion is strong but based on limited counter-trend data.
3. **Multi-level breakouts** — not analyzed separately. "Yest H + Week H" might behave differently than single-level.
4. **Day-of-week effects** — not analyzed.
5. **Symbol × time interactions** — some symbols might have different optimal windows.
6. **Reversal/reclaim follow-through** — follow-through analysis only covers BRK signals.

---

## 10. Rule Changes Summary

### KEEP (validated)
- CONF ✓ = 0% BAD (golden rule holds)
- VWAP filter ON (validated: +43pp CONF delta)
- Afternoon signals = avoid (0% GOOD follow-through despite decent CONF)
- LOW levels > HIGH levels

### CHANGE
- **Best time: 10:00-11:00** (not 9:30-10:00)
- **Best volume: 2-5x** (not 10x+)
- **AMZN is A-tier** (moved up from B)
- **TSM is risky** (12.2% BAD rate — moved to B-)
- **AMD and MSFT avoid** (40-41% CONF, poor MFE/MAE)

### NEW
- VWAP with-trend is a strong signal (+43pp CONF)
- ✓★ has 4.5% BAD risk (was thought to be 0%)
- 10x+ volume = high reward IF confirmed, but low CONF (32%)
- Reclaims are 89% post-CONF-✗ (gate logic works)
- Chop detector needs tuning (50% false positive rate)
