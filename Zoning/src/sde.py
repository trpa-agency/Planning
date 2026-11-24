"""Workspace, version, and cursor helpers for SDE and test geodatabases."""

from __future__ import annotations

import csv
import logging
import os
from pathlib import Path

import arcpy

SQ_METERS_PER_ACRE = 4046.8564224


class GuardError(RuntimeError):
    """A safety check failed; nothing was written."""


def workspace(config: dict) -> str:
    return config["sde"]["connection"]


_RESOLVED: dict[tuple[str, str], str] = {}


def dataset_path(config: dict, key: str) -> str | None:
    """Return the full path to a configured dataset.

    A name with a feature dataset prefix that does not exist falls back to the bare name
    at the workspace root, since standalone tables cannot live in a feature dataset.
    """
    name = config["datasets"].get(key)
    if not name:
        return None
    ws = workspace(config)
    cache_key = (ws, name)
    if cache_key in _RESOLVED:
        return _RESOLVED[cache_key]
    parts = [p for p in name.replace("\\", "/").split("/") if p]
    path = os.path.join(ws, *parts)
    if len(parts) > 1 and not arcpy.Exists(path):
        root = os.path.join(ws, parts[-1])
        if arcpy.Exists(root):
            logging.getLogger("sde").info("%s not found; using %s", path, root)
            path = root
    _RESOLVED[cache_key] = path
    return path


def _clean(name: str) -> str:
    """Lowercase and drop quotes; OS-authenticated owners print as "DOMAIN\\USER"."""
    return str(name).replace('"', "").strip().lower()


def _matches(version: str, names) -> bool:
    """Match a version against names; a name without an owner prefix matches any owner."""
    version = _clean(version)
    tail = version.rsplit(".", 1)[-1] if "." in version else version
    for name in names:
        name = _clean(name)
        if version == name or ("." not in name and tail == name):
            return True
    return False


def connected_version(ws: str) -> str | None:
    """Return the version a workspace points at, or None for a non-enterprise workspace."""
    desc = arcpy.Describe(ws)
    if desc.workspaceType != "RemoteDatabase":
        return None
    return desc.connectionProperties.version


def check_version(config: dict, log: logging.Logger, for_write: bool) -> str | None:
    """Confirm the connection points at the QA edit version.

    For a write, a wrong version or a protected version raises GuardError.
    For a read, a wrong version only logs a warning.
    """
    ws = workspace(config)
    if not arcpy.Exists(ws):
        raise GuardError(f"Connection not found: {ws}")
    version = connected_version(ws)
    if version is None:
        log.info("Workspace %s is not an enterprise geodatabase; version check skipped.", ws)
        return None
    expected = config["sde"]["edit_version"]
    protected = config["sde"].get("protected_versions", [])
    log.info("Connected version: %s (expected %s)", version, expected)
    if _matches(version, protected):
        log.warning("Connected to protected version %s; read only.", version)
    if _matches(version, protected) and for_write:
        raise GuardError(f"Refusing to write to protected version {version}.")
    if not _matches(version, [expected]):
        message = f"Connected to {version}, not the QA edit version {expected}."
        if for_write:
            raise GuardError(message)
        log.warning(message)
    return version


def is_versioned(path: str) -> bool:
    return bool(getattr(arcpy.Describe(path), "isVersioned", False))


def sql_text(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def sql_in(field: str, values) -> str:
    values = list(values)
    if not values:
        return "1 = 0"
    return f"{field} IN ({', '.join(sql_text(v) for v in values)})"


def norm_guid(value) -> str:
    return str(value or "").strip().upper()


def rows(path: str, fields: list[str], where: str | None = None) -> list[dict]:
    with arcpy.da.SearchCursor(path, fields, where) as cursor:
        return [dict(zip(fields, row)) for row in cursor]


def count(path: str, where: str | None = None) -> int:
    with arcpy.da.SearchCursor(path, ["OID@"], where) as cursor:
        return sum(1 for _ in cursor)


def acres(geometry) -> float:
    return geometry.area / SQ_METERS_PER_ACRE if geometry else 0.0


def write_csv(path: Path, records: list[dict], fields: list[str] | None = None) -> None:
    fields = fields or (list(records[0].keys()) if records else ["note"])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records or [])
