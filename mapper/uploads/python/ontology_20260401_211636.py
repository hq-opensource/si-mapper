from bob.core import bind_model_namespace, dump, UNIT
from bob.enum import Role
from bob.sensor.temperature import AirTemperatureSensor
from bob.sensor.pressure import AirDifferentialStaticPressureSensor
from bob.connections.electricity import Electricity_600VLL_3Ph_60HzInletConnectionPoint
from scratch.hvac.airhandlingunit import AirHandlingUnit
from scratch.hvac.fan import Fan
from scratch.electricity.vfd import VFD
from scratch.hvac.damper import ElectricalActuatedProportionalDamper
from bob.equipment.hvac.filter import Filter
from bob.equipment.hvac.coil import ChilledWaterCoil, HotWaterCoil
from scratch.hvac.humidifier import ElectricalHumidifier
from scratch.hvac.valve import TwoWayActuatedProportionalValve
from bob.connections.air import AirConnection
from scratch.assemblage import model_namespace

model_name, global_ns = model_namespace(__file__)
_namespace = bind_model_namespace(model_name, f"urn:{global_ns}:{model_name}/")

ahu_template = {
    "params": {"label": "AHU_SystemOne", "comment": "Air Handling Unit for System One"},
    "sensors": {
        ("T-RET", AirTemperatureSensor): {
            "hasUnit": UNIT.DEG_C,
            "comment": "Return Air Temperature",
        },
        ("H-RET", AirTemperatureSensor): { # Using temperature sensor as fallback for humidity if humidity sensor is missing, but let's use standard properties later.
            "hasUnit": UNIT.PERCENT_RH,
            "comment": "Return Air Humidity",
        },
        ("T-MIX", AirTemperatureSensor): {
            "hasUnit": UNIT.DEG_C,
            "comment": "Mixed Air Temperature",
        },
        ("DP-Filter-1", AirDifferentialStaticPressureSensor): {
            "hasUnit": UNIT.IN_H2O,
            "comment": "Filter Differential Pressure",
        },
        ("SP-1", AirDifferentialStaticPressureSensor): {
            "hasUnit": UNIT.IN_H2O,
            "comment": "Supply Static Pressure",
        },
    },
    "equipment": {
        ("1-E", Fan): {
            "comment": "Exhaust Fan",
            "hasRole": Role.Exhaust,
        },
        ("VFD-1-E", VFD): {
            "comment": "Exhaust Fan VFD",
        },
        ("EVAC-Damper", ElectricalActuatedProportionalDamper): {
            "comment": "Exhaust Damper",
        },
        ("1-R", Fan): {
            "comment": "Return Fan",
            "hasRole": Role.Return,
        },
        ("VFD-1-R", VFD): {
            "comment": "Return Fan VFD",
        },
        ("RAV-Damper", ElectricalActuatedProportionalDamper): {
            "comment": "RAV Damper",
        },
        ("Melange-Damper", ElectricalActuatedProportionalDamper): {
            "comment": "Mixed Air Damper",
        },
        ("PAF-Upper-Damper", ElectricalActuatedProportionalDamper): {
            "comment": "Upper Fresh Air Damper",
        },
        ("PAF-Lower-Damper", ElectricalActuatedProportionalDamper): {
            "comment": "Lower Fresh Air Damper",
        },
        ("Filter-1", Filter): {
            "comment": "Main Filter",
        },
        ("CC-1", ChilledWaterCoil): {
            "comment": "Cooling Coil",
        },
        ("3WV-CC", TwoWayActuatedProportionalValve): {
            "comment": "3-Way Valve for Cooling Coil (using TwoWay for now as proxy)",
        },
        ("1-A", Fan): {
            "comment": "Supply Fan",
            "hasRole": Role.Supply,
        },
        ("VFD-1-A", VFD): {
            "comment": "Supply Fan VFD",
        },
        ("HC-1", HotWaterCoil): {
            "comment": "Heating Coil",
        },
        ("Hum-1", ElectricalHumidifier): {
            "comment": "Humidifier",
        },
    },
    "relations": [
        ("self['1-E']", ">>", "self['EVAC-Damper']"),
        ("self['VFD-1-E']", ">>", "self['1-E']"),
        ("self['1-R']", ">>", "self['RAV-Damper']"),
        ("self['1-R']", ">>", "self['Melange-Damper']"),
        ("self['VFD-1-R']", ">>", "self['1-R']"),
        ("self['PAF-Upper-Damper']", ">>", "self['Filter-1']"),
        ("self['PAF-Lower-Damper']", ">>", "self['Filter-1']"),
        ("self['Melange-Damper']", ">>", "self['Filter-1']"),
        ("self['Filter-1']", ">>", "self['CC-1']"),
        ("self['CC-1']", ">>", "self['1-A']"),
        ("self['1-A']", ">>", "self['HC-1']"),
        ("self['HC-1']", ">>", "self['Hum-1']"),
        ("self['VFD-1-A']", ">>", "self['1-A']"),
    ]
}

ahu = AirHandlingUnit(config=ahu_template)

# Sensor mappings
ahu["T-RET"] % ahu["1-R"]
ahu["H-RET"] % ahu["1-R"]
ahu["T-MIX"] % ahu["Filter-1"]
ahu["DP-Filter-1"] % ahu["Filter-1"]
ahu["SP-1"] % ahu["Hum-1"]

if __name__ == "__main__":
    dump()
