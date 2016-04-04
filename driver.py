#!/bin/python

import time
import pigpio
import socket
import multiprocessing

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

def sampleToBuffer(outbytes):
  while True:
    pi.i2c_write_device(h, [0x37])
    time.sleep(25/1000000)
    (count, data1) = pi.i2c_read_device(h, 8)
    time.sleep(380/1000000)
    (count, data2) = pi.i2c_read_device(h, 4)
    outbytes[:] = data1 + data2;

# x, y, size
def parseBlob(b):
  if (b[0] == 0xff and b[1] == 0xff and b[2] == 0xff):
    return None
  x = b[0] + ((b[2] & 0x30) << 4)
  y = b[1] + ((b[2] & 0xC0) << 2)
  s = b[2] & 0x0F
  return (x, y, s)

def streamFromBuffer(inbytes):
  client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  client.bind(('', 56050))
  (data, address) = client.recvfrom(4096)
  print address

  i = 0;
  while True:
    data = inbytes[:]
    s = (parseBlob(data[0:3]), parseBlob(data[3:6]), parseBlob(data[6:9]), parseBlob(data[9:12]))
    client.sendto(str((i, s)) + '\n', address) 
    print str((i, s))
    i += 1;
    time.sleep(0.01)

# Set pin 4 to a 25 MHz clock
pi.hardware_clock(4, 20000000)

# Set pin 17 to 1 to disable the active-low reset pin
pi.set_mode(17, pigpio.OUTPUT)
pi.write(17, 1)

# Initialize i2c camera
h = initDevice()

# Begin sampling data from the camera
bytes = multiprocessing.Array('i', 12)
p = multiprocessing.Process(target=sampleToBuffer, args=(bytes,))
p.start()

# Wait for an incoming http connection

server_address = ('', 80)

streamFromBuffer(bytes)
