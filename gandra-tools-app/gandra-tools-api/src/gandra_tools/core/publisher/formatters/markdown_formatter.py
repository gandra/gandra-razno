"""Markdown output formatter."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from gandra_tools.core.publisher.formatters.base import BaseFormatter
from gandra_tools.models.schemas import OutputFormat

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class MarkdownFormatter(BaseFormatter):
    format = OutputFormat.MARKDOWN
    mime_type = "text/markdown"
    file_extension = ".md"

    def __init__(self) -> None:
        self._jinja_env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape([]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, content: dict, content_type: str, metadata: dict | None = None, **options) -> str:
        template_name = options.get("template") or f"{content_type}.md.j2"
        try:
            template = self._jinja_env.get_template(template_name)
        except Exception:
            template = self._jinja_env.get_template("generic.md.j2")
        return template.render(content=content, metadata=metadata or {}, content_type=content_type)
