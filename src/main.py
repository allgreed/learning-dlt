import asyncio
import os


from src.util import acquire_user_initials_or_exit, ainput, setup_signal_handlers, send_upd_message
from src.data import State, Transaction, TransactionIntent
import src.proto as Protocol


MINE_USERNAME = "77"
# TODO: get rid of this crap
# this is a global, mutable variable, because we're in the 80's
Q = []
global STATE
STATE = State()
BROADCAST_FN = None


async def setup(host, port):
    s = STATE
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

    send_synchronization_pulse(broadcast_fn=broadcast_fn)
    await asyncio.sleep(1)
    print("initial node sync complete")

    for _ in range(10):
        make_transaction(TransactionIntent(MINE_USERNAME, username), s, broadcast_fn=broadcast_fn)
    print(f"Awarded 10 WBE to {username}")
    await asyncio.sleep(0)

    return await loop(s, username, broadcast_fn=broadcast_fn)


async def loop(s, username, broadcast_fn):
    action = await ainput("Choose one of: [t]ransaction (to), [l]edger, [b]alance and hit enter\n")

    if action.startswith("t"):
        args = action.split(" ")

        if len(args) > 1:
            receipient = args[1]
        else:
            receipient = await ainput("Type username [and hit enter]: ")

        try:
            ti = TransactionIntent(to_username=receipient, from_username=username)
            make_transaction(ti, s, broadcast_fn=broadcast_fn)
        except ValueError as e:
            print(e) 

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


async def process_incoming_messages() -> None:
    s = STATE
    q = Q
    broadcast_fn = BROADCAST_FN

    local_trn = s.highest_transaction_number

    for m in q:
        print(m)

        if isinstance(m, Protocol.HighestTransaction):
            broadcast_fn(Protocol.HighestTransactionResponse(local_trn))

        elif isinstance(m, Protocol.NewTransaction):
            t = extract_transaction(m)

            if s.incorporate(t):
                broadcast_fn(Protocol.Ok())
            else:
                broadcast_fn(Protocol.NotOk())

        elif isinstance(m, Protocol.GetTransaction):
            t = s[m.number]
            broadcast_fn(t)

        elif isinstance(m, Protocol.HighestTransactionResponse):
            network_trn = m.number
            if network_trn > local_trn:
                for i in range(max(local_trn, 0), network_trn + 1):
                    broadcast_fn(Protocol.GetTransaction(i))

    q.clear()


def make_transaction(ti: TransactionIntent, state: State, broadcast_fn):
    t = Transaction.from_intent(ti, state.highest_transaction_number)

    if state.balance(t.from_username) < 1 and not t.from_username == MINE_USERNAME:
        raise ValueError("You need to have at least 1 WBE to make a transaction")

    state.incorporate(t)
    broadcast_fn(t)


def broadcast(nodes, message):
    if isinstance(message, Transaction):
        message = pack_transaction(message)

    assert isinstance(message, Protocol.Message)
    message = Protocol.encode(message)

    for n in nodes:
        send_upd_message(*n, message)


def _main():
    host = "127.0.0.1"
    port = int(os.environ["APP_PORT"])

    loop = asyncio.get_event_loop()
    setup_signal_handlers()

    class CustomProtocol(asyncio.DatagramProtocol):
        def datagram_received(self, data, addr):
            msg = Protocol.decode(data)
            Q.append(msg)
            loop = asyncio.get_event_loop()
            loop.create_task(process_incoming_messages())
    t = loop.create_datagram_endpoint(CustomProtocol, local_addr=(host, port))
    loop.run_until_complete(t)

    loop.create_task(setup(host, port))
    loop.run_forever()


def send_synchronization_pulse(broadcast_fn):
    broadcast_fn(Protocol.HighestTransaction())


def extract_transaction(msg: Protocol.NewTransaction) -> Transaction:
    return Transaction(number=msg.number, from_username=msg.from_username, to_username=msg.to_username, timestamp=msg.timestamp)


def pack_transaction(t: Transaction) -> Protocol.NewTransaction:
    return Protocol.NewTransaction(number=t.number, from_username=t.from_username, to_username=t.to_username, timestamp=t.timestamp)


if __name__ == "__main__":
    _main()
