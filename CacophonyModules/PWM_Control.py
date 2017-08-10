import Adafruit_PCA9685
import time
import threading
import RPi.GPIO as GPIO
import numpy

class X_Y_Control:
    x_channel = 0
    y_channel = 1
    x_ang = -1
    y_ang = -1
    min_ang = -82.5 #-82.5
    max_ang = 82.5 #82.5
    active = False

    # Field of view from thermal camera, used to calculate servo angle change.
    fov_h = 51 # horizontal fov
    fov_d = 63.5 # diagional fov

    # Thermal res
    thermal_x_res = 80;
    thermal_y_res = 60;

    angle_per_pixle = 51/80.0

    @classmethod
    def init(cls, config):
        print("X_Y_Control init.")
        cls.active = config["ServoControl"]["Active"]
        if cls.active:
            cls.set_x_y(0, 0)
        print("X_Y_Control init finished")

    @classmethod
    def new_frame(cls, frame):
        """ Takes a frame from the thermal camera and moves the servos to the 'hot spot' """
        (y, x) = numpy.unravel_index(frame.argmax(), frame.shape)
        x -= 40
        y -= 30
        #print(str(x)+", "+str(y))
        dx = -x/5
        dy = y/5
        if abs(x) <= 5:
            dx = 0
        if abs(y) <= 5:
            dy = 0

        cls.move_x_y(dx, dy)
        
    @classmethod
    def move_x_y(cls, dx, dy):
        cls.set_x_y(cls.x_ang+dx, cls.y_ang+dy)

    @classmethod
    def set_x_y(cls, x, y):
        if x != None:
            if x < cls.min_ang:
                x = cls.min_ang
            if x > cls.max_ang:
                x = cls.max_ang
            if cls.x_ang == x:
                PWM.set_dc(cls.x_channel, 0)
            else:
                cls.x_ang = x
                cls.set_servo_ang(cls.x_channel, cls.x_ang)
        if y != None:
            if y < cls.min_ang:
                y = cls.min_ang
            if y > cls.max_ang:
                y = cls.max_ang
            if cls.y_ang == y:
                PWM.set_dc(cls.y_channel, 0)
            else:
                cls.y_ang = y
                cls.set_servo_ang(cls.y_channel, cls.y_ang)

    @classmethod
    def set_servo_ang(cls, channel, ang):
        if cls.active and cls.active: 
            us_per_ang = (2200-800)/165.0
            us = 1500+ang*us_per_ang
            dc = (us*60.0)/1000000.0
            print(dc)
            PWM.set_dc(channel, dc)

class PWM:
    pca9685 = None
    piPwm = {} # RPi PWM pins
    
    @classmethod
    def init(cls, config):
        print("Setup for PWMs.")
        # Setup for the adafruit pca9685 pwm module
        if config["PwmControl"]["PCA9685"]:
            cls.pca9685 = Adafruit_PCA9685.PCA9685()
            cls.pca9685.set_pwm_freq(60)
        
        # Setup for on RPi onbord PWM.
        # The Pi PWM is not stable enough to control servos.
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        for pin in config["PwmControl"]["PiPwmPins"]:
            GPIO.setup(pin, GPIO.OUT)
            pwm = GPIO.PWM(pin, 60)
            pwm.start(0)
            cls.piPwm[pin] = pwm

    @classmethod
    def set_dc(cls, channel, dc):
        if cls.pca9685 != None:
            cls.pca9685.set_pwm(channel, 0, int(dc*4096))

    @classmethod
    def pi_set_dc(cls, pin, dc):
        cls.piPwm[pin].ChangeDutyCycle(dc)

class IR_Lights:
    active = False
    pca9685 = False
    channel = 2
    piPin = 13;
    dc = 0;
    action = None

    @classmethod
    def init(cls, config):
        print("IR_Lights init.")
        cls.active = config["IrLights"]["Active"]
        cls.pca9685 = config["IrLights"]["PCA9685"]
        cls.channel = config["IrLights"]["PCA9685Channel"]
        cls.piPin = config["IrLights"]["RPiPin"]

    @classmethod
    def off(cls):
        cls.set_dc(0)

    @classmethod
    def on(cls):
        cls.set_dc(100)

    @classmethod
    def inc(cls):
        cls.dc += 1
        if cls.dc > 100:
            cls.dc = 100
        cls.set_dc(cls.dc)

    @classmethod
    def dec(cls):
        cls.dc -= 1
        if cls.dc < 0:
            cls.dc = 100
        cls.set_dc(cls.dc)

    @classmethod
    def set_dc(cls, dc):
        if not cls.active:
            return
        cls.dc = dc
        if cls.pca9685:
            PWM.set(cls.channel, dc)
        else:
            PWM.pi_set_dc(cls.piPin, dc)

    @classmethod
    def inc_over_time(cls, t):
        cls.stop_action()
        cls.action = Inc_Ir_Thread(t)
        cls.action.start()

    @classmethod
    def dec_over_time(cls, t):
        cls.stop_action()
        cls.action = Dec_Ir_Thread(t)
        cls.action.start()

    @classmethod
    def stop_action(cls):
        if cls.action and cls.action.is_alive():
            cls.action.stop()
    
class Inc_Ir_Thread(threading.Thread):
    t = 0
    def __init__(self, t):
        self.t = t
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()

    def run(self):
        while IR_Lights.dc < 100 and not self._stop_event.is_set():
            IR_Lights.inc()
            time.sleep(self.t/100.0)

    def stop(self):
        self._stop_event.set()
            
class Dec_Ir_Thread(threading.Thread):
    t = 0
    def __init__(self, t):
        self.t = t
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()

    def run(self):
        while IR_Lights.dc > 0 and not self._stop_event.is_set():
            IR_Lights.dec()
            time.sleep(self.t/100.0)

    def stop(self):
        self._stop_event.set()
