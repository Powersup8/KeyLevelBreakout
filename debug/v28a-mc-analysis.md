# v2.8a MC Opposing Pairs Analysis (2026-03-03)

## Problem
MC (Momentum Cascade) signals at market open fire both bull AND bear within 5-10 minutes on nearly every day. The once-per-direction-per-session guard then prevents MC from firing later when the real move happens.

**126 opposing pairs** found across SPY/QQQ/AMD/AAPL (Sep 2025 – Mar 2026).

## Key Finding: Neither Signal Is Predictive

First signal correct: 57/126 (45%)
Second signal correct: 69/126 (55%) — essentially a coin flip.

### By Symbol
| Symbol | 1st correct | 2nd correct |
|--------|-------------|-------------|
| AMD | 30% | **70%** |
| SPY | 44% | 56% |
| QQQ | 54% | 46% |
| AAPL | 55% | 45% |

## Signal Features: Indistinguishable

| Feature | Correct MC | Wrong MC | Gap |
|---------|-----------|----------|-----|
| Ramp | 35.1x | 35.1x | 0% |
| Volume | 8.6x | 9.5x | -9% |
| Range ATR | 3.3 | 3.4 | -3% |
| Body | 62% | 59% | +5% |
| ADX | 29.7 | 29.4 | +1% |
| Close pos | 80% | 80% | 0% |
| Reversal size | 1.68 | 1.61 | +4% |

**No feature at signal time can distinguish correct from wrong.**

## VWAP/EMA Alignment: INVERSE

| Alignment | Correct | Wrong |
|-----------|---------|-------|
| Dir matches VWAP | 71% | **81%** |
| Dir matches EMA | 46% | 52% |

The WRONG signal aligns with VWAP more — the "with-trend" MC at 9:35 is the trap.

## CONF: Weak Filter

| | CONF pass | CONF fail | None |
|--|-----------|-----------|------|
| Correct MC | 28% | 40% | 32% |
| Wrong MC | 20% | 40% | 40% |

Only 8% gap — not reliable enough.

## THE ANSWER: Wait Until 9:50

**Direction from 9:50→10:20 matches 30-min outcome: 79% (99/126)**

The opening auction (9:30-9:45) is genuinely random noise. By 9:50 the real direction has emerged.

### First vs Second Signal Profile
| | First MC | Second MC |
|--|----------|-----------|
| Volume | 12.4x | 5.7x |
| Range ATR | 4.0 | 2.7 |
| Ramp | 31.3x | 38.9x |

First signal = opening explosion (high vol, high range). Second = reversal (lower vol, higher ramp ratio).

## Recommended Fix

**Suppress MC signals before 9:50 ET.** This:
1. Prevents the once-per-session slot from being burned on noise
2. Preserves MC for the real momentum move (which 79% of the time aligns with 9:50 direction)
3. Simple to implement: add time check to MC raw conditions

## Data Files
- `debug/v28a-mc-opposing-pairs.csv` — 126 pairs with correct/wrong labels
- `debug/v28a-signals.csv` — all parsed signals
- `debug/v28a-signal-audit.md` — full audit report
- `debug/2026-03-03-missed-moves.md` — today's missed moves analysis
