import asyncio
import os
from typing import Sequence

from ecdsa import SigningKey, SECP256k1

from src.util import acquire_user_initials_or_exit, ainput, setup_signal_handlers, send_upd_message, periodic
from src.data import Chain, Wallet, BlockIntent, Block, Transfer
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
    # TODO: seperate UI parts from actual action
    # action = await ainput("Choose one of: [t]ransaction (to) (pending=False), [a]prove (trn), [h]istory, [l]edger, [b]alance, [p]ending and hit enter\n")

    # if action.startswith("t"):
        # args = action.split(" ")

        # if len(args) > 1:
            # receipient = args[1]
            # pending = False

            # if len(args) > 2:
                # pending = True
        # else:
            # receipient = await ainput("Type username [and hit enter]: ")
            # _pending = await ainput("Should this be a pending transaction [y/n]: ")
            # pending = False if _pending != "y" else True 

        # try:
            # ti = TransferIntent(to_username=receipient, from_username=username, pending=pending)
            # make_transfer(ti, state, broadcast_fn=broadcast_fn)
        # except ValueError as e:
            # print(e) 

    # elif action.startswith("a"):
        # args = action.split(" ")

        # if len(args) > 1:
            # trn = args[1]
        # else:
            # trn = await ainput("Type trn [and hit enter]: ")

        # try:
            # a = ApprovalIntent(trn, approver=username)
            # approve(a, state, username, broadcast_fn=broadcast_fn)
        # except ValueError as e:
            # print(e) 

    # elif action.startswith("h"):
        # print("==========================")
        # for t in sorted(state.transactions.values(), key=lambda t: t.timestamp):
            # print(t)
        # print("==========================")

    # elif action.startswith("p"):
        # print("= {0:^6} = | = {1:^6} = | = {2:^3} =".format("FROM", "AMOUNT", "TRN"))
        # for t in sorted(state.pending_for(username), key=lambda t: t.trn):
            # amount = 1
            # print("{0:>10} | {1:>10} | {2:>7}".format(t.from_username, f"{amount} WBE", t.trn))
        # print("==========================")

    # elif action.startswith("l"):
        # print("= {0:^7} =  | = {1:^7} =".format("ACCOUNT", "BALANCE"))
        # for t in sorted(state.ledger.items(), key=lambda t: t[0]):
            # print("{0:>12} | {1:>10}".format(t[0], f"{t[1]} WBE"))
        # print("==========================")

    # elif action.startswith("b"):
        # print(f"% BALANCE for {username} %")
        # print(f"{state.balance(username)} WBE")
        # print("%%%%%%%%%%%%%%%%%%")

    # else:
        # pass


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
