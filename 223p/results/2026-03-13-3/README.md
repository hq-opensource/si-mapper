# Iteration 2026-03-13-3

## Overview

Third iteration of the 223P ontology generation run on **2026-03-13**, produced by the `_223p` sub-agent pipeline using **Claude Sonnet 4.5** (`github_copilot/claude-sonnet-4.5`) via LiteLLM.

This iteration is a direct follow-up to [2026-03-13-2](../2026-03-13-2/README.md). The agent was pinned back to `claude-sonnet-4.5` (the forced model in `agent/sub_agents/_223p/agent.py`) to compare quality and completeness against the `claude-sonnet-4.6` run. The resulting ontology maintains the dual outdoor-air damper topology and the VFD–fan electrical wiring introduced in iteration 2, with minor structural refinements.

---

## Model

| Property | Value |
|---|---|
| Model | `claude-sonnet-4.5` |
| Provider | GitHub Copilot (via LiteLLM) |
| Agent | `agent/sub_agents/_223p/` |
| Max iterations | 50 |

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

### Air Connections
```
OutdoorAir ──► damper_paf_upper ──┐
OutdoorAir ──► damper_paf_lower ──┤
                                  ▼
ReturnAir ──► fan_1_r ──► damper_rav ──► MixedAir ──► damper_melange ──► filter_1
                                                                              │
                                                              cooling_coil_1 ◄┘
                                                                    │
                                                              fan_1_a ──► heating_coil_1 ──► SupplyAir

ReturnAir ──► damper_evac ──► fan_1_e ──► ExhaustAir
```

---

## Ontology Statistics

| Metric | Count |
|---|---|
| Total `s223:*` instances | 164 |
| Named labels (`rdfs:label`) | 178 |
| `s223:ConnectionPoint` instances | 70 |
| `s223:Connectable` instances | 32 |
| `s223:Connection` instances | 14 |
| `s223:Function` instances | 9 |
| Lines in `.ttl` | 1 937 |

---

## Improvements vs Iteration 2026-03-13-2

| Topic | 2026-03-13-2 | 2026-03-13-3 |
|---|---|---|
| Model | `claude-sonnet-4.6` | `claude-sonnet-4.5` |
| Dual outdoor-air dampers | ✅ Both connected to `OutdoorAir` | ✅ Both connected to `OutdoorAir` |
| VFD–fan electrical wiring | ✅ Explicit `electricalOutlet >> electricalInlet` | ✅ Explicit `electricalOutlet >> electricalInlet` |
| `s223:ConnectionPoint` count | — | 70 |
| `s223:Connection` count | 14 | 14 |
| TTL lines | 1 938 | 1 937 (−1) |

---

## Known Limitations / Notes

- **Humidifier air-side**: `scratch.hvac.humidifier.ElectricalHumidifier` does not expose air-side connection points compatible with BOB's connection inference at this library version. The humidifier is instantiated and present in the model but is **not connected** on the air-side to preserve duct continuity.
- **Three-way valve**: `valve_3_way_1` is instantiated but not yet wired to the cooling/heating coil hydronic circuits.

