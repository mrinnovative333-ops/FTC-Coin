import pandas as pd
import json
from datetime import datetime
from pathlib import Path

JOURNAL_PATH = Path("C:/Users/bidbu/trading/journal/trade_journal.csv")

# Ensure file exists
JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
if not JOURNAL_PATH.exists():
    pd.DataFrame(columns=[
        "date", "symbol", "direction", "entry", "stop", "target", "rr",
        "risk_percent", "outcome", "pnl", "r_multiple", "setup", "notes"
    ]).to_csv(JOURNAL_PATH, index=False)

def add_trade(date, symbol, direction, entry, stop, target, risk_percent, outcome, pnl, setup, notes=""):
    rr = round(abs((target - entry) / (entry - stop)), 2) if entry != stop else 0
    r_multiple = round(pnl / (risk_percent / 100 * 10000), 2)  # assumes $10k account; adjust later

    trade = {
        "date": date,
        "symbol": symbol,
        "direction": direction,
        "entry": entry,
        "stop": stop,
        "target": target,
        "rr": rr,
        "risk_percent": risk_percent,
        "outcome": outcome,
        "pnl": pnl,
        "r_multiple": r_multiple,
        "setup": setup,
        "notes": notes,
    }

    df = pd.read_csv(JOURNAL_PATH)
    df = pd.concat([df, pd.DataFrame([trade])], ignore_index=True)
    df.to_csv(JOURNAL_PATH, index=False)
    print(f"Trade logged: {symbol} {direction} | {outcome} | R:{r_multiple}")

# Example usage
if __name__ == "__main__":
    add_trade(
        date=datetime.now().strftime("%Y-%m-%d"),
        symbol="EURUSD",
        direction="Long",
        entry=1.0800,
        stop=1.0780,
        target=1.0840,
        risk_percent=1.0,
        outcome="Win",
        pnl=200,
        setup="Bullish FVG + OB at NY open",
        notes="Clean sweep of Asia low, entered on 15M FVG."
    )
    print("\nCurrent journal:")
    print(pd.read_csv(JOURNAL_PATH).tail())
