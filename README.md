<p align="center">
 <img src="images/hiburn200.png" alt="hiburn">
</p>

<h3 align="center">HiBurn</h3>

---

<p align="center">Deploy automation tool for HiSilicon`s ip camera modules</p>
<p align="center"><em>Part of OpenHisiIpCam project</em></p>

## Why?
To deploy custom firmware (Kernel & RootFS images) onto a HiSilicon camera you usually need to do a number of actions: reset the camera's power, "catch" U-Boot console, configure network, launch TFTP server etc. It becomes especially irritating when you do it over and over again.
The tool is intended to automate this routine. All you need is to launch **hiburn**, reset camera's power and press Enter. We believe it may save your time and nerves =)


## How?
The actual description of capabilities and options you may get via `./hiburn_app.py --help`

There is an example command to upload images into device's memory and boot it  

`./hiburn_app.py --serial-port /dev/ttyCAM1 --serial-baudrate 115200 --net-device_ip 192.168.10.101 --net-host_ip_mask 192.168.10.2/24 --mem-start_addr 0x82000000 --mem-initrd_size 16M --mem-linux_size 256M boot --upload-add 0x81000000 --uimage /path/to/my/kernel/uImage --rootfs /path/yo/my/rootfs.squashfs`

*Notes*:
- Since U-Boot usually connects to default TFTP server's port (69) you will need to be a root (or find some workaround like `authbind`)
- Existing commands write into your device's RAM only; its flash stays pristine. So the device won't turn into a brick if something goes wrong - just reset it.

## Dependencies
The tool is written on python3 and needs (obviously) python3 as well as a few packages from PyPI
* pyserial
* tftpy

**********
The tool is written on Python and it should be easy to check sources and fix/modify it for your needs =)
