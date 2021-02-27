import socket
import asyncio
import os, random

# inspired by:
# https://stackoverflow.com/questions/46932654/udp-server-with-asyncio

PORT = 5555
# send messages via: nc -u localhost 5555

def main():
    print("Howdy!")
    loop = asyncio.get_event_loop()
    t = loop.create_datagram_endpoint(SyslogProtocol, local_addr=('localhost', PORT))
    loop.run_until_complete(t) # Server starts listening
    loop.run_forever()
    

class SyslogProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        super().__init__()

    def connection_made(self, transport) -> "Used by asyncio":
        self.transport = transport

    def datagram_received(self, data, addr) -> "Main entrypoint for processing message":
        # Here is where you would push message to whatever methods/classes you want.
        print(f"Received Syslog message: {data}")


if __name__ == "__main__":
    main()
