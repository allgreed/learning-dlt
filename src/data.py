from typing import Dict, Set
from datetime import datetime
from collections import defaultdict

from pydantic.dataclasses import dataclass
from pydantic import constr, conint


username_t = constr(min_length=2, max_length=2)
trn_t = conint(ge=0)


# TODO: fix propagation
@dataclass
class TransactionIntent:
    from_username: username_t
    to_username: username_t

# TODO: refactor class hierarchy Transaction -> Transfer

@dataclass
class Transaction:
    number: trn_t
    from_username: username_t
    to_username: username_t
    timestamp: int

    @classmethod
    def from_intent(cls, ti: TransactionIntent, current_trn: int, now_fn=None) -> "Transaction":
        now_fn = now_fn or (lambda: int(datetime.utcnow().timestamp()))
        return cls(current_trn + 1, ti.from_username, ti.to_username, now_fn())


@dataclass
class TransactionApproval:
    number: trn_t
    approved_trn: trn_t
    timestamp: int


@dataclass
class TransactionRequiringApproval(Transaction):
    pass


class State:    
    def __init__(self):
        self.transactions = {}

    def _append(self, t: Transaction):
        self.transactions[t.number] = t

    def __getitem__(self, trn: int):
        return self.transactions[trn]

    def incorporate(self, t: Transaction) -> bool:
        if t.number not in self.transactions:
            self._append(t)
            return True
        else:
            matching = self.transactions[t.number]
            if matching.timestamp > t.timestamp:
                self._append(t)
                return True
            elif matching == t:
                return True
            else:
                return False

    def balance(self, username: username_t):
        return self.ledger[username]

    @property
    def ledger(self):
        ledger = defaultdict(lambda: 0)
        raw_transactions = self.transactions.values()

        approved_trns, pending, real = set(), [], []
        for t in raw_transactions:
            if type(t) == TransactionApproval:
                approved_trns.add(t.approved_trn)
            elif type(t) == TransactionRequiringApproval:
                pending.append(t)
            elif type(t) == Transaction:
                real.append(t)
            else: # impossible
                assert False, "Unsupported type in transaction sorting"

        effective_transfers = real + [t for t in pending if t.number in approved_trns]

        for t in effective_transfers:
            amount = 1

            ledger[t.from_username] -= amount
            ledger[t.to_username] += amount

        return ledger

    @property
    def highest_transaction_number(self):
        try:
            return list(sorted(self.transactions.keys()))[-1]
        except IndexError:
            return -1
