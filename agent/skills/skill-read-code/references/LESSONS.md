# LESSONS.md — Distilled from 5 Code Generation Sessions

> Distilled on 2026-03-31 from sessions: 2026-03-13-1, 2026-03-13-2, 2026-03-13-3, 2026-03-16-1, 2026-03-17-1.
> Each lesson is extracted from the diff between a failed `_N` attempt and the resolved final file.

---

## 1. Imports

- **Error:** `dump` omitted from `bob.core` import, then used `get_model_graph(model_name)` to access the graph manually. -> **Fix:** Always import `dump` alongside the other core symbols: `from bob.core import UNIT, bind_model_namespace, dump`.

- **Error:** Damper, Humidifier, and Valve imported from `bob.equipment.hvac.*` (e.g. `from bob.equipment.hvac.damper import Damper`). -> **Fix:** These always come from `scratch`: `from scratch.hvac.damper import Damper`, `from scratch.hvac.humidifier import ElectricalHumidifier`, `from scratch.hvac.valve import ThreeWayMixingActuatedProportionalValve`.

- **Error:** VFD imported from `bob.equipment.electricity.vfd`. -> **Fix:** VFD comes from `scratch`: `from scratch.electricity.vfd import VFD`.

- **Error:** Unit constants imported directly from `scratch.units` as bare names (`from scratch.units import PERCENT, PASCAL`). -> **Fix:** Always use the `UNIT` object from `bob.core`: `UNIT.PERCENT`, `UNIT.PA`, `UNIT.DEG_C` etc. Never import raw unit constants from `scratch.units`.

- **Error:** `import lib223p as p` added as a serialization dependency. -> **Fix:** No external 223p library needed. Use only `dump` from `bob.core`.

---

## 2. Instantiation Pattern

- **Error:** Equipment and property constructors called with positional arguments: `Fan("fan_1_a")`, `System("HVAC_System_1")`, `Damper("damper_rav")`. -> **Fix:** Always use `label=` as a keyword argument: `Fan(label="fan_1_a")`, `System(label="HVAC_System_1")`, `Damper(label="damper_rav")`.

- **Error:** Property `hasUnit` set on a separate line after instantiation:
  ```python
  temp_prop = Temperature(label="MixedAirTemperature")
  temp_prop.hasUnit = UNIT.DEG_C
  ```
  -> **Fix:** Pass `hasUnit=` directly in the constructor call (single line):
  ```python
  temp_prop = Temperature(label="MixedAirTemperature", hasUnit=UNIT.DEG_C)
  ```

---

## 3. Connection Wiring

- **Error:** VFD → Fan connected with bare `>>` operator (`vfd_1_a >> fan_1_a`), causing a "too many compatible connection points" error. -> **Fix:** Always use explicit named ports for VFD→Fan wiring: `vfd_1_a.electricalOutlet >> fan_1_a.electricalInlet`. *(Recurring risk — appeared as an error in every session that included VFDs.)*

- **Error:** `ElectricalHumidifier` (from `scratch.hvac.humidifier`) inserted into the air-side `>>` chain (e.g. `fan_1_a >> humidifier_1 >> supply_air_conn`), causing a connection-point compatibility error. -> **Fix:** Instantiate `ElectricalHumidifier` so it appears in the ontology graph, but do NOT connect it in the air-side chain. Air chain continuity is maintained through the last compatible component (e.g. heating coil → supply connection).

---

## 4. Sensor API

- **Error:** Property attached to a sensor using assignment: `sensor.observedProperty = property_obj`. -> **Fix:** Use the method call: `sensor.add_property(property_obj)`.

- **Error:** `%` operator used to assign a measured property to a sensor: `humidity_sensor_1 % humidity_property_1`. -> **Fix:** The `%` operator is the *observation-point* operator — it attaches a sensor to a physical connection point or port, not to a property. Use `sensor.add_property(property_obj)` for property attachment.

- **Correct usage of `%`:** Attach a sensor to its observation location on the air stream:
  - Single point: `sensor_temp_melange % filter_1.airInlet`
  - Differential (two points): `sensor_diff_pressure_1 % (filter_1.airInlet, filter_1.airOutlet)`

---

## 5. Serialization

- **Error:** Serialization done via `get_model_graph(model_name)` + `g.serialize(destination=..., format="turtle")` (bob internal graph accessor). -> **Fix:** Call `dump(filename=str(output_file))` from `bob.core`. No manual graph access needed.

- **Error:** Serialization done via `hvac_system.graph.serialize(destination=..., format="turtle")` (object-level graph). -> **Fix:** Same — use `dump(filename=str(output_file))` from `bob.core`.

- **Correct pattern:**
  ```python
  if __name__ == "__main__":
      output_path = Path("223p/ttl")
      output_path.mkdir(parents=True, exist_ok=True)
      output_file = output_path / "ontology.ttl"
      dump(filename=str(output_file))
  ```

---

## 6. Structural Approach

- **Error:** All equipment instantiation wrapped inside functions (`create_ontology()`, `serialize_to_ttl()`). -> **Fix:** Use a flat, module-level top-down script. Instantiate all objects at module scope.

- **Error:** Used a class-hierarchy pattern with `System` container, `Junction` nodes, and `.contains(component)` to build the graph structure. -> **Fix:** The correct structural approach is flat: no `System` wrapper, no `Junction` — just direct equipment instantiation and `>>` wiring at module level.

- **Error:** `system.content(component1, component2, ...)` used to register components into a system. -> **Fix:** Use the single `>` operator for containment: `system > component`. Apply it per component:
  ```python
  hvac_system > fan
  hvac_system > filter_1
  ```

- **Required preamble:** Always call `bind_model_namespace` before any equipment instantiation:
  ```python
  model_name = "ahu_system"
  _namespace = bind_model_namespace(model_name, f"urn:ontology:{model_name}/")
  ```

---

## Recurring Risks (cross-session)

| Risk | Sessions where it appeared as an error |
|:-----|:---------------------------------------|
| VFD→Fan bare `>>` instead of explicit ports | 2026-03-13-1 (omitted), 2026-03-13-2 (_1), 2026-03-13-3 (_2, _3), 2026-03-16-1 (_1, _2) |
| Wrong serialization (manual graph access) | 2026-03-13-1 (_1), 2026-03-17-1 (_1) |
| Sensor API: `%` or `.observedProperty` for property assignment | 2026-03-13-3 (_2), 2026-03-17-1 (_1) |
| Positional constructor args instead of `label=` keyword | 2026-03-13-3 (_1), 2026-03-17-1 (_1, _2) |
| Humidifier wired into air-side chain | 2026-03-16-1 (_1) |
| Code wrapped in functions instead of module-level | 2026-03-17-1 (_1) |

