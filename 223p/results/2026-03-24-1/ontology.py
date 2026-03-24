import json
from pathlib import Path

from bob.core import UNIT, bind_model_namespace, dump, System
from bob.connections.air import AirConnection
from bob.equipment.hvac.fan import Fan
from bob.equipment.hvac.damper import Damper
from bob.equipment.hvac.filter import Filter
from bob.equipment.hvac.coil import ChilledWaterCoil, ElectricalHeatingCoil
from bob.equipment.hvac.humidifier import Humidifier
from bob.equipment.electricity.vfd import VFD
from bob.sensor.temperature import AirTemperatureSensor
from bob.sensor.humidity import AirHumiditySensor
from bob.sensor.pressure import AirDifferentialStaticPressureSensor
from bob.externalreference.bacnet import BACnetExternalReference
from scratch.assemblage import model_namespace

model_name, global_ns = model_namespace(__file__)
bind_model_namespace(model_name, f"urn:{global_ns}:{model_name}/")


def _bacnet_uri(point_meta: dict) -> str:
    device = point_meta.get("device-identifier", "")
    obj_type = point_meta.get("object-type", "")
    inst = point_meta.get("object-instance", "")
    return f"bacnet://{device}/{obj_type},{inst}/present-value"


def attach_bacnet_to_sensor(sensor, bacnet_json: str, unit=None):
    if not bacnet_json:
        return
    try:
        meta = json.loads(bacnet_json)
    except Exception:
        return
    if not isinstance(meta, dict) or not meta:
        return
    # pick the first point
    first = next(iter(meta.values()))
    try:
        uri = _bacnet_uri(first)
        sensor.observedProperty @ BACnetExternalReference(uri)
    except Exception:
        pass
    if unit is not None:
        try:
            sensor.observedProperty.hasUnit = unit
        except Exception:
            pass


ahu_system = System(label="AHU-1 System")

# Air connections
outdoor_air = AirConnection(label="OutdoorAir")
return_air_from_zone = AirConnection(label="ReturnAirFromZone")
return_air = AirConnection(label="ReturnAir")
mixed_air = AirConnection(label="MixedAir")
supply_air = AirConnection(label="SupplyAir")
exhaust_air = AirConnection(label="ExhaustAir")

# Dampers (OA, mixing, exhaust)
d_fa1 = Damper(label="D-FA1")
d_fa2 = Damper(label="D-FA2")
d_mix = Damper(label="D-MIX")
d_exh = Damper(label="D-EXH")

# Fans and drives
fan_supply = Fan(label="1-A")
fan_return = Fan(label="1-R")
fan_exhaust = Fan(label="1-E")
vfd_supply = VFD(label="VFD-1-A")
vfd_return = VFD(label="VFD-1-R")

# Filtration and coils
filt = Filter(label="FLT-1")
clg_coil = ChilledWaterCoil(label="CC-1")
htg_coil = ElectricalHeatingCoil(label="HC-1")

# Humidifier
humidifier = Humidifier(label="HUM-1")

# Sensors
st_mix = AirTemperatureSensor(label="ST-MIX")
st_sup = AirTemperatureSensor(label="ST-SUP")
st_ret = AirTemperatureSensor(label="ST-RET")
sdp_flt = AirDifferentialStaticPressureSensor(label="SDP-FLT")
ssp_sup = AirDifferentialStaticPressureSensor(label="SSP-SUP")
sll_1 = AirTemperatureSensor(label="SLL-1")
sh_ret = AirHumiditySensor(label="SH-RET")
sh_sup = AirHumiditySensor(label="SH-SUP")

# Wire primary airflow with explicit connection points
for damper in (d_fa1, d_fa2):
    outdoor_air >> damper.airInlet
    damper.airOutlet >> mixed_air

return_air_from_zone >> fan_return.airInlet
fan_return.airOutlet >> return_air
return_air >> d_exh.airInlet
d_exh.airOutlet >> fan_exhaust.airInlet
fan_exhaust.airOutlet >> exhaust_air

# Mixed to supply path
mixed_air >> filt.airInlet
filt.airOutlet >> clg_coil.airInlet
clg_coil.airOutlet >> htg_coil.airInlet
htg_coil.airOutlet >> fan_supply.airInlet
fan_supply.airOutlet >> supply_air

# Humidifier placement (no location specified)

# Drives to fans
vfd_supply >> fan_supply
vfd_return >> fan_return

# Sensors to connections
st_mix % mixed_air
st_sup % supply_air
st_ret % return_air
sdp_flt % (filt.airInlet, filt.airOutlet)
ssp_sup % supply_air
sll_1 % supply_air
sh_ret % return_air
sh_sup % supply_air

# BACnet metadata attachments
bacnet_meta = {
    "ST-MIX": '{"2500.AI15": {"device-identifier": 2500, "object-instance": 15, "object-type": "analog-input", "unit": "Celsius", "name": "TEMP. MEL. No.1A"}}',
    "ST-SUP": '{"2500.AI13": {"device-identifier": 2500, "object-instance": 13, "object-type": "analog-input", "unit": "Celsius", "name": "TEMP. ALIM. No.1A"}}',
    "ST-RET": '{"2500.AI14": {"device-identifier": 2500, "object-instance": 14, "object-type": "analog-input", "unit": "Celsius", "name": "TEMP. RETOUR No.1A"}}',
    "SH-RET": '{"2500.AI16": {"device-identifier": 2500, "object-instance": 16, "object-type": "analog-input", "unit": "Percentage", "name": "HUMIDITE RET. No.1A"}}',
    "SSP-SUP": '{"2500.AI17": {"object-type": "analog-input", "device-identifier": 2500, "object-instance": 17, "unit": "inWC", "name": "PRES. STAT. No.1A"}}',
    "SH-SUP": '{}',
    "SDP-FLT": '{"2500.AI18": {"object-type": "analog-input", "device-identifier": 2500, "object-instance": 18, "unit": "inWC", "name": "PRESSION FILTRE 1A"}}',
    "SLL-1": '{"2500.BV254": {"name": "ARRET BAS LIM GEL 1A", "unit": "", "object-type": "binary-value", "object-instance": 254, "device-identifier": 2500}}',
}
attach_bacnet_to_sensor(st_mix, bacnet_meta.get("ST-MIX", ""), UNIT.DEG_C)
attach_bacnet_to_sensor(st_sup, bacnet_meta.get("ST-SUP", ""), UNIT.DEG_C)
attach_bacnet_to_sensor(st_ret, bacnet_meta.get("ST-RET", ""), UNIT.DEG_C)
attach_bacnet_to_sensor(sh_ret, bacnet_meta.get("SH-RET", ""), UNIT.PERCENT)
attach_bacnet_to_sensor(sh_sup, bacnet_meta.get("SH-SUP", ""), UNIT.PERCENT)
attach_bacnet_to_sensor(ssp_sup, bacnet_meta.get("SSP-SUP", ""), UNIT.IN_WG if hasattr(UNIT, "IN_WG") else None)
attach_bacnet_to_sensor(sdp_flt, bacnet_meta.get("SDP-FLT", ""), UNIT.IN_WG if hasattr(UNIT, "IN_WG") else None)
attach_bacnet_to_sensor(sll_1, bacnet_meta.get("SLL-1", ""), UNIT.DEG_C)

# Assemble system
ahu_system > [
    d_fa1,
    d_fa2,
    d_mix,
    d_exh,
    fan_supply,
    fan_return,
    fan_exhaust,
    vfd_supply,
    vfd_return,
    filt,
    clg_coil,
    htg_coil,
    humidifier,
    st_mix,
    st_sup,
    st_ret,
    sdp_flt,
    ssp_sup,
    sll_1,
    sh_ret,
    sh_sup,
]

if __name__ == "__main__":
    output_path = Path("ttl")
    output_path.mkdir(exist_ok=True)

    output_file = output_path / "ontology.ttl"
    dump(filename=str(output_file))

    print(f"Ontology serialized to {output_file}")
