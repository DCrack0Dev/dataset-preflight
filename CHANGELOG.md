# Changelog

## 0.2.0 - 2026-10-22

- Added a local HTTP validation service with liveness, readiness, metrics, request limits, and integration tests.
- Added a non-root Docker image, read-only Compose deployment, writable ephemeral `/tmp`, and Dev Container setup.
- Added a production-only branch coverage report with an 85% CI gate.
- Added malformed-input tests and expanded contract/type/CLI tests.
- Added pinned Ruff and coverage tooling with a CI cleanliness gate.
- Added HTTP API documentation, end-to-end CLI checks, Dependabot, CODEOWNERS, and pinned dependency auditing.

## 0.1.0 - 2026-10-22

- Added contract-driven CSV validation for schema, types, nullability, uniqueness, allowed values, and numeric bounds.
- Added human-readable and JSON reports with stable exit codes.
- Added contract diffing with breaking-change classification.
- Added standard-library tests, Python matrix CI, examples, and architecture documentation.
