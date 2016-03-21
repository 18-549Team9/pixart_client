#!/bin/python

import time
import pigpio
DEV_ADDR = 0x58
pi = pigpio.pi()

def initDevice():

  h = pi.i2c_open(1, DEV_ADDR)
  pi.i2c_write_device(h, [0x30, 0x01])
  time.sleep(0.1)
  pi.i2c_write_device(h, [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x90])
  time.sleep(0.1)
  pi.i2c_write_device(h, [0x70, 0x00, 0x41])
  time.sleep(0.1)
  pi.i2c_write_device(h, [0x1A, 0x40, 0x00])
  time.sleep(0.1)
  pi.i2c_write_device(h, [0x33, 0x03])
  time.sleep(0.1)
  pi.i2c_write_device(h, [0x30, 0x08])
  time.sleep(0.1)
  return h

# x, y, size
def parseBlob(b):
  if (b[0] == 0xff and b[1] == 0xff and b[2] == 0xff):
    return None
  x = b[0] + ((b[2] & 0x30) << 4)
  y = b[1] + ((b[2] & 0xC0) << 2)
  s = b[2] & 0x0F
  return (x, y, s)

def sample(h):
  pi.i2c_write_device(h, [0x37])
  time.sleep(25/1000000)
  (count, data1) = pi.i2c_read_device(h, 8)
  time.sleep(380/1000000)
  (count, data2) = pi.i2c_read_device(h, 4)
  data = data1 + data2

  return (parseBlob(data[0:3]), parseBlob(data[3:6]), parseBlob(data[6:9]), parseBlob(data[9:12]))

# Set pin 4 to a 25 MHz clock
pi.hardware_clock(4, 20000000)

# Set pin 17 to 1 to disable the active-low reset pin
pi.set_mode(17, pigpio.OUTPUT)
pi.write(17, 1)

h = initDevice()
