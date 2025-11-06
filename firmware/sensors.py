import time
from typing import Optional, Tuple

# Prefer Adafruit library (easy). Graceful fallback if not installed.
try:
    import board, busio
    from adafruit_ina219 import INA219
    _HAVE_ADA = True
except Exception:
    _HAVE_ADA = False

from config import INA_ECM_ADDR, INA_PUMP_ADDR

# share a single I2C bus if available
_I2C = None
def _get_i2c():
    global _I2C
    if not _HAVE_ADA:
        return None
    if _I2C is None:
        _I2C = busio.I2C(board.SCL, board.SDA)
    return _I2C

class PowerSensor:
    """INA219 wrapper. If library is missing, returns zeros so code keeps running."""
    def __init__(self, address: int):
        self._ok = False
        if _HAVE_ADA:
            i2c = _get_i2c()
            try:
                self.ina = INA219(i2c, addr=address)
                self._ok = True
            except Exception:
                self._ok = False
        else:
            self._ok = False

    def read(self) -> Tuple[float, float, float, float]:
        """Return (bus_voltage_V, shunt_voltage_V, current_mA, power_mW)."""
        if not self._ok:
            return (0.0, 0.0, 0.0, 0.0)
        try:
            return (self.ina.bus_voltage, self.ina.shunt_voltage, self.ina.current, self.ina.power)
        except Exception:
            # transient I2C error → safe zeros
            return (0.0, 0.0, 0.0, 0.0)

class Instrumentation:
    def __init__(self, use_pump_sensor: bool = True):
        self.ecm = PowerSensor(INA_ECM_ADDR)
        self.pump = PowerSensor(INA_PUMP_ADDR) if use_pump_sensor else None

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
