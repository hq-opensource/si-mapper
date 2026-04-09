from bob.core import bind_model_namespace, dump, S223, UNIT, Junction
from bob.enum import Fluid
from bob.properties import Amps
from bob.properties.force import Pressure
from bob.properties.ratio import Percent
from bob.properties.temperature import Temperature
from bob.properties.states import OnOffStatus

from scratch.assemblage import model_namespace
from bob.equipment.hvac.coil import HotWaterCoil, ChilledWaterCoil
from bob.equipment.hvac.filter import Filter
from bob.sensor.temperature import AirTemperatureSensor
from bob.sensor.pressure import AirDifferentialStaticPressureSensor
from bob.sensor.humidity import AirHumiditySensor

from scratch.electricity.vfd import VFD
from scratch.hvac.damper import Damper
from scratch.hvac.fan import Fan
from scratch.hvac.humidifier import ElectricalHumidifier
from scratch.hvac.valve import ThreeWayMixingSystem

# Namespace setup
model_name, global_ns = model_namespace(__file__)
_namespace = bind_model_namespace(model_name, f"urn:{global_ns}:{model_name}/")

# Equipment Instantiation
hum_1 = ElectricalHumidifier(label="Hum-1")
hc_1 = HotWaterCoil(label="HC-1")
cc_1 = ChilledWaterCoil(label="CC-1")
filter_1 = Filter(label="Filter-1")

paf_upper_damper = Damper(label="PAF-Upper-Damper")
paf_lower_damper = Damper(label="PAF-Lower-Damper")
melange_damper = Damper(label="Melange-Damper")
rav_damper = Damper(label="RAV-Damper")
evac_damper = Damper(label="EVAC-Damper")

fan_1a = Fan(label="1-A")
fan_1r = Fan(label="1-R")
fan_1e = Fan(label="1-E")

vfd_1a = VFD(label="VFD-1-A")
vfd_1r = VFD(label="VFD-1-R")

valve_3wv_cc = ThreeWayMixingSystem(label="3WV-CC")

# Sensors
freeze_stat = AirTemperatureSensor(label="Freeze-Stat")
dp_filter_1 = AirDifferentialStaticPressureSensor(label="DP-Filter-1")
t_mix = AirTemperatureSensor(label="T-MIX")
t_alim = AirTemperatureSensor(label="T-ALIM")
t_ret = AirTemperatureSensor(label="T-RET")
h_ret = AirHumiditySensor(label="H-RET")
sp_1 = AirDifferentialStaticPressureSensor(label="SP-1")

# --- Connections ---

# Electrical Connections
vfd_1a.electricalOutlet >> fan_1a.electricalInlet
vfd_1r.electricalOutlet >> fan_1r.electricalInlet

# Air Supply Chain
mixed_air_junction = Junction(label="MixedAir_Junction", hasMedium=Fluid.Air)
paf_upper_damper.airOutlet >> mixed_air_junction
paf_lower_damper.airOutlet >> mixed_air_junction
melange_damper.airOutlet >> mixed_air_junction

mixed_air_junction >> filter_1.airInlet
filter_1.airOutlet >> cc_1.airInlet
cc_1.airOutlet >> fan_1a.airInlet
fan_1a.airOutlet >> hc_1.airInlet

# Air Return Chain
return_air_junction = Junction(label="ReturnAir_Split", hasMedium=Fluid.Air)
fan_1r.airOutlet >> return_air_junction
return_air_junction >> melange_damper.airInlet
return_air_junction >> rav_damper.airInlet

# Exhaust Air Chain
evac_damper.airOutlet >> fan_1e.airInlet

# Liquid Connections
valve_3wv_cc.fluidOutlet >> cc_1.chilledWaterInlet

# --- Sensor Assignments ---
t_mix % cc_1.airInlet
t_alim % hc_1.airOutlet
t_ret % fan_1r.airInlet
h_ret % fan_1r.airInlet
sp_1 % hc_1.airOutlet
freeze_stat % hc_1.airOutlet
dp_filter_1.add_hasObservationLocation((filter_1.airInlet, filter_1.airOutlet))

# --- BACnet Metadata & Properties ---
hum_1.add_property(Percent(label="P.C. HUM 1A", comment="2500.AV249"))
hum_1.add_property(Percent(label="HUMIDIFICATEUR 1A", comment="2500.AO40"))
hum_1.add_property(Amps(label="STATUT HUMI. 1A", comment="2500.AI19"))

hc_1.add_property(Percent(label="PID SERP. ELEC. 1A", comment="2500.CO9"))
hc_1.add_property(Percent(label="SERP. ELECT. 1A", comment="2500.AO13"))
hc_1.add_property(Temperature(label="PC. SERP. ELEC. 1A", comment="2500.AV248"))

freeze_stat.add_property(OnOffStatus(label="ARRET BAS LIM GEL 1A", comment="2500.BV254"))

dp_filter_1.add_property(Pressure(label="PRESSION FILTRE 1A", comment="2500.AI18"))

t_mix.add_property(Temperature(label="TEMP. MEL. No.1A", comment="2500.AI15"))

paf_upper_damper.add_property(Percent(label="VOLET P.A.F.1A", comment="2500.AO42"))

vfd_1a.add_property(Amps(label="VITESSE ALIM. No. 1A", comment="2500.AI6"))
vfd_1a.add_property(Percent(label="MOD. DRIVE ALM No.1A", comment="2500.AO6"))

t_alim.add_property(Temperature(label="TEMP. ALIM. No.1A", comment="2500.AI13"))

fan_1e.add_property(OnOffStatus(label="STATUT DIG 1E", comment="2500.BV1"))
fan_1e.add_property(OnOffStatus(label="A/D EVAC. No.1E", comment="2500.BO11"))

cc_1.add_property(OnOffStatus(label="PERM REFR 1A", comment="2500.BV253"))
cc_1.add_property(Temperature(label="P.C. SERP REF 1A", comment="2500.AV252"))
cc_1.add_property(Percent(label="SERP. REF. No.1A", comment="2500.AO9"))
cc_1.add_property(OnOffStatus(label="PERM. REF. 1A", comment="2500.BV147"))

evac_damper.add_property(Percent(label="VOLET EVAC. No.1E", comment="2500.AO12"))

h_ret.add_property(Percent(label="HUMIDITE RET. No.1A", comment="2500.AI16"))

t_ret.add_property(Temperature(label="TEMP. RETOUR No.1A", comment="2500.AI14"))

sp_1.add_property(Pressure(label="PRES. STAT. No.1A", comment="2500.AI17"))
sp_1.add_property(Pressure(label="P.C. PRES STAT 1A", comment="2500.AV250"))

fan_1a.add_property(OnOffStatus(label="A/D VENT. ALM. No.1A", comment="2500.BO5"))
fan_1a.add_property(OnOffStatus(label="STATUT DIG 1A", comment="2500.BV255"))

vfd_1r.add_property(Percent(label="MOD. DRIVE RET No.1R", comment="2500.AO8"))
vfd_1r.add_property(Amps(label="VITESSE RET. No.1A", comment="2500.AI11"))

melange_damper.add_property(Percent(label="VOLET MEL. No.1A", comment="2500.AO10"))
melange_damper.add_property(Temperature(label="P.C. VOLET MEL 1A", comment="2500.AV251"))

fan_1r.add_property(OnOffStatus(label="A/D VENT. RET. No.1A", comment="2500.BO7"))
fan_1r.add_property(OnOffStatus(label="STATUT DIG 1R", comment="2500.BV256"))

if __name__ == "__main__":
    dump(filename="latest_ontology.ttl")
