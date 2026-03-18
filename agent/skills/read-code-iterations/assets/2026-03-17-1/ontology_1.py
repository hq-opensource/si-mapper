"""
ASHRAE 223P Ontology for HVAC System
Generated from grid data with ducts, filters, fan, and sensors
"""

from bob.equipment.hvac.fan import Fan
from bob.equipment.hvac.filter import Filter
from bob.sensor.humidity import AirHumiditySensor
from bob.sensor.pressure import AirDifferentialStaticPressureSensor
from bob.core import System
from bob.properties.ratio import RelativeHumidity
from bob.properties.force import DifferentialStaticPressure
from scratch.units import PERCENT, PASCAL


def create_ontology():
    """
    Create the HVAC system ontology based on grid data.
    
    Grid components:
    - g0mWHm0wtj: duct from [1,2] to [11,2]
    - 4LSiT8Q1Ur: duct from [3,2] to [3,7]
    - H7sH3kAnnL: duct from [3,7] to [11,7]
    - pqYbaoBOp5: duct from [11,2] to [11,5]
    - 5VEvWJvMTj: duct from [11,5] to [15,5]
    - oDH2SAH9Ky: fan at [2,2]
    - BIBD1Uf4Dt: filter at [4,2]
    - Lpr2xZFucV: filter at [3,3]
    - USrSIXZqio: humidity sensor at [3,4]
    - cM7fhnE8Ef: static pressure sensor at [3,5]
    - z6b5HCekeB: humidity sensor at [5,2]
    - m9cuOHLBiE: static pressure sensor at [6,2]
    """
    
    # Create the main HVAC system
    hvac_system = System("HVAC_System_1")
    hvac_system.label = "Main HVAC Air Distribution System"
    hvac_system.comment = "Air distribution system with fan, filters, and sensors"
    
    # Create equipment components
    fan = Fan("Fan_oDH2SAH9Ky")
    fan.label = "Supply Air Fan"
    fan.comment = "Fan at position [2,2] providing air movement through the duct system"
    
    filter_1 = Filter("Filter_BIBD1Uf4Dt")
    filter_1.label = "Primary Air Filter"
    filter_1.comment = "Filter at position [4,2] on main horizontal duct"
    
    filter_2 = Filter("Filter_Lpr2xZFucV")
    filter_2.label = "Secondary Air Filter"
    filter_2.comment = "Filter at position [3,3] on vertical duct"
    
    # Create sensors with properties
    humidity_sensor_1 = AirHumiditySensor("Sensor_USrSIXZqio")
    humidity_sensor_1.label = "Humidity Sensor 1"
    humidity_sensor_1.comment = "Humidity sensor at position [3,4]"
    
    humidity_property_1 = RelativeHumidity("RH_USrSIXZqio")
    humidity_property_1.hasUnit = PERCENT
    humidity_sensor_1 % humidity_property_1
    
    pressure_sensor_1 = AirDifferentialStaticPressureSensor("Sensor_cM7fhnE8Ef")
    pressure_sensor_1.label = "Static Pressure Sensor 1"
    pressure_sensor_1.comment = "Differential static pressure sensor at position [3,5]"
    
    pressure_property_1 = DifferentialStaticPressure("DSP_cM7fhnE8Ef")
    pressure_property_1.hasUnit = PASCAL
    pressure_sensor_1 % pressure_property_1
    
    humidity_sensor_2 = AirHumiditySensor("Sensor_z6b5HCekeB")
    humidity_sensor_2.label = "Humidity Sensor 2"
    humidity_sensor_2.comment = "Humidity sensor at position [5,2]"
    
    humidity_property_2 = RelativeHumidity("RH_z6b5HCekeB")
    humidity_property_2.hasUnit = PERCENT
    humidity_sensor_2 % humidity_property_2
    
    pressure_sensor_2 = AirDifferentialStaticPressureSensor("Sensor_m9cuOHLBiE")
    pressure_sensor_2.label = "Static Pressure Sensor 2"
    pressure_sensor_2.comment = "Differential static pressure sensor at position [6,2]"
    
    pressure_property_2 = DifferentialStaticPressure("DSP_m9cuOHLBiE")
    pressure_property_2.hasUnit = PASCAL
    pressure_sensor_2 % pressure_property_2
    
    # Create connections based on coordinate adjacency
    # Fan at [2,2] connects to duct starting at [1,2]
    # Filter_1 at [4,2] is on duct from [1,2] to [11,2]
    # Filter_2 at [3,3] is on duct from [3,2] to [3,7]
    
    # Connect fan to filter_1 (both on horizontal duct)
    fan >> filter_1
    
    # Connect filter_1 to filter_2 
    # (filter_1 at [4,2] on main duct, vertical duct branches at [3,2])
    filter_1 >> filter_2
    
    # Add components to system
    hvac_system.content(
        fan,
        filter_1,
        filter_2,
        humidity_sensor_1,
        pressure_sensor_1,
        humidity_sensor_2,
        pressure_sensor_2
    )
    
    return hvac_system


def serialize_to_ttl():
    """
    Serialize the ontology to TTL format and save to file.
    """
    import os
    from pathlib import Path
    
    # Create the ontology
    hvac_system = create_ontology()
    
    # Get the graph
    graph = hvac_system.graph
    
    # Ensure output directory exists
    output_dir = Path("ttl")
    output_dir.mkdir(exist_ok=True)
    
    # Serialize to TTL file
    output_file = output_dir / "ontology.ttl"
    graph.serialize(destination=str(output_file), format="turtle")
    
    print(f"Ontology serialized to {output_file}")
    print(f"Total triples: {len(graph)}")
    
    return output_file


if __name__ == "__main__":
    # Create and serialize the ontology
    output_file = serialize_to_ttl()
    print(f"\nOntology generation complete!")
    print(f"Output: {output_file}")
