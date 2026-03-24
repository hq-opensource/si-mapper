---
name: skill-bacnet-points
description: Specialized instructions for identifying and extracting BACnet points from CSV files and mapping them to HVAC equipment on the grid.
---

# BACnet Extraction Skill

You specialize in BMS integration and point mapping. Your mission is to extract BACnet-specific metadata (Object Names, Object Instances, Descriptions) from technical CSV artifacts and map them to the corresponding equipment on the HVAC grid.

---

## Workflow

### 1. Ingest Files
- Call `ingest_category_files(category='bacnet')`.
- Call `load_artifacts` to load the files and read their content.

### 2. Parse the CSV Files

BACnet CSV exports follow this column schema:

| Column | Description | Example |
| :--- | :--- | :--- |
| **bacnet** | Unique point ID (`Controller.Object`) | `2500.AI11` |
| **nom** | Descriptive name (often in French) | `VITESSE RET. No.1A` |
| **valeur** | Current real-time value | `4,08806 A` |
| **unit** | Unit of measurement | `Amperes` |

#### BACnet Object Type Glossary

- The suffix in the `bacnet` column identifies the nature of the data point.
- Use asset `bacnet-device-types.csv` to map the suffix to the corresponding BACnet object type.

#### French-English Technical Dictionary

The `nom` column uses French abbreviations. Use this mapping for extraction:

| French | English Equivalent | Context |
| :--- | :--- | :--- |
| **RET. / RETOUR** | Return | Return Air / Return Pipe |
| **ALIM. / ALIMENTATION** | Supply | Supply Air / Supply Pipe |
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

#### Extraction Logic

**Golden Rule:** Look for the **Logical Grouping**, not just the name. Devices are grouped by a suffix like `1A`, `1E`, or `1R`.

1. **Define keywords**: Map the English equipment name to French keywords (e.g., "Exhaust" → `EVAC`).
2. **Filter by Name**: Search the `nom` column for the keyword.
3. **Identify Grouping**: Find points sharing a common suffix ID (e.g., all exhaust points end in `1E`).
4. **Capture the Stack**: Include measurements (.AI), commands (.BO, .AO), status (.BI, .BV), config (.AV), and logic (.PG).

### 3. Build the Metadata Structure

For each equipment piece found in the CSV, build a nested metadata structure. 

Save the :
- `bacnet` column as the key
- the `nom` column as `name`
- the `unit` column as `unit`
- the `device-identifier` needs to be extracted from the `bacnet` column prefix (e.g. `2500.AI11` → `2500`)
- the `object-type` needs to be mapped to the corresponding BACnet object type (see the glossary above), based on the suffix in the `bacnet` column (e.g. `2500.AI11` → `AI` → `analog-input`)
- the `object-instance` needs to be extracted from the `bacnet` column suffix (e.g. `2500.AI11` → `11`)

```json
{
  "AHU-1": {
    "bacnet": {
      "2500.AI11": { "name": "VITESSE RET. No.1A", "unit": "Amperes", "device-identifier": 2500, "object-type": "analog-input", "object-instance": 11 },
      "2500.AI13": { "name": "TEMP. ALIM. No.1A", "unit": "Celsius", "device-identifier": 2500, "object-type": "analog-input", "object-instance": 13 },
      "2500.AO14": { "name": "MOD. ALIM. No.1A", "unit": "%", "device-identifier": 2500, "object-type": "analog-output", "object-instance": 14 }
    }
  }
}
```

### 4. Write Metadata
- Call `write_metadata_batch` with your dictionary of updates to persist the BACnet data to the grid components.

### 5. Verify and Exit
- Confirm all identified equipment has been mapped.
- Summarize what was extracted and any equipment that could not be matched.

---

## Rules

- **Exact Matches First**: Prioritize exact equipment name matches (e.g., `VAV-101` matching `VAV_101`). If a match is partial but highly probable (e.g., `V-101`), note it in the metadata.
- **Nested Structure**: Always put results under the `"bacnet"` key to avoid collisions with other metadata.
- **Batch Processing**: Process all equipment in one pass to minimize file reads.

## Verification Checklist

- [ ] Does every extracted point match the target system ID (e.g. `1E`)?
- [ ] Have you included the control program (`.PG`) that governs the device?
- [ ] Are binary values (`.BI/.BO`) correctly identified as start/stop or status?
- [ ] Are setpoints (`.AV`) included for all modulation points (`.AO`)?
