#!/usr/bin/env python3
import os, csv, time, signal, sys
import RPi.GPIO as GPIO

from config import (LOG_DIR, LOG_FILE, MAX_FEED_MM_S, HOME_FEED_MM_S, PUMP_DUTY_RUN)
from motion import MotionController
from pump import PumpController
from safety import SafetyManager
from sensors import Instrumentation

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# graceful exit
def _cleanup_and_exit(mc, pc):
    try:
        mc.set_enabled(False)
    except Exception:
        pass
    try:
        pc.off()
    except Exception:
        pass
    try:
        GPIO.cleanup()
    except Exception:
        pass
    print("\n[SYS] Clean exit.")
    sys.exit(0)

def _sigint_handler(sig, frame):
    raise KeyboardInterrupt

signal.signal(signal.SIGINT, _sigint_handler)

def ensure_log():
    os.makedirs(LOG_DIR, exist_ok=True)
    path = os.path.join(LOG_DIR, LOG_FILE)
    if not os.path.exists(path):
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ts", "state", "ecm_V", "ecm_I_mA", "pump_I_mA", "pump_Lmin", "note"])
    return path

def log_row(path, state, instr, pump_Lmin=0.0, note=""):
    snap = instr.snapshot()
    eV = round(snap.get("ecm_bus_V", 0.0), 3)
    eI = round(snap.get("ecm_I_mA", 0.0), 1)
    pI = round(snap.get("pump_I_mA", 0.0), 1)
    with open(path, "a", newline="") as f:
        csv.writer(f).writerow([time.time(), state, eV, eI, pI, round(pump_Lmin, 3), note])

def main():
    print("[SYS] Bring-up – starting")
    log_path = ensure_log()

    safety = SafetyManager()
    motion = MotionController()
    pump   = PumpController()
    instr  = Instrumentation(use_pump_sensor=True)

    # Power path relay stays off until user is ready
    print("[SAFETY] Ensure E-STOP released to arm relay.")
    time.sleep(0.5)
    safety.relay_on()

    try:
        # ---- Homing ----
        motion.set_enabled(True)
        motion.home()

        # ---- Jog up 3 mm then down 3 mm ----
        motion.move_mm(+3.0, HOME_FEED_MM_S)
        motion.move_mm(-3.0, HOME_FEED_MM_S)

        # ---- Pump test sweep ----
        for duty in (20, 40, 60, 80, 100, 0):
            pump.set_duty(duty)
            time.sleep(2.0)
            # no flow sensor installed → always 0.0
            log_row(log_path, f"pump_duty_{duty}", instr, pump_Lmin=0.0, note="pump sweep")
            print(f"[PUMP] duty={duty:>3}%")

        # ---- Feed move with pump running ----
        pump.set_duty(PUMP_DUTY_RUN)
        motion.move_mm(+2.0, 1.0)  # demo feed
        motion.move_mm(-2.0, 1.0)
        log_row(log_path, "feed_demo", instr, pump_Lmin=0.0, note="2mm up/down")

        # idle
        pump.off()
        motion.set_enabled(False)
        safety.relay_off()

        print("[SYS] Bring-up script finished OK.")

    except KeyboardInterrupt:
        print("\n[SYS] KeyboardInterrupt")
    except Exception as e:
        print(f"[ERR] {e}")
    finally:
        _cleanup_and_exit(motion, pump)

if __name__ == "__main__":
    main()
