# FTC Testnet MVP Roadmap

**Version:** 0.2
**Updated:** 2026-07-17
**Target Network:** Base Sepolia (testnet) → Base (mainnet)
**Tooling:** Foundry (primary) + Hardhat (deployment scripts), OpenZeppelin v5.1, py-solc-x for compilation

---

## Resolved Decisions

All 6 open decisions from the prior session are now resolved (see `docs/DECISIONS.md`):
1. **L2:** Base
2. **Legal:** Delaware C-Corp + Wyoming DAO LLC + Swiss foundation (pending counsel)
3. **KYC:** Lightweight — guardian ID at creation, full KYC at $5,000+ cumulative withdrawals
4. **Stores:** Partner-merchant network first, no owned stores
5. **Raise:** $8–15M public sale, $60–80M target initial market cap
6. **Deposit:** $250 base, 1:1 treasury match for qualifying low-income families (up to $500 effective)

---

## Contracts Delivered

| Contract | File | Status |
|----------|------|--------|
| FTC.sol | `src/FTC.sol` | ERC-20, 21B fixed supply, genesis allocation, burn role, pausable |
| GuardianRegistry.sol | `src/GuardianRegistry.sol` | Guardian/child registration, age + KYC attestation, withdrawal tracking |
| ChildSavingsVault.sol | `src/ChildSavingsVault.sol` | Age-gated 5-year payouts, 25% max per checkpoint, yield accrual, deposit matching |

### Not Yet Implemented (Phase 1+)
- Treasury.sol — yield strategies, store subsidies, buyback-and-burn
- FeeDispatcher.sol — merchant fee splitting (25% burn / 35% yield / 30% stores / 10% liquidity)
- StoreDiscount.sol — merchant registry and discount logic

---

## Testnet Deployment Plan

### Step 1: Local Compilation & Tests (Week 5)
1. Compile all contracts with solc 0.8.24 (via Foundry or py-solc-x)
2. Write unit tests:
   - FTC: genesis allocation, burn, pause, transfer
   - GuardianRegistry: registration, attestation, KYC threshold
   - ChildSavingsVault: deposit, yield accrual, age-gated payout, match
3. Run fuzz tests on payout eligibility and max-payout boundary

### Step 2: Base Sepolia Deployment (Week 6)
1. Deploy FTC.sol with test allocation addresses
2. Deploy GuardianRegistry.sol (set KYC threshold = 5000 FTC)
3. Deploy ChildSavingsVault.sol (set yield rate = 1100 bps, match cap = 250 FTC)
4. Grant roles:
   - YIELD_SETTER_ROLE → Treasury multisig
   - KYC_ISSUER_ROLE → designated attestation service
   - AGE_ATTESTOR_ROLE → designated age verification service
5. Verify contracts on Basescan

### Step 3: Integration Testing (Weeks 7–8)
1. End-to-end flow: register guardian → register child → attest age → create vault → deposit → accrue yield → payout at checkpoint
2. Gas profiling for all core operations
3. Edge cases:
   - Payout before age 5 (should revert)
   - Double payout at same checkpoint (should revert)
   - Payout > 25% of balance (should revert)
   - KYC triggered at $5,000 cumulative (should revert without attestation)
   - Deposit match for qualifying family (1:1 up to cap)
   - Pause/unpause flows

### Step 4: Demo dApp (Weeks 9–10)
1. Simple web interface:
   - Guardian registration + child registration
   - Deposit FTC, view child balance
   - Simulate time progression to see payout eligibility
2. Deploy on Base Sepolia with test FTC tokens

### Step 5: Beta Campaign (Weeks 10–12)
1. Onboard 500–1,000 simulated child accounts on testnet
2. Test with real guardian wallets (volunteer families)
3. Collect analytics: gas costs, deposit patterns, payout timing

---

## Audit Gates

- **Before testnet:** Internal security review (ReentrancyGuard, AccessControl, Pausable on all contracts)
- **Before mainnet:** Two independent audit firms (OpenZeppelin / Trail of Bits / Spearbit)
- **Continuous:** Immunefi bug bounty post-mainnet

---

## Role Assignments at Launch

| Role | Holder | Purpose |
|------|--------|---------|
| DEFAULT_ADMIN_ROLE | Treasury multisig (Gnosis Safe) | Top-level governance |
| BURNER_ROLE (FTC) | Treasury / FeeDispatcher | Burn 25% of merchant fees |
| PAUSER_ROLE | Treasury multisig | Emergency pause |
| KYC_ISSUER_ROLE (GuardianRegistry) | Designated KYC partner | Guardian identity + child KYC attestation |
| AGE_ATTESTOR_ROLE (GuardianRegistry) | Designated age verifier | Confirm child birth timestamp |
| YIELD_SETTER_ROLE (ChildSavingsVault) | Treasury multisig | Set floating yield rate |
| MATCH_OPERATOR_ROLE (ChildSavingsVault) | Treasury multisig | Set match cap for low-income families |

---

## Key Parameters at Launch

| Parameter | Initial Value | Adjustable by |
|-----------|--------------|---------------|
| Yield rate | 1100 bps (11%) | YIELD_SETTER_ROLE |
| KYC threshold | 5,000 FTC (~$5,000) | Governance |
| Match cap per child | 250 FTC (~$250) | MATCH_OPERATOR_ROLE |
| Max payout per checkpoint | 2500 bps (25%) | Immutable (constant) |
| Payout ages | 5, 10, 15, 20, 25 | Immutable (constant) |

---

## Next Steps

1. ✅ Decisions documented → `docs/DECISIONS.md`
2. ✅ Core contracts written → `src/FTC.sol`, `src/GuardianRegistry.sol`, `src/ChildSavingsVault.sol`
3. ✅ Contracts compile (pending verification)
4. ⬜ Write unit tests
5. ⬜ Deploy to Base Sepolia
6. ⬜ Build demo dApp
7. ⬜ Engage securities counsel for token classification memo
8. ⬜ Implement Treasury.sol, FeeDispatcher.sol, StoreDiscount.sol (Phase 1+)