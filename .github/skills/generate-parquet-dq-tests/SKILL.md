---
name: generate-parquet-dq-tests
description: >-
  Generates one mapping-driven PyTest data quality module for a specified Parquet dataset
  using docs/parquet-aggregated-data-mapping.md. Invoke explicitly in Copilot Agent after
  the PyTest DQ Framework is implemented; refuse requests to build or modify the framework,
  Jenkinsfile, connectors, fixtures, or conftest.py as part of test generation.
disable-model-invocation: true
---

# Generate Parquet DQ tests

Follow these specifications:

- `PyTest DQ Framework/docs/test-automation-strategy.md` — **§5 Skill contract** and **§6 Test design standard** (source of truth).
- `docs/parquet-aggregated-data-mapping.md` — dataset-specific business mapping and sole specification for expected SQL.
- `PyTest DQ Framework/docs/dq-framework-design.md` — framework interfaces and directory conventions (consult if needed).

Do not store dataset-specific expected SQL in this skill. Do not consult `data_dev/` implementation SQL when deriving expected results.

## When this skill applies

Use **only when explicitly invoked** for generating or reviewing a PyTest DQ test module for a **named dataset** in the Parquet data mapping. The PyTest DQ Framework must already exist, including its PostgreSQL and Parquet connectors, `tests/conftest.py` fixtures, `src/data_quality/data_quality_validation_library.py`, and `tests/pytest.ini` marker registration.

The only permitted generated or edited output is:

`PyTest DQ Framework/tests/dq checks/parquet_files/test_<dataset_name>.py`

Generate **one module per requested dataset**; do not combine datasets into one module. Refuse framework construction or modifications to `src/`, connectors, DQ library, `conftest.py`, `pytest.ini`, `requirements.txt`, or `Jenkinsfile` within this skill. Such work belongs to Step 1 (or requires a separate explicit request outside this skill). Do not modify `data_dev/`. If prerequisites are missing, report the blocker rather than silently creating or changing them.

## Inputs you must have

1. The exact `<dataset_name>` (snake_case folder name under `/parquet_data/`), supplied by the user and defined in `docs/parquet-aggregated-data-mapping.md`.
2. The matching mapping definition: output column names and types where specified, dimensions/grain and uniqueness key, measures and aggregation/rounding, 3NF source tables and join keys, and any explicitly documented filters.
3. Author name and requirement/ticket identifier for the module header. Request missing metadata; never invent names or ticket IDs. If metadata is unavailable, leave clearly labeled header placeholders for the user, but do not invent values.
4. Existing framework interfaces: `db_connection`, `parquet_reader`, and `data_quality_library` fixtures and registered `pytest` marks.

If the mapping file, requested dataset definition, required join relationships, or measure semantics are missing or ambiguous, **stop and ask for clarification**. Never guess the transformation and never use existing Parquet results or implementation SQL to fill gaps.

**Forbidden as expected-result sources:** `data_dev/` (including `queries.py`, loader code and parquet-generation SQL), current Parquet contents, existing generated test SQL, and arbitrary inferred business rules. PostgreSQL 3NF is the **data source** for executing mapping-derived SQL, not a substitute for the mapping's business requirements.

## Hard rules

1. **Output location:** Write exactly one `test_<dataset_name>.py` module at `PyTest DQ Framework/tests/dq checks/parquet_files/`; preserve the mapping's dataset name.
2. **Direction:** `source_data` is the **expected** result obtained from PostgreSQL 3NF tables with `db_connection.get_data_sql(source_query)`. `target_data` is the **actual** result read from the generated Parquet dataset with `parquet_reader.process(...)`. Never reverse them, even if `test_examples.py` uses misleading placeholders.
3. **Mapping-only SQL:** Derive the complete expected SQL independently from `docs/parquet-aggregated-data-mapping.md`. Never read or copy SQL from `data_dev/`, its parquet loaders, or generated Parquet outputs.
4. **No extra transformations:** Do not add `UNION`, `WHERE` filters, `CASE`, sign changes, joins, or other transformations unless required by the mapping. Do not rewrite expected SQL just to make tests pass.
5. **Output schema:** Match the mapping's dimensions/grain and expected measure expressions; alias every result column to its mapped Parquet output name. Never assume the source column names are the output aliases.
6. **Parquet location:** Set `target_path = '/parquet_data/<dataset_name>'` and call `parquet_reader.process(target_path, include_subfolders=True)`.
7. **Library only:** Test bodies must call the existing `data_quality_library` methods, not duplicate pandas comparison or validation logic. Do not add no-op or always-passing assertions, or compare the target to itself.
8. **Required checks:** Implement exactly the five standard functions: `test_check_dataset_is_not_empty`, `test_check_data_completeness`, `test_check_count`, `test_check_uniqueness`, and `test_check_not_null_values`. They must perform actual validations through the library.
9. **Marks:** Every test gets `@pytest.mark.parquet_data` and `@pytest.mark.<dataset_name>` (replace with a valid concrete marker name). Only `test_check_dataset_is_not_empty` additionally receives `@pytest.mark.smoke`. Markers must be registered by the framework; report a missing mark instead of modifying `pytest.ini` under this skill.
10. **Not-null:** Pass **all mapped output columns** for the dataset to `check_not_null_values`, not only dimensions or a convenient subset.
11. **Uniqueness:** Use `check_duplicates(target_data)` as in TAS §6.2. Where grain-specific uniqueness is needed, use the library's optional `column_names` argument with the mapping's grain fields (never invent the grain). Preserve the standard test function name.
12. **Diagnostic failures:** Rely on library assertions that expose useful count differences, mismatched rows and relevant null column names. If the library does not provide adequate reporting, flag this for a separate framework change; do not silently alter it during skill execution.
13. **No dataset-specific SQL in the skill:** Keep this file reusable. Generated modules may contain concrete SQL derived from their dataset mapping; this skill must not.

## Workflow

1. Confirm the requested dataset exists in `docs/parquet-aggregated-data-mapping.md`, the framework is present, and the destination module path is correct.
2. Extract a compact mapping specification: 3NF source tables, join keys, dimension/grain columns, required output aliases, measure formulas, rounding, and explicitly allowed filters. Flag missing or contradictory requirements before generating code.
3. Derive **expected PostgreSQL SQL** solely from that mapping: construct joins, select mapped dimensions and aggregate measures, apply only mapped filters, group at the documented grain, and alias the output columns to match the Parquet target. Do not inspect ETL SQL or tweak the query after looking at target data.
4. Fill the full TAS §6.2 module skeleton below for **one** dataset. Use module-scoped `source_data` and `target_data` fixtures, existing framework fixtures, and the complete mapped not-null column list.
5. Use the five DQ library methods; apply `parquet_data` and dataset-specific markers to all five tests, and `smoke` **only** to the not-empty test.
6. Review the generated module against TAS §§5–6: fixture direction, mapping-based query, aliases/grain, target path, five checks, not-null list, markers, library calls, and header metadata. Confirm the framework has not been modified.
7. State any blocking mapping ambiguities; do not claim tests passed without running them.

## Template

Use the **full module skeleton from TAS §6.2**. Angle-bracket tokens are placeholders to replace in the **generated module**, not literal Python code to execute. Preserve source/target direction even if example test files differ.

```python
"""
Description: Data Quality checks for <dataset_name> dataset.
Requirement(s): TICKET-1234
Author(s): <name>
"""

import pytest


@pytest.fixture(scope='module')
def source_data(db_connection):
    source_query = """
    -- expected query derived from mapping (grain + measures + joins)
    """
    return db_connection.get_data_sql(source_query)


@pytest.fixture(scope='module')
def target_data(parquet_reader):
    target_path = '/parquet_data/<dataset_name>'
    return parquet_reader.process(target_path, include_subfolders=True)


@pytest.mark.parquet_data
@pytest.mark.smoke
@pytest.mark.<dataset_name>
def test_check_dataset_is_not_empty(target_data, data_quality_library):
    data_quality_library.check_dataset_is_not_empty(target_data)


@pytest.mark.parquet_data
@pytest.mark.<dataset_name>
def test_check_data_completeness(source_data, target_data, data_quality_library):
    data_quality_library.check_data_completeness(source_data, target_data)


@pytest.mark.parquet_data
@pytest.mark.<dataset_name>
def test_check_count(source_data, target_data, data_quality_library):
    data_quality_library.check_count(source_data, target_data)


@pytest.mark.parquet_data
@pytest.mark.<dataset_name>
def test_check_uniqueness(target_data, data_quality_library):
    data_quality_library.check_duplicates(target_data)


@pytest.mark.parquet_data
@pytest.mark.<dataset_name>
def test_check_not_null_values(target_data, data_quality_library):
    data_quality_library.check_not_null_values(target_data, ['<col_1>', '<col_2>', '<col_3>'])
```

## SQL derivation (generic)

- Determine the required 3NF tables and exact **join keys** from the mapping. Join source tables only as documented; do not infer joins from current parquet content.
- Translate each mapped **dimension** into a selected output expression and the appropriate `GROUP BY` expression; preserve the exact business grain and output names.
- Translate mapped **measures** into the specified aggregation (`MIN`, `AVG`, `SUM`, etc.), computed fields or name concatenation, and any explicitly specified rounding and numeric semantics. Use correct SQL aliases for mapped output columns.
- For derived date columns, follow the mapping's date expression, type conversion and granularity; do not add date truncation or ranges on your own.
- Apply `WHERE`/`HAVING` restrictions only when explicitly specified in the mapping. Do not add implementation-only `UNION`, `CASE`, exclusions or sign flips.
- Group by the mapped grain. Ensure expected output contains the **same mapped columns and aliases** as the Parquet target, with no unnecessary extra columns.
- The final SQL query must reflect **business intent**, independent of the ETL code. If the mapping is insufficient, ask rather than guessing; if the output differs from Parquet, investigate instead of modifying expected SQL to match.

## After generation

- Run pytest **only when explicitly asked**, using the `parquet_data` marker for the production suite. Do not run the pipeline or edit Jenkins during test generation.
- If tests are executed and fail, report expected mapping-derived values versus actual Parquet values; investigate potential mapping-vs-Parquet or transformation issues. Also distinguish execution/configuration errors where supported by evidence.
- **Never change expected SQL solely to turn a failing check green.** Escalate genuine mapping ambiguities instead.
- Do not change framework library functions, connectors, test fixtures, Jenkins configuration, or unrelated tests as a side effect.
