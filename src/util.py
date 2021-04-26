"""
The boring stuff
"""
import signal
import asyncio
import socket
import sys
import os


async def periodic(f, interval: float):
    while True:
        f()
        await asyncio.sleep(interval)


def send_upd_message(host, port, message) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(message, (host, port))


def setup_signal_handlers():
    def signal_handler(_, __):
        os.kill(os.getpid(), 9)

    signal.signal(signal.SIGINT, signal_handler)
