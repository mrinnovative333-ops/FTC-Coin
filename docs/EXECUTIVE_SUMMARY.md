# FTC Executive Summary

**Project:** FTC — For The Children  
**Version:** 0.2  
**Date:** 2026-07-17  
**Prepared by:** Kai, for John William Vincent

---

## 1. What is FTC?

FTC is a decentralized savings and payments protocol on **Base L2** designed to help parents and guardians build long-term, compounding wealth for children. It combines:

- **Child savings vaults** with age-gated, structured payouts every five years until age 25.
- **Low-income 1:1 deposit matching** so the neediest families start with $500 working for their child.
- **Transparent yield** funded by protocol treasury returns and ecosystem fees — explicitly not a guaranteed return.
- **FTC Stores** — a partner-merchant discount network where families pay with FTC for 10–30% savings on everyday essentials.

The mission is to create family-level abundance, reduce dependence on fragile public systems, and end generational poverty through voluntary, incentive-aligned financial tools.

---

## 2. The Problem

- Public pension and child-support systems in many countries are underfunded and politically uncertain.
- Traditional child savings products offer low yields, high fees, and little real-world utility.
- Many families lack accessible, long-term wealth-building tools that compound over a child’s lifetime.
- Cryptocurrency has so far been dominated by speculation; few projects deliver sustained, real-world value to ordinary families.

---

## 3. The Solution

FTC turns a family’s early commitment into a durable, protocol-enforced wealth engine.

### For Parents
- Open a vault for a child with a **$250 starting deposit**.
- Qualifying low-income families receive a **1:1 treasury match** (up to $250), giving their child a **$500 effective start**.
- Watch the balance grow from treasury yield and network fees.
- Withdrawals are automatically timed to life stages (ages 5, 10, 15, 20, 25).
- Only lightweight KYC at signup; full KYC required only after $5,000 in cumulative withdrawals.

### For Children
- Receive structured support for food, housing, medical, education, and independence.
- No need to manage complex wallets until payout age; guardians hold control, then control transitions.

### For Merchants / FTC Stores
- Accept FTC at checkout with near-zero-cost settlement.
- Receive treasury rebates for offering discounts to FTC families.
- Gain access to a loyal, mission-driven customer base.

---

## 4. Tokenomics at a Glance

| Parameter | Value |
|-----------|-------|
| Network | Base L2 |
| Total supply | 21,000,000,000 FTC |
| Treasury | 20% |
| Community rewards | 25% |
| Team + advisors | 15% (4-year vesting, 1-year cliff) |
| Investors | 10% (3-year vesting, 1-year cliff) |
| Public sale | 15% |
| Child savings reserve | 10% |
| Liquidity | 5% |
| Base deposit | $250 |
| Low-income match | 1:1 up to $250 |
| Yield source | Treasury APY + protocol fee subsidy (floating, not guaranteed) |
| Payout schedule | Every 5 years, ages 5–25 |
| Max payout per checkpoint | 25% of balance |
| Merchant fee | 2% |
| Consumer discount | 10–30%, scaling with adoption |
| Deflationary mechanism | 25% of merchant fees burned |
| Initial market cap target | $60–80M |
| Public sale raise target | $8–15M |

---

## 5. Technology

- **Blockchain:** Base L2.
- **Smart contracts:** Solidity 0.8.24, OpenZeppelin libraries, UUPS upgrade proxy, multisig + timelock.
- **Core contracts:** `FTC.sol`, `GuardianRegistry.sol`, `ChildSavingsVault.sol`, `Treasury.sol`, `FeeDispatcher.sol`, `StoreDiscount.sol`.
- **Oracles:** Chainlink for FTC/USD pricing; fallback TWAP.
- **Frontend:** Web app for deposits, child-account dashboards, merchant POS integration.
- **Tooling:** Foundry + Hardhat, dual-audit workflow, Forta monitoring, Immunefi bounty.

---

## 6. Roadmap Highlights

- **Month 1:** Finalize tokenomics, legal entity, securities-law memo.
- **Month 3:** Public testnet MVP on Base Sepolia with child vaults, treasury, and merchant discount demo.
- **Month 6:** Mainnet launch + first FTC Store pilot with partner merchants.
- **Month 12:** 50+ merchant network, governance DAO transition.
- **Year 2+:** Cross-chain expansion, deeper institutional partnerships.

---

## 7. Legal Structure

- **Delaware C-Corp:** Operating company for development and commercial activities.
- **Wyoming DAO LLC:** On-chain governance and protocol ownership.
- **Swiss foundation (pending securities counsel):** Non-profit ecosystem treasury and grants.

All structures require final confirmation from securities and tax counsel before token sale.

---

## 8. Why FTC Can Succeed

1. **Real utility first:** Families save and spend, not speculate.
2. **Long time horizon:** Compound growth over 20+ years is structurally powerful.
3. **Network effects:** More families → more merchants → more discounts → more adoption.
4. **Transparent and auditable:** All core logic is on-chain and open-source.
5. **Aligned incentives:** Parents, children, merchants, and the protocol all win when adoption grows.

---

## 9. Important Disclaimers

- FTC is **not** a bank, government program, or guaranteed investment product.
- Yield and discounts are **targets** based on protocol economics, not promises.
- Token value may fluctuate; child-account balances are exposed to market risk.
- All participants must comply with applicable laws in their jurisdiction.

---

## 10. 30-Year Economic Scenarios

| Scenario | Children (M) | Child Balance Pool ($B) | FTC Price | Market Cap ($B) |
|----------|--------------|--------------------------|-----------|-----------------|
| Adverse | 19.8 | $5.4 | $1.08 | $10.2 |
| Conservative | 49.3 | $24.4 | $7.85 | $74.2 |
| **Base Case** | **98.4** | **$78.1** | **$26.08** | **$246.5** |
| Abundance | 245.9 | $422.4 | $130.17 | $1,230.1 |

See `models/scenario_summary_v2.csv` for full detail.

---

*For The Children. Built to last.*
