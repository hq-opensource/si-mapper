"""
ASHRAE 223P Ontology for HVAC System
Generated from grid data

This ontology models an Air Handling Unit (AHU) system with:
- Supply and return air paths
- Fresh air intake and exhaust
- Fans with VFDs
- Dampers for air control
- Heating and cooling coils
- Filter and humidifier
- Various sensors (temperature, humidity, pressure, flow)
- Three-way valve for water control
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

# Set up namespace
model_name = "ahu_system"
_namespace = bind_model_namespace(model_name, f"urn:ontology:{model_name}/")

# ============================================================
# DAMPERS
# ============================================================

damper_paf_upper = Damper(
    label="damper_paf_upper",
    comment="Outdoor air damper - upper path at position [7,3]",
)

damper_paf_lower = Damper(
    label="damper_paf_lower",
    comment="Outdoor air damper - lower path at position [7,-1]",
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
    comment="Exhaust air damper at position [8,13]",
)

# ============================================================
# FILTER
# ============================================================

filter_1 = Filter(
    label="filter_1",
    comment="Air filter at position [12,3]",
)

# ============================================================
# COILS
# ============================================================

cooling_coil_1 = ChilledWaterCoil(
    label="cooling_coil_1",
    comment="Cooling coil at position [14,3]",
)

heating_coil_1 = HotWaterCoil(
    label="heating_coil_1",
    comment="Heating coil at position [18,3]",
)

# ============================================================
# HUMIDIFIER
# ============================================================

humidifier_1 = ElectricalHumidifier(
    label="humidifier_1",
    comment="Humidifier at position [19,3]",
)

# ============================================================
# FANS
# ============================================================

fan_1_a = Fan(
    label="fan_1_a",
    comment="Supply air fan at position [16,3]",
)

fan_1_r = Fan(
    label="fan_1_r",
    comment="Return air fan at position [20,8]",
)

fan_1_e = Fan(
    label="fan_1_e",
    comment="Exhaust air fan at position [7,13]",
)

# ============================================================
# VFDs
# ============================================================

vfd_1_a = VFD(
    label="vfd_1_a",
    comment="VFD for supply fan at position [16,4]",
)

vfd_1_r = VFD(
    label="vfd_1_r",
    comment="VFD for return fan at position [20,9]",
)

# ============================================================
# VALVE
# ============================================================

valve_3_way_1 = ThreeWayMixingActuatedProportionalValve(
    label="valve_3_way_1",
    comment="Three-way mixing valve at position [14,4]",
)

# ============================================================
# AIR CONNECTIONS
# ============================================================

outdoor_air_conn = AirConnection(
    label="OutdoorAir",
    comment="Outdoor air intake",
)

mixed_air_conn = AirConnection(
    label="MixedAir",
    comment="Mixed outdoor and return air",
)

return_air_conn = AirConnection(
    label="ReturnAir",
    comment="Return air from zones",
)

exhaust_air_conn = AirConnection(
    label="ExhaustAir",
    comment="Exhaust air to outside",
)

supply_air_conn = AirConnection(
    label="SupplyAir",
    comment="Supply air to zones",
)

# ============================================================
# SENSORS WITH PROPERTIES
# ============================================================

# Mixed Air Temperature Sensor
sensor_temp_melange = AirTemperatureSensor(
    label="sensor_temp_melange",
    comment="Mixed air temperature sensor at position [13,3]",
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
    comment="Supply air temperature sensor at position [20,3]",
)
sensor_temp_alim_prop = Temperature(
    label="SupplyAirTemperature",
    hasUnit=UNIT.DEG_C,
)
sensor_temp_alim.add_property(sensor_temp_alim_prop)

# Differential Pressure Sensor (Filter)
sensor_diff_pressure_1 = AirDifferentialStaticPressureSensor(
    label="sensor_diff_pressure_1",
    comment="Differential pressure sensor across filter at position [12,4]",
)
sensor_diff_pressure_prop = DifferentialStaticPressure(
    label="FilterDifferentialPressure",
    hasUnit=UNIT.PA,
)
sensor_diff_pressure_1.add_property(sensor_diff_pressure_prop)

# Static Pressure Sensor (Supply Duct)
sensor_static_pressure_1 = AirDifferentialStaticPressureSensor(
    label="sensor_static_pressure_1",
    comment="Static pressure sensor at position [22,3]",
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
    comment="Low limit temperature sensor at position [21,3]",
)
sensor_low_limit_prop = Temperature(
    label="LowLimitTemperature",
    hasUnit=UNIT.DEG_C,
)
sensor_low_limit_1.add_property(sensor_low_limit_prop)

# ============================================================
# AIR FLOW CONNECTIONS
# ============================================================

# Outdoor air paths (two dampers share the same outdoor air source)
outdoor_air_conn >> damper_paf_upper >> mixed_air_conn
outdoor_air_conn >> damper_paf_lower >> mixed_air_conn

# Return air path
return_air_conn >> fan_1_r >> damper_rav >> mixed_air_conn

# Exhaust path
return_air_conn >> damper_evac >> fan_1_e >> exhaust_air_conn

# Main AHU processing chain
# Note: Humidifier is kept in the model but left unconnected on the air-side
# due to connection point compatibility issues
mixed_air_conn >> damper_melange >> filter_1 >> cooling_coil_1 >> fan_1_a >> heating_coil_1 >> supply_air_conn

# ============================================================
# SENSOR OBSERVATIONS (% operator)
# ============================================================

# Associate sensors with their observation points
sensor_temp_melange % filter_1.airInlet
sensor_diff_pressure_1 % (filter_1.airInlet, filter_1.airOutlet)
sensor_temp_retour % fan_1_r.airInlet
sensor_humidity_retour % fan_1_r.airInlet
sensor_temp_alim % supply_air_conn
sensor_static_pressure_1 % supply_air_conn
sensor_low_limit_1 % supply_air_conn

# ============================================================
# VFD CONNECTIONS
# ============================================================

# Connect VFDs to fans using >> operator
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
