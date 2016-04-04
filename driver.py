#!/usr/bin/python

import time
import pigpio
import socket
import multiprocessing
import BaseHTTPServer
import urlparse

DEV_ADDR = 0x58
STREAMING = 0
STOPPING = 1
STOPPED = 2
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

def streamFromBuffer(inbytes, address, streamState):
  client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  client.bind(('', 56050))

  i = 0;
  while streamState.value == STREAMING:
    data = inbytes[:]
    s = (parseBlob(data[0:3]), parseBlob(data[3:6]), parseBlob(data[6:9]), parseBlob(data[9:12]))
    client.sendto(str((i, s)) + '\n', address) 
    print str((i, s))
    i += 1;
    time.sleep(0.01)
  streamState.value = STOPPED;

# Set pin 4 to a 25 MHz clock
pi.hardware_clock(4, 20000000)

# Set pin 17 to 1 to disable the active-low reset pin
pi.set_mode(17, pigpio.OUTPUT)
pi.write(17, 1)

# Initialize i2c camera
h = initDevice()

# Begin sampling data from the camera
bytes = multiprocessing.Array('i', range(12))
streamState = multiprocessing.Value('i', STOPPED);
p = multiprocessing.Process(target=sampleToBuffer, args=(bytes,))
p.start()

try:
  # Wait for an incoming http connection
  class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
      if self.path == '/status':
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        statuses = ['STREAMING', 'STOPPING', 'STOPPED']
        self.wfile.write('status is ' + statuses[streamState.value])
      else:
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
      length = int(self.headers.getheader('content-length'))
      field_data = self.rfile.read(length)
      fields = urlparse.parse_qs(field_data)

      if self.path == '/start':
        if 'ip' in fields and 'port' in fields:
          self.startStreaming((fields['ip'], fields['port']))
          self.send_response(200)
          return
      elif self.path == '/stop':
        self.stopStreaming()
        self.send_response(200)
        return

      self.send_response(404)

    def startStreaming(self, host):
      address = (host[0][0], int(host[1][0]))
      if streamState.value == STOPPED:
        streamState.value = STREAMING
        q = multiprocessing.Process(target=streamFromBuffer, args=(bytes,address,streamState))
        q.start()

    def stopStreaming(self):
      if (streamState.value == STREAMING):
        streamState.value = STOPPING;

  server = BaseHTTPServer.HTTPServer(('', 80), Handler)
  server.serve_forever()
except KeyboardInterrupt:
  server.socket.close()

def test():
  while True:
    pass
