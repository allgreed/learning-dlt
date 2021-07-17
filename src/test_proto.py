from textwrap import wrap

import pytest

import src.json_proto as Protocol
import src.bin_proto as BinaryProtocol


protocol_example_messages = [] 
for cls, payload in sum([ [(cls, example_payload) for example_payload in cls.EXAMPLE_PAYLOADS] for cls in Protocol.Message.__subclasses__()], []):
    try:
        example = cls.from_parse(**payload)
    except TypeError:
        print(f"Err while generating example for {cls} with payload {payload}")
        raise
    protocol_example_messages.append(example)

binary_proto_example_messages = [] 
for cls, payload in sum([ [(cls, example_payload) for example_payload in cls.EXAMPLE_PAYLOADS] for cls in BinaryProtocol.Message.__subclasses__()], []):
    try:
        example = cls.from_parse(**payload)
    except TypeError:
        print(f"Err while generating example for {cls} with payload {payload}")
        raise
    binary_proto_example_messages.append(example)


@pytest.mark.parametrize("msg", protocol_example_messages)
def test_works(msg):
    transit_msg = Protocol.encode(msg)

    print(msg)
    print(transit_msg)
    print(" ".join(wrap(transit_msg.hex(), 2)))

    assert msg == Protocol.decode(transit_msg)


def test_null():
    transit_msg = Protocol.encode(Protocol.GetCount())

    assert transit_msg[Protocol.PAYLOAD_INDICES].decode("ascii") == ""


@pytest.mark.parametrize("msg", binary_proto_example_messages)
def test_binary_works(msg):
    transit_msg = BinaryProtocol.encode(msg)

    print(msg)
    print(transit_msg)
    print(" ".join(wrap(transit_msg.hex(), 2)))

    assert msg == BinaryProtocol.decode(transit_msg)
