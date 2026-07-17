# FTC Decisions

**Status:** Resolved as of 2026-07-17  
**Owner:** John William Vincent  
**Lead:** Kai 👑

---

## Resolved Design Decisions

| # | Question | Resolution |
|---|----------|-----------|
| 1 | Network choice | **Base L2** (Coinbase) — easiest fiat on-ramp for families |
| 2 | Legal home | **Delaware C-Corp + Wyoming DAO LLC + Swiss foundation** (pending securities counsel) |
| 3 | KYC model | **Lightweight** — guardian identity verified at account creation, full KYC at $5,000 cumulative withdrawals |
| 4 | FTC Stores | **Partner-merchant discount network** — 10–30% at participating retailers, no owned physical stores |
| 5 | Raise / valuation | **$8–15M public sale**, **$60–80M target initial market cap** |
| 6 | Deposit norm | **$250 base**, **1:1 treasury match** for qualifying low-income families ($500 effective working deposit) |

---

## Technical Decisions

| # | Question | Resolution |
|---|----------|-----------|
| 7 | Token standard | ERC-20 + account-bound child savings vaults (not ERC-6551 for MVP) |
| 8 | Yield source | Hybrid: treasury yield + protocol fee subsidy. **Floating parameter, not a guarantee** |
| 9 | Fee model | Merchant-paid fees, 2% default |
| 10 | Oracle | Chainlink for FTC/USD price feeds; fallback TWAP |
| 11 | Governance | Multisig + timelock at launch → on-chain DAO |
| 12 | Toolchain | Foundry (primary) + Hardhat (secondary) |
| 13 | Solidity version | 0.8.24 |

---

## Pending Counsel Confirmation

1. Swiss foundation jurisdiction and structure.
2. Token classification memo (U.S. securities law).
3. MSB/money-transmitter analysis for merchant rebate flows.
4. EU MiCA whitepaper requirements if public sale includes EU participants.

---

## Open Build Questions (for Mr. Vincent)

1. Do you want the 1:1 match to be **permanent** or **phased out** once child reserve is depleted?
2. Should yield rate be **fixed at account opening** or **float annually** for all accounts?
3. Do you want **merchant rebates paid instantly** by Treasury, or **batch-claimed weekly/monthly**?
4. Should guardian control **automatically transfer to the child** at age 18, or remain with guardian until 25?
5. Do you want a **public sale date target** (e.g., Q4 2026, Q1 2027)?
