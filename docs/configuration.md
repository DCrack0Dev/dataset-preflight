# Configuration reference

Dataset Preflight deliberately has no required application secrets and no user-configurable runtime environment variables. The HTTP service is configured with CLI flags, which keeps local execution explicit and prevents an undocumented environment-variable contract.

## Runtime configuration

The container starts:

```text
python -m dataset_preflight serve --host 0.0.0.0 --port 8080
```

Use these CLI flags instead of environment variables:

| CLI flag | Default | Purpose |
|---|---:|---|
| `--host` | `0.0.0.0` in the container | Bind address for the HTTP service. |
| `--port` | `8080` | Listening port inside the container. |
| `--audit-log PATH` | unset | Optional metadata-only JSONL audit file. Raw CSV content is never written to the audit log. |

The Dockerfile sets `PYTHONPATH=/app/src` internally so the `src` layout is importable. This is an implementation detail, not an application setting, and should not be changed for normal deployments.

## Terraform inputs

The Docker Terraform module uses typed Terraform variables rather than runtime environment variables:

| Terraform variable | Default | Environment equivalent |
|---|---:|---|
| `image_name` | `dataset-preflight:terraform` | `TF_VAR_image_name` |
| `container_name` | `dataset-preflight` | `TF_VAR_container_name` |
| `port` | `8080` | `TF_VAR_port` |

For example:

```bash
export TF_VAR_port=18080
terraform -chdir=infra/docker plan
```

The module does not require cloud credentials, a remote state backend, or application secrets. Its provider lockfile is committed at `infra/docker/.terraform.lock.hcl`.

## Docker provider connection variables

The Terraform Docker provider follows Docker's standard client configuration when the local daemon is not on the default socket. These are infrastructure-tool variables, not Dataset Preflight application settings:

| Variable | Use |
|---|---|
| `DOCKER_HOST` | Docker daemon endpoint, such as a remote TCP or SSH endpoint. |
| `DOCKER_TLS_VERIFY` | Enables Docker TLS verification when set according to Docker client conventions. |
| `DOCKER_CERT_PATH` | Directory containing Docker TLS certificates when TLS is configured. |

Keep Docker connection values and certificates outside the repository. Do not put them in `.env` files committed to Git.

## CI-only variables

GitHub Actions supplies `GITHUB_TOKEN` to the Gitleaks and dependency-review workflows. It is used only by GitHub-hosted security actions and is never read by the application. CI also sets `PYTHONPATH=src` for the source-layout test commands.

No `.env` file is required for local development. If a future feature introduces runtime environment configuration, add it to this document, update the container and Compose/Terraform surfaces, and add a test that fails when the documented default and implementation diverge.
