// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title IFeeDispatcher
/// @notice Interface for FeeDispatcher contract used by StoreDiscount.
interface IFeeDispatcher {
    function depositFees(uint256 amount) external;
}
