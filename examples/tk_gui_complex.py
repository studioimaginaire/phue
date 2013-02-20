#!/usr/bin/python
from Tkinter import *
from phue import Bridge

'''
This example creates 3 sliders for the first 3 lights
and shows the name of the light under each slider.
There is also a checkbox to toggle the light.
'''

b = Bridge() # Enter bridge IP here.

#If running for the first time, press button on bridge and run with b.connect() uncommented
#b.connect()

root = Tk()

horizontal_frame = Frame(root)
horizontal_frame.pack()

lights = b.get_light_objects('id')

for light_id in lights:
    channel_frame = Frame(horizontal_frame)
    channel_frame.pack(side = LEFT)

    scale_command = lambda x, light_id=light_id: b.set_light(light_id,{'bri': int(x), 'transitiontime': 1})
    scale = Scale(channel_frame, from_ = 254, to = 0, command = scale_command, length = 200, showvalue = 0)
    scale.set(b.get_light(light_id,'bri'))
    scale.pack()

    button_var = BooleanVar()
    button_var.set(b.get_light(light_id, 'on'))
    button_command = lambda button_var=button_var, light_id=light_id: b.set_light(light_id, 'on', button_var.get())
    button = Checkbutton(channel_frame, variable = button_var, command = button_command)
    button.pack()

    label = Label(channel_frame)
    label.config(text = b.get_light(light_id,'name'))
    label.pack()

root.mainloop()