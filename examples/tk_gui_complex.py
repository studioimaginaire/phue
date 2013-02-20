#!/usr/bin/python
from Tkinter import *
from phue import Bridge

'''
This example creates 3 sliders for the first 3 lights
and shows the name of the light under each slider.
'''

b = Bridge() # Enter bridge IP here.

#If running for the first time, press button on bridge and run with b.connect() uncommented
#b.connect()

root = Tk()

horizontal_frame = Frame(root)
horizontal_frame.pack(side= BOTTOM)

lights = b.get_light_objects('id')

for light_id in lights:
    channel_frame = Frame(horizontal_frame)
    channel_frame.pack(side = LEFT)

    scale = Scale( channel_frame, from_ = 254, to = 0, command = lambda x, light_id=light_id: b.set_light(light_id,{'bri': int(x), 'transitiontime': 1}), length = 200 )
    scale.set(b.get_light(light_id,'bri'))
    scale.pack(side = TOP)

    label = Label(channel_frame)
    label.config(text = b.get_light(light_id,'name'))
    label.pack(side = TOP)

root.mainloop()