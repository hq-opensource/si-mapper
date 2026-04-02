import hvac_devices as hd
import hvac_spaces as hs
import lighting_devices as ld
import lighting_spaces as ls
import physical_spaces as ps
from bob.core import bind_model_namespace, dump

from scratch.assemblage import model_namespace

model_name, global_ns = model_namespace(__file__)
_namespace = bind_model_namespace(model_name, f"urn:{global_ns}:{model_name}/")


ld.kitchenette_luminaire_11.lightOutlet >> ld.kitch_light_conn
ld.kitchenette_luminaire_12.lightOutlet >> ld.kitch_light_conn
ld.kitch_light_conn >> ls.kitchenette_lightspace.lightInlet

# There is a occupancy space for Kitchenette... go figure
ld.kitchenette_movement % ls.kitchenette_lightspace
ld.kitchenette_movement.hasPhysicalLocation = ps.kitchenette

ld.privateoffice_luminaire_7.lightOutlet >> ld.privateoffice_light_conn
ld.privateoffice_luminaire_8.lightOutlet >> ld.privateoffice_light_conn
ld.privateoffice_light_conn >> ls.privateoffice_lightspace.lightInlet

ld.corridor_luminaire_9.lightOutlet >> ld.corridor_light_conn
ld.corridor_luminaire_10.lightOutlet >> ld.corridor_light_conn
ld.corridor_light_conn >> ls.corridor_lightspace.lightInlet

ld.corridor_movement % ls.corridor_lightspace
ld.corridor_movement.hasPhysicalLocation = ps.corridor

ld.bathroom_luminaire_5.lightOutlet >> ld.bathroom_light_conn
ld.bathroom_luminaire_6.lightOutlet >> ld.bathroom_light_conn
ld.bathroom_light_conn >> ls.bathroom_lightspace.lightInlet

ld.bathroom_movement % ls.bathroom_lightspace
ld.bathroom_movement.hasPhysicalLocation = ps.bathroom

# In SR-PD-MP Pritoni Layout, O1, LZ1, LZ2 have been modified
# and O1 overlap LZ1 and LZ2.
# Only one measurement location can be used for the movement
# sensor. If it's true that this sensor will see anything moving
# in those 2 spaces... then it would be a good idea to choose
# a space that correspond to the real coverage of the sensor.
# In this case, I would choose HVACSpace OpenOffice.
# Then Light could use the result of the function block Occupancy

ld.openofficeNorth_luminaire_1.lightOutlet >> ld.openofficeNorth_light_conn
ld.openofficeNorth_luminaire_2.lightOutlet >> ld.openofficeNorth_light_conn
ld.openofficeNorth_light_conn >> ls.openofficeNorth_lightspace.lightInlet

ld.openofficeSouth_luminaire_3.lightOutlet >> ld.openofficeSouth_light_conn
ld.openofficeSouth_luminaire_4.lightOutlet >> ld.openofficeSouth_light_conn
ld.openofficeSouth_light_conn >> ls.openofficeSouth_lightspace.lightInlet

# ld.openoffice_movement % ls.openofficeSouth_lightspace
ld.openoffice_movement % hs.openoffice_hvac
ld.openoffice_movement.hasPhysicalLocation = ps.openoffice

ld.natural_ligth_source_from_outdoor >> hd.window1.naturalLightInlet
ld.natural_ligth_source_from_outdoor >> hd.window2.naturalLightInlet
hd.window1.naturalLightOutlet >> ld.natural_ligth_conn
hd.window2.naturalLightOutlet >> ld.natural_ligth_conn
ld.natural_ligth_conn >> ls.openofficeNorth_lightspace.naturalLightInlet

# ld.daylight_sensor % ls.openofficeNorth_lightspace
# ld.daylight_sensor.hasPhysicalLocation = ps.openoffice

if __name__ == "__main__":
    dump()
