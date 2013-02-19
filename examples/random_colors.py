#!/usr/bin/python
from phue import Bridge
import random

b = Bridge() # Enter bridge IP here.

#If running for the first time, press button on bridge and run with b.connect() uncommented
#b.connect()

lights = b.get_light_objects()

for light in lights:
	light.brightness = 254
	light.xy = [random.random(),random.random()]


