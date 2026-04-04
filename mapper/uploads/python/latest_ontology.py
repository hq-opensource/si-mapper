import sys
from bob.core import bind_model_namespace, dump, UNIT, Junction
from bob.externalreference.bacnet import BACnetExternalReference
from bob.enum import Air

from scratch.hvac.fan import Fan
from scratch.hvac.damper import Damper
from bob.equipment.hvac.filter import Filter
from bob.equipment.hvac.coil import ChilledWaterCoil, HotWaterCoil
from scratch.hvac.humidifier import ElectricalHumidifier
from scratch.electricity.vfd import VFD
from scratch.hvac.valve import ThreeWayMixingActuatedProportionalValve

from bob.sensor.temperature import AirTemperatureSensor
from bob.sensor.humidity import AirHumiditySensor
from bob.sensor.pressure import AirDifferentialStaticPressureSensor, PressureSensor

from bob.properties.ratio import Percent
from bob.properties.boolean import Boolean
from bob.properties.electrical import Amps

_namespace = bind_model_namespace("hvac_system", "urn:hvac_system/")

# === Dampers ===
damp_melange = Damper(label="DAMP-MELANGE")
damp_melange.add_property(Percent(label="VOLET MEL. No.1A"))
damp_melange["VOLET MEL. No.1A"] @ BACnetExternalReference("bacnet://2500/analog-output,10/present-value")
damp_melange.add_property(Percent(label="P.C. VOLET MEL 1A"))
damp_melange["P.C. VOLET MEL 1A"] @ BACnetExternalReference("bacnet://2500/analog-value,251/present-value")

damp_1e = Damper(label="DAMP-1E")
damp_1e.add_property(Percent(label="VOLET EVAC. No.1E"))
damp_1e["VOLET EVAC. No.1E"] @ BACnetExternalReference("bacnet://2500/analog-output,12/present-value")

damp_paf1 = Damper(label="DAMP-PAF1")
damp_paf1.add_property(Percent(label="VOLET P.A.F.1A"))
damp_paf1["VOLET P.A.F.1A"] @ BACnetExternalReference("bacnet://2500/analog-output,42/present-value")

damp_paf2 = Damper(label="DAMP-PAF2")
damp_rav = Damper(label="DAMP-RAV")

# === Fans ===
fan_1a = Fan(label="FAN-1A")
fan_1a.add_property(Percent(label="VITESSE ALIM. No. 1A"))
fan_1a["VITESSE ALIM. No. 1A"] @ BACnetExternalReference("bacnet://2500/analog-input,6/present-value")
fan_1a.add_property(Percent(label="MOD. DRIVE ALM No.1A"))
fan_1a["MOD. DRIVE ALM No.1A"] @ BACnetExternalReference("bacnet://2500/analog-output,6/present-value")
fan_1a.add_property(Boolean(label="FAUTE VENT. ALIM. 1A"))
fan_1a["FAUTE VENT. ALIM. 1A"] @ BACnetExternalReference("bacnet://2500/binary-input,7/present-value")
fan_1a.add_property(Boolean(label="A/D VENT. ALM. No.1A"))
fan_1a["A/D VENT. ALM. No.1A"] @ BACnetExternalReference("bacnet://2500/binary-output,5/present-value")
fan_1a.add_property(Boolean(label="STATUT DIG 1A"))
fan_1a["STATUT DIG 1A"] @ BACnetExternalReference("bacnet://2500/binary-value,255/present-value")

fan_1r = Fan(label="FAN-1R")
fan_1r.add_property(Percent(label="VITESSE RET. No.1A"))
fan_1r["VITESSE RET. No.1A"] @ BACnetExternalReference("bacnet://2500/analog-input,11/present-value")
fan_1r.add_property(Percent(label="MOD. DRIVE RET No.1R"))
fan_1r["MOD. DRIVE RET No.1R"] @ BACnetExternalReference("bacnet://2500/analog-output,8/present-value")
fan_1r.add_property(Boolean(label="FAUTE VENT. RET. 1A"))
fan_1r["FAUTE VENT. RET. 1A"] @ BACnetExternalReference("bacnet://2500/binary-input,12/present-value")
fan_1r.add_property(Boolean(label="A/D VENT. RET. No.1A"))
fan_1r["A/D VENT. RET. No.1A"] @ BACnetExternalReference("bacnet://2500/binary-output,7/present-value")
fan_1r.add_property(Boolean(label="STATUT DIG 1R"))
fan_1r["STATUT DIG 1R"] @ BACnetExternalReference("bacnet://2500/binary-value,256/present-value")

fan_1e = Fan(label="FAN-1E")
fan_1e.add_property(Boolean(label="A/D EVAC. No.1E"))
fan_1e["A/D EVAC. No.1E"] @ BACnetExternalReference("bacnet://2500/binary-output,11/present-value")
fan_1e.add_property(Boolean(label="STATUT DIG 1E"))
fan_1e["STATUT DIG 1E"] @ BACnetExternalReference("bacnet://2500/binary-value,1/present-value")

# VFDs
vfd_1r = VFD(label="VFD-1R")
vfd_1a = VFD(label="VFD-1A")
vfd_1r.electricalOutlet >> fan_1r.electricalInlet
vfd_1a.electricalOutlet >> fan_1a.electricalInlet

# === Coils & Valve ===
coil_cool_1 = ChilledWaterCoil(label="COIL-COOL-1")
coil_cool_1.add_property(Percent(label="SERP. REF. No.1A"))
coil_cool_1["SERP. REF. No.1A"] @ BACnetExternalReference("bacnet://2500/analog-output,9/present-value")
coil_cool_1.add_property(Percent(label="P.C. SERP REF 1A"))
coil_cool_1["P.C. SERP REF 1A"] @ BACnetExternalReference("bacnet://2500/analog-value,252/present-value")
coil_cool_1.add_property(Boolean(label="PERM REFR 1A"))
coil_cool_1["PERM REFR 1A"] @ BACnetExternalReference("bacnet://2500/binary-value,253/present-value")
coil_cool_1.add_property(Boolean(label="PERM. REF. 1A"))
coil_cool_1["PERM. REF. 1A"] @ BACnetExternalReference("bacnet://2500/binary-value,147/present-value")

coil_heat_1 = HotWaterCoil(label="COIL-HEAT-1")
coil_heat_1.add_property(Percent(label="SERP. ELECT. 1A"))
coil_heat_1["SERP. ELECT. 1A"] @ BACnetExternalReference("bacnet://2500/analog-output,13/present-value")
coil_heat_1.add_property(Percent(label="PC. SERP. ELEC. 1A"))
coil_heat_1["PC. SERP. ELEC. 1A"] @ BACnetExternalReference("bacnet://2500/analog-value,248/present-value")

valve_3w_1 = ThreeWayMixingActuatedProportionalValve(label="VALVE-3W-1")

# === Humidifier ===
hum_1 = ElectricalHumidifier(label="HUM-1")
hum_1.add_property(Percent(label="HUMIDIFICATEUR 1A"))
hum_1["HUMIDIFICATEUR 1A"] @ BACnetExternalReference("bacnet://2500/analog-output,40/present-value")
hum_1.add_property(Percent(label="P.C. HUM 1A"))
hum_1["P.C. HUM 1A"] @ BACnetExternalReference("bacnet://2500/analog-value,249/present-value")
hum_1.add_property(Percent(label="STATUT HUMI. 1A"))
hum_1["STATUT HUMI. 1A"] @ BACnetExternalReference("bacnet://2500/analog-input,19/present-value")

# === Filter ===
filt_1 = Filter(label="FILT-1")

# === Sensors ===
sens_dp_1 = AirDifferentialStaticPressureSensor(label="SENS-DP-1")
sens_dp_1 @ BACnetExternalReference("bacnet://2500/analog-input,18/present-value")
sens_dp_1 % filt_1

sens_hum_ret = AirHumiditySensor(label="SENS-HUM-RET", hasUnit=UNIT.PERCENT_RH)
sens_hum_ret @ BACnetExternalReference("bacnet://2500/analog-input,16/present-value")

sens_ll_1 = AirTemperatureSensor(label="SENS-LL-1", hasUnit=UNIT.DEG_C)
sens_ll_1 @ BACnetExternalReference("bacnet://2500/binary-value,254/present-value")

sens_sp_1 = PressureSensor(label="SENS-SP-1", hasUnit=UNIT.PA, ofMedium=Air)
sens_sp_1 @ BACnetExternalReference("bacnet://2500/analog-input,17/present-value")
sens_sp_1.add_property(Percent(label="P.C. PRES STAT 1A"))
sens_sp_1["P.C. PRES STAT 1A"] @ BACnetExternalReference("bacnet://2500/analog-value,250/present-value")

sens_temp_mix = AirTemperatureSensor(label="SENS-TEMP-MIX", hasUnit=UNIT.DEG_C)
sens_temp_mix @ BACnetExternalReference("bacnet://2500/analog-input,15/present-value")

sens_temp_ret = AirTemperatureSensor(label="SENS-TEMP-RET", hasUnit=UNIT.DEG_C)
sens_temp_ret @ BACnetExternalReference("bacnet://2500/analog-input,14/present-value")

sens_temp_sup = AirTemperatureSensor(label="SENS-TEMP-SUP", hasUnit=UNIT.DEG_C)
sens_temp_sup @ BACnetExternalReference("bacnet://2500/analog-input,13/present-value")

# === Wiring ===
ret_jct = Junction(label="Return_Air_Junction")
mix_jct = Junction(label="Mixed_Air_Junction")
exh_jct = Junction(label="Exhaust_Air_Junction")

fan_1r.airOutlet >> ret_jct
ret_jct >> damp_rav.airInlet
ret_jct >> damp_melange.airInlet
ret_jct >> exh_jct

exh_jct >> fan_1e.airInlet
fan_1e.airOutlet >> damp_1e.airInlet

damp_paf1.airOutlet >> mix_jct
damp_paf2.airOutlet >> mix_jct
damp_melange.airOutlet >> mix_jct

mix_jct >> filt_1.airInlet
filt_1.airOutlet >> coil_cool_1.airInlet
coil_cool_1.airOutlet >> fan_1a.airInlet
fan_1a.airOutlet >> coil_heat_1.airInlet

sens_temp_mix % mix_jct
sens_temp_ret % fan_1r
sens_hum_ret % fan_1r
sens_temp_sup % fan_1a
sens_ll_1 % coil_cool_1
sens_sp_1 % fan_1a

if __name__ == "__main__":
    dump(filename="latest_ontology.ttl")
