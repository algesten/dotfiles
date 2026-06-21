#!/usr/bin/env python3
"""Query Bouni/kicad-jlcpcb-tools local catalog and project databases."""

from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

DEFAULT_CATALOG_DB = Path(
    "/Users/martin/Documents/KiCad/10.0/3rdparty/plugins/"
    "com_github_bouni_kicad-jlcpcb-tools/jlcpcb/current-parts-fts5.db"
)
DEFAULT_PROJECT_DB = Path("kicad/jlcpcb/project.db")

CATALOG_COLUMNS = (
    '"LCSC Part"',
    '"MFR.Part"',
    'Package',
    'Manufacturer',
    '"Library Type"',
    'Description',
    'Stock',
    'Price',
)


def connect(path: Path) -> sqlite3.Connection:
    if not path.exists():
        raise SystemExit(f"Database not found: {path}")
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    return con


def emit(rows: list[sqlite3.Row]) -> None:
    if not rows:
        return
    writer = csv.DictWriter(sys.stdout, fieldnames=rows[0].keys())
    writer.writeheader()
    for row in rows:
        writer.writerow(dict(row))


def cmd_meta(args: argparse.Namespace) -> None:
    with connect(args.catalog_db) as con:
        emit(con.execute("SELECT * FROM meta").fetchall())


def cmd_lookup(args: argparse.Namespace) -> None:
    cols = ", ".join(CATALOG_COLUMNS)
    placeholders = ",".join("?" for _ in args.lcsc)
    sql = f'SELECT {cols} FROM parts WHERE "LCSC Part" IN ({placeholders}) ORDER BY "LCSC Part"'
    with connect(args.catalog_db) as con:
        emit(con.execute(sql, args.lcsc).fetchall())


def cmd_search(args: argparse.Namespace) -> None:
    term = f"%{args.term}%"
    cols = ", ".join(CATALOG_COLUMNS[:-1])
    sql = f"""
        SELECT {cols}
        FROM parts
        WHERE "LCSC Part" LIKE ?
           OR "MFR.Part" LIKE ?
           OR Manufacturer LIKE ?
           OR Package LIKE ?
           OR Description LIKE ?
        ORDER BY "LCSC Part"
        LIMIT ?
    """
    with connect(args.catalog_db) as con:
        emit(con.execute(sql, (term, term, term, term, term, args.limit)).fetchall())


def package_hint_from_footprint(footprint: str) -> str:
    upper = footprint.upper()
    for token in ("SOIC", "MSOP", "TSSOP", "SSOP", "SOT-223", "SOT-23", "SOT-723", "SOT-363", "SOD-323", "SOD-523", "SOD-123", "DIP", "PDIP", "0805", "0603", "0402"):
        if token in upper:
            return token
    return ""


def search_stem(value: str) -> str:
    value = value.strip()
    if len(value) > 4 and value[-1].isalpha():
        return value[:-1]
    return value


def library_priority(library_type: str) -> int:
    order = {"basic": 0, "preferred": 1, "extended": 2}
    return order.get((library_type or "").strip().lower(), 3)


def stock_value(stock: object) -> int:
    try:
        return int(stock or 0)
    except (TypeError, ValueError):
        return 0


def min_unit_price(price: str) -> float:
    values = []
    for band in (price or "").split(","):
        if ":" not in band:
            continue
        _, value = band.split(":", 1)
        try:
            values.append(float(value))
        except ValueError:
            pass
    return min(values) if values else 999999.0


def stock_priority(stock: int) -> int:
    if stock >= 1000:
        return 0
    if stock >= 500:
        return 1
    if stock >= 100:
        return 2
    return 3


def is_user_supplier_lcsc(lcsc: str) -> bool:
    return (lcsc or "").upper().startswith("C99")


def candidate_sort_key(row: sqlite3.Row, stem: str) -> tuple[int, int, int, int, float, str]:
    stock = stock_value(row["Stock"])
    mfr = str(row["MFR.Part"] or "")
    return (
        1 if is_user_supplier_lcsc(str(row["LCSC Part"] or "")) else 0,
        library_priority(str(row["Library Type"] or "")),
        stock_priority(stock),
        -stock,
        min_unit_price(str(row["Price"] or "")),
        mfr,
    )


def cmd_candidates(args: argparse.Namespace) -> None:
    value = args.value
    package_hint = args.package or ""

    if args.reference:
        with connect(args.project_db) as project_con:
            row = project_con.execute(
                "SELECT reference, value, footprint, lcsc FROM part_info WHERE reference = ?",
                (args.reference,),
            ).fetchone()
        if row is None:
            raise SystemExit(f"Reference not found in project DB: {args.reference}")
        value = value or row["value"]
        package_hint = package_hint or package_hint_from_footprint(row["footprint"])

    if not value:
        raise SystemExit("Provide a reference or --value")

    stem = search_stem(value)
    term = f"%{stem}%"
    package_term = f"%{package_hint}%" if package_hint else "%"
    with connect(args.catalog_db) as con:
        rows = con.execute(
            """
            SELECT
              "LCSC Part",
              "MFR.Part",
              Package,
              Manufacturer,
              "Library Type",
              Description,
              Stock,
              Price,
              Datasheet
            FROM parts
            WHERE ("MFR.Part" LIKE ? OR Description LIKE ?)
              AND Package LIKE ?
            """,
            (term, term, package_term),
        ).fetchall()
    rows = sorted(rows, key=lambda row: candidate_sort_key(row, stem))[: args.limit]
    emit(rows)


def project_rows_with_catalog(args: argparse.Namespace, included_only: bool = True) -> list[dict[str, object]]:
    where = "WHERE (exclude_from_bom = 0 OR exclude_from_pos = 0)" if included_only else ""
    with connect(args.project_db) as project_con:
        project_rows = project_con.execute(
            f"""
            SELECT reference, value, footprint, lcsc, exclude_from_bom, exclude_from_pos
            FROM part_info
            {where}
            ORDER BY reference COLLATE NOCASE
            """
        ).fetchall()

    lcsc_values = sorted({row["lcsc"] for row in project_rows if row["lcsc"]})
    catalog_by_lcsc: dict[str, sqlite3.Row] = {}
    if lcsc_values:
        placeholders = ",".join("?" for _ in lcsc_values)
        with connect(args.catalog_db) as catalog_con:
            catalog_rows = catalog_con.execute(
                f"""
                SELECT "LCSC Part", "MFR.Part", Package, Manufacturer, "Library Type", Stock, Price
                FROM parts
                WHERE "LCSC Part" IN ({placeholders})
                """,
                lcsc_values,
            ).fetchall()
        catalog_by_lcsc = {row["LCSC Part"]: row for row in catalog_rows}

    rows: list[dict[str, object]] = []
    for row in project_rows:
        catalog = catalog_by_lcsc.get(row["lcsc"])
        rows.append(
            {
                "reference": row["reference"],
                "project_value": row["value"],
                "project_footprint": row["footprint"],
                "lcsc": row["lcsc"] or "",
                "exclude_from_bom": row["exclude_from_bom"],
                "exclude_from_pos": row["exclude_from_pos"],
                "catalog_mfr_part": catalog["MFR.Part"] if catalog else "",
                "catalog_package": catalog["Package"] if catalog else "",
                "catalog_manufacturer": catalog["Manufacturer"] if catalog else "",
                "catalog_type": catalog["Library Type"] if catalog else "",
                "catalog_stock": catalog["Stock"] if catalog else "",
                "catalog_price": catalog["Price"] if catalog else "",
            }
        )
    return rows


def cmd_bom_review(args: argparse.Namespace) -> None:
    rows = []
    for row in project_rows_with_catalog(args, included_only=True):
        lcsc = str(row["lcsc"] or "")
        catalog_type = str(row["catalog_type"] or "")
        stock = stock_value(row["catalog_stock"])
        base = {
            "reference": row["reference"],
            "project_value": row["project_value"],
            "project_footprint": row["project_footprint"],
            "lcsc": lcsc,
            "catalog_mfr_part": row["catalog_mfr_part"],
            "catalog_package": row["catalog_package"],
            "catalog_manufacturer": row["catalog_manufacturer"],
            "catalog_type": catalog_type,
            "catalog_stock": row["catalog_stock"],
            "exclude_from_bom": row["exclude_from_bom"],
            "exclude_from_pos": row["exclude_from_pos"],
        }
        if not lcsc:
            rows.append({"severity": "ERROR", "issue": "included_blank_lcsc", **base})
            continue
        if not row["catalog_mfr_part"]:
            rows.append({"severity": "ERROR", "issue": "selected_lcsc_not_in_catalog", **base})
            continue
        if is_user_supplier_lcsc(lcsc):
            rows.append({"severity": "ERROR", "issue": "user_supplier_lcsc_not_acceptable", **base})
        if stock < 100:
            rows.append({"severity": "ERROR", "issue": "stock_below_100", **base})
        elif stock < 500:
            rows.append({"severity": "WARN", "issue": "stock_below_500", **base})
        if catalog_type.lower() == "extended":
            rows.append({"severity": "REVIEW", "issue": "extended_part_consider_basic", **base})
        elif catalog_type.lower() == "preferred":
            rows.append({"severity": "REVIEW", "issue": "preferred_part_consider_basic", **base})
    severity_order = {"ERROR": 0, "WARN": 1, "REVIEW": 2}
    issue_order = {
        "included_blank_lcsc": 0,
        "selected_lcsc_not_in_catalog": 1,
        "user_supplier_lcsc_not_acceptable": 2,
        "stock_below_100": 3,
        "stock_below_500": 4,
        "extended_part_consider_basic": 5,
        "preferred_part_consider_basic": 6,
    }
    rows.sort(key=lambda row: (severity_order[row["severity"]], issue_order[row["issue"]], str(row["reference"])))
    if rows:
        writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def cmd_selected(args: argparse.Namespace) -> None:
    rows = []
    for row in project_rows_with_catalog(args, included_only=True):
        if not row["lcsc"]:
            continue
        rows.append(
            {
                "reference": row["reference"],
                "project_value": row["project_value"],
                "project_footprint": row["project_footprint"],
                "lcsc": row["lcsc"],
                "catalog_mfr_part": row["catalog_mfr_part"],
                "catalog_package": row["catalog_package"],
                "catalog_manufacturer": row["catalog_manufacturer"],
                "catalog_type": row["catalog_type"],
                "catalog_stock": row["catalog_stock"],
            }
        )
    emit(rows)


def cmd_unassigned(args: argparse.Namespace) -> None:
    with connect(args.project_db) as con:
        rows = con.execute(
            """
            SELECT reference, value, footprint, lcsc, exclude_from_bom, exclude_from_pos
            FROM part_info
            WHERE (exclude_from_bom = 0 OR exclude_from_pos = 0)
              AND COALESCE(lcsc, '') = ''
            ORDER BY reference COLLATE NOCASE
            """
        ).fetchall()
    emit(rows)


def cmd_timestamps(args: argparse.Namespace) -> None:
    root = args.project_root
    candidates = [
        root / "jlcpcb/project.db",
        root / "seq.kicad_pcb",
        *sorted((root / "jlcpcb/production_files").glob("*.csv")),
        *sorted((root / "jlcpcb/production_files").glob("*.zip")),
    ]
    rows = []
    for path in candidates:
        if path.exists():
            stat = path.stat()
            rows.append({"path": str(path), "mtime_epoch": int(stat.st_mtime), "size": stat.st_size})
    writer = csv.DictWriter(sys.stdout, fieldnames=["path", "mtime_epoch", "size"])
    writer.writeheader()
    writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog-db", type=Path, default=DEFAULT_CATALOG_DB)
    sub = parser.add_subparsers(dest="command", required=True)

    meta = sub.add_parser("meta", help="Show catalog metadata")
    meta.set_defaults(func=cmd_meta)

    lookup = sub.add_parser("lookup", help="Lookup exact LCSC part numbers")
    lookup.add_argument("lcsc", nargs="+")
    lookup.set_defaults(func=cmd_lookup)

    search = sub.add_parser("search", help="Search LCSC, MFR part, manufacturer, package, description")
    search.add_argument("term")
    search.add_argument("--limit", type=int, default=50)
    search.set_defaults(func=cmd_search)

    candidates = sub.add_parser("candidates", help="Find catalog candidates for a project reference or value/package")
    candidates.add_argument("reference", nargs="?", help="Project reference such as U11")
    candidates.add_argument("--project-db", type=Path, default=DEFAULT_PROJECT_DB)
    candidates.add_argument("--value", help="Part value/MFR stem to search when no reference is supplied")
    candidates.add_argument("--package", help="Package hint such as SOIC, SOT-23, 0805")
    candidates.add_argument("--limit", type=int, default=25)
    candidates.set_defaults(func=cmd_candidates)

    bom_review = sub.add_parser("bom-review", help="Run fab-prep BOM review for missing catalog parts, stock risk, and non-Basic selections")
    bom_review.add_argument("--project-db", type=Path, default=DEFAULT_PROJECT_DB)
    bom_review.set_defaults(func=cmd_bom_review)

    selected = sub.add_parser("selected", help="Join project selected parts to the catalog")
    selected.add_argument("--project-db", type=Path, default=DEFAULT_PROJECT_DB)
    selected.set_defaults(func=cmd_selected)

    unassigned = sub.add_parser("unassigned", help="Show BOM/POS included project rows with no LCSC")
    unassigned.add_argument("--project-db", type=Path, default=DEFAULT_PROJECT_DB)
    unassigned.set_defaults(func=cmd_unassigned)

    timestamps = sub.add_parser("timestamps", help="Show mtimes for project DB, PCB, and generated production files")
    timestamps.add_argument("--project-root", type=Path, default=Path("kicad"))
    timestamps.set_defaults(func=cmd_timestamps)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
