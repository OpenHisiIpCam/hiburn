import serial
import logging
import time


ENCODING = "ascii"
LF = b"\n"
CTRL_C = b"\x03"
PROMPTS = ("hisilicon #", "Zview #", "xmtech #", "hi3516dv300 #", "hi3519a #", )
READ_TIMEOUT = 0.5


def bytes_to_string(line):
    return line.decode(ENCODING, errors="replace").rstrip("\r\n")


class UBootClient:
    @classmethod
    def create_with_serial(cls, **kwargs):
        return cls(serial.Serial(**kwargs))

    @classmethod
    def create_with_serial_over_telnet(cls, host, port):
        from .serial_over_telnet import SerialOverTelnet
        return cls(SerialOverTelnet(host, port))

    def __init__(self, conn, prompts=PROMPTS):
        self.s = conn
        self.s.timeout = READ_TIMEOUT
        self.prompts = prompts
        logging.debug("UBootClient for {} constructed".format(self.s))

    def _is_prompt(self, line):
        for prompt in self.prompts:
            if line.startswith(prompt):
                return True
        return False

    def _readline(self, raw=False):
        line = self.s.readline()
        if line:
            logging.debug("<< {}".format(line))
        return line if raw else bytes_to_string(line)

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
        while not self._readline().isprintable():
            pass

        logging.debug("Wait for prompt...")
        while True:
            self._write(CTRL_C)
            if self._is_prompt(self._readline()):
                break

        logging.debug("Prompt received")

        while True:
            if self._readline().strip() in self.prompts:
                break

        logging.info("U-Boot console is fetched")

    def write_command(self, cmd):
        self._write(cmd + "\n")
        echoed = self._readline()
        if not echoed.endswith(cmd):
            raise RuntimeError("echoed data '{}' doesn't match input '{}'".format(echoed, cmd))

    def read_response(self, timeout=None, raw=False):
        """ Read lines from serial port till prompt line is received or timeout exceeded
        """

        response = []
        if timeout is not None:
            logging.debug("Read response with timeout={}...".format(timeout))
            self.s.timeout = timeout
        
        while True:
            line = self._readline(raw=True)
            if (not line) and (timeout is not None):
                break  # readline timeout exceeded
            line = bytes_to_string(line)
            if line.strip() in self.prompts:
                break  # prompt line is received
            response.append(line)

        self.s.timeout = READ_TIMEOUT  # restore original timeout
        return response

    # simple wraps for U-Boot commands are below
    def printenv(self):
        self.write_command("printenv")
        return self.read_response()

    def setenv(self, **kwargs):
        for k, v in kwargs.items():
            sv = str(v)
            sv = sv.replace(";", "\;")
            self.write_command("setenv {} {}".format(k, sv))
            self.read_response()

    def ping(self, addr):
        self.write_command("ping {}".format(addr))
        return self.read_response()

    def tftp(self, addr, file_name, size=None):
        if size is None:  # host -> device
            self.write_command("tftp {:#x} {}".format(addr, file_name))
        else:  # device -> host
            self.write_command("tftp {:#x} {} {:#x}".format(addr, file_name, size))
        return self.read_response()

    def bootm(self, uimage_addr, wait=True):
        self.write_command("bootm {:#x}".format(uimage_addr))
        if not wait:
            return
        return self.read_response(timeout=5)

    def sf_probe(self, args):
        self.write_command("sf probe {}".format(args))
        return self.read_response()

    def sf_read(self, dst_addr, flash_offset, size):
        self.write_command("sf read {:#x} {:#x} {:#x}".format(dst_addr, flash_offset, size))
        return self.read_response()
