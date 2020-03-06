import serial
import logging
import time


ENCODING = "ascii"
LF = b"\n"
CTRL_C = b"\x03"
PROMPTS = ("hisilicon #",)



class UBootClient:
    def __init__(self, port, baudrate, prompts=PROMPTS):
        self.prompts = set(prompts)
        self.s = serial.Serial(port=port, baudrate=baudrate)
        logging.debug("Serial port is opened")

    def _readline(self):
        line = self.s.readline()
        if line:
            logging.debug("<< {}".format(line))
        return line.decode(ENCODING, errors="replace").rstrip("\r\n")

    def _write(self, data):
        if isinstance(data, str):
            data = data.encode(ENCODING)
        self.s.write(data)
        logging.debug(">> {}".format(data))

    def fetch_console(self):
        """ Wait for running U-Boot and try to enter console mode
        """

        self.s.reset_input_buffer()

        logging.debug("Wait for U-Boot printable output...")
        self.s.timeout = None
        while not self._readline().isprintable():
            pass

        logging.debug("Wait for prompt...")
        self.s.timeout = 0
        while True:
            self.s.write(CTRL_C)
            if self._readline() in self.prompts:
                break

        logging.debug("Prompt received")

        # let the device write all it wants
        time.sleep(0.5)
        self.s.reset_input_buffer()

        self.s.timeout = 0.5
        while True:
            self.s.write(LF)
            if self._readline().strip() in self.prompts:
                break

        logging.info("U-Boot console is fetched")

    def write_command(self, cmd):
        self._write(cmd + "\n")
        echoed = self._readline()
        if not echoed.endswith(cmd):
            raise RuntimeError("echoed data '{}' doesn't match input '{}'".format(echoed, data))

    def read_response(self):
        """ Read lines from serial port till prompt line is received
        """
        response = []
        while True:
            line = self._readline()
            if line.strip() in self.prompts:
                break
            response.append(line)
        return response

    # simple wraps for U-Boot commands are below
    def printenv(self):
        self.write_command("printenv")
        return self.read_response()

    def setenv(self, **kwargs):
        for k, v in kwargs.items():
            v = v.replace(";", "\;")
            self.write_command("setenv {} {}".format(k, v))

    def tftp(self, offset, file_name):
        self.write_command("tftp {:#x} {}".format(offset, file_name))

    def bootm(self, uimage_addr):
        self.write_command("bootm {:#x}".format(uimage_addr))
