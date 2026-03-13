from bob.core import bind_model_namespace, dump
from bob.space.hvac import HVACSpace, HVACZone, OccupancyStatus

from scratch.assemblage import model_namespace

model_name, global_ns = model_namespace(__file__)
_namespace = bind_model_namespace(model_name, f"urn:{global_ns}:{model_name}/")

# HVAC Spaces
openoffice_hvac = HVACSpace(
    label="HVACSpace1", comment="OpenOffice.HVAC", occupancy=OccupancyStatus()
)
bathroom_hvac = HVACSpace(
    label="HVACSpace2", comment="Bathroom.HVAC", occupancy=OccupancyStatus()
)
corridorNorth_hvac = HVACSpace(
    label="HVACSpace4", comment="CorridorNorth.HVAC", occupancy=OccupancyStatus()
)
corridorSouth_hvac = HVACSpace(
    label="HVACSpace5", comment="CorridorSouth.HVAC", occupancy=OccupancyStatus()
)
privateoffice_hvac = HVACSpace(
    label="HVACSpace3", comment="PrivateOffice.HVAC", occupancy=OccupancyStatus()
)
kitchenette_hvac = HVACSpace(
    label="HVACSpace6", comment="Kitchenette.HVAC", occupancy=OccupancyStatus()
)

# HVAC Zones
hvac_zone_1 = HVACZone(
    label="HVACZone1",
    comment="HVAC Zone 1 contains open office, bathroom, private office and corridor north",
    occupancy=OccupancyStatus(),
)
hvac_zone_1 > openoffice_hvac
hvac_zone_1 > bathroom_hvac
hvac_zone_1 > corridorNorth_hvac
hvac_zone_1 > privateoffice_hvac
# hvac_zone_1.airInlet.mapsTo = privateoffice_hvac.ductAirInlet
# hvac_zone_1.airOutlet.mapsTo = openoffice_hvac.ductAirOutlet

hvac_zone_2 = HVACZone(
    label="HVACZone2",
    comment="HVAC Zone 2 contains Kitchenette and Corridor South",
    occupancy=OccupancyStatus(),
)
hvac_zone_2 > kitchenette_hvac
hvac_zone_2 > corridorSouth_hvac
# hvac_zone_2.airInlet.mapsTo = kitchenette_hvac.ductAirInlet
# hvac_zone_2.airOutlet.mapsTo = corridorSouth_hvac.ductAirOutlet

if __name__ == "__main__":
    dump()
