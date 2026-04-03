"""Tests for Plugin registry."""

from gandra_tools.core.plugin import PluginRegistry, ToolMeta


def test_register_tool():
    reg = PluginRegistry()
    meta = ToolMeta(
        name="test-tool",
        display_name="Test Tool",
        category="testing",
        description="A test tool",
    )
    reg.register(meta)
    assert "test-tool" in reg.tools
    assert reg.tools["test-tool"].category == "testing"


def test_register_with_router():
    reg = PluginRegistry()
    meta = ToolMeta(name="t", display_name="T", category="c", description="d")
    fake_router = object()
    reg.register(meta, router=fake_router)
    assert len(reg.routers) == 1


def test_list_tools():
    reg = PluginRegistry()
    reg.register(ToolMeta(name="a", display_name="A", category="cat", description="desc"))
    reg.register(ToolMeta(name="b", display_name="B", category="cat", description="desc"))
    tools = reg.list_tools()
    assert len(tools) == 2
    names = {t["name"] for t in tools}
    assert names == {"a", "b"}


def test_empty_registry():
    reg = PluginRegistry()
    assert reg.list_tools() == []
    assert reg.routers == []
