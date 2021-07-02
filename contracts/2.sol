pragma solidity >=0.7.0 <0.9.0;

contract Counter {
    uint8 constant MAX_PERSONS = 3;
    uint8 count = 0;
    address immutable owner;
    
    constructor() {
        owner = msg.sender;
    }
    
    function requestAccess() public returns (bool)
    {
        if (count < MAX_PERSONS)
        {
            count += 1;
            return true;
        }
        else
        {
            return false;
        }
    }
    
    function personLeft() public
    {
        if (count > 0)
        {
            count -= 1;
        }
    }
    
    function checkCount() public view returns (uint8)
    {
        if (msg.sender == owner)
        {
            return count;
        }
        /*Warning: Unnamed return variable can remain unassigned. Add an explicit return with value to all non-reverting code paths or name the variable. --> contracts/2_Owner.sol:33:48: | 33 | function checkCount() public view returns (uint8) | ^^^^^*/
        // this would go away if I return 0 here :d
    }
}

