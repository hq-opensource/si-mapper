"""
Figure A-2
"""

from __future__ import annotations

from typing import Any
from pathlib import Path

from bob import bind_model_namespace, data_graph, schema_graph, dump

from bob.core import System, Equipment
from bob.connections.air import (
    AirInletConnectionPoint,
    AirInletSystemConnectionPoint,
    AirOutletConnectionPoint,
    AirOutletSystemConnectionPoint,
)
from bob.connections.water import (
    HotWaterInletConnectionPoint,
    HotWaterInletSystemConnectionPoint,
    HotWaterOutletConnectionPoint,
    HotWaterOutletSystemConnectionPoint,
)

# from bob.signal import AnalogIn, AnalogOut

from header import g36_header

model_name = Path(__file__).stem
__namespace__ = bind_model_namespace(
    "exg3602", f"http://data.ashrae.org/standard223/data/{model_name}#"
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


class VAV(System):
    airInlet: AirInletSystemConnectionPoint
    airOutlet: AirOutletSystemConnectionPoint
    # airFlow: AnalogIn
    # damperPosition: AnalogOut
    hwInlet: HotWaterInletSystemConnectionPoint
    hwOutlet: HotWaterOutletSystemConnectionPoint
    # valvePosition: AnalogOut

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        # create an air flow station
        self.air_flow_station = AirFlowStation(label=self.label + ".air_flow_station")
        self > self.air_flow_station

        # create a damper
        self.damper = Damper(label=self.label + ".damper")
        self > self.damper

        # create a hot water coil
        self.hot_water_coil = HotWaterCoil(label=self.label + ".hot_water_coil")
        self > self.hot_water_coil

        # link the air pieces together
        self.air_flow_station >> self.damper
        self.damper >> self.hot_water_coil

        # reference the connections
        self.airInlet.mapsTo = self.air_flow_station.airInlet
        self.airOutlet.mapsTo = self.hot_water_coil.airOutlet
        # self.airFlow = self.air_flow_station.flow
        # self.damperPosition = self.damper.position

        self.hwInlet.mapsTo = self.hot_water_coil.hwInlet
        self.hwOutlet.mapsTo = self.hot_water_coil.hwOutlet
        # self.valvePosition = self.hot_water_coil.valvePosition


# make one
vav = VAV(label="A-2")

# dump the result
dump(
    data_graph,
    filename=f"{model_name}.data.ttl",
    header=g36_header(model_name),
)
dump(schema_graph, filename=f"{model_name}.schema.ttl")
