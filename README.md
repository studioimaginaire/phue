#phue: A Python library for the Philips Hue system.

##Introduction

This is a Python library to control the Philips Hue system.

Huge thanks to [http://rsmck.co.uk/hue] for hacking the protocol !

I decided to keep it as simple as possible and not rely on external libraries like requests so it's easily portable to any system.

It will automatically get the md5 username for you, if the button is not pressed it will prompt you to press it, use the connect() method to register.  Once pressed it will get the username and store in your home directory in a file called .python_hue

##Examples

###Basic usage

Using the set_light and get_light methods you can control pretty much all the parameters :

```python
#!/usr/bin/python

from phue import Bridge

b = Bridge('ip_of_your_bridge')

# If the app is not registered and the button is not pressed, press the button and call connect() (this only needs to be run a single time)
b.connect()

# Get the bridge state (This returns the full dictionary that you can explore)
b.get_api()

# Prints if light 1 is on or not
b.get_light(1, 'on')

# Set brightness of lamp 1 to max
b.set_light(1, 'bri', 254)

# Set brightness of lamp 2 to 50%
b.set_light(2, 'bri', 127)

# Turn lamp 2 on
b.set_light(2,'on', True)

# You can also control multiple lamps by sending a list as lamp_id
b.set_light( [1,2], 'on', True)

# Get the name of a lamp
b.get_light(1, 'name')

# The set_light method can also take a dictionary as the second argument to do more fancy stuff
# This will turn light 1 on with a transition time of 30 seconds
command =  {'transitiontime' : 300, 'on' : True, 'bri' : 254}
b.set_light(1, command)
```

###Light Objects

If you want to work in a more object-oriented way, you can get Light objects using the get_light_objects method. You can use 'id', 'name' or 'list' as argument, it will return a list with no arguments:

```python

# Get a dictionary with the light ids as the key
lights = b.get_light_objects('id')

# Get the name of bulb 1, set the brightness to 127
lights[1].name
lights[1].brightness = 127

# Get a dictionary with the light name as the key
light_names = b.get_light_objects('name')

# Set the birghtness of the bulb named "Kitchen"
light_names["Kitchen"].brightness = 254

# Get lights by name
for light in ['Kitchen', 'Bedroom', 'Garage']
    light_names[light].on = True
    light_names[light].hue = 15000
    light_names[light].saturation = 120

# Get a flat list of the light objects
lights_list = b.get_light_objects('list')

for light in lights_list:
   light.on = True
   light.brightness = 127

```

###Groups

You can also work with the groups functionality of the Bridge. Please note that only group 0 seems to be working properly right now.

```python

# List groups
b.get_group()

# List group 1
b.get_group(1)

# Get name of group 1
b.get_group(1, 'name')

# Get lights in group 1
b.get_group(1,'lights')

# Create a group with lights 1 and 3
b.create_group('Kitchen', [1,3])

# Rename group with id 1
b.set_group(1, 'name', 'New Group Name')

# Change lights within group 1
b.set_group(1, 'lights', [3,4])

# Turn group 1 off
b.set_group(1, 'on', False)

# Delete group 2
b.delete_group(1)

```
