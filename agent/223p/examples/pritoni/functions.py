import hvac_devices as hd
import lighting_devices as ld
import lighting_spaces as ls
from bob.core import UNIT, bind_model_namespace
from bob.functions import Function, FunctionInput, FunctionOutput
from scratch.producer.occupancy import OccupancyFunction
from bob.properties import Temperature
from bob.properties.states import Schedule

from scratch.assemblage import model_namespace

model_name, global_ns = model_namespace(__file__)
_namespace = bind_model_namespace(model_name, f"urn:{global_ns}:{model_name}/")


class Average(Function):
    """
    y = (u1 + u2) / 2.0
    """

    u1: FunctionInput
    u2: FunctionInput
    y: FunctionOutput


# line up the output to a special property
f_avg_temp = Temperature(label="DA-T-AVG", hasUnit=UNIT.DEG_C)

# make an instance
f = Average(
    label="FB-1",
    comment="Compute DA-T Avg",
    u1=hd.ahu["DA-T"].observedProperty,
    y=f_avg_temp,
)

#
#   Open Office
#

open_office_occ_control_schedule = Schedule(label="Open Office Occ Schedule")

open_office_occ_control = OccupancyFunction(
    label="Open Office Occ Control",
    comment="Occupancy sensor drives LightingZone1 and LightingZone2",
    inStatus=ld.openoffice_movement.observedProperty,
    inSchedule=open_office_occ_control_schedule,
    outStatus=ls.openofficeNorth_lightspace.occupancy,
)

#
#   Kitchenette
#

kitchenette_occ_control_schedule = Schedule(label="Kitchenette Occ Schedule")

kitchenette_occ_control = OccupancyFunction(
    label="Kitchenette Occ Control",
    comment="Occupancy sensor drives LightingZone1 and LightingZone2",
    inStatus=ld.kitchenette_movement.observedProperty,
    inSchedule=kitchenette_occ_control_schedule,
    outStatus=ls.kitchenette_lightspace.occupancy,
)

### kitchenette_occ_control.outStatus >> hs.hvac_zone_2.occupancy

#
#   Private Office
#

private_office_occ_control_schedule = Schedule(label="Private Office Occ Schedule")

private_office_occ_control = OccupancyFunction(
    label="Private Office Occ Control",
    comment="Deal with OccupancySpace3...probably not required but it's defined",
    inStatus=ld.privateoffice_movement.observedProperty,
    inSchedule=private_office_occ_control_schedule,
    outStatus=ls.privateoffice_lightspace.occupancy,
)

### private_office_occ_control.outStatus >> hs.privateoffice_hvac.occupancy

#
#   Bathroom
#

bathroom_occ_control_schedule = Schedule(label="Bathroom Occ Schedule")

bathroom_occ_control = OccupancyFunction(
    label="Bathroom Occ Control",
    comment="Light space O2",
    inStatus=ld.bathroom_movement.observedProperty,
    inSchedule=bathroom_occ_control_schedule,
    outStatus=ls.bathroom_lightspace.occupancy,
)

### bathroom_occ_control.outStatus >> hs.bathroom_hvac.occupancy

#
#   Corridor
#

corridor_occ_control_schedule = Schedule(label="Corridor Occ Schedule")

corridor_occ_control = OccupancyFunction(
    label="Corridor Occ Control",
    comment="Corridor Light space, O5",
    inStatus=ld.corridor_movement.observedProperty,
    inSchedule=corridor_occ_control_schedule,
    outStatus=ls.corridor_lightspace.occupancy,
)

### corridor_occ_control.outStatus >> hs.corridorNorth_hvac.occupancy
