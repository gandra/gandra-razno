"""Research API endpoints."""

from fastapi import APIRouter, Depends

from gandra_tools.core.auth import require_auth
from gandra_tools.tools.research.schemas import ResearchAnalysisInput, ResearchAnalysisOutput
from gandra_tools.tools.research.service import ResearchService

router = APIRouter(prefix="/api/v1/research", tags=["research"])

_service = ResearchService()


@router.post("/analyze", response_model=ResearchAnalysisOutput, dependencies=[Depends(require_auth)])
async def analyze(input_data: ResearchAnalysisInput):
    return await _service.analyze(input_data)
