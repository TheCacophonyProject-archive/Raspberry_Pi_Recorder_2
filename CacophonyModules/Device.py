import os
import random
import string
import json
import pickle
import requests

class device:
    group = None
    devicename = None
    server = None
    privateSettings = None
    serverUrl = None
    privateSettingsFile = None
    
    def __init__(self, config, privateSettingsFile):
        print("Device init.")
        # Save config settings
        if "Device" not in config:
            print("Error, no 'Device' in config.")
            return
        if "Group" in config["Device"]:
            self.group = config["Device"]["Group"]
        if "ServerUrl" in config["Device"]:
            self.serverUrl = config["Device"]["ServerUrl"]
        if "Name" in config["Device"]:
            self.devicename = config["Device"]["Name"]
        
        self.privateSettingsFile = privateSettingsFile

        # Check to see if there is private settings and if so load settings
        if os.path.isfile(privateSettingsFile):
            try:
                with open(privateSettingsFile, 'rb') as f:
                    self.privateSettings = pickle.load(f)
            except Exception as e:
                print("Failed to load private settings.")
                self.privateSettings = {}
        else:
            self.privateSettings = {}

        # Register if needed and get JWT
        if "jwt" in self.privateSettings:
            self.jwt = self.privateSettings["jwt"]
        elif "password" in self.privateSettings:
            self.get_new_jwt()
        else:
            self.register()
        print("Device init finished.")

    def get_new_jwt(self):
        # Check that we have devicename and password to get new jwt
        password = None
        devicename = self.devicename
        if "password" in self.privateSettigns:
            password = self.privateSettigns["password"]

        if password == None or devicename == None:
            # Device has to register if there is no password or devicename
            register()
            return
        
        serverUrl = self.serverUrl
        url = self.serverUrl + '/authenticate_device'
        try:
            payload = {
                'password': password,
                'devicename': devicename
                }
            r = requests.post(url, data = payload)
            if r.status_code == 200:
                j = json.loads(r.text)
                self.privateSettings["jwt"] = j["token"]
                self.save_private_settigns()
                print("New jwt")
            else:
                print("Error with getting new jwt.")
                print(r.text)
        except Exception as e:
            print(e)
            
    def register(self):
        devicename = self.devicename
        password = ''.join(random.sample(string.lowercase+string.digits, 20))
        group = self.group
        print("Registering")    
        url = self.serverUrl + '/api/v1/devices'
        payload = {
            'password': password,
            'devicename': devicename,
            'group': group
            }

        try:
            r = requests.post(url, data = payload)
            if r.status_code == 200:
                j = json.loads(r.text)
                self.privateSettings['password'] = password
                self.privateSettings['jwt'] = j["token"]
                self.save_private_settigns()
            else:
                print("Error with registering.")
                print(r.text)
        except Exception as e:
            print(e)
            print("Error with registering")
        

    def save_private_settigns(self):
        with open(self.privateSettingsFile, 'wb') as f:
            pickle.dump(self.privateSettings, f)
