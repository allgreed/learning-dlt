import json
from textwrap import wrap

import pytest

import src.proto as Protocol
# from src.main import pack_transaction, extract_transaction, Transfer, TransferRequiringApproval, TransferApproval
# TODO: test transalations


protocol_example_messages = [] 
for i in sum([ [(cls, example_payload) for example_payload in cls.EXAMPLE_PAYLOADS] for cls in Protocol.Message.__subclasses__()], []):
    cls, payload = i
    try:
        example = cls.from_parse(**payload)
    except TypeError:
        print(f"Err while generating example for {cls} with payload {payload}")
        raise
    protocol_example_messages.append(example)


@pytest.mark.parametrize("msg", protocol_example_messages)
def test_works(msg):
    transit_msg = Protocol.encode(msg)

    print(msg)
    print(transit_msg)
    print(" ".join(wrap(transit_msg.hex(), 2)))

    assert msg == Protocol.decode(transit_msg)


def test_null():
    transit_msg = Protocol.encode(Protocol.GetCount())

    assert json.loads(transit_msg[Protocol.PAYLOAD_INDICES].decode("ascii")) == None


# @pytest.mark.parametrize("t", [
    # Transfer(123, 456, "ab", "cd"),
    # TransferRequiringApproval(123, 456, "ab", "cd"),
    # TransferApproval(789, approved_trn=123, approver="cd", timestamp=457),
# ])
# def test_pack_unpacks(t):
    # packed = pack_transaction(t)

    # assert t == extract_transaction(packed)
