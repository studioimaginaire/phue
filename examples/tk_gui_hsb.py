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

def hue_command(x):
    print x

lights = b.get_light_objects('id')

slider_frame = Frame(root)
slider_frame.pack()

channels_frame = Frame(root)
channels_frame.pack()

label_frame = Frame(channels_frame)
label_frame.pack(side=LEFT)

label_name = Label(label_frame)
label_name.config(text = 'Name')
label_name.pack()

label_state = Label(label_frame)
label_state.config(text = 'State')
label_state.pack()

label_select = Label(label_frame)
label_select.config(text = 'Select')
label_select.pack()


hue_slider = Scale(slider_frame, from_ = 65535, to = 0, command = hue_command)
sat_slider = Scale(slider_frame, from_ = 254, to = 0, command = hue_command)
bri_slider = Scale(slider_frame, from_ = 254, to = 0, command = hue_command)
hue_slider.pack(side=LEFT)
sat_slider.pack(side=LEFT)
bri_slider.pack(side=LEFT)


for light_id in lights:
    channel_frame = Frame(channels_frame)
    channel_frame.pack(side = LEFT)
    
    button_var = BooleanVar()
    button_var.set(b.get_light(light_id, 'on'))
    button_command = lambda button_var=button_var, light_id=light_id: b.set_light(light_id, 'on', button_var.get())
    button = Checkbutton(channel_frame, variable = button_var, command = button_command)
    button.pack()

    button2_var = BooleanVar()
    button2_var.set(b.get_light(light_id, 'on'))
    button2_command = lambda button2_var=button2_var, light_id=light_id: b.set_light(light_id, 'on', button2_var.get())
    button2 = Checkbutton(channel_frame, variable = button2_var, command = button2_command)
    button2.pack()

    label = Label(channel_frame)
    label.config(text = b.get_light(light_id,'name'))
    label.pack()

root.mainloop()