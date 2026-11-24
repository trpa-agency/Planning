"""Config loading, logging, and run folders for the zoning scripts."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def parse_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--config",
        default=str(ROOT / "config.yaml"),
        help="Path to the config file (default: config.yaml in the Zoning folder).",
    )
    return parser.parse_args()


def load_config(path: str | Path) -> dict:
    path = Path(path)
    with path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    config["_path"] = str(path)
    return config


def resolve(path: str | Path) -> Path:
    """Resolve a config path against the Zoning folder."""
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_logger(name: str, config: dict, stamp: str) -> logging.Logger:
    log_dir = resolve(config["paths"]["logs"])
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    for handler in (
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_dir / f"{name}_{stamp}.log", encoding="utf-8"),
    ):
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    return logger


def run_folder(config: dict, name: str, stamp: str) -> Path:
    folder = resolve(config["paths"]["outputs"]) / f"{name}_{stamp}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder
