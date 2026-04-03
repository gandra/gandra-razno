"""ImageOps API endpoints."""

from fastapi import APIRouter, Depends

from gandra_tools.core.auth import require_auth
from gandra_tools.tools.imageops.schemas import ImageTextExtractInput, ImageTextExtractOutput
from gandra_tools.tools.imageops.service import ImageTextExtractService

router = APIRouter(prefix="/api/v1/imageops", tags=["imageops"])

_service = ImageTextExtractService()


@router.post(
    "/text-extract",
    response_model=ImageTextExtractOutput,
    dependencies=[Depends(require_auth)],
)
async def extract_text(input_data: ImageTextExtractInput):
    return _service.extract(input_data)
