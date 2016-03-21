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
  x = b[0] + ((b[2] | 0x30) << 4)
  y = b[1] + ((b[2] | 0xC0) << 2)
  s = b[2] | 0x0F
  return (x, y, s)

def sample(h):
  pi.i2c_write_device(h, [0x37])
  time.sleep(25/1000000)
  (count, data1) = pi.i2c_read_device(h, 8)
  time.sleep(380/1000000)
  (count, data2) = pi.i2c_read_device(h, 4)

  return (parseBlob(data1[0:3]), parseBlob(data1[3:6]), parseBlob(data1[6:] + [data2[0]]), parseBlob(data2[1:]))

h = initDevice()
while True:
  print sample(h)
