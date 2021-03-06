pragma solidity ^0.6.0;
//SPDX-License-Identifier: MIT
interface IUniversalMarket {
    function initialize(
        address _owner,
        string calldata _metaData,
        string calldata _name,
        string calldata _symbol,
        uint8 _decimals,
        uint256[] calldata _conditions,
        address[] calldata _references
    ) external returns (bool);
}
