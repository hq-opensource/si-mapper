#import functions as fn
import hvac_devices as hd
import lighting_devices as ld
from bob.bacnet import (
    AnalogInputObject,
    AnalogValueObject,
    BinaryInputObject,
    BinaryOutputObject,
    Device,
    DeviceObject,
    ScheduleObject,
)
from bob.core import bind_model_namespace, dump
from bob.externalreference.bacnet import BACnetExternalReference

from scratch.assemblage import model_namespace

model_name, global_ns = model_namespace(__file__)
_namespace = bind_model_namespace(model_name, f"urn:{global_ns}:{model_name}/")


# An HVAC BACnet Device
CGM_2_004 = Device(
    label="CGM-2-004",
    comment="AHU Controller",
    # deviceId=5204,
    # deviceName="CGM-2-004",
    # networkNumber=2,
    # address=4,
    # vendorId=5,
)

CGM_2_004_device_object = DeviceObject(
    objectIdentifier="device,5204",
    objectName="CGM-2-004",
    vendorName="Unknown",
    vendorIdentifier=5,
)
CGM_2_004 > CGM_2_004_device_object

VAV_2_005 = Device(
    label="CVM-2-005",
    comment="VAV for Zone 1",
    # deviceId=5205,
    # deviceName="CVM-2-005",
    # networkNumber=2,
    # address=5,
    # vendorId=5,
)

VAV_2_005_device_object = DeviceObject(
    objectIdentifier="device,5205",
    objectName="CVM-2-005",
    vendorName="Unknown",
    vendorIdentifier=5,
)
VAV_2_005 > VAV_2_005_device_object


VAV_2_006 = Device(
    label="CVM-2-006",
    comment="VAV for Zone 2",
    # deviceId=5206,
    # deviceName="CVM-2-006",
    # networkNumber=2,
    # address=6,
    # vendorId=5,
)

VAV_2_006_device_object = DeviceObject(
    objectIdentifier="device,5206",
    objectName="CVM-2-006",
    vendorName="Unknown",
    vendorIdentifier=5,
)
VAV_2_006 > VAV_2_006_device_object


rat = AnalogInputObject(
    objectIdentifier="analog-input,1209",
    objectName="RA-T",
    description="Return Air Temeprature",
)
CGM_2_004 > rat

dat_avg = AnalogValueObject(
    objectIdentifier="analog-value,321",
    objectName="DAT-AVG",
    description="Discharge Air Temp Average",
)
CGM_2_004 > dat_avg


dat = AnalogInputObject(
    objectIdentifier="analog-input,1210",
    objectName="DA-T",
    description="Discharge Air Temperature",
)
CGM_2_004 > dat

zn1_t = AnalogInputObject(
    objectIdentifier="analog-input,1001",
    objectName="ZN1-T",
    description="Zone 1 Temperature",
)
VAV_2_005 > zn1_t

zn2_t = AnalogInputObject(
    objectIdentifier="analog-input,1002",
    objectName="ZN2-T",
    description="Zone 2 Temperature",
)
VAV_2_006 > zn2_t

rf_vfd_status = BinaryInputObject(
    objectIdentifier="binary-input,5021",
    objectName="RF-S",
    description="Return Fan Status from VFD drive running",
)
CGM_2_004 > rf_vfd_status

rf_vfd_cmd = BinaryOutputObject(
    objectIdentifier="binary-output,12345",
    objectName="RF-C",
    description="Return Fan Command from VFD run command",
)
CGM_2_004 > rf_vfd_cmd

pritoni_schedule = ScheduleObject(
    objectIdentifier="schedule,1",
    objectName="OCC-SCHEDULE",
    description="Building Occupancy Schedule",
)
CGM_2_004 > pritoni_schedule

hd.vav1["ZN-T"].observedProperty @ BACnetExternalReference(
    "bacnet://5205/analog-input,1001/present-value"
)
hd.vav2["ZN-T"].observedProperty @ BACnetExternalReference(
    "bacnet://5206/analog-input,1002/present-value"
)

hd.ahu["RF_VFD"]["drive_running"] @ BACnetExternalReference(
    "bacnet://5204/binary-input,5021/present-value"
)
hd.ahu["RF_VFD"]["run_command"] @ BACnetExternalReference(
    "bacnet://5204/binary-output,12345/present-value"
)

# A bulb with only one object
ld.openofficeNorth_luminaire_1.brightnessRatio @ BACnetExternalReference(
    "bacnet://2/analog-input,1/present-value"
)
ld.openofficeNorth_luminaire_1.onOffStatus @ BACnetExternalReference(
    "bacnet://2/binary-input,1/present-value"
)

#fn.f_avg_temp @ dat_avg.presentValue

pritoni_schedule_reference = BACnetExternalReference(
    "bacnet://5204/schedule,1/present-value"
)

#fn.bathroom_occ_control_schedule @ pritoni_schedule_reference
#fn.corridor_occ_control_schedule @ pritoni_schedule_reference
#fn.kitchenette_occ_control_schedule @ pritoni_schedule_reference
#fn.open_office_occ_control_schedule @ pritoni_schedule_reference
#fn.private_office_occ_control_schedule @ pritoni_schedule_reference

if __name__ == "__main__":
    dump()
