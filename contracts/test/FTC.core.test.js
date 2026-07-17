// test/FTC.core.test.js
const { expect } = require('chai');
const { ethers } = require('hardhat');

describe('FTC Core Protocol Flow', function () {
  let ftc, registry, vault, treasury, feeDispatcher, storeDiscount;
  let owner, guardian, merchant, buyer, kycIssuer, ageAttestor;
  const childIdHash = ethers.keccak256(ethers.toUtf8Bytes('child-001'));
  const birthTime = Math.floor(Date.now() / 1000) - 6 * 365 * 24 * 60 * 60; // 6 years old

  beforeEach(async function () {
    [owner, guardian, merchant, buyer, kycIssuer, ageAttestor] = await ethers.getSigners();

    // Deploy FTC
    const FTC = await ethers.getContractFactory('FTC');
    ftc = await FTC.deploy(
      owner.address, owner.address, owner.address, owner.address,
      owner.address, owner.address, owner.address
    );
    await ftc.waitForDeployment();

    // Deploy GuardianRegistry
    const GuardianRegistry = await ethers.getContractFactory('GuardianRegistry');
    registry = await GuardianRegistry.deploy(ethers.parseUnits('1500000', 18));
    await registry.waitForDeployment();

    // Deploy ChildSavingsVault
    const ChildSavingsVault = await ethers.getContractFactory('ChildSavingsVault');
    vault = await ChildSavingsVault.deploy(
      await ftc.getAddress(),
      await registry.getAddress(),
      owner.address,
      700,
      ethers.parseUnits('75000', 18)
    );
    await vault.waitForDeployment();

    // Deploy Treasury
    const Treasury = await ethers.getContractFactory('Treasury');
    treasury = await Treasury.deploy(await ftc.getAddress());
    await treasury.waitForDeployment();

    // Deploy FeeDispatcher
    const FeeDispatcher = await ethers.getContractFactory('FeeDispatcher');
    feeDispatcher = await FeeDispatcher.deploy(await ftc.getAddress());
    await feeDispatcher.waitForDeployment();

    // Deploy StoreDiscount
    const StoreDiscount = await ethers.getContractFactory('StoreDiscount');
    storeDiscount = await StoreDiscount.deploy(
      await ftc.getAddress(),
      await feeDispatcher.getAddress()
    );
    await storeDiscount.waitForDeployment();

    // Wire roles
    await ftc.grantRole(await ftc.BURNER_ROLE(), await treasury.getAddress());
    await treasury.grantRole(await treasury.FEE_DISPATCHER_ROLE(), await feeDispatcher.getAddress());
    await feeDispatcher.grantRole(await feeDispatcher.FEE_COLLECTOR_ROLE(), await storeDiscount.getAddress());
    await feeDispatcher.setTreasury(await treasury.getAddress());
    await treasury.setChildSavingsVault(await vault.getAddress());

    // Fund guardian and buyer
    await ftc.transfer(guardian.address, ethers.parseUnits('1000000', 18));
    await ftc.transfer(buyer.address, ethers.parseUnits('1000000', 18));
    await ftc.transfer(merchant.address, ethers.parseUnits('100000', 18));
  });

  it('should deploy all contracts', async function () {
    expect(await ftc.totalSupply()).to.equal(ethers.parseUnits('21000000000', 18));
    expect(await registry.kycThreshold()).to.equal(ethers.parseUnits('1500000', 18));
  });

  it('should register guardian, attest child, create account, deposit with match, and payout', async function () {
    // Register guardian
    await registry.connect(owner).grantRole(await registry.KYC_ISSUER_ROLE(), kycIssuer.address);
    await registry.connect(owner).grantRole(await registry.AGE_ATTESTOR_ROLE(), ageAttestor.address);
    await registry.connect(kycIssuer).registerGuardian(guardian.address, true);

    // Register child
    await registry.connect(guardian).registerChild(childIdHash, birthTime);

    // Attest age
    await registry.connect(ageAttestor).attestAge(childIdHash);

    // Create vault account
    await vault.connect(guardian).createAccount(childIdHash);

    // Approve and deposit $250 equivalent = 75,000 FTC at $0.0033
    const depositAmount = ethers.parseUnits('75000', 18);
    await ftc.connect(guardian).approve(await vault.getAddress(), depositAmount);
    await vault.connect(guardian).deposit(childIdHash, depositAmount, true);

    const account = await vault.getAccount(childIdHash);
    // Principal should be 150,000 FTC (75k deposit + 75k match)
    expect(account.principal).to.equal(ethers.parseUnits('150000', 18));

    // Child is 6, so payout eligible (age 5 checkpoint)
    const max = await vault.maxPayout(childIdHash);
    expect(max).to.equal(account.balance / 4n);

    // Accrue yield first
    await vault.accrueYield(childIdHash);

    // Withdraw 25%
    await ftc.connect(owner).approve(await vault.getAddress(), ethers.parseUnits('1500000', 18));
    await vault.connect(guardian).requestPayout(childIdHash, max);

    const accountAfter = await vault.getAccount(childIdHash);
    expect(accountAfter.totalPayouts).to.equal(max);
  });

  it('should process a merchant payment and distribute fees', async function () {
    // Register merchant
    await storeDiscount.connect(owner).registerMerchant(
      merchant.address,
      2000, // 20% max discount
      ethers.parseUnits('1000000', 18) // monthly cap
    );

    // Set total children to scale discount partially
    await storeDiscount.connect(owner).updateTotalChildren(5_000_000);

    const grossAmount = ethers.parseUnits('100000', 18); // $330 at $0.0033
    await ftc.connect(buyer).approve(await storeDiscount.getAddress(), grossAmount);

    await storeDiscount.connect(buyer).processPayment(buyer.address, merchant.address, grossAmount);

    // FeeDispatcher should have 2% = 2,000 FTC
    expect(await ftc.balanceOf(await feeDispatcher.getAddress())).to.equal(ethers.parseUnits('2000', 18));

    // Distribute fees
    await feeDispatcher.distribute();

    // 25% burned = 500 FTC burned from Treasury allowance
    const burned = ethers.parseUnits('21000000000', 18) - await ftc.totalSupply();
    expect(burned).to.equal(ethers.parseUnits('500', 18));

    // Merchant should have received net after discount
    const merchantBalance = await ftc.balanceOf(merchant.address);
    expect(merchantBalance).to.be.gt(ethers.parseUnits('100000', 18));
  });
});
