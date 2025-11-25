#!/usr/bin/env python3
"""
Simple ECM cycle (stop at bottom, keep pump ON):

1. Home to upper limit.
2. Pump ON at 80 %.
3. Move down at 0.5 mm/s until bottom limit (move_mm will stop on limit).
4. Stay there with pump running until Ctrl+C.
"""

import time, sys, signal
import RPi.GPIO as GPIO

from config import HOME_FEED_MM_S, STEPS_PER_MM
from motion import MotionController
from pump import PumpController
from safety import SafetyManager

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)


def cleanup(motion, pump, safety):
    try:
        pump.off()
    except Exception:
        pass
    try:
        motion.set_enabled(False)
    except Exception:
        pass
    try:
        safety.relay_off()
    except Exception:
        pass
    GPIO.cleanup()
    print("[SYS] Clean exit.")


def main():
    print("[SYS] ECM cycle starting (stop at bottom, pump stays on)…")

    safety = SafetyManager()
    motion = MotionController()
    pump   = PumpController()

    # E-STOP must be released for relay to arm
    print("[SAFETY] Ensure E-STOP released to arm 12 V relay (if used).")
    time.sleep(0.5)
    try:
        safety.relay_on()
    except Exception:
        # if relay not actually wired, ignore
        pass

    # Ctrl+C handler
    def _sigint(_s, _f):
        print("\n[SYS] Ctrl+C → aborting cycle.")
        cleanup(motion, pump, safety)
        sys.exit(0)

    signal.signal(signal.SIGINT, _sigint)

    try:
        # 1) Home to upper limit
        print("[STEP] Homing to upper limit…")
        motion.set_enabled(True)
        motion.home()

        # 2) Pump ON at 80 %
        pump_duty = 80.0
        print(f"[PUMP] ON @ {pump_duty:.0f} % duty.")
        pump.set_duty(pump_duty)
        time.sleep(0.5)

        # 3) Move down at 0.5 mm/s until bottom limit
        feed_mm_s = 0.5   # 0.5 mm/s → 0.5 * 1600 = 800 steps/s
        print(f"[STEP] Moving DOWN @ {feed_mm_s:.2f} mm/s until bottom limit…")
        # Large travel; move_mm will stop early when bot_limit() becomes True
        motion.move_mm(-100.0, 0.1)   # -100 mm = “big number”, rely on limit switch

        print("[SYS] Bottom reached (or travel completed).")
        print("[SYS] Pump remains ON. No upward move will be performed.")
        print("[SYS] Press Ctrl+C to stop pump and exit.")

        # 4) Hold position, keep pump running until user stops script
        while True:
            time.sleep(1.0)

    except Exception as e:
        print(f"[ERR] {e}")
        cleanup(motion, pump, safety)


if __name__ == "__main__":
    main()
