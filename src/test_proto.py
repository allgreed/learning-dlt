import pytest
import src.proto as Protocol


@pytest.mark.parametrize("msg", [
    Protocol.NewTransaction(1234567, "ab", "cd", 1616693467.043559),
    Protocol.HighestTransaction(),
    Protocol.NotOk(),
    Protocol.Ok(),
    Protocol.HighestTransactionResponse(5),
    Protocol.GetTransaction(4566788),
])
def test_ble(msg):
    assert msg == Protocol.decode(Protocol.encode(msg))
