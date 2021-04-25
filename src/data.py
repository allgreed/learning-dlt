from typing import Dict, Set, Sequence
from datetime import datetime
from collections import defaultdict

from pydantic.dataclasses import dataclass
from pydantic import constr, conint
from ecdsa import SigningKey as SKey, SECP256k1
from ecdsa.keys import SigningKey, VerifyingKey


# TODO: expand this
username_t = constr(min_length=2, max_length=2)
hash_digest_t = int
nonce_t = conint(ge=0)
amount_t = conint(ge=1, le=1)


class Wallet:
    def __init__(self, sk: SigningKey, vk: VerifyingKey):
        self.signing_key = sk
        self.verifying_key = vk

    @classmethod
    def new(cls):
        sk = SigningKey.generate(curve=SECP256k1)
        vk = sk.verifying_key
        return cls(sk, vk)


@dataclass
class Transaction:
    pass


@dataclass
class Transfer(Transaction):
    from_username: username_t
    to_username: username_t
    amount: amount_t = 1


@dataclass
class Block:
    # TODO: write custom validator that it's actually digest-like
    previous_block_hash: hash_digest_t
    # TODO: constraint this retreoactively by the protocol
    nonce: nonce_t
    timestamp: int
    transactions: Sequence[Transaction]

    def _mine(previous_block_hash: hash_digest_t, timestamp: int, transactions: Sequence[Transaction]) -> nonce_t:
        # TODO: do the actual hashing and mining
        # TODO: deterministically cast transactions into JSON array, have a seperate method for that -> it's already sequential, so JSON dumps? :D

        return 5

    @classmethod():
    def pack(cls, previous_block_hash: hash_digest_t, transactions: Sequence[Transaction], now_fn=None):
        now_fn = now_fn or (lambda: int(datetime.utcnow().timestamp()))

        ts = now_fn()
        nonce = self._mine(previous_block_hash=previous_block_hash, nonce=0, timestamp=ts, transactions=transactions)

        return cls(previous_block_hash=previous_block_hash, nonce=nonce, timestamp=ts, transactions=transactions)

    @classmethod
    def genesis(cls, transactions: Sequence[Transaction], now_fn=None):
        return cls.pack(previous_block_hash=0, transactions)


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

        approved_transfers = [t for t in pending if t.trn in approved_trns]
        awaiting_transfers = [t for t in pending if t.trn not in approved_trns]
        effective_transfers = real + approved_transfers

        for t in effective_transfers:
            amount = 1

            ledger[t.from_username] -= amount
            ledger[t.to_username] += amount

        for t in awaiting_transfers:
            amount = 1

            ledger[t.from_username] -= amount

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
