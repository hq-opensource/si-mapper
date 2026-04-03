---
name: skill-ontology-lessons
description: Description of errors and common pitfalls when building the ontology and how to avoid them, based on analysis of past iterations.
---

# Ontology Lessons Skill

Use the description of errors and the solutions that worked in the past to enhance the creation of the python code for the ontology.

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

## Structural approach
- **Error:** Using `System("AHU-1")` and `ahu_system.contains(...)` or `Junction(...)` which might not be supported or correct in the current library version. -> **Fix:** Use a flat structure with `bind_model_namespace` and instantiate components directly without wrapping them in a `System` container (unless explicitly required, in which case use the `>` operator).
- **Error:** Adding components to a `System` using the `.content()` method. -> **Fix:** Use the `>` operator to add components to a system (e.g., `hvac_system > fan`).
