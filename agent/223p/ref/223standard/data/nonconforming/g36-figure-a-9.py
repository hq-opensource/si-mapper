"""
Figure A-9
"""

from __future__ import annotations

from typing import Any
from pathlib import Path

from bob import bind_model_namespace, data_graph, schema_graph, dump

from bob.core import Junction, Equipment
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

from header import g36_header

model_name = Path(__file__).stem
__namespace__ = bind_model_namespace(
    "exg3609", f"http://data.ashrae.org/standard223/data/{model_name}#"
)


class AirFlowStation(Equipment):
    airInlet: AirInletConnectionPoint
    airOutlet: AirOutletConnectionPoint
    # flow = AnalogIn


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


class Filter(Equipment):
    airInlet: AirInletConnectionPoint
    airOutlet: AirOutletConnectionPoint
    # differentialPressure = AnalogIn


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


class AHU(Equipment):
    outsideAirInlet: AirInletConnectionPoint
    supplyAirOutlet: AirOutletConnectionPoint
    returnAirInlet: AirInletConnectionPoint
    exhaustAirOutlet: AirOutletConnectionPoint

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        min_oa_damper = Damper(label=self.label + ".min_oa_damper")
        self > min_oa_damper
        economizer_oa_damper = Damper(label=self.label + ".economizer_oa_damper")
        self > economizer_oa_damper

        # split the incoming outside air
        junction = Junction()
        self > junction

        junction >> min_oa_damper.airInlet
        junction >> economizer_oa_damper.airInlet
        junction.maps_to(self.outsideAirInlet)

        outside_air_afms = AirFlowStation(label=self.label + ".outside_air_afms")
        self > outside_air_afms
        min_oa_damper >> outside_air_afms

        mixed_air = AirConnection(label=self.label + ".mixed_air")
        outside_air_afms >> mixed_air
        economizer_oa_damper >> mixed_air

        mixed_air_filter = Filter(label=self.label + ".mixed_air_filter")
        self > mixed_air_filter
        mixed_air >> mixed_air_filter.airInlet

        hot_water_coil = HotWaterCoil(label=self.label + ".hot_water_coil")
        self > hot_water_coil
        mixed_air_filter >> hot_water_coil

        chilled_water_coil = ChilledWaterCoil(label=self.label + ".chilled_water_coil")
        self > chilled_water_coil
        hot_water_coil >> chilled_water_coil

        supply_fan = Fan(label=self.label + ".supply_fan")
        self > supply_fan
        chilled_water_coil >> supply_fan
        supply_fan.airOutlet.mapsTo = self.supplyAirOutlet

        return_fan = Fan(label=self.label + ".return_fan")
        self > return_fan
        return_fan.airInlet.mapsTo = self.returnAirInlet

        # return air goes to two dampers
        return_air = AirConnection(label=self.label + ".return_air")
        return_fan >> return_air

        # make the exhaust air damper and connect it
        exhaust_air_damper = Damper(label=self.label + ".exhaust_air_damper")
        self > exhaust_air_damper
        return_air >> exhaust_air_damper

        # exhaust air damper goes outside
        exhaust_air_damper.airOutlet.mapsTo = self.exhaustAirOutlet

        # the return air damper gets its input from the return fan and goes to
        # into the mixed air
        return_air_damper = Damper(label=self.label + ".return_air_damper")
        self > return_air_damper
        return_air >> return_air_damper >> mixed_air


# make one
ahu = AHU(label="A-9")

# dump the result
dump(
    data_graph,
    filename=f"{model_name}.data.ttl",
    header=g36_header(model_name),
)
dump(schema_graph, filename=f"{model_name}.schema.ttl")
