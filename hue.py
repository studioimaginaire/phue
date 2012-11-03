#!/usr/bin/python

import urllib2
import json
import os
import time

class Hue:
    def __init__(self, bridge_ip):
        self.config_file = os.path.join(os.getenv("HOME"),'.python_hue')
        self.bridge_ip = bridge_ip
        self.bridge_api_url = 'http://' + self.bridge_ip + '/api/'
    
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
                username =  json.loads(f.read())[self.bridge_ip]['username']
                print 'Using username: ' + username
                self.get_bridge_information(username)
        
        except Exception as e:
            print e
            print 'Error opening config file, will attempt bridge registration'
            self.register_app()
    
    def get_bridge_information(self, username):
        u = urllib2.urlopen(self.bridge_api_url + username)
        for line in u.readlines():
            print json.dumps(json.loads(line), indent=4)
