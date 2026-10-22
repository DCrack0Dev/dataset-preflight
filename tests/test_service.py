from __future__ import annotations

import json
import threading
import unittest
from http import HTTPStatus
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from dataset_preflight.service import create_server

CONTRACT = {
    "name": "orders",
    "version": 1,
    "columns": [
        {"name": "id", "type": "string", "nullable": False, "unique": True},
        {"name": "amount", "type": "number", "nullable": False, "min": 0},
    ],
}


class ServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = create_server(port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.thread.join(timeout=2)
        cls.server.server_close()

    def request(self, method: str, path: str, payload: dict | None = None) -> tuple[int, dict | str]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(f"{self.base_url}{path}", data=data, method=method)
        if data is not None:
            request.add_header("Content-Type", "application/json")
        try:
            with urlopen(request, timeout=2) as response:
                body = response.read().decode("utf-8")
                status = response.status
        except HTTPError as error:
            body = error.read().decode("utf-8")
            status = error.code
        return status, json.loads(body) if path != "/metrics" else body

    def test_health_and_readiness_are_unauthenticated(self) -> None:
        self.assertEqual(self.request("GET", "/health/live"), (200, {"status": "ok"}))
        self.assertEqual(self.request("GET", "/health/ready"), (200, {"status": "ready"}))

    def test_validates_a_request_without_persisting_raw_csv(self) -> None:
        status, report = self.request("POST", "/v1/validate", {"csv": "id,amount\nA,4.5\n", "contract": CONTRACT})
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(report["valid"], True)
        self.assertEqual(report["source"], "<request>")

    def test_returns_unprocessable_entity_for_data_findings(self) -> None:
        status, report = self.request("POST", "/v1/validate", {"csv": "id,amount\nA,-1\n", "contract": CONTRACT})
        self.assertEqual(status, HTTPStatus.UNPROCESSABLE_ENTITY)
        self.assertEqual(report["issues"][0]["code"], "BELOW_MINIMUM")

    def test_returns_bad_request_for_invalid_contract(self) -> None:
        status, response = self.request("POST", "/v1/validate", {"csv": "id\nA\n", "contract": {}})
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(response["error"], "INVALID_REQUEST")

    def test_metrics_expose_request_and_validation_counts(self) -> None:
        status, metrics = self.request("GET", "/metrics")
        self.assertEqual(status, HTTPStatus.OK)
        self.assertIn("dataset_preflight_http_requests_total", metrics)
        self.assertIn("dataset_preflight_validations_total", metrics)


if __name__ == "__main__":
    unittest.main()
