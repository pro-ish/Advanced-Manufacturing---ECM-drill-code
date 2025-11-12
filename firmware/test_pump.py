#!/usr/bin/env python3
"""
Pump MOSFET test script
- Sweeps PWM duty from 0→100→0%.
- Useful for verifying gate drive and pump response.
"""

import time
import RPi.GPIO as GPIO
from config import PUMP_PWM_PIN, PUMP_PWM_HZ

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(PUMP_PWM_PIN, GPIO.OUT, initial=GPIO.LOW)
pwm = GPIO.PWM(PUMP_PWM_PIN, PUMP_PWM_HZ)
pwm.start(0)

print(f"[PUMP TEST] PWM on BCM{PUMP_PWM_PIN} @ {PUMP_PWM_HZ} Hz")
print("Ensure 24V relay ON and E-STOP released.")
time.sleep(1.0)

try:
    # Sweep up
    for duty in range(0, 101, 20):
        pwm.ChangeDutyCycle(duty)
        print(f"Duty = {duty:3d}%")
        time.sleep(2.0)

    # Hold full
    pwm.ChangeDutyCycle(100)
    print("Full ON (100%) for 3 seconds...")
    time.sleep(3.0)

    # Sweep down
    for duty in reversed(range(0, 101, 20)):
        pwm.ChangeDutyCycle(duty)
        print(f"Duty = {duty:3d}%")
        time.sleep(2.0)

    pwm.ChangeDutyCycle(0)
    print("Back to 0% — pump off.")

except KeyboardInterrupt:
    print("\n[SYS] KeyboardInterrupt — stopping.")
finally:
    pwm.stop()
    GPIO.cleanup()
    print("[PUMP TEST] Done.")
