# TradingView Indicators

Pine Script v6 indicators for US stocks (NYSE/NASDAQ) on 5-minute charts.

## KeyLevelBreakout v3.5 — Documentation

| Doc | What's Inside |
|-----|---------------|
| [KLB_PLAYBOOK.md](KLB_PLAYBOOK.md) | Signal Catalog (best→worst), Time Windows, Avoid List, Decision Flowchart, Execution, Symbols |
| [KLB_Reference.md](KLB_Reference.md) | Setup, Signal Types, Label Anatomy, CONF System, Levels, Filters, Visuals, Alerts, Settings |
| [KLB_DESIGN-JOURNAL.md](KLB_DESIGN-JOURNAL.md) | The Idea, Data Foundation, Key Discoveries, Filter Validation, Evolution, Dead Ends |
| [KLB_TV.md](KLB_TV.md) | TradingView description (copy-paste for publishing) |

## All Indicators

| Indicator | File | Description |
|-----------|------|-------------|
| [Key Level Breakout](KLB_Reference.md) | `KeyLevelBreakout.pine` | Breakout, reversal, reclaim & retest signals at key intraday levels |
| [Key Level Scanner](KeyLevelScanner.md) | `KeyLevelScanner.pine` | Monitor up to 8 tickers for key level breakouts |
| [EMA Pullback](EMAPullback.md) | `EMAPullback.pine` | Pullback entries to 9 EMA after strong moves (Puts & Calls) |
| EMA Pullback Backtest | `EMAPullback_Backtest.pine` | Strategy version of EMA Pullback for TradingView Strategy Tester |
| [15m Fib Scalper](Fib15mScalper.md) | `Fib15mScalper.pine` | Liquidity candle reversal on 15m opening range (Fibonacci TP) |

See each indicator's documentation for full details on strategy logic, inputs, and setup.

## Changelog (recent)

| Version | Date | Summary |
|---------|------|---------|
| v3.5 | 2026-03-09 | Adaptive SL by time window (morning 0.08/0.10, midday 0.20/0.25, afternoon 0.10/0.15 ATR). Afternoon suppression toggle (`i_suppressAfternoon`, default OFF). Baseline: +0.117 ATR/signal with adaptive SL. |
| v3.4 | 2026-03-08 | Bull BRK at PD Last Hr High, ORB Low Reclaim midday, BAIL positive guard (+36 ATR), NVDA bear ★2x label, special day detection. |
| v3.3c/d | 2026-03-08 | Bull REV at HIGH levels suppressed (-1,212 ATR drain). NVDA bull REV suppressed (25.3% win). |
| v3.3/b | 2026-03-08 | Fingerprint-driven quality filters: quiet coil, exhaustion dim, level freshness, midday flat-EMA boost. |
| v3.2 | 2026-03-06 | HIGH levels → REV (magnets). EXREV bypass. FADE resurrection. 4 midday levels. |
