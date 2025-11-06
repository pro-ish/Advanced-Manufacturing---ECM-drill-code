# =========================
# ECM Drill – Configuration
# =========================

# ---- GPIO map (BCM numbering) ----
STEP_PIN        = 17   # TMC2209 STEP
DIR_PIN         = 27   # TMC2209 DIR
EN_PIN          = 22   # TMC2209 EN (active LOW)

PUMP_PWM_PIN    = 18   # IRLZ44N gate (through 100Ω), PWM capable
RELAY_PIN       = 16   # Safety relay coil driver (via small NPN/MOSFET)

LIMIT_TOP_PIN   = 23   # NC to GND
LIMIT_BOT_PIN   = 24   # NC to GND
ESTOP_PIN       = 25   # NC to GND (software read; hardware still cuts power)

# ---- Motion & mechanics ----
STEPS_PER_REV   = 200          # typical NEMA-17
MICROSTEP       = 16           # TMC2209 microstepping
LEAD_MM_PER_REV = 2.0          # TR8x2 lead screw
STEPS_PER_MM    = int(STEPS_PER_REV * MICROSTEP / LEAD_MM_PER_REV)  # 1600
MAX_FEED_MM_S   = 3.0          # jogging/feed ceiling (safe)
MIN_FEED_MM_S   = 0.05

# ---- Pump control ----
PUMP_PWM_HZ     = 1000         # 1 kHz PWM for MOSFET
PUMP_DUTY_IDLE  = 0
PUMP_DUTY_RUN   = 60           # starting point; tune on bench

# ---- INA219 addresses (set by A0/A1 solder pads on modules) ----
INA_ECM_ADDR    = 0x40   # ECM loop shunt
INA_PUMP_ADDR   = 0x41   # pump branch shunt (optional)

# ---- Logging ----
LOG_DIR         = "data"
LOG_FILE        = "week4_bringup_log.csv"

# ---- Debounce / timing ----
DEBOUNCE_MS     = 20
SAFETY_POLL_MS  = 10

# ---- Shunt info (for notes; INA219 handles internally via library) ----
ECM_SHUNT_OHMS  = 0.01   # 10× 0.1Ω // parallel
PUMP_SHUNT_OHMS = 0.01

# ---- Homing ----
HOME_DIR_UP     = True   # True → set DIR to move toward TOP limit
HOME_FEED_MM_S  = 0.5
HOME_BACKOFF_MM = 0.5
