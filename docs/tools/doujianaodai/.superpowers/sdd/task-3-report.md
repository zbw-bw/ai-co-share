# Task 3 Report: Environment Preflight — Interactive Setup

## Status: DONE

## Commit
- `095c753` — feat: add preflight environment check and interactive model setup

## Files Created
- `app/preflight.py` — Implementation (6 public functions + 1 private helper)
- `tests/test_preflight.py` — 5 unit tests

## Public Interface

| Function | Signature | Description |
|----------|-----------|-------------|
| `check_python` | `() -> bool` | Returns True if Python >= 3.11 |
| `check_ollama` | `(base_url: str = "http://localhost:11434") -> tuple[bool, list[str]]` | Checks Ollama `/api/tags`, returns (ok, model_names) |
| `check_claude_code` | `() -> tuple[bool, str]` | Runs `claude --version`, returns (ok, version_string) |
| `check_screen_capture` | `() -> bool` | Tries `capture_foreground_window`, returns True if it works |
| `select_model` | `(models: list[str], current: str \| None) -> str` | Interactive model picker; returns current if valid, else prompts user |
| `run_preflight` | `(config_path: str) -> dict` | Orchestrates all checks, exits on failure, returns loaded config dict |

## Test Results

```
tests/test_preflight.py::test_check_python_passes PASSED
tests/test_preflight.py::test_check_ollama_running PASSED
tests/test_preflight.py::test_check_ollama_not_running PASSED
tests/test_preflight.py::test_check_claude_code_available PASSED
tests/test_preflight.py::test_check_claude_code_not_found PASSED
```

Full suite: 82 passed, 2 failed (pre-existing), 5 errors (pre-existing missing deps: PyQt6, Quartz).

## Notes
- Code matches the task brief verbatim
- All pre-existing tests remain unaffected
- Uses `requests` and `yaml` (both already project dependencies)
- `run_preflight` imports `load_config` from `app.config` as specified
- `_update_config_model` helper persists model selection back to YAML config
