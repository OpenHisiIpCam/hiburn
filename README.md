<p align="center">
 <img src="images/hiburn200.png" alt="hiburn">
</p>

<h3 align="center">HiBurn</h3>

---

<p align="center">Deploy automation tool for HiSilicon`s ip camera modules</p>
<p align="center"><em>Part of OpenHisiIpCam project</em></p>

## :pencil: Table of Contents
- [About](#about)
- [Installation](#installation)
- [Usage](#usage)

## :eyeglasses: About
To deploy custom firmware (Kernel & RootFS images) onto a HiSilicon camera you usually need to do a number of actions: reset the camera's power, "catch" U-Boot console, configure network, launch TFTP server etc. It becomes especially irritating when you do it over and over again.
The tool is intended to automate this routine. All you need is to launch **hiburn**, reset camera's power and press Enter. We believe it may save your time and nerves =)

## :cd: Installation <a name="installation"></a>

The tool is written on python3 and needs (obviously) python3 as well, as a few packages from PyPI.

Assuming you are on some deb base GNU/Linux (like Debian or Ubuntu), you can satisfy deps following way:
```console 
foo@bar:~$ sudo apt-get install python3 python3-serial python3-pip
foo@bar:~$ sudo pip3 install tftpy
```
## :hammer: Usage <a name="usage"></a>

The actual description of capabilities and options you may get via `./hiburn_app.py --help`:

```console
foo@bar:~/hiburn$ ./hiburn_app.py --help
usage: hiburn_app.py [-h] [--verbose] [--no-fetch] [--print-config]
                     [--reset-cmd RESET_CMD] [--config PATH] [--serial-port V]
                     [--serial-baudrate V] [--net-device_ip V]
                     [--net-host_ip_mask V] [--mem-start_addr V]
                     [--mem-alignment V] [--mem-initrd_size V]
                     [--mem-linux_size V] [--mem-uboot_size V]
                     [--linux_console V]
                     {printenv,ping,download,upload,boot} ...

optional arguments:
  -h, --help            show this help message and exit
  --verbose, -v         Print debug output
  --no-fetch, -n        Assume U-Boot's console is already fetched
  --print-config        Just print result config
  --reset-cmd RESET_CMD
                        Shell command to reset device's power
  --config PATH, -C PATH
                        Config path
  --serial-port V       Serial port to interact with, default: /dev/ttyCAM1
  --serial-baudrate V   Baudrate of the serial port, default: 115200
  --net-device_ip V     Target IP address, default: 192.168.10.101
  --net-host_ip_mask V  Host IP address and mask's length, default:
                        192.168.10.2/24
  --mem-start_addr V    RAM start address, default: 0x80000000
  --mem-alignment V     RAM alignment for uploading, default: 64K
  --mem-initrd_size V   Amount of RAM for initrd, default: 16M
  --mem-linux_size V    Amount of RAM for Linux, default: 256M
  --mem-uboot_size V    , default: 512K
  --linux_console V     Linux load console, default: ttyAMA0,115200

Action:
  {printenv,ping,download,upload,boot}
    printenv            Print U-Boot environment variables
    ping                Configure network on device and ping host
    download            Download data from device's RAM via TFTP
    upload              Upload data to device's RAM via TFTP
    boot                Upload Kernel and RootFS images into device's RAM and
                        boot it
```

### Examples

There is an example command to upload images into device's memory and boot it  

```console
foo@bar:~/hiburn$ ./hiburn_app.py --serial-port /dev/ttyCAM1 --net-device_ip 192.168.10.101 --net-host_ip_mask 192.168.10.2/24 --mem-start_addr 0x80000000 --mem-linux_size 256M boot --uimage /path/to/my/kernel/uImage --rootfs /path/yo/my/rootfs.squashfs`
```

### Notes
- Since U-Boot usually connects to default TFTP server's port (69) you will need to be a root (or find some workaround like `authbind`)
- Existing commands write into your device's RAM only; its flash stays pristine. So the device won't turn into a brick if something goes wrong - just reset it.

*The tool is written on Python and it should be easy to check sources and fix/modify it for your needs :smirk:*
