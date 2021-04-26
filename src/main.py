import asyncio
import multiprocessing
import os
from typing import Sequence, Dict, Tuple

from ecdsa import SigningKey, SECP256k1

from src.util import setup_signal_handlers, send_upd_message, periodic
from src.data import Chain, Wallet, BlockIntent, Block, Transfer, username_t, QUARRY_ACCOUNT
from src.ui import UserInterfaceIOC

MINER_P = None

async def setup(host, port):
    global MINER_P
    print(f"Starting node at {host}:{port}")

    wallet = Wallet.new()
    print("my account is:", wallet.account)

    # TODO: mine this in the miner
    t = Transfer.coinbase(miner_account=wallet.account)
    gbi = BlockIntent.genesis(transactions=[t])
    b = Block.mine_from_intent(gbi)
    print("found block:", b.hash, "[genesis]")

    input_q, output_q = multiprocessing.Queue(), multiprocessing.Queue()
    MINER_P = multiprocessing.Process(target=miner, args=(wallet.account, b, input_q, output_q))
    MINER_P.start()
    print("Miner started!")
    

    chain = Chain()
    assert chain.try_incorporate(b)

    return await loop(wallet, chain, input_q, output_q)


async def loop(wallet: Wallet, chain: Chain, input_q, output_q):
    class UI(UserInterfaceIOC):
        def transfer(self, receipient: username_t):
            # TODO: this doesn't take into account the pending transactions
            if chain.balance(wallet.account) <= 0:
                raise ValueError("Insufficient funds, mine a bit and come back later!")

            t = Transfer(from_account=wallet.account, to_account=receipient)
            input_q.put(t)

        def history(self) -> Sequence[str]:
            tt = list(chain.transactions)
            return len(tt), tt

        def ledger(self) -> Dict[str, int]:
            return chain.ledger

        def balance(self) -> Tuple[username_t, int]:
            return chain.balance(wallet.account)


    ui = UI(you=wallet.account[:8], quarry=QUARRY_ACCOUNT)
    await ui.execute()

    for _ in range(output_q.qsize()):
        assert chain.try_incorporate(output_q.get())

    return await loop(wallet, chain, input_q, output_q)


def miner(account, sync_block, in_q, out_q):
    latest = sync_block

    while True:
        pending = []
        for _ in range(in_q.qsize()):
            pending.append(in_q.get())

        t = Transfer.coinbase(miner_account=account)
        pending.append(t)
        bi = BlockIntent.next(previous=latest, transactions=pending)
        b = Block.mine_from_intent(bi)
        latest = b
        print("miner found block:", b.hash)
        out_q.put(b)


def main():
    host = "127.0.0.1"
    port = int(os.environ["APP_PORT"])

    loop = asyncio.get_event_loop()
    setup_signal_handlers()

    loop.create_task(setup(host, port))
    loop.run_forever()


if __name__ == "__main__":
    main()
