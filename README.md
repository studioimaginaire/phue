# phue: a Python library for the Philips Hue system.

##Introduction

This is a Python library to control the Philips Hue system.
You can checkout the code here : [https://code.google.com/p/studioimaginaire/source/checkout?repo=python-hue]

Huge thanks to [http://rsmck.co.uk/hue] for hacking the protocol !

I decided to keep it as simple as possible and not rely on external libraries like requests so it's easily portable to any system.

It will automatically get the md5 username for you, if the button is not pressed it will prompt you to press it, use the connect() method to register.  Once pressed it will get the username and store in your home directory in a file called .python_hue

Using the set_state() method you can control pretty much all the parameters :

```python
#!/usr/bin/python

from hue import Bridge

b = Bridge('ip_of_your_bridge')

# If the app is not registered and the button is not pressed, press the button and call connect()
b.connect()

# Get the bridge state (This returns the full dictionary that you can explore)
b.get_info()

# Prints if light 1 is on or not
b.get_state(1, 'on')

# Set brightness of lamp 1 to max
b.set_state(1, 'bri', 254)

# Set brightness of lamp 2 to 50%
b.set_state(2, 'bri', 127)

# Turn lamp 2 on
b.set_state(2,'on', True)

# You can also control multiple lamps by sending a list as lamp_id
b.set_state( [1,2], 'on', True)

# Get the name of a lamp
b.get_state(1, 'name')

# The set_state method can also take a dictionary as the second argument to do more fancy stuff
# This will turn light 1 on with a transition time of 30 seconds
command =  {'transitiontime' : 300, 'on' : True, 'bri' : 254}
b.set_state(1, command)
```

If you want to work in a more object-oriented way, check the bulbs object,
it's a dictionary containing Bulb objects that you can control, either by id or name.

```python
# Get the name of bulb 1
b.lights[1].name

# Set the birghtness of the bulb named "Kitchen"
b.lights["Kitchen"].brightness = 254

# Get lights 1 to 3
lights =  [ b.lights[x] for x in [1,2,3] ]

for light in lights:
   light.on = True
   light.brightness = 127

# Get lights by name
for light in ['Kitchen', 'Bedroom', 'Garage']
    b.lights[light].on = True
    b.lights[light].hue = 15000
    b.lights[light].saturation = 120

```