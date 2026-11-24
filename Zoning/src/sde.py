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


def dataset_path(config: dict, key: str) -> str | None:
    name = config["datasets"].get(key)
    if not name:
        return None
    return os.path.join(workspace(config), *name.split("/"))


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
    protected = {v.lower() for v in config["sde"].get("protected_versions", [])}
    log.info("Connected version: %s (expected %s)", version, expected)
    if version.lower() in protected and for_write:
        raise GuardError(f"Refusing to write to protected version {version}.")
    if version.lower() != expected.lower():
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
