"""Command-line interface for Dataset Preflight."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .contract import ContractError, load_contract
from .diff import compare_contracts
from .report import ValidationReport
from .service import serve
from .validator import CsvReadError, validate_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dataset-preflight", description="Validate CSV files against explicit data contracts."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="validate a CSV file")
    validate.add_argument("csv", type=Path)
    validate.add_argument("contract", type=Path)
    validate.add_argument("--format", choices=("text", "json"), default="text")
    diff = subparsers.add_parser("diff", help="compare two contract files")
    diff.add_argument("before", type=Path)
    diff.add_argument("after", type=Path)
    http = subparsers.add_parser("serve", help="start the local HTTP validation service")
    http.add_argument("--host", default="0.0.0.0")
    http.add_argument("--port", type=int, default=8080)
    http.add_argument("--audit-log", type=Path, help="append metadata-only events to this JSONL file")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "serve":
            serve(args.host, args.port, args.audit_log)
            return 0
        if args.command == "validate":
            report = validate_csv(args.csv, load_contract(args.contract))
            if args.format == "json":
                print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
            else:
                _print_report(report)
            return 0 if report.valid else 1
        before, after = load_contract(args.before), load_contract(args.after)
        changes = compare_contracts(before, after)
        if not changes:
            print("No schema changes.")
            return 0
        for change in changes:
            print(f"{change.kind.upper():10} {change.column}: {change.detail}")
        return 1 if any(change.kind == "breaking" for change in changes) else 0
    except (ContractError, CsvReadError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _print_report(report: ValidationReport) -> None:
    status = "PASS" if report.valid else "FAIL"
    print(f"{status}: {report.source} against {report.contract} ({report.rows} rows)")
    for issue in report.issues:
        location = f"row {issue.row}, {issue.column}" if issue.row is not None else issue.column or "schema"
        print(f"  [{issue.code}] {location}: {issue.message}")


if __name__ == "__main__":
    raise SystemExit(main())
