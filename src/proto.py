import struct
import functools
from pydantic.dataclasses import dataclass


STX = b"2"
ETX = b"3"


class Message:
    def encode(self) -> bytes:
        _args = [getattr(self, k) for k in self.__dataclass_fields__]

        return struct.pack(self.STRUCT, *_args)

    @classmethod
    def from_parse(cls, _):
        return cls()


@dataclass
class NewTransaction(Message):
    MEM = "NEW_TRANS"
    CMD = b"n"

    number: int
    from_username: str
    to_username: str
    timestamp: int

    STRUCT = "h4cI"

    def encode(self) -> bytes:
        prepacked_chars = map(functools.partial(bytes, encoding="ascii"), [*self.from_username, *self.to_username])

        int_timestamp = int(self.timestamp)  

        return struct.pack(self.STRUCT, self.number, *prepacked_chars, int_timestamp)

    @classmethod
    def from_parse(cls, args):
        number = int(args[0])

        chars = b"".join(args[1:5])
        timestamp = float(args[5])

        from_username = chars[0:2]
        to_username = chars[2:4]

        return cls(number, from_username, to_username, timestamp)


@dataclass
class HighestTransaction(Message):
    MEM = "HIGHEST_TRN"
    CMD = b"h"
    STRUCT = ""


@dataclass
class NotOk(Message):
    MEM = "NOK_MSG"
    CMD = b"f"
    STRUCT = ""

@dataclass
class Ok(Message):
    MEM = "OK_MSG"
    CMD = b"o"
    STRUCT = ""


@dataclass
class HighestTransactionResponse(Message):
    MEM = "HIGHEST_TRN_RES"
    CMD = b"m"

    number: int

    STRUCT = "h"

    @classmethod
    def from_parse(cls, args):
        return cls(number=int(args[0]))


@dataclass
class GetTransaction(Message):
    MEM = "GET_TRANS"
    CMD = b"g"

    number: int

    STRUCT = "h"

    @classmethod
    def from_parse(cls, args):
        return cls(number=int(args[0]))


def encode(msg):
    body = msg.encode()

    length = len(body).to_bytes(1, byteorder='big')
    result = STX + length + msg.CMD + body + ETX

    return result

def decode(data):
    data = data[2:-1]
    cmd = data[0:1]
    msg = data[1:]

    COMMAND_TO_CLASS = { cls.CMD: cls for cls in Message.__subclasses__()}
    cls = COMMAND_TO_CLASS[cmd]

    body = struct.unpack(cls.STRUCT, msg)
    result = cls.from_parse(body)

    return result
