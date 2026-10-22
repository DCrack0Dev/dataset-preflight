# Contract format

A contract is a JSON object with a non-empty `name`, positive integer `version`, and a non-empty `columns` array. Column names must be unique. Supported types are `string`, `integer`, `number`, `boolean`, and ISO `date` (`YYYY-MM-DD`).

Each column may set `nullable` (default `true`), `unique` (default `false`), `allowed` (an array of strings), and numeric `min`/`max` bounds. Empty CSV fields count as null. Missing required columns and unexpected columns are reported at schema level; unexpected columns are permitted only when `allow_extra_columns` is `true`.

`diff` compares two contracts. Adding a column is reported as an addition. Removing a column, narrowing nullability, or changing a type is reported as breaking. Constraint changes are reported separately because their operational impact depends on the data already in flight.
