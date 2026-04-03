import os
import re
from rdflib import URIRef
from bob.core import bind_model_namespace, dump, UNIT, Property, Equipment, Junction
from bob.externalreference.bacnet import BACnetExternalReference

from scratch.hvac.fan import Fan
from scratch.hvac.damper import Damper
from bob.equipment.hvac.filter import Filter
from bob.equipment.hvac.coil import ChilledWaterCoil, HotWaterCoil
from scratch.hvac.humidifier import ElectricalHumidifier
from scratch.electricity.vfd import VFD
from bob.sensor.temperature import AirTemperatureSensor
from bob.sensor.humidity import AirHumiditySensor
from bob.sensor.pressure import AirDifferentialStaticPressureSensor, PressureSensor
from scratch.assemblage import model_namespace
from bob.enum import Air, Fluid
from bob.connections.air import AirInletConnectionPoint, AirOutletConnectionPoint

model_name, global_ns = model_namespace(__file__)
_namespace = bind_model_namespace(model_name, f"urn:{global_ns}:{model_name}/")

class ThreeWayValve(Equipment):
    pass

# Equipment
fan_1e = Fan(label="1-E")
fan_1a = Fan(label="1-A")
fan_1r = Fan(label="1-R")

vfd_1a = VFD(label="VFD-1A")
vfd_1r = VFD(label="VFD-1R")

damp_1e = Damper(label="DAMP-1E")
damp_mel = Damper(label="DAMP-MEL")
damp_paf_up = Damper(label="DAMP-PAF-UP")
damp_paf_low = Damper(label="DAMP-PAF-LOW")
damp_rav = Damper(label="DAMP-RAV")

cc_1 = ChilledWaterCoil(label="CC-1")
hc_1 = HotWaterCoil(label="HC-1")

valve_cc = ThreeWayValve(label="VALVE-CC")

filt_1 = Filter(label="FILT-1")
hum_1 = ElectricalHumidifier(label="HUM-1")

# Sensors
temp_ret = AirTemperatureSensor(label="TEMP-RET", hasUnit=UNIT.DEG_C)
hum_ret = AirHumiditySensor(label="HUM-RET", hasUnit=UNIT.PERCENT)
temp_mix = AirTemperatureSensor(label="TEMP-MIX", hasUnit=UNIT.DEG_C)
ll_1 = AirTemperatureSensor(label="LL-1", hasUnit=UNIT.DEG_C)

sps_1 = PressureSensor(label="SPS-1", hasUnit=UNIT["IN-H2O"], ofMedium=Air)
dps_1 = AirDifferentialStaticPressureSensor(label="DPS-1", hasUnit=UNIT["IN-H2O"])

# Junctions
mixing_plenum = Junction(label="Mixing_Plenum", hasMedium=Fluid.Air)

# Connections
vfd_1a.electricalOutlet >> fan_1a.electricalInlet
vfd_1r.electricalOutlet >> fan_1r.electricalInlet

# Air flow
damp_1e.airOutlet >> fan_1e.airInlet

fan_1r.airOutlet >> damp_rav.airInlet

damp_paf_low.airOutlet >> damp_paf_up.airInlet

# PAF UP and MEL both go to the mixing plenum, which goes to the filter
damp_paf_up.airOutlet >> mixing_plenum
damp_mel.airOutlet >> mixing_plenum
mixing_plenum >> filt_1.airInlet

filt_1.airOutlet >> cc_1.airInlet
cc_1.airOutlet >> fan_1a.airInlet
fan_1a.airOutlet >> hc_1.airInlet
# Note: ElectricalHumidifier doesn't have air side connection points in our base classes, so we skip >> on it.

# Sensor linking
temp_ret % fan_1r
hum_ret % fan_1r
temp_mix % filt_1
dps_1 % filt_1
ll_1 % hc_1
sps_1 % hc_1

# BACnet point extraction
def apply_bacnet(entity, bacnet_dict, prop_name=""):
    addr = bacnet_dict.get("address", "")
    if not addr: return
    parts = addr.split(".")
    if len(parts) != 2: return
    device, obj = parts[0], parts[1]
    
    tmap = {
        "AI": "analog-input",
        "AO": "analog-output",
        "AV": "analog-value",
        "BI": "binary-input",
        "BO": "binary-output",
        "BV": "binary-value",
        "SCH": "schedule"
    }
    
    match = re.match(r"([A-Z]+)(\d+)", obj)
    if match:
        suffix, inst = match.group(1), match.group(2)
        if suffix in tmap:
            bacnet_uri = f"bacnet://{device}/{tmap[suffix]},{inst}/present-value"
            
            if isinstance(entity, Equipment) and not type(entity).__name__.endswith("Sensor"):
                p = Property(label=bacnet_dict.get("name", prop_name))
                entity.add_property(p)
                p @ BACnetExternalReference(bacnet_uri)
            else:
                entity @ BACnetExternalReference(bacnet_uri)

# Map BACnet points based on internal grid
apply_bacnet(valve_cc, {"address": "2500.AO9", "unit": "Percentage", "name": "SERP. REF. No.1A"})
apply_bacnet(valve_cc, {"address": "2500.AV252", "unit": "Celsius", "name": "P.C. SERP REF 1A"})

apply_bacnet(hc_1, {"address": "2500.AO13", "unit": "Percentage", "name": "SERP. ELECT. 1A"})
apply_bacnet(hc_1, {"address": "2500.AV248", "unit": "Celsius", "name": "PC. SERP. ELEC. 1A"})

apply_bacnet(temp_ret, {"address": "2500.AI14", "unit": "Celsius", "name": "TEMP. RETOUR No.1A"})
apply_bacnet(ll_1, {"address": "2500.BV254", "unit": "", "name": "ARRET BAS LIM GEL 1A"})
apply_bacnet(sps_1, {"address": "2500.AI17", "unit": "inWC", "name": "PRES. STAT. No.1A"})
apply_bacnet(sps_1, {"address": "2500.AV250", "unit": "inWC", "name": "P.C. PRES STAT 1A"})

apply_bacnet(temp_mix, {"address": "2500.AI15", "unit": "Celsius", "name": "TEMP. MEL. No.1A"})
apply_bacnet(damp_paf_low, {"address": "2500.AO42", "unit": "Percentage", "name": "VOLET P.A.F.1A"})

apply_bacnet(fan_1e, {"address": "2500.BO11", "unit": "On/Off", "name": "A/D EVAC. No.1E"})
apply_bacnet(fan_1e, {"address": "2500.BV1", "unit": "On/Off", "name": "STATUT DIG 1E"})

apply_bacnet(cc_1, {"address": "2500.BV253", "unit": "On/Off", "name": "PERM REFR 1A"})
apply_bacnet(cc_1, {"address": "2500.BV147", "unit": "On/Off", "name": "PERM. REF. 1A"})

apply_bacnet(hum_ret, {"address": "2500.AI16", "unit": "Percentage", "name": "HUMIDITE RET. No.1A"})
apply_bacnet(dps_1, {"address": "2500.AI18", "unit": "inWC", "name": "PRESSION FILTRE 1A"})

apply_bacnet(damp_mel, {"address": "2500.AO10", "unit": "Percentage", "name": "VOLET MEL. No.1A"})
apply_bacnet(damp_mel, {"address": "2500.AV251", "unit": "Celsius", "name": "P.C. VOLET MEL 1A"})

apply_bacnet(hum_1, {"address": "2500.AO40", "unit": "Percentage", "name": "HUMIDIFICATEUR 1A"})
apply_bacnet(hum_1, {"address": "2500.AV249", "unit": "Percentage", "name": "P.C. HUM 1A"})
apply_bacnet(hum_1, {"address": "2500.AI19", "unit": "Amperes", "name": "STATUT HUMI. 1A"})

apply_bacnet(fan_1a, {"address": "2500.AI6", "unit": "Amperes", "name": "VITESSE ALIM. No. 1A"})
apply_bacnet(fan_1a, {"address": "2500.BO5", "unit": "On/Off", "name": "A/D VENT. ALM. No.1A"})
apply_bacnet(fan_1a, {"address": "2500.BI7", "unit": "", "name": "FAUTE VENT. ALIM. 1A"})
apply_bacnet(fan_1a, {"address": "2500.BV255", "unit": "On/Off", "name": "STATUT DIG 1A"})

apply_bacnet(damp_1e, {"address": "2500.AO12", "unit": "Percentage", "name": "VOLET EVAC. No.1E"})

apply_bacnet(vfd_1r, {"address": "2500.AO8", "unit": "Percentage", "name": "MOD. DRIVE RET No.1R"})
apply_bacnet(vfd_1a, {"address": "2500.AO6", "unit": "Percentage", "name": "MOD. DRIVE ALM No.1A"})

apply_bacnet(fan_1r, {"address": "2500.BV256", "unit": "On/Off", "name": "STATUT DIG 1R"})
apply_bacnet(fan_1r, {"address": "2500.AI11", "unit": "Amperes", "name": "VITESSE RET. No.1A"})
apply_bacnet(fan_1r, {"address": "2500.BO7", "unit": "On/Off", "name": "A/D VENT. RET. No.1A"})
apply_bacnet(fan_1r, {"address": "2500.BI12", "unit": "", "name": "FAUTE VENT. RET. 1A"})

if __name__ == "__main__":
    dump(filename="latest_ontology.ttl")
