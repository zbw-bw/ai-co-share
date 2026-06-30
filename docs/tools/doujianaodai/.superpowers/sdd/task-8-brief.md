### Task 8: Delete Stale Files — Remove replaced UI and old status_bar

**Files:**
- Delete: `ui/status_bar.py`
- Delete: `ui/main_window.py`

**Interfaces:**
- Consumes: confirmation that no code imports these modules (Tasks 4-5 removed references)
- Produces: clean codebase with no dead code

- [ ] **Step 1: Verify no imports reference status_bar or main_window**

```bash
cd /Users/zy/zytest/doujianaodai && grep -r "status_bar\|StatusBar\|main_window\|MainWindow" --include="*.py" app/ ui/ tests/ monitor/ memory/ logs/
```
Expected: no matches (Task 5 rewrote app/main.py to use TrayApp, Task 4 rewrote tests/test_ui.py)

- [ ] **Step 2: Delete the files**

```bash
git rm ui/status_bar.py ui/main_window.py
```

- [ ] **Step 3: Run all tests**

Run: `cd /Users/zy/zytest/doujianaodai && python -m pytest -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git commit -m "chore: remove replaced MainWindow and StatusBar"
```
