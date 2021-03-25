"""
The boring stuff
"""
import signal
import asyncio
import socket
import sys
import os
from concurrent.futures import ThreadPoolExecutor


async def periodic(f, interval: float):
    while True:
        f()
        await asyncio.sleep(interval)


def acquire_user_initials_or_exit():
    try:
        username = sys.argv[1]
    except IndexError:
        print("Provide user initials, would you kindly?",file=sys.stderr)
        exit(1)

    if len(username) != 2:
        print("AAA!!!!! must be exactly 2 characters!",file=sys.stderr)
        exit(1)
    if not (username.isascii() and username.isprintable()):
        print("Nice try...",file=sys.stderr)
        exit(2)

    print(f"Hello, {username}")
    return username


async def ainput(prompt: str = ''):
    """https://gist.github.com/delivrance/675a4295ce7dc70f0ce0b164fcdbd798"""
    with ThreadPoolExecutor(1, 'ainput') as executor:
        return (await asyncio.get_event_loop().run_in_executor(executor, input, prompt)).rstrip()


def send_upd_message(host, port, message) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(message, (host, port))


def setup_signal_handlers():
    def signal_handler(_, __):
        os.kill(os.getpid(), 9)

    signal.signal(signal.SIGINT, signal_handler)
