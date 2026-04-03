from bob.connections.electricity import (
    Electricity_120VLN_1Ph_60HzConnection,
    Electricity_240VLL_120VLN_1Ph_60HzOutletConnectionPoint,
    Electricity_600VLL_3Ph_60HzConnection,
    Electricity_600VLL_3Ph_60HzInletConnectionPoint,
)
from bob.core import bind_model_namespace, dump
from bob.enum import Electricity
from scratch.electricity.distribution import (
    SinglePhaseDistributionPanel,
    SinglePoleCircuitBreaker,
    ThreePhaseDistributionPanel,
    ThreePolesCircuitBreaker,
    ThreePolesMainCircuitBreaker,
    TwoPolesCircuitBreaker,
    TwoPolesMainCircuitBreaker,
)
from bob.equipment.electricity.distribution import Transformer
from scratch.electricity.meter import ThreePhaseElectricalMeter
from scratch.electricity.switch import DimmableSwitch, TimerSwitch

from scratch.assemblage import model_namespace

model_name, global_ns = model_namespace(__file__)
_namespace = bind_model_namespace(model_name, f"urn:{global_ns}:{model_name}/")


mainentry_panel_config = {
    "params": {
        "label": "Main Entry Panel",
        "comment": "Main Entry Panel of Building at 600V_3Ph",
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
            "comment": "Parking Lot Lights",
            "amps": 15,
            "voltage": 347,
            "bus_bar": "A",
        },
        ("CB#2", ThreePolesCircuitBreaker): {
            "comment": "Supply Fans, AHU",
            "amps": 40,
            "voltage": "575",
        },
        ("CB#3", ThreePolesCircuitBreaker): {
            "comment": "Feeds Transformer to get 120/240",
            "amps": 100,
            "voltage": "575",
        },
        ("CB#4", ThreePolesCircuitBreaker): {
            "comment": "Return Fans, AHU",
            "amps": 40,
            "voltage": "575",
        },
        ("CB#5", ThreePolesCircuitBreaker): {
            "comment": "Building Meter Voltage Measurement Breaker",
            "amps": 15,
            "voltage": "575",
        },
        ("CB#6", ThreePolesCircuitBreaker): {
            "comment": "Chiller",
            "amps": 40,
            "voltage": "575",
        },
        ("CB#7", ThreePolesCircuitBreaker): {
            "comment": "Boiler",
            "amps": 100,
            "voltage": "575",
        },
        ("CB#8", ThreePolesCircuitBreaker): {
            "comment": "HotWaterPump",
            "amps": 20,
            "voltage": "575",
        },
        ("CB#9", ThreePolesCircuitBreaker): {
            "comment": "ChilledWaterPump",
            "amps": 20,
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
            "comment": "Lights in OpenOffice",
            "amps": 15,
            "voltage": "120",
            "bus_bar": "A",
        },
        ("CB#2", TwoPolesCircuitBreaker): {
            "comment": "Heater",
            "amps": 20,
            "voltage": "240",
        },
        ("CB#3", SinglePoleCircuitBreaker): {
            "comment": "Lights in Kitchenette",
            "amps": 15,
            "voltage": "120",
            "bus_bar": "A",
        },
        ("CB#4", SinglePoleCircuitBreaker): {
            "comment": "Lights in Corridors + bathroom",
            "amps": 15,
            "voltage": "120",
            "bus_bar": "A",
        },
        ("CB#5", SinglePoleCircuitBreaker): {
            "comment": "Lights in Private Office",
            "amps": 15,
            "voltage": "120",
            "bus_bar": "A",
        },
        ("CB#6", SinglePoleCircuitBreaker): {
            "comment": "Bathroom Fan",
            "amps": 15,
            "voltage": "120",
            "bus_bar": "B",
        },
        ("CB#7", SinglePoleCircuitBreaker): {
            "comment": "IT Room",
            "amps": 15,
            "voltage": "120",
            "bus_bar": "B",
        },
    },
    # other properties could go there... ?
}
# Electrical Equipment
main_panel = ThreePhaseDistributionPanel(config=mainentry_panel_config)
transformer_120_240 = Transformer(
    label="TX-1",
    electricalInlet=Electricity_600VLL_3Ph_60HzInletConnectionPoint,
    electricalOutlet=Electricity_240VLL_120VLN_1Ph_60HzOutletConnectionPoint,
)

dist_panel = SinglePhaseDistributionPanel(config=distribution_panel_config)
# hq = Electricity_240VLL_120VLN_1Ph_60HzConnection(label='Hydro-Québec', comment="That would be for a home...")
hq_600 = Electricity_600VLL_3Ph_60HzConnection(label="Hydro-Québec", comment="600V")
hq_600 >> main_panel["MainBreaker"]
main_panel["CB#3"] >> transformer_120_240 >> dist_panel["MainBreaker"]


# We need a trough so light breakers will be connected to multiple loads
dist_panel_cb1 = Electricity_120VLN_1Ph_60HzConnection(label="DISTPANEL-CB1")
dist_panel_cb3 = Electricity_120VLN_1Ph_60HzConnection(label="DISTPANEL-CB3")
dist_panel_cb4 = Electricity_120VLN_1Ph_60HzConnection(label="DISTPANEL-CB4")
dist_panel_cb5 = Electricity_120VLN_1Ph_60HzConnection(label="DISTPANEL-CB5")
dist_panel_cb6 = Electricity_120VLN_1Ph_60HzConnection(label="DISTPANEL-CB6")
dist_panel_cb7 = Electricity_120VLN_1Ph_60HzConnection(label="DISTPANEL-CB7")
dist_panel["CB#1"] >> dist_panel_cb1
dist_panel["CB#3"] >> dist_panel_cb3
dist_panel["CB#4"] >> dist_panel_cb4
dist_panel["CB#5"] >> dist_panel_cb5
dist_panel["CB#6"] >> dist_panel_cb6
dist_panel["CB#7"] >> dist_panel_cb7

bathroom_timer_switch = TimerSwitch(label="Bathroom Timer Switch", voltage=120, delay=2)

openofficeNorth_luminaire_1_dimmer = DimmableSwitch(
    label="Dimmer1", comment="Dimmable Switch Luminaire 1", voltage=120
)

return_fan_electrical_meter = ThreePhaseElectricalMeter(
    label="RF Meter",
    comment="Return Fan Electrical Meter (M1)",
    medium=Electricity.AC600VLL_3Ph_60Hz,
)

supply_fan_electrical_meter = ThreePhaseElectricalMeter(
    label="SF Meter",
    comment="Supply Fan Electrical Meter (M2)",
    medium=Electricity.AC600VLL_3Ph_60Hz,
)

building_electrical_meter = ThreePhaseElectricalMeter(
    label="Building Meter",
    comment="Building Electrical Meter (M3)",
    medium=Electricity.AC600VLL_3Ph_60Hz,
)

if __name__ == "__main__":
    dump()
