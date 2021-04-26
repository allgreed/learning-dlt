import asyncio
import os
from typing import Sequence, Dict, Tuple

from ecdsa import SigningKey, SECP256k1

from src.util import setup_signal_handlers, send_upd_message, periodic
from src.data import Chain, Wallet, BlockIntent, Block, Transfer, username_t
from src.ui import UserInterfaceIOC
# import src.proto as Protocol


async def setup(host, port):
    print(f"Starting node at {host}:{port}")

    wallet = Wallet.new()
    print("my account is:", wallet.incoming_account)

    t = Transfer.coinbase(miner_account=wallet.incoming_account)
    gbi = BlockIntent.genesis(transactions=[t])
    b = Block.mine_from_intent(gbi)
    print("found block:", b.hash, "[genesis]")
    
    chain = Chain()
    assert chain.try_incorporate(b)

    return await loop(wallet, chain)


async def loop(wallet: Wallet, chain: Chain):
    class UI(UserInterfaceIOC):
        def transfer(self):
            ...

        def history(self) -> Sequence[str]:
            # for t in sorted(state.transactions.values(), key=lambda t: t.timestamp):
            return ["a", "b", "c"]

        def ledger(self) -> Dict[str, int]:
            # sorted(state.ledger.items(), key=lambda t: t[0])
            return {
                "aaa": 5,
                "bbb": 7,
            }

        def balance(self) -> Tuple[username_t, int]:
            return ("stefan", 5)


    ui = UI()
    await ui.execute()

    t = Transfer.coinbase(miner_account=wallet.incoming_account)
    bi = BlockIntent.next(previous=chain.latest_block, transactions=[t])
    b = Block.mine_from_intent(bi)
    print("found block:", b.hash)
    assert chain.try_incorporate(b)

    return await loop(wallet, chain)


# TODO: this validation should be with the model
# def make_transfer(ti: TransferIntent, state: State, broadcast_fn):
    # t = Transfer.from_intent(ti, state.highest_transaction_number)

    # if state.balance(t.from_username) < 1 and not t.from_username == MINE_USERNAME:
        # raise ValueError("You need to have at least 1 WBE to make a transaction")

    # state.incorporate(t)
    # broadcast_fn(t)


def main():
    host = "127.0.0.1"
    port = int(os.environ["APP_PORT"])

    loop = asyncio.get_event_loop()
    setup_signal_handlers()

    loop.create_task(setup(host, port))
    loop.run_forever()


if __name__ == "__main__":
    main()
