import socket
import asyncio
import os
import random
import functools


def main():
    host = "127.0.0.1"
    port = int(os.environ["APP_PORT"])
    nodes_candidates = [
        (host, 5555),
        (host, 5556),
        (host, 5557),
    ]
    nodes = [n for n in nodes_candidates if n[0] != host or n[1] != port]

    print(f"Starting node at {host}:{port}, other nodes are: {nodes}")

    loop = asyncio.get_event_loop()

    t = loop.create_datagram_endpoint(CustomProtocol, local_addr=(host, port))
    loop.run_until_complete(t)

    loop.create_task(perpetually(loop, functools.partial(send_delayed_udp_message_to_all, nodes=nodes, message="test")))

    loop.run_forever()
    

class CustomProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        ip, port, *_ = addr
        print(f"Message [{data.decode()}] from [{ip}]:[{port}]")


async def send_delayed_udp_message_to_all(nodes, message):
    await asyncio.gather(*[send_delayed_upd_message(*n, message) for n in nodes])

async def send_delayed_upd_message(host, port, message) -> None:
    await asyncio.sleep(random.randint(500, 5000) / 1000)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(message.encode(), (host, port))


async def perpetually(event_loop, f):
    await f()
    event_loop.create_task(perpetually(event_loop, f))

if __name__ == "__main__":
    main()
