"""Global error handling for FastAPI."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ToolError(Exception):
    """Base exception for tool errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ToolNotFoundError(ToolError):
    def __init__(self, tool_name: str):
        super().__init__(f"Tool not found: {tool_name}", status_code=404)


class ProviderError(ToolError):
    def __init__(self, provider: str, detail: str):
        super().__init__(f"LLM provider '{provider}' error: {detail}", status_code=502)


def register_error_handlers(app: FastAPI) -> None:
    """Register global exception handlers."""

    @app.exception_handler(ToolError)
    async def tool_error_handler(request: Request, exc: ToolError):
        logger.warning("ToolError: %s (path=%s)", exc.message, request.url.path)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "type": type(exc).__name__},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        logger.warning("ValueError: %s (path=%s)", exc, request.url.path)
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc), "type": "ValueError"},
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        logger.error("Unhandled error: %s (path=%s)", exc, request.url.path, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "type": type(exc).__name__},
        )
