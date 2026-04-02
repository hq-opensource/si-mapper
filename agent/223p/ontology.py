from bob.core import bind_model_namespace, dump, UNIT, Junction
from bob.enum import Role, Fluid
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
from bob.equipment.hvac.humidifier import SteamPipe
from bob.equipment.hvac.valve import ThreeWayValveMixing
from bob.connections.air import AirConnection, AirInletConnectionPoint, AirOutletConnectionPoint
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
        ("H-RET", AirTemperatureSensor): { 
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
        ("3WV-CC", ThreeWayValveMixing): {
            "comment": "3-Way Valve for Cooling Coil",
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
            "comment": "Humidifier Generator",
        },
        ("Hum-1-Pipe", SteamPipe): {
            "comment": "Humidifier Injection Pipe",
        },
    },
    "junctions": {
        ("ExhaustDuct", Junction): {
            "comment": "Duct to exhaust damper",
            "hasMedium": Fluid.Air,
            "fromExhaustFan": AirInletConnectionPoint,
            "toExhaustDamper": AirOutletConnectionPoint,
        },
        ("ReturnSplit", Junction): {
            "comment": "Splits return air to exhaust or mixed",
            "hasMedium": Fluid.Air,
            "fromReturnFan": AirInletConnectionPoint,
            "toRAV": AirOutletConnectionPoint,
            "toMelange": AirOutletConnectionPoint,
        },
        ("FreshAirMerge", Junction): {
            "comment": "Merges upper and lower fresh air dampers",
            "hasMedium": Fluid.Air,
            "fromUpper": AirInletConnectionPoint,
            "fromLower": AirInletConnectionPoint,
            "toMixedPlenum": AirOutletConnectionPoint,
        },
        ("MixedAirPlenum", Junction): {
            "comment": "Mixes return air and fresh air",
            "hasMedium": Fluid.Air,
            "fromFresh": AirInletConnectionPoint,
            "fromMelange": AirInletConnectionPoint,
            "toFilter": AirOutletConnectionPoint,
        },
    },
    "relations": [
        ("self['1-E'].airOutlet", ">>", "self['ExhaustDuct'].fromExhaustFan"),
        ("self['ExhaustDuct'].toExhaustDamper", ">>", "self['EVAC-Damper']['damper'].airInlet"),
        ("self['VFD-1-E'].electricalOutlet", ">>", "self['1-E'].electricalInlet"),
        
        ("self['1-R'].airOutlet", ">>", "self['ReturnSplit'].fromReturnFan"),
        ("self['ReturnSplit'].toRAV", ">>", "self['RAV-Damper']['damper'].airInlet"),
        ("self['ReturnSplit'].toMelange", ">>", "self['Melange-Damper']['damper'].airInlet"),
        ("self['VFD-1-R'].electricalOutlet", ">>", "self['1-R'].electricalInlet"),
        
        ("self['PAF-Upper-Damper']['damper'].airOutlet", ">>", "self['FreshAirMerge'].fromUpper"),
        ("self['PAF-Lower-Damper']['damper'].airOutlet", ">>", "self['FreshAirMerge'].fromLower"),
        ("self['FreshAirMerge'].toMixedPlenum", ">>", "self['MixedAirPlenum'].fromFresh"),
        
        ("self['Melange-Damper']['damper'].airOutlet", ">>", "self['MixedAirPlenum'].fromMelange"),
        ("self['MixedAirPlenum'].toFilter", ">>", "self['Filter-1'].airInlet"),
        
        ("self['Filter-1'].airOutlet", ">>", "self['CC-1'].airInlet"),
        ("self['CC-1'].airOutlet", ">>", "self['1-A'].airInlet"),
        ("self['1-A'].airOutlet", ">>", "self['HC-1'].airInlet"),
        ("self['HC-1'].airOutlet", ">>", "self['Hum-1-Pipe'].airInlet"),
        ("self['Hum-1'].steamOutlet", ">>", "self['Hum-1-Pipe'].steamInlet"),
        ("self['VFD-1-A'].electricalOutlet", ">>", "self['1-A'].electricalInlet"),
    ]
}

ahu = AirHandlingUnit(config=ahu_template)

# Sensor mappings
ahu["T-RET"] % ahu["1-R"]
ahu["H-RET"] % ahu["1-R"]
ahu["T-MIX"] % ahu["Filter-1"]
ahu["DP-Filter-1"] % ahu["Filter-1"]
ahu["SP-1"] % ahu["Hum-1-Pipe"]

if __name__ == "__main__":
    dump()
