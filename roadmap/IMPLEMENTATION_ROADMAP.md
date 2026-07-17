# FTC Implementation Roadmap

**Version:** 0.1
**Target:** Testnet MVP within 90 days; mainnet-ready within 12 months.

---

## Phase 0 — Foundation (Weeks 1–4)

| Week | Task | Owner | Deliverable |
|------|------|-------|-------------|
| 1 | Finalize decisions from `docs/DECISION_LOG.md` | Mr. Vincent + Kai | Signed-off tokenomics spec |
| 1–2 | Legal entity formation (Wyoming DAO LLC + counsel) | Legal counsel | Entity docs, cap table |
| 2 | Choose L2 and tooling | Kai | Network selection memo |
| 2–3 | Brand, domain, social presence | Design/ops | Landing page, docs site |
| 3–4 | Foundry/Hardhat scaffold + CI | Kai | GitHub repo with tests |

**Legal gates:**
- Retain U.S. securities counsel for token classification memo.
- Decide whether to file Form D / Reg D for any U.S. private sale, or restrict sales to non-U.S. persons.
- Begin money-transmitter / MSB analysis if any fiat on/off-ramp is planned.

---

## Phase 1 — Testnet MVP (Weeks 5–12)

| Week | Task | Deliverable |
|------|------|-------------|
| 5–6 | `FTC.sol`, `ChildSavingsVault.sol`, `GuardianRegistry.sol` | Deployed on testnet |
| 6–7 | `Treasury.sol`, `FeeDispatcher.sol`, `StoreDiscount.sol` | Deployed + unit tests |
| 7–8 | Integration tests, fuzz tests, gas profiling | Test report |
| 8–9 | Web app (deposit, view child balance, simulate payouts) | Demo dApp |
| 9–10 | Internal security review + bug bounty pre-launch | Review memo |
| 10–12 | Public testnet campaign, 500–1,000 beta families | Testnet analytics report |

**Audit gate:** Engage Tier-2 audit firm for testnet contracts before moving to mainnet.

---

## Phase 2 — Mainnet v1 (Months 4–6)

1. **Token generation event:** Public sale (15%) + liquidity (5%).
2. **Contract deployment** with multisig + timelock.
3. **Child savings launch** with parent onboarding and KYC attestation partner.
4. **First FTC Store pilot:** 1–3 partner merchants or a single cooperative store, 10–30% discounts.
5. **Treasury yield strategy:** Conservative liquid staking / stablecoin vaults only.

**Audit gate:** Full audit by two independent firms; remediation complete.

---

## Phase 3 — Scale & Compliance (Months 7–12)

1. **Multi-jurisdiction legal review:** EU MiCA, UK FCA, select Asian markets.
2. **Governance transition:** From multisig to on-chain DAO with delegated voting.
3. **Store network expansion:** API/POS plugin, 50+ merchants, discount target 30–50%.
4. **Institutional partnerships:** Custody, exchange listings, stablecoin rails.
5. **Second audit + continuous monitoring:** Immunefi bug bounty, Forta monitoring.

---

## Phase 4 — Long-Term (Year 2+)

1. Cross-chain deployment if demand justifies it.
2. Sub-treasuries by region for store operations.
3. Integration with payroll, tax-advantaged accounts, and legacy child-savings products.
4. Protocol-owned store network (cooperative / franchise model).

---

## Key Milestones

- **M1 (Day 30):** Signed-off tokenomics + legal entity.
- **M2 (Day 90):** Testnet MVP live with 1,000+ simulated child accounts.
- **M3 (Day 180):** Mainnet v1 live.
- **M4 (Day 365):** 50+ merchant stores and $10M+ in protocol-owned value.

---

## Budget Estimate (rough)

| Item | Est. Cost |
|------|-----------|
| Legal (formation + securities memo) | $50k–$150k |
| Smart-contract audits (2 rounds) | $80k–$250k |
| Development (Solidity + frontend) | $150k–$400k |
| Design, marketing, community | $50k–$150k |
| Store pilot / partnerships | $100k–$500k |
| Reserve / contingency | $100k–$300k |
| **Total Year 1** | **$530k–$1.75M** |

Actual depends heavily on whether FTC Stores are partner-based (cheaper) or owned/operated (expensive).
