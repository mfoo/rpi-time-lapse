#!/usr/bin/python

# A web.py application for controlling a motion time lapse photography rig.
# With a Raspberry Pi running a DHCP server and configured to set up an ad-hoc
# wireless network on boot and being mounted on the rig, this script runs a
# web.py web server that serves a simple page that can configure and start/stop
# the time lapse process via any device that connects to the network and
# browses to the URL of the server.

import RPi.GPIO as GPIO, Image, time
from datetime import datetime
from math import floor
from time import sleep
from threading import Timer
import web
import json

MOTOR_TRIGGER_PIN = 18
AUTOFOCUS_PIN = 23
SHUTTER_PIN = 24

# Length of the track in cm
RAIL_DISTANCE=1600.0

# Paths for web.py
urls = (
  '/static/.+', 'static',
  '/start', 'start',
  '/stop', 'stop',
  '/status', 'status',
  '/', 'index'
)

class Camera:
  """Represents the camera state. Simple interface to allow taking photos via
  two GPIO pins connected to a remote shutter release. One pin for autofocus,
  one pin for shutter. I am using a Sony Alpha 100, which requires the
  autofocus pins to be grounded before the shutter pin."""

  def __init__(self):
    print "Camera init"
    self.autofocus_triggered = False
    self.shutter_triggered = False

  def autofocus(self, status=True):
    print "Camera autofocus", status
    GPIO.output(AUTOFOCUS_PIN, status)
    self.autofocus_triggered = status

    # Wait for the camera to register the autofocus operation
    sleep(1)

  def shutter(self, status=True):
    print "Camera shutter", status
    if status and not self.autofocus_triggered:
      self.autofocus()

    GPIO.output(SHUTTER_PIN, status)

class Motor:
  """Represents the physical DC motor."""

  def __init__(self):
    print "Motor init"
    pass

  def start(self):
    print "Motor start"
    GPIO.output(MOTOR_TRIGGER_PIN, True)

  def stop(self):
    print "Motor stop"
    GPIO.output(MOTOR_TRIGGER_PIN, False)

  def step(self, time):
    """Will block for the amount of time while the motor is moving as we need
    to be sure it has finished before taking the photo. I am not waiting for
    the motor to stop after cutting the power as it is a very low RPM motor and
    the gears mean that it won't travel much at all after the power has been
    cut."""
    print "Motor step " + str(time)
    self.start()
    sleep(time)
    self.stop()

class TimeLapse:
  PAUSED=0
  RUNNING=1
  STOPPED=2

  def __init__(self):
    print "TimeLapse init"
    self.photo_count = 0
    self.camera = Camera()
    self.motor = Motor()
    self.status = TimeLapse.STOPPED
    self.started_time = None
    self.stopping = False

  def start(self):
    print "TimeLapse start"
    self.status = TimeLapse.RUNNING
    self.started_time = datetime.now()
    t = Timer(0, self.step)
    t.start()

  def step(self):
    print "TimeLapse step"
    if self.stopping:
      self.stopping = False
      self.status = TimeLapse.STOPPED
      self.started_time = None
      return

    if self.status == TimeLapse.PAUSED:
      return

    self.motor.step(1)
    self.camera.shutter()

    t = Timer(1, self.step)
    t.start()

  def pause(self):
    print "TimeLapse pause"
    self.status = TimeLapse.PAUSED

  def resume(self):
    print "TimeLapse resume"
    self.status = TimeLapse.RUNNING
    self.step()

  def stop(self):
    print "TimeLapse stop"
    self.stopping = True

  def get_status_string(self):
    if self.status == TimeLapse.RUNNING:
      return "running"
    if self.status == TimeLapse.PAUSED:
      return "paused"
    if self.status == TimeLapse.STOPPED:
      return "stopped"

  def get_bootstrap_label_class(self):
    if self.status == TimeLapse.RUNNING:
      return "success"
    if self.status == TimeLapse.PAUSED:
      return "warning"
    if self.status == TimeLapse.STOPPED:
      return "important"


timelapse = TimeLapse()

# Setup of web.py templates
render = web.template.render('templates/', globals={'TimeLapse':TimeLapse})

class static:
  """Serves all of the static assets in the static folder"""
  def GET(self, path):
    raise web.seeother(path)

class index:
  """Main web app entry point"""
  def GET(self):
    return render.index()

class start:
  """Start the time lapse"""
  def GET(self):
    timelapse.start()
    return "Success"

class stop:
  """Stop the time lapse"""
  def GET(self):
    timelapse.stop()
    return "Success"

class status:
  """Fetch a string that returns the current timelapse status as a JSON
  object"""
  def _translate_started_time(self, time):
    if time:
      return (datetime.now() - time).total_seconds()
    else:
      return None

  def GET(self):
    return json.dumps({'status' : timelapse.get_status_string(), 'started_at':
      self._translate_started_time(timelapse.started_time), 'photo_count': timelapse.photo_count,
      'bootstrap_label': timelapse.get_bootstrap_label_class()})

if __name__ == "__main__":
  GPIO.setup(MOTOR_TRIGGER_PIN, GPIO.OUT)
  GPIO.setup(AUTOFOCUS_PIN, GPIO.OUT)
  GPIO.setup(SHUTTER_PIN, GPIO.OUT)

  app = web.application(urls, globals())
  app.run()

