import functools
import random
import multiprocessing
import time
from typing import Optional, Sequence
from datetime import datetime

from src.data import Block, username_t, Chain, Transfer, BlockIntent, hash_digest_t


class Miner:
    def __init__(self, account: username_t, cool: bool = False):
        self.account = account
        self.input = multiprocessing.Queue()
        self.output = multiprocessing.Queue()
        self.staged = []
        self.cool = cool
        self.p = None

    def start(self, sync_block: Optional[Block] = None):
        _populate_q(self.input, self.staged)
        self.p = multiprocessing.Process(target=self._exec, args=(self.account, sync_block, self.input, self.output))
        self.p.start()

    def stop(self):
        self.p.terminate()
        self.p = None
        _clean_q(self.input)
        _clean_q(self.output)

    def resync(self, sync_block: Optional[Block] = None):
        self.stop()
        self.start(sync_block)

    def submit(self, t: Transfer) -> None:
        self.staged.append(t)
        self.input.put(t)

    def sync(self, chain: Chain):
        if not self.p:
            return 

        added_blocks = []
        for _ in range(self.output.qsize()):
            erm = self.output.get()
            assert chain.try_incorporate(erm)
            added_blocks.append(erm)
            if self.staged and self.staged[0] in erm.transactions:
                self.staged.pop()

        return added_blocks

    def _exec(self, account, sync_block, in_q, out_q):
        latest = sync_block

        while True:
            pending = []
            for _ in range(in_q.qsize()):
                pending.append(in_q.get())

            t = Transfer.coinbase(miner_account=account)
            pending.append(t)

            if latest == None:
                bi = BlockIntent.genesis(transactions=pending)
            else:
                bi = BlockIntent.next(previous=latest, transactions=pending)

            if self.cool:
                # doesn't cause my laptop to overheat ;d
                t = random.randint(2, 8)
                b = Block.mine_from_intent(bi, mine_fn=functools.partial(Block._mine, is_nonce_found_fn=lambda n: True))
                time.sleep(t)
                start = 0
                end = t
            else:
                start = time.time()
                b = Block.mine_from_intent(bi)
                end = time.time()

            latest = b

            print(f"[{datetime.now().strftime('%H:%M:%S')}] miner found block: {b.hash[:16]} in {end - start:.2f}s")
            out_q.put(b)


def _clean_q(q):
    for _ in range(q.qsize()):
        q.get()


def _populate_q(q, data: Sequence):
    for i in data:
        q.put(i)
