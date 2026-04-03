"""HTML output formatter with inline CSS."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from gandra_tools.core.publisher.formatters.base import BaseFormatter
from gandra_tools.models.schemas import OutputFormat

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class HtmlFormatter(BaseFormatter):
    format = OutputFormat.HTML
    mime_type = "text/html"
    file_extension = ".html"

    def __init__(self) -> None:
        self._jinja_env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(["html"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, content: dict, content_type: str, metadata: dict | None = None, **options) -> str:
        template_name = options.get("template") or f"{content_type}.html.j2"
        try:
            template = self._jinja_env.get_template(template_name)
        except Exception:
            template = self._jinja_env.get_template("generic.html.j2")
        return template.render(content=content, metadata=metadata or {}, content_type=content_type)
