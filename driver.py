#!/usr/bin/python

import signal
import sys
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

# Configures GPIO pins to work with the camera
def initDevice():
  # Set pin 4 to a 25 MHz clock
  pi.hardware_clock(4, 25000000)

  # Set pin 17 to 0 to reset the camera as an active-low reset pin
  pi.set_mode(17, pigpio.OUTPUT)
  pi.write(17, 0)
  time.sleep(0.1)
  pi.write(17, 1)

  # Write startup bytes to the pi
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

# Samples data from input device to the buffer
def sampleToBuffer(outbytes):
  while True:
    try:
      h = initDevice()
      while True:
        pi.i2c_write_device(h, [0x37])
        time.sleep(25/1000000)
        (count, data1) = pi.i2c_read_device(h, 8)
        time.sleep(380/1000000)
        (count, data2) = pi.i2c_read_device(h, 4)
        outbytes[:] = data1 + data2;
    except (KeyboardInterrupt, SystemExit):
      raise
    except:
      pass

# Parses a 3 byte blob into a tuple of x, y, and size
def parseBlob(b):
  if (b[0] == 0xff and b[1] == 0xff and b[2] == 0xff):
    return [-1, -1, -1]
  x = b[0] + ((b[2] & 0x30) << 4)
  y = b[1] + ((b[2] & 0xC0) << 2)
  s = b[2] & 0x0F
  return [x, y, s]

# Streams data from the buffer to the input address
def streamFromBuffer(inbytes, address, streamState):
  try:
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.bind(('', 0))

    i = 0;
    while streamState.value == STREAMING:
      data = inbytes[:]
      packet = parseBlob(data[0:3]) + parseBlob(data[3:6])
      packet += parseBlob(data[6:9]) + parseBlob(data[9:12])
      client.sendto(str([i] + packet) + '\n', address)
      i += 1;
      time.sleep(0.01)
  except (KeyboardInterrupt, SystemExit):
    raise
  except:
    pass

  client.close()
  streamState.value = STOPPED;

# Begin sampling data from the camera to these bytes
bytes = multiprocessing.Array('i', 12 * [-1])
streamState = multiprocessing.Value('i', STOPPED);

class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
  def do_GET(self):
    if self.path == '/status':
      self.send_response(200)
      self.send_header('Content-type', 'text/html')
      self.end_headers()
      statuses = ['STREAMING', 'STOPPING', 'STOPPED']
      self.wfile.write('status is ' + statuses[streamState.value] + '\n')
    else:
      self.send_response(404)
      self.end_headers()

  def do_POST(self):
    try:
      length = int(self.headers.getheader('content-length'))
      field_data = self.rfile.read(length)
      fields = urlparse.parse_qs(field_data)
    except (KeyboardInterrupt, SystemExit):
      raise
    except:
      self.send_response(400) # bad request
      return

    success = False;
    if self.path == '/start':
      success = self.startStreaming(fields)
    elif self.path == '/stop':
      success = True
      self.stopStreaming()
    else:
      self.send_response(404) # not found

    if success:
      self.send_response(200) # ok
    else:
      self.send_response(500) # server error

  # Start streaming by spawning a process to stream data
  def startStreaming(self, fields):
    try:
      address = (fields['ip'][0], int(fields['port'][0]))
      if streamState.value == STOPPED:
        streamState.value = STREAMING
        q = multiprocessing.Process(target=streamFromBuffer, args=(bytes,address,streamState))
        q.start()
        return True
    except (KeyboardInterrupt, SystemExit):
      raise
    except:
      pass
    return False

  def stopStreaming(self):
    if (streamState.value == STREAMING):
      streamState.value = STOPPING;

def runServer():
  while True:
    try:
      server = BaseHTTPServer.HTTPServer(('', 80), Handler)
      server.serve_forever()
    except (KeyboardInterrupt, SystemExit):
      raise

def handleSigTerm(signal, frame):
  print 'got SIGTERM'
  sys.exit(0);

signal.signal(signal.SIGTERM, handleSigTerm)

# Start server
p = multiprocessing.Process(target=runServer, args=())
p.start()

sampleToBuffer(bytes);
