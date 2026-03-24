# Iteration 2026-03-24-1

## Overview

Sixth iteration of the 223P ontology generation, run on **2026-03-24**, produced by the `_223p` sub-agent pipeline using **Claude Sonnet 4.5** (`github_copilot/gpt-5.1-codex-max`) via LiteLLM.

This iteration is a direct follow-up to [2026-03-17-1](../2026-03-17-1/README.md). It returns to modelling a **complete Air-Handling Unit (AHU-1)** — the same full-scope system as [2026-03-16-1](../2026-03-16-1/README.md) — but with two major additions: **BACnet external references** are now attached to sensors, and all equipment uses **semantic labels** (e.g. `D-FA1`, `CC-1`, `VFD-1-A`) rather than auto-generated identifiers. The resulting ontology is the canonical model used in `223p/src/ontology.py`.

---

## Model

| Property | Value |
|---|---|
| Model | `gpt-5.1-codex-max` |
| Provider | GitHub Copilot (via LiteLLM) |
| Agent | `agent/sub_agents/_223p/` |
| Max iterations | 100 |

---

## Output Files

| File | Description |
|---|---|
| `ontology.py` | Generated Python source using the **BOB** and **SCRATCH** libraries |
| `ontology.ttl` | Serialised Turtle ontology (961 lines) |
| `ontology.html` | HTML visualisation of the ontology graph |

---

## Modelled System — AHU-1 Overview

The ontology describes a complete **Air-Handling Unit** (`AHU-1 System`) with the following equipment and sub-systems:

### Dampers (4)
| Label | Description |
|---|---|
| `D-FA1` | Outdoor air damper – upper path |
| `D-FA2` | Outdoor air damper – lower path |
| `D-MIX` | Mixed air damper |
| `D-EXH` | Exhaust air damper |

### Coils (2)
| Label | Description |
|---|---|
| `CC-1` | Chilled-water cooling coil |
| `HC-1` | Electrical heating coil |

### Fans (3)
| Label | Description |
|---|---|
| `1-A` | Supply air fan |
| `1-R` | Return air fan |
| `1-E` | Exhaust air fan |

### VFDs (2) ✅ Wired
| Label | Connected to |
|---|---|
| `VFD-1-A` | `1-A` (supply fan) |
| `VFD-1-R` | `1-R` (return fan) |

### Other Equipment
| Label | Description |
|---|---|
| `FLT-1` | Air filter |
| `HUM-1` | Humidifier (instantiated, air-side not connected) |

### Sensors (8) ✅ With BACnet references
| Label | Type | Measurement | BACnet Point |
|---|---|---|---|
| `ST-MIX` | `AirTemperatureSensor` | Mixed air temperature (°C) | `2500/analog-input,15` |
| `ST-SUP` | `AirTemperatureSensor` | Supply air temperature (°C) | `2500/analog-input,13` |
| `ST-RET` | `AirTemperatureSensor` | Return air temperature (°C) | `2500/analog-input,14` |
| `SH-RET` | `AirHumiditySensor` | Return air relative humidity (%) | `2500/analog-input,16` |
| `SH-SUP` | `AirHumiditySensor` | Supply air relative humidity (%) | *(no BACnet point)* |
| `SSP-SUP` | `AirDifferentialStaticPressureSensor` | Supply duct static pressure (inWC) | `2500/analog-input,17` |
| `SDP-FLT` | `AirDifferentialStaticPressureSensor` | Differential pressure across filter (inWC) | `2500/analog-input,18` |
| `SLL-1` | `AirTemperatureSensor` | Low-limit frost protection temperature | `2500/binary-value,254` |

### Air Connections (6)
```
OutdoorAir ──► D-FA1 ──┐
OutdoorAir ──► D-FA2 ──┴──► MixedAir ──► FLT-1 ──► CC-1 ──► HC-1 ──► 1-A ──► SupplyAir

ReturnAirFromZone ──► 1-R ──► ReturnAir ──► D-EXH ──► 1-E ──► ExhaustAir
```

---

## Ontology Statistics

| Metric | Count |
|---|---|
| Named labels (`rdfs:label`) | 82 |
| `s223:ConnectionPoint` instances | 33 |
| `s223:Connectable` instances | 21 |
| `s223:Connection` instances | 12 |
| `s223:Function` instances | 2 |
| BACnet external references | 29 |
| Lines in `.ttl` | 961 |

---

## Improvements vs Iteration 2026-03-17-1

| Topic | 2026-03-17-1 | 2026-03-24-1 |
|---|---|---|
| System scope | Simple sub-system (1 fan, 2 filters, 4 sensors) | Full AHU (4 dampers, 2 coils, 3 fans, 2 VFDs, 8 sensors) |
| Equipment labels | Auto-generated random suffixes | Semantic labels (e.g. `D-FA1`, `CC-1`) |
| BACnet references | None | 7 sensors wired to BACnet points |
| Humidifier | Not present | Instantiated (`HUM-1`) |
| VFDs | Not present | 2 VFDs wired to fans |
| `s223:Connection` count | 2 | 12 |
| `s223:ConnectionPoint` count | 7 | 33 |
| TTL lines | 328 | 961 |

---

## Known Limitations / Notes

- **`HUM-1` air-side unconnected**: The humidifier is instantiated and added to the system but its `airInlet`/`airOutlet` connection points are not wired into the main airflow path.
- **`SH-SUP` has no BACnet point**: The supply humidity sensor (`SH-SUP`) was provided with an empty BACnet metadata object (`{}`); no `BACnetExternalReference` is attached to it in the ontology.
- **`D-MIX` not wired**: `D-MIX` (mixed air damper) is instantiated and included in the system assembly but is not connected to any air path in the Python source.
- **Unit fallback for pressure sensors**: `SSP-SUP` and `SDP-FLT` use `UNIT.IN_WG` only if that constant exists on the `UNIT` enum; otherwise no unit is assigned.

