from bob.core import bind_model_namespace, dump, UNIT, Equipment, PropertyReference, S223, Junction, Fluid
from bob.connections.air import AirInletConnectionPoint, AirOutletConnectionPoint
from scratch.hvac.humidifier import ElectricalHumidifier
from scratch.hvac.damper import ElectricalActuatedProportionalDamper
from scratch.electricity.vfd import VFD
from scratch.hvac.fan import Fan
from bob.equipment.hvac.filter import Filter
from bob.sensor.temperature import AirTemperatureSensor
from bob.sensor.pressure import AirDifferentialStaticPressureSensor, AirStaticPressureSensor
from bob.sensor.humidity import AirHumiditySensor

_namespace = bind_model_namespace("AHU", "urn:ahu/")

class HeatingCoil(Equipment):
    _class_iri = S223.HeatingCoil
    airInlet: AirInletConnectionPoint
    airOutlet: AirOutletConnectionPoint
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.airOutlet.paired_to(self.airInlet)

class CoolingCoil(Equipment):
    _class_iri = S223.CoolingCoil
    airInlet: AirInletConnectionPoint
    airOutlet: AirOutletConnectionPoint
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.airOutlet.paired_to(self.airInlet)

class ThreeWayValve(Equipment):
    _class_iri = S223.Valve

# Instantiate Equipments
hum_1 = ElectricalHumidifier(label="Hum-1")
hum_1.add_property(PropertyReference(label="CTRL HUMID. 1A"))
hum_1.add_property(PropertyReference(label="P.C. HUM 1A", hasUnit=UNIT.PERCENT))
hum_1.add_property(PropertyReference(label="HUMIDIFICATEUR 1A", hasUnit=UNIT.PERCENT))
hum_1.add_property(PropertyReference(label="STATUT HUMI. 1A", hasUnit=UNIT["A"]))

hc_1 = HeatingCoil(label="HC-1")
hc_1.add_property(PropertyReference(label="PID SERP. ELEC. 1A", hasUnit=UNIT.PERCENT))
hc_1.add_property(PropertyReference(label="SERP. ELECT. 1A", hasUnit=UNIT.PERCENT))
hc_1.add_property(PropertyReference(label="PC. SERP. ELEC. 1A", hasUnit=UNIT.DEG_C))

freeze_stat = AirTemperatureSensor(label="Freeze-Stat")
freeze_stat.add_property(PropertyReference(label="ARRET BAS LIM GEL 1A"))

dp_filter_1 = AirDifferentialStaticPressureSensor(label="DP-Filter-1")
dp_filter_1.add_property(PropertyReference(label="PRESSION FILTRE 1A", hasUnit=UNIT["IN_H2O"]))

t_mix = AirTemperatureSensor(label="T-MIX")
t_mix.add_property(PropertyReference(label="TEMP. MEL. No.1A", hasUnit=UNIT.DEG_C))

paf_upper = ElectricalActuatedProportionalDamper(label="PAF-Upper-Damper")
paf_upper.add_property(PropertyReference(label="VOLET P.A.F.1A", hasUnit=UNIT.PERCENT))

vfd_1a = VFD(label="VFD-1-A")
vfd_1a.add_property(PropertyReference(label="VITESSE ALIM. No. 1A", hasUnit=UNIT["A"]))
vfd_1a.add_property(PropertyReference(label="MOD. DRIVE ALM No.1A", hasUnit=UNIT.PERCENT))
vfd_1a.add_property(PropertyReference(label="CTRL MOD. DRIVE 1A"))

t_alim = AirTemperatureSensor(label="T-ALIM")
t_alim.add_property(PropertyReference(label="TEMP. ALIM. No.1A", hasUnit=UNIT.DEG_C))

fan_1e = Fan(label="1-E")
fan_1e.add_property(PropertyReference(label="STATUT DIG 1E"))
fan_1e.add_property(PropertyReference(label="A/D EVAC. No.1E"))
fan_1e.add_property(PropertyReference(label="CTRL EVAC No.1E"))

cc_1 = CoolingCoil(label="CC-1")
cc_1.add_property(PropertyReference(label="PERM REFR 1A"))
cc_1.add_property(PropertyReference(label="CTRL SERP REFR 1A"))
cc_1.add_property(PropertyReference(label="P.C. SERP REF 1A", hasUnit=UNIT.DEG_C))
cc_1.add_property(PropertyReference(label="SERP. REF. No.1A", hasUnit=UNIT.PERCENT))
cc_1.add_property(PropertyReference(label="PERM. REF. 1A"))

evac_damper = ElectricalActuatedProportionalDamper(label="EVAC-Damper")
evac_damper.add_property(PropertyReference(label="VOLET EVAC. No.1E", hasUnit=UNIT.PERCENT))

h_ret = AirHumiditySensor(label="H-RET")
h_ret.add_property(PropertyReference(label="HUMIDITE RET. No.1A", hasUnit=UNIT.PERCENT))

t_ret = AirTemperatureSensor(label="T-RET")
t_ret.add_property(PropertyReference(label="TEMP. RETOUR No.1A", hasUnit=UNIT.DEG_C))

sp_1 = AirStaticPressureSensor(label="SP-1")
sp_1.add_property(PropertyReference(label="PRES. STAT. No.1A", hasUnit=UNIT["IN_H2O"]))
sp_1.add_property(PropertyReference(label="P.C. PRES STAT 1A", hasUnit=UNIT["IN_H2O"]))

fan_1a = Fan(label="1-A")
fan_1a.add_property(PropertyReference(label="OCC.1A"))
fan_1a.add_property(PropertyReference(label="A/D VENT. ALM. No.1A"))
fan_1a.add_property(PropertyReference(label="CTRL VENT. No.1A"))
fan_1a.add_property(PropertyReference(label="STATUT DIG 1A"))
fan_1a.add_property(PropertyReference(label="FAUTE VENT. ALIM. 1A"))
fan_1a.add_property(PropertyReference(label="CALCULS DIVERS 1A M2"))
fan_1a.add_property(PropertyReference(label="CTRL.SE.1A"))
fan_1a.add_property(PropertyReference(label="ALARMES 1A"))

vfd_1r = VFD(label="VFD-1-R")
vfd_1r.add_property(PropertyReference(label="MOD. DRIVE RET No.1R", hasUnit=UNIT.PERCENT))
vfd_1r.add_property(PropertyReference(label="VITESSE RET. No.1A", hasUnit=UNIT["A"]))

rav_damper = ElectricalActuatedProportionalDamper(label="RAV-Damper")

melange_damper = ElectricalActuatedProportionalDamper(label="Melange-Damper")
melange_damper.add_property(PropertyReference(label="VOLET MEL. No.1A", hasUnit=UNIT.PERCENT))
melange_damper.add_property(PropertyReference(label="CTRL VOLET MEL 1A"))
melange_damper.add_property(PropertyReference(label="P.C. VOLET MEL 1A", hasUnit=UNIT.DEG_C))

valve_3wv_cc = ThreeWayValve(label="3WV-CC")

filter_1 = Filter(label="Filter-1")

fan_1r = Fan(label="1-R")
fan_1r.add_property(PropertyReference(label="A/D VENT. RET. No.1A"))
fan_1r.add_property(PropertyReference(label="STATUT DIG 1R"))
fan_1r.add_property(PropertyReference(label="FAUTE VENT. RET. 1A"))

paf_lower = ElectricalActuatedProportionalDamper(label="PAF-Lower-Damper")

# Air Flow Connections
oa_mix_junction = Junction(label="OA_Mix_Junction", hasMedium=Fluid.Air)
paf_upper.airOutlet >> oa_mix_junction
paf_lower.airOutlet >> oa_mix_junction
melange_damper.airOutlet >> oa_mix_junction
oa_mix_junction >> filter_1.airInlet

filter_1.airOutlet >> cc_1.airInlet
cc_1.airOutlet >> fan_1a.airInlet
fan_1a.airOutlet >> hc_1.airInlet
# Note: ElectricalHumidifier omitted from air flow chain to prevent compatibility errors

return_split_junction = Junction(label="Return_Split_Junction", hasMedium=Fluid.Air)
fan_1r.airOutlet >> return_split_junction
return_split_junction >> melange_damper.airInlet
return_split_junction >> rav_damper.airInlet

fan_1e.airOutlet >> evac_damper.airInlet

# Electrical Connections
vfd_1a.electricalOutlet >> fan_1a.electricalInlet
vfd_1r.electricalOutlet >> fan_1r.electricalInlet

# Sensor Connections
t_mix % filter_1.airOutlet
dp_filter_1 % filter_1
t_alim % hc_1.airOutlet
freeze_stat % hc_1.airOutlet
sp_1 % hc_1.airOutlet
h_ret % fan_1r.airInlet
t_ret % fan_1r.airInlet

if __name__ == "__main__":
    dump(filename="latest_ontology.ttl")
