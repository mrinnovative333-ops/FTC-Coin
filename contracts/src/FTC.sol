// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/// @title FTC — For The Children ERC-20 Token
/// @notice 21B fixed supply, minted once at genesis, no future minting.
///         25% of merchant fees are burned via the BURNER_ROLE.
///         Deployed on Base L2.
contract FTC is ERC20, ERC20Burnable, AccessControl, Pausable {
    // ────────────────────────── Roles ──────────────────────────
    bytes32 public constant BURNER_ROLE = keccak256("BURNER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    // ──────────────────────── Constants ────────────────────────
    /// @notice 21 billion FTC with 18 decimals (same as ETH/USDC-style).
    uint256 public constant MAX_SUPPLY = 21_000_000_000 * 1e18;

    // ────────────────────────── Events ─────────────────────────
    event GenesisAllocation(
        address indexed treasury,
        address indexed publicSale,
        address indexed liquidity,
        address team,
        address investors,
        address community,
        address childReserve
    );
    event Burn(address indexed burner, uint256 amount);

    // ───────────────────────── Constructor ─────────────────────
    /// @dev All allocation addresses must be set at deployment; tokens are
    ///      minted once and never again.
    constructor(
        address treasury,
        address publicSale,
        address liquidity,
        address team,
        address investors,
        address community,
        address childReserve
    ) ERC20("For The Children", "FTC") {
        // Verify no zero addresses
        if (
            treasury == address(0) ||
            publicSale == address(0) ||
            liquidity == address(0) ||
            team == address(0) ||
            investors == address(0) ||
            community == address(0) ||
            childReserve == address(0)
        ) revert ZeroAddress();

        // Grant roles
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(BURNER_ROLE, treasury);
        _grantRole(PAUSER_ROLE, msg.sender);

        // ── Genesis allocation (matches TOKENOMICS_SPEC.md) ──
        // Bucket                          %      Tokens (with 1e18)
        // Community rewards & incentives   25%    5.25B
        // Treasury                         20%    4.20B
        // Team + advisors                  15%    3.15B
        // Investors                        10%    2.10B
        // Public sale                      15%    3.15B
        // Child savings reserve            10%    2.10B
        // Liquidity (CEX/DEX)               5%    1.05B

        _mint(community,    5_250_000_000 * 1e18); // 25%
        _mint(treasury,     4_200_000_000 * 1e18); // 20%
        _mint(team,         3_150_000_000 * 1e18); // 15%
        _mint(investors,    2_100_000_000 * 1e18); // 10%
        _mint(publicSale,   3_150_000_000 * 1e18); // 15%
        _mint(childReserve, 2_100_000_000 * 1e18); // 10%
        _mint(liquidity,    1_050_000_000 * 1e18); //  5%

        // Total = 21B exactly
        assert(totalSupply() == MAX_SUPPLY);

        emit GenesisAllocation(
            treasury, publicSale, liquidity, team, investors, community, childReserve
        );
    }

    // ──────────────────────── Burn logic ───────────────────────
    /// @notice Burn tokens from the caller (BURNER_ROLE only).
    ///         Used by FeeDispatcher to burn 25% of merchant fees.
    function burn(uint256 amount) public override onlyRole(BURNER_ROLE) {
        super.burn(amount);
        emit Burn(msg.sender, amount);
    }

    /// @notice Burn tokens from a specific account (BURNER_ROLE only).
    function burnFrom(address account, uint256 amount) public override onlyRole(BURNER_ROLE) {
        super.burnFrom(account, amount);
        emit Burn(account, amount);
    }

    // ────────────────────── Pause / unpause ────────────────────
    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(PAUSER_ROLE) {
        _unpause();
    }

    // ──────────────────────── Overrides ────────────────────────
    function _update(
        address from,
        address to,
        uint256 amount
    ) internal override whenNotPaused {
        super._update(from, to, amount);
    }

    // ──────────────────────── Errors ───────────────────────────
    error ZeroAddress();
}