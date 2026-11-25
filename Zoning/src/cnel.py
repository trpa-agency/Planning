"""District CNEL reference table: schema and CSV loading, shared by the CNEL scripts."""

from __future__ import annotations

import csv
import re
from collections import Counter

from src import io
from src.sde import GuardError

# Table schema: (field, type, length). LEGACY_CNEL keeps the old layer's value for review.
FIELDS = [
    ("ZONING_ID", "TEXT", 50),
    ("CNEL", "SHORT", None),
    ("CORRIDOR_CNEL", "TEXT", 150),
    ("CNEL_NOTE", "TEXT", 255),
    ("BASIS", "TEXT", 20),
    ("SOURCE_DOC", "TEXT", 150),
    ("SOURCE_PAGE", "TEXT", 10),
    ("DECISION", "TEXT", 10),
    ("LEGACY_CNEL", "SHORT", None),
]
NAMES = [f[0] for f in FIELDS]


def to_int(value):
    text = str(value or "").strip()
    return int(float(text)) if text else None


def load_csv(config: dict) -> dict[str, dict]:
    """Read and validate the reference CSV. Returns rows keyed by ZONING_ID.

    Each row holds the typed table values plus "_csv", the raw CSV record.
    """
    path = io.resolve(config["cnel"]["csv"])
    with path.open(encoding="utf-8", newline="") as handle:
        raw = list(csv.DictReader(handle))
    valid = set(config["cnel"]["valid_values"])
    problems = []
    dupes = [k for k, n in Counter(r["ZONING_ID"] for r in raw).items() if n > 1]
    if dupes:
        problems.append(f"duplicate ZONING_ID {dupes}")
    rows = {}
    for r in raw:
        zid = r["ZONING_ID"].strip()
        row = {name: (r.get(name) or "").strip() for name in NAMES}
        row["ZONING_ID"] = zid
        row["CNEL"] = to_int(row["CNEL"])
        row["LEGACY_CNEL"] = to_int(row["LEGACY_CNEL"])
        if row["CNEL"] not in valid:
            problems.append(f"{zid}: CNEL {row['CNEL']} not in {sorted(valid)}")
        for name, ftype, length in FIELDS:
            if ftype == "TEXT" and len(row[name]) > length:
                problems.append(f"{zid}: {name} is {len(row[name])} characters, field holds {length}")
        rows[zid] = {**row, "_csv": r}
    if problems:
        raise GuardError("Reference CSV failed checks: " + "; ".join(problems))
    return rows


# Route codes used for corridors, and the wording plan documents use for each.
ROUTE_WORDS = {
    "US 50": r"(?:US|Highway) 50",
    "SR 28": r"(?:SR|Highway) 28",
    "SR 89": r"(?:SR|Highway) 89",
    "SR 207": r"(?:SR|Highway) 207",
    "SR 267": r"(?:SR|Highway|Route) 267",
    "SR 431": r"(?:SR|Highway) 431",
}


def parse_corridors(text: str, district_cnel: int | None) -> dict[str, tuple[int, str]]:
    """Parse a CORRIDOR_CNEL value into {route: (cnel, kind)}.

    kind is "stated" (the document sets a corridor value), "permissible" (the document
    allows an override "where applicable"), or "included" (the document folds the corridor
    into the district value). Clauses that name no route, such as the airport corridor,
    are ignored.
    """
    out: dict[str, tuple[int, str]] = {}
    for clause in (c.strip() for c in (text or "").split(";")):
        if not clause or ":" not in clause:
            continue
        head, tail = clause.rsplit(":", 1)
        routes = [r for r, pattern in ROUTE_WORDS.items() if re.search(pattern, head)]
        if not routes:
            continue
        if "included in district value" in tail:
            value, kind = district_cnel, "included"
        else:
            match = re.search(r"\d\d", tail)
            if not match:
                continue
            value = int(match.group())
            kind = "permissible" if "permissible" in tail else "stated"
        for route in routes:
            out[route] = (value, kind)
    return out
