import RPi.GPIO as GPIO
from config import (PUMP_PWM_PIN, PUMP_PWM_HZ, PUMP_DUTY_IDLE, PUMP_DUTY_RUN)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(PUMP_PWM_PIN, GPIO.OUT, initial=GPIO.LOW)
_pwm = GPIO.PWM(PUMP_PWM_PIN, PUMP_PWM_HZ)

class PumpController:
    def __init__(self):
        self._duty = 0.0
        _pwm.start(PUMP_DUTY_IDLE)

    def set_duty(self, duty_percent: float):
        self._duty = max(0.0, min(100.0, float(duty_percent)))
        _pwm.ChangeDutyCycle(self._duty)

    def on(self, duty_percent=PUMP_DUTY_RUN):
        self.set_duty(duty_percent)

    def off(self):
        self.set_duty(0.0)

    # keep API compatible with main.py logs
    def liters_per_min(self) -> float:
        return 0.0
