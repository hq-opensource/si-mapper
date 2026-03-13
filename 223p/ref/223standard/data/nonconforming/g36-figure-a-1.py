"""
Figure A-1
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

# from bob.signal import AnalogIn, AnalogOut

from header import g36_header

model_name = Path(__file__).stem
_namespace = bind_model_namespace(
    "exg3601", f"http://data.ashrae.org/standard223/data/{model_name}#"
)


class AirFlowStation(Equipment):
    airInlet: AirInletConnectionPoint
    airOutlet: AirOutletConnectionPoint
    # flow = AnalogIn

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


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


class VAV(System):
    airInlet: AirInletSystemConnectionPoint
    airOutlet: AirOutletSystemConnectionPoint
    # airFlow: AnalogIn
    # damperPosition: AnalogOut

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        # create an air flow station
        self.air_flow_station = AirFlowStation(label=self.label + ".air_flow_station")
        self > self.air_flow_station

        # create a damper
        self.damper = Damper(label=self.label + ".damper")
        self > self.damper

        # link the air pieces together
        self.air_flow_station >> self.damper

        # reference the connections
        self.airInlet.mapsTo = self.air_flow_station.airInlet
        self.airOutlet.mapsTo = self.damper.airOutlet
        # self.airFlow = self.air_flow_station.flow
        # self.damperPosition = self.damper.position


# make one
vav = VAV(label="A-1")

# dump the result
dump(
    data_graph,
    filename=f"{model_name}.data.ttl",
    header=g36_header(model_name),
)
dump(schema_graph, filename=f"{model_name}.schema.ttl")
