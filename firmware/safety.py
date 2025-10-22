import time
import RPi.GPIO as GPIO
from config import (ESTOP_PIN, RELAY_PIN, DEBOUNCE_MS, SAFETY_POLL_MS)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(ESTOP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP) # NC → LOW when pressed
GPIO.setup(RELAY_PIN, GPIO.OUT, initial=GPIO.LOW)        # drive transistor to energize coil

class SafetyManager:
    def __init__(self):
        self._estop_active = False
        # event detect for quick response
        GPIO.add_event_detect(ESTOP_PIN, GPIO.BOTH, callback=self._estop_changed, bouncetime=DEBOUNCE_MS)

    def _estop_changed(self, ch):
        pressed = GPIO.input(ESTOP_PIN) == GPIO.LOW
        self._estop_active = pressed
        if pressed:
            self.relay_off()
            print("[SAFETY] E-STOP PRESSED → relay OFF")
        else:
            print("[SAFETY] E-STOP released (software). Use caution.")

    def relay_on(self):
        """Energize safety relay (enables PSU output path)."""
        if not self._estop_active:
            GPIO.output(RELAY_PIN, GPIO.HIGH)

    def relay_off(self):
        GPIO.output(RELAY_PIN, GPIO.LOW)

    def estop(self):
        """Force estop state in software (does not replace hardware estop)."""
        self._estop_active = True
        self.relay_off()

    def estop_active(self) -> bool:
        return self._estop_active

    def wait_clear(self):
        while self._estop_active:
            time.sleep(SAFETY_POLL_MS/1000.0)

