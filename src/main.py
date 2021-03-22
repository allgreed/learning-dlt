import socket
import asyncio
import os
import random
import functools
from datetime import datetime

from src.ui import acquire_user_initials_or_exit
from src.data import State, Transaction, TransactionIntent

def main():
    host = "127.0.0.1"
    port = int(os.environ["APP_PORT"])

    loop = asyncio.get_event_loop()
    t = loop.create_datagram_endpoint(CustomProtocol, local_addr=(host, port))
    loop.run_until_complete(t)
    loop.create_task(async_main(host, port))
    # loop.create_task(perpetually(loop, functools.partial(send_delayed_udp_message_to_all, nodes=nodes, message="test")))
    loop.run_forever()

async def async_main(host, port):
    nodes_candidates = [
        (host, 5555),
        (host, 5556),
        (host, 5557),
    ]
    nodes = [n for n in nodes_candidates if n[0] != host or n[1] != port]

    username = acquire_user_initials_or_exit()
    s = State([])

    print(f"Starting node at {host}:{port}, other nodes are: {nodes}")

    # TODO: synchronize
        # ask nodes for highest transaction number
            # if any is greater -> ask for missing transactions one by one

    for _ in range(10):
        s = await make_transaction(TransactionIntent("77", username), s)
        print(f"Sent 1 WBE to {username}")
        
    while True:
        # await user input
        action = input("Enter 's' or 'b' and confirm with enter\n")
        print(s.balance(username))
    # TODO: in a loop -> if enters other username -> send 1 to that person
        # TODO: add some confirm
        # TODO: check balance if possible
        # TODO: write transaction
        # TODO: send to other nodes

    # TODO: receive hook -> drop newer transaction for particular number
        # but also validate incoming transaction and respond with ok / not ok
    # TODO: every 5 seconds synchronize

    

class CustomProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        ip, port, *_ = addr
        print(f"Message [{data.decode()}] from [{ip}]:[{port}]")


async def broadcast(nodes, message):
    await asyncio.gather(*[send_delayed_upd_message(*n, message) for n in nodes])

async def send_upd_message(host, port, message) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    await sock.sendto(message.encode(), (host, port))


async def make_transaction(t: TransactionIntent, s: State) -> State:
    n = s.highest_transaction_number
    maybe_transaction = Transaction(n + 1, datetime.now(), t.from_username, t.to_username)

    # TODO: unless from is only digits
    if s.balance(t.from_username) < 1 and not t.from_username == "77":
        ...
        # TODO: fail

    await issue_transaction(maybe_transaction)

    # TODO: handle errors
    # await ack()
    # await ack()

    # TODO: dehardcode the check
    ok = True
    if ok:
        s.append(maybe_transaction)
        return s
    else: 
        # TODO: err, synchronize?
        return await make_transaction(t, s)


async def issue_transaction(t: Transaction):
    ...

if __name__ == "__main__":
    main()
