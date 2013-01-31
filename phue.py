#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os
import argparse
import platform
import sys
if sys.version_info.major > 2:
    import http.client as httplib
else:
    import httplib


# phue by Nathanaël Lécaudé - A Philips Hue Python library
# https://github.com/studioimaginaire/phue
# Original protocol hacking by rsmck : http://rsmck.co.uk/hue

if platform.system() == 'Windows':
    USER_HOME = 'USERPROFILE'
else:
    USER_HOME = 'HOME'

class Light(object):
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
        self._alert = None
       
    @property
    def name(self):
        '''Get or set the name of the light [string]'''
        self._name = self.bridge.get_light(self.light_id, 'name')
        return self._name

    @name.setter
    def name(self, value):
        old_name = self.name
        self._name = value
        self.bridge.set_light(self.light_id, 'name', self._name)
        
        self.bridge.lights_by_name[self.name] = self 
        del self.bridge.lights_by_name[old_name]

    @property
    def on(self):
        '''Get or set the state of the light [True|False]'''
        self._on = self.bridge.get_light(self.light_id, 'on')
        return self._on

    @on.setter
    def on(self, value):
        self._on = value
        self.bridge.set_light(self.light_id, 'on', self._on)

    @property
    def colormode(self):
        '''Get the color mode of the light [hue|xy|ct]'''
        self._colormode = self.bridge.get_light(self.light_id, 'colormode')
        return self._colormode
    
    @property
    def brightness(self):
        '''Get or set the brightness of the light [0-254]'''
        self._brightness = self.bridge.get_light(self.light_id, 'bri')
        return self._brightness

    @brightness.setter
    def brightness(self, value):
        self._brightness = value
        self.bridge.set_light(self.light_id, 'bri', self._brightness)
    
    @property
    def hue(self):
        '''Get or set the hue of the light [0-65535]'''
        self._hue = self.bridge.get_light(self.light_id, 'hue')
        return self._hue

    @hue.setter
    def hue(self, value):
        self._hue = value
        self.bridge.set_light(self.light_id, 'hue', self._hue)

    @property
    def saturation(self):
        '''Get or set the saturation of the light [0-254]'''
        self._saturation = self.bridge.get_light(self.light_id, 'sat')
        return self._saturation

    @saturation.setter
    def saturation(self, value):
        self._saturation = value
        self.bridge.set_light(self.light_id, 'sat', self._saturation)

    @property
    def xy(self):
        '''Get or set the color coordinates of the light [ [0.0-1.0, 0.0-1.0] ]'''
        self._xy = self.bridge.get_light(self.light_id, 'xy')
        return self._xy

    @xy.setter
    def xy(self, value):
        self._xy = value
        self.bridge.set_light(self.light_id, 'xy', self._xy)

    @property
    def colortemp(self):
        '''Get or set the color temperature of the light [154-500]'''
        self._colortemp = self.bridge.get_light(self.light_id, 'ct')
        return self._colortemp

    @colortemp.setter
    def colortemp(self, value):
        self._colortemp = value
        self.bridge.set_light(self.light_id, 'ct', self._colortemp)

    @property
    def alert(self):
        '''Get or set the alert state of the light [select|lselect|none]'''
        self._alert = self.bridge.get_light(self.light_id, 'alert')
        return self._alert

    @alert.setter
    def alert(self, value):
        self._alert = value
        self.bridge.set_light(self.light_id, 'alert', self._alert)

class Bridge(object):
    def __init__(self, ip = None, username = None):
        if os.access(os.getenv(USER_HOME),os.W_OK):
            self.config_file_path = os.path.join(os.getenv(USER_HOME),'.python_hue')
        else:
            self.config_file_path = os.path.join(os.getcwd(),'.python_hue')
        self.ip = ip
        self.username = username
        self.lights_by_id = {}
        self.lights_by_name = {}
        self._name = None

        self.minutes = 600
        self.seconds = 10
        
        self.connect()
    
    @property
    def name(self):
        '''Get or set the name of the bridge [string]'''
        self._name = self.request('GET', '/api/' + self.username + '/config')['name']
        return self._name
    
    @name.setter
    def name(self, value):
        self._name = value
        data = {'name' : self._name}
        self.request('PUT', '/api/' + self.username + '/config', json.dumps(data))

    def request(self,  mode = 'GET', address = None, data = None):
        connection = httplib.HTTPConnection(self.ip)
        if mode == 'GET' or mode == 'DELETE':
            connection.request(mode, address)
        if mode == 'PUT' or mode == 'POST':
            connection.request(mode, address, data)

        result = connection.getresponse()
        connection.close()
        return json.loads(result.read())
    
    def register_app(self):
        registration_request = {"username": "python_hue", "devicetype": "python_hue"}
        data = json.dumps(registration_request)
        response = self.request('POST', '/api', data)
        for line in response:
            for key in line:
                if 'success' in key:
                    with open(self.config_file_path, 'w') as f:
                        print('Writing configuration file to ' + self.config_file_path)
                        f.write(json.dumps({self.ip : line['success']}))
                        print('Reconnecting to the bridge')
                    self.connect()
                if 'error' in key:
                    if line['error']['type'] == 101:
                        print('Please press button on bridge to register application and call connect() method')
                    if line['error']['type'] == 7:
                        print('Unknown username')
    
    def connect(self):
        print('Attempting to connect to the bridge...')
        # If the ip and username were provided at class init
        if self.ip is not None and self.username is not None:
            print('Uding ip: ' + self.ip)
            print('Using username: ' + self.username)
            return
        
        if self.ip == None or self.username == None:
            try:
                with open(self.config_file_path) as f:
                    config = json.loads(f.read())
                    if self.ip is None:
                        self.ip = config.keys()[0]
                        print('Using ip from config: ' + self.ip)
                    else:
                        print('Using ip: ' + self.ip)
                    if self.username is None:
                        self.username =  config[self.ip]['username']
                        print('Using username from config: ' + self.username)
                    else:
                        print('Using username: ' + self.username)
            except Exception as e:
                print('Error opening config file, will attempt bridge registration')
                self.register_app()

    def get_light_id_by_name(self,name):
        lights = self.get_light()
        for light_id in lights:
            if name == lights[light_id]['name']:
                return light_id
        return False

    #Returns a dictionary containing the lights, either by name or id (use 'id' or 'name' as the mode)
    def get_light_objects(self, mode = 'list'):
        if self.lights_by_id == {}:
            lights = self.request('GET', '/api/' + self.username + '/lights/')
            for light in lights:
                self.lights_by_id[int(light)] = Light(self, int(light))
                self.lights_by_name[lights[light]['name']] = self.lights_by_id[int(light)]
        if mode == 'id':
            return self.lights_by_id
        if mode == 'name':
            return self.lights_by_name
        if mode == 'list':
            return [ self.lights_by_id[x] for x in range(1, len(self.lights_by_id) + 1) ]
  

    # Returns the full api dictionary
    def get_api(self):
        return self.request('GET', '/api/' + self.username)

    # Gets state by light_id and parameter
    def get_light(self, light_id = None, parameter = None):
        if type(light_id) == str or type(light_id) == unicode:
            light_id = self.get_light_id_by_name(light_id)
        if light_id == None:
            return self.request('GET', '/api/' + self.username + '/lights/' )
        state = self.request('GET', '/api/' + self.username + '/lights/' + str(light_id))
        if parameter == None:
            return state
        if parameter == 'name':
            return state[parameter]
        else:
            return state['state'][parameter]


    # light_id can be a single lamp or an array of lamps
    # parameters: 'on' : True|False , 'bri' : 0-254, 'sat' : 0-254, 'ct': 154-500
    def set_light(self, light_id, parameter, value = None):
        if type(parameter) == dict:
            data = parameter
        else:
            data = {parameter : value}
        light_id_array = light_id
        if type(light_id) == int or type(light_id) == str or type(light_id) == unicode:
            light_id_array = [light_id]
        result = []
        for light in light_id_array:
            if parameter  == 'name':
                result.append(self.request('PUT', '/api/' + self.username + '/lights/'+ str(light_id), json.dumps(data)))
            else:
                if type(light) == str or type(light) == unicode:
                    converted_light = self.get_light_id_by_name(light)
                else:
                    converted_light = light
                result.append(self.request('PUT', '/api/' + self.username + '/lights/'+ str(converted_light) + '/state', json.dumps(data)))
        return result
    
    def get_group(self, group_id = None, parameter = None):
        if group_id == None:
            return self.request('GET', '/api/' + self.username + '/groups/')
        if parameter == None:
            return self.request('GET', '/api/' + self.username + '/groups/'+ str(group_id))
        elif parameter == 'name' or parameter == 'lights':
            return self.request('GET', '/api/' + self.username + '/groups/'+ str(group_id))[parameter]
        else:
            return self.request('GET', '/api/' + self.username + '/groups/'+  str(group_id))['action'][parameter]

    def set_group(self, group_id, parameter, value = None):
        if type(parameter) == dict:
            data = parameter
        if parameter == 'lights' and type(value) == list:
            data = {parameter : [str(x) for x in value] }
        else:
            data = {parameter : value}

        if parameter == 'name' or parameter == 'lights':
            return self.request('PUT', '/api/' + self.username + '/groups/'+ str(group_id), json.dumps(data))
        else:
            return self.request('PUT', '/api/' + self.username + '/groups/'+ str(group_id) + '/action', json.dumps(data))

    def create_group(self, name, lights = None):
        data = {'lights' : [str(x) for x in lights], 'name': name}
        return self.request('POST', '/api/' + self.username + '/groups/', json.dumps(data))

    def delete_group(self, group_id):
        return self.request('DELETE', '/api/' + self.username + '/groups/' + str(group_id))

    def get_schedule(self, schedule_id = None, parameter = None):
        if schedule_id == None:
            return self.request('GET', '/api/' + self.username + '/schedules')
        if parameter == None:
            return self.request('GET', '/api/' + self.username + '/schedules/'+ str(schedule_id))

    def create_schedule(self, name, time, light_id, data, description = ' '):
        schedule = {
                    'name': name, 
                    'time': time, 
                    'description': description, 
                    'command':
                        {
                        'method': 'PUT', 
                        'address': '/api/' + self.username + '/lights/' + str(light_id) + '/state',
                        'body': data
                        }
                    }
        return self.request('POST', '/api/' + self.username + '/schedules', json.dumps(schedule))

    def create_group_schedule(self, name, time, group_id, data, description = ' '):
        schedule = {
                    'name': name, 
                    'time': time, 
                    'description': description, 
                    'command':
                        {
                        'method': 'PUT', 
                        'address': '/api/' + self.username + '/groups/' + str(group_id) + '/action',
                        'body': data
                        }
                    }
        return self.request('POST', '/api/' + self.username + '/schedules', json.dumps(schedule))

    def delete_schedule(self, schedule_id):
        return self.request('DELETE', '/api/' + self.username + '/schedules/' + str(schedule_id))

if __name__ == '__main__':
    b = Bridge()

    parser = argparse.ArgumentParser()
    parser.add_argument('pos1', type=list)
    parser.add_argument('pos2')
    parser.add_argument('pos3')
    args = parser.parse_args()
    print(args.pos1)

'''
light 1 on
light 2 off


group 1 on
group 2 off

light Cuisine on
light Cuisine off

'''


