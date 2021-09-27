const { expect } = require("chai");
const { ethers } = require("hardhat");
const { BigNumber } = require('ethers');

describe('InsureToken', function(){
    describe("test_inflation_delay", function(){
        const name = "InsureToken";
        const simbol = "Insure";
        const decimal = 18;
        const INITIAL_SUPPLY = BigNumber.from("126000000000000000000000000");
        const INITIAL_RATE = BigNumber.from("28000000000000000000000000");

        const YEAR = BigNumber.from(86400*365);
        const WEEK = BigNumber.from(86400*7);

        beforeEach(async () => {
            [creator, alice, bob] = await ethers.getSigners();
            const Token = await ethers.getContractFactory('InsureToken')
            Insure = await Token.deploy(name, simbol, decimal);
        });

        it("test_rate", async () => {
            expect(await Insure.rate()).to.equal("0");

            let now = BigNumber.from((await ethers.provider.getBlock('latest')).timestamp);
            await ethers.provider.send("evm_setNextBlockTimestamp", [now.add(86401).toNumber()]); //Tomorrow+1

            await Insure.update_mining_parameters();//mining_epoch: -1 => 0 / Rate: 0 => initial_rate

            let new_rate = await Insure.rate();
            console.log(new_rate.mul(YEAR).div("1000000000000000000").toNumber());
            expect(new_rate.gt('0')).to.equal(true);
            console.log((await Insure.mining_epoch()).toNumber());
            expect(new_rate).to.equal(INITIAL_RATE.div(YEAR));
        });

        it("test_start_epoch_time", async () => {
            let creation_time = await Insure.start_epoch_time();
            let now = BigNumber.from((await ethers.provider.getBlock('latest')).timestamp);
            expect(creation_time).to.equal(now.add('86400').sub(YEAR));//epoch -1 begins since Last year's tomorrow with the infration_interval of 1YEAR which means that epoch_time 0 starts since tomorrow. After that, infration rate decrease every year.
            
            
            await ethers.provider.send("evm_setNextBlockTimestamp", [now.add("86400").toNumber()]);

            await Insure.update_mining_parameters();

            expect(await Insure.start_epoch_time()).to.equal(creation_time.add(YEAR));
        });

        it("test_mining_epoch", async () => {
            expect(await Insure.mining_epoch()).to.equal('-1');

            let now = BigNumber.from((await ethers.provider.getBlock('latest')).timestamp);
            await ethers.provider.send("evm_setNextBlockTimestamp", [now.add("86400").toNumber()]); //proceed time to tomorrow because of inflation_delay = 1DAY

            await Insure.update_mining_parameters(); //mining_epoch -1 => 0

            expect(await Insure.mining_epoch()).to.equal('0');
        });

        it("test_available_supply", async ()=> {
            expect(await Insure.available_supply()).to.equal(INITIAL_SUPPLY); //1_303_030_303 * 10**18 //ok

            let now = BigNumber.from((await ethers.provider.getBlock('latest')).timestamp);
            await ethers.provider.send("evm_setNextBlockTimestamp", [now.add("86401").toNumber()]);

            await Insure.update_mining_parameters();

            let amount = await Insure.available_supply();
            //expect(amount).to.be.bignumber.not.equal(new BN('1303030303000000000000000000')); //actual: 1303030311714335457889396245
            expect(amount.gt(INITIAL_SUPPLY)).to.equal(true); //amount > 1303030303000000000000000000 //ok
        });

            
        
    });
});
  