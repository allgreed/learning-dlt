import asyncio
import os
import functools
from typing import Sequence, Dict, Tuple

from ecdsa import SigningKey, SECP256k1

import src.proto as Protocol
from src.proto import SBBSequence
from src.util import setup_signal_handlers, periodic
from src.data import Chain, Wallet, BlockIntent, Block, Transfer, username_t, QUARRY_ACCOUNT
from src.ui import UserInterfaceIOC
from src.miner import Miner
from src.coms import Net


async def loop(wallet: Wallet, chain: Chain, miner: Miner, net: Net):
    class UI(UserInterfaceIOC):
        def sync(self):
            miner.sync(chain)

        def transfer(self, receipient: username_t):
            self.sync()
            if chain.ledger(miner.staged)[wallet.account] <= 0:
                raise ValueError("Insufficient funds, mine a bit and come back later!")

            t = Transfer(from_account=wallet.account, to_account=receipient)
            miner.submit(t)

        def history(self) -> Sequence[str]:
            self.sync()
            tt = list(chain.transactions) + miner.staged
            return len(tt), reversed(tt)

        def ledger(self) -> Dict[str, int]:
            self.sync()
            return chain.ledger(miner.staged)

        def balance(self) -> Tuple[username_t, int]:
            self.sync()
            return chain.ledger(miner.staged)[wallet.account]

        def network_sync(self) -> None:
            net.broadcast(Protocol.GetCount())

    ui = UI(you=wallet.account[:8], quarry=QUARRY_ACCOUNT)

    await ui.execute()
    # TODO: after debugging - fix chain not syncing with miner without doing UI action
        # TODO: add miner ability to push sync tasks into the task queue
            # both sync + announce

    return await loop(wallet, chain, miner, net)


async def process_incoming_messages(m: Protocol.Message, seq: SBBSequence, miner: Miner, chain: Chain, net: Net) -> None:
    print(f"$ <- {m}")

    if seq.is_mining:
        if isinstance(m, Protocol.GetCount):
            net.broadcast(Protocol.Count(blocks=len(chain)))

        elif isinstance(m, Protocol.Count):
            if m.blocks > len(chain):
                seq.longer_chain_detected()
                net.broadcast(Protocol.GetBlockHashes())
                miner.stop()

        elif isinstance(m, Protocol.GetBlockHashes):
            net.broadcast(Protocol.BlockHashes(hashes=list(chain.hashes)))

        elif isinstance(m, Protocol.ReqBlock):
            requested_block_hahs = m.hash
            block = chain[requested_block_hahs]
            net.broadcast(Protocol.ExistingBlock(block=pack_block(block)))

        elif isinstance(m, Protocol.NewBlock):
            new_block = m.block
            # TODO: doesn't work or is not valid -> just drop it
            chain.try_incorporate(unpack_block(new_block))

    elif seq.is_sync_hashes:
        if isinstance(m, Protocol.BlockHashes):
            hashes = set(m.hashes)

            if len(hashes) > len(chain):
                seq.more_hashes_than_blocks()
                diff = hashes - set(chain.hashes)

                # this is a nasty hack :C
                seq.requesting = diff
                seq.new = diff.copy()

                cur = next(iter(diff))
                net.broadcast(Protocol.ReqBlock(hash=cur))

    elif seq.is_sync_blocks:
        if isinstance(m, Protocol.ExistingBlock):
            block = m.block

            if block.hash not in seq.requesting:
                print(f"Skipping {block.hash}")
                return

            seq.requesting.remove(block.hash)

            # TODO: validate
                # hash correct
                # all transactions valid
                # ...
            # TODO: when invalid -> drop it

            # ---- entering inconsistent state ----
            chain._append(unpack_block(block), update_head=False)

            if seq.requesting:
                cur = next(iter(seq.requesting))
                net.broadcast(Protocol.ReqBlock(hash=cur))
            else:
                prev = { b.previous_block_hash for b in chain.blocks.values() }
                maybe_latest = seq.new - prev
                latest = maybe_latest.pop()
                assert len(maybe_latest) == 0, "Inconsistent longest chain detected"
                # TODO: wrong - drop the invalid stuff

                chain.latest = latest
                chain._gc()
                # ---- exiting inconsistent state ----

                seq.hashes_equal_blocks()
                try:
                    miner.start(chain.latest_block)
                except KeyError:
                    print("=== CHAIN DUMP ======")
                    print(chain.blocks)
                    print(chain.latest)
                    print("=======================")

                    raise
                print("fin")
                # TODO: make sure that staged transactions are not lost <- test
    else:
        assert 0, "Entered unknown state"


async def setup(wallet: Wallet, seq: SBBSequence, miner: Miner, chain: Chain, net: Net):
    miner.start()
    print("Miner started!")
    print("my account is:", wallet.account)

    net.broadcast(Protocol.GetCount())

    return await loop(wallet, chain, miner, net)


def main():
    host = "127.0.0.1"
    port = int(os.environ["APP_PORT"])
    cool_miner = bool(os.environ.get("APP_COOL_MINER",""))

    net = Net(this=(host, port))
    wallet = Wallet.new()
    miner = Miner(wallet.account, cool=cool_miner)
    seq = SBBSequence()
    chain = Chain()
    f = functools.partial(process_incoming_messages, seq=seq, miner=miner, chain=chain, net=net)
    print("Node initialized")

    setup_signal_handlers()
    loop = asyncio.get_event_loop()
    t = loop.create_datagram_endpoint(mk_handler(f), local_addr=(host, port))
    loop.run_until_complete(t)

    loop.create_task(setup(wallet, seq, miner, chain, net))
    print(f"Started node at {host}:{port}")

    loop.run_forever()


def pack_block(b: Block) -> Protocol.Block:
    return Protocol.Block(hash=b.hash, hashedContent={"nonce": b.nonce, "prev_hash": b.previous_block_hash, "timestamp": b.timestamp, "transactions": pack_transactions(b.transactions)})


def unpack_block(b: Protocol.Block) -> Block:
    return Block(hash=b.hash, nonce=b.hashedContent.nonce, previous_block_hash=b.hashedContent.prev_hash, timestamp=b.hashedContent.timestamp, transactions=unpack_transactions(b.hashedContent.transactions))


def pack_transactions(ts: Sequence[Transfer]) -> Sequence[Protocol.Transaction]:
    return [ Protocol.Transaction(from_ac=t.from_account, to_ac=t.to_account) for t in ts]


def unpack_transactions(ts: Sequence[Protocol.Transaction]) -> Sequence[Transfer]:
    return [ Transfer(from_account=t.from_ac, to_account=t.to_ac) for t in ts]


def mk_handler(f):
    class Handler(asyncio.DatagramProtocol):
        def datagram_received(self, data, addr):
            msg = Protocol.decode(data)
            asyncio.get_event_loop().create_task(f(msg))

    return Handler


if __name__ == "__main__":
    main()
