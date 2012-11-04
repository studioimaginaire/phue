#!/usr/bin/python

import urllib2
import httplib
import json
import os
import time

# Original protocol hacking by rsmck : http://rsmck.co.uk/hue

class Hue:
    def __init__(self, bridge_ip):
        self.config_file = os.path.join(os.getenv("HOME"),'.python_hue')
        self.bridge_ip = bridge_ip
        self.bridge_api_url = 'http://' + self.bridge_ip + '/api/'
        self.username = None
    
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
                        print 'Please press button on bridge to register application'
                    #if l['error']['type'] == 7:
                        #print 'Unknown username'
    def connect(self):
        try:
            print 'Attempting to connect to the bridge'
            with open(self.config_file) as f:
                self.username =  json.loads(f.read())[self.bridge_ip]['username']
                print 'Using username: ' + self.username
        
        except Exception as e:
            print 'Error opening config file, will attempt bridge registration'
            self.register_app()
    
    
    # With no arguments, prints the whole bridge information, with a lamp_id, prints the lamp information.
    def get_info(self, lamp_id = None):
        if lamp_id != None:
            u = urllib2.urlopen(self.bridge_api_url + self.username + '/lights/' + str(lamp_id))
        else:
            u = urllib2.urlopen(self.bridge_api_url + self.username)
        for line in u.readlines():
            print json.dumps(json.loads(line), indent=4)

    # lamp_id can be a single lamp or an array or lamps
    # parameters: 'on' : True|False , 'bri' : 0-254, 'sat' : 0-254, 'ct': 154-500
    def set_state(self, lamp_id, parameter, value):
        data = {parameter : value}
        connection = httplib.HTTPConnection(self.bridge_ip + ':80')
        lamp_id_array = lamp_id
        if type(lamp_id) == int:
            lamp_id_array = [lamp_id]
        for lamp in lamp_id_array:
            connection.request('PUT', '/api/' + self.username + '/lights/'+ str(lamp) + '/state', json.dumps(data))
            result = connection.getresponse()
            print result.read()
    
