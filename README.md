# hiburn
Deploy automation tool for HiSilicon`s ip camera modules

## Why?
To deploy custom firmware (Kernel&RootFS images) onto a camera usually you need to do set of
actions: reset the camera's power, "catch" U-Boot console, configure network, launch TFTP server
etc. It becomes especially irritating when you do it over and over again.
The tool is intended to automate this process. Usually all you need is to launch **hiburn**, reset camera's
power and press Enter. We believe it may save your time and nerves =)

## How?
`./hiburn_app.py --help`
Since the tool is written on Python it should be easy to check source and fix/modify it for your needs =)

## Dependencies
The tool is written on python3 and needs (obviously) python3 as well as a few packages from PyPI
* pyserial
* tftpy
