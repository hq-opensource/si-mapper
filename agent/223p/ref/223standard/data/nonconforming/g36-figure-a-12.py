"""
Figure A-12
"""

from __future__ import annotations

from typing import Any
from pathlib import Path

from bob import bind_model_namespace, data_graph, schema_graph, dump

from bob.core import Air, Junction, Equipment
from bob.equipment.hvac.fan import Fan
from bob.connections.air import (
    AirConnection,
    AirInletConnectionPoint,
    AirOutletConnectionPoint,
)
from bob.connections.water import (
    ChilledWaterInletConnectionPoint,
    ChilledWaterOutletConnectionPoint,
    HotWaterInletConnectionPoint,
    HotWaterOutletConnectionPoint,
)

# from bob.signal import AnalogIn, AnalogOut, BinaryOut

from header import g36_header

model_name = Path(__file__).stem
__namespace__ = bind_model_namespace(
    "exg3612", f"http://data.ashrae.org/standard223/data/{model_name}#"
)


class AirFilter(Equipment):
    airInlet: AirInletConnectionPoint
    airOutlet: AirOutletConnectionPoint
    # dp = AnalogIn


class DamperPositioner(Equipment):
    # position = AnalogOut
    pass


class Damper(Equipment):
    airInlet: AirInletConnectionPoint
    airOutlet: AirOutletConnectionPoint
    # position: AnalogOut

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        # create a positioner
        self.damper_positioner = DamperPositioner(
            label=self.label + ".damper_positioner"
        )
        self > self.damper_positioner

        # reference the connections
        # self.position = self.damper_positioner.position


class ValvePositioner(Equipment):
    # position = AnalogOut
    pass


class HotWaterValve(Equipment):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        # create a positioner
        self.valve_positioner = ValvePositioner(
            label=self.label + ".valve_positioner"
        )
        self > self.valve_positioner


class ChilledWaterValve(Equipment):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        # create a positioner
        self.valve_positioner = ValvePositioner(
            label=self.label + ".valve_positioner"
        )
        self > self.valve_positioner


class HotWaterCoil(Equipment):
    airInlet: AirInletConnectionPoint
    airOutlet: AirOutletConnectionPoint
    hwInlet: HotWaterInletConnectionPoint
    hwOutlet: HotWaterOutletConnectionPoint
    # valvePosition: AnalogOut

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        # create a hot water valve
        self.hot_water_valve = HotWaterValve(label=self.label + ".hot_water_valve")
        self > self.hot_water_valve

        # reference the properties
        # self.valvePosition = self.valve_positioner.position


class ChilledWaterCoil(Equipment):
    airInlet: AirInletConnectionPoint
    airOutlet: AirOutletConnectionPoint
    chwInlet: ChilledWaterInletConnectionPoint
    chwOutlet: ChilledWaterOutletConnectionPoint
    # valvePosition: AnalogOut

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        # create a chilled water valve
        self.chilled_water_valve = ChilledWaterValve(
            label=self.label + ".chilled_water_valve"
        )
        self > self.chilled_water_valve

        # reference the properties
        # self.valvePosition = self.valve_positioner.position


class VFD(Equipment):
    # fanStatus = BinaryIn
    # fanSpeedCommand = AnalogOut
    # fanStart = BinaryOut
    pass


class VFDFan(Fan):
    # airInlet: AirInletConnectionPoint - inherits from Fan
    # airOutlet: AirOutletConnectionPoint - inherits from Fan
    # fanStatus: BinaryIn
    # fanSpeedCommand: AnalogOut
    # fanStart: BinaryOut

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        # create a positioner
        self.variable_frequency_drive = VFD(label=self.label + ".vfd")
        self > self.variable_frequency_drive

        # reference the properties
        # self.fanStatus = self.variable_frequency_drive.fanStatus
        # self.fanSpeedCommand = self.variable_frequency_drive.fanSpeedCommand
        # self.fanStart = self.variable_frequency_drive.fanStart


class LinkedDampers(Equipment):
    outsideAirInlet: AirInletConnectionPoint
    returnAirInlet: AirInletConnectionPoint
    mixedAirOutlet: AirOutletConnectionPoint

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.outside_air_damper = Damper(label=self.label + ".outside_air_damper")
        self > self.outside_air_damper
        self.outside_air_damper.airInlet.mapsTo = self.outsideAirInlet

        self.return_air_damper = Damper(label=self.label + ".return_air_damper")
        self > self.return_air_damper
        self.return_air_damper.airInlet.mapsTo = self.returnAirInlet

        # join the outputs of the dampers
        junction = Junction()  # hasSubstance Air
        self > junction

        self.outside_air_damper >> junction
        self.return_air_damper >> junction
        junction.maps_to(self.mixedAirOutlet)


class AHU(Equipment):
    outsideAirInlet: AirInletConnectionPoint
    supplyAirOutlet: AirOutletConnectionPoint
    returnAirInlet: AirInletConnectionPoint
    exhaustAirOutlet: AirOutletConnectionPoint

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        # create the linked dampers
        self.linked_dampers = LinkedDampers(label=self.label + ".linked_dampers")
        self > self.linked_dampers
        self.linked_dampers.outsideAirInlet.mapsTo = self.outsideAirInlet

        # create an air filter
        self.air_filter = AirFilter(label=self.label + ".air_filter")
        self > self.air_filter
        self.linked_dampers.mixedAirOutlet >> self.air_filter.airInlet

        # create a hot water coil
        self.hot_water_coil = HotWaterCoil(label=self.label + ".hot_water_coil")
        self > self.hot_water_coil
        self.air_filter >> self.hot_water_coil.airInlet

        # create a chilled water coil
        self.chilled_water_coil = ChilledWaterCoil(
            label=self.label + ".chilled_water_coil"
        )
        self > self.chilled_water_coil
        self.hot_water_coil.airOutlet >> self.chilled_water_coil.airInlet

        # create a supply fan
        self.supply_fan = VFDFan(label=self.label + ".supply_fan")
        self > self.supply_fan

        self.chilled_water_coil.airOutlet >> self.supply_fan.airInlet
        self.supply_fan.airOutlet.mapsTo = self.supplyAirOutlet

        # create a return fan
        self.return_fan = VFDFan(label=self.label + ".return_fan")
        self > self.return_fan
        self.return_fan.airInlet.mapsTo = self.returnAirInlet

        # create an exhaust air damper
        self.exhaust_air_damper = Damper(label=self.label + ".exhaust_air_damper")
        self > self.exhaust_air_damper
        self.exhaust_air_damper.airOutlet.mapsTo = self.exhaustAirOutlet

        # air connection for outlet from return fan
        return_air = AirConnection(label=self.label + ".return_air")
        self.return_fan >> return_air
        return_air >> self.exhaust_air_damper
        return_air >> self.linked_dampers.returnAirInlet


# make one
vav = AHU(label="A-12")

# dump the result
dump(
    data_graph,
    filename=f"{model_name}.data.ttl",
    header=g36_header(model_name),
)
dump(schema_graph, filename=f"{model_name}.schema.ttl")
