"""Tests for SettingsService — 4-layer resolution."""

from gandra_tools.core.settings_service import SettingsService


def test_resolution_fallback_to_default():
    svc = SettingsService()
    assert svc.get("llm.provider") == "openai"
    assert svc.get("llm.model") == "gpt-4o"


def test_resolution_global_overrides_default():
    svc = SettingsService()
    svc.set_global("llm.provider", "anthropic")
    assert svc.get("llm.provider") == "anthropic"


def test_resolution_env_overrides_global():
    svc = SettingsService()
    svc.set_global("llm.provider", "openai")
    svc.set_env_overrides("office-dt", {"llm.provider": "ollama"})
    svc.set_active_env("office-dt")
    assert svc.get("llm.provider") == "ollama"


def test_resolution_user_overrides_env():
    svc = SettingsService()
    svc.set_global("llm.provider", "openai")
    svc.set_env_overrides("office-dt", {"llm.provider": "ollama"})
    svc.set_active_env("office-dt")
    svc.set_user("user@test.com", "llm.provider", "anthropic")
    assert svc.get("llm.provider", user_id="user@test.com") == "anthropic"


def test_get_with_source_returns_origin():
    svc = SettingsService()
    svc.set_user("user@test.com", "llm.provider", "anthropic")

    val, source = svc.get_with_source("llm.provider", user_id="user@test.com")
    assert val == "anthropic"
    assert source == "user"

    val2, source2 = svc.get_with_source("llm.model")
    assert val2 == "gpt-4o"
    assert source2 == "default"


def test_delete_user_reverts_to_global():
    svc = SettingsService()
    svc.set_global("llm.provider", "openai")
    svc.set_user("user@test.com", "llm.provider", "anthropic")
    assert svc.get("llm.provider", user_id="user@test.com") == "anthropic"

    svc.delete_user("user@test.com", "llm.provider")
    assert svc.get("llm.provider", user_id="user@test.com") == "openai"


def test_no_active_env_skips_overrides():
    svc = SettingsService()
    svc.set_env_overrides("office-dt", {"llm.provider": "ollama"})
    # No active env set
    assert svc.get("llm.provider") == "openai"  # Default


def test_list_all_shows_resolved():
    svc = SettingsService()
    svc.set_global("llm.provider", "anthropic")
    result = svc.list_all()
    assert result["llm.provider"]["value"] == "anthropic"
    assert result["llm.provider"]["source"] == "global"
    assert result["llm.model"]["source"] == "default"


def test_output_default_dir_is_gandra_output():
    svc = SettingsService()
    assert svc.get("output.default_dir") == "gandra-output/"
