"""Configuration-file loading for the StableFill CLI."""

from __future__ import annotations

from os import path
from typing import Any, Dict

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python < 3.11
    import tomli as tomllib


CONFIG_BASENAME = "stablefill.toml"


def load_config_file(filename: str) -> Dict[str, Any]:
    """Load a StableFill TOML configuration file.

    Missing configuration files are treated as an empty configuration so the
    default ``stablefill.toml`` lookup can be unconditional.
    """

    if not filename or not path.isfile(filename):
        return {}

    with open(filename, "rb") as handle:
        return tomllib.load(handle)


def flatten_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten supported config sections into CLI-style option names."""

    flattened: Dict[str, Any] = {}
    sections = ("stablefill", "input", "output", "formatting", "options", "compile", "logging")

    for key, value in config.items():
        if key not in sections or not isinstance(value, dict):
            flattened[key.replace("-", "_")] = value

    for section in sections:
        section_values = config.get(section, {})
        if isinstance(section_values, dict):
            for key, value in section_values.items():
                flattened[key.replace("-", "_")] = value

    if "type" in flattened and "filetype" not in flattened:
        flattened["filetype"] = flattened["type"]
    if "files" in flattened and "input" not in flattened:
        flattened["input"] = flattened["files"]
    if "dir" in flattened and "input_dir" not in flattened:
        flattened["input_dir"] = flattened["dir"]
    if "directory" in flattened and "input_dir" not in flattened:
        flattened["input_dir"] = flattened["directory"]

    return flattened


def as_list(value: Any) -> list:
    """Return a TOML value as a list suitable for argparse-style fields."""

    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def as_optional_list(value: Any):
    """Return ``None`` or an argparse-style list value."""

    if value is None:
        return None
    return as_list(value)
