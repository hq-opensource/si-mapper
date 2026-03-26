from bob.equipment.hvac.fan import Fan
from bob.equipment.hvac.coil import HotWaterCoil, ChilledWaterCoil
from bob.equipment.hvac.damper import Damper
from bob.equipment.hvac.filter import Filter
from bob.equipment.hvac.humidifier import Humidifier
from bob.equipment.electricity.vfd import VFD
from bob.sensor.temperature import AirTemperatureSensor
from bob.sensor.humidity import AirHumiditySensor
from bob.sensor.pressure import AirDifferentialStaticPressureSensor, PressureSensor
from bob.connections.air import AirConnection
from bob.core import System, UNIT, dump
from bob.enum import Air

# System
system = System(label="HVAC System")

# Equipment
hc_1 = HotWaterCoil(label="HC-1")
cc_1 = ChilledWaterCoil(label="CC-1")
fan_1_e = Fan(label="1-E")
fan_1_a = Fan(label="1-A")
fan_1_r = Fan(label="1-R")
md_paf_bas = Damper(label="MD-PAF-BAS")
md_paf_haut = Damper(label="MD-PAF-HAUT")
md_melange = Damper(label="MD-MELANGE")
md_retour = Damper(label="MD-RETOUR")
md_evac = Damper(label="MD-EVAC")
flt_1 = Filter(label="FLT-1")
hum_1 = Humidifier(label="HUM-1")
vfd_1r = VFD(label="VFD-1R")
vfd_1a = VFD(label="VFD-1A")

# Sensors
ll_1 = AirTemperatureSensor(label="LL-1", hasUnit=UNIT.DEG_C)
sh_retour = AirHumiditySensor(label="SH-RETOUR")
st_alim = AirTemperatureSensor(label="ST-ALIM", hasUnit=UNIT.DEG_C)
st_retour = AirTemperatureSensor(label="ST-RETOUR", hasUnit=UNIT.DEG_C)
st_melange = AirTemperatureSensor(label="ST-MELANGE", hasUnit=UNIT.DEG_C)
sdp_1 = AirDifferentialStaticPressureSensor(label="SDP-1", hasUnit=UNIT.PA)
ssp_1 = PressureSensor(label="SSP-1", hasUnit=UNIT.PA, ofMedium=Air)

# Connections
hd_4 = AirConnection(label="HD-4")
hd_2 = AirConnection(label="HD-2")
hd_1 = AirConnection(label="HD-1")
return_air = AirConnection(label="ReturnAir")
exhaust_air = AirConnection(label="ExhaustAir")
supply_air = AirConnection(label="SupplyAir")

# Add to system
system > hc_1
system > cc_1
system > fan_1_e
system > fan_1_a
system > fan_1_r
system > md_paf_bas
system > md_paf_haut
system > md_melange
system > md_retour
system > md_evac
system > flt_1
system > hum_1
system > vfd_1r
system > vfd_1a
system > ll_1
system > sh_retour
system > st_alim
system > st_retour
system > st_melange
system > sdp_1
system > ssp_1

# Airflow Path
# Fresh Air
md_paf_bas >> hd_4
md_paf_haut >> hd_4

# Return Air
return_air >> fan_1_r
fan_1_r >> hd_2
hd_2 >> md_retour

# Recirculation
hd_2 >> md_melange
md_melange >> hd_4

# Supply Air
hd_4 >> flt_1
flt_1 >> cc_1
cc_1 >> fan_1_a
fan_1_a >> hc_1
hc_1 >> supply_air

# Exhaust Air
exhaust_air >> fan_1_e
fan_1_e >> hd_1
hd_1 >> md_evac

# Sensor relationships
st_retour % return_air
sh_retour % return_air
st_melange % flt_1.airOutlet
st_alim % supply_air
ll_1 % supply_air
ssp_1 % supply_air
sdp_1 % (flt_1.airInlet, flt_1.airOutlet)

# VFD relationships
vfd_1r.electricalOutlet >> fan_1_r.electricalInlet
vfd_1a.electricalOutlet >> fan_1_a.electricalInlet

# Dump the ontology
dump()
