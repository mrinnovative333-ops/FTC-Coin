# FTC Smart Contract Architecture

**Version:** 0.2
**Target Network:** Base L2 (Coinbase)
**Language:** Solidity 0.8.24
**Tooling:** Foundry, OpenZeppelin Contracts, Chainlink Price Feeds

---

## 1. Design Philosophy

- **Minimal on-chain state:** Keep child-account ledgers and payout rules on-chain; heavy metadata (KYC attestations, store inventory) off-chain.
- **Upgrade-governed:** Core contracts use UUPS proxy pattern with a multisig + timelock; later transition to on-chain DAO (Wyoming DAO LLC).
- **Compliance-aware:** Lightweight guardian identity at account creation; full KYC only for cumulative withdrawals above $5,000.
- **No guaranteed yield:** Yield is a floating protocol parameter based on treasury returns and fees, not a contractual debt.
- **Partner-merchant stores:** No protocol-owned physical stores; merchant discounts are funded by fees and treasury yield.

---

## 2. Contract Map

```
┌─────────────────────────────────────────────────────────────┐
│                     FTCToken (ERC-20)                       │
│  - 21B fixed supply minted at genesis                        │
│  - 25% of merchant fees burned via BURNER_ROLE               │
└───────────────┬─────────────────────────────┬───────────────┘
                │                             │
    ┌───────────▼──────────┐      ┌───────────▼──────────┐
    │  ChildSavingsVault   │      │      Treasury        │
    │ - age-gated vaults   │      │ - yield strategies   │
    │ - 5-year payouts     │      │ - store subsidies    │
    │ - 1:1 low-income match│     │ - fee distribution   │
    └───────────┬──────────┘      └───────────┬──────────┘
                │                             │
    ┌───────────▼──────────┐      ┌───────────▼──────────┐
    │  GuardianRegistry    │      │   StoreDiscount      │
    │ - guardian identity  │      │ - merchant registry  │
    │ - age/KYC threshold  │      │ - discount logic     │
    └──────────────────────┘      └───────────┬──────────┘
                                              │
                              ┌───────────────▼───────────────┐
                              │        FeeDispatcher         │
                              │ - receives merchant fees     │
                              │ - 25% burn, 35% yield, 30%   │
                              │   stores, 10% liquidity      │
                              └───────────────────────────────┘
```

---

## 3. Core Contracts (Status)

| Contract | Status | File |
|----------|--------|------|
| `FTC.sol` | Built | `src/FTC.sol` |
| `GuardianRegistry.sol` | Built | `src/GuardianRegistry.sol` |
| `ChildSavingsVault.sol` | Built | `src/ChildSavingsVault.sol` |
| `Treasury.sol` | To build | `src/Treasury.sol` |
| `FeeDispatcher.sol` | To build | `src/FeeDispatcher.sol` |
| `StoreDiscount.sol` | To build | `src/StoreDiscount.sol` |

---

## 4. Contract Details

### 4.1 `FTC.sol` — For The Children Token

- 21B fixed supply minted once at genesis across 7 buckets.
- No future minting.
- `BURNER_ROLE` held by Treasury/FeeDispatcher for deflationary burns.
- Pausable transfers in emergencies.

### 4.2 `GuardianRegistry.sol`

- Maps guardians to child accounts using privacy-preserving `childIdHash`.
- Lightweight guardian identity verified at registration.
- Full KYC attestation required only when cumulative withdrawals exceed $5,000.
- Age attestation by authorized attestors.

### 4.3 `ChildSavingsVault.sol`

- Holds each child's FTC in a non-transferable, age-gated vault.
- Payout windows: ages 5, 10, 15, 20, 25.
- Max 25% of current balance per checkpoint.
- Floating yield rate set by Treasury/governance.
- 1:1 treasury match for qualifying low-income families (up to $250 equivalent).
- KYC check via `GuardianRegistry` before payout.

### 4.4 `Treasury.sol` (To Build)

- Holds protocol-owned FTC, stablecoins, and yield-bearing assets.
- Invests into whitelisted ERC-4626 strategies (liquid staking, money markets, T-bill tokens).
- Harvests yield and sends portion to `ChildSavingsVault` to fund yield.
- Funds store subsidies and buyback-and-burn via `FeeDispatcher`.
- Multisig + timelock on all capital moves.

### 4.5 `FeeDispatcher.sol` (To Build)

- Receives merchant fees (in FTC or stablecoins from `StoreDiscount`).
- Splits fees:
  - 25% → buyback-and-burn FTC.
  - 35% → Treasury → child yield reserve.
  - 30% → store operations fund.
  - 10% → liquidity incentives.
- Callable by merchants or keepers.

### 4.6 `StoreDiscount.sol` (To Build)

- Registry of partner merchants.
- Applies consumer discount at point of sale (10–30%, scaling with adoption).
- Charges merchant fee (2%) and forwards to `FeeDispatcher`.
- Allows merchants to claim rebate from Treasury for discounts given.
- Integrates Chainlink FTC/USD price feed.

---

## 5. Security Patterns

1. **Re-entrancy:** `ReentrancyGuard` on all payout, deposit, and merchant-claim functions.
2. **Access control:** `AccessControl` with role separation.
3. **Timelock:** All Treasury moves and parameter changes through 48-hour timelock.
4. **Pausing:** `Pausable` on deposits and payouts for emergency response.
5. **Oracle failure:** Chainlink stale-price checks; fallback TWAP.

---

## 6. Deployment Targets

1. **Base Sepolia testnet:** MVP and public beta.
2. **Base mainnet:** v1 launch after two independent audits.

---

## 7. Open Questions

1. Should Treasury be a single contract or split into sub-treasuries (yield, store ops, reserves)?
2. Should FeeDispatcher accept fees only in FTC, or also in stablecoins with automatic DEX swap?
3. Should StoreDiscount discounts be set per-merchant or globally?
4. Do we need a separate `YieldReserve` contract, or can Treasury manage child yield directly?
