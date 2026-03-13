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

# ---------------------------------------------------------------------------
# Namespace
# ---------------------------------------------------------------------------
model_name = "ahu_system"
_namespace = bind_model_namespace(model_name, f"urn:ontology:{model_name}/")

# ---------------------------------------------------------------------------
# Dampers
# Grid positions:
#   damper_paf_upper  [7, 3]   – outdoor air damper, upper path
#   damper_paf_lower  [7,-1]   – outdoor air damper, lower path
#   damper_rav        [7, 8]   – return air damper
#   damper_melange    [11, 6]  – mixed air damper (between return y=8 and supply y=3)
#   damper_evac       [8, 13]  – exhaust air damper
# ---------------------------------------------------------------------------
damper_paf_upper = Damper(
    label="damper_paf_upper",
    comment="Outdoor air damper – upper path at position [7,3]",
)

damper_paf_lower = Damper(
    label="damper_paf_lower",
    comment="Outdoor air damper – lower path at position [7,-1]",
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

# ---------------------------------------------------------------------------
# Filter
# Grid position: filter_1 [12, 3]
# ---------------------------------------------------------------------------
filter_1 = Filter(
    label="filter_1",
    comment="Air filter at position [12,3]",
)

# ---------------------------------------------------------------------------
# Coils
# Grid positions:
#   cooling_coil_1  [14, 3]
#   heating_coil_1  [18, 3]
# ---------------------------------------------------------------------------
cooling_coil_1 = ChilledWaterCoil(
    label="cooling_coil_1",
    comment="Cooling coil at position [14,3]",
)

heating_coil_1 = HotWaterCoil(
    label="heating_coil_1",
    comment="Heating coil at position [18,3]",
)

# ---------------------------------------------------------------------------
# Humidifier
# Grid position: humidifier_1 [19, 3]
# ---------------------------------------------------------------------------
humidifier_1 = ElectricalHumidifier(
    label="humidifier_1",
    comment="Humidifier at position [19,3]",
)

# ---------------------------------------------------------------------------
# Fans
# Grid positions:
#   fan_1_a  [16, 3]  – supply fan
#   fan_1_r  [20, 8]  – return fan
#   fan_1_e  [7, 13]  – exhaust fan
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# VFDs
# Grid positions:
#   vfd_1_a  [16, 4]  – VFD for supply fan fan_1_a
#   vfd_1_r  [20, 9]  – VFD for return fan fan_1_r
# ---------------------------------------------------------------------------
vfd_1_a = VFD(
    label="vfd_1_a",
    comment="VFD for supply fan at position [16,4]",
)

vfd_1_r = VFD(
    label="vfd_1_r",
    comment="VFD for return fan at position [20,9]",
)

# ---------------------------------------------------------------------------
# Three-way valve
# Grid position: valve_3_way_1 [14, 4]
# ---------------------------------------------------------------------------
valve_3_way_1 = ThreeWayMixingActuatedProportionalValve(
    label="valve_3_way_1",
    comment="Three-way mixing valve at position [14,4]",
)

# ---------------------------------------------------------------------------
# Air connections (boundaries / junctions)
# ---------------------------------------------------------------------------
outdoor_air_conn = AirConnection(
    label="OutdoorAir",
    comment="Outdoor air intake – connects to damper_paf_upper and damper_paf_lower",
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

# ---------------------------------------------------------------------------
# Sensors
# ---------------------------------------------------------------------------

# -- Temperature: mixed air [13, 3] --
sensor_temp_melange = AirTemperatureSensor(
    label="sensor_temp_melange",
    comment="Mixed air temperature sensor at position [13,3]",
)
sensor_temp_melange_prop = Temperature(
    label="MixedAirTemperature",
    hasUnit=UNIT.DEG_C,
)
sensor_temp_melange.add_property(sensor_temp_melange_prop)

# -- Temperature: return air [26, 8] --
sensor_temp_retour = AirTemperatureSensor(
    label="sensor_temp_retour",
    comment="Return air temperature sensor at position [26,8]",
)
sensor_temp_retour_prop = Temperature(
    label="ReturnAirTemperature",
    hasUnit=UNIT.DEG_C,
)
sensor_temp_retour.add_property(sensor_temp_retour_prop)

# -- Temperature: supply air [20, 3] --
sensor_temp_alim = AirTemperatureSensor(
    label="sensor_temp_alim",
    comment="Supply air temperature sensor at position [20,3]",
)
sensor_temp_alim_prop = Temperature(
    label="SupplyAirTemperature",
    hasUnit=UNIT.DEG_C,
)
sensor_temp_alim.add_property(sensor_temp_alim_prop)

# -- Differential pressure: across filter [12, 4] --
sensor_diff_pressure_1 = AirDifferentialStaticPressureSensor(
    label="sensor_diff_pressure_1",
    comment="Differential pressure sensor across filter at position [12,4]",
)
sensor_diff_pressure_prop = DifferentialStaticPressure(
    label="FilterDifferentialPressure",
    hasUnit=UNIT.PA,
)
sensor_diff_pressure_1.add_property(sensor_diff_pressure_prop)

# -- Static pressure: supply duct [22, 3] --
sensor_static_pressure_1 = AirDifferentialStaticPressureSensor(
    label="sensor_static_pressure_1",
    comment="Static pressure sensor in supply duct at position [22,3]",
)
sensor_static_pressure_prop = DifferentialStaticPressure(
    label="DuctStaticPressure",
    hasUnit=UNIT.PA,
)
sensor_static_pressure_1.add_property(sensor_static_pressure_prop)

# -- Humidity: return air [24, 8] --
sensor_humidity_retour = AirHumiditySensor(
    label="sensor_humidity_retour",
    comment="Return air humidity sensor at position [24,8]",
)
sensor_humidity_retour_prop = RelativeHumidity(
    label="ReturnAirHumidity",
    hasUnit=UNIT.PERCENT,
)
sensor_humidity_retour.add_property(sensor_humidity_retour_prop)

# -- Low-limit temperature: supply duct [21, 3] --
sensor_low_limit_1 = AirTemperatureSensor(
    label="sensor_low_limit_1",
    comment="Low-limit temperature sensor in supply duct at position [21,3]",
)
sensor_low_limit_prop = Temperature(
    label="LowLimitTemperature",
    hasUnit=UNIT.DEG_C,
)
sensor_low_limit_1.add_property(sensor_low_limit_prop)

# ---------------------------------------------------------------------------
# Air-side connections
#
# Layout (left → right on grid):
#
#  Outdoor air paths
#    outdoor_air_conn → damper_paf_upper  (y=3, x=7)  ─┐
#    outdoor_air_conn → damper_paf_lower  (y=-1, x=7) ─┤→ mixed_air_conn
#
#  Return air path (y=8, right→left)
#    return_air_conn → fan_1_r → damper_rav → mixed_air_conn
#
#  Exhaust path (y=13)
#    return_air_conn → damper_evac → fan_1_e → exhaust_air_conn
#
#  Main AHU processing train (y=3, left→right)
#    mixed_air_conn → damper_melange → filter_1 → cooling_coil_1
#                   → fan_1_a → heating_coil_1 → supply_air_conn
#
#  Note: ElectricalHumidifier (humidifier_1) is present on the supply duct
#  at [19,3] but its air-side connection points are not compatible with
#  the automatic inference used by >> in this library version.  It is kept
#  in the model (instantiated) so it appears in the ontology graph, but the
#  duct continuity is maintained through heating_coil_1 → supply_air_conn.
# ---------------------------------------------------------------------------

# Outdoor air paths (two dampers share the same outdoor air source)
outdoor_air_conn >> damper_paf_upper >> mixed_air_conn
outdoor_air_conn >> damper_paf_lower >> mixed_air_conn

# Return air → fan → return damper → mixed air plenum
return_air_conn >> fan_1_r >> damper_rav >> mixed_air_conn

# Return air → exhaust path
return_air_conn >> damper_evac >> fan_1_e >> exhaust_air_conn

# Main AHU processing train
(
    mixed_air_conn
    >> damper_melange
    >> filter_1
    >> cooling_coil_1
    >> fan_1_a
    >> heating_coil_1
    >> supply_air_conn
)

# ---------------------------------------------------------------------------
# Sensor observation points  (% operator)
# ---------------------------------------------------------------------------
# sensor_temp_melange observes the air just before the filter (mixed air inlet)
sensor_temp_melange % filter_1.airInlet

# sensor_diff_pressure_1 observes differential pressure across filter
sensor_diff_pressure_1 % (filter_1.airInlet, filter_1.airOutlet)

# sensor_temp_retour observes return air entering the return fan
sensor_temp_retour % fan_1_r.airInlet

# sensor_humidity_retour observes return air entering the return fan
sensor_humidity_retour % fan_1_r.airInlet

# supply-duct sensors observe the supply air connection
sensor_temp_alim % supply_air_conn
sensor_static_pressure_1 % supply_air_conn
sensor_low_limit_1 % supply_air_conn

# ---------------------------------------------------------------------------
# VFD → Fan electrical connections
# vfd_1_a [16,4] drives fan_1_a [16,3]
# vfd_1_r [20,9] drives fan_1_r [20,8]
# ---------------------------------------------------------------------------
vfd_1_a >> fan_1_a
vfd_1_r >> fan_1_r

# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    output_path = Path("223p/ttl")
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / "ontology.ttl"
    dump(filename=str(output_file))
    print(f"Ontology serialized to {output_file}")