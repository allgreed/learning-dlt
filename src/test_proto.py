import pytest
from textwrap import wrap

import src.proto as Protocol


@pytest.mark.parametrize("msg", [
    Protocol.HighestTransaction(),
    Protocol.NotOk(),
    Protocol.HighestTransactionResponse(5),
    Protocol.GetTransaction(515),
    Protocol.NewTransaction(515, "ab", "cd", 1616693467),
    Protocol.Ok(),
])
def test_works(msg):
    transit_msg = Protocol.encode(msg)
    gibberish = b""

    print(msg)
    print(transit_msg)
    print(" ".join(wrap(transit_msg.hex(), 2)))

    # assert 0

    assert msg == Protocol.decode(transit_msg + gibberish)
