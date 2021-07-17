import struct
from typing import Dict, Sequence
from abc import abstractmethod

from pydantic.dataclasses import dataclass
from pydantic import conint

from src.data import hash_digest_t, nonce_t, username_t, timestamp_t
from src.util import _subslice


STX = b"2"
ETX = b"3"
CMD_BYTES = 1
LENGHT_BYTES = 2
HASH_LENGTH = 32
USERNAME_LEN = 64
TRN_LEN = 2 * USERNAME_LEN


class Message:
    EXAMPLE_PAYLOADS = [{}]
    STRUCT = ""

    @classmethod
    def from_parse(cls, **kwargs: Dict):
        return cls(**kwargs)

    @classmethod
    def decode(cls, payload) -> Dict:
        return cls._decode(struct.unpack(cls.STRUCT, payload))

    @staticmethod
    def _decode(*args):
        return {}

    def encode(self) -> bytes:
        _args = [getattr(self, k) for k in self.__dataclass_fields__]

        return struct.pack(self.STRUCT, *_args)


@dataclass
class GetCount(Message):
    CMD = b"a"


@dataclass
class Count(Message):
    CMD = b"c"
    EXAMPLE_PAYLOADS = [{"blocks": 8}]
    STRUCT = "!I"

    blocks: conint(ge=0)

    def _decode(args):
        assert len(args) == 1
        return {"blocks": args[0]}


@dataclass
class GetBlockHashes(Message):
    CMD = b"b"


@dataclass
class BlockHashes(Message):
    CMD = b"h"
    COUNT_STRUCT = "!I"
    EXAMPLE_PAYLOADS = [{"hashes": []}, {"hashes": ["bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc"]}]

    hashes: Sequence[hash_digest_t]

    @classmethod
    def decode(cls, payload) -> Dict:
        _hash_count = payload[:4]
        _hashes = payload[4:]

        hash_count = struct.unpack(cls.COUNT_STRUCT, _hash_count)[0]

        hashes = []
        for i in range(hash_count):
            b_hash = _hashes[i * HASH_LENGTH:(i + 1) * HASH_LENGTH]
            hash = decodex_hexstring(b_hash)
            hashes.append(hash)

        return {"hashes": hashes}

    def encode(self) -> bytes:
        result = bytes()
        b_count = struct.pack(self.COUNT_STRUCT, len(self.hashes))
        result += b_count

        for h in self.hashes:
            result += encode_hexstring(h)

        return result

@dataclass
class ReqBlock(Message):
    CMD = b"r"
    EXAMPLE_PAYLOADS = [{"hash": "bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc"}]

    @classmethod
    def decode(cls, payload) -> Dict:
        return {"hash": decodex_hexstring(payload)}

    def encode(self) -> bytes:
        return encode_hexstring(self.hash)

    hash: hash_digest_t


@dataclass
class Transaction:
    from_ac: username_t
    to_ac: username_t

    @staticmethod
    def decode(payload: bytes) -> Dict:
        b_from_ac = payload[:USERNAME_LEN]
        b_to_ac = payload[USERNAME_LEN:2 * USERNAME_LEN]

        from_ac = decodex_hexstring(b_from_ac)
        to_ac = decodex_hexstring(b_to_ac)

        return {"from_ac": from_ac, "to_ac": to_ac}

    def encode(self) -> bytes:
        result = bytes()

        result += encode_hexstring(self.from_ac)
        result += encode_hexstring(self.to_ac)

        return result


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


class BlockEncodingMixin:
    SUB_STRUCT = "!III"

    def encode(self) -> bytes:
        result = bytes()

        hc = self.block.hashedContent
        result += encode_hexstring(self.block.hash)
        result += encode_hexstring(hc.prev_hash)
        result += struct.pack(self.SUB_STRUCT, hc.nonce, hc.timestamp, len(hc.transactions))

        for trn in hc.transactions:
            result += trn.encode()

        return result

    @classmethod
    def decode(cls, payload) -> Dict:
        STATIC_PAYLOAD_END = 2 * HASH_LENGTH + struct.Struct(cls.SUB_STRUCT).size
        b_hash = payload[:HASH_LENGTH]
        b_prev_hash = payload[HASH_LENGTH:2 * HASH_LENGTH]
        nonce, timestamp, trn_count = struct.unpack(cls.SUB_STRUCT, payload[2 * HASH_LENGTH:STATIC_PAYLOAD_END])

        transactions = []
        for i in range(trn_count):
            print(len(payload), STATIC_PAYLOAD_END, i)
            trn_payload = payload[STATIC_PAYLOAD_END + i * TRN_LEN:STATIC_PAYLOAD_END + (i + 1) * TRN_LEN]
            transactions.append(Transaction.decode(trn_payload))

        return {"block": {
            "hash": decodex_hexstring(b_hash),
            "hashedContent": {
                "prev_hash": decodex_hexstring(b_prev_hash),
                "nonce": nonce,
                "timestamp": timestamp,
                "transactions": transactions,
            },
        }}


@dataclass
class ExistingBlock(BlockEncodingMixin, Message):
    CMD = b"x"
    EXAMPLE_PAYLOADS = [{"block": {"hash": "bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc", "hashedContent": {"nonce": 1, "prev_hash": "bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc", "timestamp": 1, "transactions": [{"from_ac": "0977846f7b582cf027519210e7c4d182af92780204ff1d827fdc6557b14ff231fab77a2f90889b4d832febc2f2de270d08a14b772f3c002283e0d573e643c247", "to_ac": "0977846f7b582cf027519210e7c4d182af92780204ff1d827fdc6557b14ff231fab77a2f90889b4d832febc2f2de270d08a14b772f3c002283e0d573e643c247"}]}}}]

    block: Block


@dataclass
class NewBlock(BlockEncodingMixin, Message):
    CMD = b"z"
    EXAMPLE_PAYLOADS = [{"block": {"hash": "bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc", "hashedContent": {"nonce": 1, "prev_hash": "bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc", "timestamp": 1, "transactions": [{"from_ac": "0977846f7b582cf027519210e7c4d182af92780204ff1d827fdc6557b14ff231fab77a2f90889b4d832febc2f2de270d08a14b772f3c002283e0d573e643c247", "to_ac": "0977846f7b582cf027519210e7c4d182af92780204ff1d827fdc6557b14ff231fab77a2f90889b4d832febc2f2de270d08a14b772f3c002283e0d573e643c247"}, {"from_ac": "0977846f7b582cf027519210e7c4d182afe2780204ff1d827fdc6557b14ff231fab77a2f90889b4d832febc2f2de270d08a14b772f3c002283e0d573e643c247", "to_ac": "0977846f7b582cf027519210e7c4d182af92780204ff1d827fdc6557b14ff231fab77a2f90889b4d832febc2f2de270d08a14b772f3c002283e0d573e643e247"}]}}}]

    block: Block


def encode(msg: Message):
    payload = msg.encode()

    length = (len(payload) + CMD_BYTES).to_bytes(LENGHT_BYTES, byteorder='big')
    result = STX + length + msg.CMD + payload + ETX

    return result


COMMAND_TO_CLASS = {cls.CMD: cls for cls in Message.__subclasses__()}
assert all(len(cls.CMD) == CMD_BYTES for cls in Message.__subclasses__())


DATA_INDICES = slice(len(STX) + LENGHT_BYTES, -len(ETX))
COMMAND_INDICES = _subslice(DATA_INDICES, (0, CMD_BYTES))
PAYLOAD_INDICES = _subslice(DATA_INDICES, (CMD_BYTES, None))


def decode(data) -> Message:
    cmd = data[COMMAND_INDICES]
    payload = data[PAYLOAD_INDICES]

    msg_cls = COMMAND_TO_CLASS[cmd]

    result = msg_cls.from_parse(**(msg_cls.decode(payload)))

    return result


def encode_hexstring(hash: str) -> bytes:
    return bytes.fromhex(hash)


def decodex_hexstring(hash_bytes: bytes) -> str:
    return hash_bytes.hex()
