from typing import Dict, Set
from datetime import datetime
from collections import defaultdict

from pydantic.dataclasses import dataclass
from pydantic import constr, conint


username_t = constr(min_length=2, max_length=2)
trn_t = conint(ge=0)


@dataclass
class TransferIntent:
    from_username: username_t
    to_username: username_t
    pending: bool = False

@dataclass
class ApprovalIntent:
    trn: trn_t


@dataclass
class Transaction:
    trn: trn_t
    timestamp: int


@dataclass
class Transfer(Transaction):
    from_username: username_t
    to_username: username_t

    @staticmethod
    def from_intent(ti: TransferIntent, current_trn: int, now_fn=None) -> "Transfer":
        cls = TransferRequiringApproval if ti.pending else Transfer
        now_fn = now_fn or (lambda: int(datetime.utcnow().timestamp()))
        return cls(current_trn + 1, now_fn(), ti.from_username, ti.to_username)


@dataclass
class TransferApproval(Transaction):
    approved_trn: trn_t

    # TODO: DRY! -> move this onto transaction and somehow extend? :D
    @classmethod
    def from_intent(cls, ai: ApprovalIntent, current_trn: int, now_fn=None) -> "TransferApproval":
        now_fn = now_fn or (lambda: int(datetime.utcnow().timestamp()))
        return cls(current_trn + 1, now_fn(), approved_trn=ai.trn)


@dataclass
class TransferRequiringApproval(Transfer):
    pass


class State:    
    def __init__(self):
        self.transactions = {}

    def _append(self, t: Transfer):
        self.transactions[t.trn] = t

    def __getitem__(self, trn: int):
        return self.transactions[trn]

    def incorporate(self, t: Transfer) -> bool:
        if t.trn not in self.transactions:
            self._append(t)
            return True
        else:
            matching = self.transactions[t.trn]
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
        approved_trns, pending, real = self._sorted_transactions()

        effective_transfers = real + [t for t in pending if t.trn in approved_trns]

        for t in effective_transfers:
            amount = 1

            ledger[t.from_username] -= amount
            ledger[t.to_username] += amount

        return ledger

    def _sorted_transactions(self):
        approved_trns, pending, real = set(), [], [] 
        for t in self.transactions.values():
            if type(t) is TransferApproval:
                approved_trns.add(t.approved_trn)
            elif type(t) is TransferRequiringApproval:
                pending.append(t)
            elif type(t) is Transfer:
                real.append(t)
            else: # impossible
                assert False, "Unsupported type in transaction sorting"

        return approved_trns, pending, real

    def pending_for(self, username: username_t):
        approved_trns, pending, _ = self._sorted_transactions()
        return [t for t in pending if t.trn not in approved_trns and t.to_username == username]

    @property
    def highest_transaction_number(self):
        try:
            return list(sorted(self.transactions.keys()))[-1]
        except IndexError:
            return -1
