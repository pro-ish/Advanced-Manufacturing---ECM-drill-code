import time
import RPi.GPIO as GPIO
from config import (STEP_PIN, DIR_PIN, EN_PIN, LIMIT_TOP_PIN, LIMIT_BOT_PIN,
                    STEPS_PER_MM, MAX_FEED_MM_S, MIN_FEED_MM_S, DEBOUNCE_MS,
                    HOME_DIR_UP, HOME_FEED_MM_S, HOME_BACKOFF_MM)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for p in (STEP_PIN, DIR_PIN, EN_PIN):
    GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)

for p in (LIMIT_TOP_PIN, LIMIT_BOT_PIN):
    GPIO.setup(p, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # NC → LOW when pressed

def _clamp_feed(feed_mm_s):
    return max(MIN_FEED_MM_S, min(MAX_FEED_MM_S, float(feed_mm_s)))

class MotionController:
    def __init__(self):
        self.enabled = False
        self.set_enabled(False)

    # ---- enable/disable driver ----
    def set_enabled(self, en: bool):
        # TMC2209 EN is active LOW
        GPIO.output(EN_PIN, GPIO.LOW if en else GPIO.HIGH)
        self.enabled = en

    # ---- helpers ----
    @staticmethod
    def top_limit():
        return GPIO.input(LIMIT_TOP_PIN) == GPIO.LOW

    @staticmethod
    def bot_limit():
        return GPIO.input(LIMIT_BOT_PIN) == GPIO.LOW

    def _dir_up(self, up: bool):
        GPIO.output(DIR_PIN, GPIO.HIGH if up else GPIO.LOW)

    def step_pulses(self, pulses: int, feed_mm_s: float):
        """Generate a given number of step pulses at a target feed (mm/s)."""
        feed = _clamp_feed(feed_mm_s)
        step_hz = feed * STEPS_PER_MM         # pulses per second
        if step_hz <= 0:
            return
        delay = 1.0 / (2.0 * step_hz)         # half-period

        for _ in range(int(pulses)):
            GPIO.output(STEP_PIN, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(STEP_PIN, GPIO.LOW)
            time.sleep(delay)

    def move_mm(self, mm: float, feed_mm_s: float):
        """Blocking move by mm (+up / −down). Stops if limit is hit."""
        if mm == 0:
            return
        up = (mm > 0)
        self._dir_up(up)
        steps = int(abs(mm) * STEPS_PER_MM)
        feed = _clamp_feed(feed_mm_s)
        step_hz = feed * STEPS_PER_MM
        delay = 1.0 / (2.0 * step_hz)

        for _ in range(steps):
            if (up and self.top_limit()) or ((not up) and self.bot_limit()):
                print("[MOTION] Limit hit; stopping move.")
                break
            GPIO.output(STEP_PIN, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(STEP_PIN, GPIO.LOW)
            time.sleep(delay)

    # ---- homing routine ----
    def home(self):
        """Seek the top limit (by default), back off, and re-approach slowly."""
        print("[MOTION] Homing...")
        self.set_enabled(True)

        # 1) approach
        self._dir_up(HOME_DIR_UP)
        while True:
            if (HOME_DIR_UP and self.top_limit()) or ((not HOME_DIR_UP) and self.bot_limit()):
                break
            GPIO.output(STEP_PIN, GPIO.HIGH); time.sleep(0.001)
            GPIO.output(STEP_PIN, GPIO.LOW);  time.sleep(0.001)

        time.sleep(DEBOUNCE_MS / 1000.0)

        # 2) backoff
        self._dir_up(not HOME_DIR_UP)
        self.move_mm(HOME_BACKOFF_MM if HOME_DIR_UP else -HOME_BACKOFF_MM, HOME_FEED_MM_S)

        # 3) slow re-approach
        self._dir_up(HOME_DIR_UP)
        while True:
            if (HOME_DIR_UP and self.top_limit()) or ((not HOME_DIR_UP) and self.bot_limit()):
                break
            GPIO.output(STEP_PIN, GPIO.HIGH); time.sleep(0.002)
            GPIO.output(STEP_PIN, GPIO.LOW);  time.sleep(0.002)

        print("[MOTION] Homed.")
