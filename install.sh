#!/bin/bash

# Allow hostname discovery 
apt-get update
apt-get install avahi-daemon avahi-discover libnss-mdns
apt-get install python-smbus i2ctools

# enable i2c
cat /etc/modules |
grep -v 'i2c-dev' | grep -v 'i2c-bcm2708' > 
temp.txt
cat 'i2c-dev' >> temp.txt
cat 'i2c-bcm2708' >> temp.txt
mv temp.txt /etc/modules

cat /etc/modprobe.d/raspi-blacklist.conf |
grep -v 'blacklist spi-bcm2708' |
grep -v 'blacklist i2c-bcm2708' >
temp.txt
cat '# blacklist i2c-bcm2708' >> temp.txt
cat '# blacklist spi-bcm2708' >> temp.txt
mv temp.txt /etc/modprobe.d/raspi-blacklist.conf

cat /boot/config.txt/ |
grep -v 'dtparam=i2c1' | grep -v 'dtparam=i2c_arm' >
temp.txt
cat 'dtparam=i2c1=on' >> temp.txt
cat 'dtparam=i2c_arm=on' >> temp.txt
mv temp.txt /boot/config.txt

# set i2c baud rate to fast 400 KHz
echo 'options i2c_bcm2708 baudrate=400000' > /etc/modprobe.d/i2c.conf

# install i2c tools
adduser pi i2c

# install pigpiod
cd pigpiod
make -j4
make install
make clean

# schedule driver to be run at startup
mv driver.py /usr/local/bin/pixart-driver
line="@reboot              /usr/local/bin/pigpiod"
(crontab -u userhere -l; echo "$line") | crontab -u userhere -
line="@reboot              /usr/local/bin/pixart-driver"
(crontab -u userhere -l; echo "$line") | crontab -u userhere -

reboot
