from dataclasses import dataclass
from typing import List
from datetime import datetime
from collections import defaultdict

# TODO: add some validation with pydantic - max 2 characters
username_t = str

@dataclass
class Transaction:
    number: int
    timestamp: datetime
    from_username: username_t
    to_username: username_t

@dataclass
class TransactionIntent:
    from_username: username_t
    to_username: username_t


@dataclass
class State:    
    transactions: List[Transaction]

    def append(self, t: Transaction):
        self.transactions.append(t)

    def balance(self, username: username_t):
        return self.ledger[username]

    @property
    def ledger(self):
        ledger = defaultdict(lambda: 0)
        amount = 1
        for t in self.transactions:
            ledger[t.from_username] -= amount
            ledger[t.to_username] += amount

        return ledger

    @property
    def highest_transaction_number(self):
        try:
            return list(sorted(self.transactions, key=lambda t: t.number))[-1].number
        except IndexError:
            return -1


class ProtocolMessage:
    ...

class NewTransaction(ProtocolMessage):
    ...

class HighestTransaction(ProtocolMessage):
    MEM = "HIGHEST_TRN"
    CMD = b"h"

@dataclass
class HighestTransactionResponse(ProtocolMessage):
    MEM = "HIGHEST_TRN_RES"
    CMD = b"m"
    number: int
    ...


class Protocol:
    STX = b"2"
    ETX = b"3"

    HighestTransaction = HighestTransaction
    HighestTransactionResponse = HighestTransactionResponse

    @staticmethod
    def encode(msg):
        # TODO: len in bytes
        return STX + len(msg) + msg + ETX

    @staticmethod
    def decode(data):
        msg = data.decode()

        # TODO: generalize
        if msg == "HIGHEST_TRN":
            return HighestTransaction()
        if msg.startswith("HIGHEST_TRN_RES"):
            n = int(msg.replace("HIGHEST_TRN_RES", "").strip())
            return HighestTransactionResponse(number = n)
        else:
            return msg
