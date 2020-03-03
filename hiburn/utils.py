

# -------------------------------------------------------------------------------------------------
def aligned_address(alignment, addr):
    blocks = addr // alignment + (1 if addr % alignment else 0)
    return blocks * alignment


# -------------------------------------------------------------------------------------------------
TFTP_SERVER_DEFAULT_PORT = 69


class TftpContext:
    """ Context manager for TFTP server
    """

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *args, **kwargs):
        self.server.stop()
        self.thread.join()

    def __init__(self, root_dir, listen_ip, listen_port=TFTP_SERVER_DEFAULT_PORT):
        import tftpy
        import threading
        self.server = tftpy.TftpServer(root_dir)

        def run():
            self.server.listen(listen_ip, listen_port)

        self.thread = threading.Thread(target=run)
