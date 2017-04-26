from pylepton import Lepton
from collections import deque
from os.path import join
import os
import numpy as np
import cPickle
import time
from PIL import Image
import cv2

class Camera:
    previousFrame = None
    previousId = None
    currentFrame = None
    currentId = None
    recordingFolder = None
    npyFile = None
    recording = False
    moveSens = None
    moveSize = None
    onSen = None
    offSen = None
    onCount = 0
    offCount = 0
    detection = False
    frames = 0
    startTime = None
    duration = None
    outputF = None

    def __init__(self, config):
        """ Inits lepton module. """
        self.previousFrame = None
        self.previousId = None

        
        self.moveSen =  config["ThermalCamera"]["MovementSensitivity"]
        self.moveSize = config["ThermalCamera"]["MovementSize"]
        self.onSen =    config["ThermalCamera"]["OnSensitivity"]
        self.offSen =   config["ThermalCamera"]["OffSensitivity"]
        self.frame_buffer = deque(maxlen=config["ThermalCamera"]["BufferSize"])
        

    def new_frame(self, lepton):
        # Set current frame to previous frame
        self.previousFrame = self.currentFrame
        self.previousId = self.currentId

        # Capure until the camera returns a new frame.
        while self.previousId == self.currentId:
            self.currentFrame, self.currentId = lepton.capture()
        self.currentFrame = np.resize(self.currentFrame, (60, 80))

        if self.recording:
            self.frames += 1
            np.save(self.npyFile, self.currentFrame)
        else:
            self.frame_buffer.append(self.currentFrame)

        # Detection from 2 frames 
        frameDetection = False
        diff = np.amax(self.currentFrame)-np.amin(self.currentFrame)
        if diff > 250:
            frameDetection = True
       # print(frameDetection)

        #
        if frameDetection:
            self.onCount += 1
            self.offCount = 0
        else:
            self.onCount = 0
            self.offCount += 1

        # No detection in a while, no longer detecting.
        if self.detection and self.offCount >= self.offSen:
            print('Detection off.')
            self.detection = False

        # Detection for a few frames, is now detecting.
        elif not self.detection and self.onCount >= self.onSen:
            print('Detection on.')
            self.detection = True


    def start_recording(self, folder):
        self.frames = 0
        self.recordingFolder = folder
        self.npyFile = open(join(self.recordingFolder, '001.npy'), 'w')
        self.recording = True
        self.startTime = time.time()

    def stop_recording(self):
        self.npyFile.close()
        self.stop_recording = False
        self.recording = False
        self.duration = time.time()-self.startTime
        
    def save_metadata(self):
        """ Saves the metadata of the recording to file. """
        #TODO save apropriate data.
        data = {'a':1, 'b':2}
        with open(join(self.recordingFolder, 'thermalMeta'), 'w') as f:
            cPickle.dump(data, f)

    def post_process(self):
        print('Thermal Camera post process')

        # Get size of buffer
        bufferLen = 0
        for frame in self.frame_buffer:
            bufferLen += 1

        # Make npz object to be compressed
        npz = np.zeros((self.frames+bufferLen, 60, 80))

        # Make image folder
        imageFolder = join(self.recordingFolder, 'images')
        os.makedirs(imageFolder)

        i = 0 # Frame counter
        # Process the buffer frames
        for frame in self.frame_buffer:
            rgb = process_frame_to_rgb(frame)
            save_rgb_as_image(rgb, i, imageFolder)
            i += 1

        with open(join(self.recordingFolder, '001.npy'), 'r') as npy:
            for n in range(self.frames):
                frame = np.load(npy)
                rgb = process_frame_to_rgb(frame)
                save_rgb_as_image(rgb, i, imageFolder)
                i += 1

        # Render to AVI
        inputF = join(imageFolder, "%06d.png")
        self.outputF = join(self.recordingFolder, "file.avi")
        fps = (self.frames+bufferLen)/self.duration
        command = "/usr/local/bin/ffmpeg -r {f} -i {i} {o}".format(
            f = fps, i = inputF, o = self.outputF)
        print(command)
        os.system(command)

    def get_file(self):
        return self.outputF

    def get_meta(self):
        metadata = {
            "duration": int(self.duration)
            }
        return metadata

def process_frame_to_rgb(frame):
    # Process frame to rgb image
    frame = cv2.normalize(frame, frame, 0, 65535, cv2.NORM_MINMAX)
    im = Image.new("RGB", (80, 60))
    rgb = []
    for i in frame:
        for j in i:
            rgb.append(get_heat_rgb(j/65535.0))
    return rgb

def get_heat_rgb(n):
    if (n >= 0 and n < 0.25):
        r = 0
        g = n*4*255
        b = 255
    elif (n < 0.5):
        r = 0
        g = 255
        b = 255-((n-0.25)*4*255)
    elif (n < 0.75):
        r = (n-0.5)*4*255
        b = 0
        g = 255
    elif (n <= 1):
        r = 255
        g = 255-(n-0.75)*4*255
        b = 0
    else:
        print('Error: number out or range, should be from 0-1')
        return 0, 0, 0
    return int(r), int(g), int(b)

def save_rgb_as_image(rgb, n, folder):
    im = Image.new("RGB", (80, 60))
    im.putdata(rgb)
    imName = str(n).zfill(6) + '.png'
    im.save(join(folder, imName))

