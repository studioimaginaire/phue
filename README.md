# phue: A Python library for Philips Hue

Full featured Python library to control the Philips Hue lighting system.

## Features

- Compliant with the Philips Hue API 1.0
- Support for the Philips Hue Remote API
- Support for Lights
- Support for Groups
- Support for Schedules
- Support for Scenes
- Support for Sensors
- Compatible with Python 2.6.x and upwards
- Compatible with Python 3
- No dependencies
- Simple structure, single phue.py file
- Work in a procedural way or object oriented way

## Installation

### Using distutils

```
sudo easy_install phue
```
or
```
pip install phue
```

### Manually

phue consists of a single file (phue.py) that you can put in your python search path or in site-packages (or dist-packages depending on the platform)
You can also simply run it by putting it in the same directory as you main script file or start a python interpreter in the same directory.
phue works with Python 2.6.x, 2.7.x and 3.x

## Examples

### Basic usage

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

# You can also use light names instead of the id
b.get_light('Kitchen')
b.set_light('Kitchen', 'bri', 254)

# Also works with lists
b.set_light(['Bathroom', 'Garage'], 'on', False)

# The set_light method can also take a dictionary as the second argument to do more fancy stuff
# This will turn light 1 on with a transition time of 30 seconds
command =  {'transitiontime' : 300, 'on' : True, 'bri' : 254}
b.set_light(1, command)
```

### Light Objects

If you want to work in a more object-oriented way, there are several ways you can get Light objects.

#### Get a flat list of light objects
```python

lights = b.lights

# Print light names
for l in lights:
    print(l.name)

# Set brightness of each light to 127
for l in lights:
    l.brightness = 127

```

#### Get Light objects as dictionaries

```python
# Get a dictionary with the light id as the key
lights = b.get_light_objects('id')

# Get the name of light 1, set the brightness to 127
lights[1].name
lights[1].brightness = 127

# Get a dictionary with the light name as the key
light_names = b.get_light_objects('name')

# Set the birghtness of the bulb named "Kitchen"
light_names["Kitchen"].brightness = 254

# Set lights using name as key
for light in ['Kitchen', 'Bedroom', 'Garage']
    light_names[light].on = True
    light_names[light].hue = 15000
    light_names[light].saturation = 120

# Get a flat list of the light objects (same as calling b.lights)
lights_list = b.get_light_objects('list')

for light in lights_list:
   light.on = True
   light.brightness = 127

```

### Setting Transition Times

In the Hue API, transition times are specified in deciseconds (tenths
of a second). This
is not tracked as a device setting, but rather needs to be applied on
each individual transition command you want to control the time of.

This can be done by specifying a transitiontime keyword when calling
set_light on the bridge:


```python
# Set brightness of lamp 1 to max, rapidly
b.set_light(1, 'bri', 254, transitiontime=1)
```

As a convenience, the Light class implements a wrapper that remembers
a specified transition time for that light, and applies it
automatically to every transition:

```python
light = light_names['Kitchen']
light.transitiontime = 2
# this next transition will happen rapidly
light.brightness = 20    
```

Note that there is a known bug where turning a light off with the
transitiontime specified can cause the brightness level to behave
erratically when the light is turned back on. See [this
discussion](http://www.everyhue.com/vanilla/discussion/204/bug-with-brightness-when-requesting-ontrue-transitiontime5)
This package attempts to work around this issue by automatically
resetting the brightness when necessary, but this may not work in all
cases.

Transition times from 0-300 deciseconds (i.e. 0 - 30 seconds) have
been tested to work.

### Groups

You can also work with the groups functionality of the Bridge. If groups aren't working, try re-setting the bridge by unpluging it and plugging it back again.

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

### Schedules

You can view, create and delete schedules using the following methods. Note that updates to the Hue API now use local time instead of UTC. If you have issues with schedules not triggering correctly, double check that the time zone is set correctly on your Hue Bridge and that your time in your code is not in UTC by default.

```python

# Get the list of different schedules
b.get_schedule()

# Get the data of a particular schedules
b.get_schedule(1)

# Create a schedule for a light, arguments are name, time, light_id, data (as a dictionary) and optional description
data = {'on': False, 'transitiontime': 600}
b.create_schedule('My schedule', '2012-11-12T22:34:00', 1, data, 'Bedtime' )

# Create a schedule for a group, same as above but with a group_id instead of light_id
data = {'on': False, 'transitiontime': 600}
b.create_group_schedule('My schedule', '2012-11-12T22:34:00', 0, data, 'Bedtime' )

# Delete a schedule
b.delete_schedule(1)

```
## Using the Remote Hue API
There are a few steps to complete before you can use the Remote Hue API:
- Register for a Philips Hue Developer Account
- Use the Developer Account dashboard to create an 'App'
- Use the credentials that Philips provide for your 'App' to create a token file that will be used in your code.

##### Register
The first step is to register for a developer account. Head to https://developers.meethue.com and sign up.

##### Create 'App'
Once you have registered, you can create an app and obtain your credentials at https://developers.meethue.com/user/me/apps.
> Note: When you are completing the App creation process, you will be asked to provide a callback URL. You can provide whatever you want for this URL; preferably an address that doesn't exist.

Once you've registered for your developer account and created an app, you will have been provided with a Client ID and a Client Secret (it currently takes Philips about 24 hours to process your request).

##### Create token file
Now you are ready to create your token file. This is a one off step and once the token is saved you won't need to do this again. The easiest way to create it is to run `phue.py` from a terminal with the `--token` switch. You will be asked to enter your credentials, complete the authorisation in a web browser, and paste the callback URL from your browser once you've finished the authorisation.

Just follow the instructions:
```
$ python phue.py --token
Client ID: <YOUR CLIENT ID>
Client Secret: <YOUR CLIENT SECRET>
App ID: <NAME THAT YOU GAVE TO APP>
Save token to (default: /home/user/.python_hue_token):
Your web browser should open a Philips Hue page asking you to provide authorisation to access your Philips Hue system.
Note that you need to sign in with your Philips Hue account, not your developer account.
If your browser doesn't open, you can manually visit the following address:
https://api.meethue.com/oauth2/auth?clientid=YOURCLIENTID&appid=YOURAPPNAME&deviceid=phuepy&devicename=phuepy&state=421c8c882b7218898290a135f763b153&response_type=code
Once you have provided authorisation, you will be redirected to the callback URL that you specified when setting up your developer credentials.
Please enter the entire address of the page you are sent to after completing authorisation:
Address: <YOUR CALLBACK URL>/callback?code=FJHGSauGl&state=421c8c882b7218898290a135f763b153
Saved token to /home/user/.python_hue_token
```
You can see that you have to option to specify where to save the token. Just hit enter at the `Save token to:` prompt to accept the default.



If you don't want to use the terminal, you can also create the token from a python shell:
```python
>>> from phue import RemoteToken
>>> token = RemoteToken(clientid='YOURCLIENTID', clientsecret='YOURCLIENTSECRET', appid='YOURAPPID', saveto='/home/user/.python_hue_token')
```
You will then be redirected to the Philips Hue webpage to continue authorisation in the same fashion as above.

##### How to use the token file
Now that you have remote access token, you can use it to create your Bridge object in your python code:
```python
from phue import RemoteBridge

b = RemoteBridge()
```
If you chose to save the token file somewhere other than the default location then you will need to provide the path:
```python
b = RemoteBridge(token_path='/path/to/token.file')
```

Once you have your remote bridge object, you can use it just the same as a local bridge. For example:
```python
# Prints if light 1 is on or not
b.get_light(1, 'on')
```
### Some notes on the token file
Obviously, keep it safe. With it, anyone can access your lights.

The Philips Hue remote API uses OAuth2 tokens. This means that the authorisation process actually generates two codes: An access code (used to actually access your lighting system) and a refresh code (used to obtain updated access AND refresh codes). Both these codes expire, but the refresh code is valid for significantly longer than the access code. At the time of writing, access codes are valid for 7 days and refresh codes are valid for 16 weeks, but Philips can change these periods. When the access code expires, the refresh code is used to obtain new codes (both access and refresh). The refresh process is automatically handled, so provided the token is used more frequently than the refresh token validity period (currently 16 weeks) then you should never need to generate a new token. If both codes have expired because the token hasn't been used, then the token becomes useless and you will need to generate new a new token.

You can read more about the token and authentication at https://developers.meethue.com/documentation/remote-api-authentication (a developer account is required to view this page).

#### Interacting with the token
You shouldn't need to interact with the token as the code refresh process is handled automatically. But if you feel like you want to, or have the need to inspect it closer, then the token is just an attribute of the `RemoteBridge` object (aptly named `token`).
```python
>>> from phue import RemoteBridge
>>> b = RemoteBridge()
>>> b.token
<phue.RemoteToken object at 0x102caedd0>
```
Or you can create an instance of the Token without creating a `RemoteBridge` object:
```python
>>> from phue import RemoteToken
# You need to provide the token file path if you're creating new instance of RemoteToken:
>>> token = RemoteToken(load='/path/to/token.file')
>>> token
<phue.RemoteToken object at 0x1030b45d0>
```
##### Useful methods
```python
# Does the Access token require refreshing?
>>> b.token.refresh_required
False

# When does the Access token expire?
>>> b.token.access_expires
'Sun Apr 22 10:35:35 2018'

# When does the Refresh token expire?
>>> b.token.refresh_expires
'Sun Aug  5 10:35:35 2018'

# Datetime objects of expiry
>>> b.token.refresh_token_exp
datetime.datetime(2018, 8, 5, 2, 35, 35, 391951, tzinfo=<phue.UTC object at 0x10307b1d0>)
>>> b.token.access_token_exp
datetime.datetime(2018, 4, 22, 2, 35, 35, 378105, tzinfo=<phue.UTC object at 0x10307b1d0>)

# Is the token valid (i.e. has the refresh code not yet expired)?
>>> b.token.valid
True

# Refresh the access codes:
# Returns True if the codes were refreshed and False if they weren't because they are still valid
>>> b.token.refresh()
False
# Force the access codes to be refreshed even if they are currently valid:
>>> b.token.refresh(force=True)
True

# Display the actual codes:
>>> b.token.access_token
u'ghcgX4uJ3FMdGpBUD7cBGNQV4hVK'
>>> b.token.refresh_token
u'WMsPGsx5FsvUwEpjwz94noxdJ7mtxgNK'

# Save to a new or different token file, invalidating the old token file.
>>> b.token.save('/path/to/new/location.token')
```

## Using phue with Max/MSP via Jython

You can use the phue library within [Max/MSP](http://www.cycling74.com) by using [Nick Rothwell's](http://www.cassiel.com) Jython objects.  He recently updated the version to support Jython 2.7 which is required for phue to work.

Download it here: https://github.com/cassiel/net.loadbang.jython

## Using phue on iOS via Pythonista

You can use phue on your iOS device via the [Pythonista](http://omz-software.com/pythonista) app.
This is a great way to build quick prototypes on iOS as you don't need to compile anything, you can code directly from the device itself.

See this little example:

http://www.youtube.com/embed/6K-fxWG6JSs

## Acknowledgments

Huge thanks to http://rsmck.co.uk/hue for hacking the protocol !

## License

MIT - http://opensource.org/licenses/MIT

"Hue Personal Wireless Lighting" is a trademark owned by Koninklijke Philips Electronics N.V., see www.meethue.com for more information.
I am in no way affiliated with the Philips organization.
