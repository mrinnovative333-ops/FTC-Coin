// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/// @title GuardianRegistry
/// @notice Maps guardians (parents) to child accounts and manages
///         lightweight KYC/age attestations.
///
/// Design (per DECISIONS.md #3):
///   - Guardian identity verified at account creation.
///   - Full KYC attestation only when cumulative withdrawals cross $5,000.
///   - No full KYC for small accounts or initial deposits.
contract GuardianRegistry is AccessControl, Pausable, ReentrancyGuard {
    // ────────────────────────── Roles ──────────────────────────
    bytes32 public constant KYC_ISSUER_ROLE = keccak256("KYC_ISSUER_ROLE");
    bytes32 public constant AGE_ATTESTOR_ROLE = keccak256("AGE_ATTESTOR_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    // ──────────────────────── Constants ────────────────────────
    /// @notice KYC threshold: $5,000 USD-equivalent in cumulative withdrawals.
    ///         Set as a governance parameter; stored as FTC-wei equivalent
    ///         (updated via oracle / governance).
    uint256 public kycThreshold; // in FTC smallest unit (1e18 = 1 FTC)

    // ──────────────────────── Data Types ───────────────────────
    struct Guardian {
        address wallet;
        bool   registered;
        bool   identityVerified; // lightweight guardian identity at creation
        uint256 childCount;
        bytes32[] childIds;
    }

    struct ChildRecord {
        bytes32 childIdHash;      // privacy-preserving hash (not raw PII on-chain)
        address guardian;         // parent/guardian wallet
        uint256 birthTimestamp;   // Unix timestamp of birth
        bool    ageAttested;      // birth timestamp confirmed by attester
        bool    kycVerified;      // full KYC for large withdrawals
        uint256 cumulativeWithdrawals; // running total for KYC threshold check
    }

    // ──────────────────────── State ────────────────────────────
    mapping(address => Guardian) public guardians;
    mapping(bytes32 => ChildRecord) public children;
    // Double-link: guardian => childIdHash => exists
    mapping(address => mapping(bytes32 => bool)) public guardianHasChild;

    // ────────────────────────── Events ─────────────────────────
    event GuardianRegistered(address indexed guardian, bool identityVerified);
    event ChildRegistered(
        bytes32 indexed childIdHash,
        address indexed guardian,
        uint256 birthTimestamp
    );
    event AgeAttested(bytes32 indexed childIdHash, address indexed attestor);
    event KYCAttested(bytes32 indexed childIdHash, address indexed issuer);
    event KYCThresholdUpdated(uint256 oldThreshold, uint256 newThreshold);

    // ────────────────────────── Errors ─────────────────────────
    error GuardianNotRegistered();
    error GuardianIdentityNotVerified();
    error ChildAlreadyExists();
    error ChildNotFound();
    error NotAuthorizedForChild();
    error AgeNotAttested();
    error KYCRequired();

    // ───────────────────────── Constructor ─────────────────────
    constructor(uint256 _kycThreshold) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(PAUSER_ROLE, msg.sender);
        kycThreshold = _kycThreshold;
    }

    // ───────────────────── Guardian Registration ───────────────
    /// @notice Register a guardian. Identity verification happens off-chain
    ///         (via partner) but the result is recorded here.
    /// @param guardian The guardian's wallet address.
    /// @param identityVerified Whether guardian identity was verified off-chain.
    function registerGuardian(
        address guardian,
        bool identityVerified
    ) external onlyRole(KYC_ISSUER_ROLE) whenNotPaused nonReentrant {
        if (guardian == address(0)) revert GuardianNotRegistered();

        guardians[guardian] = Guardian({
            wallet: guardian,
            registered: true,
            identityVerified: identityVerified,
            childCount: 0,
            childIds: new bytes32[](0)
        });

        emit GuardianRegistered(guardian, identityVerified);
    }

    // ─────────────────── Child Registration ────────────────────
    /// @notice Register a child under a guardian. The guardian must be
    ///         registered and identity-verified.
    /// @param childIdHash A hash of the child's identifying info (off-chain).
    /// @param birthTimestamp Unix timestamp of child's birth.
    function registerChild(
        bytes32 childIdHash,
        uint256 birthTimestamp
    ) external whenNotPaused nonReentrant {
        Guardian storage g = guardians[msg.sender];
        if (!g.registered) revert GuardianNotRegistered();
        if (!g.identityVerified) revert GuardianIdentityNotVerified();
        if (children[childIdHash].guardian != address(0)) revert ChildAlreadyExists();
        if (birthTimestamp == 0 || birthTimestamp > block.timestamp)
            revert GuardianNotRegistered(); // invalid birth time

        children[childIdHash] = ChildRecord({
            childIdHash: childIdHash,
            guardian: msg.sender,
            birthTimestamp: birthTimestamp,
            ageAttested: false,
            kycVerified: false,
            cumulativeWithdrawals: 0
        });

        g.childIds.push(childIdHash);
        g.childCount++;
        guardianHasChild[msg.sender][childIdHash] = true;

        emit ChildRegistered(childIdHash, msg.sender, birthTimestamp);
    }

    // ─────────────────────── Attestations ──────────────────────
    /// @notice Attest a child's age/birth timestamp (AGE_ATTESTOR_ROLE).
    function attestAge(
        bytes32 childIdHash
    ) external onlyRole(AGE_ATTESTOR_ROLE) whenNotPaused {
        if (children[childIdHash].guardian == address(0)) revert ChildNotFound();
        children[childIdHash].ageAttested = true;
        emit AgeAttested(childIdHash, msg.sender);
    }

    /// @notice Full KYC attestation for a child account (KYC_ISSUER_ROLE).
    ///         Required when cumulative withdrawals exceed kycThreshold.
    function attestKYC(
        bytes32 childIdHash
    ) external onlyRole(KYC_ISSUER_ROLE) whenNotPaused {
        if (children[childIdHash].guardian == address(0)) revert ChildNotFound();
        children[childIdHash].kycVerified = true;
        emit KYCAttested(childIdHash, msg.sender);
    }

    // ─────────────────── Withdrawal Tracking ───────────────────
    /// @notice Called by ChildSavingsVault before a payout to record
    ///         cumulative withdrawals and enforce KYC threshold.
    /// @dev    Reverts if KYC is required but not yet attested.
    function recordWithdrawal(
        bytes32 childIdHash,
        uint256 amount
    ) external onlyRole(KYC_ISSUER_ROLE) returns (bool kycNeeded) {
        ChildRecord storage child = children[childIdHash];
        if (child.guardian == address(0)) revert ChildNotFound();

        child.cumulativeWithdrawals += amount;

        if (child.cumulativeWithdrawals >= kycThreshold && !child.kycVerified) {
            revert KYCRequired();
        }
        return false; // KYC already done or not yet needed
    }

    /// @notice Check if a withdrawal would trigger KYC requirement.
    function wouldRequireKYC(
        bytes32 childIdHash,
        uint256 amount
    ) external view returns (bool) {
        ChildRecord storage child = children[childIdHash];
        if (child.guardian == address(0)) return false;
        uint256 newTotal = child.cumulativeWithdrawals + amount;
        return newTotal >= kycThreshold && !child.kycVerified;
    }

    // ──────────────────────── Views ────────────────────────────
    function isGuardian(address guardian) external view returns (bool) {
        return guardians[guardian].registered;
    }

    function isIdentityVerified(address guardian) external view returns (bool) {
        return guardians[guardian].identityVerified;
    }

    function getGuardianChildren(address guardian) external view returns (bytes32[] memory) {
        return guardians[guardian].childIds;
    }

    function getChildGuardian(bytes32 childIdHash) external view returns (address) {
        return children[childIdHash].guardian;
    }

    function isAgeAttested(bytes32 childIdHash) external view returns (bool) {
        return children[childIdHash].ageAttested;
    }

    function isKYCVerified(bytes32 childIdHash) external view returns (bool) {
        return children[childIdHash].kycVerified;
    }

    // ──────────────────── Admin / Governance ───────────────────
    function setKycThreshold(uint256 newThreshold) external onlyRole(DEFAULT_ADMIN_ROLE) {
        emit KYCThresholdUpdated(kycThreshold, newThreshold);
        kycThreshold = newThreshold;
    }

    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(PAUSER_ROLE) {
        _unpause();
    }
}