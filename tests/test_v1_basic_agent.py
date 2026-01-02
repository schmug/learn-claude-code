"""Tests for v1_basic_agent.py - Core agent with 4 tools."""
import pytest
from pathlib import Path
from unittest.mock import patch
import sys

# Import the module under test
import v1_basic_agent


class TestSafePath:
    """Tests for the safe_path() function."""

    @pytest.mark.unit
    def test_safe_path_allows_relative(self, temp_workspace, monkeypatch):
        """Test that safe_path allows relative paths within workspace."""
        monkeypatch.setattr('v1_basic_agent.WORKDIR', temp_workspace)

        result = v1_basic_agent.safe_path("test.txt")
        assert result == temp_workspace / "test.txt"

    @pytest.mark.unit
    def test_safe_path_prevents_escape_dotdot(self, temp_workspace, monkeypatch):
        """Test that safe_path prevents directory traversal with ../"""
        monkeypatch.setattr('v1_basic_agent.WORKDIR', temp_workspace)

        with pytest.raises(ValueError, match="escapes workspace"):
            v1_basic_agent.safe_path("../../../etc/passwd")

    @pytest.mark.unit
    def test_safe_path_prevents_escape_absolute(self, temp_workspace, monkeypatch):
        """Test that safe_path prevents absolute paths outside workspace."""
        monkeypatch.setattr('v1_basic_agent.WORKDIR', temp_workspace)

        with pytest.raises(ValueError, match="escapes workspace"):
            v1_basic_agent.safe_path("/etc/passwd")

    @pytest.mark.unit
    def test_safe_path_allows_subdirs(self, temp_workspace, monkeypatch):
        """Test that safe_path allows subdirectories within workspace."""
        monkeypatch.setattr('v1_basic_agent.WORKDIR', temp_workspace)

        result = v1_basic_agent.safe_path("subdir/file.txt")
        assert result == temp_workspace / "subdir" / "file.txt"


class TestBashTool:
    """Tests for the run_bash() function."""

    @pytest.mark.unit
    def test_bash_executes_simple_command(self, temp_workspace, monkeypatch):
        """Test that bash can execute simple commands."""
        monkeypatch.setattr('v1_basic_agent.WORKDIR', temp_workspace)

        result = v1_basic_agent.run_bash("echo 'hello world'")
        assert "hello world" in result

    @pytest.mark.unit
    def test_bash_blocks_rm_rf_root(self):
        """Test that dangerous rm -rf / command is blocked."""
        result = v1_basic_agent.run_bash("rm -rf /")
        assert "Error" in result
        assert "Dangerous" in result or "blocked" in result.lower()

    @pytest.mark.unit
    def test_bash_blocks_sudo(self):
        """Test that sudo commands are blocked."""
        result = v1_basic_agent.run_bash("sudo echo test")
        assert "Error" in result

    @pytest.mark.unit
    def test_bash_blocks_shutdown(self):
        """Test that shutdown commands are blocked."""
        result = v1_basic_agent.run_bash("shutdown now")
        assert "Error" in result

    @pytest.mark.unit
    def test_bash_blocks_reboot(self):
        """Test that reboot commands are blocked."""
        result = v1_basic_agent.run_bash("reboot")
        assert "Error" in result

    @pytest.mark.unit
    def test_bash_returns_stdout(self, temp_workspace, monkeypatch):
        """Test that bash returns stdout from commands."""
        monkeypatch.setattr('v1_basic_agent.WORKDIR', temp_workspace)

        result = v1_basic_agent.run_bash("echo 'test output'")
        assert "test output" in result

    @pytest.mark.unit
    def test_bash_works_in_workspace(self, temp_workspace, monkeypatch):
        """Test that bash commands execute in the workspace directory."""
        monkeypatch.setattr('v1_basic_agent.WORKDIR', temp_workspace)

        # Create a file and verify it's in the workspace
        v1_basic_agent.run_bash("touch marker.txt")
        assert (temp_workspace / "marker.txt").exists()

    @pytest.mark.unit
    @pytest.mark.slow
    def test_bash_timeout(self, temp_workspace, monkeypatch):
        """Test that long-running commands timeout."""
        monkeypatch.setattr('v1_basic_agent.WORKDIR', temp_workspace)

        result = v1_basic_agent.run_bash("sleep 120")
        assert "timeout" in result.lower() or "Error" in result


class TestReadFileTool:
    """Tests for the run_read() function."""

    @pytest.mark.unit
    def test_read_simple_file(self, temp_workspace, sample_files, monkeypatch):
        """Test reading a simple text file."""
        monkeypatch.setattr('v1_basic_agent.WORKDIR', temp_workspace)

        result = v1_basic_agent.run_read("test.txt")
        assert "Hello World" in result
        assert "Line 2" in result

    @pytest.mark.unit
    def test_read_with_limit(self, temp_workspace, sample_files, monkeypatch):
        """Test reading file with line limit."""
        monkeypatch.setattr('v1_basic_agent.WORKDIR', temp_workspace)

        result = v1_basic_agent.run_read("test.txt", limit=1)
        assert "Hello World" in result
        assert "more lines" in result  # Should indicate truncation

    @pytest.mark.unit
    def test_read_nonexistent_file(self, temp_workspace, monkeypatch):
        """Test that reading nonexistent file returns error."""
        monkeypatch.setattr('v1_basic_agent.WORKDIR', temp_workspace)

        result = v1_basic_agent.run_read("nonexistent.txt")
        assert "Error" in result

    @pytest.mark.unit
    def test_read_nested_file(self, temp_workspace, sample_files, monkeypatch):
        """Test reading file in subdirectory."""
        monkeypatch.setattr('v1_basic_agent.WORKDIR', temp_workspace)

        result = v1_basic_agent.run_read("subdir/nested.txt")
        assert "Nested content" in result


class TestWriteFileTool:
    """Tests for the run_write() function."""

    @pytest.mark.unit
    def test_write_new_file(self, temp_workspace, monkeypatch):
        """Test creating a new file."""
        monkeypatch.setattr('v1_basic_agent.WORKDIR', temp_workspace)

        content = "Test content\nLine 2"
        result = v1_basic_agent.run_write("new_file.txt", content)

        assert "Wrote" in result
        assert (temp_workspace / "new_file.txt").exists()
        assert (temp_workspace / "new_file.txt").read_text() == content

    @pytest.mark.unit
    def test_write_creates_parent_dirs(self, temp_workspace, monkeypatch):
        """Test that write creates parent directories if needed."""
        monkeypatch.setattr('v1_basic_agent.WORKDIR', temp_workspace)

        result = v1_basic_agent.run_write("deep/nested/file.txt", "content")

        assert "Wrote" in result
        assert (temp_workspace / "deep" / "nested" / "file.txt").exists()

    @pytest.mark.unit
    def test_write_overwrites_existing(self, temp_workspace, sample_files, monkeypatch):
        """Test that write overwrites existing files."""
        monkeypatch.setattr('v1_basic_agent.WORKDIR', temp_workspace)

        new_content = "Replaced content"
        v1_basic_agent.run_write("test.txt", new_content)

        assert (temp_workspace / "test.txt").read_text() == new_content


class TestEditFileTool:
    """Tests for the run_edit() function."""

    @pytest.mark.unit
    def test_edit_replaces_text(self, temp_workspace, sample_files, monkeypatch):
        """Test that edit replaces exact text match."""
        monkeypatch.setattr('v1_basic_agent.WORKDIR', temp_workspace)

        result = v1_basic_agent.run_edit("test.txt", "Hello World", "Hi Universe")

        assert "Edited" in result
        content = (temp_workspace / "test.txt").read_text()
        assert "Hi Universe" in content
        assert "Hello World" not in content

    @pytest.mark.unit
    def test_edit_only_first_occurrence(self, temp_workspace, monkeypatch):
        """Test that edit only replaces first occurrence."""
        monkeypatch.setattr('v1_basic_agent.WORKDIR', temp_workspace)

        # Create file with repeated text
        (temp_workspace / "repeat.txt").write_text("foo\nfoo\nfoo")

        v1_basic_agent.run_edit("repeat.txt", "foo", "bar")

        content = (temp_workspace / "repeat.txt").read_text()
        assert content.count("bar") == 1
        assert content.count("foo") == 2

    @pytest.mark.unit
    def test_edit_missing_text_fails(self, temp_workspace, sample_files, monkeypatch):
        """Test that edit fails when text not found."""
        monkeypatch.setattr('v1_basic_agent.WORKDIR', temp_workspace)

        result = v1_basic_agent.run_edit("test.txt", "NOT PRESENT", "replacement")

        assert "Error" in result
        assert "not found" in result.lower()

    @pytest.mark.unit
    def test_edit_nonexistent_file(self, temp_workspace, monkeypatch):
        """Test that editing nonexistent file returns error."""
        monkeypatch.setattr('v1_basic_agent.WORKDIR', temp_workspace)

        result = v1_basic_agent.run_edit("missing.txt", "old", "new")
        assert "Error" in result


class TestExecuteTool:
    """Tests for the execute_tool() dispatcher."""

    @pytest.mark.unit
    def test_execute_bash(self, temp_workspace, monkeypatch):
        """Test execute_tool dispatches bash correctly."""
        monkeypatch.setattr('v1_basic_agent.WORKDIR', temp_workspace)

        result = v1_basic_agent.execute_tool("bash", {"command": "echo test"})
        assert "test" in result

    @pytest.mark.unit
    def test_execute_read(self, temp_workspace, sample_files, monkeypatch):
        """Test execute_tool dispatches read_file correctly."""
        monkeypatch.setattr('v1_basic_agent.WORKDIR', temp_workspace)

        result = v1_basic_agent.execute_tool("read_file", {"path": "test.txt"})
        assert "Hello World" in result

    @pytest.mark.unit
    def test_execute_write(self, temp_workspace, monkeypatch):
        """Test execute_tool dispatches write_file correctly."""
        monkeypatch.setattr('v1_basic_agent.WORKDIR', temp_workspace)

        result = v1_basic_agent.execute_tool("write_file", {
            "path": "new.txt",
            "content": "content"
        })
        assert "Wrote" in result

    @pytest.mark.unit
    def test_execute_edit(self, temp_workspace, sample_files, monkeypatch):
        """Test execute_tool dispatches edit_file correctly."""
        monkeypatch.setattr('v1_basic_agent.WORKDIR', temp_workspace)

        result = v1_basic_agent.execute_tool("edit_file", {
            "path": "test.txt",
            "old_text": "Hello World",
            "new_text": "Hi"
        })
        assert "Edited" in result

    @pytest.mark.unit
    def test_execute_unknown_tool(self):
        """Test execute_tool handles unknown tools."""
        result = v1_basic_agent.execute_tool("unknown_tool", {})
        assert "Unknown tool" in result
