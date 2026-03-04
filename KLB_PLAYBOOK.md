# KeyLevelBreakout v2.9 — Trading Playbook

| Doc | What's Inside |
|-----|---------------|
| **KLB_PLAYBOOK.md** | Signal Catalog, Time Windows, Avoid List, Decision Flowchart, Execution, Symbols |
| [KLB_Reference.md](KLB_Reference.md) | Setup, Signal Types, Label Anatomy, CONF System, Levels, Filters, Visuals, Alerts, Settings |
| [KLB_DESIGN-JOURNAL.md](KLB_DESIGN-JOURNAL.md) | The Idea, Data Foundation, Key Discoveries, Filter Validation, Evolution, Dead Ends |

> Based on 1,841 signals, 9,596 big moves, 13 symbols, 28+ trading days

---
## 1. Signal Catalog

| Rank | Signal | Look | Edge | Action |
|------|--------|------|------|--------|
| 1 | CONF ✓★ | Gold label, black text, ✓★ | BRK only, vol<5x, morning | Full size, hold 30 min |
| 2 | CONF ✓ | Solid green/red, white text, ✓ | 0% BAD (110 signals) | Large size, hold 30 min |
| 3 | 🔇 QBS | Cyan label, 🔇 | 68% runner, 3% fakeout | Wait for CONF, then trade |
| 4 | 🔊 MC | Orange label, 🔊 | 64% runner, best MFE 2.66 | Wait for CONF, then trade |
| 5 | ⚡ Big Move | Any label with ⚡ | 65% runner across 13 symbols | Size up if CONF follows |
| 6 | BRK Score ④-⑤ | Green/red label, ④ or ⑤ | Strong setup, low BAD | Standard size, wait for CONF |
| 7 | Retest ◆ | ◆ + superscript bars | Early (1-2 bars) strongest | Add to winner |
| 8 | BRK Score ①-③ | Green/red label, low score | Mixed | Small or skip |
| 9 | Reversal ~ | Blue (bull) / orange (bear) | Level rejection | Selective — context matters |
| 10 | Reclaim ~~ | Brighter blue/orange | False breakout rejection | Skip unless CONF ✓ follows |
| 11 | ⚠ Body warn | Any label with ⚠ | 55% fakeout — INVERSE! | Reduce size or skip |
| 12 | Gray ? (dimmed) | Gray, tiny, ? suffix | Filtered or moderate ramp | Do not trade |
| 13 | CONF ✗ | Grayed out label | Failed breakout | Exit immediately |

**The golden rule:** CONF ✓ has 0% BAD rate across 110 signals.

---
## 2. Time Windows

| Window | CONF% | GOOD% | Verdict |
|--------|-------|-------|---------|
| 10:00-11:00 | 60% | 4.3% GOOD, 1.6% BAD | BEST -- trade any with-trend BRK |
| 9:30-10:00 | High variance | Best MFE (0.42 ATR) | Trade 2-5x vol + VWAP aligned. Skip <2x |
| 11:00-13:00 | ~49% | 0% GOOD | Skip -- breakeven at best |
| 13:00-16:00 | ~49% | 0% GOOD, negative MFE/MAE | SKIP -- looks fine, loses money |

---
## 3. Levels

| Level | CONF% | GOOD% | BAD% | Verdict |
|-------|-------|-------|------|---------|
| Yest L | 60% | 12.7% | 3.3% | #1 -- trade every time |
| Week L | 55% | 10.8% | 1.5% | Rare but excellent |
| PM L | 47% | 10.7% | 3.4% | #2 for follow-through |
| ORB L | 45% | 9.0% | 3.4% | Solid, frequent |
| Yest H | 59% | 4.3% | 6.9% | High CONF, weak follow-through |
| PM H | 53% | 6.2% | 8.4% | Risky -- high BAD |
| Week H | 43% | 5.2% | 8.6% | Risky |
| ORB H | 43% | 3.5% | 8.5% | Worst -- avoid |

**Rule: LOW levels >> HIGH levels.**

---
## 4. Avoid List

| Trap | Why | Data |
|------|-----|------|
| After 11:00 | 0% GOOD follow-through | MFE/MAE = 0.90 |
| CONF ✗ | Failed breakout | Exit immediately |
| ORB H breakouts | Worst level | 3.5% GOOD, 8.5% BAD |
| <2x volume | No conviction | 1.5% GOOD, 1.2% BAD |
| HIGH levels generally | Higher BAD rates | ORB H 8.5% BAD vs ORB L 3.4% |
| AMD, MSFT, GLD, TSM | Lowest CONF, poor edge | AMD: 0.81 MFE/MAE |
| Wednesday / Friday | Worst CONF days | 35%, 34% vs Mon 56% |
| Reclaims ~~ | Noise | 3% GOOD -- skip unless CONF ✓ |
| ⚠ Body ≥80% | Fakeout indicator | 55% fakeout vs 36% runner |
| Gray ? dimmed | Failed filter | Do not trade |

---
## 5. Decision Flowchart

```
Signal fires --> Is it dimmed/suppressed?
  |-- Gray with ? --> Skip
  '-- Normal color --> Check time:
      |-- 9:30-10:00? --> Vol 2-5x + VWAP? --> Trade. <2x? --> Skip
      |-- 10:00-11:00? --> BEST WINDOW. Any with-trend BRK --> Trade
      |-- 11:00-13:00? --> Skip
      '-- 13:00-16:00? --> Skip

After BRK:
  CONF ✓  --> Size up (0% BAD)
  CONF ✓★ --> Full size (27% GOOD)
  CONF ✗  --> Exit immediately

Levels: Yest L > PM L > ORB L > Week L. Avoid HIGH levels.
```

---
## 6. Execution

**Entry:** On signal bar close (5m confirmed). Wait for CONF before sizing up.

**Stop Loss** (visible on chart after CONF):
- 0.10 ATR dashed orange -- early warning. If here at minute 2, likely BAD.
- 0.15 ATR solid red -- hard stop. BAD signals hit by minute 5.
- At 5 min: if positive, switch to 0.25 ATR trailing stop from high.

**Hold Time:** 30 min minimum. GOOD peak at minute 23. BAD peak at minute 3.5. 85% of GOOD never reverse below -0.10 ATR.

**VWAP Exit:** After CONF ✓/✓★, alert fires when price crosses VWAP against position. Momentum death signal.

**5-Min Checkpoint:** Label updates with 5m✓ (hold) or 5m✗ (bail).

---
## 7. Sizing

| Signal | Size |
|--------|------|
| CONF ✓★ (gold) | Full |
| CONF ✓ (solid green/red) | Large |
| Score ④-⑤ unconfirmed | Standard |
| Score ①-③ unconfirmed | Small or skip |
| Dimmed (gray ?) | Do not trade |
| CONF ✗ | Exit |

---
## 8. Runner Score ①-⑤

| Score | Avg ATR | BAD% |
|-------|---------|------|
| ⑤ | +0.071 | 1.4% |
| ④ | +0.050 | 2.3% |
| ③ | +0.047 | 2.4% |
| ①② | Weak | Higher |

5 factors: VWAP aligned, vol 2-5x, time 9:30-10, level quality (LOW for bear, confluence for bull), not D-tier symbol.

---
## 9. Symbol Tiers

| Tier | Symbol | CONF% | Best Window |
|------|--------|-------|-------------|
| A | AMZN | 62% | 10-11 (69%) |
| A | QQQ | 59% | 10-11 (64%) |
| A | SPY | 59% | 10-11 (61%) |
| B | AAPL | 48% | 10-11 (64%) |
| B | GOOGL | 47% | 10-11 (60%) |
| B | META | 46% | 13-16 (67%) |
| B | NVDA | 45% | 10-11 (55%) |
| B | TSLA | 43% | Midday (50%) |
| C | TSM | 44% | 13-16 (60%) |
| C | SLV | 42% | 11-13 (67%) |
| D | AMD | 41% | -- |
| D | MSFT | 40% | -- |
| D | GLD | 40% | -- |

---
## 10. Day of Week

| Day | CONF% | Tip |
|-----|-------|-----|
| Mon | 56% | Best -- trade confidently |
| Thu | 41% | Average |
| Tue | 39% | Average |
| Wed | 35% | Below average |
| Fri | 34% | Worst -- be selective |
