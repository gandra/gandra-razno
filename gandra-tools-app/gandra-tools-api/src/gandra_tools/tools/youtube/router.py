"""YouTube API endpoints."""

from fastapi import APIRouter, Depends

from gandra_tools.core.auth import require_auth
from gandra_tools.tools.youtube.schemas import TranscriptInput, TranscriptOutput
from gandra_tools.tools.youtube.service import YouTubeTranscriptService

router = APIRouter(prefix="/api/v1/youtube", tags=["youtube"])

_service = YouTubeTranscriptService()


@router.post("/transcript", response_model=TranscriptOutput, dependencies=[Depends(require_auth)])
async def extract_transcript(input_data: TranscriptInput):
    return _service.extract(input_data)
