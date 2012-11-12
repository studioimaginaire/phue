#!/usr/bin/python

import urllib2
import httplib
import json
import os

# Original protocol hacking by rsmck : http://rsmck.co.uk/hue

class Light(object):
    def __init__(self, bridge, light_id):
        self.bridge = bridge
        self.light_id = light_id
        
        self._name = None
        self._on = None
        self._brightness = None
        self._hue = None
        self._saturation = None
        self._xy = None
        self._colortemp = None
        self._alert = None
       
    @property
    def name(self):
        self._name = self.bridge.get_state(self.light_id, 'name')
        return self._name

    @name.setter
    def name(self, value):
        old_name = self.name
        self._name = value
        self.bridge.set_state(self.light_id, 'name', self._name)
        
        self.bridge.lights_by_name[self.name] = self 
        del self.bridge.lights_by_name[old_name]

    @property
    def on(self):
        self._on = self.bridge.get_state(self.light_id, 'on')
        return self._on

    @on.setter
    def on(self, value):
        self._on = value
        self.bridge.set_state(self.light_id, 'on', self._on)

    @property
    def brightness(self):
        self._brightness = self.bridge.get_state(self.light_id, 'bri')
        return self._brightness

    @brightness.setter
    def brightness(self, value):
        self._brightness = value
        self.bridge.set_state(self.light_id, 'bri', self._brightness)
    
    @property
    def hue(self):
        self._hue = self.bridge.get_state(self.light_id, 'hue')
        return self._hue

    @hue.setter
    def hue(self, value):
        self._hue = value
        self.bridge.set_state(self.light_id, 'hue', self._hue)

    @property
    def saturation(self):
        self._saturation = self.bridge.get_state(self.light_id, 'sat')
        return self._saturation

    @saturation.setter
    def saturation(self, value):
        self._saturation = value
        self.bridge.set_state(self.light_id, 'sat', self._saturation)

    @property
    def xy(self):
        self._xy = self.bridge.get_state(self.light_id, 'xy')
        return self._xy

    @xy.setter
    def xy(self, value):
        self._xy = value
        self.bridge.set_state(self.light_id, 'xy', self._xy)

    @property
    def colortemp(self):
        self._colortemp = self.bridge.get_state(self.light_id, 'ct')
        return self._colortemp

    @colortemp.setter
    def colortemp(self, value):
        self._colortemp = value
        self.bridge.set_state(self.light_id, 'ct', self._colortemp)

    @property
    def alert(self):
        self._colortemp = self.bridge.get_state(self.light_id, 'alert')
        return self._alert

    @alert.setter
    def alert(self, value):
        self._alert = value
        self.bridge.set_state(self.light_id, 'alert', self._alert)

class Bridge(object):
    def __init__(self, bridge_ip, username = None):
        self.config_file = os.path.join(os.getenv("HOME"),'.python_hue')
        self.bridge_ip = bridge_ip
        self.username = username
        self.bridge_api_url = 'http://' + self.bridge_ip + '/api/'
        self.lights_by_id = {}
        self.lights_by_name = {}
        self._name = None

        self.minutes = 600
        self.seconds = 10
        
        self.connect()
    
    @property
    def name(self):
        self._name = json.loads(urllib2.urlopen(self.bridge_api_url + self.username +'/config').read())['name']
        return self._name
    
    @name.setter
    def name(self, value):
        self._name = value
        data = {'name' : self._name}
        connection = httplib.HTTPConnection(self.bridge_ip + ':80')
        connection.request('PUT', '/api/' + self.username + '/config', json.dumps(data))
        print connection.getresponse().read()

    def register_app(self):
        registration_request = {"username": "python_hue", "devicetype": "python_hue"}
        data = json.dumps(registration_request)
        u = urllib2.urlopen(self.bridge_api_url, data)
        for line in u.readlines():
            for l in json.loads(line):
                if 'success' in l:
                    with open(self.config_file, 'w') as f:
                        print 'Writing configuration file to ' + self.config_file
                        f.write(json.dumps({self.bridge_ip : l['success']}))
                        print 'Reconnecting to the bridge'
                    self.connect()
                if 'error' in l:
                    if l['error']['type'] == 101:
                        print 'Please press button on bridge to register application and call connect() method'
                    #if l['error']['type'] == 7:
                        #print 'Unknown username'
    def connect(self):
        print 'Attempting to connect to the bridge'
        if self.username == None:
            try:
                with open(self.config_file) as f:
                    self.username =  json.loads(f.read())[self.bridge_ip]['username']
                    print 'Using username: ' + self.username
        
            except Exception as e:
                print 'Error opening config file, will attempt bridge registration'
                self.register_app()
        else:
            print 'Using username: ' + self.username

    #Returns a dictionary containing the lights, either by name or id (use 'id' or 'name' as the mode)
    def get_lights(self, mode):
        if self.lights_by_id == {}:
            lights =  json.loads(urllib2.urlopen(self.bridge_api_url + self.username + '/lights/').read())
            for light in lights:
                self.lights_by_id[int(light)] = Light(self, int(light))
                self.lights_by_name[lights[light]['name']] = self.lights_by_id[int(light)]
        if mode == 'id':
            return self.lights_by_id
        if mode == 'name':
            return self.lights_by_name

    
    # Return the dictionary of the whole bridge
    def get_info(self):
        u = urllib2.urlopen(self.bridge_api_url + self.username)
        for line in u.readlines():
            return json.loads(line)            

    # Gets state by light_id and parameter
    def get_state(self, light_id, parameter):
        u = urllib2.urlopen(self.bridge_api_url + self.username +  '/lights/' + str(light_id))
        converted = json.loads(u.read())
        if parameter == 'name':
            return converted[parameter]
        else:
            return converted['state'][parameter]


    # light_id can be a single lamp or an array or lamps
    # parameters: 'on' : True|False , 'bri' : 0-254, 'sat' : 0-254, 'ct': 154-500
    def set_state(self, light_id, parameter, value = None):
        if type(parameter) == dict:
            data = parameter
        else:
            data = {parameter : value}
        connection = httplib.HTTPConnection(self.bridge_ip + ':80')
        light_id_array = light_id
        if type(light_id) == int:
            light_id_array = [light_id]
        for light in light_id_array:
            if parameter  == 'name':
                connection.request('PUT', '/api/' + self.username + '/lights/'+ str(light_id), json.dumps(data))
            else:
                connection.request('PUT', '/api/' + self.username + '/lights/'+ str(light) + '/state', json.dumps(data))
            result = connection.getresponse()
            print result.read()


