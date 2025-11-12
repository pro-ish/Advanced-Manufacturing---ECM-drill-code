#!/usr/bin/env python3
"""
Keeps pump running at 80 % duty until stopped manually (Ctrl+C).
"""

import time, RPi.GPIO as GPIO
from config import PUMP_PWM_PIN, PUMP_PWM_HZ

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(PUMP_PWM_PIN, GPIO.OUT, initial=GPIO.LOW)

pump_pwm = GPIO.PWM(PUMP_PWM_PIN, PUMP_PWM_HZ)
pump_pwm.start(80)  # 80 % duty

print(f"[PUMP] Running at 80 % duty on BCM{PUMP_PWM_PIN} ({PUMP_PWM_HZ} Hz)")
print("Press Ctrl+C to stop...")

try:
    while True:
        time.sleep(1)  # idle loop; pump keeps running

except KeyboardInterrupt:
    print("\n[SYS] KeyboardInterrupt — stopping pump.")

finally:
    pump_pwm.stop()
    GPIO.cleanup()
    print("[SYS] Pump OFF, GPIO cleaned up.")
