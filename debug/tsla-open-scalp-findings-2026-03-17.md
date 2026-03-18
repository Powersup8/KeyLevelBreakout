# TSLA Open Scalp — Consolidated Research Findings
*Session: 2026-03-17 | Updated: 2026-03-18 | Data: 280 days (Feb 2025–Mar 2026), 1m/5s/30s/1s IB bars*

## Source Files
- `tsla_always_long_backtest.py` + `tsla_always_long_results.md` — always-long baseline
- `tsla_open_research_v2.py` + `tsla_open_research_v2.md` — Module P (premarket) + Module B (bad-day avoidance)
- `tsla_module_s_v2.py` + `tsla_module_s_v2.md` — Module S v2 (30s/VIX/SPY)
- `tsla_vix1d_extension.py` + `tsla_vix1d_extension.md` — VIX 1d extension (254 days) *(2026-03-18)*
- `tsla_pm_spy_qqq.py` + `tsla_pm_spy_qqq.md` — SPY/QQQ PM trend P10/P11/P12/P13 *(2026-03-18)*

Prior research: `open-scalp-learnings.md` (Parts A–F), `tsla-scalp-research.md` (R01–R14), `tsla-scalp-deep.md` (D01–D08)

---

## Part 1: The Baseline — Always Long Is Worthless

Data: 280 days, 1m bars. Buy at 9:30 open every day.

| Hold Time | Win% | Avg P&L | Sharpe |
|---|---|---|---|
| Best (3m) | 51.1% | +$0.14 | 0.72 |
| 30m | 48.2% | $0.00 | 0.01 |
| EOD | 50.0% | -$0.10 | -0.15 |

**Conclusion: No holding period produces a blind edge. The direction filter (5-min rule) is 100% responsible for the edge.**

---

## Part 2: The 5-Min Rule — Core Signal, Confirmed Robust

Validated across two separate study windows (271 days and 280 days). Results are stable.

| Signal | n | Win% | Avg P&L | Worst Day% | Sharpe |
|---|---|---|---|---|---|
| HOLD (9:35 close > 9:30 open) | 141 | **66.7%** | **+$3.10** | 16% | 5.01 |
| BAIL (9:35 close ≤ 9:30 open) | 139 | 32.0% | -$3.30 | 41% | — |
| Blind (no filter) | 280 | 50.0% | -$0.10 | 28% | -0.15 |

### Optimal Hold Time (HOLD days only)

| Hold | Win% | Avg P&L | Sharpe | Notes |
|---|---|---|---|---|
| 10m (exit 9:40) | **81.6%** | +$2.53 | **14.64** | Best win rate / risk-adjusted |
| 20m | 72.3% | +$2.78 | 11.09 | |
| EOD | 66.7% | **+$3.10** | 5.01 | Best raw P&L |

**Rule of thumb:** 10m exit = highest quality / lowest risk (Sharpe 14.64). EOD = highest P&L but more variance. For options (theta-sensitive): 10m exit preferred.

---

## Part 3: Premarket Signals (Module P) — 234 days, 1m bars

### P3 — PM Position at 9:29 (strongest PM signal)
Where does 9:29 close sit within the full 4am–9:29 range? (0=at PM low, 1=at PM high)

| Position | n | Win% | Avg P&L | Worst% |
|---|---|---|---|---|
| Bottom 25% (≤0.22) | 59 | 39% | **-$2.94** | 39% |
| Lower-mid | 58 | 57% | +$0.15 | 31% |
| Upper-mid | 58 | 50% | +$0.05 | 31% |
| Top 25% (≥0.72) | 59 | **59%** | **+$2.11** | **20%** |

**$5 P&L spread** between bottom and top quartile.

### P4 — PM Acceleration (9:25–9:29)
Is price accelerating or decelerating in the last 5 PM bars?

| Momentum | n | Win% | Avg P&L | Worst% |
|---|---|---|---|---|
| Strong down | 71 | 37% | -$1.85 | 38% |
| Mild down | 42 | 52% | +$0.27 | 33% |
| **Strong up** | **68** | **62%** | **+$0.47** | **21%** |

### P1 — Late PM Trend (9:20–9:29 direction)

| Trend | Win% | Avg P&L | Worst% |
|---|---|---|---|
| Down | 40% | -$0.52 | 38% |
| **Up** | **65%** | **+$1.36** | **19%** |

### P7 — Most Dangerous Combo: Gap Down + PM Flat

| Combo | Worst Day% | Avg P&L |
|---|---|---|
| Gap Down + PM Flat | **59%** | -$4.27 |
| Gap Down + PM Down | 43% | -$2.71 |
| Gap Down + PM Up | 25% | +$2.39 |

Gap down recovers if PM trend is positive. Gap down with no PM recovery = trap.

### P9 — PM Bear Composite (position < Q1 AND accel < threshold)
- Flags n=41 days: 37% win, -$1.97 avg, 37% worst
- Catches 21% of worst days with only 16% false-exclude rate

### B4 — Trapped Long Days (5m HOLD but day ends negative): 37 of 117 HOLD days (32%)

| | Trapped HOLD | Good HOLD |
|---|---|---|
| Avg PM position | 0.437 | 0.523 |
| Avg PM late trend | **-0.78** | +0.16 |
| Avg PM accel | **-0.57** | +0.21 |

**73% of trapped longs are flagged by PM bear signal** (pos < Q1 OR accel < 0).

### Strategy Impact (B3)

| Strategy | Trades | Win% | Avg P&L | Sharpe |
|---|---|---|---|---|
| Blind long | 234 | 51% | -$0.16 | -0.23 |
| 5m rule | 117 | 68% | +$3.02 | 4.58 |
| 5m rule + PM filter | **97** | **72%** | **+$3.59** | **5.43** |

---

## Part 4: Opening 30-Second Signals (Module S v2) — 129 days, 30s bars

### A2 — The Four Opening Patterns (bar1 × bar2 direction)

| Pattern | n | Win% | Avg P&L | Worst% |
|---|---|---|---|---|
| UP→UP (momentum) | 28 | **67.9%** | +$1.32 | 14.3% |
| UP→DOWN (fakeout) | 33 | 45.5% | +$0.56 | 33.3% |
| DOWN→UP (reversal) | 33 | 51.5% | +$0.69 | 24.2% |
| DOWN→DOWN | 35 | 42.9% | -$2.39 | **37.1%** |

### A6 — Pattern × 5m Rule (the critical cross-tab)

| Pattern | 5m | n | Win% | Avg P&L | Worst% |
|---|---|---|---|---|---|
| DOWN→DOWN | BAIL | 21 | **19.0%** | **-$6.42** | **52%** | ← worst
| UP→DOWN | BAIL | 16 | 31.2% | -$4.10 | **56%** | ← dangerous
| UP→UP | BAIL (thin) | 9 | 55.6% | +$1.16 | 11% | ← ignore BAIL
| DOWN→UP | **HOLD** | 10 | **70.0%** | **+$5.65** | 10% | ← best hold
| DOWN→DOWN | **HOLD** | 14 | **78.6%** | +$3.65 | 14% | ← surprise winner
| UP→UP | HOLD | 19 | 73.7% | +$1.40 | 16% | |

**Key insight:** DOWN→DOWN × HOLD is the highest-confidence hold (78.6%). Price dipped for the full first minute then recovered to above-open by 9:35 — every weak hand has been shaken out.

### A3 — Bar1 Range Sweet Spot

| Range | n | Win% | Avg P&L | Worst% |
|---|---|---|---|---|
| Tiny (≤$2.02) | 33 | 42.4% | -$1.51 | 33% |
| **Mid ($2.42–3.04)** | **32** | **59.4%** | **+$4.70** | **12.5%** |
| Wide (>$3.04) | 32 | 43.8% | -$3.88 | 41% |

A very wide first bar (>$3.04) signals chaotic auction — avoid. Sweet spot is $2.42–$3.04.

---

## Part 5: VIX Regime Conditioning — 254 days, VIX 1d prev-close *(updated 2026-03-18)*

*Prior analysis used VIX 1h (85 days). Extended to VIX 1d prev-close (254 days). Direction confirmed robust; Fear regime corrected.*

### VIX Regime × Outcomes

| Regime | n | Day Above% | Avg P&L | Worst% |
|---|---|---|---|---|
| **Calm (<18)** | 146 | 46.6% | **-$0.87** | 29% |
| **Moderate (18–25)** | **86** | **59.3%** | **+$2.05** | **20%** |
| Fear (>25) | 22 | 45.5% | +$1.72 | 32% |

**Key correction vs prior 85-day result:** Fear regime is NOT reliably negative — the prior 22.2% was a small-sample fluke. The real danger is **VIX ≤15** (44% worst-day rate, avg -$2.38). Moderate (18–25) remains the best regime.

### Worst-Day Rate by VIX Tier

| VIX tier | n | worst% | avg P&L |
|---|---|---|---|
| **≤15 (very low)** | 25 | **44.0%** | **-$2.38** ← most dangerous |
| 15–20 | 157 | 26.8% | -$0.16 |
| **20–25** | **50** | **12.0%** | **+$2.66** ← best |
| >25 | 22 | 31.8% | +$1.72 |

### VIX × 5m Rule

| VIX | 5m | n | Win% | Avg P&L | Worst% |
|---|---|---|---|---|---|
| **Moderate × HOLD** | | **43** | **76.7%** | **+$5.09** | **11.6%** |
| Calm × HOLD | | 70 | 65.7% | +$2.94 | 11.4% |
| Fear × HOLD (thin) | | 13 | 53.8% | +$4.09 | 23.1% |

**VIX moderate (18–25) + 5m HOLD = highest quality scenario. Confirmed on 3× the prior sample.**

---

## Part 6: SPY Relative Strength

### C4 — SPY at 9:35 Does NOT Add Signal for HOLD Days (280 days)

| Combo | n | Win% | Avg P&L |
|---|---|---|---|
| TSLA HOLD + SPY HOLD | 81 | 66.7% | +$3.27 |
| TSLA HOLD + SPY BAIL | 60 | **66.7%** | +$2.87 |

Identical win rates. **SPY confirmation is noise for TSLA HOLD decisions.**

However for BAIL: TSLA BAIL + SPY HOLD = -$3.66 avg (TSLA being sold despite market strength = extra bearish).

### C3 — TSLA Weak vs SPY in First 30s (thin, 55 days)
- Q1 (TSLA most underperforming SPY): 33.3% win, -$3.82 avg, 42% worst
- Directional signal — more data needed

---

## Part 7: Combined Strategies

| Strategy | Trades | Win% | Avg P&L | Sharpe |
|---|---|---|---|---|
| Always hold | 280 | 50.0% | -$0.10 | -0.16 |
| 5m rule | 141 | 66.7% | +$3.10 | 5.01 |
| 5m + PM filter (TSLA P9) | 97 | 72% | +$3.59 | 5.43 |
| 5m + no fakeout | 43 | 74.4% | +$3.12 | 5.27 |
| **5m + SPY + VIX + no fakeout** | **19** | **78.9%** | **+$3.87** | **8.05** |
| **Triple PM UP × 5m HOLD** | **25** | **80.0%** | **+$3.33** | — |

The combined filter (19 trades) and triple PM alignment (25 trades) are both highly selective — useful for max-confidence sizing. Triple PM alignment is the new pre-open quality tier.

---

## Part 8: SPY/QQQ Premarket Trend (P10/P11) — 234 days *(new 2026-03-18)*

### Key Finding: SPY/QQQ PM Structure is Mostly Noise for TSLA

SPY and QQQ PM position quartiles and late-trend direction **do not predict TSLA outcomes** on their own:
- SPY PM position quartiles: 45–57% day-above range, no clean gradient
- SPY PM late trend: UP=51.3% vs DOWN=50.4% — random
- QQQ PM late trend: UP=55.6% vs DOWN=46.8% — slight signal but weak

**SPY PM top half + 5m HOLD does add win rate (74.1% vs 66.7%)** but reduces trades from 117 to 58 and Sharpe drops (3.01 vs 3.10). Not worth it as a standalone filter.

**TSLA P9 bear composite alone is stronger than adding SPY PM:**

| Strategy | Trades | Win% | Avg P&L | Sharpe |
|---|---|---|---|---|
| 5m rule | 117 | 66.7% | +$3.00 | 3.10 |
| 5m + skip TSLA P9 bear | 97 | 71.1% | +$3.59 | 3.35 |
| 5m + SPY PM late UP | 60 | 68.3% | +$2.56 | 2.31 |
| 5m + skip TSLA P9 + SPY PM UP | 50 | 70.0% | +$2.90 | 2.33 |

Adding SPY PM on top of TSLA P9 cuts trades and reduces Sharpe. **Use TSLA P9 alone.**

### One Real Signal: Triple PM Alignment × 5m Rule

When TSLA + SPY + QQQ all trend up 9:20–9:29 AND 5m HOLD fires:

| Condition | n | Win% | Avg P&L | Worst% |
|---|---|---|---|---|
| **All 3 PM UP × 5m HOLD** | **25** | **80.0%** | **+$3.33** | **8.0%** |
| NOT all 3 UP × 5m HOLD | 92 | 63.0% | +$2.92 | 21.7% |

80% win / 8% worst-day is the highest confidence pre-open tier found. Use as a **size-up signal** when the triple alignment fires.

---

## Complete Decision Playbook

### Pre-Open (9:25–9:29) — available before market opens
1. **Compute PM position**: where is 9:29 close in 4am–9:29 range?
   - < 0.22 (bottom quartile) → caution flag
2. **Compute PM acceleration**: last 5m trend direction (9:25–9:29)
   - Negative → caution flag
3. **PM Bear Signal**: pos < 0.22 AND accel < 0 → consider skipping
4. **VIX check** *(updated 2026-03-18, validated on 254 days)*:
   - ≤15 (very low) → reduce size or skip (44% worst-day rate, complacency danger)
   - 15–18 → normal-minus sizing
   - 18–25 → **full size** (best regime, 12% worst-day, +$5.09 HOLD avg)
   - > 25 → caution, but not a hard skip (regime is neutral on full dataset)
5. **Gap + PM check**: gap down AND PM flat → 59% worst-day rate, skip
6. **Triple PM alignment** *(new)*: TSLA + SPY + QQQ all trending up 9:20–9:29?
   - Yes → size-up tier (80% win, 8% worst when 5m HOLD fires)

### At 9:30:30 (bar1 closes — first 30s)
6. **Bar1 range**: > $3.04 → chaotic auction, extra caution
7. **Bar1 direction**: note UP or DOWN

### At 9:31:00 (bar2 closes — second 30s)
8. **Fakeout check**: bar1 UP + bar2 DOWN → EXIT any longs immediately (31.2% win if 5m also BAIL)
9. **Momentum**: bar1 DOWN + bar2 DOWN → monitor closely; if 5m BAIL fires this is worst case (-$6.42)
10. **Reversal setup**: bar1 DOWN + bar2 DOWN → if price recovers to HOLD by 9:35 = **highest confidence** (78.6% win)

### At 9:35 (5m rule)
11. **HOLD** (close > open): trade. Best hold times:
    - 10m exit → 81.6% win, Sharpe 14.64 (options / size-sensitive)
    - EOD → 66.7% win, +$3.10 avg (stock / relaxed)
12. **BAIL** (close ≤ open): exit immediately. Don't hold hoping.
    - SPY direction irrelevant for the HOLD/BAIL decision
    - If TSLA BAIL + SPY HOLD → extra bearish for TSLA specifically

---

## Data Gaps / Follow-Up

| Gap | Impact | Status |
|---|---|---|
| VIX 5m only from Jan 2026 | VIX conditioning limited; now superseded by VIX 1d (254 days) | Mitigated by VIX 1d ✓ |
| TSLA 15s premarket = 30 days (Jan–Feb 2026) | Higher-res PM structure; growing as collection continues | Collecting — 30 days so far |
| ~~VIX 1d covers full period (254 days)~~ | ~~FREE~~ | **Done** ✓ (tsla_vix1d_extension.py) |
| ~~QQQ + SPY premarket 1m = 234 days~~ | ~~FREE~~ | **Done** ✓ (tsla_pm_spy_qqq.py) — mostly noise, triple alignment is useful |
| Options IV/skew = 4 days | Best pre-open fear indicator | Continue collecting |
