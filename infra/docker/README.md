# Terraform Docker deployment

This module is the infrastructure-as-code equivalent of `docker compose up`. It builds the repository Dockerfile, runs the service on an unprivileged host port, and manages the container lifecycle.

```bash
terraform -chdir=infra/docker init
terraform -chdir=infra/docker validate
terraform -chdir=infra/docker plan
terraform -chdir=infra/docker apply
```

The module intentionally has no cloud credentials or remote state. It is suitable for a local worker, CI preview environment, or a host that already runs Docker. The container is read-only, receives an ephemeral `/tmp`, has `no-new-privileges`, runs as UID/GID `65534`, and has a readiness health check. Use `terraform destroy` to remove the managed container and image.
