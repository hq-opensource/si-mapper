# Iteration 2026-03-16-1

## Overview

Fourth iteration of the 223P ontology generation, run on **2026-03-16**, produced by the `_223p` sub-agent pipeline using **Claude Sonnet 4.5** (`github_copilot/claude-sonnet-4.5`) via LiteLLM.

This iteration is a direct follow-up to [2026-03-13-3](../2026-03-13-3/README.md). The primary improvement over the previous run is the **refinement of sensor observation points**: sensors are now associated with the most semantically accurate connection points on equipment (e.g. `heating_coil_1.airOutlet`, `filter_1.airInlet / airOutlet`) based on their grid position, rather than being attached to high-level `AirConnection` boundaries. The differential pressure sensor now correctly observes **two** connection points (inlet and outlet of the filter).

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
| `ontology.ttl` | Serialised Turtle ontology (1 937 lines) |
| `ontology.html` | HTML visualisation of the ontology graph |

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

### VFDs (2) ✅ Wired
| Label | Connected to |
|---|---|
| `vfd_1_a` | `fan_1_a` via `electricalOutlet >> electricalInlet` |
| `vfd_1_r` | `fan_1_r` via `electricalOutlet >> electricalInlet` |

### Other Equipment
| Label | Description |
|---|---|
| `filter_1` | Air filter |
| `humidifier_1` | Electrical humidifier (instantiated, air-side unconnected — see notes) |
| `valve_3_way_1` | Three-way mixing actuated proportional valve (instantiated, hydronic unconnected — see notes) |

### Sensors (7) ✅ Refined observation points
| Label | Measurement | Observation point |
|---|---|---|
| `sensor_temp_melange` | Mixed air temperature (°C) | `heating_coil_1.airOutlet` (grid position [19,8]) |
| `sensor_temp_retour` | Return air temperature (°C) | `ReturnAir` connection |
| `sensor_temp_alim` | Supply air temperature (°C) | `SupplyAir` connection |
| `sensor_low_limit_1` | Low-limit temperature (°C) | `SupplyAir` connection |
| `sensor_diff_pressure_1` | Differential static pressure across filter (Pa) | `filter_1.airInlet` **and** `filter_1.airOutlet` |
| `sensor_static_pressure_1` | Duct static pressure (Pa) | `SupplyAir` connection |
| `sensor_humidity_retour` | Return air relative humidity (%) | `ReturnAir` connection |

### Air Connections (5)
```
OutdoorAir ──► damper_paf_upper ──┐
OutdoorAir ──► damper_paf_lower ──┤
                                  ▼
ReturnAir ──► fan_1_r ──► damper_rav ──► MixedAir ──► damper_melange ──► filter_1
                                                                              │
                                                              cooling_coil_1 ◄┘
                                                                    │
                                                          heating_coil_1 ──► fan_1_a ──► SupplyAir

ReturnAir ──► damper_evac ──► fan_1_e ──► ExhaustAir
```

---

## Ontology Statistics

| Metric | Count |
|---|---|
| Named labels (`rdfs:label`) | 178 |
| `s223:ConnectionPoint` instances | 70 |
| `s223:Connectable` instances | 32 |
| `s223:Connection` instances | 14 |
| `s223:Function` instances | 11 |
| Lines in `.ttl` | 1 937 |

---

## Improvements vs Iteration 2026-03-13-3

| Topic | 2026-03-13-3 | 2026-03-16-1 |
|---|---|---|
| Model | `claude-sonnet-4.5` | `claude-sonnet-4.5` |
| Dual outdoor-air dampers | ✅ Both connected to `OutdoorAir` | ✅ Both connected to `OutdoorAir` |
| VFD–fan electrical wiring | ✅ Explicit `electricalOutlet >> electricalInlet` | ✅ Explicit `electricalOutlet >> electricalInlet` |
| Sensor observation points | Generic (`ReturnAir`, `SupplyAir`) | ✅ Position-based, more specific (`heating_coil_1.airOutlet`, `filter_1.airInlet/airOutlet`) |
| Differential pressure sensor | Single point | ✅ Two points (`filter_1.airInlet` + `filter_1.airOutlet`) |
| `s223:Function` count | 9 | 11 (+2) |
| `s223:Connection` count | 14 | 14 |
| `s223:ConnectionPoint` count | 70 | 70 |
| TTL lines | 1 937 | 1 937 |

---

## Known Limitations / Notes

- **Humidifier air-side**: `scratch.hvac.humidifier.ElectricalHumidifier` does not expose air-side connection points compatible with BOB's connection inference at this library version. The humidifier is instantiated and present in the model but is **not connected** on the air-side to preserve duct continuity.
- **Three-way valve**: `valve_3_way_1` is instantiated but not yet wired to the cooling/heating coil hydronic circuits.
- **`sensor_temp_melange` placement**: Based on grid position [19,8], this sensor sits between the heating coil [18,8] and the supply fan [21,8]. It is therefore attached to `heating_coil_1.airOutlet` rather than the generic `MixedAir` connection, which better reflects the physical layout.

