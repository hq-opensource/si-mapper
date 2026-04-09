import sys
from rdflib import URIRef

from bob.core import bind_model_namespace, dump, PropertyReference, UNIT
from bob.enum import Air
from bob.equipment.hvac.damper import Damper
from bob.equipment.hvac.fan import Fan
from bob.equipment.hvac.filter import Filter
from bob.equipment.hvac.coil import WaterCoil, ElectricalHeatingCoil
from scratch.hvac.humidifier import ElectricalHumidifier
from bob.equipment.hvac.valve import ThreeWayValveMixing
from bob.sensor.temperature import AirTemperatureSensor
from bob.sensor.pressure import AirDifferentialStaticPressureSensor, PressureSensor
from bob.sensor.humidity import AirHumiditySensor
from scratch.electricity.vfd import VFD

# Namespace setup
_namespace = bind_model_namespace("AHU_1", "urn:ahu1:model/")

# Equipments
paf_upper = Damper(label="PAF-Upper-Damper")
paf_upper.add_property(PropertyReference(label="VOLET P.A.F.1A"))

paf_lower = Damper(label="PAF-Lower-Damper")
evac_damper = Damper(label="EVAC-Damper")
evac_damper.add_property(PropertyReference(label="VOLET EVAC. No.1E"))

rav_damper = Damper(label="RAV-Damper")
melange_damper = Damper(label="Melange-Damper")
melange_damper.add_property(PropertyReference(label="VOLET MEL. No.1A"))
melange_damper.add_property(PropertyReference(label="CTRL VOLET MEL 1A"))
melange_damper.add_property(PropertyReference(label="P.C. VOLET MEL 1A"))

filter_1 = Filter(label="Filter-1")

cc_1 = WaterCoil(label="CC-1")
cc_1.add_property(PropertyReference(label="PERM REFR 1A"))
cc_1.add_property(PropertyReference(label="CTRL SERP REFR 1A"))
cc_1.add_property(PropertyReference(label="P.C. SERP REF 1A"))
cc_1.add_property(PropertyReference(label="SERP. REF. No.1A"))
cc_1.add_property(PropertyReference(label="PERM. REF. 1A"))

hc_1 = ElectricalHeatingCoil(label="HC-1")
hc_1.add_property(PropertyReference(label="PID SERP. ELEC. 1A"))
hc_1.add_property(PropertyReference(label="SERP. ELECT. 1A"))
hc_1.add_property(PropertyReference(label="PC. SERP. ELEC. 1A"))

hum_1 = ElectricalHumidifier(label="Hum-1")
hum_1.add_property(PropertyReference(label="CTRL HUMID. 1A"))
hum_1.add_property(PropertyReference(label="P.C. HUM 1A"))
hum_1.add_property(PropertyReference(label="HUMIDIFICATEUR 1A"))
hum_1.add_property(PropertyReference(label="STATUT HUMI. 1A"))

fan_a = Fan(label="1-A")
fan_a.add_property(PropertyReference(label="OCC.1A"))
fan_a.add_property(PropertyReference(label="A/D VENT. ALM. No.1A"))
fan_a.add_property(PropertyReference(label="CTRL VENT. No.1A"))
fan_a.add_property(PropertyReference(label="STATUT DIG 1A"))
fan_a.add_property(PropertyReference(label="FAUTE VENT. ALIM. 1A"))
fan_a.add_property(PropertyReference(label="CALCULS DIVERS 1A M2"))
fan_a.add_property(PropertyReference(label="CTRL.SE.1A"))
fan_a.add_property(PropertyReference(label="ALARMES 1A"))

vfd_a = VFD(label="VFD-1-A")
vfd_a.add_property(PropertyReference(label="VITESSE ALIM. No. 1A"))
vfd_a.add_property(PropertyReference(label="MOD. DRIVE ALM No.1A"))
vfd_a.add_property(PropertyReference(label="CTRL MOD. DRIVE 1A"))

fan_r = Fan(label="1-R")
fan_r.add_property(PropertyReference(label="A/D VENT. RET. No.1A"))
fan_r.add_property(PropertyReference(label="STATUT DIG 1R"))
fan_r.add_property(PropertyReference(label="FAUTE VENT. RET. 1A"))

vfd_r = VFD(label="VFD-1-R")
vfd_r.add_property(PropertyReference(label="MOD. DRIVE RET No.1R"))
vfd_r.add_property(PropertyReference(label="VITESSE RET. No.1A"))

fan_e = Fan(label="1-E")
fan_e.add_property(PropertyReference(label="STATUT DIG 1E"))
fan_e.add_property(PropertyReference(label="A/D EVAC. No.1E"))
fan_e.add_property(PropertyReference(label="CTRL EVAC No.1E"))

three_way_valve = ThreeWayValveMixing(label="3WV-CC")

# Sensors
t_mix = AirTemperatureSensor(label="T-MIX")
t_mix.add_property(PropertyReference(label="TEMP. MEL. No.1A"))

t_alim = AirTemperatureSensor(label="T-ALIM")
t_alim.add_property(PropertyReference(label="TEMP. ALIM. No.1A"))

t_ret = AirTemperatureSensor(label="T-RET")
t_ret.add_property(PropertyReference(label="TEMP. RETOUR No.1A"))

h_ret = AirHumiditySensor(label="H-RET")
h_ret.add_property(PropertyReference(label="HUMIDITE RET. No.1A"))

freeze_stat = AirTemperatureSensor(label="Freeze-Stat")
freeze_stat.add_property(PropertyReference(label="ARRET BAS LIM GEL 1A"))

dp_filter = AirDifferentialStaticPressureSensor(label="DP-Filter-1", hasUnit=UNIT.IN_H2O)
dp_filter.add_property(PropertyReference(label="PRESSION FILTRE 1A"))

sp_1 = PressureSensor(label="SP-1", hasUnit=UNIT.IN_H2O, ofMedium=Air)
sp_1.add_property(PropertyReference(label="PRES. STAT. No.1A"))
sp_1.add_property(PropertyReference(label="P.C. PRES STAT 1A"))

# Connections
# Electrical (VFD -> Fan)
vfd_a.electricalOutlet >> fan_a.electricalInlet
vfd_r.electricalOutlet >> fan_r.electricalInlet

# Air Flow
# Supply Side
paf_upper.airOutlet >> filter_1.airInlet
paf_lower.airOutlet >> filter_1.airInlet
melange_damper.airOutlet >> filter_1.airInlet
filter_1.airOutlet >> cc_1.airInlet
cc_1.airOutlet >> fan_a.airInlet
fan_a.airOutlet >> hc_1.airInlet

# Return Side
fan_r.airOutlet >> rav_damper.airInlet
fan_r.airOutlet >> melange_damper.airInlet

# Exhaust Side
fan_e.airOutlet >> evac_damper.airInlet

# Sensors attach (%)
t_mix % filter_1
t_alim % hc_1
t_ret % fan_r
h_ret % fan_r
freeze_stat % hc_1
dp_filter % filter_1
sp_1 % fan_a

# Final output
if __name__ == "__main__":
    dump(filename="latest_ontology.ttl")
