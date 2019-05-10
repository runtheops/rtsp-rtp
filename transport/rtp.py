import socket

from .primitives import RTPDatagram, NalUnit
from .primitives.nal_unit import NalUnitError


class RTPStream:
    def __init__(self, port=0):
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.port = port

    def _bind(self):
        self.socket.bind(('',self.port))
        self.port = self.socket.getsockname()[1]

    def _close(self):
        self.socket.close()

    def __enter__(self):
        self._bind()
        return self

    def __exit__(self, exc_t, exc_v, traceback):
        self._close()

    def __del__(self):
        self._close()

    def generate(self, buf_size=2048):
        while True:
            data = memoryview(self.socket.recv(buf_size))
            if data:
                rtp_payload = RTPDatagram(data).payload

                try:
                    nal_payload = NalUnit(rtp_payload).payload
                except NalUnitError:
                    pass

                yield nal_payload
