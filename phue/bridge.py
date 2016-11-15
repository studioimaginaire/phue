# -*- coding: utf-8 -*-

import os
import json
import socket

from .utils import USER_HOME, MOBILE, PY3K, logger, is_string
from .exception import PhueException, PhueRegistrationException, PhueRequestTimeout
from .light import Light

if PY3K:
    import http.client as httplib
else:
    import httplib


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
    def __init__(self, ip=None, username=None, config_file_path=None):
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
        elif MOBILE:
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

        # self.minutes = 600 # these do not seem to be used anywhere?
        # self.seconds = 10

        self.connect()

    @property
    def name(self):
        '''Get or set the name of the bridge [string]'''
        self._name = self.request(
            'GET', '/api/' + self.username + '/config')['name']
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
        data = {'name': self._name}
        self.request(
            'PUT', '/api/' + self.username + '/config', json.dumps(data))

    def request(self, mode='GET', address=None, data=None):
        """ Utility function for HTTP GET/PUT requests for the API"""
        connection = httplib.HTTPConnection(self.ip, timeout=10)

        try:
            if mode == 'GET' or mode == 'DELETE':
                connection.request(mode, address)
            if mode == 'PUT' or mode == 'POST':
                connection.request(mode, address, data)

            logger.debug("{0} {1} {2}".format(mode, address, str(data)))

        except socket.timeout:
            error = "{} Request to {}{} timed out.".format(mode, self.ip, address)

            logger.exception(error)
            raise PhueRequestTimeout(None, error)

        result = connection.getresponse()
        connection.close()
        if PY3K:
            return json.loads(str(result.read(), encoding='utf-8'))
        else:
            result_str = result.read()
            logger.debug(result_str)
            return json.loads(result_str)

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
        data = json.dumps(registration_request)
        response = self.request('POST', '/api', data)
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
            lights = self.request('GET', '/api/' + self.username + '/lights/')
            for light in lights:
                self.lights_by_id[int(light)] = Light(self, int(light))
                self.lights_by_name[lights[light][
                    'name']] = self.lights_by_id[int(light)]
        if mode == 'id':
            return self.lights_by_id
        if mode == 'name':
            return self.lights_by_name
        if mode == 'list':
            return self.lights_by_id.values()

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
            sensors = self.request('GET', '/api/' + self.username + '/sensors/')
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
        return self.request('GET', '/api/' + self.username)

    def get_light(self, light_id=None, parameter=None):
        """ Gets state by light_id and parameter"""

        if is_string(light_id):
            light_id = self.get_light_id_by_name(light_id)
        if light_id is None:
            return self.request('GET', '/api/' + self.username + '/lights/')
        state = self.request(
            'GET', '/api/' + self.username + '/lights/' + str(light_id))
        if parameter is None:
            return state
        if parameter == 'name':
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
                result.append(self.request('PUT', '/api/' + self.username + '/lights/' + str(
                    light_id), json.dumps(data)))
            else:
                if is_string(light):
                    converted_light = self.get_light_id_by_name(light)
                else:
                    converted_light = light
                result.append(self.request('PUT', '/api/' + self.username + '/lights/' + str(
                    converted_light) + '/state', json.dumps(data)))
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

        result = self.request('POST', '/api/' + self.username + '/sensors/', json.dumps(data))

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
            return self.request('GET', '/api/' + self.username + '/sensors/')
        data = self.request(
            'GET', '/api/' + self.username + '/sensors/' + str(sensor_id))

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
        result = self.request('PUT', '/api/' + self.username + '/sensors/' + str(
            sensor_id), json.dumps(data))
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
        del data["lastupdated"]

        result = None
        logger.debug(str(data))
        result = self.request('PUT', '/api/' + self.username + '/sensors/' + str(
            sensor_id) + "/" + structure, json.dumps(data))
        if 'error' in list(result[0].keys()):
            logger.warn("ERROR: {0} for sensor {1}".format(
                result[0]['error']['description'], sensor_id))

        logger.debug(result)
        return result

    def delete_sensor(self, sensor_id):
        try:
            name = self.sensors_by_id[sensor_id].name
            del self.sensors_by_name[name]
            del self.sensors_by_id[sensor_id]
            return self.request('DELETE', '/api/' + self.username + '/sensors/' + str(sensor_id))
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
            return self.request('GET', '/api/' + self.username + '/groups/')
        if parameter is None:
            return self.request('GET', '/api/' + self.username + '/groups/' + str(group_id))
        elif parameter == 'name' or parameter == 'lights':
            return self.request('GET', '/api/' + self.username + '/groups/' + str(group_id))[parameter]
        else:
            return self.request('GET', '/api/' + self.username + '/groups/' + str(group_id))['action'][parameter]

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
                result.append(self.request('PUT', '/api/' + self.username + '/groups/' + str(converted_group), json.dumps(data)))
            else:
                result.append(self.request('PUT', '/api/' + self.username + '/groups/' + str(converted_group) + '/action', json.dumps(data)))

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
        return self.request('POST', '/api/' + self.username + '/groups/', json.dumps(data))

    def delete_group(self, group_id):
        return self.request('DELETE', '/api/' + self.username + '/groups/' + str(group_id))

    # Scenes #####
    @property
    def scenes(self):
        return [Scene(k, **v) for k, v in self.get_scene().items()]

    def get_scene(self):
        return self.request('GET', '/api/' + self.username + '/scenes')

    def activate_scene(self, group_id, scene_id):
        return self.request('PUT', '/api/' + self.username + '/groups/' +
                            str(group_id) + '/action',
                            json.dumps({"scene": scene_id}))

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
            return self.request('GET', '/api/' + self.username + '/schedules')
        if parameter is None:
            return self.request('GET', '/api/' + self.username + '/schedules/' + str(schedule_id))

    def create_schedule(self, name, time, light_id, data, description=' '):
        schedule = {
            'name': name,
            'time': time,
            'description': description,
            'command':
            {
                'method': 'PUT',
                'address': ('/api/' + self.username +
                            '/lights/' + str(light_id) + '/state'),
                'body': data
            }
        }
        return self.request('POST', '/api/' + self.username + '/schedules', json.dumps(schedule))

    def create_group_schedule(self, name, time, group_id, data, description=' '):
        schedule = {
            'name': name,
            'time': time,
            'description': description,
            'command':
            {
                'method': 'PUT',
                'address': ('/api/' + self.username +
                            '/groups/' + str(group_id) + '/action'),
                'body': data
            }
        }
        return self.request('POST', '/api/' + self.username + '/schedules', json.dumps(schedule))

    def delete_schedule(self, schedule_id):
        return self.request('DELETE', '/api/' + self.username + '/schedules/' + str(schedule_id))
