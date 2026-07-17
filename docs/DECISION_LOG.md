# FTC Decision Log

## Decisions Resolved (2026-07-17)

All open questions have been resolved. See `docs/DECISIONS.md` for full rationale.

| # | Question | Resolution |
|---|----------|-----------|
| 1 | Network choice | **Base** (Coinbase L2) — easiest fiat onramp for families |
| 2 | Legal home | **Delaware C-Corp + Wyoming DAO LLC + Swiss foundation** (pending counsel) |
| 3 | KYC model | **Lightweight** — guardian ID at creation, full KYC at $5,000+ cumulative withdrawals |
| 4 | FTC Stores | **Partner-merchant discount network** — no owned stores |
| 5 | Raise / valuation | **$8–15M public sale, $60–80M target initial market cap** |
| 6 | Deposit norm | **$250 base, 1:1 treasury match** for qualifying low-income families (up to $500 effective) |

## Prior Decisions (carried forward)
- **Token Standard:** ERC-20 + account-bound child savings vaults (not ERC-6551 for MVP)
- **Yield Source:** Hybrid (treasury yield + fee subsidy) — floating parameter, not a guarantee
- **Fee Model:** Merchant-paid fees (2% default)
- **Oracle:** Chainlink for FTC/USD price feeds
- **Governance:** Multisig + timelock at launch → on-chain DAO

## Decisions Made by Kai (pending approval)
- Solidity 0.8.x with OpenZeppelin libraries.
- Hardhat/Foundry dual toolchain for contracts.
- Python + pandas + numpy + matplotlib for modeling.
