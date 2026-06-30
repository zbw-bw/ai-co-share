### Task 6: PyPI Packaging — pyproject.toml, MANIFEST.in, cleanup

**Files:**
- Create: `pyproject.toml`
- Create: `MANIFEST.in`
- Create: `LICENSE`
- Modify: `requirements.txt`
- Delete: `setup.py`
- Delete: `test_pipeline.py`
- Create: `ui/__init__.py` (ensure exists — already exists but verify)
- Create: `logs/__init__.py` (ensure exists)

**Interfaces:**
- Consumes: `app.main:main` entry point (Task 5)
- Produces: `doujianaodai` CLI command via `pip install .`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "doujianaodai"
version = "0.1.0"
description = "桌面宠物 Agent — 被动屏幕监控 + 活动记忆 + AI 对话"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11"
keywords = ["desktop-pet", "screen-monitor", "ai-agent", "ocr"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: MacOS X",
    "Programming Language :: Python :: 3.11",
    "Topic :: Utilities",
]
dependencies = [
    "PyQt6>=6.6.0",
    "pyobjc-framework-Quartz>=10.0; sys_platform=='darwin'",
    "pyobjc-framework-Cocoa>=10.0; sys_platform=='darwin'",
    "psutil>=5.9.0",
    "Pillow>=10.0.0",
    "paddleocr>=2.7.0",
    "paddlepaddle>=2.6.0",
    "scikit-image>=0.22.0",
    "numpy>=1.26.0",
    "PyYAML>=6.0",
    "requests>=2.31.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.0"]

[project.scripts]
doujianaodai = "app.main:main"

[tool.setuptools.packages.find]
include = ["app*", "monitor*", "memory*", "logs*", "ui*"]

[tool.setuptools.package-data]
"" = ["config.yaml"]
```

- [ ] **Step 2: Create MANIFEST.in**

```
include config.yaml
include LICENSE
include README.md
include pet_mcp_server.py
```

- [ ] **Step 3: Create LICENSE**

```
MIT License

Copyright (c) 2026 doujianaodai

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 4: Update requirements.txt — remove anthropic and ollama SDK**

```
PyQt6>=6.6.0
pyobjc-framework-Quartz>=10.0; sys_platform == "darwin"
pyobjc-framework-Cocoa>=10.0; sys_platform == "darwin"
psutil>=5.9.0
Pillow>=10.0.0
paddleocr>=2.7.0
paddlepaddle>=2.6.0
scikit-image>=0.22.0
numpy>=1.26.0
PyYAML>=6.0
requests>=2.31.0
```

- [ ] **Step 5: Delete setup.py and test_pipeline.py**

```bash
rm setup.py test_pipeline.py
rm -rf doujianaodai.egg-info/
```

- [ ] **Step 6: Verify __init__.py files exist in all packages**

```bash
# Ensure these exist (create only if missing):
touch logs/__init__.py
```

- [ ] **Step 7: Verify package installs cleanly**

```bash
cd /Users/zy/zytest/doujianaodai && pip install -e ".[dev]"
```
Expected: install succeeds without errors

- [ ] **Step 8: Verify CLI entry point works**

```bash
which doujianaodai
```
Expected: prints a path like `/Users/zy/.../bin/doujianaodai`

- [ ] **Step 9: Run all tests**

Run: `cd /Users/zy/zytest/doujianaodai && python -m pytest -v`
Expected: All tests PASS

- [ ] **Step 10: Commit**

```bash
git add pyproject.toml MANIFEST.in LICENSE requirements.txt logs/__init__.py
git rm setup.py test_pipeline.py
git clean -fd doujianaodai.egg-info/
git commit -m "feat: switch to pyproject.toml packaging, add CLI entry point"
```

---
