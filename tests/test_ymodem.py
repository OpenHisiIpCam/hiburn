from hiburn.ymodem import YModem
import logging


logging.basicConfig(level=logging.DEBUG)


class FakeSerial:
    def __init__(self, outgoing=b""):
        self.incoming = []
        self.outgoing = outgoing

    def write(self, data):
        self.incoming.append(data)
    
    def read(self, size):
        s = min(len(self.outgoing), size)
        data = self.outgoing[:s]
        self.outgoing = self.outgoing[s:]
        return data


# -------------------------------------------------------------------------------------------------
def test_basic():
    #                               C              NAK       ACK
    serial = FakeSerial(outgoing=(b"\x43" * 10 + b"\x15" + b"\x06" * 3))

    ym = YModem(serial)
    ym.transmit(b"hello serial", file_path="/my/data/path")

    assert len(serial.outgoing) == 0
    assert serial.incoming[0] == (b"\x01\x00\xff/my/data/path\x0012" + b"\x00" * 112 + b"\x1d")
    assert serial.incoming[1] == (b"\x01\x01\xfehello serial" + b"\x00" * 116 + b"\xb4")
    assert serial.incoming[2] == (b"\x04")

