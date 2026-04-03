"""Settings service — 4-layer resolution: user → env → global → default."""

import json
from typing import Any

from gandra_tools.core.config import get_settings

DEFAULTS: dict[str, Any] = {
    "llm.provider": "openai",
    "llm.model": "gpt-4o",
    "llm.temperature": 1.0,
    "llm.max_tokens": 4000,
    "embeddings.provider": "openai",
    "embeddings.model": "text-embedding-3-small",
    "output.default_dir": "gandra-output/",
    "output.default_format": "md",
    "env.active": None,
    "system.log_level": "INFO",
    "system.debug": False,
}


class SettingsService:
    """Reads settings with resolution: user → env → global → default.

    For Phase 1, settings are resolved from env vars + defaults.
    DB-backed storage (GlobalSetting, UserSetting, CodebookEnvironment)
    will be added when DB models are implemented.
    """

    def __init__(self) -> None:
        self._user_settings: dict[str, dict[str, Any]] = {}
        self._global_settings: dict[str, Any] = {}
        self._env_overrides: dict[str, dict[str, Any]] = {}
        self._active_env: str | None = None

    def get(self, key: str, user_id: str | None = None) -> Any:
        """Read setting with resolution order."""
        # 1. User-level
        if user_id and user_id in self._user_settings:
            user_val = self._user_settings[user_id].get(key)
            if user_val is not None:
                return user_val

        # 2. Active environment override
        if self._active_env and self._active_env in self._env_overrides:
            env_val = self._env_overrides[self._active_env].get(key)
            if env_val is not None:
                return env_val

        # 3. Global-level
        global_val = self._global_settings.get(key)
        if global_val is not None:
            return global_val

        # 4. Hardcoded default
        return DEFAULTS.get(key)

    def get_with_source(self, key: str, user_id: str | None = None) -> tuple[Any, str]:
        """Return (value, source) where source is 'user'|'env'|'global'|'default'."""
        if user_id and user_id in self._user_settings:
            user_val = self._user_settings[user_id].get(key)
            if user_val is not None:
                return user_val, "user"

        if self._active_env and self._active_env in self._env_overrides:
            env_val = self._env_overrides[self._active_env].get(key)
            if env_val is not None:
                return env_val, "env"

        global_val = self._global_settings.get(key)
        if global_val is not None:
            return global_val, "global"

        return DEFAULTS.get(key), "default"

    def set_user(self, user_id: str, key: str, value: Any) -> None:
        if user_id not in self._user_settings:
            self._user_settings[user_id] = {}
        self._user_settings[user_id][key] = value

    def set_global(self, key: str, value: Any) -> None:
        self._global_settings[key] = value

    def delete_user(self, user_id: str, key: str) -> None:
        if user_id in self._user_settings:
            self._user_settings[user_id].pop(key, None)

    def set_active_env(self, env_slug: str | None) -> None:
        self._active_env = env_slug

    def get_active_env(self) -> str | None:
        return self._active_env

    def set_env_overrides(self, env_slug: str, overrides: dict[str, Any]) -> None:
        self._env_overrides[env_slug] = overrides

    def list_all(self, user_id: str | None = None) -> dict[str, dict[str, Any]]:
        """Return all settings with resolved values and source."""
        result = {}
        for key in DEFAULTS:
            value, source = self.get_with_source(key, user_id)
            result[key] = {"value": value, "source": source}
        return result
