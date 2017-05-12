import picamera
from os.path import join
import cPickle as pickle
import time
import numpy as np
import os
from PIL import Image

class Camera:
    recName = 'ir_vid.h264'
    recording = False
    recordingFolder = None
    startTime = None
    duration = None
    filePath = None
    fps = None
    folder = None
    res_y = None
    res_x = None

    def __init__(self, config):
        """ Inits the camera setting the resolution. """
        self.res_x = config['IrCamera']['res_x']
        self.res_y = config['IrCamera']['res_y']
        self.camera = picamera.PiCamera()
        self.camera.resolution = (self.res_x, self.res_y)
        self.camera.framerate = 24
        self.fps = 24

    def start_recording(self, folder):
        """ Starts recording into the folder given. """
        if self.recording:
            print('ERROR: Device is already recording.')
            return
        print('Starting IR Camera recording.')
        self.folder = folder
        self.filePath = join(folder, self.recName)
        self.camera.start_recording(self.filePath)
        self.recording = True
        self.startTime = time.time()

    def stop_recording(self):
        if not self.recording:
            print('ERROR: Device is already not recording.')
            return
        print('Stopping IR Camera recording.')
        self.camera.close()
        self.recording = False
        self.duration = self.startTime - time.time()
        
    def save_metadata(self):
        """ Saves the metadata of the recording to file. """
        #TODO save apropriate data.
        with open(join(recordingFolder, 'irMeta'), 'w') as f:
            pickle.dump(data, f)

    def post_process(self, bufferDuration):
        print("IrCamera post process")

        # Create black image at save res as picamera
        rgb = np.zeros((self.res_y, self.res_x, 3), 'uint8')
        im = Image.fromarray(rgb, "RGB")
        imagePath = join(self.folder, 'blank.png')
        im.save(imagePath)

        # Render still
        blankPath = join(self.folder, 'blank.mp4')
        command = "avconv -loglevel error -loop 1 -r {f} -t {t} -i {i} {o}".format(
            f = self.fps, t = bufferDuration, i = imagePath, o = blankPath)
        print(command)
        os.system(command)

        # Render h264 to mp4
        self.mp4Vid = join(self.folder, 'vid.mp4')
        command = "avconv -loglevel error -r {f} -i {i} {o}".format(
            f = self.fps, i = self.filePath, o = self.mp4Vid)
        print(command)
        os.system(command)
        
        # Render still and h264 together.
        self.final = join(self.folder, 'final.mp4')
        command = "MP4Box -add {s} -cat {v} {o}".format(
            s = blankPath, v = self.mp4Vid, o = self.final)
        print(command)
        os.system(command)

        print("IrCamera post process finished")
        

    def get_file(self):
        return self.final

    def get_meta(self):
        return {
            "duration": int(self.duration)
            }
