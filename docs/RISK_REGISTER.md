# FTC Risk Register

**Version:** 0.1
**Last updated:** 2026-07-17

---

## 1. Regulatory / Legal Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Token classified as a security by SEC / other regulator | Medium | Critical | No profit-sharing, no guaranteed yield, no central issuer promise of returns; utility-first design; obtain securities-law memo before sale; consider Reg D / non-U.S. restrictions. |
| Money-transmitter / MSB licensing required for fiat on-ramps or store rebates | Medium | High | Use third-party licensed payment processors; no direct custody of user fiat; legal opinion before launch. |
| KYC/AML failures or sanctions exposure | Medium | High | Partner with regulated KYC provider; tiered withdrawal limits; on-chain attestations; SAR/CTR policies if AML obligations arise. |
| Consumer-protection actions (state AGs, FTC) | Medium | High | Clear disclosures: not a bank, not FDIC-insured, not a guaranteed investment; no deceptive marketing; legal review of all public materials. |
| Cross-border regulatory mismatch (MiCA, UK, Asia) | Medium | Medium | Geo-block restricted jurisdictions initially; retain local counsel before expanding. |

---

## 2. Technical / Smart-Contract Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Smart-contract exploit draining Treasury or child accounts | Low | Critical | Two independent audits; formal verification where feasible; bug bounty; timelock on admin functions; pause capability; Forta monitoring. |
| Oracle manipulation / stale price | Medium | High | Chainlink primary + DEX TWAP fallback; staleness checks; circuit breakers on large price moves. |
| Key compromise (multisig / deployer) | Low | Critical | 3-of-5 multisig with hardware wallets; social recovery; no single key control; timelock on upgrades. |
| Re-entrancy / integer bugs in payout logic | Medium | High | ReentrancyGuard; checked arithmetic; comprehensive fuzz tests; invariant testing with Foundry. |
| Bridge risk if cross-chain later | Medium | High | Avoid bridging in MVP; if later, use canonical bridges and monitor for exploits. |

---

## 3. Economic / Incentive Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Yield unsustainable if treasury underperforms | Medium | High | Yield is a protocol parameter, not a debt; cap maximum yield; conservative treasury allocation; transparent reporting; rate adjustments by governance. |
| Store discount unsustainable without volume | High | High | Start with partner-negotiated discounts / cashback, not protocol-funded 50% subsidies; scale discounts only as fee revenue scales; model in tokenomics sim. |
| Token price collapse eroding child-account value | Medium | High | Diversify treasury into stables; long-term holding incentives; avoid pump-driven launches; focus on utility adoption. |
| Low adoption → insufficient network effects | Medium | High | Partner with parent communities, schools, churches; build simple UX; onboarding subsidies limited to child reserve. |
| Run-on-payouts draining Treasury | Low | Critical | Payouts are age-gated and capped per checkpoint; reserve ratio monitored; emergency pause. |

---

## 4. Operational / Reputational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Fraudulent child accounts / duplicate registrations | Medium | Medium | Identity/KYC attestation; per-child uniqueness via identity hash; anti-gaming checks. |
| Negative press / “ponzi” accusations | Medium | High | Clear, honest messaging; audited code; public treasury dashboards; no income promises. |
| Team / founder disputes | Medium | Medium | Legal entity; vesting contracts; multisig governance; written roles and responsibilities. |
| Dependence on a single chain / L2 outage | Low | Medium | Choose proven L2; keep emergency migration plan; monitor sequencer health. |

---

## 5. Immediate Action Items

1. **Before any token sale:** written securities-law opinion.
2. **Before testnet:** complete internal audit and remediation.
3. **Before mainnet:** two independent external audits + bug bounty.
4. **Before store launch:** economic model showing discount sustainability for 5+ years.
5. **Ongoing:** monthly risk-review call with counsel and core team.
