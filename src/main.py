import asyncio
import os
from typing import Sequence, Dict, Tuple

from ecdsa import SigningKey, SECP256k1

from src.util import setup_signal_handlers, send_upd_message, periodic
from src.data import Chain, Wallet, BlockIntent, Block, Transfer, username_t, QUARRY_ACCOUNT
from src.ui import UserInterfaceIOC
from src.miner import Miner


async def loop(wallet: Wallet, chain: Chain, miner: Miner):
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

    ui = UI(you=wallet.account[:8], quarry=QUARRY_ACCOUNT)

    await ui.execute()
    miner.sync(chain)

    return await loop(wallet, chain, miner)


async def setup(host, port):
    print(f"Started node at {host}:{port}")

    wallet = Wallet.new()
    print("my account is:", wallet.account)

    miner = Miner(wallet.account)
    miner.start()
    print("Miner started!")

    chain = Chain()
    print("Chain initialized")

    return await loop(wallet, chain, miner)


def main():
    host = "127.0.0.1"
    port = int(os.environ["APP_PORT"])

    loop = asyncio.get_event_loop()
    setup_signal_handlers()

    loop.create_task(setup(host, port))
    loop.run_forever()


if __name__ == "__main__":
    main()
