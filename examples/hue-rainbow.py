#!/usr/bin/python
# This script will have all lights, which are on, continuously loop through the rainbow 
# in the time specified in totalTime
from phue import Bridge
import random
from time import sleep

b = Bridge() # Enter bridge IP here.

# If running for the first time, press button on bridge and run with b.connect() uncommented
# b.connect()

lights = b.get_light_objects()

totalTime = 30 # in seconds
transitionTime = 1 # in seconds

maxHue = 65535
hueIncrement = maxHue / totalTime

for light in lights:
    light.transitiontime = transitionTime * 10
    light.brightness = 254
    light.saturation = 254
    # light.on = True # uncomment to turn all lights on

hue = 0
while True:
    for light in lights:
	      light.hue = hue

    hue = (hue + hueIncrement) % maxHue

    sleep(transitionTime)
