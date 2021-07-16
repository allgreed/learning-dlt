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
from statemachine import StateMachine, State


username_t = constr(regex=r"^([0-9a-f]{128}|0)$")
hash_digest_t = constr(regex=r"^([0-9a-f]{64}|0)$")

nonce_t = conint(ge=0)
amount_t = conint(ge=1, le=1)
serialized_block_payload = bytes
timestamp_t = conint(ge=0)


GENESIS_BLOCK_PREV_HASH: hash_digest_t = "0"
QUARRY_ACCOUNT: username_t = "0"


class SBBSequence(StateMachine):
    mining = State("Mining", initial=True)
    sync_hashes = State("Get Block Hashes")
    sync_blocks = State("Get Blocks")

    longer_chain_detected = mining.to(sync_hashes)
    more_hashes_than_blocks = sync_hashes.to(sync_blocks)
    hashes_equal_blocks = sync_blocks.to(mining)


class Wallet:
    def __init__(self, sk: SigningKey, vk: VerifyingKey):
        self.signing_key = sk
        self.verifying_key = vk

    @property
    def account(self) -> username_t:
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
    timestamp: timestamp_t

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

        # this is a hack, but given the protocol I think it's acceptable
        # also: THIS IS NOT DETERMINISTIC ACROSS IMPLEMENTATIONS!!!
        from src.main import pack_block
        _data = json.dumps(pack_block(self), default=pydantic_encoder)
        data = json.loads(_data)["hashedContent"]

        data["nonce"] = nonce
        dump = json.dumps(data)
        return dump.encode("ascii")


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
        self.latest = GENESIS_BLOCK_PREV_HASH

    def _append(self, b: Block, _update_head: bool = True):
        assert type(b) is Block, f"trying to insert {type(b)} into chain"
        self.blocks[b.hash] = b
        if _update_head:
            self.latest = b.hash

    def is_block_valid(self, b: Block) -> bool:
        if not b._is_passed_difficulty:
            return False

        return True

    def is_valid(self) -> int:
        cur = self.latest_block
        while not cur.is_genesis:
            if not self.is_block_valid(cur):
                return False

            cur = self.blocks[cur.previous_block_hash]

        for account, balance in self.ledger().items():
            if balance < 0 and account != QUARRY_ACCOUNT:
                return False

        return True

    @property
    def latest_block(self):
        return self.blocks[self.latest]

    @property
    def hashes(self):
        return self.blocks.keys()

    def try_incorporate(self, b: Block) -> bool:
        if not self.is_block_valid(b):
            return False

        if b.previous_block_hash != self.latest:
            return False

        self._append(b)
        return True

    def __len__(self):
        return self.length_from(self.latest)

    def __contains__(self, hash):
        return hash in self.blocks

    def length_from(self, tip: Optional[hash_digest_t]) -> int:
        length = 0

        try:
            while tip != GENESIS_BLOCK_PREV_HASH:
                tip = self.blocks[tip].previous_block_hash
                length += 1
        except KeyError:
            # malformed chain, should no be taken into account
            length = -1
        finally:
            return length

    def ledger(self, additional_transactions: Sequence[Transaction] = []):
        ledger = defaultdict(lambda: 0)

        for b in self.blocks.values():
            for t in b.transactions:
                amount = t.amount
                ledger[t.from_account] -= amount
                ledger[t.to_account] += amount

        for t in additional_transactions:
            amount = t.amount
            ledger[t.from_account] -= amount
            ledger[t.to_account] += amount

        return ledger

    def gc(self):
        """
        Delete blocks not reachable from latest
        """

        cur = self.latest_block
        unreached = set(self.blocks.keys())

        while not cur.is_genesis:
            unreached.remove(cur.hash)
            cur = self.blocks[cur.previous_block_hash]
        unreached.remove(cur.hash)

        for bh in unreached: 
            del self.blocks[bh]

    def __getitem__(self, key):
        return self.blocks[key]

    @property
    def transactions(self):
        transaction_packs = map(lambda b: b.transactions, self.blocks.values())
        return itertools.chain(*transaction_packs)
