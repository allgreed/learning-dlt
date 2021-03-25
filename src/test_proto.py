import pytest
from textwrap import wrap

import src.proto as Protocol


@pytest.mark.parametrize("msg", [
    Protocol.NewTransaction(1234567, "ab", "cd", 1616693467.043559),
    Protocol.HighestTransaction(),
    Protocol.NotOk(),
    Protocol.Ok(),
    Protocol.HighestTransactionResponse(5),
    Protocol.GetTransaction(4566788),
])
def test_works(msg):
    transit_msg = Protocol.encode(msg)
    # gibberish = b"djflsdfksjdlkfs"
    gibberish = b""

    print(msg)
    print(transit_msg)
    print(" ".join(wrap(transit_msg.hex(), 2)))

    assert msg == Protocol.decode(transit_msg + gibberish)
