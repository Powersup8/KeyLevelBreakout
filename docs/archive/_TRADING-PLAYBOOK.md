# KeyLevelBreakout Trading Playbook v3.1

> Based on 1,841 signals, 13 symbols, 28 trading days (Jan 20 - Feb 27 2026)
> v2.6 with Runner Score, VWAP line, SL lines, VWAP exit alert + Evidence Stack Filters

---

## 1. TAKE These Trades

| Setup | CONF Rate | GOOD% | BAD% | How to spot |
|-------|-----------|-------|------|-------------|
| **CONF ✓ (any)** | — | 10% | **0%** | Solid green (bull) / red (bear) label with ✓, white text — zero BAD rate |
| **CONF ✓★** | — | 27.3% | 4.5% | Gold label with ✓★, black text — biggest moves |
| **2-5x vol + with-trend VWAP** | **62%** | 7.1% | 3.4% | Best CONF bucket overall |
| **10:00-11:00 window** | **60%** | 4.3% | 1.6% | Best risk/reward of the day |
| **Yest L breakout** | **60%** | 12.7% | 3.3% | #1 level for follow-through |
| **PM L breakout** | 47% | 10.7% | 3.4% | Great follow-through, high frequency |
| **Monday** | **56% CONF** | — | — | Best day of the week by far |

**The golden rule:** CONF ✓ has literally **0% BAD** rate across 110 signals. If ✓ appears, that's your highest conviction trade.

---

## 2. AVOID These

| Trap | Why | Data |
|------|-----|------|
| **Afternoon (after 11:00)** | CONF looks fine (49%) but 0% GOOD follow-through | MFE/MAE = 0.90 — negative expectancy |
| **CONF ✗ breakouts** | Immediate exit signal | 2.3% GOOD vs 10% for ✓ |
| **ORB H breakouts** | Worst level for follow-through | 3.5% GOOD, 8.5% BAD |
| **10x+ volume at open** | First-bar inflation — only 32% CONF | Lottery ticket, not core play |
| **<2x volume** | No conviction, flat P&L | 1.5% GOOD, 1.2% BAD |
| **HIGH levels (PM H, Yest H, Week H)** | Higher BAD rates than LOW levels | ORB H 8.5% BAD vs ORB L 3.4% |
| **AMD, MSFT, GLD** | Lowest CONF (40-41%) and poor edge | AMD: 0.81 MFE/MAE |
| **Wednesday / Friday** | Worst CONF days (35%, 34%) | Monday is 20pp better |
| **Reclaims (~~)** | Noise — only 3% GOOD, mostly neutral | Skip unless CONF ✓ follows |

---

## 3. Evidence Stack Filters (v2.5)

The indicator now has 4 filters that automatically suppress low-quality signals. **All ON by default.** They reduce signals by ~70% but improve GOOD:BAD from 3.0:1 to 3.8:1.

| Filter | What it does | When to override (turn OFF) |
|--------|-------------|----------------------------|
| **5m EMA Alignment** | Blocks signals against 5m EMA(20)/EMA(50) trend | Early trend reversals — if you see a major V-bottom forming |
| **RS vs SPY** | Blocks longs underperforming SPY (shorts outperforming) | Auto-skips for SPY, QQQ, GLD, SLV |
| **ADX > 20** | Blocks signals in choppy/no-trend environment | Narrow-range breakouts — sometimes the range-break IS the signal |
| **Candle Body Quality** | Blocks wick-heavy candles (body < 50%, close in wrong zone) | Gap-and-go opens where the candle shape is distorted |

**Filter Mode:** Suppress (default) hides signals entirely. Switch to **Dim** if you want to see what's being filtered (gray labels with `?`).

**When to turn filters OFF:** If you're seeing very few signals on a day you know is active, try Dim mode first to see what's being caught. Individual filters can be toggled independently.

---

## 4. Decision Flowchart

```
Signal fires → Is it dimmed/suppressed?
  ├─ Dimmed (gray with ?) → Low conviction — skip unless very strong context
  └─ Normal color → Check time:
      ├─ 9:30-10:00? → High variance window
      │   ├─ Volume 2-5x + with-trend VWAP? → Trade it
      │   ├─ Volume 10x+? → Lottery ticket — small size
      │   └─ Volume <2x? → Skip
      ├─ 10:00-11:00? → BEST WINDOW (60% CONF)
      │   ├─ Any BRK with-trend VWAP → Trade it
      │   └─ Wait for CONF ✓ to size up
      ├─ 11:00-13:00? → Low activity, breakeven — skip
      └─ 13:00-16:00? → SKIP (0% GOOD, negative MFE/MAE)

After any BRK:
  CONF ✓  → Size up (0% BAD) — solid green/red with white text
  CONF ✓★ → Full size (27% GOOD, gold label)
  CONF ✗  → Exit immediately (grayed out)

Level preference: LOW levels (Yest L > PM L > ORB L > Week L)
Avoid: HIGH levels (ORB H worst at 8.5% BAD)
```

---

## 5. Symbol Tiers + Best Windows

| Tier | Symbol | CONF% | Best Time Window | Notes |
|------|--------|-------|------------------|-------|
| **A** | **AMZN** | 62% | 10-11 (69%) | #1 overall |
| **A** | **QQQ** | 59% | 10-11 (64%) | Great 10-11 window |
| **A** | **SPY** | 59% | 10-11 (61%) | RS filter auto-bypasses |
| B | AAPL | 48% | 10-11 (64%) | Strong 10-11, weak afternoon |
| B | GOOGL | 47% | 10-11 (60%), 13-16 (58%) | Rare afternoon pick |
| B | META | 46% | 13-16 (67%) | Unusual: best afternoon |
| B | NVDA | 45% | 10-11 (55%) | Solid, follows the pack |
| B | TSLA | 43% | Midday (50%) | Erratic but low BAD (1.3%) |
| C | TSM | 44% | 13-16 (60%) | Afternoon decent |
| C | SLV | 42% | 11-13 (67%) | Morning terrible (17%) |
| **D** | **AMD** | 41% | — | Avoid — negative edge |
| **D** | **MSFT** | 40% | — | Flat, no standout window |
| **D** | **GLD** | 40% | — | Anti-correlated with market |

---

## 6. Level Cheat Sheet

| Level | CONF% | GOOD% | BAD% | Verdict |
|-------|-------|-------|------|---------|
| **Yest L** | **60%** | **12.7%** | 3.3% | **#1 — trade every time** |
| **PM L** | 47% | **10.7%** | 3.4% | **#2 for follow-through** |
| Week L | 55% | 10.8% | 1.5% | Rare but excellent risk/reward |
| ORB L | 45% | 9.0% | 3.4% | Solid, frequent |
| Yest H | 59% | 4.3% | 6.9% | High CONF but weak follow-through |
| PM H | 53% | 6.2% | 8.4% | Risky — high BAD |
| ORB H | 43% | 3.5% | **8.5%** | **Worst — avoid** |
| Week H | 43% | 5.2% | 8.6% | Risky unless high conviction |

**LOW levels >> HIGH levels** for follow-through.

---

## 7. Day of Week

| Day | CONF% | Signals | Tip |
|-----|-------|---------|-----|
| **Mon** | **56%** | 250 | Best day — trade confidently |
| Thu | 41% | 395 | Average |
| Tue | 39% | 406 | Average |
| Wed | 35% | 419 | Below average |
| Fri | 34% | 371 | Worst — be selective |

---

## 8. Execution Guide

### Hold Time
- **Optimal: 30 minutes minimum** — GOOD signals still climbing at minute 30 (avg +0.57 ATR, 100% positive)
- GOOD signals peak at **minute 23** on average; BAD signals peak at **minute 3.5**
- Consider extending to 60 min for ✓★ signals (research: momentum persists 30-120 min)

### Stop Loss (visible as SL lines on chart after CONF ✓/✓★)
- **0.15 ATR (solid red line)** — hard stop. BAD signals hit this by minute 5. Lines last 30 minutes.
- **0.10 ATR (dashed orange line)** — early warning. If here at minute 2, likely BAD. Lines last 30 minutes.
- **At 5 minutes:** if positive, switch to 0.25 ATR trailing stop from high
- **85% of GOOD signals never reverse below -0.10 ATR** — once they go, they go
- SL lines fire at CONF time (not breakout time) — drawn from the confirming breakout's close price

### Runner Score ①-⑤ (on labels)
| Score | Meaning | Data |
|-------|---------|------|
| ⑤ | All factors aligned | +0.071 ATR avg, 1.4% BAD |
| ④ | Strong setup | +0.050 ATR avg, 2.3% BAD |
| ③ | Decent setup | +0.047 ATR avg, 2.4% BAD |
| ①② | Weak — be selective | Higher BAD rate |

Factors: VWAP aligned, vol ≥5x, time 9:30-10, level quality (LOW for bear, confluence for bull), not D-tier symbol (AMD/MSFT/GLD/TSM)

### QBS/MC Signals (v2.8)
New standalone signal type based on pre-move volume ramp fingerprint (no key level needed):

| Signal | Meaning | Color | Data |
|--------|---------|-------|------|
| **🔇 QBS** | Volume drying (<0.5x) before big bar — "quiet before storm" | Cyan/teal | 68% runner, 3% fakeout |
| **🔊 MC** | Volume surging (>5x) before big bar — "momentum cascade" | Orange | 64% runner, 3% fakeout, best MFE 2.66 |
| **⚡** | Big move — bar range ≥ 2x signal-TF ATR | Size upgrade | 65% runner across 13 symbols |
| **⚠** | Body ≥80% — fakeout warning | Appended text | 55% fakeouts vs 36% runners — INVERSE |
| **Gray ?** | Moderate vol ramp (1-2x) — trap bucket | Dimmed | Worst bucket: 56% runner, 7% fakeout |

**Trading QBS/MC:** These fire once per direction per session with CONF tracking. Treat like reversal signals — ADX + Body filter applied. Best in morning 9:30-10 window.

### VWAP Exit Alert
After CONF ✓/✓★, the indicator tracks VWAP. When price crosses VWAP against your position, an alert fires. This is your **momentum death signal** — consider closing.

### Sizing
| Signal State | Size |
|-------------|------|
| CONF ✓★ (gold) | Full size |
| CONF ✓ (solid green/red, white text) | Large size (0% BAD) |
| Score ④-⑤, unconfirmed | Standard size |
| Score ①-③, unconfirmed | Small or skip |
| Dimmed (gray ?) | Do not trade |
| CONF ✗ | Exit |

---

## 9. Pine Log Fields (for analysis)

When Debug Log is ON, each signal logs:
```
[KLB] 9:40 ▲ BRK PM H vol=5.5x pos=^94 vwap=above ema=bull rs=+0.3% adx=28 body=72% O... ATR=...
```

| Field | Meaning | Good values |
|-------|---------|-------------|
| vol | Volume ratio vs baseline | 2-5x |
| pos | Close position in range | ^80+ (bull), v80+ (bear) |
| vwap | Price vs VWAP | "above" for longs |
| ema | 5m EMA trend direction | Matches signal direction |
| rs | Stock vs SPY % change | Positive for longs |
| adx | 5m ADX value | >20 (trending) |
| body | Candle body % of range | >50% |

---

## 10. Quick Settings Reference

| Setting | Default | Change when |
|---------|---------|-------------|
| Signal TF | 5m | Don't change |
| VWAP Filter | ON | Keep ON always |
| EMA Filter | ON | OFF for early trend reversals |
| RS Filter | ON | Auto-bypasses SPY/QQQ/GLD/SLV |
| ADX Filter | ON | OFF for range breakouts |
| Candle Body Filter | ON | OFF for gap opens |
| Filter Mode | Suppress | Switch to Dim to see filtered signals |
| Confirmation | ON | Keep ON always |
| Chop Warning | ON | Redundant when ADX filter is ON |
| **VWAP Line** | **ON** | Orange line on chart. OFF if you have another VWAP |
| **SL Lines** | **ON** | 30 min after CONF ✓/✓★. OFF if chart feels cluttered |
| **Runner Score** | **ON** | OFF if you prefer clean labels |
