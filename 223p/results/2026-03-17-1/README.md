# Iteration 2026-03-17-1

## Overview

Fifth iteration of the 223P ontology generation, run on **2026-03-17**, produced by the `_223p` sub-agent pipeline using **Claude Sonnet 4.5** (`github_copilot/claude-sonnet-4.5`) via LiteLLM.

This iteration is a direct follow-up to [2026-03-16-1](../2026-03-16-1/README.md). Unlike previous iterations which modelled a complete **Air-Handling Unit (AHU)**, this run targets a **simpler air distribution sub-system** extracted from a different grid layout — a single-fan topology with two filters and four sensors. Equipment labels carry auto-generated random suffixes, reflecting the raw output of the BOB library's identifier assignment.

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
| `ontology.ttl` | Serialised Turtle ontology (328 lines) |
| `ontology.html` | HTML visualisation of the ontology graph |

---

## Modelled System — Air Distribution Sub-System

The ontology describes a **simple air distribution system** with the following equipment and sensors:

### Fan (1)
| Label | Grid position | Description |
|---|---|---|
| `Fan_oDH2SAH9Ky` | [2,2] | Supply fan providing air movement through the duct system |

### Filters (2)
| Label | Grid position | Description |
|---|---|---|
| `Filter_BIBD1Uf4Dt` | [4,2] | Filter on the main horizontal duct |
| `Filter_Lpr2xZFucV` | [3,3] | Filter on the vertical duct branch |

### Sensors (4)
| Label | Type | Grid position | Measurement |
|---|---|---|---|
| `Sensor_USrSIXZqio` | `s223:HumiditySensor` | [3,4] | Relative humidity (%) |
| `Sensor_cM7fhnE8Ef` | `s223:PressureSensor` | [3,5] | Differential static pressure (Pa) |
| `Sensor_z6b5HCekeB` | `s223:HumiditySensor` | [5,2] | Relative humidity (%) |
| `Sensor_m9cuOHLBiE` | `s223:PressureSensor` | [6,2] | Differential static pressure (Pa) |

### Air Connections (2)
```
Fan_oDH2SAH9Ky ──► Filter_BIBD1Uf4Dt ──► Filter_Lpr2xZFucV
```

---

## Ontology Statistics

| Metric | Count |
|---|---|
| Named labels (`rdfs:label`) | 29 |
| `s223:ConnectionPoint` instances | 7 |
| `s223:Connectable` instances | 7 |
| `s223:Connection` instances | 2 |
| `s223:Function` instances | 2 |
| Lines in `.ttl` | 328 |

---

## Improvements vs Iteration 2026-03-16-1

| Topic | 2026-03-16-1 | 2026-03-17-1 |
|---|---|---|
| Model | `claude-sonnet-4.5` | `claude-sonnet-4.5` |
| System scope | Full AHU (5 dampers, 2 coils, 3 fans, 2 VFDs, 7 sensors) | Simpler sub-system (1 fan, 2 filters, 4 sensors) |
| Equipment labels | Semantic (e.g. `fan_1_a`, `cooling_coil_1`) | Auto-generated random suffixes |
| `s223:Connection` count | 14 | 2 |
| `s223:ConnectionPoint` count | 70 | 7 |
| `s223:Function` count | 11 | 2 |
| TTL lines | 1 937 | 328 |

---

## Known Limitations / Notes

- **Sensors not linked to connection points**: Sensors (`HumiditySensor`, `PressureSensor`) are instantiated and added to the system but do not observe specific equipment connection points. They carry observable properties (`RelativeHumidity`, `DifferentialStaticPressure`) but are not spatially anchored via `s223:observes` → connection point.
- **Auto-generated labels**: Equipment and sensor labels include random alphanumeric suffixes (e.g. `Fan_oDH2SAH9Ky`) rather than semantic identifiers, limiting human readability of the ontology.
- **`Filter_Lpr2xZFucV` outlet unconnected**: The vertical-duct filter's `airOutlet` connection point is not connected to any downstream equipment; the duct chain terminates at that point.
- **No electrical connections**: The fan's `electricalInlet` is present in the model but no VFD or power source is wired to it.

