# KLB Signal Investigation — All Signals

*Generated: 2026-03-12 20:04 ET*

## 1. Coverage Summary

| Field | Value |
|-------|-------|
| Date range | 2024-07-01 – 2026-03-11 |
| Symbols | AAPL, AMD, AMZN, GLD, GOOGL, META, MSFT, MU, NFLX, NVDA, QQQ, SLV, SPY, TSLA, TSM, XLE |
| Total signal entries | 22414 |
| Signals with IB outcome | 22401 |
| Overall win rate | 24.3% |
| 5m CHECK entries | 3698 |
| BAIL triggered | 1325 |
| HOLD triggered | 5042 |

## 2. Performance by Signal Type

| sig_type   |     N |   Win% |   AvgMFE |   AvgMAE |   MFE/MAE |
|:-----------|------:|-------:|---------:|---------:|----------:|
| BRK        |  3591 |   25.8 |    0.289 |    0.262 |      1.1  |
| FADE       |  2223 |   26.4 |    0.273 |    0.254 |      1.07 |
| QBS        |   553 |   25.9 |    0.277 |    0.289 |      0.96 |
| REV        | 12332 |   21.8 |    0.257 |    0.256 |      1    |
| RNG        |  3702 |   30.1 |    0.352 |    0.337 |      1.04 |

## 3. Performance by Symbol

| symbol   |    N |   Win% |   AvgMFE |   AvgMAE |   MFE/MAE |
|:---------|-----:|-------:|---------:|---------:|----------:|
| XLE      | 1925 |   26   |    0.268 |    0.265 |      1.01 |
| MU       | 1582 |   25.4 |    0.288 |    0.278 |      1.04 |
| SPY      | 1270 |   25.4 |    0.296 |    0.268 |      1.1  |
| NVDA     |  906 |   24.8 |    0.28  |    0.273 |      1.02 |
| QQQ      | 1199 |   24.6 |    0.29  |    0.277 |      1.04 |
| META     | 1258 |   24.5 |    0.277 |    0.269 |      1.03 |
| TSLA     | 1220 |   24.3 |    0.264 |    0.249 |      1.06 |
| GLD      | 1582 |   24.2 |    0.314 |    0.293 |      1.07 |
| TSM      | 1184 |   24.2 |    0.295 |    0.285 |      1.03 |
| AMD      | 1757 |   24   |    0.271 |    0.264 |      1.03 |
| SLV      | 1345 |   24   |    0.318 |    0.302 |      1.05 |
| AMZN     | 1230 |   23.9 |    0.267 |    0.287 |      0.93 |
| MSFT     | 1563 |   23.9 |    0.265 |    0.257 |      1.03 |
| NFLX     | 1621 |   23.6 |    0.265 |    0.243 |      1.09 |
| GOOGL    | 1169 |   23.4 |    0.276 |    0.283 |      0.97 |
| AAPL     | 1590 |   23   |    0.252 |    0.26  |      0.97 |

## 4. Performance by Time of Day

| tod       |     N |   Win% |   AvgMFE |   AvgMAE |   MFE/MAE |
|:----------|------:|-------:|---------:|---------:|----------:|
| morning   | 14396 |   28.3 |    0.322 |    0.313 |      1.03 |
| midday    |  4742 |   20   |    0.221 |    0.207 |      1.07 |
| afternoon |  3263 |   13.2 |    0.179 |    0.182 |      0.98 |

## 5. Performance by Direction

| direction   |     N |   Win% |   AvgMFE |   AvgMAE |   MFE/MAE |
|:------------|------:|-------:|---------:|---------:|----------:|
| bear        | 13432 |   24.5 |    0.287 |    0.262 |      1.1  |
| bull        |  8969 |   24.1 |    0.269 |    0.285 |      0.94 |

## 6. BAIL vs HOLD Analysis

| Outcome | N | Win% | AvgMFE | AvgMAE |
|---------|---|------|--------|--------|
| BAIL | 1325 | 8.5% | 0.202 | 0.417 |
| HOLD | 5042 | 32.0% | 0.332 | 0.241 |
| No check | 16034 | 23.2% | 0.270 | 0.269 |

**Note:** HOLD signals had higher MFE — BAIL correctly screens out weak entries.

## 7. Top 10 Best Signals (Highest MFE)

| symbol   | date       | time_str   | sig_type   | direction   | level_info          |   mfe_atr |   mae_atr | win   | bail_action   |   atr_log |
|:---------|:-----------|:-----------|:-----------|:------------|:--------------------|----------:|----------:|:------|:--------------|----------:|
| GLD      | 2026-01-29 | 10:05      | RNG        | bear        |                     |     4.691 |     0.166 | False | HOLD          |     nan   |
| GLD      | 2026-01-29 | 10:05      | BRK        | bear        | PM L                |     4.691 |     0.166 | False | HOLD          |       2.6 |
| GLD      | 2026-01-29 | 10:05      | REV        | bear        | ~ VWAP              |     4.691 |     0.166 | False | HOLD          |       2.6 |
| GLD      | 2026-01-29 | 10:15      | REV        | bear        | ~ VWAP              |     3.733 |     0.038 | True  | HOLD          |       2.3 |
| SPY      | 2024-12-18 | 15:00      | BRK        | bear        | VW Band             |     3.621 |     0.161 | False | HOLD          |       1.5 |
| SLV      | 2026-01-29 | 09:30      | REV        | bear        | ~ Today O           |     3.034 |     0.178 | False |               |       1.1 |
| GLD      | 2026-01-29 | 10:20      | BRK        | bear        | VW Band             |     3.017 |     0.497 | False | HOLD          |       3.4 |
| GLD      | 2026-01-29 | 10:20      | REV        | bear        | ~ Yest H + ~ PD Cls |     3.017 |     0.497 | False | HOLD          |       3.4 |
| QQQ      | 2025-10-10 | 10:15      | REV        | bear        | ~> VWAP             |     2.885 |     0.124 | True  |               |       1.3 |
| SLV      | 2026-01-29 | 09:55      | REV        | bear        | ~> VWAP             |     2.881 |     0.171 | False |               |       1.2 |

## 8. Top 10 Worst Signals (Non-Winners, Highest MAE)

| symbol   | date       | time_str   | sig_type   | direction   | level_info         |   mfe_atr |   mae_atr | bail_action   | ema   | vwap   |   adx |
|:---------|:-----------|:-----------|:-----------|:------------|:-------------------|----------:|----------:|:--------------|:------|:-------|------:|
| GLD      | 2026-01-29 | 09:30      | RNG        | bull        |                    |     0.284 |     5.488 |               |       |        |   nan |
| AMZN     | 2025-10-30 | 15:45      | BRK        | bear        | ORB L              |     0.095 |     5.025 | HOLD          | bear  | below  |    23 |
| XLE      | 2025-04-07 | 09:45      | RNG        | bear        |                    |     0.149 |     3.25  |               |       |        |   nan |
| SLV      | 2026-01-29 | 09:40      | REV        | bull        | ~ VWAP             |     0.03  |     3.16  |               | bull  | above  |    24 |
| AAPL     | 2025-04-07 | 09:45      | REV        | bear        | ~ VWAP             |     0.135 |     3.066 |               | bear  | below  |    22 |
| AAPL     | 2025-04-07 | 09:30      | RNG        | bear        |                    |     0.321 |     3.05  |               |       |        |   nan |
| AMZN     | 2026-01-02 | 09:45      | RNG        | bull        |                    |     0.201 |     2.991 |               |       |        |   nan |
| AMZN     | 2026-01-02 | 09:45      | REV        | bull        | ~ VWAP             |     0.201 |     2.991 |               | bull  | above  |    23 |
| QQQ      | 2025-10-10 | 10:50      | FADE       | bull        | 612.13             |     0.005 |     2.986 |               |       |        |   nan |
| SPY      | 2025-04-09 | 12:00      | REV        | bear        | ~> VWAP + ~ PD Cls |     0.088 |     2.93  |               | bull  | below  |    26 |

## 9. Failure Pattern Analysis

Total non-winners: 16949 / 22401

### By Symbol
| symbol   |    0 |
|:---------|-----:|
| XLE      | 1425 |
| AMD      | 1335 |
| NFLX     | 1239 |
| AAPL     | 1225 |
| GLD      | 1199 |
| MSFT     | 1190 |
| MU       | 1180 |
| SLV      | 1022 |
| META     |  950 |
| SPY      |  947 |
| AMZN     |  936 |
| TSLA     |  923 |
| QQQ      |  904 |
| TSM      |  898 |
| GOOGL    |  895 |
| NVDA     |  681 |

### By Time of Day
| tod       |     0 |
|:----------|------:|
| afternoon |  2833 |
| midday    |  3793 |
| morning   | 10323 |

### By Signal Type
| sig_type   |    0 |
|:-----------|-----:|
| REV        | 9647 |
| BRK        | 2666 |
| RNG        | 2589 |
| FADE       | 1637 |
| QBS        |  410 |

### EMA Context in Failures (where available)
| ema   |   count |
|:------|--------:|
| bear  |    7516 |
| bull  |    4996 |

### VWAP Context in Failures (where available)
| vwap   |   count |
|:-------|--------:|
| below  |    8089 |
| above  |    4423 |

### BAIL Regret: Signals that BAILed but MFE > 0.5 ATR

| symbol   | date       | time_str   | sig_type   | direction   | level_info    |   mfe_atr |   mae_atr |   pnl_at_check |
|:---------|:-----------|:-----------|:-----------|:------------|:--------------|----------:|----------:|---------------:|
| SLV      | 2026-01-30 | 12:15      | BRK        | bear        | VW Band       |     2.817 |     0.206 |          -0.2  |
| SLV      | 2026-01-30 | 12:20      | BRK        | bear        | Week L        |     2.669 |     0.355 |          -0.2  |
| TSM      | 2025-07-01 | 09:45      | RNG        | bear        |               |     1.333 |     0.291 |          -0.14 |
| TSM      | 2025-07-01 | 09:45      | FADE       | bear        | 227.08        |     1.333 |     0.291 |          -0.14 |
| TSM      | 2025-07-01 | 09:45      | REV        | bear        | ~ VWAP        |     1.333 |     0.291 |          -0.14 |
| TSM      | 2025-07-01 | 09:45      | BRK        | bear        | PM L          |     1.333 |     0.291 |          -0.14 |
| XLE      | 2025-10-07 | 09:30      | REV        | bear        | ~ VWAP        |     1.249 |     0.015 |          -0.14 |
| TSLA     | 2025-11-06 | 09:55      | FADE       | bear        | 460.12        |     1.247 |     0.04  |          -0.23 |
| MSFT     | 2026-01-29 | 09:35      | BRK        | bear        | PM L + Week L |     1.152 |     0.32  |          -0.18 |
| MSFT     | 2026-01-29 | 09:35      | REV        | bear        | ~ VWAP        |     1.152 |     0.32  |          -0.18 |

## 10. Signal Distribution (Symbol × Type)

| symbol   |   BRK |   FADE |   QBS |   REV |   RNG |
|:---------|------:|-------:|------:|------:|------:|
| AAPL     |   264 |    159 |    19 |   897 |   251 |
| AMD      |   332 |    148 |    33 |  1002 |   242 |
| AMZN     |   177 |    143 |    36 |   630 |   244 |
| GLD      |   230 |    150 |    25 |   998 |   179 |
| GOOGL    |   164 |    142 |    14 |   602 |   248 |
| META     |   171 |    152 |    48 |   632 |   255 |
| MSFT     |   290 |    131 |    33 |   847 |   262 |
| MU       |   256 |    132 |    70 |   896 |   228 |
| NFLX     |   333 |    149 |    38 |   845 |   257 |
| NVDA     |   179 |     91 |    18 |   393 |   228 |
| QQQ      |   190 |    141 |    34 |   652 |   185 |
| SLV      |   207 |    103 |    25 |   837 |   173 |
| SPY      |   209 |    146 |    11 |   702 |   204 |
| TSLA     |   188 |    143 |    16 |   664 |   211 |
| TSM      |   137 |    129 |    52 |   619 |   248 |
| XLE      |   264 |    165 |    83 |  1126 |   287 |

## 11. Date Coverage by Symbol

| symbol   | First      | Last       |   N_signals |
|:---------|:-----------|:-----------|------------:|
| AAPL     | 2024-12-02 | 2026-03-11 |        1590 |
| AMD      | 2024-12-02 | 2026-03-11 |        1757 |
| AMZN     | 2024-12-02 | 2026-03-11 |        1230 |
| GLD      | 2024-11-01 | 2026-03-11 |        1582 |
| GOOGL    | 2024-12-02 | 2026-03-11 |        1170 |
| META     | 2024-12-02 | 2026-03-11 |        1258 |
| MSFT     | 2024-12-02 | 2026-03-11 |        1563 |
| MU       | 2024-12-02 | 2026-03-11 |        1582 |
| NFLX     | 2024-12-02 | 2026-03-11 |        1622 |
| NVDA     | 2024-12-02 | 2026-03-11 |         909 |
| QQQ      | 2024-12-02 | 2026-03-11 |        1202 |
| SLV      | 2024-11-01 | 2026-03-11 |        1345 |
| SPY      | 2024-12-02 | 2026-03-11 |        1272 |
| TSLA     | 2024-12-03 | 2026-03-11 |        1222 |
| TSM      | 2024-12-02 | 2026-03-11 |        1185 |
| XLE      | 2024-07-01 | 2026-03-11 |        1925 |

## 12. QBS Context Deep Dive

QBS signals with outcome: 553, Win%: 25.9%

**QBS by EMA:**
| ema   |      win |   mfe_atr |   mae_atr |
|:------|---------:|----------:|----------:|
| bear  | 0.263889 |     0.288 |     0.31  |
| bull  | 0.256    |     0.3   |     0.303 |

**QBS by VWAP:**
| vwap   |      win |   mfe_atr |   mae_atr |
|:-------|---------:|----------:|----------:|
| above  | 0.298507 |     0.304 |     0.3   |
| below  | 0.222222 |     0.284 |     0.313 |

## 13. SPY Context in 5m CHECKS

SPY alignment at BAIL:
| spy_align   |   count |
|:------------|--------:|
| ~           |     459 |
| ✗           |     253 |

SPY alignment at HOLD:
| spy_align   |   count |
|:------------|--------:|
| ~           |    1653 |
| ✓           |    1211 |
| ✗           |     122 |

## 14. Key Findings

1. **Best signal type:** RNG — 30.1% win, MFE/MAE=1.04x
2. **Worst signal type:** REV — 21.8% win
3. **Best time slot:** morning — 28.3% win
4. **Worst time slot:** afternoon — 13.2% win
5. **Best symbol:** XLE — 26.0% win (N=1925)
6. **Worst symbol:** AAPL — 23.0% win (N=1590)
7. **Overall win rate:** 24.3% across 22401 signals

### Action Items

- [ ] Investigate worst signal type for suppression or filter tightening
- [ ] Investigate afternoon performance — consider time gate
- [ ] Review BAIL regret cases — if frequent, consider loosening BAIL threshold
- [ ] Check EMA/VWAP conflict pattern in failures for a new filter
- [ ] Symbol-specific: review worst performer for structural issues
