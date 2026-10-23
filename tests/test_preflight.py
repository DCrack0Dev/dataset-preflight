from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from dataset_preflight.cli import main
from dataset_preflight.contract import ContractError, parse_contract
from dataset_preflight.diff import compare_contracts
from dataset_preflight.validator import CsvReadError, validate_csv

CONTRACT = {
    "name": "orders",
    "version": 1,
    "columns": [
        {"name": "id", "type": "string", "nullable": False, "unique": True},
        {"name": "amount", "type": "number", "nullable": False, "min": 0},
        {"name": "status", "type": "string", "nullable": False, "allowed": ["paid", "refunded"]},
    ],
}


class ContractTests(unittest.TestCase):
    def test_rejects_duplicate_columns_and_invalid_bounds(self) -> None:
        with self.assertRaisesRegex(ContractError, "duplicates"):
            parse_contract(
                {
                    "name": "x",
                    "version": 1,
                    "columns": [{"name": "id", "type": "string"}, {"name": "id", "type": "string"}],
                }
            )
        with self.assertRaisesRegex(ContractError, "cannot exceed"):
            parse_contract(
                {"name": "x", "version": 1, "columns": [{"name": "amount", "type": "number", "min": 2, "max": 1}]}
            )

    def test_rejects_invalid_top_level_and_column_options(self) -> None:
        for raw, message in (
            ({}, "name"),
            ({"name": "x", "version": 0, "columns": []}, "version"),
            ({"name": "x", "version": 1, "columns": []}, "columns"),
            ({"name": "x", "version": 1, "columns": [{"name": "x", "type": "unknown"}]}, "type"),
            ({"name": "x", "version": 1, "columns": [{"name": "x", "type": "number", "min": "bad"}]}, "min"),
        ):
            with self.subTest(message=message), self.assertRaises(ContractError):
                parse_contract(raw)


class ValidationTests(unittest.TestCase):
    def test_rejects_duplicate_headers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.csv"
            path.write_text("id,id\nA,B\n", encoding="utf-8")
            with self.assertRaisesRegex(CsvReadError, "duplicate"):
                validate_csv(path, parse_contract(CONTRACT))

    def test_reports_rows_with_more_fields_than_the_header(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "wide.csv"
            path.write_text("id,amount,status\nA,2,paid,unexpected\n", encoding="utf-8")
            report = validate_csv(path, parse_contract(CONTRACT))
        self.assertEqual([issue.code for issue in report.issues], ["MALFORMED_ROW"])

    def test_reports_schema_and_row_violations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "orders.csv"
            path.write_text("id,amount,status,extra\nA,-2,unknown,x\nA,,paid,y\n", encoding="utf-8")
            report = validate_csv(path, parse_contract(CONTRACT))
        self.assertFalse(report.valid)
        self.assertEqual(report.rows, 2)
        self.assertEqual(
            [issue.code for issue in report.issues],
            ["UNEXPECTED_COLUMN", "BELOW_MINIMUM", "VALUE_NOT_ALLOWED", "DUPLICATE_VALUE", "NULL_NOT_ALLOWED"],
        )

    def test_validates_types_and_accepts_empty_nullable_values(self) -> None:
        contract = parse_contract(
            {
                "name": "events",
                "version": 1,
                "columns": [{"name": "count", "type": "integer"}, {"name": "note", "type": "string"}],
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.csv"
            path.write_text("count,note\n3,\n", encoding="utf-8")
            report = validate_csv(path, contract)
        self.assertTrue(report.valid)

    def test_reports_invalid_boolean_date_integer_and_non_finite_number(self) -> None:
        contract = parse_contract(
            {
                "name": "mixed",
                "version": 1,
                "columns": [
                    {"name": "count", "type": "integer"},
                    {"name": "active", "type": "boolean"},
                    {"name": "day", "type": "date"},
                    {"name": "amount", "type": "number"},
                ],
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mixed.csv"
            path.write_text("count,active,day,amount\nnot-an-int,yes,not-a-date,nan\n", encoding="utf-8")
            report = validate_csv(path, contract)
        self.assertEqual([issue.code for issue in report.issues], ["INVALID_TYPE"] * 4)


class DiffTests(unittest.TestCase):
    def test_classifies_breaking_and_non_breaking_changes(self) -> None:
        before = parse_contract(CONTRACT)
        after = parse_contract(
            {
                **CONTRACT,
                "version": 2,
                "columns": [
                    {"name": "id", "type": "string", "nullable": False, "unique": True},
                    {"name": "amount", "type": "integer", "nullable": False, "min": 0},
                    {"name": "region", "type": "string"},
                ],
            }
        )
        changes = compare_contracts(before, after)
        self.assertEqual(
            [(change.kind, change.column) for change in changes],
            [("breaking", "amount"), ("added", "region"), ("removed", "status")],
        )


class CliTests(unittest.TestCase):
    def test_validate_json_is_machine_readable_and_returns_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = root / "contract.json"
            dataset = root / "data.csv"
            contract.write_text(json.dumps(CONTRACT), encoding="utf-8")
            dataset.write_text("id,amount,status\nA,nope,paid\n", encoding="utf-8")
            self.assertEqual(main(["validate", str(dataset), str(contract), "--format", "json"]), 1)

    def test_text_validate_and_diff_commands_return_expected_codes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = root / "contract.json"
            changed = root / "changed.json"
            dataset = root / "data.csv"
            contract.write_text(json.dumps(CONTRACT), encoding="utf-8")
            changed.write_text(
                json.dumps({**CONTRACT, "version": 2, "columns": [{"name": "id", "type": "integer"}]}), encoding="utf-8"
            )
            dataset.write_text("id,amount,status\nA,2,paid\n", encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(["validate", str(dataset), str(contract)]), 0)
                self.assertEqual(main(["diff", str(contract), str(contract)]), 0)
                self.assertEqual(main(["diff", str(contract), str(changed)]), 1)
            self.assertIn("PASS", output.getvalue())

    def test_invalid_cli_input_returns_usage_error_code(self) -> None:
        self.assertEqual(main(["validate", "/missing/data.csv", "/missing/contract.json"]), 2)


if __name__ == "__main__":
    unittest.main()
