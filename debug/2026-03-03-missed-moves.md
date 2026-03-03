# 2026-03-03 Missed Moves Analysis

Analysis of price windows where significant moves occurred but no signals fired.

## Summary

| Symbol | Window | Dir | Move ($) | Move (ATR) | Range (ATR) | VWAP Cross |
|--------|--------|-----|----------|------------|-------------|------------|
| SPY | 10:30-13:40 | UP | +11.24 | 11.82x | 12.72x | Yes |
| QQQ | 10:30-13:40 | UP | +10.75 | 11.07x | 11.88x | Yes |
| NVDA | 10:55-11:05 | UP | +2.58 | 5.85x | 7.01x | Yes |
| AAPL | 10:10-12:30 | DOWN | -3.63 | 6.12x | 7.62x | Yes |
| AAPL | 12:30-14:40 | UP | +2.49 | 4.20x | 7.61x | Yes |
| TSLA | 10:44-11:25 | UP | +6.30 | 6.33x | 7.95x | Yes |

## Detailed Analysis

### SPY 10:30-13:40 (UP)

- **Open:** $669.85 -> **Close:** $681.09 (UP $11.24)
- **High:** $681.87 | **Low:** $669.78
- **Total range:** $12.09 = 12.72x ATR(14)
- **Net move:** $11.24 = 11.82x ATR(14)
- **ATR(14) for the day:** $0.95
- **Extreme point:** $681.87 at 13:40
- **VWAP at window start:** $672.69 | **end:** $674.60
- **VWAP crossed during window:** Yes
- **Round levels crossed:** $670, $675, $680
- **Avg volume vs day avg:** 0.87x
- **Bars:** 39 (5m), 191 (1m)

### QQQ 10:30-13:40 (UP)

- **Open:** $592.03 -> **Close:** $602.78 (UP $10.75)
- **High:** $603.50 | **Low:** $591.96
- **Total range:** $11.54 = 11.88x ATR(14)
- **Net move:** $10.75 = 11.07x ATR(14)
- **ATR(14) for the day:** $0.97
- **Extreme point:** $603.50 at 13:40
- **VWAP at window start:** $595.22 | **end:** $597.14
- **VWAP crossed during window:** Yes
- **Round levels crossed:** $595, $600
- **Avg volume vs day avg:** 1.01x
- **Bars:** 39 (5m), 191 (1m)

### NVDA 10:55-11:05 (UP)

- **Open:** $176.97 -> **Close:** $179.55 (UP $2.58)
- **High:** $180.01 | **Low:** $176.92
- **Total range:** $3.09 = 7.01x ATR(14)
- **Net move:** $2.58 = 5.85x ATR(14)
- **ATR(14) for the day:** $0.44
- **Extreme point:** $180.01 at 11:05
- **VWAP at window start:** $178.61 | **end:** $178.67
- **VWAP crossed during window:** Yes
- **Round levels crossed:** $180
- **Avg volume vs day avg:** 1.72x
- **Bars:** 3 (5m), 11 (1m)

### AAPL 10:10-12:30 (DOWN)

- **Open:** $263.90 -> **Close:** $260.27 (DOWN $3.63)
- **High:** $264.77 | **Low:** $260.25
- **Total range:** $4.52 = 7.62x ATR(14)
- **Net move:** $3.63 = 6.12x ATR(14)
- **ATR(14) for the day:** $0.59
- **Extreme point:** $260.25 at 12:30
- **VWAP at window start:** $263.12 | **end:** $262.86
- **VWAP crossed during window:** Yes
- **Avg volume vs day avg:** 0.96x
- **Bars:** 29 (5m), 141 (1m)

### AAPL 12:30-14:40 (UP)

- **Open:** $261.80 -> **Close:** $264.29 (UP $2.49)
- **High:** $264.64 | **Low:** $260.13
- **Total range:** $4.51 = 7.61x ATR(14)
- **Net move:** $2.49 = 4.20x ATR(14)
- **ATR(14) for the day:** $0.59
- **Extreme point:** $264.64 at 14:35
- **VWAP at window start:** $262.86 | **end:** $262.69
- **VWAP crossed during window:** Yes
- **Avg volume vs day avg:** 0.79x
- **Bars:** 27 (5m), 131 (1m)

### TSLA 10:44-11:25 (UP)

- **Open:** $386.24 -> **Close:** $392.54 (UP $6.30)
- **High:** $393.56 | **Low:** $385.65
- **Total range:** $7.91 = 7.95x ATR(14)
- **Net move:** $6.30 = 6.33x ATR(14)
- **ATR(14) for the day:** $0.99
- **Extreme point:** $393.56 at 11:25
- **VWAP at window start:** $390.13 | **end:** $390.16
- **VWAP crossed during window:** Yes
- **Round levels crossed:** $390
- **Avg volume vs day avg:** 1.34x
- **Bars:** 9 (5m), 42 (1m)

## Why Signals May Not Have Fired

### SPY 10:30-13:40

At 10:30:
- Price: $671.03
- VWAP: $672.69 (price below VWAP)
- Session open: $675.05
- ORB (30m): $671.95 - $676.44
- Max single 5m bar range: $2.10 (2.21x ATR)
- Avg 5m bar range: $1.20 (1.27x ATR)
- **Move type: IMPULSIVE** — at least one bar hit 2x+ ATR. Should have triggered big-move detection.
- Directional consistency: 64% (25 up / 14 down bars)

### QQQ 10:30-13:40

At 10:30:
- Price: $593.17
- VWAP: $595.22 (price below VWAP)
- Session open: $596.33
- ORB (30m): $595.00 - $598.56
- Max single 5m bar range: $2.35 (2.42x ATR)
- Avg 5m bar range: $1.30 (1.34x ATR)
- **Move type: IMPULSIVE** — at least one bar hit 2x+ ATR. Should have triggered big-move detection.
- Directional consistency: 69% (27 up / 12 down bars)

### NVDA 10:55-11:05

At 10:55:
- Price: $177.35
- VWAP: $178.61 (price below VWAP)
- Session open: $178.49
- ORB (30m): $178.04 - $180.53
- Max single 5m bar range: $1.53 (3.47x ATR)
- Avg 5m bar range: $1.07 (2.42x ATR)
- **Move type: IMPULSIVE** — at least one bar hit 2x+ ATR. Should have triggered big-move detection.
- Directional consistency: 100% (3 up / 0 down bars)

### AAPL 10:10-12:30

At 10:10:
- Price: $264.13
- VWAP: $263.12 (price above VWAP)
- Session open: $263.48
- ORB (30m): $261.21 - $265.56
- Max single 5m bar range: $1.56 (2.63x ATR)
- Avg 5m bar range: $0.74 (1.24x ATR)
- **Move type: IMPULSIVE** — at least one bar hit 2x+ ATR. Should have triggered big-move detection.
- Directional consistency: 62% (11 up / 18 down bars)

### AAPL 12:30-14:40

At 12:30:
- Price: $260.27
- VWAP: $262.86 (price below VWAP)
- EMA9: $261.93 | EMA21: $262.32 (bearish alignment)
- Session open: $263.48
- ORB (30m): $261.21 - $265.56
- Max single 5m bar range: $1.56 (2.63x ATR)
- Avg 5m bar range: $0.59 (0.99x ATR)
- **Move type: IMPULSIVE** — at least one bar hit 2x+ ATR. Should have triggered big-move detection.
- Directional consistency: 59% (16 up / 11 down bars)

### TSLA 10:44-11:25

At 10:44:
- Price: $386.25
- VWAP: $390.29 (price below VWAP)
- Session open: $395.16
- ORB (30m): $389.65 - $396.34
- Max single 5m bar range: $2.71 (2.72x ATR)
- Avg 5m bar range: $1.63 (1.64x ATR)
- **Move type: IMPULSIVE** — at least one bar hit 2x+ ATR. Should have triggered big-move detection.
- Directional consistency: 67% (6 up / 3 down bars)

## Key Takeaways

### Common Patterns in These Missed Moves

- **Average move size:** 7.57x ATR (range: 4.20 - 11.82)
- **Moves > 1.5x ATR:** 6/6
- **VWAP crossings:** 6/6 windows had VWAP cross

### Possible Reasons for No Signals

1. **Grinding/slow drift moves** — if no single bar triggers breakout detection (needs 2x ATR bar), gradual trends are invisible
2. **Already past key levels** — if levels were broken before the window, no new breakout to detect
3. **Mid-day timing** — many windows start after 10:30, which may get afternoon dimming
4. **VWAP zone already passed** — once-per-session VWAP signals may have already fired earlier
5. **Evidence stack filtering** — EMA/ADX/RS filters in suppress mode could block signals during trend transitions
