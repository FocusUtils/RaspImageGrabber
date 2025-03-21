import time
import atexit
from .state import State, abs_camera_type, abs_motor_type, abs_leds_type


def p_on(pin):
    if State.GPIO_default_on:
        GPIO.output(pin, GPIO.LOW)
    else:
        GPIO.output(pin, GPIO.HIGH)


def p_off(pin):
    if State.GPIO_default_on:
        GPIO.output(pin, GPIO.HIGH)
    else:
        GPIO.output(pin, GPIO.LOW)



class Motor(abs_motor_type):
    def __init__(self, pins):
        for pin in pins:
            GPIO.setup(pin, GPIO.OUT)
            p_off(pin)
        self.pins = pins
        self.bake_instructions()

        p_on(self.pins[0])
        self.step = self.instructuion_length * 2
    

    def bake_instructions(self):
        self.instructions = {}
        for idx in range(len(self.pins)):
            self.instructions[idx*2] = self.pins[(idx+1) % len(self.pins)]
            self.instructions[idx*2 + 1] = self.pins[idx]

        self.instructuion_length = len(self.instructions)



    def step_forward(self):
        start = time.perf_counter_ns()
        if self.step % 2 == 0:
            p_on(self.instructions[self.step % self.instructuion_length])

        if self.step % 2 == 1:
            p_off(self.instructions[self.step % self.instructuion_length])
        
        self.step += 1
        if self.step > self.instructuion_length*4:
            self.step = (self.step % self.instructuion_length) + self.instructuion_length
        time.sleep(max(0, (State.sleep_time_after_step / 1000) - (time.perf_counter_ns() - start)*10**-9))

    def step_backward(self):
        start = time.perf_counter_ns()
        if self.step % 2 == 0:
            p_on(self.instructions[(self.step-1) % self.instructuion_length])

        if self.step % 2 == 1:
            p_off(self.instructions[(self.step-1) % self.instructuion_length])
        
        self.step -= 1

        if self.step < self.instructuion_length:
            self.step = self.step + self.instructuion_length
        time.sleep(max(0, (State.sleep_time_after_step / 1000) - (time.perf_counter_ns() - start)*10**-9))


    def cleanup(self):
        for pin in self.pins:
            p_off(pin)
        
        
    def calibrate(self):
        for _ in self.pins:
            self.step_forward()
            time.sleep(.3)
            
        for _ in self.pins:
            self.step_backward()
            time.sleep(.3)
        

class Camera(abs_camera_type):
    def __init__(self, bcm_pin_number):
        self.pin = bcm_pin_number
        GPIO.setup(self.pin, GPIO.OUT)
        p_off(self.pin)

    def Close(self):
        p_off(self.pin)

    def Snap(self, *_):
        p_on(self.pin)
        time.sleep(2)
        p_off(self.pin)
        time.sleep(State.digi_cam_delay)
        State.progress()


class LEDS(abs_leds_type):
    def __init__(self, pins):
        for pin in pins:
            GPIO.setup(pin, GPIO.OUT)
            p_off(pin)
        self.pins = pins

    def on(self, idx):
        p_on(self.pins[idx])

    def off(self, idx):
        p_off(self.pins[idx])

    def all_on(self):
        for pin in self.pins:
            p_on(pin)

    def all_off(self):
        for pin in self.pins:
            p_off(pin)

    def cleanup(self):
        for pin in self.pins:
            p_off(pin)

import RPi
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

atexit.register(GPIO.cleanup)