from bob.core import bind_model_namespace, dump, Junction, UNIT
from bob.enum import Fluid, Air
from scratch.assemblage import model_namespace

# Import equipments
from bob.equipment.hvac.coil import HotWaterCoil, ChilledWaterCoil
from bob.equipment.hvac.filter import Filter
from bob.equipment.hvac.humidifier import ElectricalHumidifier, SteamPipe
from bob.equipment.hvac.fan import Fan
from bob.equipment.hvac.damper import Damper
from scratch.electricity.vfd import VFD

# Import sensors
from bob.sensor.temperature import AirTemperatureSensor
from bob.sensor.humidity import AirHumiditySensor
from bob.sensor.pressure import AirDifferentialStaticPressureSensor, PressureSensor

# Bind namespace
model_name, global_ns = model_namespace(__file__)
_namespace = bind_model_namespace(model_name, f"urn:{global_ns}:{model_name}/")

# 1. Equipments
hc_1 = HotWaterCoil(label="HC-1", comment="Heating Coil")
cc_1 = ChilledWaterCoil(label="CC-1", comment="Cooling Coil")
flt_1 = Filter(label="FLT-1", comment="Filter")
hum_1 = ElectricalHumidifier(label="HUM-1", comment="Humidifier")
steam_pipe = SteamPipe(label="HumidifierSteamPipe", comment="Steam pipe for Humidifier")

fan_1_a = Fan(label="1-A", comment="Supply Fan")
vfd_1_a = VFD(label="VFD-1A", comment="VFD for Supply Fan")
# VFD to Fan connection
vfd_1_a.electricalOutlet >> fan_1_a.electricalInlet

fan_1_r = Fan(label="1-R", comment="Return Fan")
vfd_1_r = VFD(label="VFD-1R", comment="VFD for Return Fan")
# VFD to Fan connection
vfd_1_r.electricalOutlet >> fan_1_r.electricalInlet

fan_1_e = Fan(label="1-E", comment="Exhaust Fan")

md_paf_haut = Damper(label="MD-PAF-HAUT", comment="Fresh Air Damper High")
md_paf_bas = Damper(label="MD-PAF-BAS", comment="Fresh Air Damper Low")
md_melange = Damper(label="MD-MELANGE", comment="Mixed Air Damper")
md_retour = Damper(label="MD-RETOUR", comment="Return Air Damper")
md_evac = Damper(label="MD-EVAC", comment="Exhaust Air Damper")

# 2. Sensors
ll_1 = AirTemperatureSensor(label="LL-1", comment="Low Limit Temp Sensor", hasUnit=UNIT.DEG_C)
sh_retour = AirHumiditySensor(label="SH-RETOUR", comment="Return Air Humidity Sensor")
st_alim = AirTemperatureSensor(label="ST-ALIM", comment="Supply Air Temp Sensor", hasUnit=UNIT.DEG_C)
st_retour = AirTemperatureSensor(label="ST-RETOUR", comment="Return Air Temp Sensor", hasUnit=UNIT.DEG_C)
st_melange = AirTemperatureSensor(label="ST-MELANGE", comment="Mixed Air Temp Sensor", hasUnit=UNIT.DEG_C)

sdp_1 = AirDifferentialStaticPressureSensor(label="SDP-1", comment="Filter Diff Pressure", hasUnit=UNIT.PA)
ssp_1 = PressureSensor(label="SSP-1", comment="Static Pressure Sensor", hasUnit=UNIT.PA, ofMedium=Air)

# 3. Duct topology

# --- Supply Path ---
# Fresh air from dampers (MD-PAF-HAUT and MD-PAF-BAS)
mixed_air = Junction(label="MixedAir", hasMedium=Fluid.Air)
md_paf_haut.airOutlet >> mixed_air.airInlet
md_paf_bas.airOutlet >> mixed_air.airInlet
md_melange.airOutlet >> mixed_air.airInlet

mixed_air.airOutlet >> flt_1.airInlet
flt_1.airOutlet >> cc_1.airInlet
cc_1.airOutlet >> fan_1_a.airInlet
fan_1_a.airOutlet >> hc_1.airInlet

# Steam injection
hc_1.airOutlet >> steam_pipe.airInlet
hum_1.steamOutlet >> steam_pipe.steamInlet

# --- Return Path ---
return_air = Junction(label="ReturnAir", hasMedium=Fluid.Air)
return_air.airOutlet >> fan_1_r.airInlet
fan_1_r.airOutlet >> md_melange.airInlet
fan_1_r.airOutlet >> md_retour.airInlet

# --- Exhaust Path ---
md_retour.airOutlet >> fan_1_e.airInlet
fan_1_e.airOutlet >> md_evac.airInlet

# 4. Sensor Connections
st_melange % mixed_air.airOutlet
sdp_1.add_hasObservationLocation((flt_1.airInlet, flt_1.airOutlet))
st_alim % steam_pipe.airOutlet
ll_1 % steam_pipe.airOutlet
ssp_1 % steam_pipe.airOutlet

sh_retour % return_air.airOutlet
st_retour % return_air.airOutlet

if __name__ == "__main__":
    dump()
