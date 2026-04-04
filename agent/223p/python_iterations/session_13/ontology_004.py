from bob.core import bind_model_namespace, dump, UNIT, Junction
from bob.properties import Temperature, Pressure, RelativeHumidity, Amps, OnOffCommand, OnOffStatus
from bob.properties.ratio import Percent, PercentCommand
from scratch.hvac.damper import Damper
from scratch.hvac.fan import Fan
from bob.equipment.hvac.filter import Filter
from bob.equipment.hvac.coil import ElectricalHeatingCoil, ChilledWaterCoil
from scratch.hvac.valve import ThreeWayMixingActuatedProportionalValve
from scratch.hvac.humidifier import ElectricalHumidifier
from scratch.electricity.vfd import VFD
from bob.sensor.temperature import AirTemperatureSensor
from bob.sensor.humidity import AirHumiditySensor
from bob.sensor.pressure import AirDifferentialStaticPressureSensor, PressureSensor
from bob.externalreference.bacnet import BACnetExternalReference
from bob.enum import Air

_namespace = bind_model_namespace("hvac_system_one", "urn:hvac_system_one/")

# 1. Instantiate Equipment
damper_evac = Damper(label="MD-EVAC")
fan_e = Fan(label="1-E")

damper_paf1 = Damper(label="MD-PAF-1")
damper_paf2 = Damper(label="MD-PAF-2")
damper_melange = Damper(label="MD-MELANGE")

filter_1 = Filter(label="FLT-1")
cc_1 = ChilledWaterCoil(label="CC-1")
valve_cc_1 = ThreeWayMixingActuatedProportionalValve(label="VALVE-CC-1")

fan_a = Fan(label="1-A")
vfd_1a = VFD(label="VFD-1A")

hc_1 = ElectricalHeatingCoil(label="HC-1")
hum_1 = ElectricalHumidifier(label="HUM-1")

damper_rav = Damper(label="MD-RAV")
fan_r = Fan(label="1-R")
vfd_1r = VFD(label="VFD-1R")

mix_plenum = Junction(label="MIX-PLENUM")

# 2. Connections
# Exhaust
damper_evac.airOutlet >> fan_e.airInlet

# Return
fan_r.airOutlet >> damper_rav.airInlet

# Mixing
damper_melange.airOutlet >> mix_plenum
damper_paf1.airOutlet >> mix_plenum
damper_paf2.airOutlet >> mix_plenum

# Supply
mix_plenum >> filter_1.airInlet
filter_1.airOutlet >> cc_1.airInlet
cc_1.airOutlet >> fan_a.airInlet
fan_a.airOutlet >> hc_1.airInlet
hc_1.airOutlet >> hum_1.airInlet

# Electrical
vfd_1a.electricalOutlet >> fan_a.electricalInlet
vfd_1r.electricalOutlet >> fan_r.electricalInlet

# 3. Sensors & BACnet
temp_ret = AirTemperatureSensor(label="TEMP-RET")
temp_ret % fan_r
temp_ret @ BACnetExternalReference("bacnet://2500/analog-input,14/present-value")

hum_ret = AirHumiditySensor(label="HUM-RET")
hum_ret % fan_r
hum_ret @ BACnetExternalReference("bacnet://2500/analog-input,16/present-value")

temp_mix = AirTemperatureSensor(label="TEMP-MIX")
temp_mix % filter_1
temp_mix @ BACnetExternalReference("bacnet://2500/analog-input,15/present-value")

dps_1 = AirDifferentialStaticPressureSensor(label="DPS-1")
dps_1 % filter_1
dps_1 @ BACnetExternalReference("bacnet://2500/analog-input,18/present-value")

temp_sup = AirTemperatureSensor(label="TEMP-SUP")
temp_sup % hc_1
temp_sup @ BACnetExternalReference("bacnet://2500/analog-input,13/present-value")

sps_1 = PressureSensor(label="SPS-1", ofMedium=Air, hasUnit=UNIT["IN_H2O"])
sps_1 % fan_a
sps_1 @ BACnetExternalReference("bacnet://2500/analog-input,17/present-value")

sps_1_sp = Pressure(label="P.C. PRES STAT 1A", hasUnit=UNIT["IN_H2O"])
sps_1.add_property(sps_1_sp)
sps_1_sp @ BACnetExternalReference("bacnet://2500/analog-value,250/present-value")

# 4. Equipment properties & BACnet
# HC-1
hc_1_ao13 = Percent(label="SERP. ELECT. 1A")
hc_1.add_property(hc_1_ao13)
hc_1_ao13 @ BACnetExternalReference("bacnet://2500/analog-output,13/present-value")

hc_1_av248 = Temperature(label="PC. SERP. ELEC. 1A")
hc_1.add_property(hc_1_av248)
hc_1_av248 @ BACnetExternalReference("bacnet://2500/analog-value,248/present-value")

# MD-PAF-1
paf_1_ao42 = Percent(label="VOLET P.A.F.1A")
damper_paf1.add_property(paf_1_ao42)
paf_1_ao42 @ BACnetExternalReference("bacnet://2500/analog-output,42/present-value")

# 1-E
fan_e_bo11 = OnOffCommand(label="A/D EVAC. No.1E")
fan_e.add_property(fan_e_bo11)
fan_e_bo11 @ BACnetExternalReference("bacnet://2500/binary-output,11/present-value")

fan_e_bv1 = OnOffStatus(label="STATUT DIG 1E")
fan_e.add_property(fan_e_bv1)
fan_e_bv1 @ BACnetExternalReference("bacnet://2500/binary-value,1/present-value")

# CC-1
cc_1_ao9 = PercentCommand(label="SERP. REF. No.1A")
cc_1.add_property(cc_1_ao9)
cc_1_ao9 @ BACnetExternalReference("bacnet://2500/analog-output,9/present-value")

cc_1_av252 = Temperature(label="P.C. SERP REF 1A")
cc_1.add_property(cc_1_av252)
cc_1_av252 @ BACnetExternalReference("bacnet://2500/analog-value,252/present-value")

cc_1_bv147 = OnOffStatus(label="PERM. REF. 1A")
cc_1.add_property(cc_1_bv147)
cc_1_bv147 @ BACnetExternalReference("bacnet://2500/binary-value,147/present-value")

cc_1_bv253 = OnOffStatus(label="PERM REFR 1A")
cc_1.add_property(cc_1_bv253)
cc_1_bv253 @ BACnetExternalReference("bacnet://2500/binary-value,253/present-value")

# MD-EVAC
md_evac_ao12 = Percent(label="VOLET EVAC. No.1E")
damper_evac.add_property(md_evac_ao12)
md_evac_ao12 @ BACnetExternalReference("bacnet://2500/analog-output,12/present-value")

# MD-MELANGE
md_melange_ao10 = Percent(label="VOLET MEL. No.1A")
damper_melange.add_property(md_melange_ao10)
md_melange_ao10 @ BACnetExternalReference("bacnet://2500/analog-output,10/present-value")

md_melange_av251 = Temperature(label="P.C. VOLET MEL 1A")
damper_melange.add_property(md_melange_av251)
md_melange_av251 @ BACnetExternalReference("bacnet://2500/analog-value,251/present-value")

# HUM-1
hum_1_ai19 = Amps(label="STATUT HUMI. 1A")
hum_1.add_property(hum_1_ai19)
hum_1_ai19 @ BACnetExternalReference("bacnet://2500/analog-input,19/present-value")

hum_1_ao40 = PercentCommand(label="HUMIDIFICATEUR 1A")
hum_1.add_property(hum_1_ao40)
hum_1_ao40 @ BACnetExternalReference("bacnet://2500/analog-output,40/present-value")

hum_1_av249 = Percent(label="P.C. HUM 1A")
hum_1.add_property(hum_1_av249)
hum_1_av249 @ BACnetExternalReference("bacnet://2500/analog-value,249/present-value")

# 1-A
fan_a_ai6 = Amps(label="VITESSE ALIM. No. 1A")
fan_a.add_property(fan_a_ai6)
fan_a_ai6 @ BACnetExternalReference("bacnet://2500/analog-input,6/present-value")

fan_a_bo5 = OnOffCommand(label="A/D VENT. ALM. No.1A")
fan_a.add_property(fan_a_bo5)
fan_a_bo5 @ BACnetExternalReference("bacnet://2500/binary-output,5/present-value")

fan_a_bi7 = OnOffStatus(label="FAUTE VENT. ALIM. 1A")
fan_a.add_property(fan_a_bi7)
fan_a_bi7 @ BACnetExternalReference("bacnet://2500/binary-input,7/present-value")

fan_a_bv255 = OnOffStatus(label="STATUT DIG 1A")
fan_a.add_property(fan_a_bv255)
fan_a_bv255 @ BACnetExternalReference("bacnet://2500/binary-value,255/present-value")

fan_a_bv254 = OnOffStatus(label="ARRET BAS LIM GEL 1A")
fan_a.add_property(fan_a_bv254)
fan_a_bv254 @ BACnetExternalReference("bacnet://2500/binary-value,254/present-value")

# VFD-1R
vfd_1r_ao8 = PercentCommand(label="MOD. DRIVE RET No.1R")
vfd_1r.add_property(vfd_1r_ao8)
vfd_1r_ao8 @ BACnetExternalReference("bacnet://2500/analog-output,8/present-value")

# VFD-1A
vfd_1a_ao6 = PercentCommand(label="MOD. DRIVE ALM No.1A")
vfd_1a.add_property(vfd_1a_ao6)
vfd_1a_ao6 @ BACnetExternalReference("bacnet://2500/analog-output,6/present-value")

# 1-R
fan_r_ai11 = Amps(label="VITESSE RET. No.1A")
fan_r.add_property(fan_r_ai11)
fan_r_ai11 @ BACnetExternalReference("bacnet://2500/analog-input,11/present-value")

fan_r_bo7 = OnOffCommand(label="A/D VENT. RET. No.1A")
fan_r.add_property(fan_r_bo7)
fan_r_bo7 @ BACnetExternalReference("bacnet://2500/binary-output,7/present-value")

fan_r_bi12 = OnOffStatus(label="FAUTE VENT. RET. 1A")
fan_r.add_property(fan_r_bi12)
fan_r_bi12 @ BACnetExternalReference("bacnet://2500/binary-input,12/present-value")

fan_r_bv256 = OnOffStatus(label="STATUT DIG 1R")
fan_r.add_property(fan_r_bv256)
fan_r_bv256 @ BACnetExternalReference("bacnet://2500/binary-value,256/present-value")

if __name__ == "__main__":
    dump(filename="latest_ontology.ttl")
