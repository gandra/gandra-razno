"""FileOps API endpoints."""

from fastapi import APIRouter, Depends

from gandra_tools.core.auth import require_auth
from gandra_tools.tools.fileops.schemas import (
    FileRenameInput,
    FileRenameOutput,
    FileSearchInput,
    FileSearchOutput,
)
from gandra_tools.tools.fileops.service import FileOpsService

router = APIRouter(prefix="/api/v1/fileops", tags=["fileops"])

_service = FileOpsService()


@router.post("/search", response_model=FileSearchOutput, dependencies=[Depends(require_auth)])
async def search_files(input_data: FileSearchInput):
    return _service.search(input_data)


@router.post("/rename", response_model=FileRenameOutput, dependencies=[Depends(require_auth)])
async def rename_files(input_data: FileRenameInput):
    return _service.rename(input_data)
