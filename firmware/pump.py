import time
import RPi.GPIO as GPIO
from collections import deque
from config import (PUMP_PWM_PIN, PUMP_PWM_HZ, PUMP_DUTY_IDLE, PUMP_DUTY_RUN,
                    FLOW_PIN, FLOW_PPL, DEBOUNCE_MS)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(PUMP_PWM_PIN, GPIO.OUT, initial=GPIO.LOW)
_pwm = GPIO.PWM(PUMP_PWM_PIN, PUMP_PWM_HZ)

GPIO.setup(FLOW_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

class PumpController:
    def __init__(self):
        self._duty = 0
        _pwm.start(PUMP_DUTY_IDLE)

        # Flow counting
        self._pulse_count = 0
        self._window = deque(maxlen=50)
        GPIO.add_event_detect(FLOW_PIN, GPIO.FALLING,
                              callback=self._flow_pulse, bouncetime=DEBOUNCE_MS)

    def _flow_pulse(self, ch):
        self._pulse_count += 1
        self._window.append(time.time())

    def set_duty(self, duty_percent: float):
        self._duty = max(0, min(100, float(duty_percent)))
        _pwm.ChangeDutyCycle(self._duty)

    def on(self, duty_percent=PUMP_DUTY_RUN):
        self.set_duty(duty_percent)

    def off(self):
        self.set_duty(0)

    def liters_per_min(self):
        """Estimate L/min from pulse timestamps (simple sliding window)."""
        now = time.time()
        # drop pulses older than 1 second
        while self._window and (now - self._window[0]) > 1.0:
            self._window.popleft()
        pulses_per_sec = len(self._window)
        if FLOW_PPL <= 0:
            return 0.0
        return (pulses_per_sec * 60.0) / float(FLOW_PPL)

