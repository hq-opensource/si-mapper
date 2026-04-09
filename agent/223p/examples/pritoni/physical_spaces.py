from bob.core import UNIT, bind_model_namespace, dump
from bob.properties.physical import Area
from bob.space.physical import Bathroom, Building, Corridor, Floor, Office, Roof, Room

from scratch.assemblage import model_namespace

model_name, global_ns = model_namespace(__file__)
_namespace = bind_model_namespace(model_name, f"urn:{global_ns}:{model_name}/")


# Define the building Physical Spaces
bldg = Building(
    label="Pritoni Building",
    area=Area(1060, hasUnit=UNIT.FT2, label="Pritoni Building.area"),
)
roof = Roof(label="Roof of building")
floor1 = Floor(label="Floor1")
openoffice = Office(
    label="Open office", area=Area(600, hasUnit=UNIT.FT2, label="Open office.area")
)
bathroom = Bathroom(
    label="Bathroom", area=Area(75, hasUnit=UNIT.FT2, label="Bathroom.area")
)
private_office = Office(
    label="Private office",
    area=Area(150, hasUnit=UNIT.FT2, label="Private office.area"),
)
kitchenette = Room(
    label="Kitchenette", area=Area(120, hasUnit=UNIT.FT2, label="Kitchenette.area")
)
corridor = Corridor(
    label="Corridor", area=Area(115, hasUnit=UNIT.FT2, label="Corridor.area")
)

if __name__ == "__main__":
    dump()
