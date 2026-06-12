# Script for mocking the lego mindstorm modules.
# This script is solely for debugging the script on local computer
# mock_ev3dev2.py
import sys
from unittest.mock import MagicMock

class MockMotor:
    def __init__(self, *args, **kwargs): pass
    def on(self, speed): print(f"Motor on at speed {speed}")
    def off(self): print("Motor off")
    def stop(self, stop_action="coast"): print(f"Motor stop (action)={stop_action}")
    def on_for_seconds(self, speed, seconds, **kwargs): 
        print(f"Motor on at {speed} for {seconds}s")
    def on_for_degrees(self, speed, degrees, **kwargs): 
        print(f"Motor on at {speed} for {degrees}°")
    def on_for_rotations(self, speed, rotations, **kwargs): 
        print(f"Motor on at {speed} for {rotations} rotations")
    position = 0
    speed_sp = 0

class MockSensor:
    def __init__(self, *args, **kwargs): pass
    value = 0
    
class MockColorSensor(MockSensor):
    color = 0
    reflected_light_intensity = 50

class MockUltrasonicSensor(MockSensor):
    distance_centimeters = 100

class MockTouchSensor(MockSensor):
    is_pressed = False

class MockSound:
    @staticmethod
    def beep(): print("*beep*")
    @staticmethod
    def speak(text): print(f"Speaking: {text}")

class MockLeds:
    @staticmethod
    def set_color(side, color): print(f"LEDs {side}: {color}")
    @staticmethod
    def all_off(): print("LEDs off")

# Patch sys.modules before any ev3dev2 imports
mock_ev3dev2 = MagicMock()
mock_ev3dev2.motor.MediumMotor = MockMotor
mock_ev3dev2.motor.LargeMotor = MockMotor
mock_ev3dev2.motor.OUTPUT_A = 'outA'
mock_ev3dev2.motor.OUTPUT_B = 'outB'
mock_ev3dev2.motor.OUTPUT_C = 'outC'
mock_ev3dev2.motor.OUTPUT_D = 'outD'
mock_ev3dev2.sensor.touch.TouchSensor = MockTouchSensor
mock_ev3dev2.sensor.color.ColorSensor = MockColorSensor
mock_ev3dev2.sensor.ultrasonic.UltrasonicSensor = MockUltrasonicSensor
mock_ev3dev2.sound.Sound = MockSound
mock_ev3dev2.led.Leds = MockLeds

sys.modules['ev3dev2'] = mock_ev3dev2
sys.modules['ev3dev2.motor'] = mock_ev3dev2.motor
sys.modules['ev3dev2.sensor'] = mock_ev3dev2.sensor
sys.modules['ev3dev2.sensor.touch'] = mock_ev3dev2.sensor.touch
sys.modules['ev3dev2.sensor.color'] = mock_ev3dev2.sensor.color
sys.modules['ev3dev2.sensor.ultrasonic'] = mock_ev3dev2.sensor.ultrasonic
sys.modules['ev3dev2.sound'] = mock_ev3dev2.sound
sys.modules['ev3dev2.led'] = mock_ev3dev2.led