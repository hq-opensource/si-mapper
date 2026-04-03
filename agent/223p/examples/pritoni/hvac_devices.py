import physical_spaces as ps
from bob.connections.electricity import (
    Electricity_120VLN_1Ph_60HzInletConnectionPoint,
    Electricity_600VLL_3Ph_60HzInletConnectionPoint,
)
from bob.connections.air import (
    AirInletConnectionPoint,
    AirOutletConnectionPoint,
)
from bob.core import UNIT, Role, bind_model_namespace, dump, Junction
from scratch.architectural.window import Window
from scratch.hvac.boiler import ElectricalHotWaterBoiler
from scratch.hvac.chiller import Chiller
from bob.equipment.hvac.coil import ChilledWaterCoil, HotWaterCoil
from bob.equipment.hvac.filter import Filter
from bob.equipment.hvac.heatexchanger import AirHeatExchanger
from scratch.hvac.pump import Pump
from bob.sensor.pressure import AirDifferentialStaticPressureSensor
from bob.sensor.temperature import AirTemperatureSensor
from bob.enum import Fluid

from scratch.assemblage import model_namespace
from scratch.electricity.starter import MotorStarter_600VLL_3Ph_60Hz as MotorStarter
from scratch.electricity.vfd import VFD

# Prototypes
from scratch.hvac.airhandlingunit import AirHandlingUnit
from scratch.hvac.damper import ElectricalActuatedProportionalDamper
from scratch.hvac.fan import Fan
from scratch.hvac.valve import TwoWayActuatedProportionalValve
from scratch.hvac.vav import VAV, vav_withhotwaterreheat_template

model_name, global_ns = model_namespace(__file__)
_namespace = bind_model_namespace(model_name, f"urn:{global_ns}:{model_name}/")


t = {
    "params": {"label": "AHU", "comment": "AHU delivering air to 2 VAV boxes"},
    "relations": [
        '("self[\'SF_Starter\'].electricalOutlet", ">>", "self[\'SF\'].electricalInlet")',
        '("self[\'RF_VFD\'].electricalOutlet", ">>", "self[\'RF\'].electricalInlet")',
        '(\'self["OADPR"].airOutlet\', ">>", "self.mixedAir")',
        '(\'self["MADPR"].airOutlet\', ">>", "self.mixedAir")',
        '("self.mixedAir", ">>", \'self["FILTER"].airInlet\')',
        '(\'self["FILTER"].airOutlet\', ">>", \'self["CLGCOIL"].airInlet\')',
        '(\'self["CLGCOIL"].airOutlet\', ">>", \'self["SF"].airInlet\')',
        '(\'self["SF"].airOutlet\', ">>", \'self["HTGCOIL"].airInlet\')',
        '(\'self["HTGCOIL"].airOutlet\', ">>", "self.supplyAir")',
        '("self.returnAir", ">>", \'self["RF"].airInlet\')',
        '(\'self["RF"].airOutlet\', ">>", "self.returnExhaust")',
        '("self.returnExhaust", ">>", \'self["EADPR"].airInlet\')',
        '("self.returnExhaust", ">>", \'self["MADPR"].airInlet\')',
    ],
}


ahu_template = {
    "params": {"label": "AHU", "comment": "AHU delivering air to 2 VAV boxes"},
    "sensors": {
        ("OA-T", AirTemperatureSensor): {
            "hasUnit": UNIT.DEG_C,
            "comment": "Oudoor air temperature (S3)",
        },
        ("TPD1", AirDifferentialStaticPressureSensor): {
            "hasUnit": UNIT.PA,
            "comment": "Filter Differential Pressure Sensor (S5)",
        },
        ("HC-T", AirTemperatureSensor): {
            "hasUnit": UNIT.DEG_C,
            "comment": "Air temperature after heating coil (S6)",
        },
        ("MA-T", AirTemperatureSensor): {
            "hasUnit": UNIT.DEG_F,
            "comment": "Return Air temperature (S4)",
        },
        ("DA-T", AirTemperatureSensor): {
            "hasUnit": UNIT.DEG_F,
            "comment": "Discharge Air temperature after cooling coil (S7)",
        },
        ("RA-T", AirTemperatureSensor): {
            "hasUnit": UNIT.DEG_F,
            "comment": "Return Air temperature (S2)",
        },
        ("TPD2", AirDifferentialStaticPressureSensor): {
            "hasUnit": UNIT.PA,
            "comment": "Supply Duct Static Pressure (S8)",
        },
        ("TPD3", AirDifferentialStaticPressureSensor): {
            "hasUnit": UNIT.PA,
            "comment": "Return Duct Static Pressure (S1)",
        },
    },
    "equipment": {
        ("RF", Fan): {
            "comment": "Return Air Fan",
            "electricalInlet": Electricity_600VLL_3Ph_60HzInletConnectionPoint,
            "hasRole": Role.Return,
        },
        ("RF_VFD", VFD): {
            "comment": "Return Air Fan VFD",
        },
        ("SF", Fan): {
            "comment": "Supply Air Fan",
            "electricalInlet": Electricity_600VLL_3Ph_60HzInletConnectionPoint,
            "hasRole": Role.Supply,
        },
        ("SF_Starter", MotorStarter): {
            "comment": "Supply Air Fan Starter",
        },
        ("CLGCOIL", ChilledWaterCoil): {"comment": "Cooling Coil"},
        ("HTGCOIL", HotWaterCoil): {"comment": "Heating coil"},
        ("FILTER", Filter): {"comment": "Filter"},
        ("OADPR", ElectricalActuatedProportionalDamper): {
            "comment": "Outdoor air damper"
        },
        ("MADPR", ElectricalActuatedProportionalDamper): {
            "comment": "Mixed Air Damper"
        },
        ("EADPR", ElectricalActuatedProportionalDamper): {
            "comment": "Exhaust Air Damper"
        },
    },
    "junctions": {
        ("MixedAirDuct", Junction): {
            "comment": "Mix between return air and outdoor air",
            "hasMedium": Fluid.Air,
            "fromReturnAir": AirInletConnectionPoint,
            "fromOutdoorAir": AirInletConnectionPoint,
            "toFilter": AirOutletConnectionPoint,
        },
        ("ReturnExhaustDuct", Junction): {
            "comment": "Paths for return or exhaust",
            "hasMedium": Fluid.Air,
            "fromReturn": AirInletConnectionPoint,
            "toMixedAirDamper": AirOutletConnectionPoint,
            "toExhaustDamper": AirOutletConnectionPoint,
        },
        ("SupplyAirDuct", Junction): {
            "comment": "Supply Air Duct",
            "hasMedium": Fluid.Air,
            "supplyAir": AirOutletConnectionPoint,
            "fromAHU": AirInletConnectionPoint,
        },
        ("ReturnAirDuct", Junction): {
            "comment": "Return Air Duct extracting air from open office",
            "hasMedium": Fluid.Air,
            "returnAir": AirInletConnectionPoint,
            "toReturnFan": AirOutletConnectionPoint,
        },
    },
    "relations": [
        ("self['OADPR']", ">>", "self['MixedAirDuct'].fromOutdoorAir"),
        ("self['MADPR']", ">>", "self['MixedAirDuct'].fromReturnAir"),
        ("self['MixedAirDuct']", ">>", "self['FILTER']"),
        ("self['FILTER']", ">>", "self['CLGCOIL']"),
        ("self['CLGCOIL']", ">>", "self['SF']"),
        ("self['SF']", ">>", "self['HTGCOIL']"),
        ("self['HTGCOIL']", ">>", "self['SupplyAirDuct'].fromAHU"),
        ("self['ReturnAirDuct']", ">>", "self['RF']"),
        ("self['RF']", ">>", "self['ReturnExhaustDuct'].fromReturn"),
        ("self['ReturnExhaustDuct']", ">>", "self['EADPR']"),
        ("self['ReturnExhaustDuct']", ">>", "self['MADPR']"),
        ("self['RF_VFD']", ">>", "self['RF']"),
    ],
    "boundaries": [
        "self | self['OADPR'].airInlet",
        "self | self['ReturnAirDuct'].returnAir",
        "self | self['SupplyAirDuct'].supplyAir",
        "self | self['EADPR'].airOutlet",
    ],
}

ahu = AirHandlingUnit(config=ahu_template)

clg_vlv = TwoWayActuatedProportionalValve(label="A5")
htg_vlv = TwoWayActuatedProportionalValve(label="A4")

hrv = AirHeatExchanger(label="HRV")

chiller = Chiller(label="Chiller")
chilled_water_pump = Pump(label="ChilledWaterPump")
chilled_water_pump_starter = MotorStarter(label="ChilledWaterPumpStarter")
chilled_water_pump_starter >> chilled_water_pump
boiler = ElectricalHotWaterBoiler(label="Boiler")
hot_water_pump = Pump(label="HotWaterPump")
hot_water_pump_starter = MotorStarter(label="HotWaterPumpStarter")
hot_water_pump_starter >> hot_water_pump


exhaustfan_template = {
    "cp": {
        "electricalInlet": Electricity_120VLN_1Ph_60HzInletConnectionPoint,
    },
    "params": {
        "hasRole": Role.Exhaust,
    },
}
bathroom_exhaust_fan = Fan(
    config=exhaustfan_template,
    label="ExhaustFan",
    comment="Bathroom exhaust fan",
    hasPhysicalLocation=ps.bathroom,
)
window1 = Window(
    label="Window_West",
    comment="First Window in OpenOffice, covering West portion of room",
)
window2 = Window(
    label="Window_East",
    comment="Second Window in OpenOffice, covering East portion of room",
)

vav1 = VAV(config=vav_withhotwaterreheat_template)
vav2 = VAV(config=vav_withhotwaterreheat_template)


if __name__ == "__main__":
    dump()
