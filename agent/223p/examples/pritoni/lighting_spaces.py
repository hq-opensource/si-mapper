from bob.core import bind_model_namespace, dump
from bob.properties import OccupancyStatus
from bob.space.light import LightingSpace, LightingZone

from scratch.assemblage import model_namespace

model_name, global_ns = model_namespace(__file__)
_namespace = bind_model_namespace(model_name, f"urn:{global_ns}:{model_name}/")


# Light Spaces
openofficeNorth_lightspace = LightingSpace(
    label="LightingSpace1", comment="OpenOffice North.Light"
)
openofficeNorth_lightspace.occupancy = OccupancyStatus()

openofficeSouth_lightspace = LightingSpace(
    label="LightingSpace2", comment="OpenOffice South.Light"
)
openofficeSouth_lightspace.occupancy = OccupancyStatus()

bathroom_lightspace = LightingSpace(label="LightingSpace3", comment="Bathroom.Light")
bathroom_lightspace.occupancy = OccupancyStatus()

corridor_lightspace = LightingSpace(label="LightingSpace5", comment="Corridor.Light")
corridor_lightspace.occupancy = OccupancyStatus()

privateoffice_lightspace = LightingSpace(
    label="LightingSpace4", comment="PrivateOffice.Light"
)
privateoffice_lightspace.occupancy = OccupancyStatus()

kitchenette_lightspace = LightingSpace(
    label="LightingSpace6", comment="Kitchenette.Light"
)
kitchenette_lightspace.occupancy = OccupancyStatus()

# Lighting Zones
lighting_zone_1 = LightingZone(
    label="LightingZone1",
    comment="Contains OpenOffice Space North",
    occupancy=openofficeNorth_lightspace.occupancy,
)
lighting_zone_1 > openofficeNorth_lightspace

lighting_zone_2 = LightingZone(
    label="LightingZone2",
    comment="Contains OpenOffice Space South",
    occupancy=openofficeSouth_lightspace.occupancy,
)
lighting_zone_2 > openofficeSouth_lightspace

lighting_zone_3 = LightingZone(
    label="LightingZone3",
    comment="Contains Bathroom Light Space",
    occupancy=bathroom_lightspace.occupancy,
)
lighting_zone_3 > bathroom_lightspace

lighting_zone_4 = LightingZone(
    label="LightingZone4",
    comment="Contains Private Office Light Space",
    occupancy=privateoffice_lightspace.occupancy,
)
lighting_zone_4 > privateoffice_lightspace

lighting_zone_5 = LightingZone(
    label="LightingZone5",
    comment="Contains Corridor Light Space",
    occupancy=corridor_lightspace.occupancy,
)
lighting_zone_5 > corridor_lightspace

lighting_zone_6 = LightingZone(
    label="LightingZone6",
    comment="Contains Kitchenette Light Space",
    occupancy=kitchenette_lightspace.occupancy,
)
lighting_zone_6 > kitchenette_lightspace

if __name__ == "__main__":
    dump()
