# Dataset Preflight

Dataset Preflight is a local-first command-line tool for catching malformed CSV files and schema drift before an import or deployment. It turns a small JSON data contract into deterministic validation results that are readable by people and automation.

It is designed for analysts and data engineers who need a fast, reviewable gate before data reaches a warehouse, API, or scheduled pipeline. It has no network dependency, no account requirement, and no hidden data upload.

## Workflows

- Define an explicit contract for required columns, types, nullability, uniqueness, allowed values, and numeric bounds.
- Validate a CSV file and receive row-level issues with stable codes and source locations.
- Compare two contract files to review additions, removals, and incompatible changes before deployment.
- Export the validation result as JSON for CI annotations or downstream tooling.
- Fail a pipeline with exit code `1` when the dataset violates its contract and `2` for invalid inputs or contracts.

## Quick start

Requires Python 3.11 or later.

```bash
PYTHONPATH=src python -m dataset_preflight validate examples/orders.csv examples/orders.contract.json
PYTHONPATH=src python -m dataset_preflight validate examples/orders.csv examples/orders.contract.json --format json > report.json
PYTHONPATH=src python -m dataset_preflight diff examples/orders.contract.json examples/orders.v2.contract.json
```

A contract is deliberately plain JSON:

```json
{
  "name": "orders",
  "version": 1,
  "allow_extra_columns": false,
  "columns": [
    {"name": "order_id", "type": "string", "nullable": false, "unique": true},
    {"name": "amount", "type": "number", "nullable": false, "min": 0},
    {"name": "status", "type": "string", "nullable": false, "allowed": ["paid", "refunded"]}
  ]
}
```

See [docs/contract.md](docs/contract.md) for the full contract format and [docs/architecture.md](docs/architecture.md) for module boundaries.

## Development

The implementation uses only the Python standard library at runtime. The test suite uses `unittest`, so the core checks work in an offline environment.

```bash
python -m unittest discover -s tests -v
python -m compileall -q src tests
```

## Security and limits

Dataset Preflight reads local files only and does not execute formulas or interpret cell contents. It is intentionally CSV-focused: it does not claim to validate encodings beyond Python's CSV reader, infer a schema, or replace business-level reconciliation. Keep contracts under code review and treat validation reports as potentially sensitive because they can include source values.

## License

MIT. See [LICENSE](LICENSE).
