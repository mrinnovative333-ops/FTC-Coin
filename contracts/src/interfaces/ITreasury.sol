// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title ITreasury
/// @notice Interface for Treasury contract used by FeeDispatcher.
interface ITreasury {
    function buybackAndBurn(uint256 ftcAmount) external;
    function recordDeposit(address token, uint256 amount) external;
}
