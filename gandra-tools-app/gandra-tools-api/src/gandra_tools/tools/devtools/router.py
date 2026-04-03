"""DevTools API endpoints."""

from fastapi import APIRouter, Depends

from gandra_tools.core.auth import require_auth
from gandra_tools.tools.devtools.schemas import (
    ApiTestInput,
    ApiTestOutput,
    CodeReviewInput,
    CodeReviewOutput,
)
from gandra_tools.tools.devtools.service import ApiTestService, CodeReviewService

router = APIRouter(prefix="/api/v1/devtools", tags=["devtools"])

_api_test_service = ApiTestService()
_code_review_service = CodeReviewService()


@router.post("/api-test", response_model=ApiTestOutput, dependencies=[Depends(require_auth)])
async def api_test(input_data: ApiTestInput):
    return await _api_test_service.test(input_data)


@router.post("/code-review", response_model=CodeReviewOutput, dependencies=[Depends(require_auth)])
async def code_review(input_data: CodeReviewInput):
    return await _code_review_service.review(input_data)
