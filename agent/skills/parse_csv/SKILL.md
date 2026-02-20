---
name: parse_csv
description: Specialized instructions for parsing and extracting device information from BACnet filtered CSV files.
---

# BACnet CSV Parsing Skill

This skill provides a specialized knowledge base and prompt structure for LLMs to understand and extract information from BACnet-exported CSV files.

## 1. File Structure Overview

BACnet CSV exports typically follow this column schema:

| Column | Description | Example |
| :--- | :--- | :--- |
| **bacnet** | Unique point ID (`Controller.Object`) | `2500.AI11` |
| **nom** | Descriptive name (often in French) | `VITESSE RET. No.1A` |
| **valeur** | Current real-time value | `4,08806 A` |
| **unit** | Unit of measurement | `Amperes` |

## 2. BACnet Object Type Glossary

Understanding the suffix in the `bacnet` column is critical for identifying the "nature" of the data point.

| Suffix | Full Name | Description |
| :--- | :--- | :--- |
| **.AI** | Analog Input | Measured physical values (Temp, Pressure, Speed). |
| **.AO** | Analog Output | Control signals (0-100% modulation). |
| **.AV** | Analog Value | Internal setpoints or calculation buffers. |
| **.BI** | Binary Input | Physical status (Running/Stopped, Fault). |
| **.BO** | Binary Output | Physical commands (Start/Stop, Open/Close). |
| **.BV** | Binary Value | Internal software flags or logical triggers. |
| **.CO** | Control Loop | PID loop parameters (modulation logic). |
| **.PG** | Program | Control sequences and logic blocks. |
| **.SCH** | Schedule | Weekly or daily operation timers. |
| **.TL** | Trend Log | Historical data collection points. |

## 3. French-English Technical Dictionary

The `nom` column contains specific abbreviations. Use this mapping for extraction:

| French | English Equivalent | Context |
| :--- | :--- | :--- |
| **RET. / RETOUR** | Return | Return Air / Return Pipe |
| **ALIM. / ALIMENTATION**| Supply | Supply Air / Supply Pipe |
| **MEL. / MELANGE** | Mixing | Mixing Box / Outside Air Mixing |
| **EVAC. / EVACUATION** | Exhaust | Exhaust Air / Evacuation |
| **TEMP.** | Temperature | Thermal measurement |
| **PRES. / STAT.** | Pressure / Static | Airflow or Hydraulic pressure |
| **HUMI. / HUM** | Humidifier | Humidity control |
| **SERP. / ELECT.** | Coil / Electric | Electric Coil |
| **SERP. / REF.** | Coil / Cooling | Refroidissement / Cooling Coil |
| **ELECT.** | Electric | Electrical heating/power |
| **P.A.F** | Fresh Air Inlet | Prise d'Air Frais |
| **MOD.** | Modulation | Analog control (0-100%) |
| **DRIVE** | VFD | Variable Frequency Drive |
| **PC. / P.C.** | Setpoint | Point de Consigne |
| **FAUTE** | Fault | 0 = Active Fault, 1 = Normal |
| **VENT.** | Fan | Ventilateur |
| **A/D** | Start/Stop | Arrêt/Départ |
| **STATUT DIG** | Digital Status | Logical On/Off state |
| **CALCULS / CTRL** | Logic / Control | Control Program points |

## 4. Extraction Logic & Protocol

**Golden Rule:** When extracting a device, do not just look for the name. Look for the **Logical Grouping**. Devices are usually grouped by a suffix like `1A`, `1E`, or `1R`.

### Step-by-Step Extraction:
1. **Define keywords**: Map the English request to French keywords (e.g., "Exhaust" -> `EVAC`).
2. **Filter by Name**: Search the `nom` column for the keyword.
3. **Identify Grouping**: Notice if the points share a common ID (e.g., all exhaust points end in `1E`).
4. **Capture the Stack**: Include:
    *   **Measurements** (.AI)
    *   **Commands** (.BO, .AO)
    *   **Status** (.BI, .BV)
    *   **Config** (.AV)
    *   **Logic** (.PG)

## 5. Verification Checklist

- [ ] Does every extracted point match the target system ID (e.g. `1E`)?
- [ ] Have you included the control program (`.PG`) that governs the device?
- [ ] Are binary values (`.BI/.BO`) correctly identified as start/stop or status?
- [ ] Are setpoints (`.AV`) included for all modulation points (`.AO`)?

---
