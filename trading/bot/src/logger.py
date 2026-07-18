import pandas as pd
from datetime import datetime
from pathlib import Path

class TradeLogger:
    def __init__(self, log_dir="../logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.columns = [
            "timestamp", "pair", "action", "price", "lots",
            "pnl", "balance", "reason", "signal_json"
        ]
        self.buffer = []

    def log(self, timestamp, pair, action, price, lots=0, pnl=0, balance=0, reason="", signal_json=""):
        self.buffer.append({
            "timestamp": timestamp,
            "pair": pair,
            "action": action,
            "price": price,
            "lots": lots,
            "pnl": pnl,
            "balance": balance,
            "reason": reason,
            "signal_json": signal_json,
        })
        self.flush()

    def flush(self):
        df = pd.DataFrame(self.buffer, columns=self.columns)
        if self.log_file.exists():
            df.to_csv(self.log_file, mode="a", header=False, index=False)
        else:
            df.to_csv(self.log_file, index=False)
        self.buffer = []

if __name__ == "__main__":
    logger = TradeLogger()
    logger.log(datetime.now(), "EURUSD", "OPEN_BUY", 1.0800, lots=1.0, balance=50000)
    print("Log saved to:", logger.log_file)
