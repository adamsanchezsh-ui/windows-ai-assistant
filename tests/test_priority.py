"""Tests for priority helpers (no real process changes)."""

from src.priority import find_pids_by_name


def test_find_pids_returns_list():
    # Should not crash; may return empty list
    result = find_pids_by_name("nonexistent_process_xyz_12345.exe")
    assert isinstance(result, list)
