"""
FTC Tokenomics Simulation v0.1
================================
Purpose: Model supply, vesting, treasury, child-account growth, and payout sustainability
under multiple macro / adoption scenarios.

Run: python models/ftc_tokenomics_v0.py
"""
import math
from dataclasses import dataclass, field
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


@dataclass
class Tokenomics:
    # Supply
    total_supply: float = 21_000_000_000.0  # 21B tokens, like Bitcoin magnitude but more accessible
    # Distribution
    community_rewards_pct: float = 0.25  # staking, store rewards, ecosystem incentives
    treasury_pct: float = 0.20           # store network, stability, partnerships
    team_advisors_pct: float = 0.15      # 4-year vesting
    investors_pct: float = 0.10          # seed, private, strategic; 1y cliff + 2y vest
    public_sale_pct: float = 0.15        # launchpad / IDO
    child_savings_reserve_pct: float = 0.10  # protocol-funded matching / early-adopter bonuses
    liquidity_pct: float = 0.05          # CEX/DEX liquidity
    # Vesting
    team_vesting_years: float = 4.0
    investor_vesting_years: float = 3.0
    # Child account parameters
    annual_yield_rate: float = 0.12      # modeled APY from protocol cash flows (not a guarantee)
    parent_match_rate: float = 0.25      # protocol matches parent contribution up to this amount (funded from reserve)
    max_match_per_child: float = 500.0   # USD equivalent max match per child
    payout_interval_years: float = 5.0
    final_payout_age: float = 25.0
    initial_deposit_usd: float = 500.0   # typical family starting deposit
    # Protocol cash flows
    tx_fee_pct: float = 0.02             # 2% per transaction
    annual_store_volume_usd: float = 1_000_000.0  # starting year 1
    store_discount_pct: float = 0.50
    treasury_burn_pct_of_fees: float = 0.25
    treasury_to_child_rewards_pct: float = 0.35
    treasury_to_store_ops_pct: float = 0.30
    treasury_to_liquidity_pct: float = 0.10
    # Adoption
    new_children_per_year_start: float = 10_000.0
    children_growth_rate: float = 0.30   # annual growth in child accounts
    years: int = 30

    def run(self) -> pd.DataFrame:
        records: List[Dict] = []
        total_supply = self.total_supply
        supply_unlocked = self.public_sale_pct * total_supply + self.liquidity_pct * total_supply
        supply_locked = total_supply - supply_unlocked
        team_locked = self.team_advisors_pct * total_supply
        investor_locked = self.investors_pct * total_supply
        child_reserve = self.child_savings_reserve_pct * total_supply
        treasury_balance = self.treasury_pct * total_supply
        community_pool = self.community_rewards_pct * total_supply

        children_count = 0.0
        total_child_principal_usd = 0.0
        total_child_balance_usd = 0.0
        cumulative_fees_collected = 0.0

        for year in range(self.years + 1):
            # Vesting unlock
            if year > 0:
                team_unlock_this_year = team_locked / self.team_vesting_years if year <= self.team_vesting_years else 0.0
                investor_unlock_this_year = investor_locked / self.investor_vesting_years if year <= self.investor_vesting_years else 0.0
                supply_unlocked += team_unlock_this_year + investor_unlock_this_year
                team_locked = max(team_locked - team_unlock_this_year, 0)
                investor_locked = max(investor_locked - investor_unlock_this_year, 0)

            # Adoption growth (sigmoid-like; capped by practical network size)
            new_children = self.new_children_per_year_start * ((1 + self.children_growth_rate) ** year)
            children_count += new_children

            # Parent deposits and protocol match
            deposits = new_children * self.initial_deposit_usd
            match_usd = min(deposits * self.parent_match_rate, new_children * self.max_match_per_child)
            match_tokens = match_usd  # assume stable USD valuation for modeling
            child_reserve = max(child_reserve - match_tokens, 0)
            total_child_principal_usd += deposits + match_usd

            # Annual yield on existing child balances
            yield_usd = total_child_balance_usd * self.annual_yield_rate
            total_child_balance_usd += deposits + match_usd + yield_usd

            # Store volume and fee generation
            store_volume = self.annual_store_volume_usd * ((1 + self.children_growth_rate) ** year)
            fees = store_volume * self.tx_fee_pct
            cumulative_fees_collected += fees

            # Treasury allocation of fees
            treasury_balance += fees
            burn = fees * self.treasury_burn_pct_of_fees
            treasury_balance -= burn
            total_supply -= burn

            # Payouts for children reaching payout age (every 5 years)
            payouts_this_year = 0.0
            if year > 0 and year % int(self.payout_interval_years) == 0:
                # simplified: each cohort that is old enough withdraws a fraction
                eligible_children = children_count * 0.05  # rough steady-state fraction age 5+
                payout_per_child = total_child_balance_usd * 0.03 / max(eligible_children, 1)
                payouts_this_year = eligible_children * payout_per_child
                total_child_balance_usd -= payouts_this_year

            records.append({
                "year": year,
                "supply_unlocked": supply_unlocked,
                "supply_locked": team_locked + investor_locked,
                "total_supply": total_supply,
                "children_count": children_count,
                "new_children": new_children,
                "child_principal_usd": total_child_principal_usd,
                "child_balance_usd": total_child_balance_usd,
                "treasury_balance": treasury_balance,
                "community_pool": community_pool,
                "annual_fees": fees,
                "annual_burn": burn,
                "annual_payouts": payouts_this_year,
            })

        return pd.DataFrame(records)

    def plot(self, df: pd.DataFrame, scenario_name: str = "Base Case") -> None:
        fig, axs = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(f"FTC Tokenomics — {scenario_name}", fontsize=14, fontweight="bold")

        axs[0, 0].plot(df["year"], df["total_supply"] / 1e9, label="Total Supply")
        axs[0, 0].set_title("Total Supply (B tokens)")
        axs[0, 0].set_xlabel("Year")
        axs[0, 0].legend()
        axs[0, 0].grid(True, alpha=0.3)

        axs[0, 1].plot(df["year"], df["children_count"] / 1e6, color="green")
        axs[0, 1].set_title("Cumulative Child Accounts (M)")
        axs[0, 1].set_xlabel("Year")
        axs[0, 1].grid(True, alpha=0.3)

        axs[1, 0].plot(df["year"], df["child_balance_usd"] / 1e6, color="purple")
        axs[1, 0].set_title("Child Account Balance Pool ($M)")
        axs[1, 0].set_xlabel("Year")
        axs[1, 0].grid(True, alpha=0.3)

        axs[1, 1].plot(df["year"], df["treasury_balance"] / 1e6, label="Treasury", color="orange")
        axs[1, 1].plot(df["year"], df["annual_fees"] / 1e6, label="Annual Fees", color="blue")
        axs[1, 1].set_title("Treasury & Annual Fees ($M)")
        axs[1, 1].set_xlabel("Year")
        axs[1, 1].legend()
        axs[1, 1].grid(True, alpha=0.3)

        safe = scenario_name.lower().replace(" ", "_").replace("/", "_").replace("\\", "_")
        out_path = f"C:/Users/bidbu/ftc/models/tokenomics_{safe}.png"
        plt.tight_layout()
        plt.savefig(out_path)
        print(f"Saved chart: {out_path}")


def main():
    scenarios = {
        "Base Case": Tokenomics(annual_yield_rate=0.10, children_growth_rate=0.30),
        "High Adoption": Tokenomics(annual_yield_rate=0.12, children_growth_rate=0.60, new_children_per_year_start=50_000.0),
        "Low Yield / Stagnant": Tokenomics(annual_yield_rate=0.03, children_growth_rate=0.10, tx_fee_pct=0.01),
        "Adverse (High Payouts + Low Fees)": Tokenomics(annual_yield_rate=0.04, children_growth_rate=0.15, tx_fee_pct=0.005, treasury_burn_pct_of_fees=0.05),
    }

    summary_rows = []
    for name, sim in scenarios.items():
        df = sim.run()
        sim.plot(df, scenario_name=name)
        final = df.iloc[-1]
        summary_rows.append({
            "scenario": name,
            "final_supply_B": round(final["total_supply"] / 1e9, 2),
            "final_children_M": round(final["children_count"] / 1e6, 2),
            "final_child_balance_$M": round(final["child_balance_usd"] / 1e6, 1),
            "final_treasury_$M": round(final["treasury_balance"] / 1e6, 1),
            "total_burned_B": round((sim.total_supply - final["total_supply"]) / 1e9, 2),
        })

    summary = pd.DataFrame(summary_rows)
    print("\n=== 30-Year Scenario Summary ===")
    print(summary.to_string(index=False))
    summary.to_csv("C:/Users/bidbu/ftc/models/scenario_summary.csv", index=False)


if __name__ == "__main__":
    main()
