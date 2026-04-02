"""
Figure A-4
"""

from __future__ import annotations

from typing import Any
from pathlib import Path

from bob import bind_model_namespace, data_graph, schema_graph, dump

from bob.core import Junction, Equipment
from bob.equipment.hvac.fan import Fan
from bob.connections.air import (
    AirInletConnectionPoint,
    AirOutletConnectionPoint,
)
from bob.connections.water import (
    HotWaterInletConnectionPoint,
    HotWaterOutletConnectionPoint,
)

# from bob.signal import AnalogIn, AnalogOut, BinaryOut

from header import g36_header

model_name = Path(__file__).stem
__namespace__ = bind_model_namespace(
    "exg3604", f"http://data.ashrae.org/standard223/data/{model_name}#"
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


class ValvePositioner(Equipment):
    # position = AnalogOut
    pass


class HotWaterValve(Equipment):
    pass


class ECMFan(Fan):
    # airInlet: AirInletConnectionPoint
    # airOutlet: AirOutletConnectionPoint
    pass


class ECM(Equipment):
    # fanStart = BinaryOut
    # fanSpeedFeedback = AnalogIn
    # fanSpeedCommand = AnalogOut
    pass


class HotWaterCoil(Equipment):
    airInlet: AirInletConnectionPoint
    airOutlet: AirOutletConnectionPoint
    hwInlet: HotWaterInletConnectionPoint
    hwOutlet: HotWaterOutletConnectionPoint
    # valvePosition: AnalogOut

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        # create a positioner
        self.valve_positioner = ValvePositioner(label=self.label + ".damper_positioner")
        self > self.valve_positioner

        # create a hot water valve
        self.hot_water_valve = HotWaterValve(label=self.label + ".hot_water_valve")
        self > self.hot_water_valve

        # reference the properties
        # self.valvePosition = self.valve_positioner.position


class VAV(Equipment):
    supplyAirInlet: AirInletConnectionPoint
    returnAirInlet: AirInletConnectionPoint
    supplyAirOutlet: AirOutletConnectionPoint
    # supplyAirFlow: AnalogIn
    # damperPosition: AnalogOut
    hwInlet: HotWaterInletConnectionPoint
    hwOutlet: HotWaterOutletConnectionPoint
    # hwValvePosition: AnalogOut

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        # create an air flow station
        self.air_flow_station = AirFlowStation(label=self.label + ".air_flow_station")
        self > self.air_flow_station
        self.air_flow_station.airInlet.mapsTo = self.supplyAirInlet
        # self.supplyAirFlow = self.air_flow_station.flow

        # create a damper
        self.damper = Damper(label=self.label + ".damper")
        self > self.damper
        # self.damperPosition = self.damper.position

        # create a hot water coil
        self.hot_water_coil = HotWaterCoil(label=self.label + ".hot_water_coil")
        self > self.hot_water_coil
        self.hot_water_coil.hwInlet.mapsTo = self.hwInlet
        self.hot_water_coil.hwOutlet.mapsTo = self.hwOutlet
        self.hot_water_coil.airInlet.mapsTo = self.returnAirInlet
        # self.hwValvePosition = self.hot_water_coil.valvePosition

        # create a fan with an ECM part
        self.fan = ECMFan(label=self.label + ".fan")
        self.fan_ecm = ECM(label=self.label + ".fan.ecm")
        self > self.fan > self.fan_ecm
        self.hot_water_coil >> self.fan

        # merge the outlets together
        junction = Junction()
        self > junction

        self.damper.airOutlet >> junction
        self.fan.airOutlet >> junction
        junction.maps_to(self.supplyAirOutlet)


# make one
vav = VAV(label="A-4")

# dump the result
dump(
    data_graph,
    filename=f"{model_name}.data.ttl",
    header=g36_header(model_name),
)
dump(schema_graph, filename=f"{model_name}.schema.ttl")
