import asyncio
import os
import functools
import logging
from typing import Sequence, Dict, Tuple

from ecdsa import SigningKey, SECP256k1

import src.proto as Protocol
from src.proto import SBBSequence
from src.util import setup_signal_handlers, periodic
from src.data import Chain, Wallet, BlockIntent, Block, Transfer, username_t, QUARRY_ACCOUNT
from src.ui import UserInterfaceIOC
from src.miner import Miner
from src.coms import Net


async def main_loop(wallet: Wallet, chain: Chain, miner: Miner, net: Net):
    class UI(UserInterfaceIOC):
        def transfer(self, receipient: username_t):
            if chain.ledger(miner.staged)[wallet.account] <= 0:
                raise ValueError("Insufficient funds, mine a bit and come back later!")

            t = Transfer(from_account=wallet.account, to_account=receipient)
            miner.submit(t)

        def history(self) -> Sequence[str]:
            tt = list(chain.transactions) + miner.staged
            return len(tt), reversed(tt)

        def ledger(self) -> Dict[str, int]:
            return chain.ledger(miner.staged)

        def balance(self) -> Tuple[username_t, int]:
            return chain.ledger(miner.staged)[wallet.account]

        def network_sync(self) -> None:
            net.broadcast(Protocol.GetCount())

        def flip_detailed_logging(self) -> None:
            if logging.getLogger().level == logging.INFO:
                logging.info("Setting log level to DEBUG")
                logging.getLogger().setLevel(logging.DEBUG)
            else:
                logging.info("Setting log level to INFO")
                logging.getLogger().setLevel(logging.INFO)

    ui = UI(you=wallet.account[:8], quarry=QUARRY_ACCOUNT)

    await ui.execute()

    return await main_loop(wallet, chain, miner, net)


async def process_incoming_messages(m: Protocol.Message, seq: SBBSequence, miner: Miner, chain: Chain, net: Net) -> None:
    logging.debug(f"<- {m}")

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
            if chain.try_incorporate(unpack_block(new_block)):
                miner.resync(chain.latest_block)

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
                logging.debug(f"Skipping {block.hash}")
                return

            seq.requesting.remove(block.hash)

            # TODO: validate
                # hash correct
                # all transactions valid
                # ...
            # TODO: when invalid -> drop it

            chain._append(unpack_block(block), update_head=False)

            if seq.requesting:
                cur = next(iter(seq.requesting))
                net.broadcast(Protocol.ReqBlock(hash=cur))
            else:
                prev = { b.previous_block_hash for b in chain.blocks.values() }
                latest_candidates = seq.new - prev

                for c in latest_candidates:
                    if c in chain and chain.length_from(c) > len(chain):
                        chain.latest = c

                chain._gc()

                seq.hashes_equal_blocks()
                miner.start(chain.latest_block)
    else:
        assert 0, "Entered unknown state"


def _synchronize_local(chain, miner, net):
    new_blocks = miner.sync(chain)
    for b in new_blocks:
        net.broadcast(Protocol.NewBlock(pack_block(b)))


def _synchronize_remote(chain, miner, net):
    _synchronize_local(chain, miner, net)
    net.broadcast(Protocol.GetCount())


def main():
    setup_signal_handlers()
    logging.getLogger().setLevel(logging.INFO)

    host = "127.0.0.1"
    port = int(os.environ["APP_PORT"])
    cool_miner = bool(os.environ.get("APP_COOL_MINER",""))
    loop = asyncio.get_event_loop()

    net = Net(this=(host, port))
    wallet = Wallet.new()
    logging.info("my account is: %s", wallet.account)
    miner = Miner(wallet.account, cool=cool_miner)
    seq = SBBSequence()
    chain = Chain()
    f = functools.partial(process_incoming_messages, seq=seq, miner=miner, chain=chain, net=net)

    t = loop.create_datagram_endpoint(mk_handler(f), local_addr=(host, port))
    loop.run_until_complete(t)

    loop.create_task(periodic(lambda: _synchronize_remote(chain, miner, net), 60))
    loop.create_task(main_loop(wallet, chain, miner, net))
    loop.create_task(periodic(lambda: _synchronize_local(chain, miner, net), 0.1))

    miner.start()

    logging.info(f"Starting node at {host}:{port}")
    loop.run_forever()


def pack_block(b: Block) -> Protocol.Block:
    # see BlockIntent._serialize for details
    try:
        hash = b.hash
        nonce = b.nonce
    except AttributeError:
        hash = "1" * 64
        nonce = 1

    return Protocol.Block(hash=hash, hashedContent={"nonce": nonce, "prev_hash": b.previous_block_hash, "timestamp": b.timestamp, "transactions": pack_transactions(b.transactions)})


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
