import picamera
from os.path import join
import cPickle as pickle
import time

class Camera:
    recName = 'ir_vid.h264'
    recording = False
    recordingFolder = None
    startTime = None
    duration = None
    filePath = None

    def __init__(self, config):
        """ Inits the camera setting the resolution. """
        res_x = config['IrCamera']['res_x']
        res_y = config['IrCamera']['res_y']
        self.camera = picamera.PiCamera()
        self.camera.resolution = (res_x, res_y)
        self.camera.framerate = 24

    def start_recording(self, folder):
        """ Starts recording into the folder given. """
        if self.recording:
            print('ERROR: Device is already recording.')
            return
        print('Starting IR Camera recording.')
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

    def post_process(self):
        print("IrCamera post process")

    def get_file(self):
        return self.filePath

    def get_meta(self):
        return {
            "duration": int(self.duration)
            }
