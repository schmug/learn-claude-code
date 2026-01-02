# Implementation Plan: Code Analysis Recommendations

**Generated**: 2026-01-02
**Priority Order**: Critical → High → Medium → Low
**Estimated Total Effort**: 8-12 hours

---

## Critical Priority (Do First)

### 1. Fix requirements.txt ✅ COMPLETED
**Priority**: Critical
**Effort**: 5 minutes
**Impact**: Fixes broken installation for new users

**Current State**:
```txt
pygame==2.5.2
numpy==1.24.3
```

**Changes Required**:
```txt
# Core dependencies
anthropic>=0.18.1,<1.0.0
python-dotenv>=1.0.0,<2.0.0

# Optional: Remove if unused
# pygame==2.5.2
# numpy==1.24.3
```

**Files to Modify**:
- `requirements.txt`

**Action Steps**:
1. Verify pygame/numpy are unused with: `grep -r "import pygame\|import numpy" *.py`
2. Replace requirements.txt content
3. Test fresh install: `pip install -r requirements.txt`
4. Update README Quick Start section if needed

---

### 2. Clarify .env.example ✅ COMPLETED
**Priority**: Critical
**Effort**: 10 minutes
**Impact**: Reduces confusion for international users

**Current State**:
```env
ANTHROPIC_API_KEY=sk-xxx
ANTHROPIC_BASE_URL=https://api.moonshot.cn/anthropic
MODEL_NAME=kimi-k2-turbo-preview
```

**Changes Required**:
```env
# =============================================================================
# API Configuration
# =============================================================================

# Required: Your Anthropic API key
# Get one at: https://console.anthropic.com/settings/keys
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxx

# Optional: Custom API endpoint (for Anthropic-compatible services)
# Default: Official Anthropic API (https://api.anthropic.com)
# Example: Moonshot AI (China): https://api.moonshot.cn/anthropic
# ANTHROPIC_BASE_URL=

# Model Selection
# Official models: claude-sonnet-4-20250514, claude-opus-4-5-20251101
# Moonshot models: kimi-k2-turbo-preview (requires ANTHROPIC_BASE_URL)
MODEL_NAME=claude-sonnet-4-20250514

# =============================================================================
# Advanced Configuration (Optional)
# =============================================================================

# Maximum tokens for model responses (default: 8000)
# MAX_TOKENS=8000

# Timeout for tool execution in seconds (default: 60)
# TOOL_TIMEOUT=60

# Maximum output size in bytes (default: 50000)
# MAX_OUTPUT_SIZE=50000
```

**Files to Modify**:
- `.env.example`

**Action Steps**:
1. Update .env.example with comprehensive comments
2. Add section in README explaining API configuration options
3. Test that default configuration works

---

### 3. Add Security Warning to README ✅ COMPLETED
**Priority**: Critical
**Effort**: 15 minutes
**Impact**: Sets proper expectations about security boundaries

**Changes Required**:

Add new section to README.md after "Philosophy":

```markdown
## Security Considerations

⚠️ **Educational Code - Not Production Ready**

These implementations prioritize **clarity over security**. Before using in production:

### Known Security Limitations

1. **Command Injection Risk**: All versions use `shell=True` in subprocess calls
   - Educational context: Demonstrates agent capabilities
   - Production use: Implement proper command parsing and use `shell=False`

2. **Incomplete Input Validation**: Basic blocklist for dangerous commands
   - Current: Blocks `rm -rf /`, `sudo`, `shutdown`, `reboot`
   - Missing: Many other dangerous patterns
   - Recommendation: Use sandboxing (Docker, firejail) or restricted shells

3. **Path Traversal**: While `safe_path()` validates paths, it's basic
   - Current: Prevents `../` escaping
   - Production: Add chroot or container isolation

### Production Hardening Checklist

- [ ] Replace `shell=True` with proper command parsing
- [ ] Implement sandboxing (Docker, firejail, or restricted Python environment)
- [ ] Add comprehensive input validation and sanitization
- [ ] Enable audit logging for all tool executions
- [ ] Implement rate limiting and resource quotas
- [ ] Add authentication and authorization
- [ ] Review and expand dangerous command blocklist
- [ ] Consider using AST parsing instead of `eval`/`exec` where needed

### Recommended Sandboxing

```bash
# Option 1: Docker (recommended for production)
docker run --rm -it \
  -v $(pwd):/workspace \
  -w /workspace \
  --network none \
  python:3.11 python v1_basic_agent.py

# Option 2: Firejail (Linux)
firejail --noprofile --net=none python v1_basic_agent.py
```

For more on AI agent security, see:
- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [Anthropic Model Safety](https://www.anthropic.com/safety)
```

**Files to Modify**:
- `README.md`
- `README_zh.md` (add Chinese translation)

**Action Steps**:
1. Add security section to README.md
2. Translate and add to README_zh.md
3. Consider adding SECURITY.md with vulnerability reporting process

---

## High Priority

### 4. Add Basic Test Suite ✅ COMPLETED
**Priority**: High
**Effort**: 2-3 hours
**Impact**: Ensures code works, prevents regressions

**Structure**:
```
tests/
├── __init__.py
├── conftest.py              # pytest configuration
├── test_v0_bash_agent.py    # v0 tests
├── test_v1_basic_agent.py   # v1 tests
├── test_v2_todo_agent.py    # v2 tests
├── test_v3_subagent.py      # v3 tests
├── test_v4_skills_agent.py  # v4 tests
└── fixtures/                # test data
    ├── sample_skill/
    │   └── SKILL.md
    └── test_files/
```

**Example Tests**:

```python
# tests/test_v1_basic_agent.py
import pytest
from pathlib import Path
from v1_basic_agent import safe_path, run_bash, run_read, run_write, run_edit, WORKDIR

class TestSafePath:
    def test_safe_path_allows_relative(self):
        result = safe_path("test.txt")
        assert result == WORKDIR / "test.txt"

    def test_safe_path_prevents_escape(self):
        with pytest.raises(ValueError, match="escapes workspace"):
            safe_path("../../../etc/passwd")

    def test_safe_path_allows_subdirs(self):
        result = safe_path("subdir/file.txt")
        assert result == WORKDIR / "subdir" / "file.txt"

class TestBashTool:
    def test_bash_executes_simple_command(self):
        result = run_bash("echo 'hello'")
        assert "hello" in result

    def test_bash_blocks_rm_rf_root(self):
        result = run_bash("rm -rf /")
        assert "Error" in result

    def test_bash_blocks_sudo(self):
        result = run_bash("sudo echo test")
        assert "Error" in result

    def test_bash_timeout(self):
        result = run_bash("sleep 1000")
        assert "timeout" in result.lower() or "Timeout" in result

class TestFileTool:
    def test_write_and_read(self, tmp_path, monkeypatch):
        monkeypatch.setattr('v1_basic_agent.WORKDIR', tmp_path)

        content = "test content\nline 2"
        write_result = run_write("test.txt", content)
        assert "Wrote" in write_result

        read_result = run_read("test.txt")
        assert read_result == content

    def test_edit_replaces_text(self, tmp_path, monkeypatch):
        monkeypatch.setattr('v1_basic_agent.WORKDIR', tmp_path)

        original = "Hello World\nGoodbye World"
        run_write("test.txt", original)

        result = run_edit("test.txt", "Hello", "Hi")
        assert "Edited" in result

        content = run_read("test.txt")
        assert content == "Hi World\nGoodbye World"

    def test_edit_fails_on_missing_text(self, tmp_path, monkeypatch):
        monkeypatch.setattr('v1_basic_agent.WORKDIR', tmp_path)

        run_write("test.txt", "Hello World")
        result = run_edit("test.txt", "Missing", "Replace")
        assert "Error" in result
```

```python
# tests/test_v2_todo_agent.py
import pytest
from v2_todo_agent import TodoManager

class TestTodoManager:
    def test_valid_todo_update(self):
        todo = TodoManager()
        items = [
            {"content": "Task 1", "status": "pending", "activeForm": "Working on task 1"},
            {"content": "Task 2", "status": "in_progress", "activeForm": "Doing task 2"},
        ]
        result = todo.update(items)
        assert "Task 1" in result
        assert "[>]" in result  # in_progress marker

    def test_rejects_multiple_in_progress(self):
        todo = TodoManager()
        items = [
            {"content": "Task 1", "status": "in_progress", "activeForm": "Working 1"},
            {"content": "Task 2", "status": "in_progress", "activeForm": "Working 2"},
        ]
        with pytest.raises(ValueError, match="Only one task"):
            todo.update(items)

    def test_validates_required_fields(self):
        todo = TodoManager()
        items = [{"content": "Task 1", "status": "pending"}]  # Missing activeForm
        with pytest.raises(ValueError, match="activeForm required"):
            todo.update(items)

    def test_max_20_items(self):
        todo = TodoManager()
        items = [
            {"content": f"Task {i}", "status": "pending", "activeForm": f"Working {i}"}
            for i in range(25)
        ]
        result = todo.update(items)
        assert len(todo.items) == 20  # Should truncate
```

```python
# tests/conftest.py
import pytest
from pathlib import Path
import tempfile

@pytest.fixture
def temp_workspace(monkeypatch):
    """Provide isolated workspace for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        yield workspace

@pytest.fixture
def mock_anthropic_client(monkeypatch):
    """Mock Anthropic API calls"""
    class MockMessage:
        def __init__(self):
            self.content = [type('obj', (object,), {'text': 'test response', 'type': 'text'})]
            self.stop_reason = 'end_turn'

    class MockClient:
        def __init__(self, *args, **kwargs):
            pass

        class messages:
            @staticmethod
            def create(*args, **kwargs):
                return MockMessage()

    # Apply mock to all versions
    for module in ['v0_bash_agent', 'v1_basic_agent', 'v2_todo_agent', 'v3_subagent', 'v4_skills_agent']:
        try:
            monkeypatch.setattr(f'{module}.client', MockClient())
        except:
            pass
```

**Files to Create**:
- `tests/__init__.py`
- `tests/conftest.py`
- `tests/test_v1_basic_agent.py` (start with v1, expand to others)
- `tests/test_v2_todo_agent.py`
- `pytest.ini`

**Action Steps**:
1. Install pytest: Add `pytest>=7.0.0` to requirements.txt
2. Create tests directory structure
3. Implement smoke tests (ensure agents start)
4. Implement unit tests for tools
5. Implement integration tests (mock API)
6. Add GitHub Actions CI workflow (optional)

---

### 5. Add Type Annotations
**Priority**: High
**Effort**: 2-3 hours
**Impact**: Better IDE support, early error detection

**Strategy**: Add types to v1-v4 (keep v0 minimalist for pedagogical reasons)

**Example Changes**:

```python
# v1_basic_agent.py - Before
def safe_path(p: str) -> Path:
    """Ensure path stays within workspace."""
    # ... implementation

def run_bash(command: str) -> str:
    """Execute shell command with safety checks."""
    # ... implementation

def run_read(path: str, limit: int = None) -> str:
    """Read file contents with optional line limit."""
    # ... implementation

def execute_tool(name: str, args: dict) -> str:
    """Dispatch tool call to the appropriate implementation."""
    # ... implementation

def agent_loop(messages: list) -> list:
    """The complete agent in one function."""
    # ... implementation
```

```python
# v1_basic_agent.py - After
from typing import Optional, List, Dict, Any

def safe_path(p: str) -> Path:
    """Ensure path stays within workspace."""
    # ... implementation

def run_bash(command: str) -> str:
    """Execute shell command with safety checks."""
    # ... implementation

def run_read(path: str, limit: Optional[int] = None) -> str:
    """Read file contents with optional line limit."""
    # ... implementation

def execute_tool(name: str, args: Dict[str, Any]) -> str:
    """Dispatch tool call to the appropriate implementation."""
    # ... implementation

def agent_loop(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The complete agent in one function."""
    # ... implementation
```

```python
# v2_todo_agent.py - TodoManager
from typing import List, Dict, Any

class TodoManager:
    def __init__(self) -> None:
        self.items: List[Dict[str, str]] = []

    def update(self, items: List[Dict[str, Any]]) -> str:
        """Validate and update the todo list."""
        # ... implementation

    def render(self) -> str:
        """Render the todo list as human-readable text."""
        # ... implementation
```

**Files to Modify**:
- `v1_basic_agent.py`
- `v2_todo_agent.py`
- `v3_subagent.py`
- `v4_skills_agent.py`

**Action Steps**:
1. Add `from typing import ...` imports
2. Add return type hints to all functions
3. Add parameter type hints
4. Add type hints to class attributes
5. Install mypy: `pip install mypy`
6. Create `mypy.ini` configuration
7. Run `mypy v1_basic_agent.py` and fix issues
8. Add mypy to CI (optional)

**mypy.ini**:
```ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True

# Be lenient with imports for educational code
ignore_missing_imports = True
```

---

### 6. Improve Error Messages
**Priority**: High
**Effort**: 1 hour
**Impact**: Better debugging experience

**Current Pattern** (generic):
```python
except Exception as e:
    return f"Error: {e}"
```

**Improved Pattern** (specific):

```python
# v1_basic_agent.py - run_bash
def run_bash(command: str) -> str:
    """Execute shell command with safety checks."""
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous):
        return f"Error: Dangerous command blocked: '{command}'\nBlocked patterns: {dangerous}"

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=WORKDIR,
            capture_output=True,
            text=True,
            timeout=60
        )
        output = (result.stdout + result.stderr).strip()
        return output[:50000] if output else "(no output)"

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after 60 seconds: '{command}'\nTip: Use background processes for long-running commands."
    except FileNotFoundError as e:
        return f"Error: Command not found: '{command}'\nDetails: {e}\nTip: Check if the command is installed (e.g., 'which {command.split()[0]}')"
    except PermissionError as e:
        return f"Error: Permission denied: '{command}'\nDetails: {e}"
    except Exception as e:
        return f"Error ({type(e).__name__}): {e}\nCommand: '{command}'"
```

```python
# v1_basic_agent.py - run_read
def run_read(path: str, limit: Optional[int] = None) -> str:
    """Read file contents with optional line limit."""
    try:
        text = safe_path(path).read_text()
        lines = text.splitlines()

        if limit and limit < len(lines):
            lines = lines[:limit]
            lines.append(f"... ({len(text.splitlines()) - limit} more lines)")

        return "\n".join(lines)[:50000]

    except FileNotFoundError:
        return f"Error: File not found: '{path}'\nTip: Use 'bash' tool with 'ls' or 'find' to locate the file."
    except PermissionError:
        return f"Error: Permission denied when reading: '{path}'\nTip: Check file permissions with 'ls -la {path}'"
    except UnicodeDecodeError:
        return f"Error: Cannot decode file as UTF-8: '{path}'\nTip: This might be a binary file. Use 'file {path}' to check."
    except Exception as e:
        return f"Error ({type(e).__name__}) reading '{path}': {e}"
```

```python
# v1_basic_agent.py - run_write
def run_write(path: str, content: str) -> str:
    """Write content to file, creating parent directories if needed."""
    try:
        fp = safe_path(path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content)
        return f"Wrote {len(content)} bytes to {path}"

    except PermissionError:
        return f"Error: Permission denied when writing to: '{path}'\nTip: Check directory permissions."
    except OSError as e:
        return f"Error: OS error when writing to '{path}': {e}\nTip: Check disk space and path validity."
    except Exception as e:
        return f"Error ({type(e).__name__}) writing to '{path}': {e}"
```

```python
# v1_basic_agent.py - run_edit
def run_edit(path: str, old_text: str, new_text: str) -> str:
    """Replace exact text in a file (surgical edit)."""
    try:
        fp = safe_path(path)
        content = fp.read_text()

        if old_text not in content:
            # Helpful debug info
            lines = content.splitlines()
            preview = "\n".join(lines[:5])
            return (f"Error: Text not found in {path}\n"
                   f"Looking for: '{old_text[:100]}...'\n"
                   f"File preview (first 5 lines):\n{preview}\n"
                   f"Tip: Check for exact match including whitespace.")

        new_content = content.replace(old_text, new_text, 1)
        fp.write_text(new_content)
        return f"Edited {path}: Replaced text (old: {len(old_text)} chars, new: {len(new_text)} chars)"

    except FileNotFoundError:
        return f"Error: File not found: '{path}'"
    except Exception as e:
        return f"Error ({type(e).__name__}) editing '{path}': {e}"
```

**Files to Modify**:
- `v1_basic_agent.py`
- `v2_todo_agent.py`
- `v3_subagent.py`
- `v4_skills_agent.py`

**Action Steps**:
1. Replace generic `except Exception as e` with specific exceptions
2. Add helpful tips in error messages
3. Include context (command/path/etc) in errors
4. Test error messages with intentional failures

---

## Medium Priority

### 7. Add Linting Configuration
**Priority**: Medium
**Effort**: 30 minutes
**Impact**: Consistent code style

**Tools**: Use `ruff` (modern, fast linter that replaces flake8, black, isort, etc.)

**Files to Create**:

**pyproject.toml**:
```toml
[tool.ruff]
# Target Python 3.11+
target-version = "py311"

# Line length to match educational style
line-length = 100

# Enable select rules
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "N",  # pep8-naming
    "UP", # pyupgrade
    "B",  # flake8-bugbear
]

# Ignore specific rules
ignore = [
    "E501",  # line too long (handled by formatter)
    "B008",  # do not perform function calls in argument defaults
]

# Exclude patterns
exclude = [
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "build",
    "dist",
]

[tool.ruff.format]
# Use double quotes
quote-style = "double"

# Indent with spaces
indent-style = "space"

[tool.ruff.isort]
# Group imports
known-first-party = ["v0_bash_agent", "v1_basic_agent", "v2_todo_agent", "v3_subagent", "v4_skills_agent"]
```

**.pre-commit-config.yaml** (optional, for git hooks):
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
```

**Files to Create**:
- `pyproject.toml`
- `.pre-commit-config.yaml` (optional)

**Action Steps**:
1. Add `ruff>=0.1.9` to requirements.txt
2. Create pyproject.toml with ruff config
3. Run `ruff check .` to see issues
4. Run `ruff check . --fix` to auto-fix
5. Run `ruff format .` to format code
6. Add to CI workflow (optional)

---

### 8. Implement Subagent Depth Limit
**Priority**: Medium
**Effort**: 30 minutes
**Impact**: Prevents infinite recursion

**Changes**:

```python
# v3_subagent.py and v4_skills_agent.py

# Add constant at top
MAX_SUBAGENT_DEPTH = 3

# Modify run_task signature
def run_task(description: str, prompt: str, agent_type: str, _depth: int = 0) -> str:
    """
    Execute a subagent task with isolated context.

    Args:
        description: Short task name for display
        prompt: Detailed instructions for subagent
        agent_type: Type of agent to spawn
        _depth: Internal recursion depth counter

    Returns:
        Final text response from subagent
    """
    # Check depth limit
    if _depth >= MAX_SUBAGENT_DEPTH:
        return (f"Error: Maximum subagent depth ({MAX_SUBAGENT_DEPTH}) reached.\n"
                f"Current depth: {_depth}\n"
                f"Tip: Break down the task into smaller sequential steps instead of nesting subagents.")

    if agent_type not in AGENT_TYPES:
        return f"Error: Unknown agent type '{agent_type}'"

    # ... rest of implementation stays the same ...

    # When calling execute_tool for nested Task calls, pass depth
    # Modify execute_tool to accept and forward depth:

def execute_tool(name: str, args: dict, _depth: int = 0) -> str:
    """Dispatch tool call to implementation."""
    if name == "bash":
        return run_bash(args["command"])
    if name == "read_file":
        return run_read(args["path"], args.get("limit"))
    if name == "write_file":
        return run_write(args["path"], args["content"])
    if name == "edit_file":
        return run_edit(args["path"], args["old_text"], args["new_text"])
    if name == "TodoWrite":
        return run_todo(args["items"])
    if name == "Task":
        # Pass incremented depth
        return run_task(args["description"], args["prompt"], args["agent_type"], _depth=_depth + 1)
    if name == "Skill":
        return run_skill(args["skill"])
    return f"Unknown tool: {name}"

# In run_task's internal loop, when executing tools:
for tc in tool_calls:
    tool_count += 1
    output = execute_tool(tc.name, tc.input, _depth=_depth)  # Pass depth
    # ... rest stays same
```

**Files to Modify**:
- `v3_subagent.py` (lines 425-534)
- `v4_skills_agent.py` (lines 609-690)

**Action Steps**:
1. Add MAX_SUBAGENT_DEPTH constant
2. Add _depth parameter to run_task
3. Add depth check at start of run_task
4. Modify execute_tool to pass depth
5. Add test for depth limit
6. Document in system prompt or tool description

---

### 9. Add Caching to Skill Loading
**Priority**: Medium
**Effort**: 15 minutes
**Impact**: Minor performance optimization

**Changes**:

```python
# v4_skills_agent.py

from functools import lru_cache

class SkillLoader:
    """Loads and manages skills from SKILL.md files."""

    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.skills = {}
        self.load_skills()

    # ... other methods stay the same ...

    @lru_cache(maxsize=32)
    def get_skill_content(self, name: str) -> Optional[str]:
        """
        Get full skill content for injection (cached).

        This is Layer 2 - the complete SKILL.md body, plus any available
        resources (Layer 3 hints).

        Results are cached to avoid re-parsing on repeated loads.

        Returns None if skill not found.
        """
        if name not in self.skills:
            return None

        skill = self.skills[name]
        content = f"# Skill: {skill['name']}\n\n{skill['body']}"

        # List available resources
        resources = []
        for folder, label in [
            ("scripts", "Scripts"),
            ("references", "References"),
            ("assets", "Assets")
        ]:
            folder_path = skill["dir"] / folder
            if folder_path.exists():
                files = list(folder_path.glob("*"))
                if files:
                    resources.append(f"{label}: {', '.join(f.name for f in files)}")

        if resources:
            content += f"\n\n**Available resources in {skill['dir']}:**\n"
            content += "\n".join(f"- {r}" for r in resources)

        return content

    def clear_cache(self) -> None:
        """Clear the skill content cache (useful if skills are modified)."""
        self.get_skill_content.cache_clear()
```

**Files to Modify**:
- `v4_skills_agent.py` (lines 222-254)

**Action Steps**:
1. Import lru_cache from functools
2. Add @lru_cache decorator to get_skill_content
3. Add clear_cache() method
4. Update type hint to Optional[str]
5. Add note in docstring about caching

---

## Low Priority (Nice to Have)

### 10. Make Hardcoded Constants Configurable
**Priority**: Low
**Effort**: 30 minutes
**Impact**: Better customization

**Changes**:

```python
# All versions (v1-v4) - Update configuration section

# Configuration
API_KEY = os.getenv("ANTHROPIC_API_KEY")
BASE_URL = os.getenv("ANTHROPIC_BASE_URL")
MODEL = os.getenv("MODEL_NAME", "claude-sonnet-4-20250514")
WORKDIR = Path.cwd()

# New: Configurable limits
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "8000"))
TOOL_TIMEOUT = int(os.getenv("TOOL_TIMEOUT", "60"))
MAX_OUTPUT_SIZE = int(os.getenv("MAX_OUTPUT_SIZE", "50000"))

# Use in run_bash
def run_bash(command: str) -> str:
    """Execute shell command with safety checks."""
    # ... safety checks ...
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=WORKDIR,
            capture_output=True,
            text=True,
            timeout=TOOL_TIMEOUT  # Use config
        )
        output = (result.stdout + result.stderr).strip()
        return output[:MAX_OUTPUT_SIZE] if output else "(no output)"  # Use config
    # ... error handling ...

# Use in agent_loop
def agent_loop(messages: list) -> list:
    while True:
        response = client.messages.create(
            model=MODEL,
            system=SYSTEM,
            messages=messages,
            tools=TOOLS,
            max_tokens=MAX_TOKENS,  # Use config
        )
        # ... rest stays same ...
```

**Files to Modify**:
- `v1_basic_agent.py`
- `v2_todo_agent.py`
- `v3_subagent.py`
- `v4_skills_agent.py`
- `.env.example` (add documentation)

**Action Steps**:
1. Add constants with os.getenv() at top of each file
2. Replace hardcoded values throughout
3. Update .env.example with new options
4. Document in README

---

### 11. Add TodoManager Max Length Validation
**Priority**: Low
**Effort**: 10 minutes
**Impact**: Edge case handling

**Changes**:

```python
# v2_todo_agent.py, v3_subagent.py, v4_skills_agent.py

class TodoManager:
    """Manages a structured task list with enforced constraints."""

    MAX_ITEMS = 20
    MAX_CONTENT_LENGTH = 200
    MAX_ACTIVE_LENGTH = 100

    def __init__(self):
        self.items = []

    def update(self, items: list) -> str:
        """Validate and update the todo list."""
        validated = []
        in_progress_count = 0

        for i, item in enumerate(items):
            # Extract and validate fields
            content = str(item.get("content", "")).strip()
            status = str(item.get("status", "pending")).lower()
            active_form = str(item.get("activeForm", "")).strip()

            # Validation checks
            if not content:
                raise ValueError(f"Item {i}: content required")
            if len(content) > self.MAX_CONTENT_LENGTH:
                raise ValueError(
                    f"Item {i}: content too long ({len(content)} chars, max {self.MAX_CONTENT_LENGTH})\n"
                    f"Tip: Keep todo items concise. Full context goes in the task itself."
                )
            if not active_form:
                raise ValueError(f"Item {i}: activeForm required")
            if len(active_form) > self.MAX_ACTIVE_LENGTH:
                raise ValueError(
                    f"Item {i}: activeForm too long ({len(active_form)} chars, max {self.MAX_ACTIVE_LENGTH})"
                )
            if status not in ("pending", "in_progress", "completed"):
                raise ValueError(f"Item {i}: invalid status '{status}'")

            if status == "in_progress":
                in_progress_count += 1

            validated.append({
                "content": content,
                "status": status,
                "activeForm": active_form
            })

        # Enforce constraints
        if len(validated) > self.MAX_ITEMS:
            raise ValueError(f"Max {self.MAX_ITEMS} todos allowed (got {len(validated)})")
        if in_progress_count > 1:
            raise ValueError("Only one task can be in_progress at a time")

        self.items = validated
        return self.render()
```

**Files to Modify**:
- `v2_todo_agent.py` (lines 90-161)
- `v3_subagent.py` (lines 147-191)
- `v4_skills_agent.py` (lines 300-343)

**Action Steps**:
1. Add MAX_CONTENT_LENGTH and MAX_ACTIVE_LENGTH class constants
2. Add length validation in update() method
3. Improve error messages with tips
4. Add tests for validation

---

## Implementation Order

### Week 1: Critical + High Priority
**Day 1** (1-2 hours):
- [ ] Fix requirements.txt (#1)
- [ ] Update .env.example (#2)
- [ ] Add security warning to README (#3)

**Day 2-3** (4-6 hours):
- [ ] Set up test infrastructure (#4)
- [ ] Write unit tests for v1 tools
- [ ] Write tests for TodoManager

**Day 4-5** (3-4 hours):
- [ ] Add type annotations to v1 (#5)
- [ ] Add type annotations to v2-v4
- [ ] Run mypy and fix issues

**Day 6** (1-2 hours):
- [ ] Improve error messages in v1 (#6)
- [ ] Apply to v2-v4

### Week 2: Medium + Low Priority
**Day 1** (30 min):
- [ ] Add linting configuration (#7)
- [ ] Run ruff and fix issues

**Day 2** (1 hour):
- [ ] Implement subagent depth limit (#8)
- [ ] Add tests for depth limit

**Day 3** (30 min):
- [ ] Add skill caching (#9)
- [ ] Make constants configurable (#10)

**Day 4** (30 min):
- [ ] Add TodoManager length validation (#11)
- [ ] Final testing and verification

---

## Testing Checklist

After each implementation:
- [ ] All Python files compile without syntax errors
- [ ] All tests pass
- [ ] Mypy type checking passes (if applicable)
- [ ] Ruff linting passes (if applicable)
- [ ] Manual smoke test: each version can start and handle a simple request
- [ ] Documentation updated (README, docstrings)
- [ ] Changes committed with descriptive messages

---

## Success Metrics

**Before**:
- Missing dependencies in requirements.txt
- No type annotations
- No tests
- Generic error messages
- No linting
- Potential infinite recursion
- Unclear .env.example

**After**:
- ✅ Complete dependencies
- ✅ Full type coverage (v1-v4)
- ✅ Test suite with >80% coverage
- ✅ Helpful error messages
- ✅ Consistent code style
- ✅ Depth limits on recursion
- ✅ Clear configuration docs
- ✅ Security warnings prominent

---

## Notes

1. **Keep v0 Minimalist**: Don't add types/tests to v0_bash_agent.py or v0_bash_agent_mini.py - their pedagogical value is in simplicity

2. **Maintain Educational Focus**: All changes should preserve code clarity. If a change makes code harder to understand, reconsider it.

3. **Test As You Go**: Don't implement all changes then test. Test each change individually.

4. **Document Why, Not Just What**: Update docstrings to explain the reasoning behind changes, not just what changed.

5. **Incremental Commits**: Commit after each major change with clear messages following conventional commits format.

---

**Total Estimated Time**: 8-12 hours
**Priority**: Critical items can be done in 1-2 hours for immediate impact
**Optional**: Low priority items can be skipped if time-constrained
