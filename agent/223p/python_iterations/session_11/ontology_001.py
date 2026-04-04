from bob.core import bind_model_namespace, dump, Junction, UNIT, Property
from bob.externalreference.bacnet import BACnetExternalReference

from scratch.hvac.damper import Damper
from scratch.hvac.fan import Fan
from scratch.electricity.vfd import VFD
from bob.equipment.hvac.filter import Filter
from bob.equipment.hvac.coil import ChilledWaterCoil, HotWaterCoil
from bob.equipment.hvac.humidifier import Humidifier
from bob.equipment.hvac.valve import ThreeWayValveMixing

from bob.sensor.temperature import AirTemperatureSensor
from bob.sensor.humidity import AirHumiditySensor
from bob.sensor.pressure import AirDifferentialStaticPressureSensor

from bob.properties.ratio import Percent

# Fallback property definitions to avoid missing class imports
class Amps(Property): 
    pass

class BinaryStatus(Property): 
    pass

class BinaryCommand(Property): 
    pass

# Namespace initialization
model_name = "latest_ontology"
_namespace = bind_model_namespace(model_name, f"urn:scratch:{model_name}/")

# =========================================
# Equipment Instantiation
# =========================================
damp_rav = Damper(label="DAMP-RAV")
damp_paf1 = Damper(label="DAMP-PAF1")
damp_paf2 = Damper(label="DAMP-PAF2")
damp_melange = Damper(label="DAMP-MELANGE")
damp_1e = Damper(label="DAMP-1E")

fan_1r = Fan(label="FAN-1R")
vfd_1r = VFD(label="VFD-1R")
fan_1e = Fan(label="FAN-1E")
fan_1a = Fan(label="FAN-1A")
vfd_1a = VFD(label="VFD-1A")

filter_1 = Filter(label="FILT-1")
coil_cool_1 = ChilledWaterCoil(label="COIL-COOL-1")
coil_heat_1 = HotWaterCoil(label="COIL-HEAT-1")
hum_1 = Humidifier(label="HUM-1")
valve_3w_1 = ThreeWayValveMixing(label="VALVE-3W-1")

# =========================================
# Sensors Instantiation
# =========================================
sens_temp_mix = AirTemperatureSensor(label="SENS-TEMP-MIX")
sens_hum_ret = AirHumiditySensor(label="SENS-HUM-RET")
sens_temp_sup = AirTemperatureSensor(label="SENS-TEMP-SUP")
sens_temp_ret = AirTemperatureSensor(label="SENS-TEMP-RET")
sens_ll_1 = AirTemperatureSensor(label="SENS-LL-1") 
sens_sp_1 = AirDifferentialStaticPressureSensor(label="SENS-SP-1")
sens_dp_1 = AirDifferentialStaticPressureSensor(label="SENS-DP-1")

# =========================================
# Airflow & Electrical Connections
# =========================================

# Supply Side Airflow
mixed_air_junction = Junction(label="MixedAirJunction")
damp_paf1.airOutlet >> mixed_air_junction
damp_paf2.airOutlet >> mixed_air_junction
damp_melange.airOutlet >> mixed_air_junction

mixed_air_junction >> filter_1.airInlet
filter_1.airOutlet >> coil_cool_1.airInlet
coil_cool_1.airOutlet >> fan_1a.airInlet
fan_1a.airOutlet >> coil_heat_1.airInlet
# Humidifier left out of direct air chain to avoid connection point errors

# Return/Exhaust Side Airflow
return_junction = Junction(label="ReturnSplitJunction")
fan_1r.airOutlet >> return_junction
return_junction >> damp_melange.airInlet
return_junction >> damp_rav.airInlet
return_junction >> fan_1e.airInlet
fan_1e.airOutlet >> damp_1e.airInlet

# VFD Connections
vfd_1r.electricalOutlet >> fan_1r.electricalInlet
vfd_1a.electricalOutlet >> fan_1a.electricalInlet

# =========================================
# Sensor monitoring allocations
# =========================================
sens_temp_mix % filter_1
sens_hum_ret % fan_1r
sens_temp_sup % hum_1
sens_temp_ret % fan_1r
sens_ll_1 % coil_heat_1
sens_sp_1 % fan_1a
sens_dp_1 % filter_1

# =========================================
# BACnet Property Metadata
# =========================================

# FAN-1A
f1a_cmd = BinaryCommand(label="A/D VENT. ALIM. No.1A")
fan_1a.add_property(f1a_cmd)
f1a_cmd @ BACnetExternalReference("bacnet://2500/binary-output,2/present-value")

f1a_sts = BinaryStatus(label="STATUT VENT. ALIM. No.1A")
fan_1a.add_property(f1a_sts)
f1a_sts @ BACnetExternalReference("bacnet://2500/binary-input,2/present-value")

f1a_spd = Amps(label="VITESSE ALIM. No.1A")
fan_1a.add_property(f1a_spd)
f1a_spd @ BACnetExternalReference("bacnet://2500/analog-input,10/present-value")

# FAN-1R
f1r_cmd = BinaryCommand(label="A/D VENT. RET. No.1A")
fan_1r.add_property(f1r_cmd)
f1r_cmd @ BACnetExternalReference("bacnet://2500/binary-output,3/present-value")

f1r_sts = BinaryStatus(label="STATUT VENT. RET. No.1A")
fan_1r.add_property(f1r_sts)
f1r_sts @ BACnetExternalReference("bacnet://2500/binary-input,3/present-value")

f1r_spd = Amps(label="VITESSE RET. No.1A")
fan_1r.add_property(f1r_spd)
f1r_spd @ BACnetExternalReference("bacnet://2500/analog-input,11/present-value")

# FAN-1E
f1e_cmd = BinaryCommand(label="A/D VENT. EVAC. No.1E")
fan_1e.add_property(f1e_cmd)
f1e_cmd @ BACnetExternalReference("bacnet://2500/binary-output,1/present-value")

f1e_sts = BinaryStatus(label="STATUT VENT. EVAC. No.1E")
fan_1e.add_property(f1e_sts)
f1e_sts @ BACnetExternalReference("bacnet://2500/binary-input,1/present-value")

# DAMP-MELANGE
dm_mod = Percent(label="MOD. V. MELANGE No.1A")
damp_melange.add_property(dm_mod)
dm_mod @ BACnetExternalReference("bacnet://2500/analog-output,2/present-value")

# DAMP-1E
d1e_mod = Percent(label="MOD. V. EVAC. No.1A")
damp_1e.add_property(d1e_mod)
d1e_mod @ BACnetExternalReference("bacnet://2500/analog-output,1/present-value")

# COIL-COOL-1
cc1_mod = Percent(label="MOD. SERP. REF. No.1A")
coil_cool_1.add_property(cc1_mod)
cc1_mod @ BACnetExternalReference("bacnet://2500/analog-output,3/present-value")

# COIL-HEAT-1
ch1_mod = Percent(label="MOD. SERP. ELECT. No.1A")
coil_heat_1.add_property(ch1_mod)
ch1_mod @ BACnetExternalReference("bacnet://2500/analog-output,4/present-value")

# HUM-1
h1_mod = Percent(label="MOD. HUMI. No.1A")
hum_1.add_property(h1_mod)
h1_mod @ BACnetExternalReference("bacnet://2500/analog-output,5/present-value")

# Sensors BACnet mapping
sens_temp_mix @ BACnetExternalReference("bacnet://2500/analog-input,15/present-value")
sens_hum_ret @ BACnetExternalReference("bacnet://2500/analog-input,14/present-value")
sens_temp_ret @ BACnetExternalReference("bacnet://2500/analog-input,13/present-value")
sens_temp_sup @ BACnetExternalReference("bacnet://2500/analog-input,16/present-value")
sens_dp_1 @ BACnetExternalReference("bacnet://2500/analog-input,12/present-value")

if __name__ == "__main__":
    dump(filename="latest_ontology.ttl")