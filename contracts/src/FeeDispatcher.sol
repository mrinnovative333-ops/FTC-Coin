// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "./interfaces/ITreasury.sol";
import "./FTC.sol";

/// @title FeeDispatcher
/// @notice Receives merchant transaction fees (in FTC) and routes them:
///   25% buyback & burn
///   35% to Treasury → child yield reserve
///   30% to Treasury → store operations fund
///   10% to Treasury → liquidity incentives
///
/// All percentages are in basis points and governance-adjustable within caps.
contract FeeDispatcher is AccessControl, Pausable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    // ────────────────────────── Roles ──────────────────────────
    bytes32 public constant FEE_COLLECTOR_ROLE = keccak256("FEE_COLLECTOR_ROLE");
    bytes32 public constant PARAMS_ADMIN_ROLE = keccak256("PARAMS_ADMIN_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    // ──────────────────────── Constants ────────────────────────
    uint256 public constant BPS_DENOM = 10000;
    /// @notice Total fee split must equal 100%.
    uint256 public constant TOTAL_BPS = 10000;

    // ──────────────────────── State ────────────────────────────
    FTC public immutable ftcToken;
    ITreasury public treasury;

    /// @notice Burn split in bps (e.g., 2500 = 25%).
    uint256 public burnBps = 2500;
    /// @notice Child yield reserve split in bps.
    uint256 public childYieldBps = 3500;
    /// @notice Store operations split in bps.
    uint256 public storeOpsBps = 3000;
    /// @notice Liquidity incentives split in bps.
    uint256 public liquidityBps = 1000;

    /// @notice Accumulated fees waiting to be distributed.
    uint256 public pendingFees;

    // ────────────────────────── Events ─────────────────────────
    event FeesReceived(address indexed source, uint256 amount);
    event FeesDistributed(uint256 burnAmount, uint256 childYieldAmount, uint256 storeOpsAmount, uint256 liquidityAmount);
    event SplitUpdated(uint256 burnBps, uint256 childYieldBps, uint256 storeOpsBps, uint256 liquidityBps);
    event TreasurySet(address indexed treasury);

    // ────────────────────────── Errors ─────────────────────────
    error ZeroAddress();
    error InvalidSplit();
    error NoPendingFees();
    error TreasuryNotSet();

    // ───────────────────────── Constructor ─────────────────────
    constructor(address _ftcToken) {
        if (_ftcToken == address(0)) revert ZeroAddress();
        ftcToken = FTC(_ftcToken);

        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(FEE_COLLECTOR_ROLE, msg.sender);
        _grantRole(PARAMS_ADMIN_ROLE, msg.sender);
        _grantRole(PAUSER_ROLE, msg.sender);
    }

    // ─────────────────────── Setters ──────────────────────────
    function setTreasury(address _treasury) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (_treasury == address(0)) revert ZeroAddress();
        treasury = ITreasury(_treasury);
        emit TreasurySet(_treasury);
    }

    /// @notice Update fee split. Must sum to 100%.
    function setSplit(
        uint256 _burnBps,
        uint256 _childYieldBps,
        uint256 _storeOpsBps,
        uint256 _liquidityBps
    ) external onlyRole(PARAMS_ADMIN_ROLE) {
        if (_burnBps + _childYieldBps + _storeOpsBps + _liquidityBps != TOTAL_BPS)
            revert InvalidSplit();
        burnBps = _burnBps;
        childYieldBps = _childYieldBps;
        storeOpsBps = _storeOpsBps;
        liquidityBps = _liquidityBps;
        emit SplitUpdated(_burnBps, _childYieldBps, _storeOpsBps, _liquidityBps);
    }

    // ─────────────────────── Fee Receipt ───────────────────────
    /// @notice Called by StoreDiscount or merchants to deposit fees.
    function depositFees(uint256 amount) external onlyRole(FEE_COLLECTOR_ROLE) whenNotPaused nonReentrant {
        if (amount == 0) revert NoPendingFees();
        ftcToken.transferFrom(msg.sender, address(this), amount);
        pendingFees += amount;
        emit FeesReceived(msg.sender, amount);
    }

    // ─────────────────────── Distribution ──────────────────────
    /// @notice Distribute pending fees according to the current split.
    function distribute() external whenNotPaused nonReentrant {
        if (address(treasury) == address(0)) revert TreasuryNotSet();
        uint256 total = pendingFees;
        if (total == 0) revert NoPendingFees();

        pendingFees = 0;

        uint256 burnAmount = (total * burnBps) / BPS_DENOM;
        uint256 childYieldAmount = (total * childYieldBps) / BPS_DENOM;
        uint256 storeOpsAmount = (total * storeOpsBps) / BPS_DENOM;
        uint256 liquidityAmount = total - burnAmount - childYieldAmount - storeOpsAmount;

        // Approve Treasury to burn the burn portion
        if (burnAmount > 0) {
            ftcToken.approve(address(treasury), burnAmount);
            treasury.buybackAndBurn(burnAmount);
        }

        // Send the rest to Treasury as fee revenue
        uint256 treasuryShare = childYieldAmount + storeOpsAmount + liquidityAmount;
        if (treasuryShare > 0) {
            IERC20(address(ftcToken)).safeTransfer(address(treasury), treasuryShare);
            treasury.recordDeposit(address(ftcToken), treasuryShare);
        }

        emit FeesDistributed(burnAmount, childYieldAmount, storeOpsAmount, liquidityAmount);
    }

    // ─────────────────────── Views ─────────────────────────────
    function getSplit() external view returns (uint256, uint256, uint256, uint256) {
        return (burnBps, childYieldBps, storeOpsBps, liquidityBps);
    }

    // ─────────────────────── Pause ─────────────────────────────
    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(PAUSER_ROLE) {
        _unpause();
    }
}
