import time
import threading
import RPi.GPIO as GPIO

class IR_Lights:
    pin = 13;
    val = 0;
    pwm = None
    action = None

    @classmethod
    def init(cls):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(cls.pin, GPIO.OUT)
        cls.pwm = GPIO.PWM(cls.pin, 200)
        cls.pwm.start(cls.val)

    @classmethod
    def off(cls):
        cls.set_val(0)

    @classmethod
    def on(cls):
        cls.set_val(100)

    @classmethod
    def inc(cls):
        cls.val += 1
        if cls.val > 100:
            cls.val = 100
        cls.set_val(cls.val)

    @classmethod
    def dec(cls):
        cls.val -= 1
        if cls.val < 0:
            cls.val = 100
        cls.set_val(cls.val)

    @classmethod
    def set_val(cls, val):
        cls.val = val
        cls.pwm.ChangeDutyCycle(val)

    @classmethod
    def inc_over_time(cls, t):
        cls.stop_action()
        cls.action = Inc_Thread(t)
        cls.action.start()

    @classmethod
    def dec_over_time(cls, t):
        cls.stop_action()
        cls.action = Dec_Thread(t)
        cls.action.start()

    @classmethod
    def stop_action(cls):
        if cls.action and cls.action.is_alive():
            cls.action.stop()
    
class Inc_Thread(threading.Thread):
    t = 0
    def __init__(self, t):
        self.t = t
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()

    def run(self):
        while IR_Lights.val < 100 and not self._stop_event.is_set():
            IR_Lights.inc()
            time.sleep(self.t/100.0)

    def stop(self):
        self._stop_event.set()
            
class Dec_Thread(threading.Thread):
    t = 0
    def __init__(self, t):
        self.t = t
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()

    def run(self):
        while IR_Lights.val > 0 and not self._stop_event.is_set():
            IR_Lights.dec()
            time.sleep(self.t/100.0)

    def stop(self):
        self._stop_event.set()
