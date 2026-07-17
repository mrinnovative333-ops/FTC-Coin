// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "./GuardianRegistry.sol";

/// @title ChildSavingsVault
/// @notice Holds each child's FTC savings in a non-transferable, age-gated vault.
///
/// Design (per TOKENOMICS_SPEC.md + DECISIONS.md):
///   - Payout windows: ages 5, 10, 15, 20, 25 (every 5 years from birth).
///   - Max 25% of current balance per checkpoint.
///   - Yield is a floating protocol parameter (NOT a guarantee).
///   - Base deposit: $250 equivalent; treasury 1:1 match for qualifying low-income families.
///   - KYC required when cumulative withdrawals exceed $5,000 (via GuardianRegistry).
contract ChildSavingsVault is AccessControl, Pausable, ReentrancyGuard {
    // ────────────────────────── Roles ──────────────────────────
    bytes32 public constant YIELD_SETTER_ROLE = keccak256("YIELD_SETTER_ROLE");
    bytes32 public constant MATCH_OPERATOR_ROLE = keccak256("MATCH_OPERATOR_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    // ──────────────────────── Constants ────────────────────────
    /// @notice First payout age.
    uint256 public constant PAYOUT_START_AGE = 5;
    /// @notice Payout interval (every 5 years).
    uint256 public constant PAYOUT_INTERVAL = 5;
    /// @notice Last payout age.
    uint256 public constant PAYOUT_END_AGE = 25;
    /// @notice Max % of balance withdrawable per checkpoint (25% = 2500 bps).
    uint256 public constant MAX_PAYOUT_BPS = 2500;
    /// @notice BPS denominator.
    uint256 public constant BPS_DENOM = 10000;
    /// @notice Seconds per year (approximate, for age calculation).
    uint256 public constant SECONDS_PER_YEAR = 365 days;

    // ──────────────────────── Data Types ───────────────────────
    struct Account {
        address guardian;          // parent/guardian wallet
        bytes32 childIdHash;       // links to GuardianRegistry
        uint256 birthTime;         // birth timestamp
        uint256 principal;         // total deposited (parent + match)
        uint256 balance;           // current balance including accrued yield
        uint256 lastAccrualTime;   // last time yield was accrued
        uint256 totalPayouts;      // cumulative amount withdrawn
        uint256 lastPayoutAge;     // age at last payout (prevents double-withdraw per checkpoint)
        bool    active;
    }

    // ──────────────────────── State ────────────────────────────
    IERC20 public immutable ftcToken;
    GuardianRegistry public immutable guardianRegistry;

    mapping(bytes32 => Account) public accounts;
    bytes32[] public childAccounts;
    uint256 public totalChildren;
    uint256 public totalDeposited;
    uint256 public totalMatched;
    uint256 public totalPaidOut;

    /// @notice Current annual yield rate in bps (e.g., 1100 = 11%).
    ///         Set by Treasury/governance. NOT a guarantee — floating parameter.
    uint256 public yieldRateBps;

    /// @notice Match cap per qualifying child (in FTC smallest units).
    uint256 public matchCapPerChild;

    /// @notice Child reserve token allocation (for matching deposits).
    address public childReserve;

    // ────────────────────────── Events ─────────────────────────
    event AccountCreated(bytes32 indexed childIdHash, address indexed guardian, uint256 birthTime);
    event Deposited(bytes32 indexed childIdHash, address indexed depositor, uint256 amount, uint256 matchAmount);
    event YieldAccrued(bytes32 indexed childIdHash, uint256 amount, uint256 newBalance);
    event Payout(bytes32 indexed childIdHash, address indexed guardian, uint256 amount, uint256 childAge);
    event YieldRateUpdated(uint256 oldRate, uint256 newRate);
    event MatchCapUpdated(uint256 oldCap, uint256 newCap);

    // ────────────────────────── Errors ─────────────────────────
    error AccountInactive();
    error AccountAlreadyExists();
    error GuardianNotVerified();
    error AgeNotAttested();
    error NotEligibleForPayout();
    error ExceedsMaxPayout();
    error AlreadyWithdrawnThisCheckpoint();
    error TransferFailed();

    // ───────────────────────── Constructor ─────────────────────
    constructor(
        address _ftcToken,
        address _guardianRegistry,
        address _childReserve,
        uint256 _yieldRateBps,
        uint256 _matchCapPerChild
    ) {
        ftcToken = IERC20(_ftcToken);
        guardianRegistry = GuardianRegistry(_guardianRegistry);
        childReserve = _childReserve;
        yieldRateBps = _yieldRateBps;
        matchCapPerChild = _matchCapPerChild;

        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(PAUSER_ROLE, msg.sender);
    }

    // ───────────────────── Account Creation ────────────────────
    /// @notice Create a savings account for a child. The child must be
    ///         registered in GuardianRegistry with age attested.
    function createAccount(bytes32 childIdHash) external whenNotPaused nonReentrant {
        if (accounts[childIdHash].active) revert AccountAlreadyExists();

        // Verify guardian is registered and identity-verified
        if (!guardianRegistry.isGuardian(msg.sender)) revert GuardianNotVerified();
        if (!guardianRegistry.isIdentityVerified(msg.sender)) revert GuardianNotVerified();
        if (!guardianRegistry.isAgeAttested(childIdHash)) revert AgeNotAttested();

        // Pull birth time from GuardianRegistry
        (, , uint256 birthTime, , , ) = guardianRegistry.children(childIdHash);

        accounts[childIdHash] = Account({
            guardian: msg.sender,
            childIdHash: childIdHash,
            birthTime: birthTime,
            principal: 0,
            balance: 0,
            lastAccrualTime: block.timestamp,
            totalPayouts: 0,
            lastPayoutAge: 0,
            active: true
        });

        childAccounts.push(childIdHash);
        totalChildren++;

        emit AccountCreated(childIdHash, msg.sender, birthTime);
    }

    // ──────────────────────── Deposits ─────────────────────────
    /// @notice Deposit FTC into a child's account.
    /// @param childIdHash The child's identifier hash.
    /// @param amount Amount of FTC to deposit (in smallest units).
    /// @param qualifyForMatch Whether this family qualifies for the low-income match.
    function deposit(
        bytes32 childIdHash,
        uint256 amount,
        bool qualifyForMatch
    ) external whenNotPaused nonReentrant {
        Account storage acct = accounts[childIdHash];
        if (!acct.active) revert AccountInactive();

        // Accrue yield before deposit
        _accrueYield(acct);

        // Transfer tokens from depositor to vault
        if (!ftcToken.transferFrom(msg.sender, address(this), amount))
            revert TransferFailed();

        acct.principal += amount;
        acct.balance += amount;
        totalDeposited += amount;

        // Treasury match for qualifying low-income families (1:1 up to cap)
        uint256 matchAmount = 0;
        if (qualifyForMatch && amount <= matchCapPerChild) {
            matchAmount = amount;
            if (ftcToken.balanceOf(childReserve) >= matchAmount) {
                if (ftcToken.transferFrom(childReserve, address(this), matchAmount)) {
                    acct.principal += matchAmount;
                    acct.balance += matchAmount;
                    totalMatched += matchAmount;
                }
            }
        }

        emit Deposited(childIdHash, msg.sender, amount, matchAmount);
    }

    // ──────────────────── Yield Accrual ────────────────────────
    /// @notice Accrue yield for a specific child account.
    function accrueYield(bytes32 childIdHash) external whenNotPaused nonReentrant {
        Account storage acct = accounts[childIdHash];
        if (!acct.active) revert AccountInactive();
        _accrueYield(acct);
    }

    function _accrueYield(Account storage acct) internal {
        if (acct.balance == 0 || yieldRateBps == 0) {
            acct.lastAccrualTime = block.timestamp;
            return;
        }

        uint256 timeElapsed = block.timestamp - acct.lastAccrualTime;
        if (timeElapsed == 0) return;

        // Simple yield: balance * rate * timeElapsed / (1 year) / BPS_DENOM
        uint256 accrued = (acct.balance * yieldRateBps * timeElapsed)
            / (BPS_DENOM * SECONDS_PER_YEAR);

        acct.balance += accrued;
        acct.lastAccrualTime = block.timestamp;

        emit YieldAccrued(acct.childIdHash, accrued, acct.balance);
    }

    // ──────────────────────── Payouts ──────────────────────────
    /// @notice Request a payout for a child. Only the guardian can call.
    ///         Must be at a 5-year checkpoint (ages 5, 10, 15, 20, 25).
    ///         Max 25% of current balance per checkpoint.
    function requestPayout(bytes32 childIdHash, uint256 amount)
        external
        whenNotPaused
        nonReentrant
    {
        Account storage acct = accounts[childIdHash];
        if (!acct.active) revert AccountInactive();
        if (acct.guardian != msg.sender) revert GuardianNotVerified();

        // Check age eligibility
        uint256 childAge = _getAge(acct);
        if (!_isPayoutEligible(childAge)) revert NotEligibleForPayout();
        if (acct.lastPayoutAge == childAge) revert AlreadyWithdrawnThisCheckpoint();

        // Accrue yield before payout
        _accrueYield(acct);

        // Check max payout (25% of balance)
        uint256 maxPayoutAmount = (acct.balance * MAX_PAYOUT_BPS) / BPS_DENOM;
        if (amount > maxPayoutAmount) revert ExceedsMaxPayout();
        if (amount == 0 || amount > acct.balance) revert NotEligibleForPayout();

        // KYC check via GuardianRegistry
        // This reverts if KYC is required but not yet attested
        guardianRegistry.recordWithdrawal(childIdHash, amount);

        // Transfer to guardian
        acct.balance -= amount;
        acct.totalPayouts += amount;
        acct.lastPayoutAge = childAge;
        totalPaidOut += amount;

        if (!ftcToken.transfer(msg.sender, amount))
            revert TransferFailed();

        emit Payout(childIdHash, msg.sender, amount, childAge);
    }

    // ──────────────────────── Views ────────────────────────────
    /// @notice Get the current age of a child in years.
    function _getAge(Account storage acct) internal view returns (uint256) {
        if (block.timestamp < acct.birthTime) return 0;
        return (block.timestamp - acct.birthTime) / SECONDS_PER_YEAR;
    }

    /// @notice Check if a child is eligible for a payout at their current age.
    function _isPayoutEligible(uint256 age) internal pure returns (bool) {
        if (age < PAYOUT_START_AGE || age > PAYOUT_END_AGE) return false;
        return (age % PAYOUT_INTERVAL) == 0;
    }

    /// @notice Public helper: is this child currently at a payout checkpoint?
    function isPayoutEligible(bytes32 childIdHash) external view returns (bool) {
        Account storage acct = accounts[childIdHash];
        if (!acct.active) return false;
        uint256 age = _getAge(acct);
        return _isPayoutEligible(age);
    }

    /// @notice Get full account details.
    function getAccount(bytes32 childIdHash) external view returns (
        address guardian,
        uint256 birthTime,
        uint256 principal,
        uint256 balance,
        uint256 totalPayouts,
        uint256 lastPayoutAge,
        bool active
    ) {
        Account storage acct = accounts[childIdHash];
        return (
            acct.guardian,
            acct.birthTime,
            acct.principal,
            acct.balance,
            acct.totalPayouts,
            acct.lastPayoutAge,
            acct.active
        );
    }

    /// @notice Max withdrawable amount at current checkpoint.
    function maxPayout(bytes32 childIdHash) external view returns (uint256) {
        Account storage acct = accounts[childIdHash];
        return (acct.balance * MAX_PAYOUT_BPS) / BPS_DENOM;
    }

    function getChildAge(bytes32 childIdHash) external view returns (uint256) {
        Account storage acct = accounts[childIdHash];
        return _getAge(acct);
    }

    // ──────────────────── Admin / Governance ───────────────────
    /// @notice Set the floating yield rate (YIELD_SETTER_ROLE / Treasury).
    function setYieldRate(uint256 newRateBps) external onlyRole(YIELD_SETTER_ROLE) {
        emit YieldRateUpdated(yieldRateBps, newRateBps);
        yieldRateBps = newRateBps;
    }

    /// @notice Set the match cap per qualifying child (MATCH_OPERATOR_ROLE).
    function setMatchCap(uint256 newCap) external onlyRole(MATCH_OPERATOR_ROLE) {
        emit MatchCapUpdated(matchCapPerChild, newCap);
        matchCapPerChild = newCap;
    }

    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(PAUSER_ROLE) {
        _unpause();
    }
}