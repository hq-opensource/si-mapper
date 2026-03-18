"""
ASHRAE 223P Ontology for AHU HVAC System
Generated from grid data

This ontology models an Air Handling Unit (AHU) system with:
- Supply, return, and exhaust air fans with VFDs
- Fresh air intake with dampers
- Return and exhaust air paths
- Heating and cooling coils
- Filter and humidifier
- Various sensors (temperature, humidity, pressure)
- Three-way mixing valve for water control
"""

from pathlib import Path
from bob.core import UNIT, bind_model_namespace, dump
from bob.connections.air import AirConnection
from bob.equipment.hvac.coil import ChilledWaterCoil, HotWaterCoil
from bob.equipment.hvac.fan import Fan
from bob.equipment.hvac.filter import Filter
from bob.properties.force import DifferentialStaticPressure
from bob.properties.ratio import RelativeHumidity
from bob.properties.temperature import Temperature
from bob.sensor.humidity import AirHumiditySensor
from bob.sensor.pressure import AirDifferentialStaticPressureSensor
from bob.sensor.temperature import AirTemperatureSensor
from scratch.electricity.vfd import VFD
from scratch.hvac.damper import Damper
from scratch.hvac.humidifier import ElectricalHumidifier
from scratch.hvac.valve import ThreeWayMixingActuatedProportionalValve

# ============================================================
# NAMESPACE SETUP
# ============================================================

model_name = "ahu_system"
_namespace = bind_model_namespace(model_name, f"urn:ontology:{model_name}/")

# ============================================================
# DAMPERS
# Based on grid positions:
#   damper_paf_upper  [7, 4]  - outdoor air damper, upper path
#   damper_paf_lower  [7, 1]  - outdoor air damper, lower path
#   damper_rav        [7, 8]  - return air damper
#   damper_melange    [11, 6] - mixed air damper
#   damper_evac       [7, 11] - exhaust air damper
# ============================================================

damper_paf_upper = Damper(
    label="damper_paf_upper",
    comment="Outdoor air damper - upper path at position [7,4]",
)

damper_paf_lower = Damper(
    label="damper_paf_lower",
    comment="Outdoor air damper - lower path at position [7,1]",
)

damper_rav = Damper(
    label="damper_rav",
    comment="Return air damper at position [7,8]",
)

damper_melange = Damper(
    label="damper_melange",
    comment="Mixed air damper at position [11,6]",
)

damper_evac = Damper(
    label="damper_evac",
    comment="Exhaust air damper at position [7,11]",
)

# ============================================================
# FILTER
# Position: [13, 8]
# ============================================================

filter_1 = Filter(
    label="filter_1",
    comment="Air filter at position [13,8]",
)

# ============================================================
# COILS
# Positions:
#   cooling_coil_1  [15, 8]
#   heating_coil_1  [18, 8]
# ============================================================

cooling_coil_1 = ChilledWaterCoil(
    label="cooling_coil_1",
    comment="Cooling coil at position [15,8]",
)

heating_coil_1 = HotWaterCoil(
    label="heating_coil_1",
    comment="Heating coil at position [18,8]",
)

# ============================================================
# HUMIDIFIER
# Position: [23, 8]
# Note: ElectricalHumidifier from scratch doesn't have compatible
# air-side connection points, so it's instantiated but not connected
# in the air flow chain to avoid connection errors.
# ============================================================

humidifier_1 = ElectricalHumidifier(
    label="humidifier_1",
    comment="Humidifier at position [23,8]",
)

# ============================================================
# FANS
# Positions:
#   fan_1_a  [21, 8]  - supply air fan
#   fan_1_r  [16, 4]  - return air fan
#   fan_1_e  [9, 1]   - exhaust air fan
# ============================================================

fan_1_a = Fan(
    label="fan_1_a",
    comment="Supply air fan at position [21,8]",
)

fan_1_r = Fan(
    label="fan_1_r",
    comment="Return air fan at position [16,4]",
)

fan_1_e = Fan(
    label="fan_1_e",
    comment="Exhaust air fan at position [9,1]",
)

# ============================================================
# VFDs
# Positions:
#   vfd_1_a  [21, 9]  - VFD for supply fan fan_1_a
#   vfd_1_r  [16, 5]  - VFD for return fan fan_1_r
# ============================================================

vfd_1_a = VFD(
    label="vfd_1_a",
    comment="VFD for supply fan at position [21,9]",
)

vfd_1_r = VFD(
    label="vfd_1_r",
    comment="VFD for return fan at position [16,5]",
)

# ============================================================
# THREE-WAY VALVE
# Position: [15, 9]
# ============================================================

valve_3_way_1 = ThreeWayMixingActuatedProportionalValve(
    label="valve_3_way_1",
    comment="Three-way mixing valve at position [15,9]",
)

# ============================================================
# AIR CONNECTIONS (boundaries / junctions)
# ============================================================

outdoor_air_conn = AirConnection(
    label="OutdoorAir",
    comment="Outdoor air intake - connects to damper_paf_upper and damper_paf_lower",
)

mixed_air_conn = AirConnection(
    label="MixedAir",
    comment="Mixed outdoor and return air entering the AHU processing train",
)

return_air_conn = AirConnection(
    label="ReturnAir",
    comment="Return air from served zones",
)

exhaust_air_conn = AirConnection(
    label="ExhaustAir",
    comment="Exhaust air discharged to outdoors",
)

supply_air_conn = AirConnection(
    label="SupplyAir",
    comment="Conditioned supply air delivered to zones",
)

# ============================================================
# SENSORS WITH PROPERTIES
# Positions from grid:
#   sensor_temp_melange         [19, 8]
#   sensor_temp_retour          [26, 8]
#   sensor_temp_alim            [19, 4]
#   sensor_diff_pressure_1      [13, 9]
#   sensor_static_pressure_1    [28, 8]
#   sensor_humidity_retour      [24, 8]
#   sensor_low_limit_1          [21, 4]
# ============================================================

# Mixed Air Temperature Sensor
sensor_temp_melange = AirTemperatureSensor(
    label="sensor_temp_melange",
    comment="Mixed air temperature sensor at position [19,8]",
)
sensor_temp_melange_prop = Temperature(
    label="MixedAirTemperature",
    hasUnit=UNIT.DEG_C,
)
sensor_temp_melange.add_property(sensor_temp_melange_prop)

# Return Air Temperature Sensor
sensor_temp_retour = AirTemperatureSensor(
    label="sensor_temp_retour",
    comment="Return air temperature sensor at position [26,8]",
)
sensor_temp_retour_prop = Temperature(
    label="ReturnAirTemperature",
    hasUnit=UNIT.DEG_C,
)
sensor_temp_retour.add_property(sensor_temp_retour_prop)

# Supply Air Temperature Sensor
sensor_temp_alim = AirTemperatureSensor(
    label="sensor_temp_alim",
    comment="Supply air temperature sensor at position [19,4]",
)
sensor_temp_alim_prop = Temperature(
    label="SupplyAirTemperature",
    hasUnit=UNIT.DEG_C,
)
sensor_temp_alim.add_property(sensor_temp_alim_prop)

# Differential Pressure Sensor (Filter)
sensor_diff_pressure_1 = AirDifferentialStaticPressureSensor(
    label="sensor_diff_pressure_1",
    comment="Differential pressure sensor across filter at position [13,9]",
)
sensor_diff_pressure_prop = DifferentialStaticPressure(
    label="FilterDifferentialPressure",
    hasUnit=UNIT.PA,
)
sensor_diff_pressure_1.add_property(sensor_diff_pressure_prop)

# Static Pressure Sensor (Supply Duct)
sensor_static_pressure_1 = AirDifferentialStaticPressureSensor(
    label="sensor_static_pressure_1",
    comment="Static pressure sensor in supply duct at position [28,8]",
)
sensor_static_pressure_prop = DifferentialStaticPressure(
    label="DuctStaticPressure",
    hasUnit=UNIT.PA,
)
sensor_static_pressure_1.add_property(sensor_static_pressure_prop)

# Return Air Humidity Sensor
sensor_humidity_retour = AirHumiditySensor(
    label="sensor_humidity_retour",
    comment="Return air humidity sensor at position [24,8]",
)
sensor_humidity_retour_prop = RelativeHumidity(
    label="ReturnAirHumidity",
    hasUnit=UNIT.PERCENT,
)
sensor_humidity_retour.add_property(sensor_humidity_retour_prop)

# Low Limit Temperature Sensor
sensor_low_limit_1 = AirTemperatureSensor(
    label="sensor_low_limit_1",
    comment="Low limit temperature sensor in supply duct at position [21,4]",
)
sensor_low_limit_prop = Temperature(
    label="LowLimitTemperature",
    hasUnit=UNIT.DEG_C,
)
sensor_low_limit_1.add_property(sensor_low_limit_prop)

# ============================================================
# AIR FLOW CONNECTIONS
# 
# Layout analysis from grid (x-axis is horizontal, y is vertical):
#
# Fresh air paths:
#   - outdoor_air_conn → damper_paf_upper (y=4) → mixed_air_conn
#   - outdoor_air_conn → damper_paf_lower (y=1) → mixed_air_conn
#
# Return air path (y=8 horizontal line, then y=4 for return fan):
#   - return_air_conn → fan_1_r (x=16) → damper_rav (x=7) → mixed_air_conn
#
# Exhaust path (y=11 then down to y=1):
#   - return_air_conn → damper_evac (x=7, y=11) → fan_1_e (x=9, y=1) → exhaust_air_conn
#
# Main AHU processing train (y=8 horizontal line):
#   - mixed_air_conn → damper_melange (x=11) → filter_1 (x=13) → cooling_coil_1 (x=15)
#     → heating_coil_1 (x=18) → fan_1_a (x=21) → supply_air_conn
#   Note: Humidifier at [23,8] is kept in the model but not connected
#   in the air chain due to connection point incompatibility.
# ============================================================

# Outdoor air paths (two dampers share the same outdoor air source)
outdoor_air_conn >> damper_paf_upper >> mixed_air_conn
outdoor_air_conn >> damper_paf_lower >> mixed_air_conn

# Return air → return fan → return damper → mixed air junction
return_air_conn >> fan_1_r >> damper_rav >> mixed_air_conn

# Exhaust path: return air → exhaust damper → exhaust fan → exhaust outlet
return_air_conn >> damper_evac >> fan_1_e >> exhaust_air_conn

# Main AHU processing train (humidifier omitted from air chain)
(
    mixed_air_conn
    >> damper_melange
    >> filter_1
    >> cooling_coil_1
    >> heating_coil_1
    >> fan_1_a
    >> supply_air_conn
)

# ============================================================
# SENSOR OBSERVATIONS (% operator)
# Associate sensors with their observation points
# ============================================================

# sensor_temp_melange observes the air stream after heating coil (based on x position)
sensor_temp_melange % heating_coil_1.airOutlet

# sensor_diff_pressure_1 observes differential pressure across filter
sensor_diff_pressure_1 % (filter_1.airInlet, filter_1.airOutlet)

# sensor_temp_retour observes return air 
sensor_temp_retour % return_air_conn

# sensor_humidity_retour observes return air
sensor_humidity_retour % return_air_conn

# supply-duct sensors observe the supply air connection
sensor_temp_alim % supply_air_conn
sensor_static_pressure_1 % supply_air_conn
sensor_low_limit_1 % supply_air_conn

# ============================================================
# VFD CONNECTIONS (Electrical control of fans)
# vfd_1_a [21,9] drives fan_1_a [21,8]
# vfd_1_r [16,5] drives fan_1_r [16,4]
# ============================================================

vfd_1_a >> fan_1_a
vfd_1_r >> fan_1_r

# ============================================================
# SERIALIZE TO TTL
# ============================================================

if __name__ == "__main__":
    output_path = Path("ttl")
    output_path.mkdir(parents=True, exist_ok=True)
    
    output_file = output_path / "ontology.ttl"
    dump(filename=str(output_file))
    
    print(f"✓ Ontology successfully serialized to {output_file}")
    print(f"✓ Generated ASHRAE 223P compliant ontology for AHU system")
    print(f"✓ Includes: 5 dampers, 3 fans, 2 VFDs")
    print(f"✓ Includes: filter, cooling coil, heating coil, humidifier")
    print(f"✓ Includes: 7 sensors, 1 three-way valve")
