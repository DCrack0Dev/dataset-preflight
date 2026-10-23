"""Local HTTP service for pipeline integrations."""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, replace
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from typing import Any

from .audit import AuditLog
from .contract import ContractError, parse_contract
from .observability import ErrorTracker, configure_error_tracking, configure_logging, logger
from .schema import ValidationRequest
from .validator import CsvReadError, validate_csv

MAX_REQUEST_BYTES = 1_000_000


@dataclass
class Metrics:
    requests: int = 0
    validations: int = 0
    invalid_requests: int = 0
    failed_validations: int = 0

    def __post_init__(self) -> None:
        self._lock = Lock()

    def record_request(self) -> None:
        with self._lock:
            self.requests += 1

    def record_validation(self, valid: bool) -> None:
        with self._lock:
            self.validations += 1
            if not valid:
                self.failed_validations += 1

    def record_invalid_request(self) -> None:
        with self._lock:
            self.invalid_requests += 1

    def render(self) -> str:
        with self._lock:
            values = {
                "dataset_preflight_http_requests_total": self.requests,
                "dataset_preflight_validations_total": self.validations,
                "dataset_preflight_failed_validations_total": self.failed_validations,
                "dataset_preflight_invalid_requests_total": self.invalid_requests,
            }
        return "".join(f"{name} {value}\n" for name, value in values.items())


class PreflightHTTPServer(ThreadingHTTPServer):
    """Threaded server carrying shared metrics for request handlers."""

    daemon_threads = True

    def __init__(
        self,
        address: tuple[str, int],
        audit_path: Path | None = None,
        error_tracker: ErrorTracker | None = None,
    ) -> None:
        super().__init__(address, PreflightRequestHandler)
        self.metrics = Metrics()
        self.audit = AuditLog(audit_path)
        self.error_tracker = error_tracker or configure_error_tracking()


class PreflightRequestHandler(BaseHTTPRequestHandler):
    server: PreflightHTTPServer

    def do_GET(self) -> None:
        if self.path == "/health/live":
            self._send_json(HTTPStatus.OK, {"status": "ok"})
        elif self.path == "/health/ready":
            self._send_json(HTTPStatus.OK, {"status": "ready"})
        elif self.path == "/metrics":
            self._send_text(HTTPStatus.OK, self.server.metrics.render())
        elif self.path == "/openapi.json":
            self._send_json(HTTPStatus.OK, _openapi_document())
        else:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "NOT_FOUND"})

    def do_POST(self) -> None:
        self.server.metrics.record_request()
        logger.info("request received method=POST path=%s client=%s", self.path, self.client_address[0])
        if self.path != "/v1/validate":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "NOT_FOUND"})
            return
        try:
            request = ValidationRequest.model_validate(self._read_json())
            contract = parse_contract(request.contract, source="request.contract")
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", suffix=".csv") as csv_file:
                csv_file.write(request.csv)
                csv_file.flush()
                report = replace(validate_csv(Path(csv_file.name), contract), source="<request>")
            self.server.metrics.record_validation(report.valid)
            self.server.audit.record("validation", valid=report.valid, issues=len(report.issues), rows=report.rows)
            logger.info(
                "validation completed valid=%s rows=%d issues=%d", report.valid, report.rows, len(report.issues)
            )
            self._send_json(HTTPStatus.OK if report.valid else HTTPStatus.UNPROCESSABLE_ENTITY, report.as_dict())
        except (ContractError, CsvReadError, ValueError, TypeError, json.JSONDecodeError) as exc:
            self.server.metrics.record_invalid_request()
            self.server.audit.record("invalid_request", error=str(exc))
            self.server.error_tracker.capture_exception(exc)
            logger.warning("invalid validation request: %s", exc)
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "INVALID_REQUEST", "message": str(exc)})

    def _read_json(self) -> dict[str, Any]:
        content_length = self.headers.get("Content-Length")
        if content_length is None or not content_length.isdigit():
            raise ValueError("Content-Length is required")
        if int(content_length) > MAX_REQUEST_BYTES:
            raise ValueError("request body is too large")
        raw = self.rfile.read(int(content_length))
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise TypeError("request body must be a JSON object")
        return payload

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, status: HTTPStatus, body: str) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: object) -> None:
        logger.info("http access %s", format % args)


def create_server(
    host: str = "127.0.0.1",
    port: int = 8080,
    audit_path: Path | None = None,
    error_tracker: ErrorTracker | None = None,
) -> PreflightHTTPServer:
    return PreflightHTTPServer((host, port), audit_path, error_tracker)


def serve(host: str = "0.0.0.0", port: int = 8080, audit_path: Path | None = None) -> None:
    configure_logging()
    server = create_server(host, port, audit_path)
    logger.info("service starting host=%s port=%d", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("service shutdown requested")
        pass
    finally:
        server.server_close()
        logger.info("service stopped")


def _openapi_document() -> dict[str, Any]:
    return {
        "openapi": "3.0.3",
        "info": {"title": "Dataset Preflight API", "version": "0.2.0"},
        "paths": {
            "/v1/validate": {"post": {"summary": "Validate CSV content"}},
            "/health/live": {"get": {"summary": "Liveness probe"}},
            "/health/ready": {"get": {"summary": "Readiness probe"}},
            "/metrics": {"get": {"summary": "Prometheus-style metrics"}},
        },
    }
