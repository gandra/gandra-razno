"""DevTools service — API testing and code review."""

import logging
import time
from datetime import date
from pathlib import Path

import httpx

from gandra_tools.core.config import get_settings
from gandra_tools.core.llm import LLMFactory
from gandra_tools.core.publisher import PublisherService
from gandra_tools.core.publisher.schemas import PublishRequest
from gandra_tools.tools.devtools.schemas import (
    ApiTestInput,
    ApiTestOutput,
    ApiTestResult,
    CodeReviewFinding,
    CodeReviewInput,
    CodeReviewOutput,
)

logger = logging.getLogger(__name__)


class ApiTestService:
    """Test HTTP API endpoints."""

    async def test(self, input_data: ApiTestInput) -> ApiTestOutput:
        results: list[ApiTestResult] = []

        for _ in range(input_data.repeat):
            result = await self._single_request(input_data)
            results.append(result)

        avg_time = sum(r.response_time_ms for r in results) / max(len(results), 1)
        all_passed = all(r.success for r in results)

        return ApiTestOutput(
            method=input_data.method.value,
            url=input_data.url,
            repeat_count=input_data.repeat,
            results=results,
            avg_response_time_ms=round(avg_time, 1),
            all_passed=all_passed,
            expected_status=input_data.expected_status,
        )

    async def _single_request(self, input_data: ApiTestInput) -> ApiTestResult:
        headers = input_data.headers or {}
        body = input_data.body

        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=input_data.timeout_seconds) as client:
                if isinstance(body, dict):
                    resp = await client.request(
                        input_data.method.value, input_data.url, headers=headers, json=body
                    )
                elif isinstance(body, str):
                    resp = await client.request(
                        input_data.method.value, input_data.url, headers=headers, content=body
                    )
                else:
                    resp = await client.request(
                        input_data.method.value, input_data.url, headers=headers
                    )
        except httpx.TimeoutException:
            elapsed = int((time.time() - start) * 1000)
            return ApiTestResult(
                status_code=0,
                response_time_ms=elapsed,
                headers={},
                body_preview="[TIMEOUT]",
                body_size_bytes=0,
                success=False,
            )
        except httpx.ConnectError as e:
            elapsed = int((time.time() - start) * 1000)
            return ApiTestResult(
                status_code=0,
                response_time_ms=elapsed,
                headers={},
                body_preview=f"[CONNECTION ERROR: {e}]",
                body_size_bytes=0,
                success=False,
            )

        elapsed = int((time.time() - start) * 1000)
        body_text = resp.text[:500]
        resp_headers = dict(resp.headers)

        success = True
        if input_data.expected_status is not None:
            success = resp.status_code == input_data.expected_status

        return ApiTestResult(
            status_code=resp.status_code,
            response_time_ms=elapsed,
            headers=resp_headers,
            body_preview=body_text,
            body_size_bytes=len(resp.content),
            success=success,
        )


class CodeReviewService:
    """AI-powered code review."""

    def __init__(self) -> None:
        self.publisher = PublisherService()

    async def review(self, input_data: CodeReviewInput) -> CodeReviewOutput:
        settings = get_settings()
        path = Path(input_data.path)

        if not path.exists():
            raise ValueError(f"Path does not exist: {input_data.path}")

        # Collect files
        files = self._collect_files(path, input_data)
        if not files:
            return CodeReviewOutput(
                files_reviewed=0, total_findings=0, findings=[], summary="No files found to review."
            )

        # Build code context
        code_context = self._build_context(files, input_data)

        # Get LLM review
        llm = LLMFactory.get_client(
            provider=input_data.llm_provider,
            model=input_data.llm_model,
            api_key=input_data.llm_api_key,
            settings=settings,
        )

        focus_str = ", ".join(input_data.focus)
        prompt = (
            f"Review this code for: {focus_str}.\n"
            f"For each finding, provide JSON array with objects: "
            f'file, line (int or null), severity (info/warning/error/critical), '
            f'category ({focus_str}), message, suggestion.\n'
            f"Also provide a summary field.\n"
            f"Respond as JSON: {{\"findings\": [...], \"summary\": \"...\"}}\n\n"
            f"{code_context}"
        )

        try:
            resp = await llm.chat([{"role": "user", "content": prompt}])
            from gandra_tools.tools.research.service import ResearchService

            data = ResearchService._parse_json_response(resp.content)
            findings = [CodeReviewFinding(**f) for f in data.get("findings", [])]
            summary = data.get("summary", f"Reviewed {len(files)} file(s).")
        except Exception as e:
            logger.warning("Code review LLM call failed: %s", e)
            findings = []
            summary = f"Review failed: {e}"

        output = CodeReviewOutput(
            files_reviewed=len(files),
            total_findings=len(findings),
            findings=findings,
            summary=summary,
        )

        # Publish report
        output_dir = "gandra-output/devtools/"
        file_name = f"code-review_{date.today():%Y%m%d}"
        output_path = Path(output_dir) / f"{file_name}.{input_data.output_format.value}"
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        pub_content = {
            "summary": summary,
            "files_reviewed": len(files),
            "total_findings": len(findings),
            "findings": [f.model_dump() for f in findings],
        }
        pub_resp = self.publisher.publish(
            PublishRequest(
                content=pub_content,
                content_type="code_review",
                format=input_data.output_format,
                output_path=str(output_path),
                metadata={"title": f"Code Review: {path.name}"},
            )
        )
        output.file_path = pub_resp.file_path
        return output

    def _collect_files(self, path: Path, input_data: CodeReviewInput) -> list[Path]:
        import fnmatch

        if path.is_file():
            return [path]

        files = []
        for f in sorted(path.rglob("*")):
            if not f.is_file():
                continue
            if any(fnmatch.fnmatch(str(f), pat) for pat in input_data.ignore_patterns):
                continue
            if any(part.startswith(".") for part in f.parts):
                continue
            # Only text files
            if f.suffix in (".py", ".js", ".ts", ".java", ".go", ".rs", ".rb", ".vue", ".jsx", ".tsx", ".sh", ".yaml", ".yml", ".toml", ".json", ".sql", ".md"):
                files.append(f)
            if len(files) >= input_data.max_files:
                break
        return files

    def _build_context(self, files: list[Path], input_data: CodeReviewInput) -> str:
        parts = []
        for f in files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                lang = input_data.language or f.suffix.lstrip(".")
                parts.append(f"--- {f} ({lang}) ---\n{content[:3000]}\n")
            except Exception:
                continue
        return "\n".join(parts)
