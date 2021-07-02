pragma solidity >=0.7.0 <0.9.0;

contract Counter {
    uint8 constant MAX_PERSONS = 3;
    uint8 count = 0;
    
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
    
    function checkCount(string memory username, string memory password) public view returns (uint)
    {
        // yup, I know I should compare lengths as well
        if (hashCompareWithLengthCheck(username, "admin") && hashCompareWithLengthCheck(password, "123"))
        {
            return count;
        }
    }
    
    function hashCompareWithLengthCheck(string memory a, string memory b) internal pure returns (bool) {
    if(bytes(a).length != bytes(b).length) {
        return false;
    } else {
        return keccak256(bytes(a)) == keccak256(bytes(b));
    }
    }
}
