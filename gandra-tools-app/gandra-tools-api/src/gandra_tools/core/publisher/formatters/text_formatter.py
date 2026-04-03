"""Plain text output formatter."""

from gandra_tools.core.publisher.formatters.base import BaseFormatter
from gandra_tools.models.schemas import OutputFormat


class TextFormatter(BaseFormatter):
    format = OutputFormat.TEXT
    mime_type = "text/plain"
    file_extension = ".txt"

    def render(self, content: dict, content_type: str, metadata: dict | None = None, **options) -> str:
        lines = []
        if metadata:
            if "title" in metadata:
                lines.append(metadata["title"].upper())
                lines.append("=" * len(metadata["title"]))
                lines.append("")

        for key, value in content.items():
            if isinstance(value, list):
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
            elif isinstance(value, dict):
                lines.append(f"{key}:")
                for k, v in value.items():
                    lines.append(f"  {k}: {v}")
            else:
                lines.append(f"{key}: {value}")
            lines.append("")

        return "\n".join(lines).strip() + "\n"
