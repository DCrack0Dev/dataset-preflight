# Architecture

The package keeps pure contract parsing, validation, reporting, and CLI orchestration separate.

- `contract.py` parses JSON into immutable dataclasses and rejects ambiguous contracts before any rows are read.
- `validator.py` streams rows through Python's CSV reader, checks schema and column constraints, and emits stable issue codes. It does not infer types or mutate input files.
- `report.py` owns the serializable report shape used by both human and JSON output.
- `diff.py` compares immutable contracts and classifies changes for deployment review.
- `cli.py` maps workflows to exit codes: `0` means success, `1` means a valid command found data/schema findings, and `2` means the input or contract could not be processed.
- `service.py` adapts the same validator to a dependency-free local HTTP API. It owns request-size limits, response status mapping, liveness/readiness probes, and Prometheus-style counters. Raw request data is written only to a temporary file during validation.

The standard library is sufficient at runtime. This keeps the validation gate portable and avoids a network or service dependency in CI. Tests use temporary files and deterministic fixtures so they exercise the public behavior without relying on the user's filesystem.

The Docker image and Compose definition are deployment wrappers, not alternate application logic. The image runs as an unprivileged user, exposes port 8080, and has an unauthenticated readiness endpoint suitable for container health checks. The service is intentionally stateless; durable reports belong in the caller's pipeline storage.
