import time
from typing import Tuple

# Try to use Adafruit INA219; fall back to zeros if not available.
try:
    import board, busio
    from adafruit_ina219 import INA219
    _HAVE_ADA = True
except Exception:
    _HAVE_ADA = False

from config import (
    INA_ECM_ADDR, INA_PUMP_ADDR,
    ECM_SHUNT_OHMS, PUMP_SHUNT_OHMS,
    ECM_INVERT_SIGN, PUMP_INVERT_SIGN,
    ECM_I_OFFSET_MA, PUMP_I_OFFSET_MA,
    CURRENT_EMA_ALPHA,
)

# Shared I2C
_I2C = None
def _get_i2c():
    global _I2C
    if not _HAVE_ADA:
        return None
    if _I2C is None:
        _I2C = busio.I2C(board.SCL, board.SDA)
    return _I2C

class _EMA:
    def __init__(self, alpha: float):
        self.alpha = max(0.0, min(1.0, float(alpha)))
        self._y = None
    def filt(self, x: float) -> float:
        if self.alpha <= 0.0:
            return x
        self._y = x if self._y is None else (self.alpha * x + (1 - self.alpha) * self._y)
        return self._y

class PowerSensor:
    """
    INA219 wrapper with simple per-channel scaling and offset.
    Adafruit lib defaults to 0.1Ω; we scale to match actual shunt values.
    """
    def __init__(self, address: int, shunt_ohms: float, invert_sign: bool, i_offset_mA: float, name: str):
        self.name = name
        self.scale = 0.0
        self.invert = -1.0 if invert_sign else 1.0
        self.i_off = float(i_offset_mA)
        self._ema_i = _EMA(CURRENT_EMA_ALPHA)
        self._ok = False

        if _HAVE_ADA:
            try:
                i2c = _get_i2c()
                self.ina = INA219(i2c, addr=address)
                # Adafruit library is calibrated for 0.1Ω typical configs; scale current/power
                self.scale = 0.1 / float(shunt_ohms if shunt_ohms > 0 else 0.1)
                self._ok = True
            except Exception:
                self._ok = False

    def read(self) -> Tuple[float, float, float, float]:
        """Return (bus_V, shunt_V, current_mA, power_mW) with scaling, sign, offset, and EMA."""
        if not self._ok:
            return (0.0, 0.0, 0.0, 0.0)
        try:
            bv = float(self.ina.bus_voltage)
            sv = float(self.ina.shunt_voltage)
            i  = float(self.ina.current) * self.scale * self.invert + self.i_off
            i  = self._ema_i.filt(i)
            p  = float(self.ina.power)   * self.scale * abs(self.invert)  # mW; signless
            return (bv, sv, i, p)
        except Exception:
            return (0.0, 0.0, 0.0, 0.0)

class Instrumentation:
    def __init__(self, use_pump_sensor: bool = False):
        self.ecm = PowerSensor(INA_ECM_ADDR, ECM_SHUNT_OHMS, ECM_INVERT_SIGN, ECM_I_OFFSET_MA, "ecm")
        self.pump = PowerSensor(INA_PUMP_ADDR, PUMP_SHUNT_OHMS, PUMP_INVERT_SIGN, PUMP_I_OFFSET_MA, "pump") if use_pump_sensor else None

    def snapshot(self):
        vb, vs, i, p = self.ecm.read()
        data = {
            "ecm_bus_V": vb,
            "ecm_shunt_V": vs,
            "ecm_I_mA": i,
            "ecm_P_mW": p,
        }
        if self.pump:
            vb2, vs2, i2, p2 = self.pump.read()
            data.update({
                "pump_bus_V": vb2,
                "pump_shunt_V": vs2,
                "pump_I_mA": i2,
                "pump_P_mW": p2
            })
        return data
