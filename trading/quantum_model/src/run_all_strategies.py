"""
Run all three strategy variants and compare results.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
# Also access bot's economic calendar module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "bot" / "src"))

import pandas as pd
from unified_engine import TradeConfig, run_straddle_backtest, run_hetm_backtest, run_hybrid_backtest
from data_loader import DATA_DIR, ASSETS


def load_events():
    from economic_calendar import EconomicCalendar
    cal = EconomicCalendar(str(DATA_DIR / "events.csv"))
    cal.save_default()
    return cal.load()


def load_assets(start="2023-01-01", end="2024-12-31"):
    assets = {}
    for name in ASSETS.keys():
        path = DATA_DIR / f"{name}.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path)
        date_col = "time" if "time" in df.columns else "Date"
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.rename(columns={date_col: "time"})
        df = df[(df["time"] >= start) & (df["time"] <= end)]
        if len(df) > 30:
            assets[name] = df
    return assets


def main():
    cfg = TradeConfig(
        starting_balance=50000.0,
        risk_per_trade_pct=1.0,
        max_lots_hard_cap=5.0,
        spread_pips=1.0,
        commission_per_lot=0.0,
        kill_switch_drawdown_pct=10.0,
    )

    assets = load_assets()
    df_daily = assets["EURUSD"].copy()
    events = load_events()

    print("=== STRATEGY 1: News Straddle ===")
    broker1 = run_straddle_backtest(df_daily, events, cfg)
    s1 = broker1.summary()
    for k, v in s1.items():
        print(f"  {k}: {v}")

    print("\n=== STRATEGY 2: HETM Directional ===")
    closes = pd.DataFrame({name: df.set_index("time")["Close"] for name, df in assets.items()})
    closes = closes.dropna()
    broker2 = run_hetm_backtest(closes, assets, cfg)
    s2 = broker2.summary()
    for k, v in s2.items():
        print(f"  {k}: {v}")

    print("\n=== STRATEGY 3: Hybrid (HETM + Straddle) ===")
    broker3 = run_hybrid_backtest(closes, assets, events, cfg)
    s3 = broker3.summary()
    for k, v in s3.items():
        print(f"  {k}: {v}")

    print("\n=== COMPARISON ===")
    comparison = pd.DataFrame([s1, s2, s3], index=["News Straddle", "HETM Directional", "Hybrid"])
    print(comparison.to_string())
    comparison.to_csv(DATA_DIR / "strategy_comparison.csv")


if __name__ == "__main__":
    main()
