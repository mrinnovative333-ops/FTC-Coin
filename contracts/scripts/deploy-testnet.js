// scripts/deploy-testnet.js
// Deploys the full FTC protocol to Base Sepolia for testnet MVP.
// Usage: npx hardhat run scripts/deploy-testnet.js --network base_sepolia

const { ethers } = require('ethers');

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log('Deploying with account:', deployer.address);

  // 1. Deploy FTC token with genesis allocations
  const FTC = await ethers.getContractFactory('FTC');
  const ftc = await FTC.deploy(
    deployer.address, // treasury placeholder
    deployer.address, // public sale placeholder
    deployer.address, // liquidity placeholder
    deployer.address, // team placeholder
    deployer.address, // investors placeholder
    deployer.address, // community placeholder
    deployer.address  // child reserve placeholder
  );
  await ftc.waitForDeployment();
  console.log('FTC deployed to:', await ftc.getAddress());

  // 2. Deploy GuardianRegistry with $5,000 KYC threshold in FTC
  // At $0.0033/FTC (midpoint of $60-80M mcap / 21B supply), $5,000 = ~1.5M FTC
  const kycThreshold = ethers.parseUnits('1500000', 18);
  const GuardianRegistry = await ethers.getContractFactory('GuardianRegistry');
  const registry = await GuardianRegistry.deploy(kycThreshold);
  await registry.waitForDeployment();
  console.log('GuardianRegistry deployed to:', await registry.getAddress());

  // 3. Deploy ChildSavingsVault
  // Yield rate 7% = 700 bps. Match cap $250 equivalent = ~75,000 FTC at $0.0033.
  const ChildSavingsVault = await ethers.getContractFactory('ChildSavingsVault');
  const vault = await ChildSavingsVault.deploy(
    await ftc.getAddress(),
    await registry.getAddress(),
    deployer.address, // child reserve placeholder (should be separate multisig)
    700,              // yieldRateBps = 7%
    ethers.parseUnits('75000', 18) // matchCapPerChild
  );
  await vault.waitForDeployment();
  console.log('ChildSavingsVault deployed to:', await vault.getAddress());

  // 4. Deploy Treasury
  const Treasury = await ethers.getContractFactory('Treasury');
  const treasury = await Treasury.deploy(await ftc.getAddress());
  await treasury.waitForDeployment();
  console.log('Treasury deployed to:', await treasury.getAddress());

  // 5. Deploy FeeDispatcher
  const FeeDispatcher = await ethers.getContractFactory('FeeDispatcher');
  const feeDispatcher = await FeeDispatcher.deploy(await ftc.getAddress());
  await feeDispatcher.waitForDeployment();
  console.log('FeeDispatcher deployed to:', await feeDispatcher.getAddress());

  // 6. Deploy StoreDiscount
  const StoreDiscount = await ethers.getContractFactory('StoreDiscount');
  const storeDiscount = await StoreDiscount.deploy(
    await ftc.getAddress(),
    await feeDispatcher.getAddress()
  );
  await storeDiscount.waitForDeployment();
  console.log('StoreDiscount deployed to:', await storeDiscount.getAddress());

  // 7. Wire roles
  // Grant Treasury BURNER_ROLE on FTC
  await (await ftc.grantRole(await ftc.BURNER_ROLE(), await treasury.getAddress())).wait();
  // Grant FeeDispatcher FEE_DISPATCHER_ROLE on Treasury
  await (await treasury.grantRole(await treasury.FEE_DISPATCHER_ROLE(), await feeDispatcher.getAddress())).wait();
  // Grant StoreDiscount FEE_COLLECTOR_ROLE on FeeDispatcher
  await (await feeDispatcher.grantRole(await feeDispatcher.FEE_COLLECTOR_ROLE(), await storeDiscount.getAddress())).wait();
  // Set Treasury in FeeDispatcher
  await (await feeDispatcher.setTreasury(await treasury.getAddress())).wait();
  // Set ChildSavingsVault in Treasury
  await (await treasury.setChildSavingsVault(await vault.getAddress())).wait();

  console.log('\n--- Deployment complete ---');
  console.log('FTC:', await ftc.getAddress());
  console.log('GuardianRegistry:', await registry.getAddress());
  console.log('ChildSavingsVault:', await vault.getAddress());
  console.log('Treasury:', await treasury.getAddress());
  console.log('FeeDispatcher:', await feeDispatcher.getAddress());
  console.log('StoreDiscount:', await storeDiscount.getAddress());
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
