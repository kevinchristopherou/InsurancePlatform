pragma solidity ^0.6.0;

import "../libraries/token/ERC20/IERC20.sol";

contract TestVault{

    address token;

    constructor(address _token)public{
        token = _token;
    }

    function withdrawAllAttribution(address _to)external returns(uint256){
        uint256 amount = IERC20(token).balanceOf(address(this));
        IERC20(token).transfer(_to, amount);

        return amount;
    }

}