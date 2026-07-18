# Unified Trading Engine — Backtest Results

**Date:** 2026-07-17  
**Account:** $50,000 USD  
**Risk per trade:** 1%  
**Hard lot cap:** 5 lots  
**Spread cost:** 1 pip  
**Period:** 2023-01-01 to 2024-12-31  
**Asset:** EURUSD  

---

## Strategy Comparison

| Strategy | Final Balance | Return | Win Rate | Trades | Net PnL | Gross PnL | Costs |
|----------|--------------|--------|----------|--------|---------|-----------|-------|
| News Straddle | $56,654.37 | **+13.31%** | 67.86% | 28 | +$6,761.63 | +$6,863.32 | $101.69 |
| HETM Directional | $50,000.00 | 0.00% | — | 0 | $0.00 | $0.00 | $0.00 |
| **Hybrid (HETM + Straddle)** | **$58,021.55** | **+16.04%** | 67.74% | 31 | **+$8,297.88** | +$8,565.79 | $267.91 |

---

## Key Takeaways

1. **News Straddle works on EURUSD with proper risk sizing.** The earlier losing result was caused by bad lot sizing, not the strategy.
2. **Risk-based lot sizing + 5-lot cap keeps drawdown controlled.** No kill switch triggered.
3. **HETM alone is too conservative on daily data.** It needs higher-frequency data or a lower confidence threshold.
4. **Hybrid wins.** Using HETM as a directional filter on the straddle improves return by +2.7%.

---

## Next Tests to Run

- Lower HETM confidence threshold to 0.20–0.25 on daily data.
- Test on GBPUSD, XAUUSD, USDJPY.
- Use hourly data for sharper entries.
- Add slippage model for fast-moving news.
- Walk-forward parameter optimization on straddle ATR multipliers.

---

## How to Reproduce

```bash
cd /c/Users/bidbu/trading/quantum_model/src
python data_loader.py
python run_all_strategies.py
```

Results are saved to `../data/strategy_comparison.csv`.
