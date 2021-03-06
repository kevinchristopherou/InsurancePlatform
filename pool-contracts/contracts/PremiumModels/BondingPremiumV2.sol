pragma solidity ^0.6.0;

import "../libraries/math/SafeMath.sol";
import "./Calculator.sol";

contract BondingPremiumV2 {
    using SafeMath for uint256;

    ABDKMath64x64 calculator;

    event CommitNewAdmin(uint256 deadline, address future_admin);
    event NewAdmin(address admin);

    uint256 public k; //k
    uint256 public b; //b
    uint256 public a; //a

    uint256 public low_risk_util; //expressed in util rate
    uint256 public low_risk_liquidity; //expressed in total liquidity amount
    uint256 public low_risk_b;

    address public owner;
    address public future_owner;
    uint256 public transfer_ownership_deadline;
    uint256 public constant ADMIN_ACTIONS_DELAY = 3 * 86400;

    modifier onlyOwner() {
        require(isOwner(), "Ownable: caller is not the owner");
        _;
    }

    /***
     * -- Fondamental Equation f(x)--
     * (x-a)(y-a) = k
     *
     * f(x) = k/(x-a)+a
     * f(x) pass through (1000000, 0) (0, 1000000)
     *
     * Using Quadratic Formula,
     * a = (1e6 - sqrt(1e6^2+4k))/2
     *
     * use below instead of above to avoid negative value.
     * -a  = (1e6 + sqrt(1e6^2+4k))/2 - 1e6
     * f(x) = k/(x+a)-a
     *
     * --Yearly Premium Equation g(x)--
     * g(x) = f(x)*365 + b
     *      = 365(k/(x+a)-a)+b
     * x = 1e6 - Utilization Rate
     *
     * Premium%
     * |
     * \
     * ||
     * |\
     * | \-_
     * |    \-_
     * |       \-____
     * |-------------\------->LP left%
     * f(x) is like uniswap bonding curve which is customized so that it crrosses over axis at the point (1000000, 0) (0,1000000)
     * Base rate is applied addition to this.
     *
     * -- Initial Parameters --
     * k = 300100000
     * b = 30000
     * => a=300
     *
     * //Apply lower base_fee for low risk insurance.
     * low_risk_b = 5000 //0.5%
     * low_risk_border = uint256(1e24) //1M USDC
     */

    constructor(address _calculator) public {
        calculator = ABDKMath64x64(_calculator);
        
        //setPremium()
        b = 30000;
        k = 300100000;
        a = (
            uint256(1e6).add(sqrt(uint256(1e6).mul(uint256(1e6)).add(k.mul(4))))
        )
        .div(2)
        .sub(uint256(1e6));

        //setOptions()
        low_risk_b = 5000; //0.5%
        low_risk_liquidity = uint256(1e12); //1M USDC (6 decimals)
        low_risk_util = 150000; //15% utilization

        owner = msg.sender;
    }

    function getPremiumRate(uint256 _totalLiquidity, uint256 _lockedAmount)
        public
        view
        returns (uint256)
    {
        // utilization rate (0~1000000)
        uint256 _util = _lockedAmount.mul(1e6).div(_totalLiquidity);

        // yearly premium rate
        uint256 _premiumRate;

        uint256 Q = uint256(1e6).sub(_util).add(a); //(x+a)
        if (_util < low_risk_util && _totalLiquidity > low_risk_liquidity) {
            //utilizatio < 10% && totalliquidity > low_risk_border (easily acomplished if leverage applied)
            _premiumRate = k
            .mul(365)
            .sub(Q.mul(a).mul(365))
            .add(Q.mul(low_risk_b))
            .div(Q)
            .div(10); //change 100.0000% to 100.000%
        } else {
            _premiumRate = k
            .mul(365)
            .sub(Q.mul(a).mul(365))
            .add(Q.mul(b))
            .div(Q)
            .div(10); //change 100.0000% to 100.000%
        }

        //Return premium
        return _premiumRate;
    }

    // Returns percent value of premium (100 = 1 premium)
    function getPremiumValue(
        uint256 _amount,
        uint256 _term,
        uint256 _totalLiquidity,
        uint256 _lockedAmount,
        uint256 _b
    ) internal view returns (uint256) {
        
        if (_amount == 0) {
            return 0;
        }
        
        uint256 p1 = 1000000;
        p1 = p1.sub(_lockedAmount.add(_amount).mul(1e6).div(_totalLiquidity));
        
        uint256 p2 = 1000000;
        p2 = p2.sub(_lockedAmount.mul(1e6).div(_totalLiquidity));
        
        int128 ln_p1 = calculator.ln(calculator.fromUInt(p1.add(a)));
        uint256 ln_res_p1 = calculator.mulu(ln_p1, k).mul(365);
        uint256 _premium_p1 = ln_res_p1.add(_b.mul(p1)).sub(a.mul(365).mul(p1));
        
        int128 ln_p2 = calculator.ln(calculator.fromUInt(p2.add(a)));
        uint256 ln_res_p2 = calculator.mulu(ln_p2, k).mul(365);
        uint256 _premium_p2 = ln_res_p2.add(_b.mul(p2)).sub(a.mul(365).mul(p2));

        uint256 _premium = _premium_p2.sub(_premium_p1);
        
        return _premium;
    } 
    
    // Returns token amount for premium
    function getPremium(
        uint256 _amount,
        uint256 _term,
        uint256 _totalLiquidity,
        uint256 _lockedAmount
    ) external view returns (uint256) {
        require(_amount.add(_lockedAmount) <= _totalLiquidity, "Amount exceeds.");
        
        uint256 _util = _lockedAmount.mul(1e6).div(_totalLiquidity);
            
        uint256 _b = b;
        if (_util < low_risk_util && _totalLiquidity > low_risk_liquidity) 
            _b = low_risk_b;
        
        uint256 premium = getPremiumValue(_amount, _term, _totalLiquidity, _lockedAmount, _b);
        
        uint256 year = _term.div(365 days);
        uint256 percent = premium.mul(year);
        
        return percent.mul(_totalLiquidity).div(1e12);
    }

    /**
     * @notice Set a premium model
     * @param _baseRatePerYear The Base rate addition to the bonding curve. (scaled by 1e5)
     * @param _multiplierPerYear The rate of mixmum premium(scaled by 1e5)
     */
    function setPremium(uint256 _baseRatePerYear, uint256 _multiplierPerYear)
        external
        onlyOwner
    {
        b = _baseRatePerYear;
        k = _multiplierPerYear;
        a = (
            uint256(1e6).add(sqrt(uint256(1e6).mul(uint256(1e6)).add(k.mul(4))))
        )
        .div(2)
        .sub(uint256(1e6));
    }

    /***
     * @notice Set optional parameters
     * @param _a low_risk_border
     * @param _b low_risk_b
     * @param _c low_risk_util
     */
    function setOptions(
        uint256 _a,
        uint256 _b,
        uint256 _c,
        uint256 _d
    ) external onlyOwner {
        require(_b < b, "low_risk_base_fee must lower than base_fee");

        low_risk_liquidity = _a;
        low_risk_b = _b;
        low_risk_util = _c;
    }

    function sqrt(uint256 x) internal pure returns (uint256 y) {
        uint256 z = (x + 1) / 2;
        y = x;
        while (z < y) {
            y = z;
            z = (x / z + z) / 2;
        }
    }

    function get_owner() public view returns (address) {
        return owner;
    }

    function isOwner() public view returns (bool) {
        return msg.sender == owner;
    }

    function commit_transfer_ownership(address _owner) external {
        require(msg.sender == owner, "dev: only owner");
        require(transfer_ownership_deadline == 0, "dev: active transfer");

        uint256 _deadline = block.timestamp.add(ADMIN_ACTIONS_DELAY);
        transfer_ownership_deadline = _deadline;
        future_owner = _owner;

        emit CommitNewAdmin(_deadline, _owner);
    }

    function apply_transfer_ownership() external {
        require(msg.sender == owner, "dev: only owner");
        require(
            block.timestamp >= transfer_ownership_deadline,
            "dev: insufficient time"
        );
        require(transfer_ownership_deadline != 0, "dev: no active transfer");

        transfer_ownership_deadline = 0;
        address _owner = future_owner;

        owner = _owner;

        emit NewAdmin(owner);
    }
}
