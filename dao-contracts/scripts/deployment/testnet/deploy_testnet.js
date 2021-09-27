const hre = require("hardhat");
const { ethers } = require("hardhat");
const { BigNumber } = require('ethers');

/***
 * Before the launch, make sure that
 * - BOOST_WARMUP = 0;
 * - INFLATION_DELAY > now - (Wed 12pm UTC)
 */

/***
 * For testnet, only the basic contracts will be deployed.
 * No vesting and admin management.
 */

async function main() {
    await hre.run('compile');

    const [deployer] = await ethers.getSigners();


    // We get the contract to deploy
    const InsureToken = await hre.ethers.getContractFactory("InsureToken");
    const VotingEscrow = await hre.ethers.getContractFactory("VotingEscrow");
    const GaugeController = await hre.ethers.getContractFactory("GaugeController");
    const Minter = await hre.ethers.getContractFactory("Minter");
    const LiquidityGauge = await hre.ethers.getContractFactory("LiquidityGauge");

    //config
    const name = "InsureToken";
    const simbol = "Insure";
    const decimal = 18;

    const ZERO_ADDRESS = "0x0000000000000000000000000000000000000000";

    const REGISTRY_ADDRESS = "0xe73Aa421A1c6C8c7057dc5094337589db66B7f54";
    let VESTING_ADDRESSES = ["0x9c56673F8446d8B982054dAD1C19D3098dB0716A"];
    let VESTING_ALLOCATION = [BigNumber.from("1000").mul("1000000000000000000")];//1000e18
    const ARAGON_AGENT = "0x1000000000000000000000000000000000000000";

    const GAUGE_TYPES = [
        ["Liquidity", BigNumber.from("1000000000000000000")], //10**18
    ]

    const POOL_TOKENS = [
        ["Pool1", "0xAF736aa216Efa36abCb5114b8E30F27005309B8C" , 12],
        ["Pool2", "0xf24822B5AF6fCc55a04Fc451f6D056c609C465b8" , 24],
        ["Index1", "0x9B25E3e0Ef3253bE0A91928067511684646a96DF", 100],
        ["CDS", "0xfE2C9367A06fE6c0FF813A37dbb011740aECecEC", 200]
    ]

    const POOL_PROXY_ADMINS = {
        "Ownership": deployer.address,
        "Params": deployer.address,
        "Emergency": deployer.address 
    }

    const FUNDING_ADMINS = [
        deployer.address,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        ZERO_ADDRESS
    ];

    //other constants
    const ten_to_the_21 = BigNumber.from("1000000000000000000000");


    //===deploy start===
    console.log("========== Basic Deployment START ==========");
    console.log("deployer:", deployer.address);

    //InsureToken
    const token = await InsureToken.deploy(name, simbol, decimal);
    console.log("InsureToken deployed to:", token.address);

    //VotingEscrow
    const voting_escrow = await VotingEscrow.deploy(
        token.address,
        "Vote-escrowed INSURE",
        "veINSURE",
        "veINSURE_1.0.0"
    );
    console.log("VotingEscrow deployed to:", voting_escrow.address);
    await voting_escrow.changeController(ARAGON_AGENT);

    //GaugeController
    const gauge_controller = await GaugeController.deploy(
        token.address,
        voting_escrow.address
    );
    console.log("GaugeController deployed to:", gauge_controller.address);

    //Minter
    const minter = await Minter.deploy(token.address, gauge_controller.address, REGISTRY_ADDRESS);
    console.log("Minter deployed to:", minter.address);
    let tx = await token.set_minter(minter.address);
    await tx.wait();
    console.log("InsureToken minter is:", await token.minter());

    //set gauge_type
    for(let el in GAUGE_TYPES){
        let name = GAUGE_TYPES[el][0];
        let weight = GAUGE_TYPES[el][1];
        tx = await gauge_controller.add_type(name, weight);
        await tx.wait();
    };
    console.log((await gauge_controller.gauge_type_names(1))); //Liquidity

    //LiquidityGauge x4
    for(let el in POOL_TOKENS){ //LiquidityGauge
        let name = POOL_TOKENS[el][0];
        let lp_token = POOL_TOKENS[el][1];
        let weight = POOL_TOKENS[el][2];

        let liquidity_gauge = await LiquidityGauge.deploy(lp_token, minter.address, deployer.address);
        console.log("LiquidityGauge deployed to:", liquidity_gauge.address, "{",name, lp_token, weight,"}");
        await gauge_controller.add_gauge(liquidity_gauge.address, 1, weight);
    }

    console.log("========== Basic Deployment END ==========");

}

main()
    .then(() => process.exit(0))
    .catch(error => {
    console.error(error);
    process.exit(1);
    });