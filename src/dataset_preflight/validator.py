"""CSV validation against a DatasetContract."""

from __future__ import annotations

import csv
import math
from datetime import date
from pathlib import Path

from .contract import ColumnContract, DatasetContract
from .report import Issue, ValidationReport


class CsvReadError(ValueError):
    """Raised when a CSV cannot be read as a tabular file."""


def validate_csv(path: Path, contract: DatasetContract) -> ValidationReport:
    issues: list[Issue] = []
    try:
        handle = path.open("r", encoding="utf-8", newline="")
    except (OSError, UnicodeError) as exc:
        raise CsvReadError(f"cannot read CSV {path}: {exc}") from exc

    with handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames
        if headers is None or any(header is None or not header.strip() for header in headers):
            raise CsvReadError("CSV must have a non-empty header row")
        headers = [header.strip() for header in headers]
        if len(headers) != len(set(headers)):
            raise CsvReadError("CSV header contains duplicate column names")
        expected = set(contract.column_names)
        actual = set(headers)
        for name in sorted(expected - actual):
            issues.append(Issue("MISSING_COLUMN", f"required column {name!r} is missing", column=name))
        if not contract.allow_extra_columns:
            for name in sorted(actual - expected):
                issues.append(Issue("UNEXPECTED_COLUMN", f"column {name!r} is not in the contract", column=name))

        seen_values: dict[str, set[str]] = {column.name: set() for column in contract.columns if column.unique}
        rows = 0
        for row_number, row in enumerate(reader, start=2):
            rows += 1
            if None in row:
                issues.append(Issue("MALFORMED_ROW", "row contains more fields than the header", row_number))
            for column in contract.columns:
                if column.name not in actual:
                    continue
                value = row.get(column.name)
                _validate_value(issues, row_number, value, column)
                if column.unique and value not in (None, ""):
                    if value in seen_values[column.name]:
                        issues.append(
                            Issue(
                                "DUPLICATE_VALUE",
                                f"value is not unique in {column.name!r}",
                                row_number,
                                column.name,
                                value,
                            )
                        )
                    seen_values[column.name].add(value)

    return ValidationReport(contract.name, str(path), rows, tuple(issues))


def _validate_value(issues: list[Issue], row: int, value: str | None, column: ColumnContract) -> None:
    if value is None or value.strip() == "":
        if not column.nullable:
            issues.append(Issue("NULL_NOT_ALLOWED", "value is required", row, column.name, value))
        return
    value = value.strip()
    if column.allowed and value not in column.allowed:
        issues.append(
            Issue("VALUE_NOT_ALLOWED", f"value must be one of {list(column.allowed)!r}", row, column.name, value)
        )
    try:
        parsed = _parse_type(value, column.type)
    except ValueError as exc:
        issues.append(Issue("INVALID_TYPE", str(exc), row, column.name, value))
        return
    if (
        column.minimum is not None
        and isinstance(parsed, (int, float))
        and not isinstance(parsed, bool)
        and parsed < column.minimum
    ):
        issues.append(Issue("BELOW_MINIMUM", f"value must be at least {column.minimum:g}", row, column.name, value))
    if (
        column.maximum is not None
        and isinstance(parsed, (int, float))
        and not isinstance(parsed, bool)
        and parsed > column.maximum
    ):
        issues.append(Issue("ABOVE_MAXIMUM", f"value must be at most {column.maximum:g}", row, column.name, value))


def _parse_type(value: str, expected: str) -> str | int | float | bool | date:
    if expected == "string":
        return value
    if expected == "integer":
        try:
            parsed = int(value)
        except ValueError as exc:
            raise ValueError("value must be an integer") from exc
        if str(parsed) != value and not (value.startswith("+") and str(parsed) == value[1:]):
            raise ValueError("value must be an integer")
        return parsed
    if expected == "number":
        try:
            numeric_value = float(value)
        except ValueError as exc:
            raise ValueError("value must be a number") from exc
        if not math.isfinite(numeric_value):
            raise ValueError("value must be a finite number")
        return numeric_value
    if expected == "boolean":
        if value.lower() not in {"true", "false"}:
            raise ValueError("value must be true or false")
        return value.lower() == "true"
    if expected == "date":
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("value must be an ISO date (YYYY-MM-DD)") from exc
    raise AssertionError(f"unsupported type: {expected}")
