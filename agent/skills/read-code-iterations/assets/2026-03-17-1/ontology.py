"""
ASHRAE 223P Ontology for HVAC System
Generated from grid data with ducts, filters, fan, and sensors
"""

from pathlib import Path
from bob.equipment.hvac.fan import Fan
from bob.equipment.hvac.filter import Filter
from bob.sensor.humidity import AirHumiditySensor
from bob.sensor.pressure import AirDifferentialStaticPressureSensor
from bob.core import System, UNIT, bind_model_namespace, dump
from bob.properties.ratio import RelativeHumidity
from bob.properties.force import DifferentialStaticPressure


# Set up namespace
model_name = "hvac_system"
_namespace = bind_model_namespace(model_name, f"urn:ontology:{model_name}/")

# Create the main HVAC system
hvac_system = System(label="HVAC_System_1")
hvac_system.comment = "Air distribution system with fan, filters, and sensors"

# Create equipment components
fan = Fan(label="Fan_oDH2SAH9Ky")
fan.comment = "Fan at position [2,2] providing air movement through the duct system"

filter_1 = Filter(label="Filter_BIBD1Uf4Dt")
filter_1.comment = "Filter at position [4,2] on main horizontal duct"

filter_2 = Filter(label="Filter_Lpr2xZFucV")
filter_2.comment = "Filter at position [3,3] on vertical duct"

# Create sensors with properties
humidity_sensor_1 = AirHumiditySensor(label="Sensor_USrSIXZqio")
humidity_sensor_1.comment = "Humidity sensor at position [3,4]"

humidity_property_1 = RelativeHumidity(label="RH_USrSIXZqio", hasUnit=UNIT.PERCENT)
humidity_sensor_1.add_property(humidity_property_1)

pressure_sensor_1 = AirDifferentialStaticPressureSensor(label="Sensor_cM7fhnE8Ef")
pressure_sensor_1.comment = "Differential static pressure sensor at position [3,5]"

pressure_property_1 = DifferentialStaticPressure(label="DSP_cM7fhnE8Ef", hasUnit=UNIT.PA)
pressure_sensor_1.add_property(pressure_property_1)

humidity_sensor_2 = AirHumiditySensor(label="Sensor_z6b5HCekeB")
humidity_sensor_2.comment = "Humidity sensor at position [5,2]"

humidity_property_2 = RelativeHumidity(label="RH_z6b5HCekeB", hasUnit=UNIT.PERCENT)
humidity_sensor_2.add_property(humidity_property_2)

pressure_sensor_2 = AirDifferentialStaticPressureSensor(label="Sensor_m9cuOHLBiE")
pressure_sensor_2.comment = "Differential static pressure sensor at position [6,2]"

pressure_property_2 = DifferentialStaticPressure(label="DSP_m9cuOHLBiE", hasUnit=UNIT.PA)
pressure_sensor_2.add_property(pressure_property_2)

# Create connections based on coordinate adjacency
# Fan at [2,2] connects to filter_1 at [4,2] (both on horizontal duct)
fan >> filter_1

# Filter_2 at [3,3] is on vertical duct from [3,2] to [3,7]
# This is adjacent to the main horizontal duct
filter_1 >> filter_2

# Add components to system using > operator
hvac_system > fan
hvac_system > filter_1
hvac_system > filter_2
hvac_system > humidity_sensor_1
hvac_system > pressure_sensor_1
hvac_system > humidity_sensor_2
hvac_system > pressure_sensor_2

# Serialize the ontology to TTL file
if __name__ == "__main__":
    output_path = Path("ttl")
    output_path.mkdir(exist_ok=True)
    
    output_file = output_path / "ontology.ttl"
    dump(filename=str(output_file))
    
    print(f"Ontology serialized to {output_file}")
