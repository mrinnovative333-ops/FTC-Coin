// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "./interfaces/IYieldStrategy.sol";
import "./FTC.sol";

/// @title Treasury
/// @notice Protocol treasury for FTC. Holds assets, deploys capital into
///         whitelisted yield strategies, funds store subsidies, and executes
///         buyback-and-burn in coordination with FeeDispatcher.
///
/// Design choices:
///   - All capital moves require TREASURY_MANAGER_ROLE and go through timelock off-chain.
///   - Only whitelisted ERC-4626-style strategies can receive funds.
///   - Yield is harvested and sent to ChildSavingsVault to fund the floating yieldRate.
///   - No direct user withdrawals; only protocol-outflows to approved contracts.
contract Treasury is AccessControl, Pausable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    // ────────────────────────── Roles ──────────────────────────
    bytes32 public constant TREASURY_MANAGER_ROLE = keccak256("TREASURY_MANAGER_ROLE");
    bytes32 public constant YIELD_HARVESTER_ROLE = keccak256("YIELD_HARVESTER_ROLE");
    bytes32 public constant FEE_DISPATCHER_ROLE = keccak256("FEE_DISPATCHER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    // ──────────────────────── State ────────────────────────────
    FTC public immutable ftcToken;
    address public childSavingsVault;

    /// @notice Whitelisted yield strategies (ERC-4626 compatible).
    mapping(address => bool) public whitelistedStrategies;
    /// @notice Assets deployed per strategy (in token units).
    mapping(address => uint256) public allocations;

    /// @notice Direct holdings of stablecoins / other assets not in strategies.
    mapping(address => uint256) public directHoldings;

    // ────────────────────────── Events ─────────────────────────
    event StrategyWhitelisted(address indexed strategy);
    event StrategyRemoved(address indexed strategy);
    event Invested(address indexed strategy, address indexed token, uint256 amount);
    event Divested(address indexed strategy, address indexed token, uint256 amount);
    event YieldHarvested(address indexed token, uint256 amount, address indexed to);
    event StoreSubsidy(address indexed merchant, address indexed token, uint256 amount);
    event BuybackAndBurn(uint256 ftcAmount);
    event ChildSavingsVaultSet(address indexed vault);

    // ────────────────────────── Errors ─────────────────────────
    error ZeroAddress();
    error StrategyNotWhitelisted();
    error StrategyAlreadyWhitelisted();
    error InsufficientBalance();
    error TransferFailed();
    error InvalidAmount();

    // ───────────────────────── Constructor ─────────────────────
    constructor(address _ftcToken) {
        if (_ftcToken == address(0)) revert ZeroAddress();
        ftcToken = FTC(_ftcToken);

        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(TREASURY_MANAGER_ROLE, msg.sender);
        _grantRole(YIELD_HARVESTER_ROLE, msg.sender);
        _grantRole(FEE_DISPATCHER_ROLE, msg.sender);
        _grantRole(PAUSER_ROLE, msg.sender);
    }

    // ─────────────────────── Setters ──────────────────────────
    function setChildSavingsVault(address _vault) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (_vault == address(0)) revert ZeroAddress();
        childSavingsVault = _vault;
        emit ChildSavingsVaultSet(_vault);
    }

    // ───────────────────── Strategy Management ─────────────────
    function whitelistStrategy(address strategy) external onlyRole(TREASURY_MANAGER_ROLE) {
        if (strategy == address(0)) revert ZeroAddress();
        if (whitelistedStrategies[strategy]) revert StrategyAlreadyWhitelisted();
        whitelistedStrategies[strategy] = true;
        emit StrategyWhitelisted(strategy);
    }

    function removeStrategy(address strategy) external onlyRole(TREASURY_MANAGER_ROLE) {
        whitelistedStrategies[strategy] = false;
        emit StrategyRemoved(strategy);
    }

    // ──────────────────────── Deposits ─────────────────────────
    /// @notice Accept fee revenue from FeeDispatcher.
    ///         ERC-20 transfers must be approved by FeeDispatcher.
    function recordDeposit(address token, uint256 amount) external onlyRole(FEE_DISPATCHER_ROLE) {
        directHoldings[token] += amount;
    }

    // ──────────────────────── Investments ──────────────────────
    /// @notice Invest treasury assets into a whitelisted yield strategy.
    function invest(address strategy, address token, uint256 amount)
        external
        onlyRole(TREASURY_MANAGER_ROLE)
        whenNotPaused
        nonReentrant
    {
        if (!whitelistedStrategies[strategy]) revert StrategyNotWhitelisted();
        if (amount == 0) revert InvalidAmount();
        if (directHoldings[token] < amount) revert InsufficientBalance();

        directHoldings[token] -= amount;
        allocations[strategy] += amount;

        IERC20(token).forceApprove(strategy, amount);
        IYieldStrategy(strategy).deposit(amount, address(this));

        emit Invested(strategy, token, amount);
    }

    /// @notice Divest from a strategy back to direct holdings.
    function divest(address strategy, address token, uint256 shares)
        external
        onlyRole(TREASURY_MANAGER_ROLE)
        whenNotPaused
        nonReentrant
    {
        if (!whitelistedStrategies[strategy]) revert StrategyNotWhitelisted();
        if (shares == 0) revert InvalidAmount();

        uint256 received = IYieldStrategy(strategy).redeem(shares, address(this), address(this));
        allocations[strategy] -= received;
        directHoldings[token] += received;

        emit Divested(strategy, token, received);
    }

    /// @notice Harvest yield from a strategy and send to ChildSavingsVault.
    function harvestYield(address strategy, address token)
        external
        onlyRole(YIELD_HARVESTER_ROLE)
        whenNotPaused
        nonReentrant
    {
        if (!whitelistedStrategies[strategy]) revert StrategyNotWhitelisted();
        if (childSavingsVault == address(0)) revert ZeroAddress();

        uint256 profit = IYieldStrategy(strategy).harvest();
        if (profit == 0) return;

        IERC20(token).safeTransfer(childSavingsVault, profit);
        emit YieldHarvested(token, profit, childSavingsVault);
    }

    // ───────────────────── Store Subsidies ─────────────────────
    /// @notice Fund a partner merchant's discount rebate.
    function fundStoreSubsidy(address merchant, address token, uint256 amount)
        external
        onlyRole(TREASURY_MANAGER_ROLE)
        whenNotPaused
        nonReentrant
    {
        if (merchant == address(0)) revert ZeroAddress();
        if (amount == 0) revert InvalidAmount();
        if (directHoldings[token] < amount) revert InsufficientBalance();

        directHoldings[token] -= amount;
        IERC20(token).safeTransfer(merchant, amount);
        emit StoreSubsidy(merchant, token, amount);
    }

    // ─────────────────── Buyback and Burn ──────────────────────
    /// @notice Burn FTC that has been sent to Treasury by FeeDispatcher.
    function buybackAndBurn(uint256 ftcAmount)
        external
        onlyRole(FEE_DISPATCHER_ROLE)
        whenNotPaused
        nonReentrant
    {
        if (ftcAmount == 0) revert InvalidAmount();
        ftcToken.burn(ftcAmount);
        emit BuybackAndBurn(ftcAmount);
    }

    // ─────────────────────── Views ─────────────────────────────
    function totalDirectHolding(address token) external view returns (uint256) {
        return directHoldings[token];
    }

    function totalAllocated(address strategy) external view returns (uint256) {
        return allocations[strategy];
    }

    // ─────────────────────── Pause ─────────────────────────────
    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(PAUSER_ROLE) {
        _unpause();
    }
}
