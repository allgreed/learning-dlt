import functools
import logging
from typing import Tuple

from src.util import send_udp_message


class Net:
    def __init__(self, this: Tuple[str, int], proto_cls):
        self.this = this
        self._discover_peers()
        self._fn = functools.partial(Net._broadcast_udp, destinations=self.peers)
        self.protocol = proto_cls

    def _discover_peers(self):
        host = self.this[0]
        nodes_candidates = [
            (host, 5555),
            (host, 5556),
            (host, 5557),
            (host, 5558),
        ]
        self.peers = [n for n in nodes_candidates if n != self.this]

    def broadcast(self, message):
        assert isinstance(message, self.protocol.Message)
        payload = self.protocol.encode(message)

        logging.debug(f"@ {message} @")
        self._fn(payload)

    @staticmethod
    def _broadcast_udp(message, destinations):
        for d in destinations:
            send_udp_message(*d, message)
