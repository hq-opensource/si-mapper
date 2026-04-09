import hvac_devices as hd
import hvac_spaces as hs
import physical_spaces as ps
from bob.connections.air import AirConnection
from bob.core import bind_model_namespace, dump
from bob.properties.states import OnOffCommand, OnOffStatus

from scratch.assemblage import model_namespace

model_name, global_ns = model_namespace(__file__)
_namespace = bind_model_namespace(model_name, f"urn:{global_ns}:{model_name}/")


# Comment
"""
Now looking at the plan, we miss a detail regarding air movement. How is the return air
dealt with ?

A single return in the open office ? In this case, air will be forced through doors up 
to the open office... 

Return grills in each room open on a big plenum covering the entire floor ?

Most probably, the bathroom doesn't have a return grill... just an exhaust... but again,
we miss this information.

Both scenarios are possible and they will endup being modeled differently

Based on what we have here, it's impossible to know exactly.

Knowing that, I'll still try to connect the HVAC Spaces to get the more probably air flow

"""
corridorNorth_doors = AirConnection(
    label="CorridorNorthDoors",
    comment="There are 3 doors in this space, so I'm using a connection to model those relationships",
)
# My model of spaces include 1 input for doors, 1 input for Windows, etc... if there are multiple of those, use a connection.
hs.kitchenette_hvac.doors >> hs.corridorSouth_hvac.doors
hs.corridorSouth_hvac.airTransfer >> hs.corridorNorth_hvac.airTransfer
hs.corridorNorth_hvac.doors >> corridorNorth_doors
hs.privateoffice_hvac.doors >> corridorNorth_doors
hs.bathroom_hvac.doors >> corridorNorth_doors
hs.openoffice_hvac.doors >> corridorNorth_doors

outdoor = AirConnection(
    label="Outdoor",
    comment="This is where we exhaust air of bathroom, and windows of OpenOffice are connected here to",
)
plenum = AirConnection(
    label="Plenum",
    comment="Plenum. It's where Duct Static Pressure Low port is connected",
)
openoffice_windows = AirConnection(
    label="OpenOfficeWindows",
    comment="There are 2 windows connected to the space, so I use a connection",
)
# AHU
outdoor >> hd.hrv.supplyAirInlet
hd.hrv.supplyAirOutlet >> hd.ahu["OADPR"].airInlet
hs.openoffice_hvac.ductAirOutlet >> hd.ahu['ReturnAirDuct'].returnAir
hd.ahu["EADPR"].airOutlet >> hd.hrv.exhaustAirInlet
hd.hrv.exhaustAirOutlet >> outdoor

# AHU Sensors
hd.ahu["OA-T"] % outdoor
hd.ahu["TPD1"] % (hd.ahu["FILTER"].airInlet, hd.ahu["FILTER"].airOutlet)
hd.ahu["MA-T"] % hd.ahu["FILTER"].airInlet

hd.ahu["HC-T"] % hd.ahu["HTGCOIL"].airOutlet
hd.ahu["DA-T"] % hd.ahu["SF"].airOutlet
hd.ahu["RA-T"] % hd.ahu["MADPR"].airInlet
hd.ahu["TPD2"] % (hd.ahu["SF"].airOutlet, plenum)

hd.ahu["TPD3"] % (hd.ahu["RF"].airOutlet, plenum)

hd.ahu["RF_VFD"].drive_running = OnOffStatus(label="VFD DriveRunning")
hd.ahu["RF_VFD"].run_command = OnOffCommand(label="Run Command")

hd.boiler.hotWaterLeaving >> hd.hot_water_pump.fluidInlet
hd.hot_water_pump.fluidOutlet >> hd.ahu["HTGCOIL"].hotWaterInlet

hd.ahu["HTGCOIL"].hotWaterOutlet >> hd.htg_vlv["valve"].fluidInlet
hd.htg_vlv['valve'].fluidOutlet >> hd.boiler.hotWaterEntering

hd.chiller.chilledWaterLeaving >> hd.chilled_water_pump.fluidInlet
hd.chilled_water_pump.fluidOutlet >> hd.ahu["CLGCOIL"].chilledWaterInlet
hd.ahu["CLGCOIL"].chilledWaterOutlet >> hd.clg_vlv["valve"].fluidInlet
hd.clg_vlv["valve"].fluidOutlet >> hd.chiller.chilledWaterEntering


# Windows
#hd.window1 >> outdoor
#hd.window1 >> openoffice_windows
hd.window1.hasPhysicalLocation = ps.openoffice

#hd.window2 >> outdoor
#hd.window2 >> openoffice_windows
hd.window2.hasPhysicalLocation = ps.openoffice
openoffice_windows >> hs.openoffice_hvac.windows

# Exhaust Fan
hd.bathroom_exhaust_fan.airInlet << hs.bathroom_hvac.ductAirOutlet
hd.bathroom_exhaust_fan.airOutlet >> outdoor


# VAV Boxes
# Relationships between Equipment and positioning sensors
supply_connection = AirConnection(
    label="SupplyAirDuct",
    comment="Supply Air Duct from AHU to VAV Boxes",
)
hd.ahu['SupplyAirDuct'].supplyAir >> supply_connection
supply_connection >> hd.vav1["DPR"].airInlet
hd.vav1.hasPhysicalLocation = ps.private_office

# vav1 >> hs.hvac_zone_1
hd.vav1["REHEAT"].airOutlet >> hs.privateoffice_hvac.ductAirInlet
hd.vav1["ZN-T"] % hs.openoffice_hvac
hd.vav1["ZN-T"].hasPhysicalLocation = ps.openoffice


supply_connection >> hd.vav2["DPR"].airInlet
hd.vav2.hasPhysicalLocation = ps.kitchenette

# vav2 >> hs.hvac_zone_2
hd.vav2["REHEAT"].airOutlet >> hs.kitchenette_hvac.ductAirInlet
hd.vav2["ZN-T"] % hs.corridorSouth_hvac
hd.vav2["ZN-T"].hasPhysicalLocation = ps.corridor

hs.hvac_zone_1.airInlet.mapsTo = hs.privateoffice_hvac.ductAirInlet
hs.hvac_zone_1.airOutlet.mapsTo = hs.openoffice_hvac.ductAirOutlet

hs.hvac_zone_2.airInlet.mapsTo = hs.kitchenette_hvac.ductAirInlet
hs.hvac_zone_2.airOutlet.mapsTo = hs.corridorSouth_hvac.airTransfer

# hd.vav1.airInlet.mapsTo = hd.vav1["VAV1_damper"].airInlet
# hd.vav1.airOutlet.mapsTo = hd.vav1["VAV1_HeatingCoil"].airOutlet
# hd.vav2.airInlet.mapsTo = hd.vav2["VAV2_damper"].airInlet
# hd.vav2.airOutlet.mapsTo = hd.vav2["VAV2_HeatingCoil"].airOutlet

hd.ahu.outsideAirInlet = hd.ahu["OADPR"].airInlet
hd.ahu.returnAirInlet = hd.ahu["MADPR"].airInlet
hd.ahu.supplyAirOutlet = hd.ahu["SF"].airOutlet
hd.ahu.exhaustAirOutlet = hd.ahu["EADPR"].airOutlet
hd.ahu.electricalInlet = hd.ahu["SF_Starter"].electricalInlet

if __name__ == "__main__":
    dump()
