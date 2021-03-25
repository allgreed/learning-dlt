from typing import Dict
from datetime import datetime
from collections import defaultdict

from pydantic.dataclasses import dataclass
from pydantic import constr


username_t = constr(min_length=2, max_length=2)


@dataclass
class TransactionIntent:
    from_username: username_t
    to_username: username_t


@dataclass
class Transaction:
    number: int
    from_username: username_t
    to_username: username_t
    timestamp: float

    @classmethod
    def from_intent(cls, ti: TransactionIntent, current_trn: int, now_fn=None) -> "Transaction":
        now_fn = now_fn or (lambda: datetime.utcnow().timestamp())
        return cls(current_trn + 1, ti.from_username, ti.to_username, now_fn())


class State:    
    def __init__(self, transactions=None):
        self.transactions = transactions or {}

    def _append(self, t: Transaction):
        self.transactions[t.number] = t

    def __getitem__(self, trn: int):
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
