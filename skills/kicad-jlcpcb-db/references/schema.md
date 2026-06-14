# kicad-jlcpcb-tools Database Schema

## Catalog DB

Default path:

```text
/Users/martin/Documents/KiCad/10.0/3rdparty/plugins/com_github_bouni_kicad-jlcpcb-tools/jlcpcb/current-parts-fts5.db
```

Tables:

```sql
CREATE VIRTUAL TABLE parts using fts5 (
  'LCSC Part',
  'First Category',
  'Second Category',
  'MFR.Part',
  'Package',
  'Solder Joint' unindexed,
  'Manufacturer',
  'Library Type',
  'Description',
  'Datasheet' unindexed,
  'Price' unindexed,
  'Stock' unindexed,
  tokenize='trigram'
);

CREATE TABLE mapping (
  'footprint',
  'value',
  'LCSC'
);

CREATE TABLE meta (
  'filename',
  'size',
  'partcount',
  'date',
  'last_update'
);
```

The `parts` table is an FTS5 virtual table. Always quote names containing spaces or punctuation.

## Project DB

Typical path:

```text
kicad/jlcpcb/project.db
```

Schema observed in this project:

```sql
CREATE TABLE part_info (
  reference NOT NULL PRIMARY KEY,
  value TEXT NOT NULL,
  footprint TEXT NOT NULL,
  lcsc TEXT,
  stock NUMERIC,
  exclude_from_bom NUMERIC DEFAULT 0,
  exclude_from_pos NUMERIC DEFAULT 0
);

CREATE TABLE metadata (
  key TEXT NOT NULL PRIMARY KEY,
  value TEXT NOT NULL
);
```

`exclude_from_bom=0` means included in generated BOM. `exclude_from_pos=0` means included in CPL/POS placement output.

## Useful Queries

Catalog metadata:

```sql
SELECT * FROM meta;
```

Exact LCSC lookup:

```sql
SELECT "LCSC Part", "MFR.Part", Package, Manufacturer, "Library Type", Description, Stock, Price
FROM parts
WHERE "LCSC Part" = 'C2944066';
```

Part-name search:

```sql
SELECT "LCSC Part", "MFR.Part", Package, Manufacturer, "Library Type", Description, Stock
FROM parts
WHERE "MFR.Part" LIKE '%ADG419%' OR Description LIKE '%ADG419%'
ORDER BY "LCSC Part";
```

Package-filtered candidate search:

```sql
SELECT "LCSC Part", "MFR.Part", Package, Manufacturer, "Library Type", Description, Stock, Price, Datasheet
FROM parts
WHERE ("MFR.Part" LIKE '%ADG419BR%' OR Description LIKE '%ADG419BR%')
  AND Package LIKE '%SOIC%'
ORDER BY CAST(Stock AS INTEGER) DESC;
```

Join project assignments to catalog:

```sql
ATTACH DATABASE 'kicad/jlcpcb/project.db' AS proj;
SELECT
  p.reference,
  p.value AS project_value,
  p.footprint AS project_footprint,
  p.lcsc,
  parts."MFR.Part" AS catalog_mfr_part,
  parts.Package AS catalog_package,
  parts.Manufacturer AS catalog_manufacturer,
  parts."Library Type" AS catalog_type,
  parts.Stock AS catalog_stock
FROM proj.part_info p
LEFT JOIN parts ON parts."LCSC Part" = p.lcsc
WHERE p.exclude_from_bom = 0 AND COALESCE(p.lcsc, '') <> ''
ORDER BY p.reference COLLATE NOCASE;
```

Find BOM/POS included parts without LCSC:

```sql
SELECT reference, value, footprint, lcsc
FROM part_info
WHERE exclude_from_bom = 0 AND COALESCE(lcsc, '') = ''
ORDER BY reference COLLATE NOCASE;
```

## Known Interpretation

Generated `BOM-*.csv` and `CPL-*.csv` are build artifacts. Their contents can be stale if the plugin database or PCB changed after generation. Compare timestamps with `project.db` and `.kicad_pcb` before treating generated CSVs as current.

## Candidate Selection Policy

Default ranking for suggested JLC/LCSC alternatives:

1. Library type: Basic first, Preferred second, Extended last. Basic can justify packaging/circuit changes.
2. Stock: under 500 is a warning sign; under 100 is a hard no unless explicitly overridden; prefer above 1000; choose highest stock among equivalents.
3. Price: ignore small differences under USD 1 per part; consider only meaningful per-unit or total build deltas.
4. Assembly/package: avoid JLC-mounted THT when a credible SMT option exists. Through-hole assembly adds an extra JLCPCB soldering/assembly fee and process step. THT can still be accepted for manual soldering, uniquely suitable parts, or when the SMT alternative needs disproportionate redesign.

This is a ranking policy, not proof of electrical equivalence. Confirm voltage range, pinout, package, and electrical specs before changing a circuit or package.


## Plugin Search Screen Interpretation

For the part selector UI query semantics, catalog variants, result columns, price-band interpretation, and the difference between FTS5 `MATCH` and broad `LIKE` searches, read `plugin-search.md`.
