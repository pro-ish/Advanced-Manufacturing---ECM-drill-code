#!/usr/bin/env python3
"""
ECM Drill – System Bring-up Test
- Arms relay and starts pump
- Jog tests (slow, short moves)
- Live limit switch monitor
- Detects physical E-STOP / PSU cut (if INA219 @ 0x40 is wired)

Safe defaults: slow speeds, tiny strokes, graceful cleanup.
"""

import time, signal, sys
import RPi.GPIO as GPIO

from config import (
    RELAY_PIN, PUMP_DUTY_RUN,
    LIMIT_TOP_PIN, LIMIT_BOT_PIN,
    STEPS_PER_MM, MIN_FEED_MM_S, HOME_FEED_MM_S,
)

# ==== USER TUNABLES ====
EXPECT_NC_LIMITS = True     # True if switches are NC→GND (recommended)
MM_STROKE        = 2.0      # small jog distance
FEED_MM_S        = 0.5      # gentle
PUMP_STABILIZE_S = 2.0      # time to prime/stabilize flow
ECM_V_CUT_V      = 2.0      # if bus_V < this, we assume E-STOP/PSU cut
USE_INA_CHECK    = True     # set False if INA219 not wired yet
# ========================

# Lazy imports so the script runs even if some modules aren’t installed yet
from safety import SafetyManager
from pump   import PumpController
from motion import MotionController
try:
    from sensors import Instrumentation
except Exception:
    Instrumentation = None

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Input pull-ups for limits
GPIO.setup(LIMIT_TOP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(LIMIT_BOT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(RELAY_PIN, GPIO.OUT, initial=GPIO.LOW)

def lim_state(pin):
    level = GPIO.input(pin)
    if EXPECT_NC_LIMITS:
        # NC→GND: normal = LOW (closed), triggered = HIGH (opened)
        return ("TRIGGERED", level == GPIO.HIGH)
    else:
        # NO: normal = HIGH (open), triggered = LOW (closed)
        return ("TRIGGERED", level == GPIO.LOW)

def show_limits(prefix=""):
    name, top_trig = lim_state(LIMIT_TOP_PIN)
    _,    bot_trig = lim_state(LIMIT_BOT_PIN)
    t = "TRIG" if top_trig else "ok  "
    b = "TRIG" if bot_trig else "ok  "
    print(f"{prefix}LIMITS  TOP:{t}  BOT:{b}", end="\r")

def main():
    print("[SYS] System bring-up test starting…")
    safety = SafetyManager()                 # software E-STOP can be disabled in safety.py
    pump   = PumpController()
    motion = MotionController()
    instr  = None
    if USE_INA_CHECK and Instrumentation:
        try:
            instr = Instrumentation(use_pump_sensor=False)
        except Exception:
            instr = None

    def cleanup():
        try: pump.off()
        except: pass
        try: motion.set_enabled(False)
        except: pass
        try: safety.relay_off()
        except: pass
        try: GPIO.cleanup()
        except: pass
        print("\n[SYS] Clean exit.")

    def sigint(_s,_f):
        print("\n[SYS] Ctrl+C")
        cleanup()
        sys.exit(0)
    signal.signal(signal.SIGINT, sigint)

    # --- Arm relay & start pump BEFORE motion ---
    print("[SAFETY] Arming relay…")
    safety.relay_on()
    time.sleep(0.2)

    print(f"[PUMP] Duty → {PUMP_DUTY_RUN}%  (priming {PUMP_STABILIZE_S:.1f}s)")
    pump.set_duty(PUMP_DUTY_RUN)
    t0 = time.time()
    while time.time() - t0 < PUMP_STABILIZE_S:
        show_limits(prefix="")
        time.sleep(0.05)
    print()

    # --- Quick limit sanity readout (user can press switches to confirm) ---
    print("[TEST] Press your limit switches now to verify states (2 s)…")
    t1 = time.time()
    while time.time() - t1 < 2.0:
        show_limits(prefix="")
        time.sleep(0.05)
    print()

    # --- Enable motor & perform short jogs with live limit guard ---
    motion.set_enabled(True)
    step_hz = max(FEED_MM_S, MIN_FEED_MM_S) * STEPS_PER_MM
    half = 1.0 / (2.0 * step_hz)
    pulses = int(MM_STROKE * STEPS_PER_MM)

    def limit_blocked(up: bool) -> bool:
        # Stop if moving toward a triggered limit
        _, top_trig = lim_state(LIMIT_TOP_PIN)
        _, bot_trig = lim_state(LIMIT_BOT_PIN)
        return (up and top_trig) or ((not up) and bot_trig)

    def estop_cut_detected() -> bool:
        if not instr:
            return False
        try:
            s = instr.snapshot()
            v = float(s.get("ecm_bus_V", 0.0))
            return v < ECM_V_CUT_V
        except Exception:
            return False

    def jog(up: bool):
        dir_txt = "UP  " if up else "DOWN"
        motion._dir_up(up)
        moved = 0
        for _ in range(pulses):
            if limit_blocked(up):
                print(f"\n[LIMIT] {dir_txt} blocked → stopping jog.")
                return
            if estop_cut_detected():
                print("\n[SAFETY] Power cut detected (E-STOP/PSU) → stopping.")
                return
            GPIO.output(motion.STEP_PIN if hasattr(motion, 'STEP_PIN') else 17, GPIO.HIGH)
            time.sleep(half)
            GPIO.output(motion.STEP_PIN if hasattr(motion, 'STEP_PIN') else 17, GPIO.LOW)
            time.sleep(half)
            moved += 1
            if moved % (STEPS_PER_MM // 2 or 1) == 0:
                show_limits(prefix=f"[MOVE {dir_txt}] ")
        print()

    print(f"[MOVE] Jog UP {MM_STROKE} mm @ {FEED_MM_S:.2f} mm/s")
    jog(True)
    time.sleep(0.5)
    print(f"[MOVE] Jog DOWN {MM_STROKE} mm @ {FEED_MM_S:.2f} mm/s")
    jog(False)

    # --- Wrap up ---
    print("[SYS] Test complete. Shutting down pump and relay.")
    pump.off()
    motion.set_enabled(False)
    safety.relay_off()
    cleanup()

if __name__ == "__main__":
    main()
