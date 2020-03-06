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
- [Typical scenarios](#typical_scenarios)

## :eyeglasses: About <a name="about"></a>

This is U-Boot interaction automation utility. Main function is kernel, rootfs RAM upload and starting system.
This can be useful during development in cases, when you have to repeat reset-upload-start cycle many times.

Basicly, tool catches U-Boot prompt, inputs commands to tune net, set kernel bootargs, start kernel.
U-Boot operates on eraly stage of device boot process, right after power on, so 
HiBurn accepts manual and auto modes for target device reset, 
see [typical scenarios](#typical scenarios) section for details.

## :cd: Installation <a name="installation"></a>

The tool is written on python3 and needs (obviously) python3 as well, as a few packages from PyPI.

Assuming you are on some deb base GNU/Linux (like Debian or Ubuntu), you can satisfy deps following way:
```console 
foo@bar:~$ sudo apt-get install python3 python3-serial python3-pip
foo@bar:~$ sudo pip3 install tftpy
```

## :hammer: Usage <a name="usage"></a>

**TODO**

```console
foo@bar:~/hiburn$ ./burner.py --help
usage: burner2.py [-h] [--log-level LVL] [--mode {raw,camstore}]
                  [--reset-power CMD] --port PORT [--baudrate BAUDRATE]
                  [--uboot-params UBOOT_PARAMS]
                  {printenv,mac,load,mprobe,spi-dump} ...

Interact with devices via serial port

optional arguments:
  -h, --help            show this help message and exit
  --log-level LVL, -l LVL
                        Logging level (default: INFO)
  --mode {raw,camstore}
  --reset-power CMD     Use given command to reset target device
  --port PORT, -p PORT  Serial port device
  --baudrate BAUDRATE   Serial port baudrate for raw mode (default: 115200)
  --uboot-params UBOOT_PARAMS
                        U-Boot console's parameters

Action:
  {printenv,mac,load,mprobe,spi-dump}
    printenv            Print U-Boot's environment variables
    mac                 Change MAC address
    load                Load image onto device and boot it (without burning)
    mprobe              Probe memroy
    spi-dump            Dump SPI-Flash content
```

## :file_folder: Typical scenario <a name="typical_scenarios"></a>

### Manual operation <a name="manual_operation"></a>

This is typical scenario when everything is on your table.

![Manual schema](TODO_IMAGE)

```shell
TODO sample hiburn invoke
```

### Remote debug facility <a name="remote_debug_facility"></a>

> This method is justified only in the case of frequent experiments 
> or remote debugging, as it will require additional hardware.

Idea is to automate device power control.  
This can be done DIY electronics like Arduino.

![Arduino schema](TODO_IMAGE)

Or find something like USB Relay (complete device that allow relay to be controlled via usb HID).

![USB Relay schema](TODO_IMAGE)


```shell
TODO sample power control script
TODO sample hiburn invoke
```




