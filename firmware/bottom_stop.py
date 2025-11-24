#!/usr/bin/env python3
"""
Simple ECM cycle (modified):
- Home to top
- Pump ON @ 80%
- Move down until bottom limit
- STOP there (no upward move)
- Pump stays ON until Ctrl+C
"""

import time, sys, signal
import RPi.GPIO as GPIO

from config import (
    HOME_FEED_MM_S,
    STEPS_PER_MM,
)
from motion import MotionController
from pump import PumpController
from safety import SafetyManager

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

def cleanup(motion, pump, safety):
    try: pump.off()
    except: pass
    try: motion.set_enabled(False)
    except: pass
    try: safety.relay_off()
    except: pass
    GPIO.cleanup()
    print("[SYS] Clean exit.")

def main():
    print("[SYS] ECM cycle starting (stop at bottom)…")

    safety = SafetyManager()
    motion = MotionController()
    pump   = PumpController()

    print("[SAFETY] Ensure E-STOP released.")
    time.sleep(0.5)
    safety.relay_on()

    def _sigint(_s,_f):
        print("\n[SYS] Ctrl+C → stopping.")
        cleanup(motion,pump,safety)
        sys.exit(0)

    signal.signal(signal.SIGINT, _sigint)

    try:
        # 1) Home
        print("[STEP] Homing to upper limit…")
        motion.set_enabled(True)
        motion.home()

        # 2) Pump ON
        print("[PUMP] ON @ 80%")
        pump.set_duty(80)
        time.sleep(0.5)

        # 3) Move down until bottom limit
        print("[STEP] Moving DOWN until bottom limit…")
        motion._dir_up(False)  # DOWN direction

        feed_mm_s = 0.1
        step_hz = feed_mm_s * STEPS_PER_MM
        delay = 1.0 / (2 * step_hz)

        while True:
            if motion.bot_limit():
                print("[LIMIT] Bottom limit reached — STOPPING movement.")
                break

            GPIO.output(motion.step_pin, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(motion.step_pin, GPIO.LOW)
            time.sleep(delay)

        print("[SYS] At bottom. Pump will stay ON. No upward move.")

        print("Press Ctrl+C to stop pump and exit…")
        while True:
            time.sleep(1)

    except Exception as e:
        print(f"[ERR] {e}")
        cleanup(motion,pump,safety)

if __name__ == "__main__":
    main()
