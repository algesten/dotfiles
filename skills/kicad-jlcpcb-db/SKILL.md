---
name: kicad-jlcpcb-db
description: Query, validate, and review Bouni/kicad-jlcpcb-tools local databases for KiCad projects. Use when Codex needs to run a fab-prep BOM review, inspect selected LCSC/JLCPCB part assignments, search the plugin catalog database directly, join a project DB to the catalog, explain BOM/POS/POP data from the plugin, detect stale generated BOM/CPL files, or flag mismatched selected parts before fabrication.
---

# KiCad JLCPCB DB

## Overview

Use this skill for local database-backed inspection of the Bouni `kicad-jlcpcb-tools` plugin. Prefer direct SQLite queries over screenshots or inference when validating LCSC selections.

## Known Locations

Default plugin catalog directory on this machine:

```text
/Users/martin/Documents/KiCad/10.0/3rdparty/plugins/com_github_bouni_kicad-jlcpcb-tools/jlcpcb
```

Important files:

```text
current-parts-fts5.db  Full local JLCPCB/LCSC catalog used by the plugin
mappings.db            Footprint/value to LCSC mappings
corrections.db         Placement rotation/offset corrections
```

KiCad CLI is available on this machine at:

```text
/Users/martin/bin/kicad-cli
```

Use it for schematic/PCB validation when useful, especially ERC/DRC/export checks after symbol, footprint, or assignment changes.

Per-project plugin database, relative to a KiCad project repo:

```text
kicad/jlcpcb/project.db
```

Generated outputs, when present:

```text
kicad/jlcpcb/production_files/BOM-<project>.csv
kicad/jlcpcb/production_files/CPL-<project>.csv
kicad/jlcpcb/production_files/GERBER-<project>.zip
```

## Workflow

1. Identify the project DB, usually `kicad/jlcpcb/project.db`.
2. Query the catalog DB directly for exact LCSC part numbers or candidate MFR parts.
3. For a suspect reference, run `candidates <ref>` to search the catalog by project value and footprint-derived package hint. When exact plugin search behavior matters, load `references/plugin-search.md` first.
4. Join project assignments to the catalog before concluding a selected part is correct.
5. Compare generated BOM/CPL timestamps against the project DB and `.kicad_pcb`; stale outputs can preserve old assignments.
6. Treat blank catalog join columns as a real finding: the selected LCSC is not present in the active `current-parts-fts5.db` catalog.

## Fab BOM Review

When the user says `Run the BOM review to prepare for fab` or similar:

1. Run `meta`, `timestamps`, and `bom-review` against the project.
2. Report active issues in this order: included blank LCSC, selected LCSC missing from catalog, stock under 100, stock under 500, JLC-mounted THT/through-hole parts, Extended parts, then Preferred parts.
3. Treat `exclude_from_bom=1` and `exclude_from_pos=1` blank-LCSC rows as intentionally manual/DNP unless the user asks to review manual parts. Do not list them as active assembly problems.
4. For each Extended, low-stock, or JLC-mounted THT item, review one part at a time: inspect how it is used in the schematic/PCB, search the catalog for Basic/SMT equivalents, and consider whether a footprint/package or modest circuit redesign would improve manufacturability.
5. Do not call an alternative equivalent from search text alone. Confirm electrical role, value/specs, pinout, package/footprint, and stock. State when a proposed change requires schematic or PCB edits.
6. Keep unresolved items as an ordered punch list and remove items only after the project DB/schematic/PCB state confirms they are resolved or intentionally excluded.
7. Do not present stale generated BOM/CPL/Gerber files as the next component-review item. Timestamp checks are diagnostic context; mention stale production outputs only when the user asks for final fab readiness, export/package generation, or generated-file validation.

## Selection Policy

When ranking candidate JLC parts, use this default priority:

1. Reject any part JLCPCB marks `Consign` or user-supplier. Reject LCSC codes beginning `C99`, but do not treat that prefix as the only consign signal. Consign/user-supplier parts mean the user would have to send parts to JLCPCB, and they are not acceptable candidates unless the user explicitly overrides this rule.
2. Basic parts trump Extended parts. Prefer Basic strongly enough to consider package changes or modest circuit redesign if it materially improves manufacturability. Treat Preferred as better than Extended but below Basic unless the user says otherwise.
3. Stock matters. Parts under 500 in stock are a warning sign. Parts under 100 are a hard no unless the user explicitly overrides it. Prefer stock well above 1000; among equivalent choices, choose the part with the highest stock.
4. Price is secondary. Below USD 1 per part, price normally does not matter. Consider price only when the difference is meaningful, such as several USD per unit or a 5-10 USD build impact.
5. Avoid JLC-mounted THT when practical. Through-hole assembly adds an extra soldering/assembly fee and process step, so prefer SMT equivalents for parts JLCPCB will mount. A THT part can still be accepted when stock/function/package tradeoffs justify it, when it will be manually soldered, or when no credible SMT redesign exists.

The `candidates` helper sorts valid non-`C99` parts first, then by library type (`Basic`, then `Preferred`, then `Extended`), then stock tier (`>=1000`, `>=500`, `>=100`, `<100`), then stock quantity, then minimum listed unit price.


## User JLCPCB Inventory

For this user, the smallest practical JLCPCB assembly order is 2 units.

Parts intentionally supplied from the user's JLCPCB part library / prepaid inventory should not be treated as active stock problems during BOM review, even when catalog stock is low or zero. Still verify that the selected LCSC part matches the schematic role, package, and footprint.

Known user part library / prepaid inventory from project notes and user-provided JLCPCB inventory screenshots:

| LCSC | Part | Inventory note |
|------|------|----------------|
| C338758 | SN74HC163DR | prepaid/library part; ignore catalog stock warning |
| C432201 | STM32G031J6M6 | prepaid/library part; ignore catalog stock warning |
| C2652279 | TL084CPT | user library quantity 36 |
| C524236 | PCM3060PW | user library quantity 32 |
| C880681 | MAX6818EAP+T | user library quantity 10 |
| C91754 | HY931147C | user library quantity 46 |

## Query Helper

Use the bundled helper for common checks:

```bash
python3 ~/.codex/skills/kicad-jlcpcb-db/scripts/query_jlcpcb.py meta
python3 ~/.codex/skills/kicad-jlcpcb-db/scripts/query_jlcpcb.py lookup C2944066
python3 ~/.codex/skills/kicad-jlcpcb-db/scripts/query_jlcpcb.py search ADG419
python3 ~/.codex/skills/kicad-jlcpcb-db/scripts/query_jlcpcb.py candidates U11 --project-db kicad/jlcpcb/project.db
python3 ~/.codex/skills/kicad-jlcpcb-db/scripts/query_jlcpcb.py candidates --value ADG419BR --package SOIC
python3 ~/.codex/skills/kicad-jlcpcb-db/scripts/query_jlcpcb.py selected --project-db kicad/jlcpcb/project.db
python3 ~/.codex/skills/kicad-jlcpcb-db/scripts/query_jlcpcb.py bom-review --project-db kicad/jlcpcb/project.db
python3 ~/.codex/skills/kicad-jlcpcb-db/scripts/query_jlcpcb.py unassigned --project-db kicad/jlcpcb/project.db
python3 ~/.codex/skills/kicad-jlcpcb-db/scripts/query_jlcpcb.py timestamps --project-root kicad
```

The helper emits CSV by default. Use `--catalog-db` if the plugin DB is somewhere else.

## Direct SQLite Patterns

Read `references/schema.md` for column names and direct SQL examples. Read `references/plugin-search.md` when reproducing the plugin part selector search behavior, interpreting stock/price/type fields as the UI does, or explaining why direct SQLite search results differ from the GUI. The catalog table uses quoted names such as `"LCSC Part"` and `"MFR.Part"`; unquoted normalized names like `lcsc` do not work.

## Reporting Rules

When reporting validation results:

- State which database was queried and its catalog date from `meta`.
- Distinguish project DB assignments from generated BOM/CPL files.
- Quote exact LCSC, project value/footprint, catalog MFR part/package, library type, stock, and whether the project row is excluded from BOM/POS.
- Do not infer a correct replacement unless it was found by direct catalog search or the user asks for alternatives.
