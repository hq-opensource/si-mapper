from pathlib import Path

from bob.core import bind_model_namespace

from scratch.assemblage import create_data_and_schema_ttl, model_namespace
from scratch.header import sample_header

import physical_spaces as ps  # isort: skip  # noqa: F401
import hvac_devices as hd  # isort: skip  # noqa: F401
import hvac_spaces as hs  # isort: skip  # noqa: F401
import hvac  # isort: skip  # noqa: F401
import lighting_spaces as ls  # isort: skip  # noqa: F401
import lighting_devices as ld  # isort: skip  # noqa: F401
import lighting  # isort: skip  # noqa: F401
import network_devices as nd  # isort: skip  # noqa: F401
import electrical_devices as ed  # isort: skip  # noqa: F401
import electricity  # isort: skip  # noqa: F401

#import functions  # isort: skip  # noqa: F401
import bacnet_references  # isort: skip  # noqa: F401
import fake_values  # isort: skip  # noqa: F401


model_name, global_ns = model_namespace(__file__)
_namespace = bind_model_namespace(model_name, f"urn:{global_ns}:{model_name}/")

# Relations between Physical spaces and Domain spaces
ps.bldg > ps.roof
ps.bldg > ps.floor1
ps.floor1 > ps.openoffice > hs.openoffice_hvac
ps.openoffice > ls.openofficeNorth_lightspace
ps.openoffice > ls.openofficeSouth_lightspace

ps.floor1 > ps.bathroom > hs.bathroom_hvac
ps.bathroom > ls.bathroom_lightspace

ps.floor1 > ps.corridor > hs.corridorNorth_hvac
ps.corridor > hs.corridorSouth_hvac
ps.corridor > ls.corridor_lightspace

ps.floor1 > ps.private_office > hs.privateoffice_hvac
ps.private_office > ls.privateoffice_lightspace

ps.floor1 > ps.kitchenette > hs.kitchenette_hvac
ps.kitchenette > ls.kitchenette_lightspace


_folder = Path(__file__).parent
create_data_and_schema_ttl(model_name, _folder, header=sample_header(model_name))
