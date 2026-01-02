"""Tests for v2_todo_agent.py - TodoManager functionality."""
import pytest
from v2_todo_agent import TodoManager


class TestTodoManager:
    """Tests for the TodoManager class."""

    @pytest.mark.unit
    def test_empty_todo_list(self):
        """Test rendering empty todo list."""
        todo = TodoManager()
        result = todo.render()
        assert "No todos" in result

    @pytest.mark.unit
    def test_valid_todo_update(self):
        """Test updating with valid todo items."""
        todo = TodoManager()
        items = [
            {
                "content": "Task 1",
                "status": "pending",
                "activeForm": "Working on task 1"
            },
            {
                "content": "Task 2",
                "status": "in_progress",
                "activeForm": "Doing task 2"
            },
            {
                "content": "Task 3",
                "status": "completed",
                "activeForm": "Done with task 3"
            }
        ]

        result = todo.update(items)

        assert "Task 1" in result
        assert "Task 2" in result
        assert "Task 3" in result
        assert "[ ]" in result  # pending marker
        assert "[>]" in result  # in_progress marker
        assert "[x]" in result  # completed marker
        assert "(1/3" in result  # progress counter

    @pytest.mark.unit
    def test_rejects_multiple_in_progress(self):
        """Test that only one task can be in_progress."""
        todo = TodoManager()
        items = [
            {
                "content": "Task 1",
                "status": "in_progress",
                "activeForm": "Working 1"
            },
            {
                "content": "Task 2",
                "status": "in_progress",
                "activeForm": "Working 2"
            }
        ]

        with pytest.raises(ValueError, match="Only one task"):
            todo.update(items)

    @pytest.mark.unit
    def test_validates_required_content(self):
        """Test that content field is required."""
        todo = TodoManager()
        items = [
            {
                "status": "pending",
                "activeForm": "Working"
            }
        ]

        with pytest.raises(ValueError, match="content"):
            todo.update(items)

    @pytest.mark.unit
    def test_validates_required_active_form(self):
        """Test that activeForm field is required."""
        todo = TodoManager()
        items = [
            {
                "content": "Task 1",
                "status": "pending"
            }
        ]

        with pytest.raises(ValueError, match="activeForm"):
            todo.update(items)

    @pytest.mark.unit
    def test_validates_status_values(self):
        """Test that status must be valid enum value."""
        todo = TodoManager()
        items = [
            {
                "content": "Task 1",
                "status": "invalid_status",
                "activeForm": "Working"
            }
        ]

        with pytest.raises(ValueError, match="invalid status"):
            todo.update(items)

    @pytest.mark.unit
    def test_max_20_items(self):
        """Test that todo list enforces 20 item maximum."""
        todo = TodoManager()
        items = [
            {
                "content": f"Task {i}",
                "status": "pending",
                "activeForm": f"Working {i}"
            }
            for i in range(25)
        ]

        with pytest.raises(ValueError, match="Max 20"):
            todo.update(items)

    @pytest.mark.unit
    def test_allows_exactly_20_items(self):
        """Test that exactly 20 items is allowed."""
        todo = TodoManager()
        items = [
            {
                "content": f"Task {i}",
                "status": "pending",
                "activeForm": f"Working {i}"
            }
            for i in range(20)
        ]

        # Should not raise
        result = todo.update(items)
        assert len(todo.items) == 20

    @pytest.mark.unit
    def test_render_formats_correctly(self):
        """Test that render formats todos with correct markers."""
        todo = TodoManager()
        todo.items = [
            {"content": "Pending task", "status": "pending", "activeForm": "Working"},
            {"content": "Active task", "status": "in_progress", "activeForm": "Doing"},
            {"content": "Done task", "status": "completed", "activeForm": "Finished"}
        ]

        result = todo.render()

        # Check markers
        assert "[ ] Pending task" in result
        assert "[>] Active task" in result
        assert "[x] Done task" in result

        # Check progress
        assert "(1/3 completed)" in result or "(1/3 done)" in result

    @pytest.mark.unit
    def test_update_replaces_items(self):
        """Test that update replaces the entire todo list."""
        todo = TodoManager()

        # First update
        items1 = [
            {"content": "Task A", "status": "pending", "activeForm": "Working A"}
        ]
        todo.update(items1)
        assert len(todo.items) == 1

        # Second update replaces
        items2 = [
            {"content": "Task B", "status": "pending", "activeForm": "Working B"},
            {"content": "Task C", "status": "pending", "activeForm": "Working C"}
        ]
        todo.update(items2)

        assert len(todo.items) == 2
        assert todo.items[0]["content"] == "Task B"
        assert todo.items[1]["content"] == "Task C"

    @pytest.mark.unit
    def test_strips_whitespace(self):
        """Test that content and activeForm are stripped."""
        todo = TodoManager()
        items = [
            {
                "content": "  Task with spaces  ",
                "status": "pending",
                "activeForm": "  Working  "
            }
        ]

        todo.update(items)

        assert todo.items[0]["content"] == "Task with spaces"
        assert todo.items[0]["activeForm"] == "Working"

    @pytest.mark.unit
    def test_empty_content_after_strip_fails(self):
        """Test that whitespace-only content is rejected."""
        todo = TodoManager()
        items = [
            {
                "content": "   ",
                "status": "pending",
                "activeForm": "Working"
            }
        ]

        with pytest.raises(ValueError, match="content"):
            todo.update(items)

    @pytest.mark.unit
    def test_zero_in_progress_allowed(self):
        """Test that having zero in_progress tasks is valid."""
        todo = TodoManager()
        items = [
            {"content": "Task 1", "status": "pending", "activeForm": "Working 1"},
            {"content": "Task 2", "status": "completed", "activeForm": "Done 2"}
        ]

        # Should not raise
        result = todo.update(items)
        assert "(1/2" in result  # 1 completed out of 2
