# TradingView Indicators

Pine Script v6 indicators for US stocks (NYSE/NASDAQ) on 5-minute charts.

## KeyLevelBreakout v2.8 — Documentation

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
