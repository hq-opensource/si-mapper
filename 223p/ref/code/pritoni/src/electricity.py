import electrical_devices as ed
import hvac_devices as hd
import lighting_devices as ld
import network_devices as nd
import physical_spaces as ps
from bob.core import bind_model_namespace, dump

from scratch.assemblage import model_namespace

model_name, global_ns = model_namespace(__file__)
_namespace = bind_model_namespace(model_name, f"urn:{global_ns}:{model_name}/")


# Make Electrical connections
ed.main_panel["CB#2"] >> hd.ahu["SF_Starter"].electricalInlet
ed.main_panel["CB#4"] >> hd.ahu["RF_VFD"].electricalInlet
ed.main_panel["CB#6"] >> hd.chiller.electricalInlet
ed.main_panel["CB#7"] >> hd.boiler.electricalInlet
ed.main_panel["CB#8"] >> hd.hot_water_pump_starter.electricalInlet
ed.main_panel["CB#9"] >> hd.chilled_water_pump_starter.electricalInlet

ed.dist_panel_cb1 >> [
    ed.openofficeNorth_luminaire_1_dimmer,
    ld.openofficeNorth_luminaire_2,
    ld.openofficeSouth_luminaire_3,
    ld.openofficeSouth_luminaire_4,
]
(
    ed.openofficeNorth_luminaire_1_dimmer.electricalOutlet
    >> ld.openofficeNorth_luminaire_1.electricalInlet
)

ed.dist_panel_cb3 >> [
    ld.kitchenette_luminaire_11,
    ld.kitchenette_luminaire_12,
]

ed.dist_panel_cb4 >> [
    ld.bathroom_luminaire_5,
    ld.bathroom_luminaire_6,
    ld.corridor_luminaire_9,
    ld.corridor_luminaire_10,
]

ed.dist_panel_cb5 >> [
    ld.privateoffice_luminaire_7,
    ld.privateoffice_luminaire_8,
]

ed.dist_panel_cb6 >> ed.bathroom_timer_switch >> hd.bathroom_exhaust_fan.electricalInlet

ed.dist_panel_cb7 >> nd.ethernet_switch.electricalInlet
ed.dist_panel_cb7 >> nd.firewall.electricalInlet


ed.return_fan_electrical_meter.hasPhysicalLocation = ps.bldg
ed.return_fan_electrical_meter.set_measurement_location(hd.ahu["RF"].electricalInlet)

ed.supply_fan_electrical_meter.hasPhysicalLocation = ps.bldg
ed.supply_fan_electrical_meter.set_measurement_location(hd.ahu["SF"].electricalInlet)

ed.building_electrical_meter.hasPhysicalLocation = ps.bldg
ed.building_electrical_meter.set_voltage_measurement_location(ed.main_panel["CB#5"])
ed.building_electrical_meter.set_current_measurement_location(
    ed.main_panel["MainBreaker"].electricalInlet
)


if __name__ == "__main__":
    dump()
