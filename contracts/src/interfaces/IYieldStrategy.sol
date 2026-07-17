// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title IYieldStrategy
/// @notice Minimal interface for ERC-4626-compatible yield strategies used by Treasury.
interface IYieldStrategy {
    /// @notice Deposit assets and receive shares.
    function deposit(uint256 assets, address receiver) external returns (uint256);

    /// @notice Redeem shares for assets.
    function redeem(uint256 shares, address receiver, address owner) external returns (uint256);

    /// @notice Harvest available yield and return the amount.
    function harvest() external returns (uint256);

    /// @notice Total assets managed by the strategy.
    function totalAssets() external view returns (uint256);

    /// @notice Convert assets to shares.
    function convertToShares(uint256 assets) external view returns (uint256);

    /// @notice Convert shares to assets.
    function convertToAssets(uint256 shares) external view returns (uint256);
}
