# Tests for learn-claude-code

This directory contains the test suite for the learn-claude-code project.

## Running Tests

### Installation

First, install the test dependencies:

```bash
pip install pytest
# Or install all development dependencies:
# pip install -r requirements.txt
```

### Running All Tests

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with detailed failure information
pytest tests/ -v --tb=long

# Run with coverage (requires pytest-cov)
pytest tests/ --cov=. --cov-report=html
```

### Running Specific Tests

```bash
# Run only v1 tests
pytest tests/test_v1_basic_agent.py -v

# Run only v2 TodoManager tests
pytest tests/test_v2_todo_agent.py -v

# Run only unit tests (fast)
pytest tests/ -v -m unit

# Skip slow tests
pytest tests/ -v -m "not slow"
```

## Test Structure

```
tests/
├── README.md                  # This file
├── conftest.py                # Shared fixtures and configuration
├── __init__.py                # Package marker
├── test_v1_basic_agent.py     # Tests for v1 (core tools)
├── test_v2_todo_agent.py      # Tests for v2 (TodoManager)
└── fixtures/                  # Test data files
    └── test_files/
```

## Test Categories

Tests are marked with categories for selective running:

- `@pytest.mark.unit` - Fast unit tests for individual functions
- `@pytest.mark.integration` - Integration tests for agent loops
- `@pytest.mark.slow` - Slow-running tests (timeout tests, etc.)

## Writing New Tests

When adding new tests:

1. Follow the existing structure (TestClassName with test_method_name)
2. Use descriptive test names that explain what is being tested
3. Use fixtures from `conftest.py` for common setup (temp_workspace, sample_files)
4. Mark tests appropriately (`@pytest.mark.unit`, etc.)
5. Add docstrings explaining the test purpose

Example:

```python
@pytest.mark.unit
def test_my_feature(temp_workspace, monkeypatch):
    """Test that my feature works correctly."""
    monkeypatch.setattr('v1_basic_agent.WORKDIR', temp_workspace)

    result = my_function()
    assert result == expected_value
```

## Current Test Coverage

### v1_basic_agent.py
- ✅ safe_path() - Path validation and security
- ✅ run_bash() - Command execution and blocklist
- ✅ run_read() - File reading with limits
- ✅ run_write() - File creation and directories
- ✅ run_edit() - Text replacement
- ✅ execute_tool() - Tool dispatcher

### v2_todo_agent.py
- ✅ TodoManager.update() - Validation logic
- ✅ TodoManager.render() - Formatting
- ✅ Constraint enforcement (max items, single in_progress)

### To Add (Future)
- [ ] v3_subagent.py - Subagent spawning and context isolation
- [ ] v4_skills_agent.py - Skill loading and caching
- [ ] Integration tests with mocked API
- [ ] Error message quality tests

## Continuous Integration

Tests can be run in CI with:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
```

## Notes

- Tests use `monkeypatch` to isolate WORKDIR and avoid modifying the actual project
- The `temp_workspace` fixture provides a clean temporary directory for each test
- Mock fixtures prevent actual API calls during tests
- Tests are designed to run quickly (< 1 second each except slow tests)
