"""Publisher service — orchestrates formatting and file output."""

from pathlib import Path

from gandra_tools.core.publisher.formatters.base import BaseFormatter
from gandra_tools.core.publisher.formatters.html_formatter import HtmlFormatter
from gandra_tools.core.publisher.formatters.json_formatter import JsonFormatter
from gandra_tools.core.publisher.formatters.markdown_formatter import MarkdownFormatter
from gandra_tools.core.publisher.formatters.social_formatter import (
    FacebookFormatter,
    InstagramFormatter,
    LinkedInFormatter,
    XFormatter,
)
from gandra_tools.core.publisher.formatters.text_formatter import TextFormatter
from gandra_tools.core.publisher.schemas import PublishRequest, PublishResponse
from gandra_tools.models.schemas import OutputFormat

_FORMATTERS: dict[OutputFormat, BaseFormatter] = {}


def _get_formatters() -> dict[OutputFormat, BaseFormatter]:
    global _FORMATTERS
    if not _FORMATTERS:
        _FORMATTERS = {
            OutputFormat.JSON: JsonFormatter(),
            OutputFormat.MARKDOWN: MarkdownFormatter(),
            OutputFormat.TEXT: TextFormatter(),
            OutputFormat.HTML: HtmlFormatter(),
            OutputFormat.FACEBOOK: FacebookFormatter(),
            OutputFormat.LINKEDIN: LinkedInFormatter(),
            OutputFormat.INSTAGRAM: InstagramFormatter(),
            OutputFormat.X: XFormatter(),
        }
    return _FORMATTERS


class PublisherService:
    """Publishes structured content in various formats."""

    def publish(self, request: PublishRequest) -> PublishResponse:
        formatters = _get_formatters()
        formatter = formatters.get(request.format)
        if formatter is None:
            raise ValueError(f"Unsupported format: {request.format}")

        options = request.options or {}
        if request.template:
            options["template"] = request.template

        rendered = formatter.render(
            content=request.content,
            content_type=request.content_type,
            metadata=request.metadata,
            **options,
        )

        file_path = None
        if request.output_path:
            path = Path(request.output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered, encoding="utf-8")
            file_path = str(path)

        return PublishResponse(
            format=request.format,
            content=rendered,
            file_path=file_path,
            size_bytes=len(rendered.encode("utf-8")),
            content_type_mime=formatter.mime_type,
        )

    def publish_multi(
        self, content: dict, content_type: str, formats: list[OutputFormat], metadata: dict | None = None
    ) -> list[PublishResponse]:
        results = []
        for fmt in formats:
            resp = self.publish(
                PublishRequest(
                    content=content,
                    content_type=content_type,
                    format=fmt,
                    metadata=metadata,
                )
            )
            results.append(resp)
        return results

    @staticmethod
    def get_supported_formats() -> list[str]:
        return [f.value for f in OutputFormat]
