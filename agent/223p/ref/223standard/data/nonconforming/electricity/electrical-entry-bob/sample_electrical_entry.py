from cProfile import label
from pathlib import Path
from typing import Any
from bob.equipment.electricity.meter import ThreePhaseElectricalMeter

from header import sample_header

from bob.connections.air import *
from bob.connections.electricity import *
from bob.connections.light import LightVisibleConnection
from bob.connections.occupancy import (
    OccupancyInletSystemConnectionPoint,
    OccupancyOutletSystemConnectionPoint,
)
from bob.core import P223, QUANTITYKIND, UNIT, bind_model_namespace, dump, get_datagraph
from bob.equipment.architectural import Window
from bob.equipment.electricity.distribution import (
    SinglePhaseDistributionPanel,
    SinglePoleCircuitBreaker,
    ThreePhaseDistributionPanel,
    ThreePolesCircuitBreaker,
    ThreePolesMainCircuitBreaker,
    Transformer,
    TwoPolesCircuitBreaker,
    TwoPolesMainCircuitBreaker,
)
from bob.equipment.hvac.airhandlingunit import AirHandlingUnit
from bob.equipment.hvac.coil import ChilledWaterCoil, HotWaterCoil
from bob.equipment.hvac.damper import ElectricalActuatedProportionalDamper
from bob.equipment.hvac.fan import Fan
from bob.equipment.hvac.filter import Filter
from bob.equipment.hvac.vav import VAV
from bob.equipment.lighting.light import Luminaire
from bob.property import QuantifiableObservableProperty
from bob.sensor.flow import AirFlowSensor
from bob.sensor.temperature import AirTemperatureSensor
from bob.space.hvac import HVACSpace, HVACZone
from bob.space.light import LightingSpace, LightingZone
from bob.space.physical import Bathroom, Building, Corridor, Floor, Office, Roof, Room

model_name = Path(__file__).stem
_namespace = bind_model_namespace("ex", f"urn:ex/{model_name}/")


# Define breaker in template
mainentry_panel_config = {
    "params": {
        "label": "Main Entry Panel",
        "comment": "Main Entry Panel of Building at 575V",
        "voltage": "575",
    },
    "sensors": {},
    "equipment": {
        ("MainBreaker", ThreePolesMainCircuitBreaker): {
            "comment": "Main breaker of panel",
            "amps": 400,
            "voltage": "575",
        },
        ("CB#1", SinglePoleCircuitBreaker): {
            "comment": "Lights",
            "amps": 15,
            "voltage": 347,
            "bus_bar": "A",
        },
        ("CB#2", ThreePolesCircuitBreaker): {
            "comment": "Fans, AHU",
            "amps": 40,
            "voltage": "575",
        },
        ("CB#3", ThreePolesCircuitBreaker): {
            "comment": "Feeds Transformer to get 120/240",
            "amps": 100,
            "voltage": "575",
        },
        ("CB#4", ThreePolesCircuitBreaker): {
            "comment": "Used for Meter",
            "amps": 15,
            "voltage": "575",
        },
    },
    # other properties could go there... ?
}

distribution_panel_config = {
    "params": {
        "label": "My Panel",
        "comment": "Description of my panel",
        "voltage": "120_240",
    },
    "sensors": {},
    "equipment": {
        ("MainBreaker", TwoPolesMainCircuitBreaker): {
            "comment": "Main breaker of panel",
            "amps": 200,
            "voltage": "120_240",
        },
        ("CB#1", SinglePoleCircuitBreaker): {
            "comment": "Lights",
            "amps": 15,
            "voltage": "120",
            "bus_bar": "A",
        },
        ("CB#2", TwoPolesCircuitBreaker): {
            "comment": "Heater",
            "amps": 20,
            "voltage": "240",
        },
    },
    # other properties could go there... ?
}


def test_electrical_entry():
    # Electrical Equipment

    main_panel = ThreePhaseDistributionPanel(config=mainentry_panel_config)
    transformer_120_240 = Transformer(
        label="TX-1",
        electricalInlet=Electricity_575V_60HzInletConnectionPoint,
        electricalOutlet=Electricity_120V_240V_60HzOutletConnectionPoint,
    )

    dist_panel = SinglePhaseDistributionPanel(config=distribution_panel_config)
    # hq = Electricity_120V_240V_60HzConnection(label='Hydro-Québec', comment="That would be for a home...")
    hq_600 = Electricity_575V_60HzConnection(label="Hydro-Québec", comment="600V")
    hq_600 >> main_panel["MainBreaker"]
    main_panel["CB#3"] >> transformer_120_240 >> dist_panel["MainBreaker"]

    building_electrical_meter = ThreePhaseElectricalMeter(
        label="Building Meter",
        comment="Building Electrical Meter (M3)",
        medium=Electricity.AC575V_60Hz,
    )
    # building_electrical_meter.hasPhysicalLocation = ps.bldg
    building_electrical_meter.set_voltage_measurement_location(main_panel["CB#4"])
    building_electrical_meter.set_current_measurement_location(
        main_panel["MainBreaker"].electricalInlet
    )


if __name__ == "__main__":
    r = test_electrical_entry()
    dump(filename=f"samples/ttl/{model_name}.ttl", header=sample_header(model_name))
