import pytest
from textwrap import wrap

import src.proto as Protocol
from src.main import pack_transaction, extract_transaction, Transfer, TransferRequiringApproval, TransferApproval


@pytest.mark.parametrize("msg", [
    Protocol.HighestTransaction(),
    Protocol.NotOk(),
    Protocol.HighestTransactionResponse(5),
    Protocol.GetTransaction(515),
    Protocol.NewTransaction(515, "ab", "cd", 1616693467),
    Protocol.NewTransaction(515, "00", "cd", 1616693468, approved_trn=213),
    Protocol.NewTransaction(515, "ab", "cd", 1616693469, approved=False),
    Protocol.Ok(),
])
def test_works(msg):
    transit_msg = Protocol.encode(msg)

    print(msg)
    print(transit_msg)
    print(" ".join(wrap(transit_msg.hex(), 2)))

    assert msg == Protocol.decode(transit_msg)


@pytest.mark.parametrize("t", [
    Transfer(123, 456, "ab", "cd"),
    TransferRequiringApproval(123, 456, "ab", "cd"),
    TransferApproval(789, approved_trn=123, timestamp=457),
])
def test_pack_unpacks(t):
    packed = pack_transaction(t)

    assert t == extract_transaction(packed)
