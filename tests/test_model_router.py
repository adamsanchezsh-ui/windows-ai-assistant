"""Unit tests for model router parsing and agent basics."""

import pytest
from src.model import parse_model_spec
from src.agent import AIMode, SYSTEM_PROMPTS
from src.game_profiles import get_profile, find_profile_by_process


def test_parse_model_spec():
    assert parse_model_spec("openai:gpt-4o") == ("openai", "gpt-4o")
    assert parse_model_spec("anthropic:claude-3-5-sonnet") == ("anthropic", "claude-3-5-sonnet")
    assert parse_model_spec("gpt-4o") == ("openai", "gpt-4o")


def test_all_modes_have_prompts():
    for mode in AIMode:
        assert mode in SYSTEM_PROMPTS
        assert len(SYSTEM_PROMPTS[mode]) > 10


def test_game_profiles():
    mc = get_profile("minecraft")
    assert mc is not None
    assert "javaw.exe" in mc.process_names

    found = find_profile_by_process("cs2.exe")
    assert found is not None
    assert found.name == "cs2"

    assert get_profile("nonexistent") is None
