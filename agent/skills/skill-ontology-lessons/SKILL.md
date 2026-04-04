---
name: skill-ontology-lessons
description: Description of errors and common pitfalls when building the ontology and how to avoid them, based on analysis of past iterations.
---

# Ontology Lessons Skill

Use the description of errors and the solutions that worked in the past to enhance the creation of the python code for the ontology.

> **Consultation note:** When re-consulting mid-loop, search by error category keyword (e.g., "Sensor API", "Connection wiring") — do not re-read the full file. Target the relevant category section only.

---

# Error-to-Resolution Lessons

## Imports
- **Error:** Importing components from non-existent or incorrect paths like `bob.equipment.hvac.damper`, `bob.equipment.electricity.vfd`, `bob.equipment.hvac.valve`, `lib223p`. -> **Fix:** Import specific components from `scratch` when not available in `bob` (e.g., `scratch.electricity.vfd import VFD`, `scratch.hvac.damper import Damper`, `scratch.hvac.humidifier import ElectricalHumidifier`, `scratch.hvac.valve import ThreeWayMixingActuatedProportionalValve`).
- **Error:** Importing units from `scratch.units` (e.g., `PERCENT`, `PASCAL`). -> **Fix:** Import `UNIT` from `bob.core` and use `UNIT.PERCENT`, `UNIT.PA`.

## Instantiation pattern
- **Error:** Passing the name as a positional argument (e.g., `System("HVAC_System_1")`, `Fan("Fan_1")`). -> **Fix:** Pass the name using the `label` keyword argument (e.g., `System(label="HVAC_System_1")`, `Fan(label="Fan_1")`).
- **Error:** Setting `hasUnit` as an attribute after instantiation (e.g., `prop.hasUnit = UNIT.PERCENT`). -> **Fix:** Pass `hasUnit` as a keyword argument during instantiation (e.g., `RelativeHumidity(label="...", hasUnit=UNIT.PERCENT)`).

## Connection wiring
- **Error:** Connecting VFDs to fans using the simple `>>` operator (`vfd >> fan`) causes a "too many compatible connection points" error because VFDs have multiple compatible electrical connection points. -> **Fix:** Use explicit connection points: `vfd.electricalOutlet >> fan.electricalInlet`. *(Recurring risk across multiple sessions)*
- **Error:** Including `ElectricalHumidifier` in the main air flow chain (`>> humidifier_1 >>`) causes connection errors because it lacks compatible air-side connection points. -> **Fix:** Instantiate the humidifier but omit it from the air flow chain (`>>`) to avoid connection errors.

## Sensor API
- **Error:** Assigning properties to sensors using `sensor.observedProperty = sensor_prop`. -> **Fix:** Use the `add_property()` method: `sensor.add_property(sensor_prop)`.
- **Error:** Using `sensor % property` to attach a measurement property to a sensor. -> **Fix:** Use `sensor.add_property(prop)`. Note: `sensor % equipment` (attaching a sensor to the thing it monitors) is correct — only `sensor % property` is wrong.

## Serialization
- **Error:** Attempting to serialize the graph using `get_model_graph(model_name)` and `g.serialize(...)` or `DataGraph().serialize(...)` which may fail or be incorrect. -> **Fix:** Use `dump(filename=str(output_file))` imported from `bob.core` to serialize the ontology.

## BACnet External References
> **Structure:** Each `bacnet_N` entry now contains pre-computed fields: `code` (original raw address, e.g. `"2500.AI13"`), `address` (fully-formed BACnet URI or `null` for skip types, e.g. `"bacnet://2500/analog-input,13/present-value"`), and `ref_type` (`"sensor"`, `"property"`, or `"skip"`). Use `bacnet_N["address"]` directly.
- **Pattern for sensors** — `@` works directly on a sensor (Sensor IS a Property):
  ```python
  t_alim @ BACnetExternalReference("bacnet://2500/analog-input,13/present-value")
  ```
- **Pattern for equipment control/actuator points** — create the property variable first, then link to the external reference (you cannot call `@` on the equipment node directly):
  ```python
  mod_drive = Percent(label="MOD. DRIVE ALM No.1A")
  vfd_1_a.add_property(mod_drive)
  mod_drive @ BACnetExternalReference("bacnet://2500/analog-output,6/present-value")
  ```
- **Validation rule:** if the ontology has `comment="BACnet: ..."` patterns but no `BACnetExternalReference` usages, treat this as an **error** (e.g., `add_property(Percent(label="TEMP. ALIM.", comment="BACnet: 2500.AI13"))`). -> **Fix:** Use `BACnetExternalReference` with the `@` operator. Import: `from bob.externalreference.bacnet import BACnetExternalReference`.
- **Address parsing:** Convert `<device>.<TypeCode><instance>` to `bacnet://<device>/<object-type>,<instance>/present-value`. Suffix map: `AI`→`analog-input`, `AO`→`analog-output`, `AV`→`analog-value`, `BI`→`binary-input`, `BO`→`binary-output`, `BV`→`binary-value`, `SCH`→`schedule`. Skip `PG`, `CO`, `TL` — not valid types; keep as comments. Example: `"2500.AI13"` → `"bacnet://2500/analog-input,13/present-value"`.


## Structural approach
- **Error:** Using `System("AHU-1")` and `ahu_system.contains(...)` or `Junction(...)` which might not be supported or correct in the current library version. -> **Fix:** Use a flat structure with `bind_model_namespace` and instantiate components directly without wrapping them in a `System` container (unless explicitly required, in which case use the `>` operator).
- **Error:** Adding components to a `System` using the `.content()` method. -> **Fix:** Use the `>` operator to add components to a system (e.g., `hvac_system > fan`).
