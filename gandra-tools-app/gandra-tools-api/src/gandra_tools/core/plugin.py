"""Plugin registry — autodiscovery of tools."""

import importlib
import pkgutil
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolMeta:
    name: str
    display_name: str
    category: str
    description: str
    version: str = "1.0.0"
    tools: list[dict[str, str]] = field(default_factory=list)


class PluginRegistry:
    """Discovers and registers tool plugins from tools/ package."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolMeta] = {}
        self._routers: list[Any] = []

    @property
    def tools(self) -> dict[str, ToolMeta]:
        return dict(self._tools)

    @property
    def routers(self) -> list[Any]:
        return list(self._routers)

    def register(self, meta: ToolMeta, router: Any | None = None) -> None:
        self._tools[meta.name] = meta
        if router is not None:
            self._routers.append(router)

    def discover(self, package_name: str = "gandra_tools.tools") -> None:
        """Scan tools/ subpackages for TOOL_META and router."""
        try:
            package = importlib.import_module(package_name)
        except ImportError:
            return

        if not hasattr(package, "__path__"):
            return

        for _importer, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
            if not is_pkg:
                continue

            full_name = f"{package_name}.{module_name}"
            try:
                mod = importlib.import_module(full_name)
            except ImportError:
                continue

            tool_meta_dict = getattr(mod, "TOOL_META", None)
            if tool_meta_dict is None:
                continue

            meta = ToolMeta(**tool_meta_dict)

            router = None
            try:
                router_mod = importlib.import_module(f"{full_name}.router")
                router = getattr(router_mod, "router", None)
            except ImportError:
                pass

            self.register(meta, router)

    def list_tools(self) -> list[dict]:
        return [
            {
                "name": m.name,
                "display_name": m.display_name,
                "category": m.category,
                "description": m.description,
                "version": m.version,
                "tools": m.tools,
            }
            for m in self._tools.values()
        ]


registry = PluginRegistry()
