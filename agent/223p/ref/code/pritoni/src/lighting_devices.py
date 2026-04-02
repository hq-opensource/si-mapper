import lighting_spaces as ls
import physical_spaces as ps
from bob.connections.electricity import Electricity_120VLN_1Ph_60HzInletConnectionPoint
from bob.connections.light import LightVisibleConnection
from bob.core import UNIT, bind_model_namespace, dump
from bob.equipment.lighting.light import Luminaire
from bob.properties.electricity import ElectricPower
from bob.properties.ratio import PercentCommand
from bob.properties.states import OnOffCommand, OnOffStatus
from bob.sensor.motion import OccupantMotionSensor

from scratch.assemblage import model_namespace

model_name, global_ns = model_namespace(__file__)
_namespace = bind_model_namespace(model_name, f"urn:{global_ns}:{model_name}/")


# Now we build lights for Kitchenette
kitchenette_luminaire_11 = Luminaire(
    label="Luminaire11",
    comment="Luminaire in kitchenette #11",
    hasPhysicalLocation=ps.kitchenette,
    electricalInlet=Electricity_120VLN_1Ph_60HzInletConnectionPoint,
    electricalPower=ElectricPower(15, hasUnit=UNIT.W),
    onOffStatus=OnOffStatus(),
    onOffCommand=OnOffCommand(),
)
kitchenette_luminaire_12 = Luminaire(
    label="Luminaire12",
    comment="Luminaire in kitchenette #12",
    hasPhysicalLocation=ps.kitchenette,
    electricalInlet=Electricity_120VLN_1Ph_60HzInletConnectionPoint,
    electricalPower=ElectricPower(15, hasUnit=UNIT.W),
    onOffStatus=OnOffStatus(),
    onOffCommand=OnOffCommand(),
)
kitchenette_movement = OccupantMotionSensor(
    label="O4",
    comment="Occupancy sensor for kitchenette luminaires 11 & 12 (O4)",
)
kitch_light_conn = LightVisibleConnection(
    label="LightHub_11_12", comment="Needed to connect multiple luminaires to space"
)


# Now we build lights for Private Office
privateoffice_luminaire_7 = Luminaire(
    label="Luminaire7",
    comment="Luminaire #7 in Private Office",
    hasPhysicalLocation=ps.private_office,
    onOffStatus=OnOffStatus(),
    onOffCommand=OnOffCommand(),
    electricalInlet=Electricity_120VLN_1Ph_60HzInletConnectionPoint,
    electricalPower=ElectricPower(20, hasUnit=UNIT.W),
)
privateoffice_luminaire_8 = Luminaire(
    label="Luminaire8",
    comment="Luminaire #8 in Private Office",
    hasPhysicalLocation=ps.private_office,
    onOffStatus=OnOffStatus(),
    onOffCommand=OnOffCommand(),
    electricalInlet=Electricity_120VLN_1Ph_60HzInletConnectionPoint,
    electricalPower=ElectricPower(20, hasUnit=UNIT.W),
)
privateoffice_movement = OccupantMotionSensor(
    label="O3",
    comment="Occupancy sensor for Private Office (O3)",
    hasPhysicalLocation=ps.private_office,
)
privateoffice_movement % ls.privateoffice_lightspace
privateoffice_light_conn = LightVisibleConnection(
    label="LightHub_7_8", comment="Needed to connect multiple luminaires to space"
)


# privateoffice_movement % privateoffice_lightspace
# privateoffice_movement.hasPhysicalLocation = private_office

# Now we build lights for Corridor
corridor_luminaire_9 = Luminaire(
    label="Luminaire9",
    comment="Luminaire #9 in Corridor",
    hasPhysicalLocation=ps.corridor,
    onOffStatus=OnOffStatus(),
    onOffCommand=OnOffCommand(),
    electricalInlet=Electricity_120VLN_1Ph_60HzInletConnectionPoint,
    electricalPower=ElectricPower(15, hasUnit=UNIT.W),
)
corridor_luminaire_10 = Luminaire(
    label="Luminaire10",
    comment="Luminaire #10 in Corridor",
    hasPhysicalLocation=ps.corridor,
    onOffStatus=OnOffStatus(),
    onOffCommand=OnOffCommand(),
    electricalInlet=Electricity_120VLN_1Ph_60HzInletConnectionPoint,
    electricalPower=ElectricPower(15, hasUnit=UNIT.W),
)
corridor_movement = OccupantMotionSensor(
    label="O5",
    comment="Occupancy sensor for Corridor (O5)",
)
corridor_light_conn = LightVisibleConnection(
    label="LightHub_9_10", comment="Needed to connect multiple luminaires to space"
)


# Now we build lights for Bathroom
bathroom_luminaire_5 = Luminaire(
    label="Luminaire5",
    comment="Luminaire #5 in Bathroom",
    hasPhysicalLocation=ps.bathroom,
    onOffStatus=OnOffStatus(),
    onOffCommand=OnOffCommand(),
    electricalInlet=Electricity_120VLN_1Ph_60HzInletConnectionPoint,
    electricalPower=ElectricPower(10, hasUnit=UNIT.W),
)
bathroom_luminaire_6 = Luminaire(
    label="Luminaire6",
    comment="Luminaire #6 in Bathroom",
    hasPhysicalLocation=ps.bathroom,
    onOffStatus=OnOffStatus(),
    onOffCommand=OnOffCommand(),
    electricalInlet=Electricity_120VLN_1Ph_60HzInletConnectionPoint,
    electricalPower=ElectricPower(10, hasUnit=UNIT.W),
)
bathroom_light_conn = LightVisibleConnection(
    label="LightHub_5_6", comment="Needed to connect multiple luminaires to space"
)
bathroom_movement = OccupantMotionSensor(
    label="O2",
    comment="Occupancy sensor for Bathroom (O2)",
)


# Now we build lights for OpenOffice East


openofficeNorth_luminaire_1 = Luminaire(
    label="Luminaire1",
    comment="Luminaire #1 in OpenOffice North",
    hasPhysicalLocation=ps.openoffice,
    brightnessRatio=PercentCommand(),
    onOffStatus=OnOffStatus(),
    onOffCommand=OnOffCommand(),
    electricalInlet=Electricity_120VLN_1Ph_60HzInletConnectionPoint,
    electricalPower=ElectricPower(40, hasUnit=UNIT.W),
)
openofficeNorth_luminaire_2 = Luminaire(
    label="Luminaire2",
    comment="Luminaire #2 in OpenOffice North",
    hasPhysicalLocation=ps.openoffice,
    onOffStatus=OnOffStatus(),
    onOffCommand=OnOffCommand(),
    electricalInlet=Electricity_120VLN_1Ph_60HzInletConnectionPoint,
    electricalPower=ElectricPower(40, hasUnit=UNIT.W),
)
openofficeSouth_luminaire_3 = Luminaire(
    label="Luminaire3",
    comment="Luminaire #3 in OpenOffice South",
    hasPhysicalLocation=ps.openoffice,
    onOffStatus=OnOffStatus(),
    onOffCommand=OnOffCommand(),
    electricalInlet=Electricity_120VLN_1Ph_60HzInletConnectionPoint,
    electricalPower=ElectricPower(40, hasUnit=UNIT.W),
)
openofficeSouth_luminaire_4 = Luminaire(
    label="Luminaire4",
    comment="Luminaire #4 in OpenOffice South",
    hasPhysicalLocation=ps.openoffice,
    onOffStatus=OnOffStatus(),
    onOffCommand=OnOffCommand(),
    electricalInlet=Electricity_120VLN_1Ph_60HzInletConnectionPoint,
    electricalPower=ElectricPower(40, hasUnit=UNIT.W),
)
openofficeNorth_light_conn = LightVisibleConnection(
    label="LightHub_1_2", comment="Needed to connect multiple luminaires to space"
)
openofficeSouth_light_conn = LightVisibleConnection(
    label="LightHub_3_4", comment="Needed to connect multiple luminaires to space"
)

# Occupancy in OpenOffice comes from 1 sensors for both spaces
openoffice_movement = OccupantMotionSensor(
    label="O1",
    comment="Occupancy sensor for OpenOffice (O1)",
)

# daylight_sensor = DaylightSensor(
#    label="D1", comment="Daylight sensor installed in open office (D1)"
# )

# Windows are good for natural light
natural_ligth_source_from_outdoor = LightVisibleConnection(
    label="Natural Light comes from outside",
    comment="2 windows contribute and light is brought to 2 light spaces",
)
natural_ligth_conn = LightVisibleConnection(
    label="LightHub_NaturalLight",
    comment="2 windows contribute and light is brought to 2 light spaces",
)

if __name__ == "__main__":
    dump()
