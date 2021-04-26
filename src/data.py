import itertools
import hashlib
import json
from typing import Dict, Set, Sequence, Optional, Tuple
from datetime import datetime
from collections import defaultdict

from pydantic.dataclasses import dataclass
from pydantic.json import pydantic_encoder
from pydantic import constr, conint
from ecdsa import SigningKey as SKey, SECP256k1
from ecdsa.keys import SigningKey, VerifyingKey


# TODO: expand this -> with actual constraints
username_t = constr(min_length=2, max_length=128)
hash_digest_t = str
nonce_t = conint(ge=0)
amount_t = conint(ge=1, le=1)
serialized_block_payload = bytes


GENESIS_BLOCK_PREV_HASH: hash_digest_t = "0"
QUARRY_ACCOUNT: username_t = "000"


class Wallet:
    def __init__(self, sk: SigningKey, vk: VerifyingKey):
        self.signing_key = sk
        self.verifying_key = vk

    @property
    def incoming_account(self) -> username_t:
        return self.verifying_key.to_string().hex()

    @classmethod
    def new(cls):
        sk = SigningKey.generate(curve=SECP256k1)
        vk = sk.verifying_key
        return cls(sk, vk)


@dataclass(frozen=True)
class Transaction:
    pass


@dataclass(frozen=True)
class Transfer(Transaction):
    from_account: username_t
    to_account: username_t
    amount: amount_t = 1

    @classmethod
    def new(from_account: username_t, to_account: username_t):
        return cls(to_account=to_account, from_account=from_account, amount=1)

    @classmethod
    def coinbase(cls, miner_account: username_t):
        return cls(to_account=miner_account, from_account=QUARRY_ACCOUNT, amount=1)


@dataclass(frozen=True)
class BlockIntent:
    previous_block_hash: hash_digest_t
    transactions: Sequence[Transaction]
    timestamp: int

    @classmethod
    def genesis(cls, transactions: Sequence[Transaction], now_fn=None) -> "BlockIntent":
        now_fn = now_fn or (lambda: int(datetime.utcnow().timestamp()))
        ts = now_fn()

        return cls(previous_block_hash=GENESIS_BLOCK_PREV_HASH, timestamp=ts, transactions=transactions)

    @classmethod
    def next(cls, previous: "Block", transactions: Sequence[Transaction], now_fn=None) -> "BlockIntent":
        now_fn = now_fn or (lambda: int(datetime.utcnow().timestamp()))
        ts = now_fn()

        return cls(previous_block_hash=previous.hash, timestamp=ts, transactions=transactions)

    def _serialize(self, nonce: Optional[nonce_t] = None) -> serialized_block_payload:
        if nonce is None:
            nonce = self.nonce

        # TODO: deterministically cast transactions into JSON array, have a seperate method for that -> it's already sequential, so JSON dumps? :D - but it can fail on stuff like key ordering -> test it!
        _data = json.dumps(self, default=pydantic_encoder)
        data = json.loads(_data)
        data["nonce"] = nonce
        dump = json.dumps(data)
        return dump.encode("utf-8")


@dataclass(frozen=True)
class Block(BlockIntent):
    nonce: nonce_t
    transactions: Tuple[Transaction, ...]
    hash: hash_digest_t

    @staticmethod
    def _hash(payload: serialized_block_payload) -> hash_digest_t:
        m = hashlib.sha256()
        m.update(payload)

        return m.digest().hex()

    @staticmethod
    def _is_passed_difficulty(digest: hash_digest_t) -> bool:
        return digest.startswith("0000")

    @staticmethod
    def _mine(bi: BlockIntent, is_nonce_found_fn=None) -> nonce_t:
        is_nonce_found_fn = is_nonce_found_fn or Block._is_passed_difficulty

        for nonce_candidate in itertools.count(start=0):
            payload = bi._serialize(nonce=nonce_candidate)

            if is_nonce_found_fn(Block._hash(payload)):
                return nonce_candidate

    @classmethod
    def mine_from_intent(cls, bi: BlockIntent, mine_fn=None):
        mine_fn = mine_fn or Block._mine
        nonce = mine_fn(bi)

        return cls(previous_block_hash=bi.previous_block_hash, nonce=nonce, timestamp=bi.timestamp, transactions=bi.transactions, hash=cls._hash(bi._serialize(nonce=nonce)))

    @property
    def is_genesis(self):
        return self.previous_block_hash == GENESIS_BLOCK_PREV_HASH


class Chain:    
    def __init__(self):
        self.blocks = {}
        self.latest = None

    def _append(self, b: Block):
        self.blocks[b.hash] = b
        self.latest = b.hash

    @property
    def latest_block(self):
        return self.blocks[self.latest]

    # def __getitem__(self, trn: int):
        # return self.transactions[trn]

    def try_incorporate(self, b: Block) -> bool:
        self._append(b)
        return True
        # if t.trn not in self.transactions:
            # self._append(t)
            # return True
        # else:
            # matching = self.transactions[t.trn]
            # if matching.timestamp > t.timestamp:
                # self._append(t)
                # return True
            # elif matching == t:
                # return True
            # else:
                # return False

    # def balance(self, username: username_t):
        # return self.ledger[username]

    # @property
    # def ledger(self):
        # ledger = defaultdict(lambda: 0)
        # approved_trns, pending, real = self._sorted_transactions()

        # approved_transfers = [t for t in pending if t.trn in approved_trns]
        # awaiting_transfers = [t for t in pending if t.trn not in approved_trns]
        # effective_transfers = real + approved_transfers

        # for t in effective_transfers:
            # amount = 1

            # ledger[t.from_username] -= amount
            # ledger[t.to_username] += amount

        # for t in awaiting_transfers:
            # amount = 1

            # ledger[t.from_username] -= amount

        # return ledger

    # def _sorted_transactions(self):
        # approved_trns, pending, real = set(), [], [] 
        # for t in self.transactions.values():
            # if type(t) is TransferApproval:
                # approved_trns.add(t.approved_trn)
            # elif type(t) is TransferRequiringApproval:
                # pending.append(t)
            # elif type(t) is Transfer:
                # real.append(t)
            # else: # impossible
                # assert False, "Unsupported type in transaction sorting"

        # return approved_trns, pending, real
