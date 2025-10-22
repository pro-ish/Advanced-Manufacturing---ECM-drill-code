import time
from typing import Optional

# Prefer Adafruit library (easy). Fallback to stub if not installed.
try:
    import board, busio
    from adafruit_ina219 import INA219
    _HAVE_ADA = True
except Exception:
    _HAVE_ADA = False

from config import INA_ECM_ADDR, INA_PUMP_ADDR

class PowerSensor:
    def __init__(self, address: int):
        if not _HAVE_ADA:
            raise RuntimeError("adafruit-circuitpython-ina219 not installed. "
                               "Install with: pip install adafruit-circuitpython-ina219")
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.ina = INA219(self.i2c, addr=address)

    def read(self):
        """Return tuple (bus_voltage_V, shunt_voltage_V, current_mA, power_mW)."""
        return (self.ina.bus_voltage, self.ina.shunt_voltage, self.ina.current, self.ina.power)

class Instrumentation:
    def __init__(self, use_pump_sensor=True):
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

