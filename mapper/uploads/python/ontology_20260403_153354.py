import logging

from bob.core import bind_model_namespace, dump, UNIT, Junction
from bob.properties.ratio import Percent
from bob.properties.electricity import Amps

from scratch.assemblage import model_namespace

from bob.equipment.hvac.coil import HotWaterCoil, ChilledWaterCoil
from scratch.hvac.humidifier import ElectricalHumidifier
from bob.sensor.temperature import AirTemperatureSensor
from bob.sensor.pressure import AirDifferentialStaticPressureSensor
from bob.sensor.humidity import AirHumiditySensor
from scratch.hvac.damper import Damper
from scratch.hvac.fan import Fan
from scratch.electricity.vfd import VFD
from bob.equipment.hvac.filter import Filter
from scratch.hvac.valve import ThreeWayMixingActuatedProportionalValve

# logging
_log = logging.getLogger(__name__)

model_name, global_ns = model_namespace(__file__)
_namespace = bind_model_namespace(model_name, f"urn:{global_ns}:{model_name}/")

def main():
    hum_1 = ElectricalHumidifier(label="Hum-1")
    hc_1 = HotWaterCoil(label="HC-1")
    cc_1 = ChilledWaterCoil(label="CC-1")
    
    freeze_stat = AirTemperatureSensor(label="Freeze-Stat", hasUnit=UNIT.DEG_C)
    dp_filter = AirDifferentialStaticPressureSensor(label="DP-Filter-1", hasUnit=UNIT.PA)
    t_mix = AirTemperatureSensor(label="T-MIX", hasUnit=UNIT.DEG_C)
    t_alim = AirTemperatureSensor(label="T-ALIM", hasUnit=UNIT.DEG_C)
    t_ret = AirTemperatureSensor(label="T-RET", hasUnit=UNIT.DEG_C)
    h_ret = AirHumiditySensor(label="H-RET", hasUnit=UNIT.PERCENT)
    sp_1 = AirDifferentialStaticPressureSensor(label="SP-1", hasUnit=UNIT.PA)
    
    paf_upper = Damper(label="PAF-Upper-Damper")
    paf_lower = Damper(label="PAF-Lower-Damper")
    melange = Damper(label="Melange-Damper")
    evac = Damper(label="EVAC-Damper")
    rav = Damper(label="RAV-Damper")
    
    fan_1_a = Fan(label="1-A")
    vfd_1_a = VFD(label="VFD-1-A")
    
    fan_1_r = Fan(label="1-R")
    vfd_1_r = VFD(label="VFD-1-R")
    
    fan_1_e = Fan(label="1-E")
    
    filter_1 = Filter(label="Filter-1")
    valve_3wv = ThreeWayMixingActuatedProportionalValve(label="3WV-CC")

    mix_junc_1 = Junction(label="Mix-Junction-1")
    mix_junc_2 = Junction(label="Mix-Junction-2")

    # Wiring
    vfd_1_a.electricalOutlet >> fan_1_a.electricalInlet
    vfd_1_r.electricalOutlet >> fan_1_r.electricalInlet
    
    paf_upper.airOutlet >> mix_junc_1
    paf_lower.airOutlet >> mix_junc_1
    melange.airOutlet >> mix_junc_1
    
    mix_junc_1 >> filter_1.airInlet
    
    filter_1.airOutlet >> cc_1.airInlet
    cc_1.airOutlet >> fan_1_a.airInlet
    fan_1_a.airOutlet >> hc_1.airInlet
    
    fan_1_r.airOutlet >> mix_junc_2
    mix_junc_2 >> melange.airInlet
    mix_junc_2 >> evac.airInlet
    mix_junc_2 >> rav.airInlet
    evac.airOutlet >> fan_1_e.airInlet
    
    # Sensors
    dp_filter % filter_1
    t_mix % filter_1.airInlet
    t_ret % fan_1_r.airInlet
    h_ret % fan_1_r.airInlet
    freeze_stat % hc_1.airOutlet
    t_alim % hc_1.airOutlet
    sp_1 % hc_1.airOutlet

    # BACnet attributes attached directly
    hum_1.add_property(Percent(label="HUMIDIFICATEUR 1A", comment="BACnet: 2500.AO40"))
    hum_1.add_property(Percent(label="CTRL HUMID. 1A", comment="BACnet: 2500.PG16"))
    hum_1.add_property(Amps(label="STATUT HUMI. 1A", comment="BACnet: 2500.AI19"))
    hum_1.add_property(Percent(label="P.C. HUM 1A", comment="BACnet: 2500.AV249"))
    
    hc_1.add_property(Percent(label="CTRL.SE.1A", comment="BACnet: 2500.PG18"))
    hc_1.add_property(Percent(label="PC. SERP. ELEC. 1A", comment="BACnet: 2500.AV248"))
    hc_1.add_property(Percent(label="PID SERP. ELEC. 1A", comment="BACnet: 2500.CO9"))
    hc_1.add_property(Percent(label="SERP. ELECT. 1A", comment="BACnet: 2500.AO13"))
    
    freeze_stat.add_property(Percent(label="ARRET BAS LIM GEL 1A", comment="BACnet: 2500.BV254"))
    dp_filter.add_property(Percent(label="PRESSION FILTRE 1A", comment="BACnet: 2500.AI18"))
    t_mix.add_property(Percent(label="TEMP. MEL. No.1A", comment="BACnet: 2500.AI15"))
    paf_upper.add_property(Percent(label="VOLET P.A.F.1A", comment="BACnet: 2500.AO42"))
    
    vfd_1_a.add_property(Percent(label="MOD. DRIVE ALM No.1A", comment="BACnet: 2500.AO6"))
    vfd_1_a.add_property(Percent(label="CTRL MOD. DRIVE 1A", comment="BACnet: 2500.PG12"))
    
    t_alim.add_property(Percent(label="TEMP. ALIM. No.1A", comment="BACnet: 2500.AI13"))
    
    fan_1_e.add_property(Percent(label="STATUT DIG 1E", comment="BACnet: 2500.BV1"))
    fan_1_e.add_property(Percent(label="A/D EVAC. No.1E", comment="BACnet: 2500.BO11"))
    fan_1_e.add_property(Percent(label="CTRL EVAC No.1E", comment="BACnet: 2500.PG15"))
    
    cc_1.add_property(Percent(label="PERM. REF. 1A", comment="BACnet: 2500.BV147"))
    cc_1.add_property(Percent(label="PERM REFR 1A", comment="BACnet: 2500.BV253"))
    cc_1.add_property(Percent(label="CTRL SERP REFR 1A", comment="BACnet: 2500.PG13"))
    cc_1.add_property(Percent(label="SERP. REF. No.1A", comment="BACnet: 2500.AO9"))
    cc_1.add_property(Percent(label="P.C. SERP REF 1A", comment="BACnet: 2500.AV252"))
    
    evac.add_property(Percent(label="VOLET EVAC. No.1E", comment="BACnet: 2500.AO12"))
    h_ret.add_property(Percent(label="HUMIDITE RET. No.1A", comment="BACnet: 2500.AI16"))
    t_ret.add_property(Percent(label="TEMP. RETOUR No.1A", comment="BACnet: 2500.AI14"))
    
    sp_1.add_property(Percent(label="PRES. STAT. No.1A", comment="BACnet: 2500.AI17"))
    sp_1.add_property(Percent(label="P.C. PRES STAT 1A", comment="BACnet: 2500.AV250"))
    
    fan_1_a.add_property(Percent(label="FAUTE VENT. ALIM. 1A", comment="BACnet: 2500.BI7"))
    fan_1_a.add_property(Percent(label="CALCULS DIVERS 1A M2", comment="BACnet: 2500.PG10"))
    fan_1_a.add_property(Percent(label="OCC.1A", comment="BACnet: 2500.SCH1"))
    fan_1_a.add_property(Amps(label="VITESSE ALIM. No. 1A", comment="BACnet: 2500.AI6"))
    fan_1_a.add_property(Percent(label="ALARMES 1A", comment="BACnet: 2500.PG17"))
    fan_1_a.add_property(Percent(label="CTRL VENT. No.1A", comment="BACnet: 2500.PG11"))
    fan_1_a.add_property(Percent(label="STATUT DIG 1A", comment="BACnet: 2500.BV255"))
    fan_1_a.add_property(Percent(label="A/D VENT. ALM. No.1A", comment="BACnet: 2500.BO5"))
    
    vfd_1_r.add_property(Percent(label="MOD. DRIVE RET No.1R", comment="BACnet: 2500.AO8"))
    
    melange.add_property(Percent(label="CTRL VOLET MEL 1A", comment="BACnet: 2500.PG14"))
    melange.add_property(Percent(label="VOLET MEL. No.1A", comment="BACnet: 2500.AO10"))
    melange.add_property(Percent(label="P.C. VOLET MEL 1A", comment="BACnet: 2500.AV251"))
    
    fan_1_r.add_property(Percent(label="STATUT DIG 1R", comment="BACnet: 2500.BV256"))
    fan_1_r.add_property(Percent(label="FAUTE VENT. RET. 1A", comment="BACnet: 2500.BI12"))
    fan_1_r.add_property(Amps(label="VITESSE RET. No.1A", comment="BACnet: 2500.AI11"))
    fan_1_r.add_property(Percent(label="A/D VENT. RET. No.1A", comment="BACnet: 2500.BO7"))
    
    paf_lower.add_property(Percent(label="VOLET P.A.F.1A", comment="BACnet: 2500.AO42"))

if __name__ == "__main__":
    main()
    dump(filename="latest_ontology.ttl")
