from dataclasses import dataclass

class Message:
    ...

    def encode(self):
        return self.MEM

    @classmethod
    def from_parse(cls, _):
        return cls()


@dataclass
class NewTransaction(Message):
    MEM = "NEW_TRANS"

    number: int
    from_username: str
    to_username: str
    timestamp: float

    @classmethod
    def from_parse(cls, args):
        # TODO: adapt to binary
        number = int(args[0])
        from_username = args[1]
        to_username = args[2]
        timestamp = float(args[3])

        return cls(number, from_username, to_username, timestamp)


@dataclass
class HighestTransaction(Message):
    MEM = "HIGHEST_TRN"
    CMD = b"h"


@dataclass
class NotOk(Message):
    MEM = "NOK_MSG"
    CMD = b"f"

@dataclass
class Ok(Message):
    MEM = "OK_MSG"
    CMD = b"o"


@dataclass
class HighestTransactionResponse(Message):
    MEM = "HIGHEST_TRN_RES"
    CMD = b"m"
    number: int

    @classmethod
    def from_parse(cls, args):
        # TODO: adapt to binary
        return cls(number=int(args[0]))


@dataclass
class GetTransaction(Message):
    MEM = "GET_TRANS"
    number: int
    CMD = b"g"

    @classmethod
    def from_parse(cls, args):
        # TODO: adapt to binary
        return cls(number=int(args[0]))


class Protocol:
    STX = b"2"
    ETX = b"3"

    # TODO: can this be done smarter? yep, with an import xd
    HighestTransaction = HighestTransaction
    HighestTransactionResponse = HighestTransactionResponse
    GetTransaction = GetTransaction
    NewTransaction = NewTransaction
    Message = Message

    @staticmethod
    def encode(msg):
        return msg.encode()
        # TODO: len in bytes
        # return STX + len(msg) + msg + ETX

    @staticmethod
    def decode(data):
        msg = data.decode()

        cmd, *body = msg.split(" ")

        cmd_cls = { cls.MEM: cls for cls in Message.__subclasses__()}[cmd]
        result = cmd_cls.from_parse(body)

        return result
