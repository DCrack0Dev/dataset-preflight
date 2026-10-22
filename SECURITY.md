# Security

Dataset Preflight reads CSV and JSON files from the local filesystem. It does not upload data, execute formulas, or require credentials. Reports may repeat invalid source values, so store generated reports according to the sensitivity of the input data.

Do not expose this CLI through an untrusted file-upload service without adding authorization, resource limits, and safe temporary-file handling. Please report suspected security issues privately to the repository owner rather than publishing sensitive sample data in an issue.
