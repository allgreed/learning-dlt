import asyncio
import os
import functools
from typing import Sequence, Dict, Tuple

from ecdsa import SigningKey, SECP256k1

import src.proto as Protocol
from src.util import setup_signal_handlers, send_udp_message, periodic
from src.data import Chain, Wallet, BlockIntent, Block, Transfer, username_t, QUARRY_ACCOUNT
from src.ui import UserInterfaceIOC
from src.miner import Miner


# TODO: extract this and net? + hardcode peer discovery?
from statemachine import StateMachine, State
class SBBSequence(StateMachine):
    mining = State("Mining", initial=True)
    sync_hashes = State("Get Block Hashes")
    sync_blocks = State("Get Blocks")

    longer_chain_detected = mining.to(sync_hashes)
    more_hashes_than_blocks = sync_hashes.to(sync_blocks)
    hashes_equal_blocks = sync_blocks.to(mining)


class Net:
    def __init__(self, peers: Sequence[Tuple[str, int]]):
        self.peers = peers
        self._fn = functools.partial(Net._broadcast_udp, destinations=self.peers)

    def broadcast(self, message: Message):
        assert isinstance(message, Protocol.Message)
        message = Protocol.encode(message)

        self._fn(message)

    @staticmethod
    def _broadcast_udp(message, destinations):
        for d in destinations:
            send_udp_message(*d, message)


async def loop(wallet: Wallet, chain: Chain, miner: Miner):
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

    ui = UI(you=wallet.account[:8], quarry=QUARRY_ACCOUNT)

    await ui.execute()

    return await loop(wallet, chain, miner)


async def process_incoming_messages(m: Protocol.Message, seq: SBBSequence, miner: Miner, chain: Chain, net: Net) -> None:
    # if isinstance(m, Protocol.HighestTransaction):
        # broadcast_fn(Protocol.HighestTransactionResponse(local_trn))

    # elif isinstance(m, Protocol.NewTransaction):
        # print(m)
        # t = extract_transaction(m)

        # # was it suppose to mean incorporate or already have the same?
        # if state.incorporate(t):
            # broadcast_fn(Protocol.Ok())
        # else:
            # broadcast_fn(Protocol.NotOk())

    # elif isinstance(m, Protocol.GetTransaction):
        # print(m)
        # t = state[m.number]
        # broadcast_fn(t)

    # elif isinstance(m, Protocol.HighestTransactionResponse):
        # network_trn = m.number
        # if network_trn > local_trn:
            # for i in range(max(local_trn, 0), network_trn + 1):
                # broadcast_fn(Protocol.GetTransaction(i))
    # else:
    print(m)


async def setup(wallet: Wallet, seq: SBBSequence, miner: Miner, chain: Chain, net: Net):
    miner.start()
    print("Miner started!")
    print("my account is:", wallet.account)

    net.broadcast(Protocol.GetCount())

    return await loop(wallet, chain, miner)


def main():
    host = "127.0.0.1"
    port = int(os.environ["APP_PORT"])
    cool_miner = bool(os.environ.get("APP_COOL_MINER",""))

    nodes_candidates = [
        (host, 5555),
        (host, 5556),
        (host, 5557),
    ]
    nodes = [n for n in nodes_candidates if n[0] != host or n[1] != port]

    net = Net(nodes)
    wallet = Wallet.new()
    miner = Miner(wallet.account, cool=cool_miner)
    seq = SBBSequence()
    chain = Chain()
    f = functools.partial(process_incoming_messages, seq=seq, miner=miner, chain=chain, net=net)
    print("Node initialized")

    loop = asyncio.get_event_loop()
    setup_signal_handlers()

    class CustomProtocol(asyncio.DatagramProtocol):
        def datagram_received(self, data, addr):
            msg = Protocol.decode(data)
            asyncio.get_event_loop().create_task(f(msg))

    t = loop.create_datagram_endpoint(CustomProtocol, local_addr=(host, port))
    loop.run_until_complete(t)

    loop.create_task(setup(wallet, seq, miner, chain, net))
    print(f"Started node at {host}:{port}")

    loop.run_forever()


if __name__ == "__main__":
    main()
