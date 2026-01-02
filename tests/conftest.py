"""Pytest configuration and shared fixtures."""
import pytest
import tempfile
from pathlib import Path
from typing import Generator


@pytest.fixture
def temp_workspace() -> Generator[Path, None, None]:
    """
    Provide an isolated temporary workspace for tests.

    This fixture creates a temporary directory that gets cleaned up
    after the test completes. Use this instead of modifying the actual
    project workspace.

    Yields:
        Path: Path to temporary workspace directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        yield workspace


@pytest.fixture
def sample_files(temp_workspace: Path) -> dict:
    """
    Create sample files in the temporary workspace.

    Returns:
        dict: Mapping of file purposes to their paths
    """
    files = {}

    # Simple text file
    simple_file = temp_workspace / "test.txt"
    simple_file.write_text("Hello World\nLine 2\nLine 3")
    files["simple"] = simple_file

    # Python file
    py_file = temp_workspace / "script.py"
    py_file.write_text('#!/usr/bin/env python\nprint("Hello from Python")\n')
    files["python"] = py_file

    # Nested directory structure
    subdir = temp_workspace / "subdir"
    subdir.mkdir()
    nested_file = subdir / "nested.txt"
    nested_file.write_text("Nested content")
    files["nested"] = nested_file

    return files


@pytest.fixture
def mock_anthropic_client(monkeypatch):
    """
    Mock Anthropic API client to avoid real API calls in tests.

    This fixture creates a mock client that returns predefined responses
    without making actual API calls. Use this for integration tests.
    """
    class MockTextBlock:
        def __init__(self, text: str):
            self.text = text
            self.type = "text"

    class MockMessage:
        def __init__(self, text: str = "Test response", stop_reason: str = "end_turn"):
            self.content = [MockTextBlock(text)]
            self.stop_reason = stop_reason

    class MockMessages:
        @staticmethod
        def create(*args, **kwargs):
            return MockMessage()

    class MockClient:
        def __init__(self, *args, **kwargs):
            self.messages = MockMessages()

    # Patch the client for all agent modules
    for module in ['v0_bash_agent', 'v1_basic_agent', 'v2_todo_agent',
                   'v3_subagent', 'v4_skills_agent']:
        try:
            # This will be patched in individual test files
            pass
        except:
            pass

    return MockClient
