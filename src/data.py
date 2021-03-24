from dataclasses import dataclass
from typing import Dict
from datetime import datetime
from collections import defaultdict

# TODO: add some validation with pydantic - max 2 characters
username_t = str

@dataclass
class Transaction:
    number: int
    from_username: username_t
    to_username: username_t
    timestamp: float


@dataclass
class TransactionIntent:
    from_username: username_t
    to_username: username_t


class State:    
    def __init__(self, transactions=None):
        self.transactions = transactions or {}

    def _append(self, t: Transaction):
        self.transactions[t.number] = t

    # TODO: change into subscription, migrate GetTransaction hanlder
    def get(self, trn: int):
        return self.transactions[trn]

    def incorporate(self, t: Transaction) -> bool:
        if t.number not in self.transactions:
            self._append(t)
            return True
        else:
            if self.transactions[t.number].timestamp > t.timestamp:
                self._append(t)
                return True
            else:
                return False

    def balance(self, username: username_t):
        return self.ledger[username]

    @property
    def ledger(self):
        ledger = defaultdict(lambda: 0)
        amount = 1
        for t in self.transactions.values():
            ledger[t.from_username] -= amount
            ledger[t.to_username] += amount

        return ledger

    @property
    def highest_transaction_number(self):
        try:
            return list(sorted(self.transactions.keys()))[-1]
        except IndexError:
            return -1
