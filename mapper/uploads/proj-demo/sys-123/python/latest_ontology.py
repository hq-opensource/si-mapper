from bob.core import bind_model_namespace, dump, Junction, UNIT
from bob.enum import Fluid, Air
from bob.externalreference.bacnet import BACnetExternalReference

from bob.equipment.hvac.coil import ChilledWaterCoil, ElectricalHeatingCoil
from bob.equipment.hvac.filter import Filter
from scratch.hvac.damper import Damper
from scratch.hvac.fan import Fan
from scratch.hvac.humidifier import ElectricalHumidifier
from scratch.hvac.valve import ThreeWayValveMixing
from scratch.electricity.vfd import VFD

from bob.sensor.temperature import AirTemperatureSensor
from bob.sensor.humidity import AirHumiditySensor
from bob.sensor.pressure import AirDifferentialStaticPressureSensor, PressureSensor
from bob.sensor.sensor import Sensor

from bob.properties.ratio import Percent
from bob.properties import Amps, Pressure, Temperature
from bob.properties.states import OnOffStatus, OnOffCommand

from scratch.assemblage import model_namespace

model_name, global_ns = model_namespace(__file__)
_namespace = bind_model_namespace(model_name, f"urn:{global_ns}:{model_name}/")

# HC-1
hc_1 = ElectricalHeatingCoil(label="HC-1")
prop_hc1_temp = Temperature(label="PC. SERP. ELEC. 1A", comment="BACnet: 2500.AV248")
hc_1.add_property(prop_hc1_temp)
prop_hc1_temp @ BACnetExternalReference("bacnet://2500/analog-value,248/present-value")

prop_hc1_pct = Percent(label="SERP. ELECT. 1A", comment="BACnet: 2500.AO13")
hc_1.add_property(prop_hc1_pct)
prop_hc1_pct @ BACnetExternalReference("bacnet://2500/analog-output,13/present-value")

# Dampers
mix_damper = Damper(label="MIX-DAMPER")
prop_mix_damper_temp = Temperature(label="P.C. VOLET MEL 1A", comment="BACnet: 2500.AV251")
mix_damper.add_property(prop_mix_damper_temp)
prop_mix_damper_temp @ BACnetExternalReference("bacnet://2500/analog-value,251/present-value")

prop_mix_damper_pct = Percent(label="VOLET MEL. No.1A", comment="BACnet: 2500.AO10")
mix_damper.add_property(prop_mix_damper_pct)
prop_mix_damper_pct @ BACnetExternalReference("bacnet://2500/analog-output,10/present-value")

evac_damper = Damper(label="EVAC-DAMPER")
prop_evac_damper_pct = Percent(label="VOLET EVAC. No.1E", comment="BACnet: 2500.AO12")
evac_damper.add_property(prop_evac_damper_pct)
prop_evac_damper_pct @ BACnetExternalReference("bacnet://2500/analog-output,12/present-value")

paf_upper_damper = Damper(label="PAF-UPPER-DAMPER")
prop_paf_upper_pct = Percent(label="VOLET P.A.F.1A", comment="BACnet: 2500.AO42")
paf_upper_damper.add_property(prop_paf_upper_pct)
prop_paf_upper_pct @ BACnetExternalReference("bacnet://2500/analog-output,42/present-value")

paf_lower_damper = Damper(label="PAF-LOWER-DAMPER")
prop_paf_lower_pct = Percent(label="VOLET P.A.F.1A", comment="BACnet: 2500.AO42")
paf_lower_damper.add_property(prop_paf_lower_pct)
prop_paf_lower_pct @ BACnetExternalReference("bacnet://2500/analog-output,42/present-value")

rav_damper = Damper(label="RAV-DAMPER")

# Sensors
mix_temp_1 = AirTemperatureSensor(label="MIX-TEMP-1", comment="BACnet: 2500.AI15")
mix_temp_1.observedProperty @ BACnetExternalReference("bacnet://2500/analog-input,15/present-value")

ret_hum_1 = AirHumiditySensor(label="RET-HUM-1", comment="BACnet: 2500.AI16", hasUnit=UNIT.PERCENT)
ret_hum_1.observedProperty @ BACnetExternalReference("bacnet://2500/analog-input,16/present-value")

ret_temp_1 = AirTemperatureSensor(label="RET-TEMP-1", comment="BACnet: 2500.AI14")
ret_temp_1.observedProperty @ BACnetExternalReference("bacnet://2500/analog-input,14/present-value")

dp_1 = AirDifferentialStaticPressureSensor(label="DP-1", comment="BACnet: 2500.AI18")
dp_1.observedProperty @ BACnetExternalReference("bacnet://2500/analog-input,18/present-value")

static_1 = PressureSensor(label="STATIC-1", hasUnit=UNIT.IN_H2O, ofMedium=Air, comment="BACnet: 2500.AI17")
static_1.observedProperty @ BACnetExternalReference("bacnet://2500/analog-input,17/present-value")
prop_static_1_press = Pressure(label="P.C. PRES STAT 1A", comment="BACnet: 2500.AV250")
static_1.add_property(prop_static_1_press)
prop_static_1_press @ BACnetExternalReference("bacnet://2500/analog-value,250/present-value")

freezestat_1 = Sensor(label="FREEZESTAT-1", comment="BACnet: 2500.BV254")
prop_freezestat_1_status = OnOffStatus(label="ARRET BAS LIM GEL 1A", comment="BACnet: 2500.BV254")
freezestat_1.add_property(prop_freezestat_1_status)
prop_freezestat_1_status @ BACnetExternalReference("bacnet://2500/binary-value,254/present-value")

# VFDs
vfd_1_a = VFD(label="VFD-1-A")
prop_vfd_1_a_pct = Percent(label="MOD. DRIVE ALM No.1A", comment="BACnet: 2500.AO6")
vfd_1_a.add_property(prop_vfd_1_a_pct)
prop_vfd_1_a_pct @ BACnetExternalReference("bacnet://2500/analog-output,6/present-value")

vfd_1_r = VFD(label="VFD-1-R")
prop_vfd_1_r_pct = Percent(label="MOD. DRIVE RET No.1R", comment="BACnet: 2500.AO8")
vfd_1_r.add_property(prop_vfd_1_r_pct)
prop_vfd_1_r_pct @ BACnetExternalReference("bacnet://2500/analog-output,8/present-value")

# Fans
fan_1_e = Fan(label="1-E")
prop_fan_1_e_status = OnOffStatus(label="STATUT DIG 1E", comment="BACnet: 2500.BV1")
fan_1_e.add_property(prop_fan_1_e_status)
prop_fan_1_e_status @ BACnetExternalReference("bacnet://2500/binary-value,1/present-value")

prop_fan_1_e_cmd = OnOffCommand(label="A/D EVAC. No.1E", comment="BACnet: 2500.BO11")
fan_1_e.add_property(prop_fan_1_e_cmd)
prop_fan_1_e_cmd @ BACnetExternalReference("bacnet://2500/binary-output,11/present-value")

fan_1_a = Fan(label="1-A")
prop_fan_1_a_status = OnOffStatus(label="STATUT DIG 1A", comment="BACnet: 2500.BV255")
fan_1_a.add_property(prop_fan_1_a_status)
prop_fan_1_a_status @ BACnetExternalReference("bacnet://2500/binary-value,255/present-value")

prop_fan_1_a_cmd = OnOffCommand(label="A/D VENT. ALM. No.1A", comment="BACnet: 2500.BO5")
fan_1_a.add_property(prop_fan_1_a_cmd)
prop_fan_1_a_cmd @ BACnetExternalReference("bacnet://2500/binary-output,5/present-value")

prop_fan_1_a_amps = Amps(label="VITESSE ALIM. No. 1A", comment="BACnet: 2500.AI6")
fan_1_a.add_property(prop_fan_1_a_amps)
prop_fan_1_a_amps @ BACnetExternalReference("bacnet://2500/analog-input,6/present-value")

prop_fan_1_a_fault = OnOffStatus(label="FAUTE VENT. ALIM. 1A", comment="BACnet: 2500.BI7")
fan_1_a.add_property(prop_fan_1_a_fault)
prop_fan_1_a_fault @ BACnetExternalReference("bacnet://2500/binary-input,7/present-value")

fan_1_r = Fan(label="1-R")
prop_fan_1_r_status = OnOffStatus(label="STATUT DIG 1R", comment="BACnet: 2500.BV256")
fan_1_r.add_property(prop_fan_1_r_status)
prop_fan_1_r_status @ BACnetExternalReference("bacnet://2500/binary-value,256/present-value")

prop_fan_1_r_amps = Amps(label="VITESSE RET. No.1A", comment="BACnet: 2500.AI11")
fan_1_r.add_property(prop_fan_1_r_amps)
prop_fan_1_r_amps @ BACnetExternalReference("bacnet://2500/analog-input,11/present-value")

prop_fan_1_r_fault = OnOffStatus(label="FAUTE VENT. RET. 1A", comment="BACnet: 2500.BI12")
fan_1_r.add_property(prop_fan_1_r_fault)
prop_fan_1_r_fault @ BACnetExternalReference("bacnet://2500/binary-input,12/present-value")

prop_fan_1_r_cmd = OnOffCommand(label="A/D VENT. RET. No.1A", comment="BACnet: 2500.BO7")
fan_1_r.add_property(prop_fan_1_r_cmd)
prop_fan_1_r_cmd @ BACnetExternalReference("bacnet://2500/binary-output,7/present-value")

# Coils & other equipment
cc_1 = ChilledWaterCoil(label="CC-1")
prop_cc_1_perm = OnOffStatus(label="PERM. REF. 1A", comment="BACnet: 2500.BV147")
cc_1.add_property(prop_cc_1_perm)
prop_cc_1_perm @ BACnetExternalReference("bacnet://2500/binary-value,147/present-value")

prop_cc_1_temp = Temperature(label="P.C. SERP REF 1A", comment="BACnet: 2500.AV252")
cc_1.add_property(prop_cc_1_temp)
prop_cc_1_temp @ BACnetExternalReference("bacnet://2500/analog-value,252/present-value")

prop_cc_1_pct = Percent(label="SERP. REF. No.1A", comment="BACnet: 2500.AO9")
cc_1.add_property(prop_cc_1_pct)
prop_cc_1_pct @ BACnetExternalReference("bacnet://2500/analog-output,9/present-value")

prop_cc_1_perm2 = OnOffStatus(label="PERM REFR 1A", comment="BACnet: 2500.BV253")
cc_1.add_property(prop_cc_1_perm2)
prop_cc_1_perm2 @ BACnetExternalReference("bacnet://2500/binary-value,253/present-value")

valve_cc_1 = ThreeWayValveMixing(label="VALVE-CC-1")

filter_1 = Filter(label="FILTER-1")

hum_1 = ElectricalHumidifier(label="HUM-1")
prop_hum_1_amps = Amps(label="STATUT HUMI. 1A", comment="BACnet: 2500.AI19")
hum_1.add_property(prop_hum_1_amps)
prop_hum_1_amps @ BACnetExternalReference("bacnet://2500/analog-input,19/present-value")

prop_hum_1_pct = Percent(label="P.C. HUM 1A", comment="BACnet: 2500.AV249")
hum_1.add_property(prop_hum_1_pct)
prop_hum_1_pct @ BACnetExternalReference("bacnet://2500/analog-value,249/present-value")

prop_hum_1_pct2 = Percent(label="HUMIDIFICATEUR 1A", comment="BACnet: 2500.AO40")
hum_1.add_property(prop_hum_1_pct2)
prop_hum_1_pct2 @ BACnetExternalReference("bacnet://2500/analog-output,40/present-value")


# Connections / Air Flow
j_fresh_air = Junction(label="Fresh Air Junction", hasMedium=Fluid.Air)
paf_upper_damper >> j_fresh_air
paf_lower_damper >> j_fresh_air

j_mix = Junction(label="Mixed Air Junction", hasMedium=Fluid.Air)
j_fresh_air >> j_mix
mix_damper >> j_mix

j_return_split = Junction(label="Return Split Junction", hasMedium=Fluid.Air)
fan_1_r >> j_return_split
j_return_split >> mix_damper
j_return_split >> rav_damper

rav_damper >> fan_1_e
fan_1_e >> evac_damper

j_mix >> filter_1
filter_1 >> cc_1
cc_1 >> fan_1_a
fan_1_a >> hc_1

# Sensors wiring
mix_temp_1 % filter_1
ret_hum_1 % fan_1_r
ret_temp_1 % fan_1_r
freezestat_1 % cc_1
static_1 % fan_1_a
dp_1 % filter_1

# Electrical / Drives
vfd_1_a.electricalOutlet >> fan_1_a.electricalInlet
vfd_1_r.electricalOutlet >> fan_1_r.electricalInlet

if __name__ == "__main__":
    dump(filename="latest_ontology.ttl")
