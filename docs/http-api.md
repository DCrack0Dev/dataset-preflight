# HTTP API

The optional HTTP service is intended for a local pipeline worker or an isolated container. It accepts CSV content in the request body, validates it against an inline contract, and does not persist the raw CSV.

## `POST /v1/validate`

Request:

```json
{
  "csv": "id,amount\nA,4.50\n",
  "contract": {
    "name": "orders",
    "version": 1,
    "columns": [
      {"name": "id", "type": "string", "nullable": false},
      {"name": "amount", "type": "number", "nullable": false, "min": 0}
    ]
  }
}
```

The endpoint returns `200` when the report is valid, `422` when the request is valid but the CSV has contract findings, and `400` when the JSON body or contract is invalid. Responses use the same report shape as the CLI's JSON output. Requests are limited to 1 MB before JSON parsing.

## Operational endpoints

`GET /health/live` returns `{"status":"ok"}` when the process is responding. `GET /health/ready` returns `{"status":"ready"}` when the service can accept validation work. `GET /metrics` returns plain-text counters suitable for a Prometheus scrape.

The service has no authentication. Keep it on a trusted local network or behind an authenticated gateway. The container runs as an unprivileged user and the Compose example uses a read-only root filesystem with ephemeral `/tmp` storage.
