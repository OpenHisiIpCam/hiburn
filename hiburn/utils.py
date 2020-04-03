import logging
import os


# -------------------------------------------------------------------------------------------------
_INT_BASES = {"0b": 2, "0o": 8, "0x": 16}
_HSIZE_SUFFIXES = {"b": 1, "k": 1 << 10, "m": 1 << 20, "g": 1 << 30}


def str2bool(val: str):
    return val.lower() in ("y", "yes", "on", "true", "1")


def str2int(val: str):
    return int(val, base=_INT_BASES.get(val[:2].lower(), 10))


def hsize2int(val: str):
    if val[-1].isalpha():
        mul = _HSIZE_SUFFIXES.get(val[-1].lower())
        if mul is None:
            raise ValueError("Couldn't parse {}".format(val))
        return mul * str2int(val[:-1])
    else:
        return str2int(val)


# -------------------------------------------------------------------------------------------------
def align_address_down(alignment, addr):
    return addr // alignment * alignment


# -------------------------------------------------------------------------------------------------
def align_address_up(alignment, addr):
    return align_address_down(alignment, addr + alignment - 1)


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

        logging.getLogger("tftpy").setLevel(logging.WARN)

        self.server = tftpy.TftpServer(root_dir)

        def run():
            self.server.listen(listen_ip, listen_port)

        self.thread = threading.Thread(target=run)


# -------------------------------------------------------------------------------------------------
def upload_files_via_tftp(u_boot_client, files_and_addrs, listen_ip, listen_port=TFTP_SERVER_DEFAULT_PORT):
    import tempfile
    import shutil

    with tempfile.TemporaryDirectory() as tmpdir:
        num = 0
        with TftpContext(tmpdir, listen_ip=listen_ip, listen_port=listen_port):
            for filename, addr in files_and_addrs:
                logging.info("Upload '{}' via TFTP to address {:#x}".format(filename, addr))
                tmp_filename = os.path.join(tmpdir, str(num))
                num += 1
                shutil.copyfile(filename, tmp_filename)
                u_boot_client.tftp(addr, tmp_filename)


# -------------------------------------------------------------------------------------------------
def download_files_via_tftp(uboot, files_addrs_sizes, listen_ip, listen_port=TFTP_SERVER_DEFAULT_PORT):
    import tempfile
    import shutil

    with tempfile.TemporaryDirectory() as tmpdir:
        num = 0
        with TftpContext(tmpdir, listen_ip=listen_ip, listen_port=listen_port):
            for filename, addr, size in files_addrs_sizes:
                logging.info("Download {} bytes from {:#x} to '{}' via TFTP".format(size, addr, filename))
                tmp_filename = os.path.join(tmpdir, str(num))
                num += 1
                uboot.tftp(addr, tmp_filename, size)
                shutil.copyfile(tmp_filename, filename)
