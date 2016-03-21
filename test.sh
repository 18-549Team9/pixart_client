#!/bin/bash

# put clk on gpio 4, rst on gpio17

# enable i2c
cat /etc/modprobe.d/raspi-blacklist.conf |
grep -v 'blacklist i2c-bcm2708' >
temp.txt
cat '# blacklist i2c-bcm2708' >> temp.txt
mv temp.txt /etc/modprobe.d/raspi-blacklist.conf

cat /etc/modules |
grep -v 'i2c-dev' >
temp.txt
cat 'i2c-dev' >> temp.txt
mv temp.txt /etc/modules

# set i2c baud rate to fast 400 KHz
echo 'options i2c_bcm2708 baudrate=400000' > /etc/modprobe.d/i2c.conf

# install i2c tools
apt-get update
apt-get install i2c-tools
adduser pi i2c

# obtain pigpio and start daemon on startup

reboot
