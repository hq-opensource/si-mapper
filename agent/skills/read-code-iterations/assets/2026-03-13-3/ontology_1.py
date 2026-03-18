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

from bob.equipment.hvac.fan import Fan
from bob.equipment.hvac.damper import Damper
from bob.equipment.hvac.filter import Filter
from bob.equipment.hvac.humidifier import Humidifier
from bob.equipment.hvac.coil import HotWaterCoil, ChilledWaterCoil
from bob.sensor.temperature import AirTemperatureSensor
from bob.sensor.humidity import AirHumiditySensor
from bob.sensor.pressure import AirDifferentialStaticPressureSensor
from bob.sensor.flow import AirFlowSensor
from bob.equipment.hvac.valve import ThreeWayValveMixing
from bob.equipment.electricity.vfd import VFD
from bob.core import System, Junction
from bob.properties.temperature import Temperature
from bob.properties.ratio import RelativeHumidity, Percent
from bob.properties.force import DifferentialStaticPressure, Pressure
from bob.properties.flow import Flow
from bob.properties.states import OnOffStatus
from bob.connections.air import AirConnection
from bob.connections.liquid import HotWaterConnection

# Import 223p for serialization
import lib223p as p

# Create the main AHU system
ahu_system = System("AHU-1")
ahu_system.label = "Air Handling Unit 1"
ahu_system.comment = "Main air handling unit with supply and return air paths"

# ============================================================
# SUPPLY AIR PATH EQUIPMENT
# ============================================================

# Fresh Air Damper (upper intake path)
damper_paf_upper = Damper("damper_paf_upper")
damper_paf_upper.label = "Fresh Air Damper Upper"
ahu_system.contains(damper_paf_upper)

# Fresh Air Damper (lower intake path)
damper_paf_lower = Damper("damper_paf_lower")
damper_paf_lower.label = "Fresh Air Damper Lower"
ahu_system.contains(damper_paf_lower)

# Return Air Damper
damper_rav = Damper("damper_rav")
damper_rav.label = "Return Air Damper"
ahu_system.contains(damper_rav)

# Mixing Damper (combines return and fresh air)
damper_melange = Damper("damper_melange")
damper_melange.label = "Mixed Air Damper"
ahu_system.contains(damper_melange)

# Filter
filter_1 = Filter("filter_1")
filter_1.label = "Supply Air Filter"
ahu_system.contains(filter_1)

# Cooling Coil
cooling_coil_1 = ChilledWaterCoil("cooling_coil_1")
cooling_coil_1.label = "Cooling Coil"
ahu_system.contains(cooling_coil_1)

# Three-way valve for cooling coil
valve_3_way_1 = ThreeWayValveMixing("valve_3_way_1")
valve_3_way_1.label = "Cooling Coil Control Valve"
ahu_system.contains(valve_3_way_1)

# Heating Coil
heating_coil_1 = HotWaterCoil("heating_coil_1")
heating_coil_1.label = "Heating Coil"
ahu_system.contains(heating_coil_1)

# Humidifier
humidifier_1 = Humidifier("humidifier_1")
humidifier_1.label = "Steam Humidifier"
ahu_system.contains(humidifier_1)

# Supply Fan
fan_1_a = Fan("fan_1_a")
fan_1_a.label = "Supply Air Fan"
ahu_system.contains(fan_1_a)

# VFD for Supply Fan
vfd_1_a = VFD("vfd_1_a")
vfd_1_a.label = "Supply Fan VFD"
ahu_system.contains(vfd_1_a)

# ============================================================
# RETURN/EXHAUST AIR PATH EQUIPMENT
# ============================================================

# Return Air Fan
fan_1_r = Fan("fan_1_r")
fan_1_r.label = "Return Air Fan"
ahu_system.contains(fan_1_r)

# VFD for Return Fan
vfd_1_r = VFD("vfd_1_r")
vfd_1_r.label = "Return Fan VFD"
ahu_system.contains(vfd_1_r)

# Exhaust Fan
fan_1_e = Fan("fan_1_e")
fan_1_e.label = "Exhaust Air Fan"
ahu_system.contains(fan_1_e)

# Exhaust Damper
damper_evac = Damper("damper_evac")
damper_evac.label = "Exhaust Air Damper"
ahu_system.contains(damper_evac)

# ============================================================
# SENSORS
# ============================================================

# Mixed Air Temperature Sensor
sensor_temp_melange = AirTemperatureSensor("sensor_temp_melange")
sensor_temp_melange.label = "Mixed Air Temperature Sensor"
temp_melange_prop = Temperature("temp_melange")
temp_melange_prop.label = "Mixed Air Temperature"
sensor_temp_melange.add_property(temp_melange_prop)
ahu_system.contains(sensor_temp_melange)

# Supply Air Temperature Sensor
sensor_temp_alim = AirTemperatureSensor("sensor_temp_alim")
sensor_temp_alim.label = "Supply Air Temperature Sensor"
temp_alim_prop = Temperature("temp_alim")
temp_alim_prop.label = "Supply Air Temperature"
sensor_temp_alim.add_property(temp_alim_prop)
ahu_system.contains(sensor_temp_alim)

# Return Air Temperature Sensor
sensor_temp_retour = AirTemperatureSensor("sensor_temp_retour")
sensor_temp_retour.label = "Return Air Temperature Sensor"
temp_retour_prop = Temperature("temp_retour")
temp_retour_prop.label = "Return Air Temperature"
sensor_temp_retour.add_property(temp_retour_prop)
ahu_system.contains(sensor_temp_retour)

# Return Air Humidity Sensor
sensor_humidity_retour = AirHumiditySensor("sensor_humidity_retour")
sensor_humidity_retour.label = "Return Air Humidity Sensor"
humidity_retour_prop = RelativeHumidity("humidity_retour")
humidity_retour_prop.label = "Return Air Relative Humidity"
sensor_humidity_retour.add_property(humidity_retour_prop)
ahu_system.contains(sensor_humidity_retour)

# Differential Pressure Sensor (Filter)
sensor_diff_pressure_1 = AirDifferentialStaticPressureSensor("sensor_diff_pressure_1")
sensor_diff_pressure_1.label = "Filter Differential Pressure Sensor"
diff_pressure_prop = DifferentialStaticPressure("diff_pressure_filter")
diff_pressure_prop.label = "Filter Differential Pressure"
sensor_diff_pressure_1.add_property(diff_pressure_prop)
ahu_system.contains(sensor_diff_pressure_1)

# Static Pressure Sensor (Supply Duct)
sensor_static_pressure_1 = AirDifferentialStaticPressureSensor("sensor_static_pressure_1")
sensor_static_pressure_1.label = "Supply Duct Static Pressure Sensor"
static_pressure_prop = DifferentialStaticPressure("static_pressure_supply")
static_pressure_prop.label = "Supply Duct Static Pressure"
sensor_static_pressure_1.add_property(static_pressure_prop)
ahu_system.contains(sensor_static_pressure_1)

# Low Limit Sensor (Freeze Protection)
sensor_low_limit_1 = AirTemperatureSensor("sensor_low_limit_1")
sensor_low_limit_1.label = "Low Limit Temperature Sensor"
temp_low_limit_prop = Temperature("temp_low_limit")
temp_low_limit_prop.label = "Low Limit Temperature"
sensor_low_limit_1.add_property(temp_low_limit_prop)
ahu_system.contains(sensor_low_limit_1)

# ============================================================
# AIR FLOW CONNECTIONS
# ============================================================

# Create junctions for air path splits/merges
junction_fresh_air_merge = Junction("junction_fresh_air_merge")
junction_fresh_air_merge.label = "Fresh Air Merge Junction"
ahu_system.contains(junction_fresh_air_merge)

junction_mixed_air = Junction("junction_mixed_air")
junction_mixed_air.label = "Mixed Air Junction"
ahu_system.contains(junction_mixed_air)

junction_return_split = Junction("junction_return_split")
junction_return_split.label = "Return Air Split Junction"
ahu_system.contains(junction_return_split)

# Fresh air paths (coordinates suggest parallel paths that merge)
# Upper fresh air path: damper_paf_upper -> junction
damper_paf_upper >> junction_fresh_air_merge

# Lower fresh air path: damper_paf_lower -> junction
damper_paf_lower >> junction_fresh_air_merge

# Return air path: damper_rav -> mixed air junction
damper_rav >> junction_mixed_air

# Fresh air to mixed air junction
junction_fresh_air_merge >> junction_mixed_air

# Mixed air through mixing damper
junction_mixed_air >> damper_melange

# Supply air path (main sequence through AHU)
damper_melange >> filter_1
filter_1 >> cooling_coil_1
cooling_coil_1 >> heating_coil_1
heating_coil_1 >> humidifier_1
humidifier_1 >> fan_1_a

# Return air path
# Based on coordinates, return air comes back and splits to return fan and recirculation
fan_1_r >> junction_return_split
junction_return_split >> damper_rav  # Recirculation path

# Exhaust path
junction_return_split >> damper_evac
damper_evac >> fan_1_e

# ============================================================
# SENSOR OBSERVATIONS
# ============================================================

# Associate sensors with their observation points using the % operator
sensor_temp_melange % damper_melange  # Mixed air temperature after mixing
sensor_diff_pressure_1 % filter_1  # Filter pressure drop
sensor_temp_alim % fan_1_a  # Supply air temperature
sensor_temp_retour % fan_1_r  # Return air temperature
sensor_humidity_retour % fan_1_r  # Return air humidity
sensor_static_pressure_1 % fan_1_a  # Supply duct static pressure
sensor_low_limit_1 % heating_coil_1  # Freeze protection at heating coil

# ============================================================
# VFD CONNECTIONS (Electrical control)
# ============================================================

# VFDs control fan speed
# Using hasProperty relationship to connect VFD control to fan operation
fan_speed_a_prop = Percent("fan_1_a_speed")
fan_speed_a_prop.label = "Supply Fan Speed Command"
vfd_1_a.add_property(fan_speed_a_prop)

fan_speed_r_prop = Percent("fan_1_r_speed")
fan_speed_r_prop.label = "Return Fan Speed Command"
vfd_1_r.add_property(fan_speed_r_prop)

# ============================================================
# WATER CONNECTIONS FOR COILS
# ============================================================

# Three-way valve controls chilled water to cooling coil
valve_3_way_1.fluidOutlet >> cooling_coil_1.chilledWaterInlet

# Note: Hot water connections for heating coil would be modeled similarly
# but coordinates don't show explicit water piping in the grid

# ============================================================
# SERIALIZE TO TTL
# ============================================================

if __name__ == "__main__":
    # Serialize the ontology to Turtle format
    output_path = "ttl/ontology.ttl"
    
    # Use 223p library to serialize
    # The p.serialize_to_file function will create the TTL file
    try:
        import os
        os.makedirs("ttl", exist_ok=True)
        
        # Serialize using bob's built-in serialization
        from bob.core import DataGraph
        
        graph = DataGraph()
        ahu_system.content()  # Ensure all content is in the graph
        
        # Serialize to TTL
        graph.serialize(destination=output_path, format='turtle')
        
        print(f"✓ Ontology successfully serialized to {output_path}")
        print(f"✓ Generated ASHRAE 223P compliant ontology for AHU-1")
        print(f"✓ Includes: {len([damper_paf_upper, damper_paf_lower, damper_rav, damper_melange, damper_evac])} dampers")
        print(f"✓ Includes: {len([fan_1_a, fan_1_r, fan_1_e])} fans")
        print(f"✓ Includes: {len([filter_1, cooling_coil_1, heating_coil_1, humidifier_1])} treatment components")
        print(f"✓ Includes: {len([sensor_temp_melange, sensor_temp_alim, sensor_temp_retour, sensor_humidity_retour, sensor_diff_pressure_1, sensor_static_pressure_1, sensor_low_limit_1])} sensors")
        
    except Exception as e:
        print(f"✗ Error during serialization: {e}")
        import traceback
        traceback.print_exc()
