"""
FTC Tokenomics Simulation v1.2
================================
Realistic aggregate-cohort model for FTC (For The Children).

Key improvements:
- Each yearly cohort tracks: children_count, principal_usd, balance_usd.
- Sigmoid adoption with a long tail (Gompertz / shifted logistic).
- Age-based payouts every 5 years until age 25.
- Token price from network valuation divided by circulating float.
- Treasury grows from merchant fees and yields; burn is deflationary.

Run: python models/ftc_tokenomics_v1_2.py
"""
from dataclasses import dataclass
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


@dataclass
class Tokenomics:
    # --- Supply ---
    total_supply: float = 21_000_000_000.0  # 21B FTC

    # --- Distribution ---
    community_rewards_pct: float = 0.25
    treasury_pct: float = 0.20
    team_advisors_pct: float = 0.15
    investors_pct: float = 0.10
    public_sale_pct: float = 0.15
    child_savings_reserve_pct: float = 0.10
    liquidity_pct: float = 0.05

    # --- Vesting ---
    team_vesting_years: float = 4.0
    team_cliff_years: float = 1.0
    investor_vesting_years: float = 3.0
    investor_cliff_years: float = 1.0

    # --- Adoption (Gompertz-like long tail) ---
    max_children: float = 100_000_000.0
    adoption_inflection_year: float = 12.0
    adoption_steepness: float = 0.35
    new_children_year0: float = 100_000.0

    # --- Child account mechanics ---
    initial_deposit_usd: float = 500.0
    parent_match_rate: float = 0.25
    max_match_usd_per_child: float = 125.0
    payout_interval_years: int = 5
    final_payout_age: int = 25

    # --- Yield on child balances ---
    treasury_apy: float = 0.07
    protocol_subsidy_apy: float = 0.04

    # --- Store network / fees ---
    avg_spend_per_family_year_usd: float = 3_000.0
    merchant_tx_fee_pct: float = 0.02
    discount_to_consumer_pct: float = 0.30
    treasury_burn_pct_of_fees: float = 0.25
    treasury_to_child_rewards_pct: float = 0.35
    treasury_to_store_ops_pct: float = 0.30
    treasury_to_liquidity_pct: float = 0.10

    # --- Valuation ---
    initial_market_cap_usd: float = 50_000_000.0
    valuation_per_child_usd: float = 500.0
    years: int = 30

    def adoption_curve(self, year: int) -> float:
        """Cumulative children by year using a shifted logistic with a long tail."""
        return self.max_children / (1 + np.exp(-self.adoption_steepness * (year - self.adoption_inflection_year)))

    def new_children_in_year(self, year: int) -> float:
        if year == 0:
            return self.new_children_year0
        prev = self.adoption_curve(year - 1)
        curr = self.adoption_curve(year)
        return max(curr - prev, 0)

    def effective_token_price(self, year: int, circulating: float, total_children: float) -> float:
        network_value = self.initial_market_cap_usd + total_children * self.valuation_per_child_usd
        # Only a fraction of circulating supply is assumed liquid / price-setting
        effective_float = max(circulating * 0.20, 1_000_000.0)
        return network_value / effective_float

    def run(self) -> pd.DataFrame:
        records: List[Dict] = []

        total_supply = self.total_supply
        unlocked = (self.public_sale_pct + self.liquidity_pct) * total_supply
        team_locked = self.team_advisors_pct * total_supply
        investor_locked = self.investors_pct * total_supply
        child_reserve_tokens = self.child_savings_reserve_pct * total_supply
        treasury_tokens = self.treasury_pct * total_supply
        community_pool_tokens = self.community_rewards_pct * total_supply

        # Cohorts: each year appends one aggregate cohort dict
        cohorts: List[Dict] = []

        for year in range(self.years + 1):
            # --- Vesting ---
            if year > 0:
                team_unlock = 0.0
                investor_unlock = 0.0
                if year >= self.team_cliff_years:
                    elapsed_after_cliff = year - self.team_cliff_years + 1
                    vesting_period = self.team_vesting_years - self.team_cliff_years
                    if elapsed_after_cliff <= vesting_period:
                        team_unlock = team_locked / (vesting_period - elapsed_after_cliff + 1)
                if year >= self.investor_cliff_years:
                    elapsed_after_cliff = year - self.investor_cliff_years + 1
                    vesting_period = self.investor_vesting_years - self.investor_cliff_years
                    if elapsed_after_cliff <= vesting_period:
                        investor_unlock = investor_locked / (vesting_period - elapsed_after_cliff + 1)
                unlocked += team_unlock + investor_unlock
                team_locked = max(team_locked - team_unlock, 0)
                investor_locked = max(investor_locked - investor_unlock, 0)

            # --- Adoption ---
            new_kids = self.new_children_in_year(year)
            deposits = new_kids * self.initial_deposit_usd
            match = min(deposits * self.parent_match_rate, new_kids * self.max_match_usd_per_child)

            price = self.effective_token_price(year, unlocked, sum(c["count"] for c in cohorts) + new_kids)

            # Deduct match from child reserve token pool
            match_tokens = match / price if price > 0 else 0
            child_reserve_tokens = max(child_reserve_tokens - match_tokens, 0)

            # Append aggregate cohort
            cohorts.append({"age": 0, "count": new_kids, "principal": deposits + match, "balance": deposits + match})

            # --- Age cohorts and apply yield ---
            for c in cohorts:
                c["age"] += 1
                # Yield curve: higher early, stabilizes as the protocol matures
                age_factor = max(0.2, 1.0 - c["age"] / 40.0)
                effective_yield = self.treasury_apy + self.protocol_subsidy_apy * age_factor
                c["balance"] *= (1 + effective_yield)

            # --- Store network fees ---
            total_children = sum(c["count"] for c in cohorts)
            active_families = sum(c["count"] for c in cohorts if c["age"] >= 1)
            store_volume = active_families * self.avg_spend_per_family_year_usd
            fees_usd = store_volume * self.merchant_tx_fee_pct

            fee_tokens = fees_usd / price if price > 0 else 0
            treasury_tokens += fee_tokens
            burn_tokens = fee_tokens * self.treasury_burn_pct_of_fees
            treasury_tokens -= burn_tokens
            total_supply -= burn_tokens

            # --- Payouts every 5 years starting at age 5 ---
            annual_payouts = 0.0
            for c in cohorts:
                if c["age"] > 0 and c["age"] % self.payout_interval_years == 0 and c["age"] <= self.final_payout_age:
                    payout = c["balance"] * 0.25
                    c["balance"] -= payout
                    annual_payouts += payout

            total_child_balance = sum(c["balance"] for c in cohorts)
            total_child_principal = sum(c["principal"] for c in cohorts)
            market_cap = price * unlocked

            records.append({
                "year": year,
                "new_children": new_kids,
                "total_children": total_children,
                "active_families": active_families,
                "total_child_principal_usd": total_child_principal,
                "total_child_balance_usd": total_child_balance,
                "annual_payouts_usd": annual_payouts,
                "store_volume_usd": store_volume,
                "annual_fees_usd": fees_usd,
                "annual_burn_tokens": burn_tokens,
                "price_usd": price,
                "market_cap_usd": market_cap,
                "circulating_tokens": unlocked,
                "locked_tokens": team_locked + investor_locked,
                "treasury_tokens": treasury_tokens,
                "treasury_usd": treasury_tokens * price,
                "total_supply": total_supply,
                "child_reserve_tokens": child_reserve_tokens,
            })

        return pd.DataFrame(records)

    def plot(self, df: pd.DataFrame, scenario_name: str = "Base Case") -> None:
        fig, axs = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle(f"FTC Tokenomics v1.2 — {scenario_name}", fontsize=14, fontweight="bold")

        axs[0, 0].plot(df["year"], df["total_children"] / 1e6, color="green")
        axs[0, 0].set_title("Cumulative Children (M)")
        axs[0, 0].set_xlabel("Year")
        axs[0, 0].grid(True, alpha=0.3)

        axs[0, 1].plot(df["year"], df["total_child_balance_usd"] / 1e9, color="purple")
        axs[0, 1].set_title("Child Balance Pool ($B)")
        axs[0, 1].set_xlabel("Year")
        axs[0, 1].grid(True, alpha=0.3)

        axs[0, 2].plot(df["year"], df["annual_payouts_usd"] / 1e6, color="red")
        axs[0, 2].set_title("Annual Payouts ($M)")
        axs[0, 2].set_xlabel("Year")
        axs[0, 2].grid(True, alpha=0.3)

        axs[1, 0].plot(df["year"], df["price_usd"], color="blue")
        axs[1, 0].set_title("Modeled Token Price ($)")
        axs[1, 0].set_xlabel("Year")
        axs[1, 0].set_yscale("log")
        axs[1, 0].grid(True, alpha=0.3)

        axs[1, 1].plot(df["year"], df["total_supply"] / 1e9, label="Total Supply")
        axs[1, 1].plot(df["year"], df["circulating_tokens"] / 1e9, label="Circulating")
        axs[1, 1].set_title("Supply (B tokens)")
        axs[1, 1].set_xlabel("Year")
        axs[1, 1].legend()
        axs[1, 1].grid(True, alpha=0.3)

        axs[1, 2].plot(df["year"], df["treasury_usd"] / 1e9, color="orange")
        axs[1, 2].set_title("Treasury Value ($B)")
        axs[1, 2].set_xlabel("Year")
        axs[1, 2].grid(True, alpha=0.3)

        safe = scenario_name.lower().replace(" ", "_").replace("/", "_").replace("\\\\", "_")
        out_path = f"C:/Users/bidbu/ftc/models/tokenomics_v1_2_{safe}.png"
        plt.tight_layout()
        plt.savefig(out_path)
        print(f"Saved chart: {out_path}")


def main():
    scenarios = {
        "Conservative": Tokenomics(
            max_children=50_000_000,
            treasury_apy=0.05,
            protocol_subsidy_apy=0.03,
            avg_spend_per_family_year_usd=2_000,
            valuation_per_child_usd=300,
        ),
        "Base Case": Tokenomics(
            max_children=100_000_000,
            treasury_apy=0.07,
            protocol_subsidy_apy=0.04,
            avg_spend_per_family_year_usd=3_000,
            valuation_per_child_usd=500,
        ),
        "Abundance": Tokenomics(
            max_children=250_000_000,
            treasury_apy=0.10,
            protocol_subsidy_apy=0.06,
            avg_spend_per_family_year_usd=5_000,
            valuation_per_child_usd=1_000,
            discount_to_consumer_pct=0.45,
        ),
        "Adverse": Tokenomics(
            max_children=20_000_000,
            treasury_apy=0.03,
            protocol_subsidy_apy=0.01,
            avg_spend_per_family_year_usd=1_000,
            valuation_per_child_usd=100,
            merchant_tx_fee_pct=0.01,
        ),
    }

    summary_rows = []
    for name, sim in scenarios.items():
        df = sim.run()
        sim.plot(df, scenario_name=name)
        final = df.iloc[-1]
        summary_rows.append({
            "scenario": name,
            "final_children_M": round(final["total_children"] / 1e6, 2),
            "final_child_balance_$B": round(final["total_child_balance_usd"] / 1e9, 2),
            "final_price_$": round(final["price_usd"], 4),
            "final_market_cap_$B": round(final["market_cap_usd"] / 1e9, 2),
            "final_treasury_$B": round(final["treasury_usd"] / 1e9, 2),
            "total_burned_B": round((sim.total_supply - final["total_supply"]) / 1e9, 2),
        })

    summary = pd.DataFrame(summary_rows)
    print("\n=== 30-Year Scenario Summary (v1.2) ===")
    print(summary.to_string(index=False))
    summary.to_csv("C:/Users/bidbu/ftc/models/scenario_summary_v1_2.csv", index=False)


if __name__ == "__main__":
    main()
