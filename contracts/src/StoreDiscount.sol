// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "./interfaces/IFeeDispatcher.sol";
import "./FTC.sol";

/// @title StoreDiscount
/// @notice Partner-merchant discount network for FTC.
///
/// Design:
///   - Merchants register with a max discount (10–30%) and monthly rebate cap.
///   - At checkout, consumer pays discounted price; merchant later claims rebate.
///   - Merchant pays 2% transaction fee on gross sale, forwarded to FeeDispatcher.
///   - Discount rate scales globally with total protocol adoption.
contract StoreDiscount is AccessControl, Pausable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    // ────────────────────────── Roles ──────────────────────────
    bytes32 public constant MERCHANT_REGISTRAR_ROLE = keccak256("MERCHANT_REGISTRAR_ROLE");
    bytes32 public constant REBATE_ADMIN_ROLE = keccak256("REBATE_ADMIN_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    // ──────────────────────── Constants ────────────────────────
    uint256 public constant BPS_DENOM = 10000;
    uint256 public constant MERCHANT_FEE_BPS = 200; // 2%
    /// @notice Minimum discount at launch.
    uint256 public constant MIN_DISCOUNT_BPS = 1000; // 10%
    /// @notice Maximum discount at scale.
    uint256 public constant MAX_DISCOUNT_BPS = 3000; // 30%
    /// @notice Total children required to reach max discount.
    uint256 public constant SCALE_CHILDREN = 10_000_000;

    // ──────────────────────── State ────────────────────────────
    FTC public immutable ftcToken;
    IFeeDispatcher public immutable feeDispatcher;

    struct Merchant {
        bool registered;
        uint256 maxDiscountBps;
        uint256 monthlyRebateCap;
        uint256 accruedRebate;
        uint256 lifetimeVolume;
        uint256 lifetimeFees;
    }

    mapping(address => Merchant) public merchants;
    uint256 public totalProtocolChildren;

    // ────────────────────────── Events ─────────────────────────
    event MerchantRegistered(address indexed merchant, uint256 maxDiscountBps, uint256 rebateCap);
    event MerchantUpdated(address indexed merchant, uint256 maxDiscountBps, uint256 rebateCap);
    event PaymentProcessed(
        address indexed buyer,
        address indexed merchant,
        uint256 grossAmount,
        uint256 discountAmount,
        uint256 feeAmount,
        uint256 netAmount
    );
    event RebateClaimed(address indexed merchant, uint256 amount);
    event TotalChildrenUpdated(uint256 total);

    // ────────────────────────── Errors ─────────────────────────
    error ZeroAddress();
    error NotRegisteredMerchant();
    error DiscountTooHigh();
    error RebateCapExceeded();
    error NothingToClaim();

    // ───────────────────────── Constructor ─────────────────────
    constructor(address _ftcToken, address _feeDispatcher) {
        if (_ftcToken == address(0) || _feeDispatcher == address(0)) revert ZeroAddress();
        ftcToken = FTC(_ftcToken);
        feeDispatcher = IFeeDispatcher(_feeDispatcher);

        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MERCHANT_REGISTRAR_ROLE, msg.sender);
        _grantRole(REBATE_ADMIN_ROLE, msg.sender);
        _grantRole(PAUSER_ROLE, msg.sender);
    }

    // ───────────────────── Merchant Management ─────────────────
    function registerMerchant(
        address merchant,
        uint256 maxDiscountBps,
        uint256 monthlyRebateCap
    ) external onlyRole(MERCHANT_REGISTRAR_ROLE) whenNotPaused {
        if (merchant == address(0)) revert ZeroAddress();
        if (maxDiscountBps < MIN_DISCOUNT_BPS || maxDiscountBps > MAX_DISCOUNT_BPS)
            revert DiscountTooHigh();

        merchants[merchant] = Merchant({
            registered: true,
            maxDiscountBps: maxDiscountBps,
            monthlyRebateCap: monthlyRebateCap,
            accruedRebate: 0,
            lifetimeVolume: 0,
            lifetimeFees: 0
        });

        emit MerchantRegistered(merchant, maxDiscountBps, monthlyRebateCap);
    }

    function updateMerchant(
        address merchant,
        uint256 maxDiscountBps,
        uint256 monthlyRebateCap
    ) external onlyRole(MERCHANT_REGISTRAR_ROLE) whenNotPaused {
        if (!merchants[merchant].registered) revert NotRegisteredMerchant();
        if (maxDiscountBps < MIN_DISCOUNT_BPS || maxDiscountBps > MAX_DISCOUNT_BPS)
            revert DiscountTooHigh();

        Merchant storage m = merchants[merchant];
        m.maxDiscountBps = maxDiscountBps;
        m.monthlyRebateCap = monthlyRebateCap;
        emit MerchantUpdated(merchant, maxDiscountBps, monthlyRebateCap);
    }

    // ─────────────────────── Discount Logic ────────────────────
    /// @notice Current global discount, scaling from 10% to 30% based on adoption.
    function currentGlobalDiscountBps() public view returns (uint256) {
        if (totalProtocolChildren >= SCALE_CHILDREN) return MAX_DISCOUNT_BPS;
        return MIN_DISCOUNT_BPS
            + ((MAX_DISCOUNT_BPS - MIN_DISCOUNT_BPS) * totalProtocolChildren) / SCALE_CHILDREN;
    }

    /// @notice Effective discount for a merchant = lower of merchant max and global discount.
    function effectiveDiscountBps(address merchant) public view returns (uint256) {
        Merchant storage m = merchants[merchant];
        if (!m.registered) revert NotRegisteredMerchant();
        uint256 global = currentGlobalDiscountBps();
        return m.maxDiscountBps < global ? m.maxDiscountBps : global;
    }

    // ─────────────────────── Payment Flow ──────────────────────
    /// @notice Process a consumer payment at a merchant.
    /// @param buyer Address paying with FTC.
    /// @param merchant Registered merchant.
    /// @param grossAmount Pre-discount amount in FTC.
    function processPayment(
        address buyer,
        address merchant,
        uint256 grossAmount
    ) external whenNotPaused nonReentrant {
        if (buyer == address(0) || merchant == address(0)) revert ZeroAddress();
        Merchant storage m = merchants[merchant];
        if (!m.registered) revert NotRegisteredMerchant();

        uint256 discountBps = effectiveDiscountBps(merchant);
        uint256 discountAmount = (grossAmount * discountBps) / BPS_DENOM;
        uint256 feeAmount = (grossAmount * MERCHANT_FEE_BPS) / BPS_DENOM;
        uint256 netAmount = grossAmount - discountAmount - feeAmount;

        if (m.accruedRebate + discountAmount > m.monthlyRebateCap) revert RebateCapExceeded();

        // Buyer pays grossAmount to this contract
        ftcToken.transferFrom(buyer, address(this), grossAmount);

        // Merchant receives net after discount and fee
        IERC20(address(ftcToken)).safeTransfer(merchant, netAmount);

        // Fee sent to FeeDispatcher (must be pre-approved)
        IERC20(address(ftcToken)).forceApprove(address(feeDispatcher), feeAmount);
        feeDispatcher.depositFees(feeAmount);

        // Discount accrued as rebate claimable from Treasury later
        m.accruedRebate += discountAmount;
        m.lifetimeVolume += grossAmount;
        m.lifetimeFees += feeAmount;

        emit PaymentProcessed(buyer, merchant, grossAmount, discountAmount, feeAmount, netAmount);
    }

    // ─────────────────────── Rebate Claims ─────────────────────
    /// @notice Merchant claims accrued rebate from this contract.
    /// @dev    In production, Treasury.fundStoreSubsidy() would send rebates.
    ///         For the MVP this contract holds accumulated discount tokens.
    function claimRebate() external whenNotPaused nonReentrant {
        Merchant storage m = merchants[msg.sender];
        if (!m.registered) revert NotRegisteredMerchant();
        uint256 amount = m.accruedRebate;
        if (amount == 0) revert NothingToClaim();

        m.accruedRebate = 0;
        IERC20(address(ftcToken)).safeTransfer(msg.sender, amount);

        emit RebateClaimed(msg.sender, amount);
    }

    // ─────────────────────── Adoption Oracle ─────────────────
    /// @notice Update total protocol children to scale discounts.
    ///         In production, this could be read from ChildSavingsVault.
    function updateTotalChildren(uint256 total) external onlyRole(REBATE_ADMIN_ROLE) {
        totalProtocolChildren = total;
        emit TotalChildrenUpdated(total);
    }

    // ─────────────────────── Views ─────────────────────────────
    function getMerchant(address merchant) external view returns (Merchant memory) {
        return merchants[merchant];
    }

    // ─────────────────────── Pause ─────────────────────────────
    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(PAUSER_ROLE) {
        _unpause();
    }
}
