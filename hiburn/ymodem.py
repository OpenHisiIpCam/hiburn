import logging
import binascii

# http://pauillac.inria.fr/~doligez/zmodem/ymodem.txt

# SOH = b"\x01"
# EOT = b"\x04"
# ACK = b"\x06"
# NAK = b"\x15"
#     #   <can> 18H
#     #   <C>   43H


# COUNTER = 0xFF  # to start from 0x00


# def read(serial, size):
#     data = serial.read(size)
#     logging.debug("<< {}".format(data.hex()))
#     return data


# def write(serial, data):
#     serial.write(data)
#     logging.debug(">> {}".format(data.hex()))


# def send_chunk(serial, data):
#     global COUNTER
#     assert len(data) <= 128

#     COUNTER = (COUNTER + 1) % (0xFF + 1)

#     data = data + b"\0" * (128 - len(data))
#     cksum = sum(int(b) for b in data) & 0xFF
#     num = COUNTER

#     frame = SOH + bytes([num, ~num & 0xFF]) + data + bytes([cksum])

#     while True:
#         write(serial, frame)
#         if read(serial, 1) == ACK:
#             logging.debug("Fame {} is ACKed by receiver".format(num))
#             break
#         logging.debug("Retry to send frame {}...".format(num))


# def ymodem_transmit(serial, data=b"hey device!"):
#     global COUNTER
#     COUNTER = 0xFF

#     logging.info("YMODEM waits for handshake... (it may be about 10-20 seconds)")
#     while True:
#         handshake = read(serial, 1)
#         if handshake == NAK:
#             break

#     logging.info("YMODEM got appropriate handshake, start transmission...")
#     send_chunk(serial, b"/some/file/path\0" + str(len(data)).encode("ascii"))

#     total_bytes = len(data)
#     sent_bytes = 0
#     perc = 0
#     while data:
#         chunk_size = min(len(data), 128)
#         send_chunk(serial, data[:chunk_size])
#         data = data[chunk_size:]

#         sent_bytes += chunk_size
#         if (int(sent_bytes/total_bytes * 100) > perc):
#             perc = int(sent_bytes/total_bytes * 100)
#             logging.info("Sent {} bytes of {} ({}%)".format(sent_bytes, total_bytes, perc))

#     while True:
#         write(serial, EOT)
#         resp = read(serial, 1)
#         if resp == ACK:
#             break
    
#     logging.info("YMODEM finished")



class YModem:
    SOH = b"\x01"
    STX = b"\x02"
    EOT = b"\x04"
    ACK = b"\x06"
    NAK = b"\x15"
    CAN = b"\x18"
    C   = b"\x43"

    MAX_RETRIES = 50
    SHORT_PAYLOAD_SIZE = 128
    LONG_PAYLOAD_SIZE = 1024

    class Stat:
        def __init__(self, total_bytes):
            self.total_bytes = total_bytes
            self.sent_bytes = 0
            self.sent_perc = 0
        
        def on_sent(self, bytes_count):
            self.sent_bytes += bytes_count
            perc = int(self.sent_bytes/self.total_bytes * 100)
            if (perc > self.sent_perc):
                self.sent_perc = perc
                logging.debug("Sent {} bytes of {} ({}%)".format(self.sent_bytes, self.total_bytes, self.sent_perc))

    @staticmethod
    def crc16(data):
        val = binascii.crc_hqx(data, 0)
        return bytes([val >> 8, 0xFF & val])

    @staticmethod
    def checksum(data):
        val = sum(int(b) for b in data) & 0xFF
        return bytes([val])

    def __init__(self, serial):
        self.serial = serial
        self.counter = 0
        self.retry_counter = 0
        self.stat = None

    def send_data(self, data, long=False, crc16=False):
        PAYLOAD_SIZE = self.LONG_PAYLOAD_SIZE if long else self.SHORT_PAYLOAD_SIZE

        head = self.STX if long else self.SOH
        while data:
            chunk_size = min(len(data), PAYLOAD_SIZE)
            num = self.counter & 0xFF
            padding = b"\0" * (PAYLOAD_SIZE - chunk_size)
            payload = data[:chunk_size] + padding
            tail = self.crc16(payload) if crc16 else self.checksum(payload)

            self.counter += 1
            frame = head + bytes([num, ~num & 0xFF]) + payload + tail
            self.send_frame(frame)

            data = data[chunk_size:]

            if self.stat is not None:
                self.stat.on_sent(chunk_size)

    def send_eot(self):
         while True:
            self.serial.write(self.EOT)
            if self.serial.read(1) == self.ACK:
                break
    
    def send_frame(self, frame):
        while self.retry_counter < self.MAX_RETRIES:
            self.serial.write(frame)
            if self.serial.read(1) == self.ACK:
                self.retry_counter = 0
                return
            logging.debug("Retry to send frame {}...".format(frame[:3]))
            self.retry_counter += 1

        raise RuntimeError("Could not send frame {}... after {} retires".format(frame[:3], self.retry_counter))


    def transmit(self, data, file_path="", long=False):
        logging.info("YMODEM waits for handshake... (it may be about 10-20 seconds)")

        crc = False
        while True:
            handshake = self.serial.read(1)
            if handshake == self.C:
                crc = True
                break
            if handshake == self.NAK:
                break

        logging.info("YMODEM got handshake, start transmission...")
        self.send_data(
            data=file_path.encode("ascii") + b"\0" + str(len(data)).encode("ascii"),
            long=long,
            crc16=crc
        )

        self.stat = self.Stat(len(data))
        self.send_data(data=data, long=long, crc16=crc)
        logging.info("YMODEM all {} bytes of data has been transmitted".format(self.stat.total_bytes))
        self.stat = None

        self.send_eot()
        logging.info("YMODEM finished")

