#!/usr/bin/env python3
"""
TMC2209 step/dir driver test — jogs motor up/down safely.
"""
import time, sys, signal
import RPi.GPIO as GPIO
from config import (STEP_PIN, DIR_PIN, EN_PIN, LIMIT_TOP_PIN, LIMIT_BOT_PIN,
                    STEPS_PER_MM, MIN_FEED_MM_S)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(STEP_PIN, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(DIR_PIN,  GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(EN_PIN,   GPIO.OUT, initial=GPIO.HIGH)  # HIGH = disabled
GPIO.setup(LIMIT_TOP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(LIMIT_BOT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def top_limit(): return GPIO.input(LIMIT_TOP_PIN) == GPIO.LOW
def bot_limit(): return GPIO.input(LIMIT_BOT_PIN) == GPIO.LOW

def cleanup():
    GPIO.output(EN_PIN, GPIO.HIGH)
    GPIO.cleanup()

def pulses_at_rate(pulses, step_hz, up):
    GPIO.output(DIR_PIN, GPIO.HIGH if up else GPIO.LOW)
    half = 1.0 / (2.0 * step_hz)
    for _ in range(pulses):
        if (up and top_limit()) or ((not up) and bot_limit()):
            print("\n[LIMIT] Hit — stopping.")
            return False
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(half)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(half)
    return True

def main():
    print("[TMC2209] Stepper test starting...")
    def sigint(_s,_f):
        print("\n[SYS] Ctrl+C — exit")
        cleanup(); sys.exit(0)
    signal.signal(signal.SIGINT, sigint)

    GPIO.output(EN_PIN, GPIO.LOW)   # enable
    time.sleep(0.1)

    mm_each = 2.0
    speeds = (0.5, 1.0, 2.0)
    for v in speeds:
        step_hz = max(v, MIN_FEED_MM_S) * STEPS_PER_MM
        pulses  = int(mm_each * STEPS_PER_MM)
        print(f"[MOVE] Up {mm_each} mm @ {v:.2f} mm/s ({int(step_hz)} pps)")
        if not pulses_at_rate(pulses, step_hz, True): break
        time.sleep(0.4)
        print(f"[MOVE] Down {mm_each} mm @ {v:.2f} mm/s ({int(step_hz)} pps)")
        if not pulses_at_rate(pulses, step_hz, False): break
        time.sleep(0.6)

    print("[TMC2209] Disable driver (EN = HIGH).")
    GPIO.output(EN_PIN, GPIO.HIGH)
    _ = pulses_at_rate(200, 500, True)  # should not move
    print("[TMC2209] Test complete.")
    cleanup()

if __name__ == "__main__":
    main()
