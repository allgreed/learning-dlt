import socket
import asyncio
import signal
import os
import sys
import random
import functools
from pprint import pprint
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from src.ui import acquire_user_initials_or_exit
from src.data import State, Transaction, TransactionIntent, Protocol


MINE_USERNAME = "77"
# this is a global, mutable variable, because we're in the 80's
Q = []


async def setup(host, port):
    nodes_candidates = [
        (host, 5555),
        (host, 5556),
        (host, 5557),
    ]
    nodes = [n for n in nodes_candidates if n[0] != host or n[1] != port]

    username = acquire_user_initials_or_exit()
    s = State([])
    broadcast_fn = lambda msg: broadcast(nodes, msg)

    print(f"Starting node at {host}:{port}, other nodes are: {nodes}")

    sync(broadcast_fn=broadcast_fn)
    await asyncio.sleep(0.5)
    s = process_incoming_messages(Q, s, broadcast_fn=broadcast_fn)
    print("initial node sync complete")

    for _ in range(10):
        s = make_transaction(TransactionIntent(MINE_USERNAME, username), s, broadcast_fn=broadcast_fn)
    print(f"Awarded 10 WBE to {username}")
    await asyncio.sleep(0.5)

    s = process_incoming_messages(Q, s, broadcast_fn=broadcast_fn)

    return await loop(s, broadcast_fn=broadcast_fn)


async def loop(s, broadcast_fn):
    s = process_incoming_messages(Q, s, broadcast_fn=broadcast_fn)
    # await user input
    action = await ainput("Enter 's' or 'b' and confirm with enter\n")
    # print(s.balance(username))
    pprint(s.ledger)
    # TODO: in a loop -> if enters other username -> send 1 to that person
        # TODO: add some confirm
        # TODO: check balance if possible
        # TODO: write transaction
        # TODO: send to other nodes

    # TODO: receive hook -> drop newer transaction for particular number
        # but also validate incoming transaction and respond with ok / not ok
    # TODO: every 5 seconds sync

    return await loop(s, broadcast_fn=broadcast_fn)

# AAAAAAAAAAAAAA
class CustomProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        msg = Protocol.decode(data)
        Q.append(msg)


def broadcast(nodes, message):
    for n in nodes:
        send_upd_message(*n, message)


def send_upd_message(host, port, message) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(message.encode(), (host, port))

# AAAAAAAAAAAAAA


# TODO: schedule it more often
def process_incoming_messages(q, s: State, broadcast_fn) -> State:
    new_state = s

    for m in q:
        print(m)

        if isinstance(m, Protocol.HighestTransaction):
            broadcast_fn(f"HIGHEST_TRN_RES {s.highest_transaction_number}")

        elif isinstance(m, Protocol.HighestTransactionResponse):
            network_number = m.number
            if network_number > s.highest_transaction_number:
                print("Sync required, syncing!!!")
                # TODO: implement

    q.clear()

    return new_state


def sync(broadcast_fn):
    broadcast_fn("HIGHEST_TRN")


def make_transaction(ti: TransactionIntent, s: State, broadcast_fn) -> State:
    n = s.highest_transaction_number
    t = Transaction(n + 1, datetime.now(), ti.from_username, ti.to_username)

    if s.balance(t.from_username) < 1 and not t.from_username == MINE_USERNAME:
        ...
        # TODO: fail

    broadcast_fn(f"NEW_TRANS {t.number} {t.from_username} {t.to_username} {t.timestamp}")

    s.append(t)
    return s

def _main():
    host = "127.0.0.1"
    port = int(os.environ["APP_PORT"])

    def signal_handler(_, __):
        os.kill(os.getpid(), 9)

    signal.signal(signal.SIGINT, signal_handler)

    loop = asyncio.get_event_loop()
    t = loop.create_datagram_endpoint(CustomProtocol, local_addr=(host, port))
    loop.run_until_complete(t)
    loop.create_task(setup(host, port))
    loop.run_forever()


async def ainput(prompt: str = ''):
    """https://gist.github.com/delivrance/675a4295ce7dc70f0ce0b164fcdbd798"""
    with ThreadPoolExecutor(1, 'ainput') as executor:
        return (await asyncio.get_event_loop().run_in_executor(executor, input, prompt)).rstrip()

if __name__ == "__main__":
    _main()
