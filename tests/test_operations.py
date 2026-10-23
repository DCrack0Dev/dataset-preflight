from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]


class OperationsArtifactTests(unittest.TestCase):
    def test_compose_is_read_only_and_has_ephemeral_tmp(self) -> None:
        compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn("read_only: true", compose)
        self.assertIn("- /tmp", compose)
        self.assertIn("healthcheck:", compose)

    def test_dockerfile_uses_non_root_runtime(self) -> None:
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("USER nobody", dockerfile)
        self.assertIn("EXPOSE 8080", dockerfile)

    def test_openapi_document_has_expected_paths(self) -> None:
        document = json.loads((ROOT / "docs/openapi.json").read_text(encoding="utf-8"))
        self.assertEqual(document["openapi"], "3.0.3")
        self.assertIn("/v1/validate", document["paths"])
        self.assertIn("/health/ready", document["paths"])


if __name__ == "__main__":
    unittest.main()
