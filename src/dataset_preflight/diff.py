"""Compare two contracts and classify schema changes."""

from __future__ import annotations

from dataclasses import dataclass

from .contract import DatasetContract


@dataclass(frozen=True)
class Change:
    kind: str
    column: str
    detail: str


def compare_contracts(before: DatasetContract, after: DatasetContract) -> tuple[Change, ...]:
    old = {column.name: column for column in before.columns}
    new = {column.name: column for column in after.columns}
    changes: list[Change] = []
    compatibility_changes: list[Change] = []
    additions: list[Change] = []
    removals: list[Change] = []
    for name in sorted(old.keys() - new.keys()):
        removals.append(Change("removed", name, "column removed"))
    for name in sorted(new.keys() - old.keys()):
        additions.append(Change("added", name, "column added"))
    for name in sorted(old.keys() & new.keys()):
        left, right = old[name], new[name]
        if left.type != right.type:
            compatibility_changes.append(Change("breaking", name, f"type changed from {left.type} to {right.type}"))
        if left.nullable and not right.nullable:
            compatibility_changes.append(Change("breaking", name, "column is now non-nullable"))
        if left.unique != right.unique:
            compatibility_changes.append(
                Change("constraint", name, f"unique changed from {left.unique} to {right.unique}")
            )
        if left.allowed != right.allowed:
            compatibility_changes.append(Change("constraint", name, "allowed values changed"))
        if left.minimum != right.minimum or left.maximum != right.maximum:
            compatibility_changes.append(Change("constraint", name, "numeric bounds changed"))
    if before.allow_extra_columns != after.allow_extra_columns:
        compatibility_changes.append(
            Change(
                "constraint",
                "*",
                f"allow_extra_columns changed from {before.allow_extra_columns} to {after.allow_extra_columns}",
            )
        )
    changes.extend(sorted(compatibility_changes, key=lambda change: (change.kind != "breaking", change.column)))
    changes.extend(additions)
    changes.extend(removals)
    return tuple(changes)
