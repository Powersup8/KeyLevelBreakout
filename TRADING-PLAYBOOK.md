# KeyLevelBreakout Trading Playbook

> Based on 3,753 signals, 13 symbols, 24 trading days (Jan 20 - Feb 27 2026)

---

## 1. TAKE These Trades

| Setup | Win% | Loss% | How to spot |
|-------|------|--------|-------------|
| **BRK + CONF ✓ + >5x vol** | 54% | 0% | Green label, ✓ appended, fat volume bar |
| **Any CONF ✓** | 53% | 0% | ✓ on label = price immediately followed through |
| **Week H/L breakout** | 33-38% | 3% | Rare (1/day avg) but huge moves when they work |
| **Reversal at Yest H/L** | 30% | 7% | ~ label at yesterday's level, with-trend |

**The golden rule:** CONF ✓ has literally 0% BAD rate. If you see ✓, that's your highest conviction trade.

---

## 2. AVOID These

| Trap | Why | Data |
|------|-----|------|
| **Anything after 11:00** | Follow-through drops to near zero | 0% GOOD in 11-13, 7% in 13-16 |
| **Reclaims (~~)** | Weakest signal type by far | 8% GOOD, 8% BAD — coin flip minus fees |
| **CONF ✗ breakouts** | If it doesn't immediately run, it won't | 12% GOOD vs 53% for CONF ✓ |
| **Low volume (<2x) signals** | No institutional conviction | 32% CONF rate vs 60% for 10x+ volume |
| **3+ consecutive CONF ✗** | Chop day developing | Early CONF fail rate 28% on chop days vs 51% on normal days |

**The chop rule:** If your first 2-3 signals all fail CONF, stop trading. It's a chop day (18% of all days).

---

## 3. Biggest Learnings (Assumptions We Had WRONG)

**❌ "Trade cautiously at open, it's unreliable"**
WRONG. Morning 9:30-10:00 has the BEST CONF rate (48% vs 30% rest of day). It's where volume and conviction are highest. Trade aggressively here, manage size for higher MAE risk.

**❌ "Weekly levels are the strongest"**
MISLEADING. Week L has the worst CONF rate (17%) but the best follow-through when it works (33% GOOD). Yest H (44%) and PM L (43%) are actually the most reliable levels for confirmation. Weekly = selective high-conviction only.

**❌ "Confirmation can come slowly"**
WRONG. 100% of CONF passes are auto-promotes (new breakout displaces old). Zero signals ever confirmed via waiting. If price doesn't immediately break through, it ALWAYS fails. The CONF system is binary: instant momentum or nothing.

---

## 4. Decision Flowchart

```
Signal fires → Check time
  ├─ Before 11:00? → Check CONF
  │   ├─ CONF ✓? → TRADE IT (53% win, 0% loss)
  │   ├─ CONF ✗? → Watch for reclaim (40% chance) as counter-trade
  │   └─ Waiting? → Volume >5x? → lean in. Volume <2x? → skip.
  └─ After 11:00? → SKIP (unless extraordinary setup)

Chop check: 2-3 CONF ✗ in a row at open → scale back or stop
```

---

## 5. Level Cheat Sheet

| Level | CONF Rate | Follow-through | Best for |
|-------|-----------|----------------|----------|
| **Yest H** | 44% | 31% GOOD | Most reliable all-around |
| **PM L** | 43% | 28% GOOD | High frequency + quality |
| **ORB L** | 41% | 38% GOOD | Strong follow-through |
| **ORB H** | 38% | 19% GOOD | Most signals but mediocre |
| **Week H** | 34% | 39% GOOD | Selective — big when it works |
| **Week L** | 17% | 33% GOOD | Worst CONF, best follow-through |

**Focus on:** Yest H/L and PM L for consistency. Week H/L for big swings only.

---

## 6. Best Symbols

| Tier | Symbols | CONF Rate |
|------|---------|-----------|
| **A-tier** | SPY (51%), QQQ (49%), TSLA (46%) | Trade these first |
| **B-tier** | NVDA (44%), META (42%), MSFT (41%) | Solid |
| **C-tier** | AMD (31%), GLD (30%) | More chop, be selective |

---

## 7. What to Do NEXT

### For trading NOW:
1. Focus 9:30-10:00 window — it's your highest edge
2. Wait for CONF ✓ before committing size
3. After 2-3 CONF fails → stop or reduce size
4. Ignore reclaims (~~) unless you have specific thesis
5. After CONF ✗ → watch for reclaim counter-trade (40% probability)

### For the indicator (v2.4):
1. **Make CONF ✓ visible** — it's the gold standard but currently looks like every other breakout
2. **Add VWAP to logs** — can't validate the VWAP filter without it
3. **Dim afternoon signals** — they're noise, reduce visual clutter
