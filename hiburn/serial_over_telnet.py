from telnetlib import Telnet


class SerialOverTelnet:
    def __str__(self):
        return f"SerialOverTelnet({self.host}:{self.port})"

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.conn = Telnet(host=self.host, port=self.port)
        self._timeout = None

    def readline(self):
        return self.conn.read_until(b"\n", timeout=self._timeout)

    def write(self, data):
        self.conn.write(data)

    def reset_input_buffer(self):
        self.conn.read_very_eager()  # drop all read data

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, timeout):
        self._timeout = timeout
