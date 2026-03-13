# Iteration 2026-03-13-1

## Overview

First iteration of the 223P ontology generation run on **2026-03-13**, produced by the `_223p` sub-agent pipeline using **Claude Sonnet 4.5** (`github_copilot/claude-sonnet-4.5`) via LiteLLM.

The goal of this iteration was to generate a valid ASHRAE 223P-compliant ontology (Turtle / `.ttl`) for a complete **Air-Handling Unit (AHU) system**, starting from the grid-layout data extracted by the MCP server.

---

## Model

| Property | Value |
|---|---|
| Model | `claude-sonnet-4.5` |
| Provider | GitHub Copilot (via LiteLLM) |
| Agent | `agent/sub_agents/_223p/` |
| Max iterations | 100 |

---

## Output Files

| File | Description |
|---|---|
| `ontology.py` | Generated Python source using the **BOB** and **SCRATCH** libraries |
| `ontology.ttl` | Serialised Turtle ontology (1 894 lines) |
| `ontology.html` | HTML visualisation of the ontology graph |

---

## Iterations
- 1 run of 15 to 20 iteration was needed to generate the inital python file
- 3 validation runs of 50 iterations were needed to fix errors and warnings in the generated code, and to ensure the generated code produced a valid ontology.

---

## Modelled System — AHU Overview

The ontology describes a complete **Air-Handling Unit** with the following equipment and sub-systems:

### Dampers (5)
| Label | Description |
|---|---|
| `damper_paf_upper` | Outdoor air damper – upper path |
| `damper_paf_lower` | Outdoor air damper – lower path |
| `damper_rav` | Return air damper |
| `damper_melange` | Mixed air damper |
| `damper_evac` | Exhaust air damper |

### Coils (2)
| Label | Description |
|---|---|
| `cooling_coil_1` | Chilled-water cooling coil |
| `heating_coil_1` | Hot-water heating coil |

### Fans (3)
| Label | Description |
|---|---|
| `fan_1_a` | Supply air fan |
| `fan_1_r` | Return air fan |
| `fan_1_e` | Exhaust air fan |

### VFDs (2)
| Label | Description |
|---|---|
| `vfd_1_a` | Variable-frequency drive for supply fan |
| `vfd_1_r` | Variable-frequency drive for return fan |

### Other Equipment
| Label | Description |
|---|---|
| `filter_1` | Air filter |
| `humidifier_1` | Electrical humidifier (modelled but left air-side unconnected — see note below) |
| `valve_3_way_1` | Three-way mixing actuated proportional valve |

### Sensors (7)
| Label | Measurement |
|---|---|
| `sensor_temp_melange` | Mixed air temperature (°C) |
| `sensor_temp_retour` | Return air temperature (°C) |
| `sensor_temp_alim` | Supply air temperature (°C) |
| `sensor_low_limit_1` | Low-limit temperature (°C) |
| `sensor_diff_pressure_1` | Differential static pressure across filter (Pa) |
| `sensor_static_pressure_1` | Duct static pressure (Pa) |
| `sensor_humidity_retour` | Return air relative humidity (%) |

### Air Connections (5)
`OutdoorAir` → `MixedAir` → (AHU chain) → `SupplyAir`  
`ReturnAir` → `fan_1_r` → `damper_rav` → `MixedAir`  
`ReturnAir` → `damper_evac` → `fan_1_e` → `ExhaustAir`

---

## Ontology Statistics

| Metric | Count |
|---|---|
| Total named entities | 186 |
| Named labels | 178 |
| `s223:ConnectionPoint` instances | 42 |
| `s223:Connectable` instances | 29 |
| `s223:Connection` instances | 12 |
| `s223:Function` instances | 11 |
| Lines in `.ttl` | 1 894 |

---

## Known Limitations / Notes

- **Humidifier air-side**: `scratch.hvac.humidifier.ElectricalHumidifier` does not expose air-side connection points compatible with BOB's connection inference at this library version. The humidifier is instantiated and present in the model but is **not connected** on the air-side to preserve duct continuity.
- **VFD connections**: The VFD class exposes multiple compatible electrical connection points; simple `>>` inference is ambiguous. VFDs are instantiated but their electrical connections to fans are not wired in this iteration.
- **Three-way valve**: `valve_3_way_1` is instantiated but not yet wired to the cooling/heating coil hydronic circuits.

---

## Comparison with Iteration 2026-03-13-2

See `../2026-03-13-2/` for the follow-up iteration.

