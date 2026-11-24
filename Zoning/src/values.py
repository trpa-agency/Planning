"""Value normalization shared by the fix rebuild and posting scripts."""

from __future__ import annotations

NUMERIC_FIELDS = {"density"}


def norm(value, numeric: bool = False):
    """Normalize for comparison.

    Blank is None. Text ignores case and collapses whitespace, including line breaks.
    Only numeric fields compare as numbers; zoning IDs must stay text ("45" is not "045").
    """
    if value is None:
        return None
    text = " ".join(str(value).split())
    if text == "":
        return None
    if numeric:
        try:
            number = float(text)
            return int(number) if number.is_integer() else number
        except ValueError:
            pass
    return text.casefold()


def same(a, b, field: str = "") -> bool:
    numeric = field.casefold() in NUMERIC_FIELDS
    return norm(a, numeric) == norm(b, numeric)


def use_key(value) -> str:
    return " ".join(str(value or "").casefold().split())


def table_of(row: dict, default: str) -> str:
    """Map a fix row's TABLE column to a dataset key."""
    name = str(row.get("TABLE", "")).replace("_", "").casefold()
    if name.startswith("special"):
        return "special_designation"
    if name.startswith("permissible"):
        return "permissible_uses"
    return default
