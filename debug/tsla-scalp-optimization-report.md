# TSLA Open Scalp — Optimization Report
*Generated: 2026-03-19 01:10 | 61 experiments | 117 min runtime*

## Top 10 Configurations (by validation score)

| Rank | Config | Val Trades | Val Win% | Val Avg | Val Score | All Sharpe | All Worst% |
|---|---|---|---|---|---|---|---|
| 1 | ORB_WIDTH=3.5 | 59 | 23.7% | $0.02 | 0.5 | 0.73 | 1.6% |
| 2 | FALLBACK_SL=1.25 | 59 | 20.3% | $0.0 | 0.1 | 1.95 | 0.0% |
| 3 | FALLBACK_SL=1.0 | 59 | 16.9% | $-0.0 | -0.1 | 2.19 | 0.0% |
| 4 | HOLD=3bars | 59 | 23.7% | $-0.11 | -3.0 | 1.73 | 0.0% |
| 5 | HOLD=15bars | 59 | 18.6% | $-0.15 | -3.4 | 1.44 | 0.0% |
| 6 | COMBO: hold=15 sl=orb_low | 59 | 18.6% | $-0.15 | -3.4 | 1.44 | 0.0% |
| 7 | COMBO: hold=15 sl=orb_low_025 | 59 | 18.6% | $-0.18 | -3.9 | 1.23 | 0.0% |
| 8 | SL=fixed_2 | 59 | 22.0% | $-0.2 | -5.3 | 1.0 | 0.0% |
| 9 | FALLBACK_SL=3.0 | 59 | 33.9% | $-0.13 | -5.3 | 1.28 | 0.8% |
| 10 | PATH_EFF=on_wide | 52 | 21.2% | $-0.25 | -5.4 | 1.57 | 0.0% |

## Phase: ORB_WIDTH

| Config | All n | All Win% | All Avg | All Score | All Sharpe | All Worst% |
|---|---|---|---|---|---|---|
| ORB_WIDTH=0 | 122 | 25.4% | $0.26 | 16.4 | 1.21 | 0.0% |
| ORB_WIDTH=0.5 | 122 | 25.4% | $0.26 | 16.4 | 1.21 | 0.0% |
| ORB_WIDTH=1.0 | 122 | 25.4% | $0.26 | 16.4 | 1.21 | 0.0% |
| ORB_WIDTH=1.5 | 122 | 25.4% | $0.26 | 16.4 | 1.21 | 0.0% |
| ORB_WIDTH=2.0 | 122 | 25.4% | $0.26 | 16.4 | 1.21 | 0.0% |
| ORB_WIDTH=2.5 | 122 | 25.4% | $0.18 | 11.3 | 0.81 | 0.8% |
| ORB_WIDTH=3.5 | 122 | 26.2% | $0.17 | 11.2 | 0.73 | 1.6% |
| ORB_WIDTH=3.0 | 122 | 24.6% | $0.04 | 2.2 | 0.16 | 1.6% |

## Phase: HOLD

| Config | All n | All Win% | All Avg | All Score | All Sharpe | All Worst% |
|---|---|---|---|---|---|---|
| HOLD=3bars | 122 | 28.7% | $0.34 | 23.7 | 1.73 | 0.0% |
| HOLD=15bars | 122 | 23.0% | $0.35 | 19.9 | 1.44 | 0.0% |
| HOLD=10bars | 122 | 25.4% | $0.26 | 16.4 | 1.21 | 0.0% |
| HOLD=8bars | 122 | 27.9% | $0.23 | 15.3 | 1.15 | 0.0% |
| HOLD=5bars | 122 | 27.9% | $0.21 | 14.1 | 1.09 | 0.0% |
| HOLD=12bars | 122 | 24.6% | $0.23 | 14.0 | 1.07 | 0.0% |
| HOLD=20bars | 122 | 23.0% | $0.22 | 12.1 | 0.7 | 1.6% |
| HOLD=25bars | 122 | 22.1% | $0.12 | 6.7 | 0.36 | 2.5% |
| HOLD=30bars | 122 | 22.1% | $0.12 | 6.7 | 0.36 | 2.5% |
| HOLD=45bars | 122 | 22.1% | $0.12 | 6.7 | 0.36 | 2.5% |
| HOLD=60bars | 122 | 22.1% | $0.12 | 6.7 | 0.36 | 2.5% |
| HOLD=90bars | 122 | 22.1% | $0.12 | 6.7 | 0.36 | 2.5% |
| HOLD=120bars | 122 | 22.1% | $0.12 | 6.7 | 0.36 | 2.5% |
| HOLD=180bars | 122 | 22.1% | $0.12 | 6.7 | 0.36 | 2.5% |
| HOLD=EOD | 122 | 22.1% | $0.12 | 6.7 | 0.36 | 2.5% |

## Phase: SL

| Config | All n | All Win% | All Avg | All Score | All Sharpe | All Worst% |
|---|---|---|---|---|---|---|
| SL=orb_low | 122 | 25.4% | $0.26 | 16.4 | 1.21 | 0.0% |
| SL=fixed_2 | 122 | 27.0% | $0.22 | 14.4 | 1.0 | 0.0% |
| SL=orb_low_025 | 122 | 25.4% | $0.22 | 13.5 | 1.0 | 0.0% |
| SL=orb_low_050 | 122 | 26.2% | $0.19 | 12.4 | 0.88 | 0.0% |

## Phase: FALLBACK_SL

| Config | All n | All Win% | All Avg | All Score | All Sharpe | All Worst% |
|---|---|---|---|---|---|---|
| FALLBACK_SL=3.0 | 122 | 36.9% | $0.34 | 30.3 | 1.28 | 0.8% |
| FALLBACK_SL=1.25 | 122 | 24.6% | $0.41 | 24.7 | 1.95 | 0.0% |
| FALLBACK_SL=1.0 | 122 | 22.1% | $0.44 | 23.8 | 2.19 | 0.0% |
| FALLBACK_SL=2.0 | 122 | 29.5% | $0.29 | 21.1 | 1.24 | 0.0% |
| FALLBACK_SL=1.5 | 122 | 25.4% | $0.26 | 16.4 | 1.21 | 0.0% |
| FALLBACK_SL=2.5 | 122 | 31.1% | $0.14 | 10.8 | 0.56 | 0.8% |
| FALLBACK_SL=1.75 | 122 | 25.4% | $0.13 | 8.2 | 0.6 | 0.0% |

## Phase: ACCEL

| Config | All n | All Win% | All Avg | All Score | All Sharpe | All Worst% |
|---|---|---|---|---|---|---|
| ACCEL=4m | 122 | 25.4% | $0.27 | 16.6 | 1.23 | 0.0% |
| ACCEL=2m (baseline) | 122 | 25.4% | $0.26 | 16.4 | 1.21 | 0.0% |

## Phase: PATH_EFF

| Config | All n | All Win% | All Avg | All Score | All Sharpe | All Worst% |
|---|---|---|---|---|---|---|
| PATH_EFF=on_wide | 101 | 27.7% | $0.35 | 19.6 | 1.57 | 0.0% |
| PATH_EFF=on | 77 | 27.3% | $0.28 | 12.0 | 1.23 | 0.0% |

## Phase: FAKEOUT

| Config | All n | All Win% | All Avg | All Score | All Sharpe | All Worst% |
|---|---|---|---|---|---|---|
| FAKEOUT=new_low_required (v1.2c) | 122 | 25.4% | $0.26 | 16.4 | 1.21 | 0.0% |
| FAKEOUT=any_updn (v1.1k) | 122 | 25.4% | $0.26 | 16.4 | 1.21 | 0.0% |

## Phase: COMBO

| Config | All n | All Win% | All Avg | All Score | All Sharpe | All Worst% |
|---|---|---|---|---|---|---|
| COMBO: hold=15 sl=orb_low | 122 | 23.0% | $0.35 | 19.9 | 1.44 | 0.0% |
| COMBO: hold=15 sl=orb_low_025 | 122 | 23.0% | $0.3 | 17.0 | 1.23 | 0.0% |
| COMBO: hold=10 sl=orb_low | 122 | 25.4% | $0.26 | 16.4 | 1.21 | 0.0% |
| COMBO: hold=10 sl=orb_low_025 | 122 | 25.4% | $0.22 | 13.5 | 1.0 | 0.0% |
| COMBO: hold=20 sl=orb_low | 122 | 23.0% | $0.22 | 12.1 | 0.7 | 1.6% |
| COMBO: hold=15 path_eff=on | 77 | 23.4% | $0.3 | 10.8 | 1.15 | 0.0% |
| COMBO: hold=20 sl=orb_low_025 | 122 | 23.0% | $0.18 | 9.9 | 0.57 | 1.6% |
| COMBO: hold=30 sl=orb_low | 122 | 22.1% | $0.12 | 6.7 | 0.36 | 2.5% |
| COMBO: hold=45 sl=orb_low | 122 | 22.1% | $0.12 | 6.7 | 0.36 | 2.5% |
| COMBO: hold=60 sl=orb_low | 122 | 22.1% | $0.12 | 6.7 | 0.36 | 2.5% |
| COMBO: hold=EOD sl=orb_low | 122 | 22.1% | $0.12 | 6.7 | 0.36 | 2.5% |
| COMBO: hold=30 sl=orb_low_025 | 122 | 22.1% | $0.09 | 4.7 | 0.25 | 2.5% |
| COMBO: hold=45 sl=orb_low_025 | 122 | 22.1% | $0.09 | 4.7 | 0.25 | 2.5% |
| COMBO: hold=60 sl=orb_low_025 | 122 | 22.1% | $0.09 | 4.7 | 0.25 | 2.5% |
| COMBO: hold=EOD sl=orb_low_025 | 122 | 22.1% | $0.09 | 4.7 | 0.25 | 2.5% |
| COMBO: hold=20 path_eff=on | 77 | 23.4% | $0.03 | 1.1 | 0.11 | 1.3% |
| COMBO: hold=30 path_eff=on | 77 | 22.1% | $-0.03 | -1.0 | -0.08 | 2.6% |
| COMBO: hold=45 path_eff=on | 77 | 22.1% | $-0.03 | -1.0 | -0.08 | 2.6% |
| COMBO: hold=60 path_eff=on | 77 | 22.1% | $-0.03 | -1.0 | -0.08 | 2.6% |
| COMBO: hold=EOD path_eff=on | 77 | 22.1% | $-0.03 | -1.0 | -0.08 | 2.6% |

## Best Configuration: ORB_WIDTH=3.5

```json
{
  "min_orb_width": 3.5
}
```

## Recommendations

*(Based on validation performance — configs that generalize beyond training data)*

- **ORB_WIDTH:** ORB_WIDTH=3.5 (val_score=0.5, all_sharpe=0.73)
- **HOLD:** HOLD=3bars (val_score=-3.0, all_sharpe=1.73)
- **SL:** SL=fixed_2 (val_score=-5.3, all_sharpe=1.0)
- **FALLBACK_SL:** FALLBACK_SL=1.25 (val_score=0.1, all_sharpe=1.95)
- **ACCEL:** ACCEL=2m (baseline) (val_score=-5.8, all_sharpe=1.21)
- **PATH_EFF:** PATH_EFF=on_wide (val_score=-5.4, all_sharpe=1.57)
- **FAKEOUT:** FAKEOUT=new_low_required (v1.2c) (val_score=-5.8, all_sharpe=1.21)
- **COMBO:** COMBO: hold=15 sl=orb_low (val_score=-3.4, all_sharpe=1.44)