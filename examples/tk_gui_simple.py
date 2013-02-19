#!/usr/bin/python
from Tkinter import *
from phue import Bridge

'''
This example creates a slider that controls the
brightness of the first 3 lights.
'''

b = Bridge() # Enter bridge IP here.

#If running for the first time, press button on bridge and run with b.connect() uncommented
#b.connect()

b.set_light([1,2,3], 'on', True)

def sel(data):
    b.set_light([1,2,3],{'bri':int(data), 'transitiontime': 1})

root = Tk()
scale = Scale( root, from_ = 254, to = 0, command= sel, length = 200 )
scale.set(b.get_light(1,'bri'))
scale.pack(anchor=CENTER)

root.mainloop()