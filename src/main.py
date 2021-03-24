import asyncio
import os

from src.util import acquire_user_initials_or_exit, ainput, setup_signal_handlers, send_upd_message
from src.data import State, Transaction, TransactionIntent
from src.proto import Protocol


MINE_USERNAME = "77"
# TODO: get rid of this crap
# this is a global, mutable variable, because we're in the 80's
Q = []
global STATE
STATE = State()
BROADCAST_FN = None


async def setup(host, port):
    nodes_candidates = [
        (host, 5555),
        (host, 5556),
        (host, 5557),
    ]
    nodes = [n for n in nodes_candidates if n[0] != host or n[1] != port]

    username = acquire_user_initials_or_exit()
    broadcast_fn = lambda msg: broadcast(nodes, msg)
    global BROADCAST_FN
    BROADCAST_FN = broadcast_fn

    print(f"Starting node at {host}:{port}, other nodes are: {nodes}")

    sync(broadcast_fn=broadcast_fn)
    await asyncio.sleep(1)
    print("initial node sync complete")

    for _ in range(10):
        global STATE
        STATE = make_transaction(TransactionIntent(MINE_USERNAME, username), STATE, broadcast_fn=broadcast_fn)
    print(f"Awarded 10 WBE to {username}")
    await asyncio.sleep(0)

    return await loop(STATE, username, broadcast_fn=broadcast_fn)


async def loop(s, username, broadcast_fn):
    action = await ainput("Choose one of: [t]ransaction, [l]edger, [b]alance and hit enter\n")

    if action.startswith("t"):
        ...
        receipient = await ainput("Type username [and hit enter]: ")
        # TODO: test validation at the data layer and handle the err here
        ti = TransactionIntent(to_username=receipient, from_username=username)
        s = make_transaction(ti, s, broadcast_fn=broadcast_fn)
    elif action.startswith("l"):
        print("= {0:^7} =  | = {1:^7} =".format("ACCOUNT", "BALANCE"))
        for t in sorted(s.ledger.items(), key=lambda t: t[0]):
            print("{0:>12} | {1:>10}".format(t[0], f"{t[1]} WBE"))
        print("==========================")
    elif action.startswith("b"):
        print(f"% BALANCE for {username} %")
        print(f"{s.balance(username)} WBE")
        print("%%%%%%%%%%%%%%%%%%")
    else:
        pass

    # TODO: every 5 seconds sync

    return await loop(s, username, broadcast_fn=broadcast_fn)


async def process_incoming_messages() -> State:
    s = STATE
    q = Q
    local_trn = STATE.highest_transaction_number

    for m in q:
        print(m)

        if isinstance(m, Protocol.HighestTransaction):
            BROADCAST_FN(f"HIGHEST_TRN_RES {local_trn}")

        elif isinstance(m, Protocol.NewTransaction):
            t = extract_transaction(m)

            incorporate = STATE.incorporate(t)

            if incorporate:
                BROADCAST_FN(f"OK_MSG")
            else:
                BROADCAST_FN(f"NOK_MSG")

        # TODO: dry
        elif isinstance(m, Protocol.GetTransaction):
            t = s.get(m.number)
            BROADCAST_FN(f"NEW_TRANS {t.number} {t.from_username} {t.to_username} {t.timestamp}")

        elif isinstance(m, Protocol.HighestTransactionResponse):
            network_trn = m.number
            if network_trn > STATE.highest_transaction_number:
                for i in range(max(local_trn -1, 0), network_trn + 1):
                    BROADCAST_FN(f"GET_TRANS {i}")

    q.clear()

    return STATE


def sync(broadcast_fn):
    broadcast_fn("HIGHEST_TRN")


def make_transaction(ti: TransactionIntent, s: State, broadcast_fn) -> State:
    n = s.highest_transaction_number
    # TODO: move this logic into datamodel
    from datetime import datetime
    t = Transaction(n + 1, ti.from_username, ti.to_username, datetime.utcnow().timestamp())

    if s.balance(t.from_username) < 1 and not t.from_username == MINE_USERNAME:
        ...
        # TODO: fail

    broadcast_fn(f"NEW_TRANS {t.number} {t.from_username} {t.to_username} {t.timestamp}")

    s.incorporate(t)
    return s


def broadcast(nodes, message):
    if isinstance(message, Transaction):
        message = pack_transaction(message)

    if isinstance(message, Protocol.Message):
        message = Protocol.encode(message)

    for n in nodes:
        send_upd_message(*n, message)


def _main():
    host = "127.0.0.1"
    port = int(os.environ["APP_PORT"])

    loop = asyncio.get_event_loop()
    setup_signal_handlers()

    class CustomProtocol(asyncio.DatagramProtocol):
        # def connection_made(self, transport):
            # self.transport = transport

        def datagram_received(self, data, addr):
            msg = Protocol.decode(data)
            Q.append(msg)
            loop = asyncio.get_event_loop()
            loop.create_task(process_incoming_messages())
    t = loop.create_datagram_endpoint(CustomProtocol, local_addr=(host, port))
    loop.run_until_complete(t)

    loop.create_task(setup(host, port))
    loop.run_forever()


def extract_transaction(msg: Protocol.NewTransaction) -> Transaction:
    return Transaction(number=msg.number, from_username=msg.from_username, to_username=msg.to_username, timestamp=msg.timestamp)


def pack_transaction(t: Transaction) -> Protocol.NewTransaction:
    return NewTransaction(number=t.number, from_username=t.from_username, to_username=t.to_username, timestamp=t.timestamp)


if __name__ == "__main__":
    _main()
