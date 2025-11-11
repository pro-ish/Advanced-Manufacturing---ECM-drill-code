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

# ---- INA219 per-channel config ----
INA_ECM_ADDR       = 0x40
INA_PUMP_ADDR      = 0x41  # wire later if needed

# Your physical shunts (Ω)
ECM_SHUNT_OHMS     = 0.010
PUMP_SHUNT_OHMS    = 0.010

# If wiring makes current negative, flip here
ECM_INVERT_SIGN    = False
PUMP_INVERT_SIGN   = False

# Simple software zeroing (mA) added/subtracted after calibration
ECM_I_OFFSET_MA    = 0.0
PUMP_I_OFFSET_MA   = 0.0

# Tiny smoothing for display/logs (0 = off, 0.1 = gentle)
CURRENT_EMA_ALPHA  = 0.15

# ---- ECM material constants for MRR ----
ATOMIC_WEIGHT_KG_PER_MOL = 0.02698   # Aluminum
VALENCE_Z                 = 3
DENSITY_KG_PER_M3         = 2700.0
CURRENT_EFFICIENCY        = 0.90
FARADAY_C_PER_MOL         = 96485.33212
K_MM3_PER_COULOMB = (
    CURRENT_EFFICIENCY
    * ATOMIC_WEIGHT_KG_PER_MOL
    / (VALENCE_Z * FARADAY_C_PER_MOL * DENSITY_KG_PER_M3)
) * 1e9  # mm^3 per Coulomb

# ---- Hole target ----
TOOL_DIAMETER_MM = 1.00
OVERCUT_MM       = 0.00
TARGET_DEPTH_MM  = 2.00
