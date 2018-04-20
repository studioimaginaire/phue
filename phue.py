#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
phue by Nathanaël Lécaudé - A Philips Hue Python library
Contributions by Marshall Perrin, Justin Lintz
https://github.com/studioimaginaire/phue
Original protocol hacking by rsmck : http://rsmck.co.uk/hue

Published under the MIT license - See LICENSE file for more details.

"Hue Personal Wireless Lighting" is a trademark owned by Koninklijke Philips Electronics N.V., see www.meethue.com for more information.
I am in no way affiliated with the Philips organization.

'''

import binascii
import calendar
import hashlib
import json
import logging
import os
import platform
import re
import sys
import socket
import webbrowser
from copy import deepcopy
from datetime import datetime, timedelta
if sys.version_info[0] > 2:
    PY3K = True
else:
    PY3K = False

if PY3K:
    import http.client as httplib
    from datetime import timezone
    from urllib.parse import parse_qs, urlparse, urlencode
    UTC = timezone.utc
else:
    import httplib
    from datetime import tzinfo
    from urllib import urlencode
    from urlparse import parse_qs, urlparse

    FileNotFoundError = IOError

    class UTC(tzinfo):
        def utcoffset(self, dt):
            return timedelta(0)

        def tzname(self, dt):
            return "UTC"

        def dst(self, dt):
            return timedelta(0)
    UTC = UTC()
    input = raw_input

logger = logging.getLogger('phue')


if platform.system() == 'Windows':
    USER_HOME = 'USERPROFILE'
else:
    USER_HOME = 'HOME'

__version__ = '1.1'


def is_string(data):
    """Utility method to see if data is a string."""
    if PY3K:
        return isinstance(data, str)
    else:
        return isinstance(data, str) or isinstance(data, unicode)  # noqa


class PhueException(Exception):

    def __init__(self, id, message):
        self.id = id
        self.message = message


class PhueRegistrationException(PhueException):
    pass


class PhueRequestTimeout(PhueException):
    pass


class Light(object):

    """ Hue Light object

    Light settings can be accessed or set via the properties of this object.

    """
    def __init__(self, bridge, light_id):
        self.bridge = bridge
        self.light_id = light_id

        self._name = None
        self._on = None
        self._brightness = None
        self._colormode = None
        self._hue = None
        self._saturation = None
        self._xy = None
        self._colortemp = None
        self._effect = None
        self._alert = None
        self.transitiontime = None  # default
        self._reset_bri_after_on = None
        self._reachable = None
        self._type = None

    def __repr__(self):
        # like default python repr function, but add light name
        return '<{0}.{1} object "{2}" at {3}>'.format(
            self.__class__.__module__,
            self.__class__.__name__,
            self.name,
            hex(id(self)))

    # Wrapper functions for get/set through the bridge, adding support for
    # remembering the transitiontime parameter if the user has set it
    def _get(self, *args, **kwargs):
        return self.bridge.get_light(self.light_id, *args, **kwargs)

    def _set(self, *args, **kwargs):

        if self.transitiontime is not None:
            kwargs['transitiontime'] = self.transitiontime
            logger.debug("Setting with transitiontime = {0} ds = {1} s".format(
                self.transitiontime, float(self.transitiontime) / 10))

            if (args[0] == 'on' and args[1] is False) or (
                    kwargs.get('on', True) is False):
                self._reset_bri_after_on = True
        return self.bridge.set_light(self.light_id, *args, **kwargs)

    @property
    def name(self):
        '''Get or set the name of the light [string]'''
        if PY3K:
            self._name = self._get('name')
        else:
            self._name = self._get('name').encode('utf-8')
        return self._name

    @name.setter
    def name(self, value):
        old_name = self.name
        self._name = value
        self._set('name', self._name)

        logger.debug("Renaming light from '{0}' to '{1}'".format(
            old_name, value))

        self.bridge.lights_by_name[self.name] = self
        del self.bridge.lights_by_name[old_name]

    @property
    def on(self):
        '''Get or set the state of the light [True|False]'''
        self._on = self._get('on')
        return self._on

    @on.setter
    def on(self, value):

        # Some added code here to work around known bug where
        # turning off with transitiontime set makes it restart on brightness = 1
        # see
        # http://www.everyhue.com/vanilla/discussion/204/bug-with-brightness-when-requesting-ontrue-transitiontime5

        # if we're turning off, save whether this bug in the hardware has been
        # invoked
        if self._on and value is False:
            self._reset_bri_after_on = self.transitiontime is not None
            if self._reset_bri_after_on:
                logger.warning(
                    'Turned off light with transitiontime specified, brightness will be reset on power on')

        self._set('on', value)

        # work around bug by resetting brightness after a power on
        if self._on is False and value is True:
            if self._reset_bri_after_on:
                logger.warning(
                    'Light was turned off with transitiontime specified, brightness needs to be reset now.')
                self.brightness = self._brightness
                self._reset_bri_after_on = False

        self._on = value

    @property
    def colormode(self):
        '''Get the color mode of the light [hs|xy|ct]'''
        self._colormode = self._get('colormode')
        return self._colormode

    @property
    def brightness(self):
        '''Get or set the brightness of the light [0-254].

        0 is not off'''

        self._brightness = self._get('bri')
        return self._brightness

    @brightness.setter
    def brightness(self, value):
        self._brightness = value
        self._set('bri', self._brightness)

    @property
    def hue(self):
        '''Get or set the hue of the light [0-65535]'''
        self._hue = self._get('hue')
        return self._hue

    @hue.setter
    def hue(self, value):
        self._hue = int(value)
        self._set('hue', self._hue)

    @property
    def saturation(self):
        '''Get or set the saturation of the light [0-254]

        0 = white
        254 = most saturated
        '''
        self._saturation = self._get('sat')
        return self._saturation

    @saturation.setter
    def saturation(self, value):
        self._saturation = value
        self._set('sat', self._saturation)

    @property
    def xy(self):
        '''Get or set the color coordinates of the light [ [0.0-1.0, 0.0-1.0] ]

        This is in a color space similar to CIE 1931 (but not quite identical)
        '''
        self._xy = self._get('xy')
        return self._xy

    @xy.setter
    def xy(self, value):
        self._xy = value
        self._set('xy', self._xy)

    @property
    def colortemp(self):
        '''Get or set the color temperature of the light, in units of mireds [154-500]'''
        self._colortemp = self._get('ct')
        return self._colortemp

    @colortemp.setter
    def colortemp(self, value):
        if value < 154:
            logger.warn('154 mireds is coolest allowed color temp')
        elif value > 500:
            logger.warn('500 mireds is warmest allowed color temp')
        self._colortemp = value
        self._set('ct', self._colortemp)

    @property
    def colortemp_k(self):
        '''Get or set the color temperature of the light, in units of Kelvin [2000-6500]'''
        self._colortemp = self._get('ct')
        return int(round(1e6 / self._colortemp))

    @colortemp_k.setter
    def colortemp_k(self, value):
        if value > 6500:
            logger.warn('6500 K is max allowed color temp')
            value = 6500
        elif value < 2000:
            logger.warn('2000 K is min allowed color temp')
            value = 2000

        colortemp_mireds = int(round(1e6 / value))
        logger.debug("{0:d} K is {1} mireds".format(value, colortemp_mireds))
        self.colortemp = colortemp_mireds

    @property
    def effect(self):
        '''Check the effect setting of the light. [none|colorloop]'''
        self._effect = self._get('effect')
        return self._effect

    @effect.setter
    def effect(self, value):
        self._effect = value
        self._set('effect', self._effect)

    @property
    def alert(self):
        '''Get or set the alert state of the light [select|lselect|none]'''
        self._alert = self._get('alert')
        return self._alert

    @alert.setter
    def alert(self, value):
        if value is None:
            value = 'none'
        self._alert = value
        self._set('alert', self._alert)

    @property
    def reachable(self):
        '''Get the reachable state of the light [boolean]'''
        self._reachable = self._get('reachable')
        return self._reachable

    @property
    def type(self):
        '''Get the type of the light [string]'''
        self._type = self._get('type')
        return self._type


class SensorState(dict):
    def __init__(self, bridge, sensor_id):
        self._bridge = bridge
        self._sensor_id = sensor_id

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self._bridge.set_sensor_state(self._sensor_id, self)


class SensorConfig(dict):
    def __init__(self, bridge, sensor_id):
        self._bridge = bridge
        self._sensor_id = sensor_id

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self._bridge.set_sensor_config(self._sensor_id, self)


class Sensor(object):

    """ Hue Sensor object

    Sensor config and state can be read and updated via the properties of this object

    """
    def __init__(self, bridge, sensor_id):
        self.bridge = bridge
        self.sensor_id = sensor_id

        self._name = None
        self._model = None
        self._swversion = None
        self._type = None
        self._uniqueid = None
        self._manufacturername = None
        self._state = SensorState(bridge, sensor_id)
        self._config = {}
        self._recycle = None

    def __repr__(self):
        # like default python repr function, but add sensor name
        return '<{0}.{1} object "{2}" at {3}>'.format(
            self.__class__.__module__,
            self.__class__.__name__,
            self.name,
            hex(id(self)))

    # Wrapper functions for get/set through the bridge
    def _get(self, *args, **kwargs):
        return self.bridge.get_sensor(self.sensor_id, *args, **kwargs)

    def _set(self, *args, **kwargs):
        return self.bridge.set_sensor(self.sensor_id, *args, **kwargs)

    @property
    def name(self):
        '''Get or set the name of the sensor [string]'''
        if PY3K:
            self._name = self._get('name')
        else:
            self._name = self._get('name').encode('utf-8')
        return self._name

    @name.setter
    def name(self, value):
        old_name = self.name
        self._name = value
        self._set('name', self._name)

        logger.debug("Renaming sensor from '{0}' to '{1}'".format(
            old_name, value))

        self.bridge.sensors_by_name[self.name] = self
        del self.bridge.sensors_by_name[old_name]

    @property
    def modelid(self):
        '''Get a unique identifier of the hardware model of this sensor [string]'''
        self._modelid = self._get('modelid')
        return self._modelid

    @property
    def swversion(self):
        '''Get the software version identifier of the sensor's firmware [string]'''
        self._swversion = self._get('swversion')
        return self._swversion

    @property
    def type(self):
        '''Get the sensor type of this device [string]'''
        self._type = self._get('type')
        return self._type

    @property
    def uniqueid(self):
        '''Get the unique device ID of this sensor [string]'''
        self._uniqueid = self._get('uniqueid')
        return self._uniqueid

    @property
    def manufacturername(self):
        '''Get the name of the manufacturer [string]'''
        self._manufacturername = self._get('manufacturername')
        return self._manufacturername

    @property
    def state(self):
        ''' A dictionary of sensor state. Some values can be updated, some are read-only. [dict]'''
        data = self._get('state')
        self._state.clear()
        self._state.update(data)
        return self._state

    @state.setter
    def state(self, data):
        self._state.clear()
        self._state.update(data)

    @property
    def config(self):
        ''' A dictionary of sensor config. Some values can be updated, some are read-only. [dict]'''
        data = self._get('config')
        self._config.clear()
        self._config.update(data)
        return self._config

    @config.setter
    def config(self, data):
        self._config.clear()
        self._config.update(data)

    @property
    def recycle(self):
        ''' True if this resource should be automatically removed when the last reference to it disappears [bool]'''
        self._recycle = self._get('manufacturername')
        return self._manufacturername


class Group(Light):

    """ A group of Hue lights, tracked as a group on the bridge

    Example:

        >>> b = Bridge()
        >>> g1 = Group(b, 1)
        >>> g1.hue = 50000 # all lights in that group turn blue
        >>> g1.on = False # all will turn off

        >>> g2 = Group(b, 'Kitchen')  # you can also look up groups by name
        >>> # will raise a LookupError if the name doesn't match

    """

    def __init__(self, bridge, group_id):
        Light.__init__(self, bridge, None)
        del self.light_id  # not relevant for a group

        try:
            self.group_id = int(group_id)
        except:
            name = group_id
            groups = bridge.get_group()
            for idnumber, info in groups.items():
                if PY3K:
                    if info['name'] == name:
                        self.group_id = int(idnumber)
                        break
                else:
                    if info['name'] == name.decode('utf-8'):
                        self.group_id = int(idnumber)
                        break
            else:
                raise LookupError("Could not find a group by that name.")

    # Wrapper functions for get/set through the bridge, adding support for
    # remembering the transitiontime parameter if the user has set it
    def _get(self, *args, **kwargs):
        return self.bridge.get_group(self.group_id, *args, **kwargs)

    def _set(self, *args, **kwargs):
        # let's get basic group functionality working first before adding
        # transition time...
        if self.transitiontime is not None:
            kwargs['transitiontime'] = self.transitiontime
            logger.debug("Setting with transitiontime = {0} ds = {1} s".format(
                self.transitiontime, float(self.transitiontime) / 10))

            if (args[0] == 'on' and args[1] is False) or (
                    kwargs.get('on', True) is False):
                self._reset_bri_after_on = True
        return self.bridge.set_group(self.group_id, *args, **kwargs)

    @property
    def name(self):
        '''Get or set the name of the light group [string]'''
        if PY3K:
            self._name = self._get('name')
        else:
            self._name = self._get('name').encode('utf-8')
        return self._name

    @name.setter
    def name(self, value):
        old_name = self.name
        self._name = value
        logger.debug("Renaming light group from '{0}' to '{1}'".format(
            old_name, value))
        self._set('name', self._name)

    @property
    def lights(self):
        """ Return a list of all lights in this group"""
        # response = self.bridge.request('GET', '/api/{0}/groups/{1}'.format(self.bridge.username, self.group_id))
        # return [Light(self.bridge, int(l)) for l in response['lights']]
        return [Light(self.bridge, int(l)) for l in self._get('lights')]

    @lights.setter
    def lights(self, value):
        """ Change the lights that are in this group"""
        logger.debug("Setting lights in group {0} to {1}".format(
            self.group_id, str(value)))
        self._set('lights', value)


class AllLights(Group):

    """ All the Hue lights connected to your bridge

    This makes use of the semi-documented feature that
    "Group 0" of lights appears to be a group automatically
    consisting of all lights.  This is not returned by
    listing the groups, but is accessible if you explicitly
    ask for group 0.
    """
    def __init__(self, bridge=None):
        if bridge is None:
            bridge = Bridge()
        Group.__init__(self, bridge, 0)


class Scene(object):
    """ Container for Scene """

    def __init__(self, sid, appdata=None, lastupdated=None,
                 lights=None, locked=False, name="", owner="",
                 picture="", recycle=False, version=0):
        self.scene_id = sid
        self.appdata = appdata or {}
        self.lastupdated = lastupdated
        if lights is not None:
            self.lights = sorted([int(x) for x in lights])
        else:
            self.lights = []
        self.locked = locked
        self.name = name
        self.owner = owner
        self.picture = picture
        self.recycle = recycle
        self.version = version

    def __repr__(self):
        # like default python repr function, but add sensor name
        return '<{0}.{1} id="{2}" name="{3}" lights={4}>'.format(
            self.__class__.__module__,
            self.__class__.__name__,
            self.scene_id,
            self.name,
            self.lights)


class Bridge(object):

    """ Interface to the Hue ZigBee bridge

    You can obtain Light objects by calling the get_light_objects method:

        >>> b = Bridge(ip='192.168.1.100')
        >>> b.get_light_objects()
        [<phue.Light at 0x10473d750>,
         <phue.Light at 0x1046ce110>]

    Or more succinctly just by accessing this Bridge object as a list or dict:

        >>> b[1]
        <phue.Light at 0x10473d750>
        >>> b['Kitchen']
        <phue.Light at 0x10473d750>



    """
    def __init__(self, ip=None, username=None, config_file_path=None, api='/api/'):
        """ Initialization function.

        Parameters:
        ------------
        ip : string
            IP address as dotted quad
        username : string, optional

        """

        if config_file_path is not None:
            self.config_file_path = config_file_path
        elif os.getenv(USER_HOME) is not None and os.access(os.getenv(USER_HOME), os.W_OK):
            self.config_file_path = os.path.join(os.getenv(USER_HOME), '.python_hue')
        elif 'iPad' in platform.machine() or 'iPhone' in platform.machine() or 'iPad' in platform.machine():
            self.config_file_path = os.path.join(os.getenv(USER_HOME), 'Documents', '.python_hue')
        else:
            self.config_file_path = os.path.join(os.getcwd(), '.python_hue')

        self.ip = ip
        self.username = username
        self.lights_by_id = {}
        self.lights_by_name = {}
        self.sensors_by_id = {}
        self.sensors_by_name = {}
        self._name = None
        self.api = api

        # self.minutes = 600 # these do not seem to be used anywhere?
        # self.seconds = 10

        self.connect()

    @property
    def name(self):
        '''Get or set the name of the bridge [string]'''
        self._name = self.request(
            'GET', self.api + self.username + '/config')['name']
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
        data = {'name': self._name}
        self.request(
            'PUT', self.api + self.username + '/config', data)

    def request(self, mode='GET', address=None, data=None):
        """ Utility function for HTTP GET/PUT requests for the API"""
        if self.token:
            connection = httplib.HTTPSConnection(self.ip, timeout=20)
            headers = {
                'Content-Type': 'application/json',
                'Authorization': self.token.bearer()
            }
        else:
            connection = httplib.HTTPConnection(self.ip, timeout=10)
            headers = {}

        try:
            if mode == 'GET' or mode == 'DELETE':
                connection.request(mode, address, None, headers)
            if mode == 'PUT' or mode == 'POST':
                connection.request(mode, address, json.dumps(data), headers)

            logger.debug("{0} {1} {2} {3}".format(mode, address,
                                                  str(data), str(headers)))

        except socket.timeout:
            error = "{} Request to {}{} timed out.".format(mode, self.ip, address)

            logger.exception(error)
            raise PhueRequestTimeout(None, error)

        result = connection.getresponse()
        response = result.read()
        connection.close()
        if PY3K:
            return json.loads(response.decode('utf-8'))
        else:
            logger.debug(response)
            return json.loads(response)

    def get_ip_address(self, set_result=False):

        """ Get the bridge ip address from the meethue.com nupnp api """

        connection = httplib.HTTPSConnection('www.meethue.com')
        connection.request('GET', '/api/nupnp')

        logger.info('Connecting to meethue.com/api/nupnp')

        result = connection.getresponse()

        if PY3K:
            data = json.loads(str(result.read(), encoding='utf-8'))
        else:
            result_str = result.read()
            data = json.loads(result_str)

        """ close connection after read() is done, to prevent issues with read() """

        connection.close()

        ip = str(data[0]['internalipaddress'])

        if ip is not '':
            if set_result:
                self.ip = ip

            return ip
        else:
            return False

    def register_app(self):
        """ Register this computer with the Hue bridge hardware and save the resulting access token """
        registration_request = {"devicetype": "python_hue"}
        response = self.request('POST', self.api, registration_request)
        for line in response:
            for key in line:
                if 'success' in key:
                    with open(self.config_file_path, 'w') as f:
                        logger.info(
                            'Writing configuration file to ' + self.config_file_path)
                        f.write(json.dumps({self.ip: line['success']}))
                        logger.info('Reconnecting to the bridge')
                    self.connect()
                if 'error' in key:
                    error_type = line['error']['type']
                    if error_type == 101:
                        raise PhueRegistrationException(error_type,
                                                        'The link button has not been pressed in the last 30 seconds.')
                    if error_type == 7:
                        raise PhueException(error_type,
                                            'Unknown username')

    def connect(self):
        """ Connect to the Hue bridge """
        logger.info('Attempting to connect to the bridge...')
        # If the ip and username were provided at class init
        if self.ip is not None and self.username is not None:
            logger.info('Using ip: ' + self.ip)
            logger.info('Using username: ' + self.username)
            return

        if self.ip is None or self.username is None:
            try:
                with open(self.config_file_path) as f:
                    config = json.loads(f.read())
                    if self.ip is None:
                        self.ip = list(config.keys())[0]
                        logger.info('Using ip from config: ' + self.ip)
                    else:
                        logger.info('Using ip: ' + self.ip)
                    if self.username is None:
                        self.username = config[self.ip]['username']
                        logger.info(
                            'Using username from config: ' + self.username)
                    else:
                        logger.info('Using username: ' + self.username)
            except Exception as e:
                logger.info(
                    'Error opening config file, will attempt bridge registration')
                self.register_app()

    def get_light_id_by_name(self, name):
        """ Lookup a light id based on string name. Case-sensitive. """
        lights = self.get_light()
        for light_id in lights:
            if PY3K:
                if name == lights[light_id]['name']:
                    return light_id
            else:
                if name.decode('utf-8') == lights[light_id]['name']:
                    return light_id
        return False

    def get_light_objects(self, mode='list'):
        """Returns a collection containing the lights, either by name or id (use 'id' or 'name' as the mode)
        The returned collection can be either a list (default), or a dict.
        Set mode='id' for a dict by light ID, or mode='name' for a dict by light name.   """
        if self.lights_by_id == {}:
            lights = self.request('GET', self.api + self.username + '/lights/')
            for light in lights:
                self.lights_by_id[int(light)] = Light(self, int(light))
                self.lights_by_name[lights[light][
                    'name']] = self.lights_by_id[int(light)]
        if mode == 'id':
            return self.lights_by_id
        if mode == 'name':
            return self.lights_by_name
        if mode == 'list':
            # return ligts in sorted id order, dicts have no natural order
            return [self.lights_by_id[id] for id in sorted(self.lights_by_id)]

    def get_sensor_id_by_name(self, name):
        """ Lookup a sensor id based on string name. Case-sensitive. """
        sensors = self.get_sensor()
        for sensor_id in sensors:
            if PY3K:
                if name == sensors[sensor_id]['name']:
                    return sensor_id
            else:
                if name.decode('utf-8') == sensors[sensor_id]['name']:
                    return sensor_id
        return False

    def get_sensor_objects(self, mode='list'):
        """Returns a collection containing the sensors, either by name or id (use 'id' or 'name' as the mode)
        The returned collection can be either a list (default), or a dict.
        Set mode='id' for a dict by sensor ID, or mode='name' for a dict by sensor name.   """
        if self.sensors_by_id == {}:
            sensors = self.request('GET', self.api + self.username + '/sensors/')
            for sensor in sensors:
                self.sensors_by_id[int(sensor)] = Sensor(self, int(sensor))
                self.sensors_by_name[sensors[sensor][
                    'name']] = self.sensors_by_id[int(sensor)]
        if mode == 'id':
            return self.sensors_by_id
        if mode == 'name':
            return self.sensors_by_name
        if mode == 'list':
            return self.sensors_by_id.values()

    def __getitem__(self, key):
        """ Lights are accessibly by indexing the bridge either with
        an integer index or string name. """
        if self.lights_by_id == {}:
            self.get_light_objects()

        try:
            return self.lights_by_id[key]
        except:
            try:
                if PY3K:
                    return self.lights_by_name[key]
                else:
                    return self.lights_by_name[key.decode('utf-8')]
            except:
                raise KeyError(
                    'Not a valid key (integer index starting with 1, or light name): ' + str(key))

    @property
    def lights(self):
        """ Access lights as a list """
        return self.get_light_objects()

    def get_api(self):
        """ Returns the full api dictionary """
        return self.request('GET', self.api + self.username)

    def get_light(self, light_id=None, parameter=None):
        """ Gets state by light_id and parameter"""

        if is_string(light_id):
            light_id = self.get_light_id_by_name(light_id)
        if light_id is None:
            return self.request('GET', self.api + self.username + '/lights/')
        state = self.request(
            'GET', self.api + self.username + '/lights/' + str(light_id))
        if parameter is None:
            return state
        if parameter in ['name', 'type', 'uniqueid', 'swversion']:
            return state[parameter]
        else:
            try:
                return state['state'][parameter]
            except KeyError as e:
                raise KeyError(
                    'Not a valid key, parameter %s is not associated with light %s)'
                    % (parameter, light_id))

    def set_light(self, light_id, parameter, value=None, transitiontime=None):
        """ Adjust properties of one or more lights.

        light_id can be a single lamp or an array of lamps
        parameters: 'on' : True|False , 'bri' : 0-254, 'sat' : 0-254, 'ct': 154-500

        transitiontime : in **deciseconds**, time for this transition to take place
                         Note that transitiontime only applies to *this* light
                         command, it is not saved as a setting for use in the future!
                         Use the Light class' transitiontime attribute if you want
                         persistent time settings.

        """
        if isinstance(parameter, dict):
            data = parameter
        else:
            data = {parameter: value}

        if transitiontime is not None:
            data['transitiontime'] = int(round(
                transitiontime))  # must be int for request format

        light_id_array = light_id
        if isinstance(light_id, int) or is_string(light_id):
            light_id_array = [light_id]
        result = []
        for light in light_id_array:
            logger.debug(str(data))
            if parameter == 'name':
                result.append(self.request('PUT', self.api + self.username + '/lights/' + str(
                    light_id), data))
            else:
                if is_string(light):
                    converted_light = self.get_light_id_by_name(light)
                else:
                    converted_light = light
                result.append(self.request('PUT', self.api + self.username + '/lights/' + str(
                    converted_light) + '/state', data))
            if 'error' in list(result[-1][0].keys()):
                logger.warn("ERROR: {0} for light {1}".format(
                    result[-1][0]['error']['description'], light))

        logger.debug(result)
        return result

    # Sensors #####

    @property
    def sensors(self):
        """ Access sensors as a list """
        return self.get_sensor_objects()

    def create_sensor(self, name, modelid, swversion, sensor_type, uniqueid, manufacturername, state={}, config={}, recycle=False):
        """ Create a new sensor in the bridge. Returns (ID,None) of the new sensor or (None,message) if creation failed. """
        data = {
            "name": name,
            "modelid": modelid,
            "swversion": swversion,
            "type": sensor_type,
            "uniqueid": uniqueid,
            "manufacturername": manufacturername,
            "recycle": recycle
        }
        if (isinstance(state, dict) and state != {}):
            data["state"] = state

        if (isinstance(config, dict) and config != {}):
            data["config"] = config

        result = self.request('POST', self.api + self.username + '/sensors/', data)

        if ("success" in result[0].keys()):
            new_id = result[0]["success"]["id"]
            logger.debug("Created sensor with ID " + new_id)
            new_sensor = Sensor(self, int(new_id))
            self.sensors_by_id[new_id] = new_sensor
            self.sensors_by_name[name] = new_sensor
            return new_id, None
        else:
            logger.debug("Failed to create sensor:" + repr(result[0]))
            return None, result[0]

    def get_sensor(self, sensor_id=None, parameter=None):
        """ Gets state by sensor_id and parameter"""

        if is_string(sensor_id):
            sensor_id = self.get_sensor_id_by_name(sensor_id)
        if sensor_id is None:
            return self.request('GET', self.api + self.username + '/sensors/')
        data = self.request(
            'GET', self.api + self.username + '/sensors/' + str(sensor_id))

        if isinstance(data, list):
            logger.debug("Unable to read sensor with ID {0}: {1}".format(sensor_id, repr(data)))
            return None

        if parameter is None:
            return data
        return data[parameter]

    def set_sensor(self, sensor_id, parameter, value=None):
        """ Adjust properties of a sensor

        sensor_id must be a single sensor.
        parameters: 'name' : string

        """
        if isinstance(parameter, dict):
            data = parameter
        else:
            data = {parameter: value}

        result = None
        logger.debug(str(data))
        result = self.request('PUT', self.api + self.username + '/sensors/' + str(
            sensor_id), data)
        if 'error' in list(result[0].keys()):
            logger.warn("ERROR: {0} for sensor {1}".format(
                result[0]['error']['description'], sensor_id))

        logger.debug(result)
        return result

    def set_sensor_state(self, sensor_id, parameter, value=None):
        """ Adjust the "state" object of a sensor

        sensor_id must be a single sensor.
        parameters: any parameter(s) present in the sensor's "state" dictionary.

        """
        self.set_sensor_content(sensor_id, parameter, value, "state")

    def set_sensor_config(self, sensor_id, parameter, value=None):
        """ Adjust the "config" object of a sensor

        sensor_id must be a single sensor.
        parameters: any parameter(s) present in the sensor's "config" dictionary.

        """
        self.set_sensor_content(sensor_id, parameter, value, "config")

    def set_sensor_content(self, sensor_id, parameter, value=None, structure="state"):
        """ Adjust the "state" or "config" structures of a sensor
        """
        if (structure != "state" and structure != "config"):
            logger.debug("set_sensor_current expects structure 'state' or 'config'.")
            return False

        if isinstance(parameter, dict):
            data = parameter.copy()
        else:
            data = {parameter: value}

        # Attempting to set this causes an error.
        if "lastupdated" in data:
            del data["lastupdated"]

        result = None
        logger.debug(str(data))
        result = self.request('PUT', self.api + self.username + '/sensors/' + str(
            sensor_id) + "/" + structure, data)
        if 'error' in list(result[0].keys()):
            logger.warn("ERROR: {0} for sensor {1}".format(
                result[0]['error']['description'], sensor_id))

        logger.debug(result)
        return result

    def delete_scene(self, scene_id):
        try:
            return self.request('DELETE', self.api + self.username + '/scenes/' + str(scene_id))
        except:
            logger.debug("Unable to delete scene with ID {0}".format(scene_id))

    def delete_sensor(self, sensor_id):
        try:
            name = self.sensors_by_id[sensor_id].name
            del self.sensors_by_name[name]
            del self.sensors_by_id[sensor_id]
            return self.request('DELETE', self.api + self.username + '/sensors/' + str(sensor_id))
        except:
            logger.debug("Unable to delete nonexistent sensor with ID {0}".format(sensor_id))

    # Groups of lights #####
    @property
    def groups(self):
        """ Access groups as a list """
        return [Group(self, int(groupid)) for groupid in self.get_group().keys()]

    def get_group_id_by_name(self, name):
        """ Lookup a group id based on string name. Case-sensitive. """
        groups = self.get_group()
        for group_id in groups:
            if PY3K:
                if name == groups[group_id]['name']:
                    return group_id
            else:
                if name.decode('utf-8') == groups[group_id]['name']:
                    return group_id
        return False

    def get_group(self, group_id=None, parameter=None):
        if is_string(group_id):
            group_id = self.get_group_id_by_name(group_id)
        if group_id is False:
            logger.error('Group name does not exit')
            return
        if group_id is None:
            return self.request('GET', self.api + self.username + '/groups/')
        if parameter is None:
            return self.request('GET', self.api + self.username + '/groups/' + str(group_id))
        elif parameter == 'name' or parameter == 'lights':
            return self.request('GET', self.api + self.username + '/groups/' + str(group_id))[parameter]
        else:
            return self.request('GET', self.api + self.username + '/groups/' + str(group_id))['action'][parameter]

    def set_group(self, group_id, parameter, value=None, transitiontime=None):
        """ Change light settings for a group

        group_id : int, id number for group
        parameter : 'name' or 'lights'
        value: string, or list of light IDs if you're setting the lights

        """

        if isinstance(parameter, dict):
            data = parameter
        elif parameter == 'lights' and (isinstance(value, list) or isinstance(value, int)):
            if isinstance(value, int):
                value = [value]
            data = {parameter: [str(x) for x in value]}
        else:
            data = {parameter: value}

        if transitiontime is not None:
            data['transitiontime'] = int(round(
                transitiontime))  # must be int for request format

        group_id_array = group_id
        if isinstance(group_id, int) or is_string(group_id):
            group_id_array = [group_id]
        result = []
        for group in group_id_array:
            logger.debug(str(data))
            if is_string(group):
                converted_group = self.get_group_id_by_name(group)
            else:
                converted_group = group
            if converted_group is False:
                logger.error('Group name does not exit')
                return
            if parameter == 'name' or parameter == 'lights':
                result.append(self.request('PUT', self.api + self.username + '/groups/' + str(converted_group), data))
            else:
                result.append(self.request('PUT', self.api + self.username + '/groups/' + str(converted_group) + '/action', data))

        if 'error' in list(result[-1][0].keys()):
            logger.warn("ERROR: {0} for group {1}".format(
                result[-1][0]['error']['description'], group))

        logger.debug(result)
        return result

    def create_group(self, name, lights=None):
        """ Create a group of lights

        Parameters
        ------------
        name : string
            Name for this group of lights
        lights : list
            List of lights to be in the group.

        """
        data = {'lights': [str(x) for x in lights], 'name': name}
        return self.request('POST', self.api + self.username + '/groups/', data)

    def delete_group(self, group_id):
        return self.request('DELETE', self.api + self.username + '/groups/' + str(group_id))

    # Scenes #####
    @property
    def scenes(self):
        return [Scene(k, **v) for k, v in self.get_scene().items()]

    def get_scene(self):
        return self.request('GET', self.api + self.username + '/scenes')

    def activate_scene(self, group_id, scene_id):
        return self.request('PUT', self.api + self.username + '/groups/' +
                            str(group_id) + '/action',
                            {"scene": scene_id})

    def run_scene(self, group_name, scene_name):
        """Run a scene by group and scene name.

        As of 1.11 of the Hue API the scenes are accessable in the
        API. With the gen 2 of the official HUE app everything is
        organized by room groups.

        This provides a convenience way of activating scenes by group
        name and scene name. If we find exactly 1 group and 1 scene
        with the matching names, we run them.

        If we find more than one we run the first scene who has
        exactly the same lights defined as the group. This is far from
        perfect, but is convenient for setting lights symbolically (and
        can be improved later).

        """
        groups = [x for x in self.groups if x.name == group_name]
        scenes = [x for x in self.scenes if x.name == scene_name]
        if len(groups) != 1:
            logger.warn("run_scene: More than 1 group found by name %s",
                        group_name)
            return
        group = groups[0]
        if len(scenes) == 0:
            logger.warn("run_scene: No scene found %s", scene_name)
            return
        if len(scenes) == 1:
            self.activate_scene(group.group_id, scenes[0].scene_id)
            return
        # otherwise, lets figure out if one of the named scenes uses
        # all the lights of the group
        group_lights = sorted([x.light_id for x in group.lights])
        for scene in scenes:
            if group_lights == scene.lights:
                self.activate_scene(group.group_id, scene.scene_id)
                return
        logger.warn("run_scene: did not find a scene: %s "
                    "that shared lights with group %s",
                    (scene_name, group))

    # Schedules #####
    def get_schedule(self, schedule_id=None, parameter=None):
        if schedule_id is None:
            return self.request('GET', self.api + self.username + '/schedules')
        if parameter is None:
            return self.request('GET', self.api + self.username + '/schedules/' + str(schedule_id))

    def create_schedule(self, name, time, light_id, data, description=' '):
        schedule = {
            'name': name,
            'localtime': time,
            'description': description,
            'command':
            {
                'method': 'PUT',
                'address': (self.api + self.username +
                            '/lights/' + str(light_id) + '/state'),
                'body': data
            }
        }
        return self.request('POST', self.api + self.username + '/schedules', schedule)

    def set_schedule_attributes(self, schedule_id, attributes):
        """
        :param schedule_id: The ID of the schedule
        :param attributes: Dictionary with attributes and their new values
        """
        return self.request('PUT', self.api + self.username + '/schedules/' + str(schedule_id), data=attributes)

    def create_group_schedule(self, name, time, group_id, data, description=' '):
        schedule = {
            'name': name,
            'localtime': time,
            'description': description,
            'command':
            {
                'method': 'PUT',
                'address': (self.api + self.username +
                            '/groups/' + str(group_id) + '/action'),
                'body': data
            }
        }
        return self.request('POST', self.api + self.username + '/schedules', schedule)

    def delete_schedule(self, schedule_id):
        return self.request('DELETE', self.api + self.username + '/schedules/' + str(schedule_id))


class PhueAuthorisationError(PhueException):
    pass


class PhueTokenExpired(PhueException):
    pass


class PhueInvalidToken(PhueException):
    pass


class RemoteBridge(Bridge):

    def __init__(self, username=None, config_file_path=None, token_path=None):
        if config_file_path is None:
            if os.getenv(USER_HOME) is not None and os.access(os.getenv(USER_HOME), os.W_OK):
                config_file_path = os.path.join(os.getenv(USER_HOME), '.python_hue_remote')
            elif 'iPad' in platform.machine() or 'iPhone' in platform.machine() or 'iPad' in platform.machine():
                config_file_path = os.path.join(os.getenv(USER_HOME), 'Documents', '.python_hue_remote')
            else:
                config_file_path = os.path.join(os.getcwd(), '.python_hue_remote')
        self.token = self.get_token(token_path)
        super(RemoteBridge, self).__init__(
            ip='api.meethue.com', username=username,
            config_file_path=config_file_path, api='/bridge/')

    def get_token(self, token_path=None):
        if token_path is None:
            if os.getenv(USER_HOME) is not None and os.access(os.getenv(USER_HOME), os.W_OK):
                token_path = os.path.join(os.getenv(USER_HOME), '.python_hue_token')
            elif 'iPad' in platform.machine() or 'iPhone' in platform.machine() or 'iPad' in platform.machine():
                token_path = os.path.join(os.getenv(USER_HOME), 'Documents', '.python_hue_token')
            else:
                token_path = os.path.join(os.getcwd(), '.python_hue_token')
        return RemoteToken(load=token_path)

    def press_link_button(self):
        logger.info('Pressing remote virtual link button..')
        data = {'linkbutton': True}
        connection = httplib.HTTPSConnection(self.ip, timeout=10)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': self.token.bearer()
        }
        connection.request('PUT', '{}{}'.format(self.api, '0/config'),
                           json.dumps(data), headers)
        result = connection.getresponse()
        logger.debug('Response from API: {} {}'.format(
            result.status, result.reason))
        if result.status != 200:
            raise PhueRegistrationException(result.status, result.read())

    def get_ip_address(self, *args, **kwargs):
        raise NotImplementedError

    def register_app(self, *args, **kwargs):
        self.press_link_button()
        super(RemoteBridge, self).register_app(*args, **kwargs)


class RemoteToken(object):
    """ A Python Class to interact with the Philips Hue remote access API to
    manage the associated OAuth2 tokens.

    You will need to provide your own account credentials from
    https://developers.meethue.com/user/me/apps
    """

    API =               'api.meethue.com'
    ENDPOINT_AUTH =     '/oauth2/auth'
    ENDPOINT_TOKEN =    '/oauth2/token'
    ENDPOINT_REFRESH =  '/oauth2/refresh'

    def __init__(self, clientid=None, clientsecret=None, appid=None,
                 saveto=None, load=None):
        """ A new token object requires your own credentials from
        https://developers.meethue.com/user/me/apps
        You will be required to visit a URL (generated by this object) and
        paste in the callback URL that is created after authorisation through
        the web browser is complete. The required information from that URL
        will be parsed in the `new()` method.

        When registering, you can use what ever you want for the callback URL
        (it doesn't even need to be a valid URL).

        Args:
            clientid (str): The clientid you obtain from Hue when registering
                for the Hue Remote API.
            clientsecret (str): The clientsecret you have received from Hue
                when registering for the Hue Remote API.
            appid (str): The App name you specified when registering for the Hue
                Remote API.
            saveto (str optional): The file to save details to so they can be
                reloaded at a later time.
            load (str optional): If specified, load token data from the path
                instead of attempting to autorise a new one. This will override
                the remaining attributes, as they are filled from the file
                contents instead.
        """

        if load:
            self.load(load)
        elif (clientid and clientsecret and appid):
            self.clientid = clientid
            self.clientsecret = clientsecret
            self.appid = appid
            self.saveto = saveto
            self.__authorize__()
        else:
            raise ValueError('Missing required argumets clientid, clientsecret and appid')

    def __authorize__(self):
        """ Obtains new access and refresh tokens from the Philips Hue API

        This method is intended to be called from the `__init__` method.

        Returns:
            None
        """

        state = binascii.b2a_hex(os.urandom(16))
        if PY3K:
            state = state.decode()
        URL = 'https://{}{}?clientid={}&appid={}&deviceid=phuepy&devicename=phuepy&state={}&response_type=code'.format(
            self.API, self.ENDPOINT_AUTH, self.clientid, self.appid, state)
        try:
            webbrowser.open(URL)
        except:
            logger.info('The was an error opening the web browser')
            pass
        print('Your web browser should open a Philips Hue page asking you to provide authorisation to access your Philips Hue system.\nNote that you need to sign in with your Philips Hue account, not your developer account.\nIf your browser doesn\'t open, you can manually visit the following address:\n' + URL + '\nOnce you have provided authorisation, you will be redirected to the callback URL that you specified when setting up your developer credentials.\nPlease enter the entire address of the page you are sent to after completing authorisation:')
        resp = input('Address: ')
        parsed = urlparse(resp)
        if parse_qs(parsed.query)['state'][0] != state:
            # Confirm that the code in the callback URL matches what we
            # generated in the `state` variable.
            logger.info('URL was not validated. State code {} is not equal to {}',
                        parse_qs(parsed.query)['state'][0], state)
            raise ValueError('The URL is not valid.')
        code = parse_qs(parsed.query)['code'][0]
        # Use the `code` from the callback URL to obtain an nonce from the API
        params = urlencode({'code': code, 'grant_type': 'authorization_code'})
        www_authenticate = self.__get_nonce__(self.ENDPOINT_TOKEN, params)
        # Now exchange the `nonce` and `code` for our tokens.
        headers = {'Authorization': self.__digest__(
            self.ENDPOINT_TOKEN, www_authenticate)}
        connection = httplib.HTTPSConnection(self.API, timeout=20)
        connection.request('POST',
                           self.ENDPOINT_TOKEN + '?' + params,
                           None,
                           headers)
        self.__parse_token_json__(connection.getresponse())
        connection.close()

    def __get_nonce__(self, url, params):
        """ Obtains an nonce from the Philips Hue API to be used in the
        digest calculations.
        Returns a dict containing the `realm` and `nonce` from the
        `WWW-Authenticate` header.
        """

        connection = httplib.HTTPSConnection(self.API, timeout=20)
        connection.request('POST', url + '?' + params)
        response = connection.getresponse()
        www_authenticate = response.getheader('WWW-Authenticate')
        # Use a regex to parse the string contained in the `WWW-Authenticate`
        # header and obtain the `realm` and `nonce` values.
        # Example header: WWW-Authenticate: Digest realm="oauth2_client@api.meethue.com", nonce="7b6e45de18ac4ee452ee0a0de91dbb10"
        reg = re.compile(r'(\w+)[:=][\s"]?([^",]+)"?')
        www_authenticate = dict(reg.findall(www_authenticate))
        logger.debug('Obtained nonce: {}, realm: {}'
                     .format(www_authenticate['nonce'],
                             www_authenticate['realm']))
        connection.close()
        return www_authenticate

    def __parse_token_json__(self, resp):
        """ Parses the JSON string from the Philips Hue API that is received
        when obtaining a new token or refreshing the tokens.

        The expiry time is caluclated and recorded in UTC in the
        `access_token_exp` and `refresh_token_exp` attributes.
        """

        logger.debug('Response from API: {} {}'.format(resp.status, resp.reason))
        token = json.loads(resp.read())
        logger.debug('Text from API: {}'.format(token))
        if resp.status == 200:
            if token['access_token']:  # All values will be blank if failed due to query error.
                self.access_token = token['access_token']
                self.refresh_token = token['refresh_token']
                self.access_token_exp = datetime.utcnow() + timedelta(
                    seconds=(int(token['access_token_expires_in'])))
                self.refresh_token_exp = datetime.utcnow() + timedelta(
                    seconds=(int(token['refresh_token_expires_in'])))
                self.access_token_exp = self.access_token_exp.replace(
                    tzinfo=UTC)
                self.refresh_token_exp = self.refresh_token_exp.replace(
                    tzinfo=UTC)
                if self.saveto:
                    self.save()
            else:
                raise PhueAuthorisationError(None,
                                             'Unable to obtain tokens from API')
        else:
            raise PhueAuthorisationError(token['ErrorCode'], token['Error'])

    def __utc_to_local__(self, utc_dt):
        """ Converts a UTC datetime object to an unaware datetime object in
        local time
        """

        timestamp = calendar.timegm(utc_dt.timetuple())
        local_dt = datetime.fromtimestamp(timestamp)
        return local_dt.replace(microsecond=utc_dt.microsecond)

    def __digest__(self, url, www_authenticate, verb='POST'):
        """ Returns an Authorization header that includes the digest hash

        Args:
            url (str): The API endpoint the request will be sent to
            www_authenticate (dict): The nonce and realm from the initial
                challange
            verb (str optional): The HTTP request type (default POST)

        Returns:
            header: The Authorization header
        """

        part1 = ':'.join([
            self.clientid,
            www_authenticate['realm'],
            self.clientsecret,
        ])
        part3 = ':'.join([verb, url])
        if PY3K:
            part1 = part1.encode()
            part3 = part3.encode()
        digest_plain = ':'.join([
            hashlib.md5(part1).hexdigest(),
            www_authenticate['nonce'],
            hashlib.md5(part3).hexdigest(),
        ])
        if PY3K:
            digest_plain = digest_plain.encode()
        return ('Digest username="{}", realm="{}", nonce="{}", uri="{}", response="{}"'
                .format(
                    self.clientid,
                    www_authenticate['realm'],
                    www_authenticate['nonce'],
                    url,
                    hashlib.md5(digest_plain).hexdigest()
                    )
                )

    @property
    def access_expires(self):
        """ Returns a human friendly expiry time in local time.
        """

        return self.__utc_to_local__(self.access_token_exp).strftime('%c')

    @property
    def refresh_expires(self):
        """ Returns a human friendly expiry time in local time.
        """

        return self.__utc_to_local__(self.refresh_token_exp).strftime('%c')

    @property
    def refresh_required(self):
        """ Returns a boolean, `True` if the access token has expired (or will
        expire in the next 30 minutes) and can be refreshed,
        `False` if the access token is still valid.
        """

        if (self.access_token_exp - timedelta(minutes=30)) > datetime.now(UTC):
            return False
        else:
            return True
        pass

    @property
    def valid(self):
        """ Returns a boolean, `True` if the access or refresh tokens
        are still valid, `False` if they are both expired. If `False`, then a
        new `Token` object will need to be created.
        """

        if (self.refresh_token_exp) > datetime.now(UTC):
            return True
        else:
            return False
        pass

    def save(self, saveto=None):
        """ Save the token data so it can be loaded later.

        This is acheived by serialising `__dict__` into JSON, removing
        `self.saveto` from the JSON string and writing it to the location
        specified in in the `saveto` parameter (if specified), or the location
        in `self.saveto`. If both `saveto` and `self.saveto` are specified, the
        method parameter will take precendece, and will update `self.saveto`
        to match the new location. If none are specified, an `AttributeError`
        is raised.
        `saveto` is string representing a file path.

        Args:
            saveto (str, optional): The file to save details to,
                overriding the existing save location (if it is set)

        Returns:
            None
        """

        if saveto:
            self.saveto = saveto
        if self.saveto:
            current_state = deepcopy(self.__dict__)
            current_state.pop('saveto')
            current_state['access_token_exp'] = (current_state['access_token_exp']
                                                 .replace(tzinfo=None).isoformat())
            current_state['refresh_token_exp'] = (current_state['refresh_token_exp']
                                                  .replace(tzinfo=None).isoformat())
            with open(self.saveto, 'w') as f:
                text = json.dumps(current_state)
                logger.debug('Saving text to token file: {}'.format(text))
                f.write(text)
        else:
            raise AttributeError('No save location is defined.')

    def load(self, loadfrom):
        """ Loads attributes from a JSON string stored in a file written by the
        save method.

        Args:
            loadfrom (str): A path to the file to load details from
        """

        try:
            with open(loadfrom, 'r') as f:
                text = f.read()
                current_state = json.loads(text)
                logger.debug('Loading token from file: {}'.format(text))
        except FileNotFoundError:
            raise PhueInvalidToken(None, 'No token exists yet. Generate one first')
        try:
            self.saveto = loadfrom
            self.clientid = current_state['clientid']
            self.clientsecret = current_state['clientsecret']
            self.appid = current_state['appid']
            self.access_token = current_state['access_token']
            self.refresh_token = current_state['refresh_token']
            self.access_token_exp = datetime.strptime(
                current_state['access_token_exp'],
                '%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=UTC)
            self.refresh_token_exp = datetime.strptime(
                current_state['refresh_token_exp'],
                '%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=UTC)
        except KeyError:
            raise PhueInvalidToken(None, 'This token file is corrupt or invalid')
        self.refresh()

    def refresh(self, force=False):
        """ Refreshes the current tokens.

        If the access token is still valid (i.e. doesn't expire in the next 30
        minutes), then the tokens won't be refreshed unless the `force`
        parameter is `True`.

        If the saveto attribute has a value, then the new token details
        are also saved to the file.

        Args:
            force (bool optional): Refresh the token, even if it hasn't expired

        Returns:
            True if refreshed, False if not refreshed.
        """

        if self.valid:
            if force or self.refresh_required:
                params = urlencode({'grant_type': 'refresh_token'})
                www_authenticate = self.__get_nonce__(
                    self.ENDPOINT_REFRESH, params)
                data = urlencode({'refresh_token': self.refresh_token})
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Authorization': self.__digest__(self.ENDPOINT_REFRESH,
                                                     www_authenticate)
                }
                connection = httplib.HTTPSConnection(self.API, timeout=20)
                connection.request('POST',
                                   self.ENDPOINT_REFRESH + '?' + params,
                                   data,
                                   headers)
                self.__parse_token_json__(connection.getresponse())
                logger.info('Token refreshed. Access expires: {}, Refresh Expires: {}'
                            .format(self.access_token_exp.isoformat(),
                                    self.refresh_token_exp.isoformat()))
                connection.close()
                return True
            else:
                logger.info('Refresh not required.')
                return False
        else:
            msg = 'This token has expired. Please generate a new token.'
            logger.exception(msg)
            raise PhueTokenExpired(None, msg)

    def bearer(self):
        """ A convinence method to get the current access token in a format to
        use i nan Authorization header

        If the access token needs refreshing, this method will refresh it first,
        then return the updated access token.

        Args:
            None

        Returns:
            token (str): A valid Bearer token to use in the Authorization header
                when accessing the Philips Hue API
        """

        if self.valid:
            self.refresh(force=False)
            return 'Bearer {}'.format(self.access_token)
        else:
            msg = 'This token has expired. Please generate a new token.'
            logger.exception(msg)
            raise PhueTokenExpired(None, msg)


if __name__ == '__main__':
    import argparse

    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument('--config-file-path', required=False)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--token', action='store_true')
    group.add_argument('--host')
    args = parser.parse_args()

    if args.token:
        if os.getenv(USER_HOME) is not None and os.access(os.getenv(USER_HOME), os.W_OK):
            token_path = os.path.join(os.getenv(USER_HOME), '.python_hue_token')
        elif 'iPad' in platform.machine() or 'iPhone' in platform.machine() or 'iPad' in platform.machine():
            token_path = os.path.join(os.getenv(USER_HOME), 'Documents', '.python_hue_token')
        else:
            token_path = os.path.join(os.getcwd(), '.python_hue_token')
        clientid = input('Client ID: ')
        clientsecret = input('Client Secret: ')
        appid = input('App ID: ')
        saveto = input('Save token to (default: {}): '.format(token_path))
        if not saveto:
            saveto = token_path
        RemoteToken(clientid, clientsecret, appid, saveto=saveto)
        print('Saved token to {}'.format(saveto))
    else:
        while True:
            try:
                b = Bridge(args.host, config_file_path=args.config_file_path)
                break
            except PhueRegistrationException as e:
                input('Press button on Bridge then hit Enter to try again')
