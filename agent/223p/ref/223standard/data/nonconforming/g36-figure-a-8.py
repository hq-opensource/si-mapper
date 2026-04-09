"""
Figure A-8
"""

from __future__ import annotations

from typing import Any
from pathlib import Path

from bob import bind_model_namespace, data_graph, schema_graph, dump

from bob.core import Equipment
from bob.connections.air import (
    AirConnection,
    AirInletConnectionPoint,
    AirOutletConnectionPoint,
)

# from bob.signal import AnalogIn, AnalogOut, BinaryOut

from header import g36_header

model_name = Path(__file__).stem
__namespace__ = bind_model_namespace(
    "exg3608", f"http://data.ashrae.org/standard223/data/{model_name}#"
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


class VAV(Equipment):
    hotDeckAirInlet: AirInletConnectionPoint
    coldDeckAirInlet: AirInletConnectionPoint
    supplyAirOutlet: AirOutletConnectionPoint
    # supplyAirFlow: AnalogIn
    # hotDeckDamperPosition: AnalogOut
    # coldDeckDamperPosition: AnalogOut

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        # create a hot deck damper
        self.hot_deck_damper = Damper(label=self.label + ".hot_deck_damper")
        self > self.hot_deck_damper
        self.hot_deck_damper.airInlet.mapsTo = self.hotDeckAirInlet
        # self.hotDeckDamperPosition = self.hot_deck_damper.position

        # create a cold deck damper
        self.cold_deck_damper = Damper(label=self.label + ".cold_deck_damper")
        self > self.cold_deck_damper
        self.cold_deck_damper.airInlet.mapsTo = self.coldDeckAirInlet
        # self.coldDeckDamperPosition = self.cold_deck_damper.position

        # create an air flow station
        self.air_flow_station = AirFlowStation(label=self.label + ".air_flow_station")
        self > self.air_flow_station
        # self.supplyAirFlow = self.air_flow_station.flow

        # connection for merge
        merged_air = AirConnection(label=self.label + ".merge")

        # link the air pieces together
        self.hot_deck_damper.airOutlet >> merged_air
        self.cold_deck_damper.airOutlet >> merged_air
        merged_air >> self.air_flow_station.airInlet

        # supply air outlet comes from the air flow station
        self.air_flow_station.airOutlet.mapsTo = self.supplyAirOutlet


# make one
vav = VAV(label="A-8")

# dump the result
dump(
    data_graph,
    filename=f"{model_name}.data.ttl",
    header=g36_header(model_name),
)
dump(schema_graph, filename=f"{model_name}.schema.ttl")
