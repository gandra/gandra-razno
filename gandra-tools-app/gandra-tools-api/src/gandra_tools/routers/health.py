"""Health check endpoint."""

from fastapi import APIRouter

from gandra_tools.core.plugin import registry

router = APIRouter(tags=["health"])


@router.get("/api/v1/health")
async def health():
    return {"status": "ok", "service": "gandra-tools-api"}


@router.get("/api/v1/tools")
async def list_tools():
    return {"tools": registry.list_tools()}
