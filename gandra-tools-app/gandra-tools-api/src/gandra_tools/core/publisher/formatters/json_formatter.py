"""JSON output formatter."""

import json

from gandra_tools.core.publisher.formatters.base import BaseFormatter
from gandra_tools.models.schemas import OutputFormat


class JsonFormatter(BaseFormatter):
    format = OutputFormat.JSON
    mime_type = "application/json"
    file_extension = ".json"

    def render(self, content: dict, content_type: str, metadata: dict | None = None, **options) -> str:
        output = {"content_type": content_type, "data": content}
        if metadata:
            output["metadata"] = metadata
        indent = options.get("indent", 2)
        return json.dumps(output, ensure_ascii=False, indent=indent, default=str)
