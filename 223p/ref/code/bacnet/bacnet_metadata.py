from bob.core import Property, UNIT
from bob.externalreference.bacnet import BACnetExternalReference
from bob.properties import Temperature

def attach_bacnet_metadata(prop: Property, point_meta: dict):
  device = point_meta.get("device-identifier", "")
  object_type = point_meta.get("object-type", "")
  inst = point_meta.get("object-instance", "")
  try:
    prop @ BACnetExternalReference(f"bacnet://{device}/{object_type},{inst}/present-value")
  except ValueError as e:
    # Skip invalid BACnet URLs
    print(f"Warning: Invalid BACnet URL for code {point_meta}: {e}")

temp_property = Temperature(
    label="ReturnAirTemperature",
    hasUnit=UNIT.DEG_C,
)
attach_bacnet_metadata(temp_property, {"device-identifier": "2500", "object-type": "analog-input", "object-instance": "1"})