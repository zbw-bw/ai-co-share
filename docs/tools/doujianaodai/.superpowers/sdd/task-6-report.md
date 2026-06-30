# Task 6 Report: PyPI Packaging — pyproject.toml + cleanup

## Status: DONE

## Commit
- `15ec99e` — feat: switch to pyproject.toml packaging, add CLI entry point

## What was done

1. **Created `pyproject.toml`** — modern packaging with `[build-system]`, `[project]`, `[project.scripts]` entry point `doujianaodai = "app.main:main"`, and `[project.optional-dependencies]` for dev (pytest). One deviation from the brief: changed `package-data` key from `""` to `"*"` because modern setuptools (>=68) rejects empty-string keys per PEP 517 validation.

2. **Created `MANIFEST.in`** — includes config.yaml, LICENSE, README.md, pet_mcp_server.py.

3. **Created `LICENSE`** — MIT license, exact text from brief.

4. **Updated `requirements.txt`** — removed `anthropic>=0.34.0` and `ollama>=0.3.0` lines.

5. **Deleted `setup.py`** — old packaging file removed.

6. **Deleted `test_pipeline.py`** — root-level temp test file removed.

7. **Verified `logs/__init__.py`** — already existed (0 bytes), no action needed.

8. **Verified `ui/__init__.py`** — already existed, no action needed.

9. **`doujianaodai.egg-info/`** — existed and was cleaned up during `pip install -e`.

10. **`pip install -e ".[dev]"`** — succeeded. All dependencies resolved. CLI entry point installed at `.venv/bin/doujianaodai`.

11. **All 91 tests pass** in 12.75s.

## Deviation from brief

The brief specified `"" = ["config.yaml"]` for `[tool.setuptools.package-data]`. Modern setuptools (v68+) rejects empty-string keys; the wildcard `"*"` is the correct equivalent. Changed to `"*" = ["config.yaml"]` which has identical semantics (match all packages).

## Test summary

91 passed, 0 failed, 0 errors (12.75s)
