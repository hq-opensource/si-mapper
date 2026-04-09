import logging
from bob.core import bind_model_namespace, dump, UNIT, Role, Junction
from bob.externalreference.bacnet import BACnetExternalReference
from bob.enum import Air, Water
from scratch.hvac.fan import Fan
from scratch.electricity.vfd import VFD
from bob.equipment.hvac.coil import WaterCoil, ElectricalHeatingCoil, ChilledWaterCoil
from bob.equipment.hvac.damper import Damper
from bob.equipment.hvac.filter import Filter
from bob.equipment.hvac.humidifier import ElectricalHumidifier
from bob.equipment.hvac.pump import Pump
from scratch.hvac.valve import ThreeWayMixingActuatedProportionalValve
from bob.sensor.pressure import AirDifferentialStaticPressureSensor, PressureSensor
from bob.sensor.temperature import AirTemperatureSensor
from bob.sensor.humidity import AirHumiditySensor
from bob.properties import PercentCommand, OnOffCommand, OnOffStatus, Amps, Pressure, Temperature, RelativeHumidity
from scratch.assemblage import model_namespace

model_name, global_ns = model_namespace(__file__)
_namespace = bind_model_namespace(model_name, f"urn:{global_ns}:{model_name}/")

# 1. Equipment Instantiation
fan_3_A = Fan(label="3-A")
vfd_3_A = VFD(label="VFD-3-A")

fan_3_E = Fan(label="3-E")
vfd_3_E = VFD(label="VFD-3-E")

fan_3_R = Fan(label="3-R")
vfd_3_R = VFD(label="VFD-3-R")

# Coils
hc_1 = WaterCoil(label="HC-1") # Heat Recovery coil in exhaust
hc_2 = WaterCoil(label="HC-2") # Heat Recovery coil in supply
hc_3 = ElectricalHeatingCoil(label="HC-3")
cc_1 = ChilledWaterCoil(label="CC-1")

# Humidifier
hum_1 = ElectricalHumidifier(label="HUM-1")

# Pump & Valve
pmp_1 = Pump(label="PMP-1")
v3w_1 = ThreeWayMixingActuatedProportionalValve(label="V3W-1")

# Dampers
dmp_1 = Damper(label="DMP-1") # Outside Air
dmp_2 = Damper(label="DMP-2") # Exhaust
dmp_3 = Damper(label="DMP-3") # Mixing

# Filters
flt_1 = Filter(label="FLT-1")
flt_2 = Filter(label="FLT-2")

# Sensors
ts_1 = AirTemperatureSensor(label="TS-1", hasUnit=UNIT.DEG_C)
hs_1 = AirHumiditySensor(label="HS-1", hasUnit=UNIT.PERCENT_RH)
hs_2 = AirHumiditySensor(label="HS-2", hasUnit=UNIT.PERCENT_RH)
sps_2 = PressureSensor(label="SPS-2", hasUnit=UNIT.IN_H2O, ofMedium=Air)
sps_3 = PressureSensor(label="SPS-3", hasUnit=UNIT.IN_H2O, ofMedium=Air)
sps_4 = PressureSensor(label="SPS-4", hasUnit=UNIT.IN_H2O, ofMedium=Air)
dps_1 = AirDifferentialStaticPressureSensor(label="DPS-1", hasUnit=UNIT.IN_H2O)
dps_2 = AirDifferentialStaticPressureSensor(label="DPS-2", hasUnit=UNIT.IN_H2O)
lls_1 = AirTemperatureSensor(label="LLS-1", hasUnit=UNIT.DEG_C) # Low Limit Freeze Stat

# Junctions
mixing_junction = Junction(label="MixingJunction", hasMedium=Air)
return_split = Junction(label="ReturnSplitJunction", hasMedium=Air)

# 2. Connections

# VFDs to Fans
vfd_3_A.electricalOutlet >> fan_3_A.electricalInlet
vfd_3_E.electricalOutlet >> fan_3_E.electricalInlet
vfd_3_R.electricalOutlet >> fan_3_R.electricalInlet

# Airflow - Supply
dmp_1.airOutlet >> flt_2.airInlet
flt_2.airOutlet >> hc_2.airInlet
hc_2.airOutlet >> mixing_junction
mixing_junction >> cc_1.airInlet
cc_1.airOutlet >> fan_3_A.airInlet
fan_3_A.airOutlet >> hc_3.airInlet

# Airflow - Return
fan_3_R.airOutlet >> return_split
return_split >> dmp_3.airInlet # To Mixing
dmp_3.airOutlet >> mixing_junction
return_split >> dmp_2.airInlet # To Exhaust

# Airflow - Exhaust
flt_1.airOutlet >> hc_1.airInlet
hc_1.airOutlet >> fan_3_E.airInlet

# Waterflow - Heat Recovery Loop
hc_1.waterOutlet >> pmp_1.fluidInlet
pmp_1.fluidOutlet >> hc_2.waterInlet
hc_2.waterOutlet >> hc_1.waterInlet

# Sensor observations
dps_1 % (flt_1.airInlet, flt_1.airOutlet)
dps_2 % (flt_2.airInlet, flt_2.airOutlet)
ts_1 % hc_3.airOutlet
sps_4 % fan_3_R.airInlet
sps_2 % hc_3.airOutlet
sps_3 % hc_3.airOutlet
lls_1 % hc_2.airOutlet
hs_2 % fan_3_R.airInlet
hs_1 % fan_3_E.airOutlet


# 3. BACnet Properties Mapping

# DMP-3
dmp_3_mod = PercentCommand(label="VOLET MEL. No.3A")
dmp_3.add_property(dmp_3_mod)
dmp_3_mod @ BACnetExternalReference("bacnet://1000/analog-output,23/present-value")

# SPS-4
sps_4 @ BACnetExternalReference("bacnet://1000/analog-input,28/present-value")

# HC-3
hc_3_mod = PercentCommand(label="SERP. ELECT. No.3A")
hc_3.add_property(hc_3_mod)
hc_3_mod @ BACnetExternalReference("bacnet://1000/analog-output,20/present-value")

# 3-E
fan_3_E_fault = OnOffStatus(label="FAUTE VENT. EVAC. 3E")
fan_3_E_speed = PercentCommand(label="VITESSE EVAC. No.3E")
fan_3_E_cmd = OnOffCommand(label="A/D VENT. EVAC. 3E")
fan_3_E.add_property(fan_3_E_fault)
fan_3_E.add_property(fan_3_E_speed)
fan_3_E.add_property(fan_3_E_cmd)
fan_3_E_fault @ BACnetExternalReference("bacnet://1000/binary-input,26/present-value")
fan_3_E_speed @ BACnetExternalReference("bacnet://1000/analog-input,25/present-value")
fan_3_E_cmd @ BACnetExternalReference("bacnet://1000/binary-output,24/present-value")

# TS-1
ts_1 @ BACnetExternalReference("bacnet://1000/analog-input,22/present-value")

# CC-1
cc_1_mod = PercentCommand(label="SERP. REF. No.3A")
cc_1_perm = OnOffCommand(label="PERM. REF. No.3A")
cc_1.add_property(cc_1_mod)
cc_1.add_property(cc_1_perm)
cc_1_mod @ BACnetExternalReference("bacnet://1000/analog-output,19/present-value")
cc_1_perm @ BACnetExternalReference("bacnet://1000/binary-value,144/present-value")

# VFD-3-R
vfd_3_r_mod = PercentCommand(label="MOD. DRIVE RET No.3R")
vfd_3_R.add_property(vfd_3_r_mod)
vfd_3_r_mod @ BACnetExternalReference("bacnet://1000/analog-output,22/present-value")

# VFD-3-A
vfd_3_a_mod = PercentCommand(label="MOD. DRIVE ALM No.3A")
vfd_3_A.add_property(vfd_3_a_mod)
vfd_3_a_mod @ BACnetExternalReference("bacnet://1000/analog-output,18/present-value")

# SPS-2 (has 2 points, we'll map one to the sensor directly, and add another property)
sps_2 @ BACnetExternalReference("bacnet://1000/analog-input,29/present-value")
sps_2_rdc = Pressure(label="PRES. STAT. RDC 3A")
sps_2.add_property(sps_2_rdc)
sps_2_rdc @ BACnetExternalReference("bacnet://1000/analog-input,30/present-value")

# V3W-1
v3w_1_mod = PercentCommand(label="VALVE RECUP. No.3A")
v3w_1_temp = Temperature(label="TEMP. GL. REC. 3A")
v3w_1.add_property(v3w_1_mod)
v3w_1.add_property(v3w_1_temp)
v3w_1_mod @ BACnetExternalReference("bacnet://1000/analog-output,26/present-value")
v3w_1_temp @ BACnetExternalReference("bacnet://1000/analog-input,27/present-value")

# DMP-1
dmp_1_mod = PercentCommand(label="VOLET AIR FRAIS 3A")
dmp_1.add_property(dmp_1_mod)
dmp_1_mod @ BACnetExternalReference("bacnet://1000/analog-output,6/present-value")

# VFD-3-E
vfd_3_e_mod = PercentCommand(label="MOD. DRIVE EV. No.3E")
vfd_3_E.add_property(vfd_3_e_mod)
vfd_3_e_mod @ BACnetExternalReference("bacnet://1000/analog-output,25/present-value")

# 3-A
fan_3_A_status = Amps(label="STATUS ALIM. No.3A")
fan_3_A_fault = OnOffStatus(label="FAUTE VENT. ALIM. 3A")
fan_3_A_cmd = OnOffCommand(label="A/D VENT. ALM. No.3A")
fan_3_A_state = OnOffStatus(label="ETAT DIG. V.A. No.3A")
fan_3_A.add_property(fan_3_A_status)
fan_3_A.add_property(fan_3_A_fault)
fan_3_A.add_property(fan_3_A_cmd)
fan_3_A.add_property(fan_3_A_state)
fan_3_A_status @ BACnetExternalReference("bacnet://1000/analog-input,20/present-value")
fan_3_A_fault @ BACnetExternalReference("bacnet://1000/binary-input,21/present-value")
fan_3_A_cmd @ BACnetExternalReference("bacnet://1000/binary-output,17/present-value")
fan_3_A_state @ BACnetExternalReference("bacnet://1000/binary-value,222/present-value")

# HUM-1
hum_1_cmd = PercentCommand(label="HUMIDIFICATEUR No.3")
hum_1_perm = OnOffCommand(label="PERMISSION HUM.")
hum_1_status = Amps(label="STATUT HUM. 3A")
hum_1.add_property(hum_1_cmd)
hum_1.add_property(hum_1_perm)
hum_1.add_property(hum_1_status)
hum_1_cmd @ BACnetExternalReference("bacnet://1000/analog-output,64/present-value")
hum_1_perm @ BACnetExternalReference("bacnet://1000/binary-value,4/present-value")
hum_1_status @ BACnetExternalReference("bacnet://1000/analog-input,3/present-value")

# HS-2
hs_2 @ BACnetExternalReference("bacnet://1000/analog-input,61/present-value")

# 3-R
fan_3_R_fault = OnOffStatus(label="FAUTE VENT. RET. 3R")
fan_3_R_speed = PercentCommand(label="VITESSE RET. No.3R")
fan_3_R_cmd = OnOffCommand(label="A/D VENT. RET. No.3R")
fan_3_R_state = OnOffStatus(label="ETAT DIG. V.R. No.3R")
fan_3_R.add_property(fan_3_R_fault)
fan_3_R.add_property(fan_3_R_speed)
fan_3_R.add_property(fan_3_R_cmd)
fan_3_R.add_property(fan_3_R_state)
fan_3_R_fault @ BACnetExternalReference("bacnet://1000/binary-input,24/present-value")
fan_3_R_speed @ BACnetExternalReference("bacnet://1000/analog-input,23/present-value")
fan_3_R_cmd @ BACnetExternalReference("bacnet://1000/binary-output,21/present-value")
fan_3_R_state @ BACnetExternalReference("bacnet://1000/binary-value,223/present-value")

# HS-1
hs_1 @ BACnetExternalReference("bacnet://1000/analog-input,60/present-value")
hs_1_temp = Temperature(label="HUMIDITE EVAC.")
hs_1.add_property(hs_1_temp)
hs_1_temp @ BACnetExternalReference("bacnet://1000/analog-input,47/present-value")

# PMP-1
pmp_1_cmd1 = OnOffCommand(label="A/D POMPE PG1 No.3A")
pmp_1_cmd2 = OnOffCommand(label="PMP. GLYC. RECUP. 3A")
pmp_1_status = OnOffStatus(label="STATUS DIG. PMP PG1")
pmp_1.add_property(pmp_1_cmd1)
pmp_1.add_property(pmp_1_cmd2)
pmp_1.add_property(pmp_1_status)
pmp_1_cmd1 @ BACnetExternalReference("bacnet://1000/binary-output,29/present-value")
pmp_1_cmd2 @ BACnetExternalReference("bacnet://1000/binary-output,27/present-value")
pmp_1_status @ BACnetExternalReference("bacnet://1000/binary-value,61/present-value")

if __name__ == "__main__":
    dump(filename="latest_ontology.ttl")
