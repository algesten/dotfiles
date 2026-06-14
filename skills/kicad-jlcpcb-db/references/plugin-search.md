# Plugin Search Screen and Database Interpretation

This reference captures behavior verified from the local Bouni/kicad-jlcpcb-tools source in:

```text
/Users/martin/Documents/KiCad/10.0/3rdparty/plugins/com_github_bouni_kicad-jlcpcb-tools
```

Relevant files: `library.py`, `partselector.py`, `partselector_columns.py`, `search_escape.py`, and `dblib/__init__.py`.

## Active Catalog Variant

The plugin defaults to `DEFAULT_LIBRARY = "current-parts"`, which maps to:

```text
current-parts-fts5.db
```

The `current-parts` database is generated with a filter equivalent to:

```sql
NOT (stock = 0 AND last_on_stock < obsolete_threshold)
```

where the default obsolete threshold is 365 days. So `current-parts-fts5.db` is not the full historical catalog; it is the current/non-obsolete catalog used by the search UI by default.

Other configured variants exist in source:

```text
basic-preferred -> basic-parts-fts5.db, where basic = 1 OR preferred = 1
all-parts       -> parts-fts5.db, no filtering
empty           -> empty-parts-fts5.db
```

For fab checks, use `current-parts-fts5.db` unless the user explicitly asks to compare another catalog variant.

## Search Result Columns

The part selector table columns map to DB fields as follows:

```text
LCSC         -> LCSC Part
MFR Number   -> MFR.Part
Package      -> Package
Type         -> Library Type
Params       -> derived from Description, First Category, Package; not a DB field
Stock        -> Stock
Manufacturer -> Manufacturer
Description  -> Description
Price        -> Price
```

The selector also fetches `First Category` as an extra DB field so it can derive/display `Params`.

## Search Query Semantics

The UI refuses to search if both Keyword and Part Number are empty.

The selected DB fields are queried from the FTS5 `parts` table. The result is ordered by the active UI sort column using a natural sort collation and is limited to 1000 rows. If the UI reports `limited`, it means 1000 rows were returned, not that exactly 1000 parts exist.

Keyword search behavior:

- The keyword box is split on spaces.
- Terms with length >= 3 become FTS5 phrase tokens in `parts MATCH ...`.
- Terms with length < 3 are searched only against lowercase `description` with SQL `LIKE '%term%' ESCAPE '\'`.
- The help text says keyword search is automatically wrapped in wildcards, but the current code actually uses FTS5 phrase tokens for >=3 char terms and LIKE only for <3 char terms. For direct SQLite searches, use broader `LIKE` only when you intentionally want behavior wider than the plugin UI.

Field filter behavior:

```text
Manufacturer  -> FTS5 field query "Manufacturer":"value"
Package       -> FTS5 field query "Package":"value"
Category      -> FTS5 field query "First Category":"value", except blank/All
Subcategory   -> FTS5 field query "Second Category":"value"
Part Number   -> FTS5 field query "MFR.Part":"value"
Solder Joints -> FTS5 field query "Solder Joint":"value"
```

## Category and Subcategory Behavior

The plugin has a separate `categories` table in the active parts DB:

```sql
CREATE TABLE categories (
  'First Category',
  'Second Category'
);
```

`Library.categories` builds an in-memory `category_map` from:

```sql
SELECT *
FROM categories
ORDER BY UPPER("First Category"), UPPER("Second Category")
```

The category list returned to the UI is the cached category keys with `All` inserted at index 0. The code also initializes an empty category key `""` with no subcategories.

Subcategories are not global. When the selected category changes, the UI clears the subcategory combo and populates it with `category_map[category]`. So only subcategories for the selected first category are shown.

Search behavior:

- Category is ignored if it is blank or exactly `All`.
- Otherwise category adds an FTS5 field query against `"First Category"`.
- Subcategory adds an FTS5 field query against `"Second Category"` whenever nonblank.
- The source does not independently verify that a manually typed subcategory belongs to the selected category; it just adds both field filters if both are nonblank.

For direct database work, use the `categories` table to discover valid first/second category pairs before constructing category-limited searches.

Library type checkboxes add:

```sql
"Library Type" IN ("Basic", "Extended", "Preferred")
```

using only the checked types.

The `Only show parts in stock` checkbox adds:

```sql
"Stock" > "0"
```

Note that the plugin stores `Stock` as text in the FTS table. For ranking and thresholds, cast stock to integer in direct SQLite queries.

## Price Interpretation

`Price` is a comma-separated set of quantity bands such as `1-9:0.123,10-99:0.100,100-:0.080`. The UI chooses the unit price for the number of selected references being assigned, then displays unit and total cost. For direct candidate ranking, parse the numeric band prices and prefer lower price only after Basic/Preferred/Extended and stock ranking.

## Practical Query Guidance

For plugin-faithful UI reproduction, use FTS5 `MATCH` and the field query forms above. For BOM review and equivalence search, it is acceptable to use wider `LIKE` searches over `MFR.Part`, `Description`, and `Package`, but report that this is broader than the plugin UI.

Always quote DB columns containing spaces or punctuation: `"LCSC Part"`, `"MFR.Part"`, `"Library Type"`, `"First Category"`, `"Second Category"`, and `"Solder Joint"`.
