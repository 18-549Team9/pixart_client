#!/bin/bash

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

apt-get update
apt-get install i2c-tools
adduser pi i2c
reboot
