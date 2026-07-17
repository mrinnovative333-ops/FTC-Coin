# FTC Legal Considerations Memo

**Version:** 0.1
**Date:** 2026-07-17
**Prepared by:** Kai (not legal counsel — this memo flags issues for attorney review)

---

## 1. Overview

FTC is a decentralized protocol with a token, child savings vaults, merchant discounts, and a treasury. This creates overlapping legal questions in securities, commodities, money-transmission, tax, and consumer-protection law. This document identifies the major issues and suggests how to engage counsel.

---

## 2. Securities Law (U.S.)

### 2.1 Primary Question
Will FTC be deemed an “investment contract” under the Howey test?

**Howey elements:**
1. Investment of money.
2. In a common enterprise.
3. With expectation of profits.
4. Derived from the efforts of others.

### 2.2 Risk Factors
- If users buy FTC expecting price appreciation driven by the team/protocol, the token may satisfy Howey.
- Guaranteed or marketed yield strengthens the “expectation of profits” prong.
- Marketing that emphasizes wealth, abundance, or returns increases risk.

### 2.3 Mitigation
- **No guaranteed yield.** Yield is a protocol parameter based on treasury performance and fees, not a debt obligation.
- **Utility emphasis.** FTC is required to access discounts, open vaults, and pay at stores.
- **Decentralization.** Over time, migrate control from the team to a DAO.
- **Disclosures.** Every vault opening and public communication includes: “FTC is not a security, bank deposit, or guaranteed investment.”
- **Pre-launch legal opinion.** Retain U.S. securities counsel to issue a classification memo.

---

## 3. Money Transmission / MSB

### 3.1 Primary Question
Does operating Treasury, merchant rebates, or fiat on-ramps require state or federal MSB registration?

### 3.2 Risk Factors
- Accepting and transmitting value on behalf of users is a regulated activity in many jurisdictions.
- Direct fiat custody or conversion would likely trigger FinCEN MSB rules in the U.S.

### 3.3 Mitigation
- Use licensed third-party payment processors for fiat on/off-ramps.
- Treasury holds crypto assets only; stablecoin operations through whitelisted ERC-4626 vaults.
- Merchants receive rebates in FTC directly from smart contracts, not from a centralized transmitter.
- Obtain legal memo before enabling any fiat functionality.

---

## 4. Consumer Protection

### 4.1 FTC / State AG Risk
- Marketing claims like “end generational poverty” or “guaranteed abundance” could draw scrutiny.
- Any representation of future returns must be truthful, substantiated, and not misleading.

### 4.2 Mitigation
- Use aspirational framing for the mission and factual framing for mechanics.
- Disclose risks prominently: token volatility, yield variability, no FDIC insurance, no government backing.
- Avoid income projections in marketing materials.

---

## 5. Tax

### 5.1 U.S. Tax Considerations
- Token sales may trigger ordinary income or capital gains depending on structure.
- Parent deposits into child vaults may be treated as gifts; consult tax advisor.
- Merchant discounts / rebates may create taxable income or 1099 reporting obligations.

### 5.2 Mitigation
- Engage crypto tax counsel early.
- Provide users with transaction history exports for their own tax reporting.

---

## 6. KYC / AML / Sanctions

### 6.1 Requirements
- Even if the protocol is permissionless, interacting with U.S.-linked entities or fiat rails creates AML obligations.
- Large withdrawals, merchant onboarding, and investor sales should include sanctions screening.

### 6.2 Recommended Approach
- Tiered KYC:
  - Deposits below $500/year: no verification.
  - Withdrawals above $1,000/year: KYC attestation.
  - Merchant rebates above threshold: full KYC + OFAC screening.
- Use a regulated identity provider or privacy-preserving attestation (e.g., ZK passport).

---

## 7. International

- **EU MiCA:** Asset-referenced tokens and e-money tokens have strict rules. Utility tokens are less regulated but still require whitepaper and issuer registration.
- **UK:** FCA registration may be required for cryptoasset businesses.
- **Other jurisdictions:** Vary widely; geo-block high-risk countries and obtain local counsel before expansion.

---

## 8. Entity Structure Recommendation (Preliminary)

1. **U.S. operating entity:** Wyoming DAO LLC or Delaware C-Corp for protocol development and grants.
2. **Foundation / Association (Cayman / Swiss / Singapore):** Non-profit vehicle for treasury and ecosystem grants, if non-U.S. structure is desired.
3. **Multisig + Timelock:** Legal entity should not have unilateral control over user funds.

**Final structure requires counsel.**

---

## 9. Action Items

| # | Task | Priority |
|---|------|----------|
| 1 | Retain U.S. securities counsel for token-classification memo | Critical |
| 2 | Retain tax counsel for entity and token-sale structuring | Critical |
| 3 | Select KYC/AML provider or privacy-preserving attestation vendor | High |
| 4 | Draft Terms of Use, Privacy Policy, Risk Disclosures | High |
| 5 | Geo-block restricted jurisdictions at launch | High |
| 6 | File entity formation documents | High |
| 7 | Ongoing compliance monitoring | Medium |

---

## 10. Disclaimer

This memo is for internal planning only. It does **not** constitute legal advice. All legal conclusions must be confirmed by qualified counsel in the relevant jurisdictions.
