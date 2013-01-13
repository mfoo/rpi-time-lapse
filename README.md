#rpi-time-lapse

This repository tracks code for my panning timelapse photography rig that I am
making. The eventual goal is to produce something similar to [Ben
Wiggins'](http://vimeo.com/50061391) time lapse videos, where the camera
physically moves along a rig during the time lapse process.

The entire time lapse process is automated and controllable via a simple web.py
python script which serves up a simple [Twitter Bootstrap](http://twitter.github.com/bootstrap/)
site with a status overview and some buttons.

The idea is that a Raspberry Pi is mounted with a DSLR and a motor and a power
system on a long track. The Raspberry Pi is connected to the DSLR via a custom
remote shutter trigger and to a motor via a motor driver. When the Pi boots it
sets up an ad-hoc wireless connection via a USB wireless adapter. Any device
that connects to the network will be able to see the web app and control the
system. This means that while out taking photos it is easy to control the
entire rig from my smartphone.
