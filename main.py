import cv2
from pylepton import Lepton
import numpy as np
import time
from multiprocessing import Process, Queue
from CacophonyModules import CacoProcesses, IrCamera, ThermalCamera, Device
from collections import deque
from os.path import join
import picamera
import os
import json
from math import floor

CONFIG_FILE = 'config.json'
PRIVATE_SETTINGS = 'private'
RECORDINGS_FOLDER = 'recordings'

fileDir = os.path.dirname(os.path.realpath(__file__))

def init():
    print("Init new IR Camera, Thermal Camera, and Device.")
    with open(join(fileDir, CONFIG_FILE), 'r') as f:
        config = json.load(f)
        #print(config)
        ir_camera = IrCamera.Camera(config)
        thermal_camera = ThermalCamera.Camera(config)
        device = Device.device(config, join(fileDir, PRIVATE_SETTINGS))
    print("Init finished.")
    return ir_camera, thermal_camera, device

def save_new_settings(settings):
    with open(CONFIG_FILE, 'w') as configFile:
        json.dump(settings, configFile)


# Setup
ir_camera, thermal_camera, device = init()
queue = Queue()
recording = False
newSettingsFlag = False
newSettingsData = None

with Lepton() as l:
    while True:
        #Check to see if there are any new messages in the queue.
        if not queue.empty():
            message, data = queue.get(block=False)
            if message == 'NEW_JWT':
                #TODO
                print('New JWT')
            elif message == 'NEW_SETTINGS':
                #TODO
                print('NEW_SETTINGS')
                if recording:
                    # Dont want to save new setting when recording
                    newSettingsFlag = True
                    newSettings = data
                else:
                    # Save new settings and get new
                    save_new_settings(data)
                    ir_camera, thermal_camera, device = init()
                    
        # Get new thermal frame
        thermal_camera.new_frame(l)

        # Starting recording
        if not recording and thermal_camera.detection:
            # Make recording folder
            recordingTimeMillis = int(floor(time.time()*1000))
            recordingFolder = join(fileDir, RECORDINGS_FOLDER, str(recordingTimeMillis)) 
            os.makedirs(recordingFolder)
            recording = True
            thermal_camera.start_recording(recordingFolder)
            ir_camera.start_recording(recordingFolder)

        # Stoping recording
        if recording and not thermal_camera.detection:
            recording = False
            thermal_camera.stop_recording()
            ir_camera.stop_recording()
            p = Process(target = CacoProcesses.post_processing,
                args=(thermal_camera, ir_camera, device, queue))
            p.start()
            if newSettingsFlag:
                newSettingsFlag = False
                save_new_settings(newSettings)
            ir_camera, thermal_camera, device = init()
