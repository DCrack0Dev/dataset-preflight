# Terraform Docker deployment

This module is the infrastructure-as-code equivalent of `docker compose up`. It builds the repository Dockerfile, runs the service on an unprivileged host port, and manages the container lifecycle.

```bash
terraform -chdir=infra/docker init
terraform -chdir=infra/docker validate
terraform -chdir=infra/docker plan
terraform -chdir=infra/docker apply
```

The module intentionally has no cloud credentials or remote state. It is suitable for a local worker, CI preview environment, or a host that already runs Docker. The container is read-only, receives an ephemeral `/tmp`, has `no-new-privileges`, runs as UID/GID `65534`, and has a readiness health check. Use `terraform destroy` to remove the managed container and image.

## Variables and environment

The module has three typed Terraform inputs: `image_name` (default `dataset-preflight:terraform`), `container_name` (default `dataset-preflight`), and `port` (default `8080`, restricted to 1024–65535). They may be supplied as `TF_VAR_image_name`, `TF_VAR_container_name`, and `TF_VAR_port` respectively.

The application has no required runtime environment variables. The container's `PYTHONPATH=/app/src` is an internal Dockerfile setting; service host, port, and optional audit logging use the CLI flags documented in [../../docs/configuration.md](../../docs/configuration.md). If Terraform needs to connect to a non-default Docker daemon, the Docker provider honors `DOCKER_HOST`, `DOCKER_TLS_VERIFY`, and `DOCKER_CERT_PATH` according to Docker client conventions. Keep those connection values and certificates outside Git.
