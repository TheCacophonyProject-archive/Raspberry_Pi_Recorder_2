#!/usr/bin/python
import cv2
from pylepton.Lepton3 import Lepton3
import numpy as np
import time
from multiprocessing import Process, Queue
from CacophonyModules import CacoProcesses, IrCamera, ThermalCamera, Device
from CacophonyModules.PWM_Control import X_Y_Control, IR_Lights, PWM
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

with open(join(fileDir, CONFIG_FILE), 'r') as f:
    config = json.load(f)
    PWM.init(config)
    IR_Lights.init(config)
    X_Y_Control.init(config)

def init():
    print("Init new IR Camera, Thermal Camera, and Device.")
    with open(join(fileDir, CONFIG_FILE), 'r') as f:
        config = json.load(f)
        #print(config)
        ir_camera = IrCamera.Camera(config)
        thermal_camera = ThermalCamera.Camera(config)
        device = Device.device(config, join(fileDir, PRIVATE_SETTINGS))
    print("Init finished.")
    return ir_camera, thermal_camera, device, config['Main']['MaxRecordingLen'], config['Main']['MaxWaitTime']

def save_new_settings(settings):
    with open(CONFIG_FILE, 'w') as configFile:
        json.dump(settings, configFile)


# Setup
ir_camera, thermal_camera, device, maxRecordingLen, maxWaitTime = init()
queue = Queue()
recording = False
newSettingsFlag = False
newSettingsData = None
recordingStartTime = None
overMaxRecordingLen = None

with Lepton3() as l:
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

        if thermal_camera.frameDetection:
            X_Y_Control.new_frame(thermal_camera.currentFrame)
        else:
            # Stops servos 'buzzing' noise
            X_Y_Control.move_x_y(0, 0)

        if recordingStartTime and time.time()-recordingStartTime >= maxRecordingLen:
            overMaxRecordingLen = True
            print("Max recording len. Stopping recording.")

        # Starting recording
        if not recording and thermal_camera.detection and not overMaxRecordingLen:
            print("Starting recording.")
            IR_Lights.inc_over_time(10)
            # Make recording folder
            recordingStartTime = time.time()
            recordingFolder = join(fileDir, RECORDINGS_FOLDER, str(int(recordingStartTime)))
            os.makedirs(recordingFolder)
            recording = True
            thermal_camera.start_recording(recordingFolder)
            ir_camera.start_recording(recordingFolder)

        # Stoping recording
        if (recording and not thermal_camera.detection) or overMaxRecordingLen:
            recording = False
            IR_Lights.dec_over_time(10)
            thermal_camera.stop_recording()
            ir_camera.stop_recording()
            p = Process(target = CacoProcesses.post_processing,
                args=(thermal_camera, ir_camera, device, queue))
            p.start()
            if newSettingsFlag:
                newSettingsFlag = False
                save_new_settings(newSettings)

            # Wait for thermal camera to stop detection.
            if thermal_camera.detection:
                print("Waiting fot detection to stop before starting again")
            stopTime = time.time()
            while thermal_camera.detection and time.time()-stopTime < maxWaitTime:
                thermal_camera.new_frame(l)
            if not thermal_camera.detection:
                print("Detection stopped.")
            else:
                print("Max stop time exceded.")
            overMaxRecordingLen = False
            
            ir_camera, thermal_camera, device, maxRecordingLen, maxWaitTime = init()
            recordingStartTime = None
