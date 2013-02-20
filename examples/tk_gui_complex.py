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

b.set_light([1,2,3], 'on', True)

'''
def sel1(data):
    b.set_light(1,{'bri':int(data), 'transitiontime': 1})

def sel2(data):
    b.set_light(2,{'bri':int(data), 'transitiontime': 1})

def sel3(data):
    b.set_light(3,{'bri':int(data), 'transitiontime': 1})
'''
root = Tk()

horizontal_frame = Frame(root)
horizontal_frame.pack(side= BOTTOM)

'''
channel1_frame = Frame(horizontal_frame)
channel1_frame.pack(side = LEFT)

channel2_frame = Frame(horizontal_frame)
channel2_frame.pack(side = LEFT)

channel3_frame = Frame(horizontal_frame)
channel3_frame.pack(side = LEFT)

scale1 = Scale( channel1_frame, from_ = 254, to = 0, command= sel1, length = 200 )
scale1.set(b.get_light(1,'bri'))
scale1.pack(side = TOP)

label1 = Label(channel1_frame)
label1.config(text = b.get_light(1,'name'))
label1.pack(side = TOP)

scale2 = Scale( channel2_frame, from_ = 254, to = 0, command= sel2, length = 200 )
scale2.set(b.get_light(2,'bri'))
scale2.pack(side = TOP)

label2 = Label(channel2_frame)
label2.config(text = b.get_light(2,'name'))
label2.pack(side = TOP)

scale3 = Scale( channel3_frame, from_ = 254, to = 0, command= sel3, length = 200 )
scale3.set(b.get_light(3,'bri'))
scale3.pack(side = TOP)

label3 = Label(channel3_frame)
label3.config(text = b.get_light(3,'name'))
label3.pack(side = TOP)
'''

lights = b.get_light_objects('id')

for light_id in lights:
    channel_frame = Frame(horizontal_frame)
    channel_frame.pack(side = LEFT)
    
    scale = Scale( channel_frame, from_ = 254, to = 0, command= lambda x: b.set_light(light_id,{'bri':int(x), 'transitiontime': 1}), length = 200 )
    print light_id
    scale.set(b.get_light(light_id,'bri'))
    scale.pack(side = TOP)

    label = Label(channel_frame)
    label.config(text = b.get_light(light_id,'name'))
    label.pack(side = TOP)





root.mainloop()