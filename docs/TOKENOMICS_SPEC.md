# FTC Tokenomics Specification v2.0

**Based on model:** `models/ftc_tokenomics_v2.py`
**Updated:** 2026-07-17 with resolved design decisions.

---

## 1. Supply and Distribution

| Bucket | Allocation | Tokens | Vesting / Lock |
|--------|-----------|--------|----------------|
| Community rewards & incentives | 25% | 5.25B | Released over 10–20 years via programs |
| Treasury | 20% | 4.20B | Protocol-owned; deployed into yield + store subsidies |
| Team + advisors | 15% | 3.15B | 1-year cliff, 4-year linear vest |
| Investors | 10% | 2.10B | 1-year cliff, 3-year linear vest |
| Public sale | 15% | 3.15B | Unlocked at TGE |
| Child savings reserve | 10% | 2.10B | Used for low-income 1:1 deposit matching |
| Liquidity (CEX/DEX) | 5% | 1.05B | Unlocked at TGE / LP incentives |
| **Total** | **100%** | **21.00B** | — |

**Deflationary mechanism:** 25% of all merchant transaction fees are permanently burned.

---

## 2. Network

**Base L2** (Coinbase) — chosen for low fees, fast finality, and easiest fiat on-ramp for families via Coinbase Pay / Base ecosystem.

---

## 3. Adoption Model

New child accounts follow a Gompertz-like logistic curve capped at `max_children` (default 100M). Early years are small; growth accelerates around year 10–12; adoption saturates as the addressable market matures.

---

## 4. Child Account Mechanics

### Deposits
- **Base deposit:** $250 equivalent in FTC.
- **1:1 treasury match** for qualifying low-income families, capped at $250 match.
- Effective starting deposit for matched families: **$500**.
- ~40% of new families assumed to qualify for the match.

### Yield
- Floating protocol parameter set by governance/Treasury based on:
  - Treasury APY on protocol-owned assets (default 7%).
  - Additional fee subsidy from merchant fees/community pool (default 4%, declining as cohorts age).
- Yield is **not a guaranteed return.**

### Payouts
- First payout window: child age 5.
- Subsequent windows: ages 10, 15, 20, 25.
- At each window, up to **25% of current balance** may be withdrawn.
- Withdrawals above the $5,000 cumulative threshold require full KYC attestation.

### KYC
- **Lightweight:** guardian identity verified at account creation.
- **Full KYC:** triggered only when cumulative withdrawals exceed $5,000.

---

## 5. Store Network and Fees

### Merchant economics
- Merchant pays a **2% transaction fee** on FTC-denominated sales.
- Consumer discount scales with adoption: **10% early, up to 30% at scale**.
- Merchant later claims a rebate from Treasury for the discount given.

### Fee distribution
| Destination | Share |
|-------------|-------|
| Buyback & burn (deflationary) | 25% |
| Treasury → child yield reserve | 35% |
| Store operations fund | 30% |
| Liquidity incentives | 10% |

### Sustainability rule
Discounts are funded by merchant fees and treasury yield. The launch target is 10–30% with a path to higher only as transaction volume scales.

---

## 6. Treasury Operations

- Custodies FTC, stablecoins, and yield-bearing positions.
- Invests only into whitelisted, low-risk strategies (liquid staking, money-market ERC-4626 vaults, short-duration T-bill tokens).
- Allocates yield to child-savings reserve and store subsidies.
- Executes buyback-and-burn via FeeDispatcher.

---

## 7. 30-Year Scenario Summary (v2.0)

| Scenario | Children (M) | Child Balance Pool ($B) | FTC Price | Market Cap ($B) | Treasury ($B) | Burned (B) |
|----------|--------------|--------------------------|-----------|-----------------|---------------|------------|
| Adverse | 19.77 | $5.36 | $1.08 | $10.18 | $8.49 | 1.23 |
| Conservative | 49.27 | $24.37 | $7.85 | $74.20 | $75.76 | 1.82 |
| **Base Case** | **98.44** | **$78.13** | **$26.08** | **$246.45** | **$239.86** | **1.67** |
| Abundance | 245.95 | $422.36 | $130.17 | $1,230.14 | $1,094.95 | 1.40 |

**Interpretation:** The 1:1 low-income match reduces the aggregate child pool compared to the earlier $500/$125 model, but dramatically improves access for the neediest families. In the Base Case, the network creates ~$78B in aggregate child wealth over 30 years.

---

## 8. Key Assumptions and Sensitivities

- Base deposit: $250.
- Low-income match eligibility: 40% of families.
- Match cap: $250 per qualifying child.
- Average family spend at FTC stores: $3,000/year.
- Merchant fee: 2%.
- Long-term treasury APY: 7%.
- Initial market cap: $70M (midpoint of $60–80M target range).
- Price model: network value per child × active children, divided by 20% of circulating float.

**Sensitivities:**
- Higher match eligibility or larger match cap → larger child pool but faster reserve depletion.
- Higher merchant volume → larger treasury and more sustainable discounts.
- Higher yield → larger balances but also higher regulatory risk if marketed as a guarantee.

---

## 9. Open Questions

1. Should yield be fixed for a cohort at deposit time, or floating annually?
2. What is the maximum match cap in FTC terms (needs oracle/governance)?
3. Should unused child-reserve tokens be burned, recycled, or retained after depletion?
4. How do we handle under-18 wallet custody and key management at payout age?
5. Should the public sale be a single event or staged across multiple rounds?
