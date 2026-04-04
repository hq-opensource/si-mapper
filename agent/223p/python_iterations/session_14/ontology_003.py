import logging
from bob.core import bind_model_namespace, dump, UNIT, Equipment, S223
from bob.externalreference.bacnet import BACnetExternalReference
from bob.properties.electricity import ElectricPower, Amps
from bob.properties.ratio import Percent
from bob.properties.states import OnOffStatus, OnOffCommand, Schedule
from bob.properties import Temperature, Pressure
from bob.properties.flow import Flow
from scratch.assemblage import model_namespace

from bob.sensor.temperature import AirTemperatureSensor
from bob.sensor.pressure import AirDifferentialStaticPressureSensor, PressureSensor
from bob.sensor.humidity import AirHumiditySensor
from bob.sensor.sensor import Sensor
from scratch.hvac.fan import Fan
from scratch.hvac.damper import Damper
from bob.equipment.hvac.filter import Filter
from bob.equipment.hvac.coil import ChilledWaterCoil, HotWaterCoil
from scratch.hvac.humidifier import ElectricalHumidifier
from scratch.electricity.vfd import VFD
from bob.enum import Air

model_name, global_ns = model_namespace(__file__)
_namespace = bind_model_namespace(model_name, f"urn:{global_ns}:{model_name}/")

class ThreeWayValve(Equipment):
    _class_iri = S223.Valve

# Instantiate Equipment
fan_1e = Fan(label="1-E")
fan_1r = Fan(label="1-R")
fan_1a = Fan(label="1-A")

vfd_1r = VFD(label="VFD-1R")
vfd_1a = VFD(label="VFD-1A")

d_1e = Damper(label="D-1E")
d_rav = Damper(label="D-RAV")
d_mel = Damper(label="D-Mel")
d_paf1 = Damper(label="D-PAF1")
d_paf2 = Damper(label="D-PAF2")

cc_1 = ChilledWaterCoil(label="CC-1")
hc_1 = HotWaterCoil(label="HC-1")

f_1 = Filter(label="F-1")
hum_1 = ElectricalHumidifier(label="HUM-1")

v3w_1 = ThreeWayValve(label="V3W-1")

# Instantiate Sensors
te_ret = AirTemperatureSensor(label="TE-Ret", hasUnit=UNIT.DEG_C)
te_mel = AirTemperatureSensor(label="TE-Mel", hasUnit=UNIT.DEG_C)
he_ret = AirHumiditySensor(label="HE-Ret", hasUnit=UNIT.PERCENT)
sp_1 = PressureSensor(label="SP-1", hasUnit=UNIT.IN_H2O, ofMedium=Air)
dp_f1 = AirDifferentialStaticPressureSensor(label="DP-F1", hasUnit=UNIT.IN_H2O)
ll_1 = Sensor(label="LL-1")

# Connections (Airflow & Electricity)
fan_1e.airOutlet >> d_1e.airInlet
fan_1r.airOutlet >> d_rav.airInlet
fan_1r.airOutlet >> d_mel.airInlet
d_paf1.airOutlet >> f_1.airInlet
d_paf2.airOutlet >> f_1.airInlet
d_mel.airOutlet >> f_1.airInlet
f_1.airOutlet >> cc_1.airInlet
cc_1.airOutlet >> fan_1a.airInlet
fan_1a.airOutlet >> hc_1.airInlet

vfd_1r.electricalOutlet >> fan_1r.electricalInlet
vfd_1a.electricalOutlet >> fan_1a.electricalInlet

# Attach Sensors
te_ret % fan_1r
he_ret % fan_1r
te_mel % f_1
dp_f1 % f_1
ll_1 % hc_1
sp_1 % fan_1a

# BACnet External References & Properties
# HC-1
hc_1_ao = Percent(label="SERP. ELECT. 1A", hasUnit=UNIT.PERCENT)
hc_1_av = Temperature(label="PC. SERP. ELEC. 1A", hasUnit=UNIT.DEG_C)
hc_1.add_property(hc_1_ao)
hc_1.add_property(hc_1_av)
hc_1_ao @ BACnetExternalReference("bacnet://2500/analog-output,13/present-value")
hc_1_av @ BACnetExternalReference("bacnet://2500/analog-value,248/present-value")

# DP-F1
dp_f1 @ BACnetExternalReference("bacnet://2500/analog-input,18/present-value")

# TE-Mel
te_mel @ BACnetExternalReference("bacnet://2500/analog-input,15/present-value")

# LL-1
ll_1 @ BACnetExternalReference("bacnet://2500/binary-value,254/present-value")

# D-PAF1
d_paf1_ao = Percent(label="VOLET P.A.F.1A", hasUnit=UNIT.PERCENT)
d_paf1.add_property(d_paf1_ao)
d_paf1_ao @ BACnetExternalReference("bacnet://2500/analog-output,42/present-value")

# 1-E
fan_1e_bo = OnOffCommand(label="A/D EVAC. No.1E")
fan_1e_bv = OnOffStatus(label="STATUT DIG 1E")
fan_1e.add_property(fan_1e_bo)
fan_1e.add_property(fan_1e_bv)
fan_1e_bo @ BACnetExternalReference("bacnet://2500/binary-output,11/present-value")
fan_1e_bv @ BACnetExternalReference("bacnet://2500/binary-value,1/present-value")

# CC-1
cc_1_ao = Percent(label="SERP. REF. No.1A", hasUnit=UNIT.PERCENT)
cc_1_av = Temperature(label="P.C. SERP REF 1A", hasUnit=UNIT.DEG_C)
cc_1_bv1 = OnOffStatus(label="PERM. REF. 1A")
cc_1_bv2 = OnOffStatus(label="PERM REFR 1A")
cc_1.add_property(cc_1_ao)
cc_1.add_property(cc_1_av)
cc_1.add_property(cc_1_bv1)
cc_1.add_property(cc_1_bv2)
cc_1_ao @ BACnetExternalReference("bacnet://2500/analog-output,9/present-value")
cc_1_av @ BACnetExternalReference("bacnet://2500/analog-value,252/present-value")
cc_1_bv1 @ BACnetExternalReference("bacnet://2500/binary-value,147/present-value")
cc_1_bv2 @ BACnetExternalReference("bacnet://2500/binary-value,253/present-value")

# D-Mel
d_mel_ao = Percent(label="VOLET MEL. No.1A", hasUnit=UNIT.PERCENT)
d_mel_av = Temperature(label="P.C. VOLET MEL 1A", hasUnit=UNIT.DEG_C)
d_mel.add_property(d_mel_ao)
d_mel.add_property(d_mel_av)
d_mel_ao @ BACnetExternalReference("bacnet://2500/analog-output,10/present-value")
d_mel_av @ BACnetExternalReference("bacnet://2500/analog-value,251/present-value")

# TE-Ret
te_ret @ BACnetExternalReference("bacnet://2500/analog-input,14/present-value")

# SP-1
sp_1 @ BACnetExternalReference("bacnet://2500/analog-input,17/present-value")
sp_1_av = Pressure(label="P.C. PRES STAT 1A", hasUnit=UNIT.IN_H2O)
sp_1.add_property(sp_1_av)
sp_1_av @ BACnetExternalReference("bacnet://2500/analog-value,250/present-value")

# D-1E
d_1e_ao = Percent(label="VOLET EVAC. No.1E", hasUnit=UNIT.PERCENT)
d_1e.add_property(d_1e_ao)
d_1e_ao @ BACnetExternalReference("bacnet://2500/analog-output,12/present-value")

# HUM-1
hum_1_ai = Amps(label="STATUT HUMI. 1A")
hum_1_ao = Percent(label="HUMIDIFICATEUR 1A", hasUnit=UNIT.PERCENT)
hum_1_av = Percent(label="P.C. HUM 1A", hasUnit=UNIT.PERCENT)
hum_1.add_property(hum_1_ai)
hum_1.add_property(hum_1_ao)
hum_1.add_property(hum_1_av)
hum_1_ai @ BACnetExternalReference("bacnet://2500/analog-input,19/present-value")
hum_1_ao @ BACnetExternalReference("bacnet://2500/analog-output,40/present-value")
hum_1_av @ BACnetExternalReference("bacnet://2500/analog-value,249/present-value")

# 1-A
fan_1a_ai13 = Temperature(label="TEMP. ALIM. No.1A", hasUnit=UNIT.DEG_C)
fan_1a_ai6 = Amps(label="VITESSE ALIM. No. 1A")
fan_1a_bi = OnOffStatus(label="FAUTE VENT. ALIM. 1A")
fan_1a_bo = OnOffCommand(label="A/D VENT. ALM. No.1A")
fan_1a_bv = OnOffStatus(label="STATUT DIG 1A")
fan_1a_sch = Schedule(label="OCC.1A")
fan_1a.add_property(fan_1a_ai13)
fan_1a.add_property(fan_1a_ai6)
fan_1a.add_property(fan_1a_bi)
fan_1a.add_property(fan_1a_bo)
fan_1a.add_property(fan_1a_bv)
fan_1a.add_property(fan_1a_sch)
fan_1a_ai13 @ BACnetExternalReference("bacnet://2500/analog-input,13/present-value")
fan_1a_ai6 @ BACnetExternalReference("bacnet://2500/analog-input,6/present-value")
fan_1a_bi @ BACnetExternalReference("bacnet://2500/binary-input,7/present-value")
fan_1a_bo @ BACnetExternalReference("bacnet://2500/binary-output,5/present-value")
fan_1a_bv @ BACnetExternalReference("bacnet://2500/binary-value,255/present-value")
fan_1a_sch @ BACnetExternalReference("bacnet://2500/schedule,1/present-value")

# HE-Ret
he_ret @ BACnetExternalReference("bacnet://2500/analog-input,16/present-value")

# VFD-1A
vfd_1a_ao = Percent(label="MOD. DRIVE ALM No.1A", hasUnit=UNIT.PERCENT)
vfd_1a.add_property(vfd_1a_ao)
vfd_1a_ao @ BACnetExternalReference("bacnet://2500/analog-output,6/present-value")

# VFD-1R
vfd_1r_ao = Percent(label="MOD. DRIVE RET No.1R", hasUnit=UNIT.PERCENT)
vfd_1r.add_property(vfd_1r_ao)
vfd_1r_ao @ BACnetExternalReference("bacnet://2500/analog-output,8/present-value")

# 1-R
fan_1r_ai = Amps(label="VITESSE RET. No.1A")
fan_1r_bi = OnOffStatus(label="FAUTE VENT. RET. 1A")
fan_1r_bo = OnOffCommand(label="A/D VENT. RET. No.1A")
fan_1r_bv = OnOffStatus(label="STATUT DIG 1R")
fan_1r.add_property(fan_1r_ai)
fan_1r.add_property(fan_1r_bi)
fan_1r.add_property(fan_1r_bo)
fan_1r.add_property(fan_1r_bv)
fan_1r_ai @ BACnetExternalReference("bacnet://2500/analog-input,11/present-value")
fan_1r_bi @ BACnetExternalReference("bacnet://2500/binary-input,12/present-value")
fan_1r_bo @ BACnetExternalReference("bacnet://2500/binary-output,7/present-value")
fan_1r_bv @ BACnetExternalReference("bacnet://2500/binary-value,256/present-value")

if __name__ == "__main__":
    dump(filename="latest_ontology.ttl")
