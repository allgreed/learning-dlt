import asyncio
import os
from typing import Sequence, Dict, Tuple

from ecdsa import SigningKey, SECP256k1

from src.util import setup_signal_handlers, send_upd_message, periodic
from src.data import Chain, Wallet, BlockIntent, Block, Transfer, username_t, QUARRY_ACCOUNT
from src.ui import UserInterfaceIOC


async def setup(host, port):
    print(f"Starting node at {host}:{port}")

    wallet = Wallet.new()
    print("my account is:", wallet.account)

    t = Transfer.coinbase(miner_account=wallet.account)
    gbi = BlockIntent.genesis(transactions=[t])
    b = Block.mine_from_intent(gbi)
    print("found block:", b.hash, "[genesis]")
    
    chain = Chain()
    assert chain.try_incorporate(b)

    return await loop(wallet, chain)


async def loop(wallet: Wallet, chain: Chain):
    pending_transactions = []

    class UI(UserInterfaceIOC):
        def transfer(self, receipient: username_t):
            # TODO: ensure balance >= 1
            t = Transfer(from_account=wallet.account, to_account=receipient)
            pending_transactions.append(t)

        def history(self) -> Sequence[str]:
            tt = list(chain.transactions)
            return len(tt), tt

        def ledger(self) -> Dict[str, int]:
            return chain.ledger

        def balance(self) -> Tuple[username_t, int]:
            return chain.balance(wallet.account)


    ui = UI(you=wallet.account[:8], quarry=QUARRY_ACCOUNT)
    await ui.execute()

    t = Transfer.coinbase(miner_account=wallet.account)
    pending_transactions.append(t)
    bi = BlockIntent.next(previous=chain.latest_block, transactions=pending_transactions)
    b = Block.mine_from_intent(bi)
    print("found block:", b.hash)
    assert chain.try_incorporate(b)

    return await loop(wallet, chain)


def main():
    host = "127.0.0.1"
    port = int(os.environ["APP_PORT"])

    loop = asyncio.get_event_loop()
    setup_signal_handlers()

    loop.create_task(setup(host, port))
    loop.run_forever()


if __name__ == "__main__":
    main()
