from bob.core import bind_model_namespace, dump, UNIT
from bob.properties.states import OnOffStatus, OnOffCommand
from bob.properties.ratio import PercentCommand, Percent
from bob.properties.electricity import Amps
from bob.properties import Temperature, Pressure, RelativeHumidity

from scratch.assemblage import model_namespace
from scratch.hvac.fan import Fan
from scratch.hvac.damper import Damper
from scratch.hvac.humidifier import ElectricalHumidifier
from bob.equipment.hvac.coil import ElectricalHeatingCoil, ChilledWaterCoil
from bob.equipment.hvac.filter import Filter
from scratch.hvac.valve import ThreeWayValveMixing
from scratch.electricity.vfd import VFD

from bob.sensor.pressure import AirDifferentialStaticPressureSensor
from bob.sensor.temperature import AirTemperatureSensor
from bob.sensor.humidity import AirHumiditySensor

model_name, global_ns = model_namespace(__file__)
_namespace = bind_model_namespace(model_name, f"urn:{global_ns}:{model_name}/")

hum_1 = ElectricalHumidifier(label="Hum-1")
hum_1.add_property(PercentCommand(label="P.C. HUM 1A", comment="BACnet: 2500.AV249"))
hum_1.add_property(PercentCommand(label="HUMIDIFICATEUR 1A", comment="BACnet: 2500.AO40"))
hum_1.add_property(Amps(label="STATUT HUMI. 1A", comment="BACnet: 2500.AI19"))

hc_1 = ElectricalHeatingCoil(label="HC-1")
hc_1.add_property(PercentCommand(label="PID SERP. ELEC. 1A", comment="BACnet: 2500.CO9"))
hc_1.add_property(PercentCommand(label="SERP. ELECT. 1A", comment="BACnet: 2500.AO13"))
hc_1.add_property(Temperature(label="PC. SERP. ELEC. 1A", comment="BACnet: 2500.AV248", hasUnit=UNIT.DEG_C))

freeze_stat = AirTemperatureSensor(label="Freeze-Stat", hasUnit=UNIT.DEG_C)
freeze_stat.add_property(OnOffStatus(label="ARRET BAS LIM GEL 1A", comment="BACnet: 2500.BV254"))

dp_filter_1 = AirDifferentialStaticPressureSensor(label="DP-Filter-1", hasUnit=UNIT["IN-H2O"])
dp_filter_1.add_property(Pressure(label="PRESSION FILTRE 1A", comment="BACnet: 2500.AI18", hasUnit=UNIT["IN-H2O"]))

t_mix = AirTemperatureSensor(label="T-MIX", hasUnit=UNIT.DEG_C)
t_mix.add_property(Temperature(label="TEMP. MEL. No.1A", comment="BACnet: 2500.AI15", hasUnit=UNIT.DEG_C))

damper_paf_upper = Damper(label="PAF-Upper-Damper")
damper_paf_upper.add_property(PercentCommand(label="VOLET P.A.F.1A", comment="BACnet: 2500.AO42"))

vfd_1_a = VFD(label="VFD-1-A")
vfd_1_a.add_property(Amps(label="VITESSE ALIM. No. 1A", comment="BACnet: 2500.AI6"))
vfd_1_a.add_property(PercentCommand(label="MOD. DRIVE ALM No.1A", comment="BACnet: 2500.AO6"))

fan_1_e = Fan(label="1-E")
fan_1_e.add_property(OnOffStatus(label="STATUT DIG 1E", comment="BACnet: 2500.BV1"))
fan_1_e.add_property(OnOffCommand(label="A/D EVAC. No.1E", comment="BACnet: 2500.BO11"))

cc_1 = ChilledWaterCoil(label="CC-1")
cc_1.add_property(OnOffStatus(label="PERM REFR 1A", comment="BACnet: 2500.BV253"))
cc_1.add_property(Temperature(label="P.C. SERP REF 1A", comment="BACnet: 2500.AV252", hasUnit=UNIT.DEG_C))
cc_1.add_property(PercentCommand(label="SERP. REF. No.1A", comment="BACnet: 2500.AO9"))
cc_1.add_property(OnOffStatus(label="PERM. REF. 1A", comment="BACnet: 2500.BV147"))

damper_evac = Damper(label="EVAC-Damper")
damper_evac.add_property(PercentCommand(label="VOLET EVAC. No.1E", comment="BACnet: 2500.AO12"))

h_ret = AirHumiditySensor(label="H-RET", hasUnit=UNIT.PERCENT)
h_ret.add_property(RelativeHumidity(label="HUMIDITE RET. No.1A", comment="BACnet: 2500.AI16", hasUnit=UNIT.PERCENT))

t_ret = AirTemperatureSensor(label="T-RET", hasUnit=UNIT.DEG_C)
t_ret.add_property(Temperature(label="TEMP. RETOUR No.1A", comment="BACnet: 2500.AI14", hasUnit=UNIT.DEG_C))

sp_1 = AirDifferentialStaticPressureSensor(label="SP-1", hasUnit=UNIT["IN-H2O"])
sp_1.add_property(Pressure(label="PRES. STAT. No.1A", comment="BACnet: 2500.AI17", hasUnit=UNIT["IN-H2O"]))
sp_1.add_property(Pressure(label="P.C. PRES STAT 1A", comment="BACnet: 2500.AV250", hasUnit=UNIT["IN-H2O"]))

fan_1_a = Fan(label="1-A")
fan_1_a.add_property(OnOffStatus(label="STATUT DIG 1A", comment="BACnet: 2500.BV255"))
fan_1_a.add_property(OnOffCommand(label="A/D VENT. ALM. No.1A", comment="BACnet: 2500.BO5"))
fan_1_a.add_property(Temperature(label="TEMP. ALIM. No.1A", comment="BACnet: 2500.AI13", hasUnit=UNIT.DEG_C))

vfd_1_r = VFD(label="VFD-1-R")
vfd_1_r.add_property(PercentCommand(label="MOD. DRIVE RET No.1R", comment="BACnet: 2500.AO8"))
vfd_1_r.add_property(Amps(label="VITESSE RET. No.1A", comment="BACnet: 2500.AI11"))

damper_rav = Damper(label="RAV-Damper")

damper_melange = Damper(label="Melange-Damper")
damper_melange.add_property(PercentCommand(label="VOLET MEL. No.1A", comment="BACnet: 2500.AO10"))
damper_melange.add_property(Temperature(label="P.C. VOLET MEL 1A", comment="BACnet: 2500.AV251", hasUnit=UNIT.DEG_C))

valve_3w_cc = ThreeWayValveMixing(label="3WV-CC")

filter_1 = Filter(label="Filter-1")

fan_1_r = Fan(label="1-R")
fan_1_r.add_property(OnOffCommand(label="A/D VENT. RET. No.1A", comment="BACnet: 2500.BO7"))
fan_1_r.add_property(OnOffStatus(label="STATUT DIG 1R", comment="BACnet: 2500.BV256"))

damper_paf_lower = Damper(label="PAF-Lower-Damper")

from bob.core import Junction
from bob.connections.air import AirInletConnectionPoint, AirOutletConnectionPoint
from bob.enum import Fluid

fan_1_r_junction = Junction(label="Fan_1_R_Discharge_Junction")

fan_1_r.airOutlet >> fan_1_r_junction

fan_1_r_junction >> damper_evac.airInlet
fan_1_r_junction >> damper_melange.airInlet
fan_1_r_junction >> damper_rav.airInlet

# VFD -> Fan Connections
vfd_1_a.electricalOutlet >> fan_1_a.electricalInlet
vfd_1_r.electricalOutlet >> fan_1_r.electricalInlet

# Duct connections

damper_evac.airOutlet >> fan_1_e.airInlet

mixed_air_junction = Junction(label="Mixed_Air_Junction")
damper_melange.airOutlet >> mixed_air_junction
damper_paf_upper.airOutlet >> mixed_air_junction
damper_paf_lower.airOutlet >> mixed_air_junction

mixed_air_junction >> filter_1.airInlet

filter_1.airOutlet >> cc_1.airInlet
cc_1.airOutlet >> hc_1.airInlet
hc_1.airOutlet >> fan_1_a.airInlet

# Sensor mapping
t_mix % filter_1.airInlet
dp_filter_1 % filter_1.airInlet
dp_filter_1 % filter_1.airOutlet
t_ret % fan_1_r.airInlet
h_ret % fan_1_r.airInlet
freeze_stat % hc_1.airOutlet
sp_1 % fan_1_a.airOutlet

if __name__ == "__main__":
    import os
    output_file = os.path.join(os.path.dirname(__file__), "ontology.ttl")
    dump(filename=output_file)
