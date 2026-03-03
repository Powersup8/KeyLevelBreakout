# Deep Analysis Findings — March 2026

## Multi-Symbol Fingerprint (1841 signals, 13 symbols)

### Top Differentiators: Good vs Bad Breakouts

| Rank | Metric | GOOD (n=231) | BAD (n=809) | Gap |
|------|--------|-------------|------------|-----|
| 1 | **LOW levels** (PM L, Yest L, ORB L, Week L) | 65% | 49% | **+17%** |
| 2 | **Bear direction** | 65% | 49% | **+17%** |
| 3 | **EMA aligned** (5m EMA20+EMA50) | 90% | 78% | **+13%** |
| 4 | **Vol ≥ 5x** | 39% | 33% | **+6%** |
| 5 | VWAP aligned | 95% | 93% | +2% |
| 6 | Body ≥ 70% | 22% | 23% | -2% (not a differentiator!) |
| 7 | ADX ≥ 25 | 49% | 53% | -4% (inverse!) |
| 8 | Multi-level | 16% | 19% | -3% (inverse!) |

### Filter Validation

| Filter | Works? | Evidence | Action |
|--------|--------|----------|--------|
| **EMA Alignment** | **YES — strongest filter** | 90% vs 78%, +13% gap | Keep ON |
| **VWAP Direction** | YES | 95% vs 93%, nearly universal in good trades | Keep ON |
| **ADX > 20** | YES (threshold correct) | <20 worst CONF (22%), 20-25 best CONF (26%) | Keep ON |
| **Body ≥ 50%** | **NO — zero differentiation** | 49% good vs 48% bad | **Lower to 30% or remove** |
| **RS vs SPY** | Weak | -0.3% good vs 0.0% bad | Keep ON, low impact |

### ADX Barbell Effect (new finding)

| ADX Range | CONF Rate | Avg MFE | Interpretation |
|-----------|-----------|---------|----------------|
| <20 | 22% | 0.36 | Weakest — filter removes these ✓ |
| **20-25** | **26%** | 0.28 | **Sweet spot for hit rate** |
| 25-30 | 23% | 0.29 | Solid |
| 30-35 | 21% | 0.39 | Decent, better MFE |
| 35-50 | 19% | 0.32 | Lower hit rate |
| 50+ | 13% | **0.68** | Rare but explosive |

ADX 20-25 wins most often. ADX 50+ wins biggest. Don't raise the threshold above 20.

### Volume — 10x+ Is King (corrects v2.4 finding)

| Volume | CONF Rate | Avg MFE |
|--------|-----------|---------|
| <2x | 21% | 0.22 |
| 2-5x | 20% | 0.30 |
| 5-10x | 20% | 0.34 |
| **10x+** | **32%** | **0.50** |

**Correction:** v2.4 said "2-5x is the sweet spot" — WRONG across all symbols. 10x+ has both the best CONF rate AND best follow-through. Runner Score vol factor should change from 2-5x → ≥5x or ≥10x.

### CONF Rate by Level Type

| Level | CONF Rate | MFE | Tier |
|-------|-----------|-----|------|
| **Yest L** | **30%** | **0.41** | A — Best |
| PM L | 27% | 0.35 | A |
| ORB L | 27% | 0.32 | A |
| Week L | 22% | 0.28 | B |
| Week H | 20% | 0.29 | B |
| PM H | 18% | 0.36 | C |
| Yest H | 15% | 0.33 | C |
| **ORB H** | **14%** | 0.33 | C — Worst |

LOW levels have ~2x the CONF rate of HIGH levels across all symbols.

### Symbol Tiers

| Tier | Symbols | CONF Rate |
|------|---------|-----------|
| A | GOOGL (35%), TSLA (32%), QQQ (28%) | 28-35% |
| B | SPY (24%), NVDA (23%), AMZN (23%), SLV (22%) | 22-24% |
| C | META (21%), AMD (20%), MSFT (20%), TSM (19%) | 19-21% |
| D | AAPL (13%), GLD (6%) | 6-13% |

### Time of Day — MFE Tells the Real Story

| Time | CONF Rate | MFE |
|------|-----------|-----|
| 9:30-10:00 | 22% | **0.42** (best follow-through) |
| 10:00-11:00 | 22% | 0.31 |
| 11:00-12:00 | 28% | 0.38 |
| 12:00+ | 22% | **0.15** (worst follow-through) |

CONF rate is flat, but MFE drops sharply after noon. Afternoon dimming validated.

---

## v2.6e Fix: Reversal Volume Gate Removed

### Problem
TSLA 2/25 12:15 Week H rejection: price touched 416.90 (exact Week H), 95% body candle rejected below zone (C=415.23 < zone body 416.15). All conditions passed EXCEPT volume: 613K < threshold 804K (1.5x SMA20).

The volume filter was designed for breakouts (institutional continuation) but reversals are different — the rejection candle doesn't need high volume. The APPROACH had volume (12:00: 839K = 1.55x), the rejection is the signal.

### Fix (v2.6e)
Removed `volPassBull`/`volPassBear` from `bullRev()`/`bearRev()`. Reversals no longer require volume gate. Breakouts still do.

### Future options if too many false reversals appear:
- Option 2: Lower multiplier for reversals (1.0x instead of 1.5x)
- Option 3: Check volume on the APPROACH bar instead of the rejection bar

---

## TSLA 2/26 — "Level Desert" Problem

### What we caught
- 9:35: `▼ BRK PM L+Yest L` (16.5x vol, CONF ✓, MFE 0.47)
- 10:15: `▼ BRK Yest L` (1.5x vol, CONF ✓, MFE 0.44)
- 10:20: `▼ BRK ORB L` (3.3x vol, CONF ✓, MFE 0.21)

### What we missed

**10:34/35 bounce** (405.13 → 407.80, 97% body ▲, $2.67 in 5 min)
- No key level at $405 area
- All levels (PM L 411, Yest L 412.15, ORB L 410.92) already broken far above
- Week L (400.51) is far below
- This is a bounce off the **developing intraday low** — a level type we don't track

**11:34+ breakdown** (409.74 → 404.27, $5.47 in 25 min)
- VWAP was at 409.93 — price pushed to 410.17, got rejected at VWAP, then collapsed
- This is a **VWAP rejection** — VWAP used as filter but not as signal level
- No key level at 409-410 (ORB L = 410.92 already broken)
- The 1m candles show textbook selling: 11:36 body=83%, 11:37 body=94%, 11:38 body=67%

### Root cause: "Level Desert"
After the initial breaks (PM L at 9:35, Yest L at 10:15, ORB L at 10:20), ALL 8 key level types are either broken or far away. The indicator goes silent in exactly the zone where the biggest continuation/re-entry moves happen.

### Proposed solutions (prioritized)

**1. VWAP as a signal level (HIGH priority)**
- We already compute and plot VWAP
- Add VWAP rejection signals: wick pushes into VWAP, close rejects
- The 11:34 move is a textbook VWAP rejection that produced $5.47 in 25 min
- Would catch the most common "level desert" setup

**2. Intraday developing H/L (MEDIUM priority)**
- Track today's running high/low as dynamic levels
- Break of today's low → bearish continuation signal
- Bounce off today's low → bull reversal signal
- The 10:35 bounce is off the developing intraday low (~$405)
- More complex: levels keep updating throughout the day

**3. ORB extension levels (LOW priority)**
- After ORB L breaks, watch ORB L - 1 ATR as next support
- Creates "step-down" levels in the continuation zone
- Simple to implement but artificial

---

## Momentum Profile Reminder (from previous 5s analysis)

These findings should guide the deep analysis (next step):
- **Good signals peak at minute 23** — they accelerate, not decelerate
- **Bad signals turn negative in first 5 minutes** — early MAE gate works
- **85% of good signals never retrace below -0.10 ATR** — once they go, they go
- **Trailing stop (0.25 ATR from high, start at +0.05)** captures most good signal MFE

### The ideal trade template (from all data combined)
1. **Bear breakout** of Yest L or PM L
2. **EMA aligned** (below EMA20 + EMA50)
3. **10x+ volume** (or at least ≥5x)
4. **VWAP below** (with-trend)
5. **ADX 20-25** (trend starting, not exhausted)
6. **On GOOGL, TSLA, or QQQ**
7. **Before 11:00** (best MFE window)
8. **Check at 5 minutes:** if still positive → hold for the 23-minute acceleration
9. **Trail stop at 0.25 ATR** from running high after +0.05 ATR

---

## Big Move Fingerprint (9596 significant 5m bars, 13 symbols)

### Methodology
Scanned all 13 symbols' 5m data for "big bars" (body≥60%, range≥0.12 ATR), computed indicators (ADX, EMA9/20/50, VWAP distance, volume ratio), measured MFE/MAE from 5s candle data.

Classification: Runners (MFE>0.3 ATR): 8098 (84%) | Fakeouts (MFE<0.1, MAE<-0.15): 268 (3%) | Middle: 1230

### Key Findings

**1. Body ≥ 80% is a FAKEOUT indicator (INVERSE!)**
- Fakeouts: 55% have body ≥80%
- Runners: only 36% have body ≥80%
- Gap: -19% — the higher the body%, the MORE likely it's a fakeout/exhaustion
- **Action: Lower body filter from 50% to 30% or remove entirely**

**2. VWAP proximity is the best zone for follow-through**
- At VWAP (±0.1 ATR): **89% runner rate, 1.98 MFE** (best!)
- Far from VWAP (>0.3 ATR): 83%, 1.42 MFE
- Moves originating right at VWAP have 47% better MFE than extended moves
- **Action: Implement VWAP-as-signal-level — the most validated "level desert" fix**

**3. 5-minute gate is the single strongest predictor**
- >+0.15 ATR at 5min: **98% runner, 0% fakeout**
- >+0.05 ATR at 5min: 91% runner, 0% fakeout
- < -0.05 ATR at 5min: 81% runner, 5% fakeout
- This applies to ALL significant moves, not just key level signals
- Best combo: 5min >0.05 + EMA aligned + VWAP aligned → **93% runner, 0% fakeout** (n=1411)

**4. Vol ≥ 2x is MORE common in fakeouts (15%) than runners (8%)**
- For general big moves, high volume ratio signals exhaustion/capitulation
- Note: this is volume relative to 20-bar SMA, not absolute volume
- For key level breakouts specifically, high volume still matters (different context)

**5. Time confirmation**
- 9:30-10:00: **92% runner rate**, 2.35 MFE (best window)
- 12:00+: 84% runner rate, 1.42 MFE (still decent for big bars)
- The morning edge is real but the afternoon dropoff is less severe for big moves

**6. Bear direction edge persists**: 51% runners vs 44% fakeouts (+7% gap)

### Filter Stacking Results

| Stack | n | Runner% | Fakeout% | MFE |
|-------|---|---------|----------|-----|
| 5min >0.05 + EMA + VWAP | 1,411 | **93%** | **0%** | 1.75 |
| EMA + VWAP + bear + ADX≥20 + before 11 | 523 | 86% | 2% | 1.82 |
| EMA + VWAP + before 11 | 1,324 | 86% | 2% | 1.78 |
| EMA + VWAP + ADX≥20 + vol≥2x | 370 | 85% | 4% | 2.04 |

### Top Runners Clustering
The biggest runners cluster on specific dates:
- **2026-02-12 GLD**: Multiple 20+ ATR MFE moves (gold selloff day)
- **2026-02-26 SPY/QQQ/TSM**: Multi-symbol selloff (macro event)
- **2026-01-29 GLD**: 15+ ATR moves (gold reversal)
- Pattern: multi-symbol correlation events produce the biggest runners

### Top Fakeout Patterns
- **Late afternoon** (15:00-15:50): 11 of top 20 fakeouts — end-of-day reversal zone
- **High VWAP distance** (2-7 ATR from VWAP): extended moves that snap back
- **Everything aligned** (EMA ✓, VWAP ✓): false confidence — the alignment was from the PRIOR move, exhaustion is coming
- This explains the Vol ≥ 2x fakeout edge: volume spike at the END of a move = capitulation

---

## Data Files
- `debug/enriched-signals.csv` — 1841 signals with all computed indicators, ready for reuse
- `debug/big-moves.csv` — 9596 big moves with indicators and follow-through, ready for reuse
- `debug/big-move-fingerprint.md` — full big move fingerprint analysis
- `debug/multi-symbol-fingerprint.md` — full multi-symbol signal analysis
- `debug/good-trade-fingerprint.md` — TSLA-only analysis (with ADX/RS from Pine log)
- `debug/multi_symbol_fingerprint.py` — signal analysis script (loads 5m cache for indicators)
- `debug/big_move_fingerprint.py` — big move scanner script (5m + 5s data)
