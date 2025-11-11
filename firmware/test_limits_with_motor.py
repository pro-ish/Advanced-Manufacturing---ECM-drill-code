#!/usr/bin/env python3
"""
Limit-switch test with live motor motion (TMC2209 via STEP/DIR/EN).
- Moves toward TOP until its limit triggers, backs off, then moves toward BOT.
- Prints live limit states and stops immediately on trigger.
- Ctrl+C exits cleanly.

Wiring assumption (recommended fail-safe):
  COM -> GND, NC -> GPIO (internal pull-up)
If yours are NO, set EXPECT_NC_LIMITS = False.
"""
import time, sys, signal
import RPi.GPIO as GPIO
from config import (
    STEP_PIN, DIR_PIN, EN_PIN,
    LIMIT_TOP_PIN, LIMIT_BOT_PIN,
    STEPS_PER_MM, MIN_FEED_MM_S
)

# ======= USER TUNABLES =======
EXPECT_NC_LIMITS  = True     # True for NC→GND wiring (recommended)
START_TOWARD_TOP  = True     # True: go up first; False: go down first
TEST_FEED_MM_S    = 0.6      # test speed (mm/s)
BACKOFF_MM        = 1.0      # retract distance after a hit
STROKE_TIMEOUT_S  = 30       # safety timeout per stroke
# =============================

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Outputs
for p in (STEP_PIN, DIR_PIN, EN_PIN):
    GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)

# Inputs with pull-ups
GPIO.setup(LIMIT_TOP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(LIMIT_BOT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def read_limit(pin: int) -> bool:
    """Return True if limit is TRIGGERED."""
    level = GPIO.input(pin)
    if EXPECT_NC_LIMITS:
        # NC→GND: normal=LOW, triggered=HIGH
        return level == GPIO.HIGH
    else:
        # NO: normal=HIGH, triggered=LOW
        return level == GPIO.LOW

def print_limits(prefix=""):
    t = "TRIG" if read_limit(LIMIT_TOP_PIN) else "ok  "
    b = "TRIG" if read_limit(LIMIT_BOT_PIN) else "ok  "
    print(f"{prefix}LIMITS  TOP:{t}  BOT:{b}", end="\r")

def step_dir(up: bool):
    GPIO.output(DIR_PIN, GPIO.HIGH if up else GPIO.LOW)

def do_steps(pulses: int, step_hz: float, up: bool, stop_on_limit=True) -> int:
    """Return number of steps actually taken."""
    step_dir(up)
    half = 1.0 / (2.0 * step_hz)
    moved = 0
    t0 = time.time()
    for _ in range(pulses):
        # Stop if moving toward an active limit
        if stop_on_limit:
            if up and read_limit(LIMIT_TOP_PIN):
                print("\n[LIMIT] TOP triggered.")
                break
            if (not up) and read_limit(LIMIT_BOT_PIN):
                print("\n[LIMIT] BOT triggered.")
                break
        # Safety timeout
        if time.time() - t0 > STROKE_TIMEOUT_S:
            print("\n[SAFETY] Stroke timeout.")
            break
        # One step
        GPIO.output(STEP_PIN, GPIO.HIGH); time.sleep(half)
        GPIO.output(STEP_PIN, GPIO.LOW);  time.sleep(half)
        moved += 1
        if moved % max(1, (STEPS_PER_MM // 2)) == 0:
            print_limits(prefix="[MOVE] ")
    return moved

def mm_to_steps(mm: float) -> int:
    return int(abs(mm) * STEPS_PER_MM)

def cleanup():
    try: GPIO.output(EN_PIN, GPIO.HIGH)  # disable
    except: pass
    GPIO.cleanup()
    print("\n[SYS] Clean exit.")

def main():
    # Ctrl+C handler
    signal.signal(signal.SIGINT, lambda s,f: (cleanup(), sys.exit(0)))

    # Enable driver (active LOW on most TMC2209 boards)
    GPIO.output(EN_PIN, GPIO.LOW)
    time.sleep(0.2)

    # Basic state print
    print("[TEST] Limit-switch with motion test. Ctrl+C to exit.")
    print_limits(prefix=""); print()

    # Sanity: both limits triggered? refuse to move.
    if read_limit(LIMIT_TOP_PIN) and read_limit(LIMIT_BOT_PIN):
        print("[ERR] Both limits read TRIGGERED; check wiring.")
        cleanup(); return

    feed = max(TEST_FEED_MM_S, MIN_FEED_MM_S)
    step_hz = feed * STEPS_PER_MM
    backoff_steps = mm_to_steps(BACKOFF_MM)

    # 1) Move toward first end until limit hits, then back off.
    first_up = START_TOWARD_TOP
    print(f"[MOVE] Toward {'TOP' if first_up else 'BOT'} @ {feed:.2f} mm/s")
    moved = do_steps(pulses=mm_to_steps(1000), step_hz=step_hz, up=first_up, stop_on_limit=True)
    if moved == 0:
        print("[WARN] No movement registered; check EN/current/limits.")
    print(f"[BACKOFF] {BACKOFF_MM:.2f} mm")
    do_steps(pulses=backoff_steps, step_hz=step_hz/2, up=not first_up, stop_on_limit=False)

    time.sleep(0.5)

    # 2) Move toward the opposite end until its limit hits, then back off.
    print(f"[MOVE] Toward {'BOT' if first_up else 'TOP'} @ {feed:.2f} mm/s")
    moved = do_steps(pulses=mm_to_steps(1000), step_hz=step_hz, up=not first_up, stop_on_limit=True)
    print(f"[BACKOFF] {BACKOFF_MM:.2f} mm")
    do_steps(pulses=backoff_steps, step_hz=step_hz/2, up=first_up, stop_on_limit=False)

    print("\n[TEST] Done.")
    cleanup()

if __name__ == "__main__":
    main()
