from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]


class CliEndToEndTests(unittest.TestCase):
    def test_module_cli_validates_example_from_repository_root(self) -> None:
        environment = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "dataset_preflight",
                "validate",
                "examples/orders.csv",
                "examples/orders.contract.json",
                "--format",
                "json",
            ],
            cwd=ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["valid"])

    def test_module_cli_prints_human_readable_success_report(self) -> None:
        environment = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "dataset_preflight",
                "validate",
                "examples/orders.csv",
                "examples/orders.contract.json",
            ],
            cwd=ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
