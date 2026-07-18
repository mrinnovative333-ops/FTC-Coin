# FTC Trading Bot

**Status:** Paper / backtest mode only. No live trading without explicit user activation.  
**Owner:** John William Vincent (Mr Innovative)  
**Strategy:** News-driven OCO straddle with trailing stop loss.  
**Markets:** Forex (EUR/USD, GBP/USD, USD/JPY, XAU/USD).

---

## What This Bot Does

1. Loads economic events (NFP, CPI, FOMC, ECB, etc.) from a calendar source.
2. Before a high-impact event, places a **buy stop** and **sell stop** (OCO straddle) at a distance from current price.
3. When one order is filled, cancels the opposite order.
4. Trails the winning trade with a configurable trailing stop.
5. Logs every action and result to CSV and console.

---

## Safety Defaults

- **Mode:** `paper` by default. Live trading requires `MODE=live` in `.env` **and** a manual confirmation flag.
- **Max daily risk:** 2% of account
- **Max total drawdown:** 6%
- **Max spread:** 20 pips (skip trade if spread too wide)
- **No weekend / holiday trading**
- **No trading if ATR is too low** (choppy market)

---

## Quick Start

```bash
cd /c/Users/bidbu/trading/bot
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with your preferences
python src/main.py --mode backtest --days 90
```

---

## File Structure

```
bot/
  src/
    main.py              # entry point
    config_loader.py     # load YAML config
    strategy.py          # OCO straddle logic
    risk_manager.py       # position sizing, kill switches
    broker_paper.py      # simulated broker
    broker_oanda.py      # OANDA REST API placeholder
    data_feed.py         # fetch price data
    calendar.py          # economic calendar
    logger.py            # trade logging
    notifier.py          # optional Telegram alerts
  tests/
    test_strategy.py     # unit tests
  config/
    config.example.yaml  # template
  data/                  # historical data
  logs/                  # bot logs
```

---

## Important Warning

This bot is a tool, not a money printer. News straddles face:
- Wide spreads during events
- Slippage on fills
- False breakouts (both sides hit)
- Prop firm rules that may ban news trading

**Never trade live money until the bot is profitable in paper mode for at least 60 days.**

---

## Next Steps

1. Backtest the strategy on 2+ years of EURUSD data.
2. Optimize parameters (grid search).
3. Forward-test on paper for 60+ days.
4. Only then consider connecting to OANDA or similar broker.
