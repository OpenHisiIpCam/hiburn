import logging

SOH = b"\x01"
EOT = b"\x04"
ACK = b"\x06"
NAK = b"\x15"
    #   <can> 18H
    #   <C>   43H


COUNTER = 0xFF  # to start from 0x00


def read(serial, size):
    data = serial.read(size)
    logging.debug("<< {}".format(data.hex()))
    return data


def write(serial, data):
    serial.write(data)
    logging.debug(">> {}".format(data.hex()))


def send_chunk(serial, data):
    global COUNTER
    assert len(data) <= 128

    COUNTER = (COUNTER + 1) % (0xFF + 1)

    data = data + b"\0" * (128 - len(data))
    cksum = sum(int(b) for b in data) & 0xFF
    num = COUNTER

    frame = SOH + bytes([num, ~num & 0xFF]) + data + bytes([cksum])

    while True:
        write(serial, frame)
        if read(serial, 1) == ACK:
            logging.debug("Fame {} is ACKed by receiver".format(num))
            break
        logging.debug("Retry to send frame {}...".format(num))


def ymodem_transmit(serial, data=b"hey device!"):
    global COUNTER
    COUNTER = 0xFF

    logging.info("YMODEM waits for handshake... (it may be about 10-20 seconds)")
    while True:
        handshake = read(serial, 1)
        if handshake == NAK:
            break

    logging.info("YMODEM got appropriate handshake, start transmission...")
    send_chunk(serial, b"/some/file/path\0" + str(len(data)).encode("ascii"))

    total_bytes = len(data)
    sent_bytes = 0
    perc = 0
    while data:
        chunk_size = min(len(data), 128)
        send_chunk(serial, data[:chunk_size])
        data = data[chunk_size:]

        sent_bytes += chunk_size
        if (int(sent_bytes/total_bytes * 100) > perc):
            perc = int(sent_bytes/total_bytes * 100)
            logging.info("Sent {} bytes of {} ({}%)".format(sent_bytes, total_bytes, perc))

    while True:
        write(serial, EOT)
        resp = read(serial, 1)
        if resp == ACK:
            break
    
    logging.info("YMODEM finished")