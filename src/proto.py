import json
from typing import Optional, Dict, Sequence

from pydantic.dataclasses import dataclass
from pydantic.json import pydantic_encoder
from pydantic import conint, BaseModel
from statemachine import StateMachine, State

from src.data import hash_digest_t, nonce_t, username_t, timestamp_t
from src.util import _subslice


STX = b"2"
ETX = b"3"
CMD_BYTES = 1
LENGHT_BYTES = 2


class SBBSequence(StateMachine):
    mining = State("Mining", initial=True)
    sync_hashes = State("Get Block Hashes")
    sync_blocks = State("Get Blocks")

    longer_chain_detected = mining.to(sync_hashes)
    more_hashes_than_blocks = sync_hashes.to(sync_blocks)
    hashes_equal_blocks = sync_blocks.to(mining)


class Message:
    EXAMPLE_PAYLOADS = [{}]

    @classmethod
    def from_parse(cls, **kwargs: Dict):
        return cls(**kwargs)


@dataclass
class GetCount(Message):
    CMD = b"a"


@dataclass
class Count(Message):
    CMD = b"c"
    EXAMPLE_PAYLOADS = [{"blocks": 8}]

    blocks: conint(ge=0)


@dataclass
class GetBlockHashes(Message):
    CMD = b"b"


@dataclass
class BlockHashes(Message):
    CMD = b"h"
    EXAMPLE_PAYLOADS = [{"hashes": []}, {"hashes": ["bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc"]}]

    hashes: Sequence[hash_digest_t]


@dataclass
class ReqBlock(Message):
    CMD = b"r"
    EXAMPLE_PAYLOADS = [{"hash": "bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc"}]

    hash: hash_digest_t


@dataclass
class Transaction:
    from_ac: username_t
    to_ac: username_t


@dataclass
class HashedContent:
    nonce: nonce_t
    prev_hash: hash_digest_t
    timestamp: timestamp_t
    transactions: Sequence[Transaction]


@dataclass
class Block:
    hash: hash_digest_t
    hashedContent: HashedContent


@dataclass
class ExistingBlock(Message):
    CMD = b"x"
    EXAMPLE_PAYLOADS = [{"block": {"hash": "bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc", "hashedContent": {"nonce": 1, "prev_hash": "bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc", "timestamp": 1, "transactions": [{"from_ac": "0977846f7b582cf027519210e7c4d182af92780204ff1d827fdc6557b14ff231fab77a2f90889b4d832febc2f2de270d08a14b772f3c002283e0d573e643c247", "to_ac": "0977846f7b582cf027519210e7c4d182af92780204ff1d827fdc6557b14ff231fab77a2f90889b4d832febc2f2de270d08a14b772f3c002283e0d573e643c247"}]}}}]

    block: Block


@dataclass
class NewBlock(Message):
    CMD = b"z"
    EXAMPLE_PAYLOADS = [{"block": {"hash": "bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc", "hashedContent": {"nonce": 1, "prev_hash": "bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc", "timestamp": 1, "transactions": [{"from_ac": "0977846f7b582cf027519210e7c4d182af92780204ff1d827fdc6557b14ff231fab77a2f90889b4d832febc2f2de270d08a14b772f3c002283e0d573e643c247", "to_ac": "0977846f7b582cf027519210e7c4d182af92780204ff1d827fdc6557b14ff231fab77a2f90889b4d832febc2f2de270d08a14b772f3c002283e0d573e643c247"}]}}}]

    block: Block


def encode(msg: Message):
    payload = json.dumps(msg, default=_pydantic_encoder).encode("ascii")

    length = (len(payload) + CMD_BYTES).to_bytes(LENGHT_BYTES, byteorder='big')
    result = STX + length + msg.CMD + payload + ETX

    return result


COMMAND_TO_CLASS = { cls.CMD: cls for cls in Message.__subclasses__()}
assert all(len(cls.CMD) == CMD_BYTES for cls in Message.__subclasses__())


DATA_INDICES = slice(len(STX) + LENGHT_BYTES, -len(ETX))
COMMAND_INDICES = _subslice(DATA_INDICES, (0, CMD_BYTES))
PAYLOAD_INDICES = _subslice(DATA_INDICES, (CMD_BYTES, None))


def decode(data) -> Message:
    cmd = data[COMMAND_INDICES]
    payload = data[PAYLOAD_INDICES]

    msg_cls = COMMAND_TO_CLASS[cmd]

    body = json.loads(payload.decode("ascii")) or {}
    result = msg_cls.from_parse(**body)

    return result


def _pydantic_encoder(obj):
    """
    Basically a pydantic JSON encoder, but returns None instead of {} for "empty" objects
    """
    if isinstance(obj, Message) and type(obj).__pydantic_model__.__annotations__ == {}:
        return None 

    return pydantic_encoder(obj)
