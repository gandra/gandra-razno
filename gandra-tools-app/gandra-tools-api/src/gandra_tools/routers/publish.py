"""Publish endpoints — format and export content."""

from fastapi import APIRouter, Depends

from gandra_tools.core.auth import require_auth
from gandra_tools.core.publisher.schemas import MultiPublishRequest, PublishRequest, PublishResponse
from gandra_tools.core.publisher.service import PublisherService

router = APIRouter(prefix="/api/v1/publish", tags=["publish"])

_publisher = PublisherService()


@router.post("", response_model=PublishResponse, dependencies=[Depends(require_auth)])
async def publish(request: PublishRequest):
    return _publisher.publish(request)


@router.post("/multi", response_model=list[PublishResponse], dependencies=[Depends(require_auth)])
async def publish_multi(request: MultiPublishRequest):
    return _publisher.publish_multi(
        content=request.content,
        content_type=request.content_type,
        formats=request.formats,
        metadata=request.metadata,
    )


@router.get("/formats")
async def list_formats():
    return {"formats": _publisher.get_supported_formats()}
