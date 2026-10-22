"""Contract loading and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ContractError(ValueError):
    """Raised when a contract is malformed or unsupported."""


SUPPORTED_TYPES = {"string", "integer", "number", "boolean", "date"}


@dataclass(frozen=True)
class ColumnContract:
    name: str
    type: str
    nullable: bool = True
    unique: bool = False
    allowed: tuple[str, ...] = ()
    minimum: float | None = None
    maximum: float | None = None


@dataclass(frozen=True)
class DatasetContract:
    name: str
    version: int
    columns: tuple[ColumnContract, ...]
    allow_extra_columns: bool = False

    @property
    def column_names(self) -> tuple[str, ...]:
        return tuple(column.name for column in self.columns)


def load_contract(path: Path) -> DatasetContract:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read contract {path}: {exc}") from exc
    return parse_contract(raw, source=str(path))


def parse_contract(raw: Any, source: str = "contract") -> DatasetContract:
    if not isinstance(raw, dict):
        raise ContractError(f"{source} must be a JSON object")
    name = _required_string(raw, "name", source)
    version = raw.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise ContractError(f"{source}.version must be a positive integer")
    raw_columns = raw.get("columns")
    if not isinstance(raw_columns, list) or not raw_columns:
        raise ContractError(f"{source}.columns must be a non-empty array")

    columns: list[ColumnContract] = []
    seen: set[str] = set()
    for index, item in enumerate(raw_columns):
        location = f"{source}.columns[{index}]"
        if not isinstance(item, dict):
            raise ContractError(f"{location} must be an object")
        column_name = _required_string(item, "name", location)
        if column_name in seen:
            raise ContractError(f"{location}.name duplicates {column_name!r}")
        seen.add(column_name)
        column_type = _required_string(item, "type", location)
        if column_type not in SUPPORTED_TYPES:
            raise ContractError(f"{location}.type must be one of {sorted(SUPPORTED_TYPES)}")
        nullable = item.get("nullable", True)
        unique = item.get("unique", False)
        if not isinstance(nullable, bool) or not isinstance(unique, bool):
            raise ContractError(f"{location}.nullable and unique must be booleans")
        allowed_raw = item.get("allowed", [])
        if not isinstance(allowed_raw, list) or not all(isinstance(value, str) for value in allowed_raw):
            raise ContractError(f"{location}.allowed must be an array of strings")
        minimum = _optional_number(item, "min", location)
        maximum = _optional_number(item, "max", location)
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ContractError(f"{location}.min cannot exceed max")
        if column_type not in {"integer", "number"} and (minimum is not None or maximum is not None):
            raise ContractError(f"{location}.min and max require a numeric type")
        columns.append(ColumnContract(column_name, column_type, nullable, unique, tuple(allowed_raw), minimum, maximum))

    allow_extra = raw.get("allow_extra_columns", False)
    if not isinstance(allow_extra, bool):
        raise ContractError(f"{source}.allow_extra_columns must be a boolean")
    return DatasetContract(name, version, tuple(columns), allow_extra)


def _required_string(raw: dict[str, Any], key: str, source: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{source}.{key} must be a non-empty string")
    return value.strip()


def _optional_number(raw: dict[str, Any], key: str, source: str) -> float | None:
    value = raw.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"{source}.{key} must be a number")
    return float(value)
