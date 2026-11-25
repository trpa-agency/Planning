"""Paged ArcGIS REST pulls into a geodatabase."""

from __future__ import annotations

import json
import logging
import os
import tempfile
import urllib.parse
import urllib.request

import arcpy

log = logging.getLogger("sde")


def query_all(layer_url: str, fields: str = "*", where: str = "1=1", out_sr: int = 26910,
              page_size: int = 1000) -> dict:
    """Return the layer's features as one Esri JSON feature set, paging by OBJECTID."""
    features, offset, payload = [], 0, {}
    while True:
        params = urllib.parse.urlencode({
            "where": where, "outFields": fields, "outSR": out_sr, "f": "json",
            "resultOffset": offset, "resultRecordCount": page_size, "orderByFields": "OBJECTID",
        })
        with urllib.request.urlopen(f"{layer_url}/query?{params}", timeout=120) as resp:
            payload = json.load(resp)
        if "error" in payload:
            raise RuntimeError(f"{layer_url}: {payload['error']}")
        features += payload.get("features", [])
        if not payload.get("exceededTransferLimit"):
            break
        offset += page_size
    payload["features"] = features
    return payload


def to_feature_class(layer_url: str, out_fc: str, fields: str = "*", out_sr: int = 26910) -> int:
    """Pull a layer and write it to out_fc. Returns the feature count."""
    data = query_all(layer_url, fields, out_sr=out_sr)
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "layer.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle)
        arcpy.conversion.JSONToFeatures(path, out_fc)
    log.info("Pulled %s features from %s", len(data["features"]), layer_url)
    return len(data["features"])
