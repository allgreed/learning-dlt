// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.7.0 <0.9.0;

contract HelloWorld {

    string storedThing;

    function set_thing(string memory s) public {
        storedThing = s;
    }

    function get_thing() public view returns (string memory){
        return storedThing;
    }
}
