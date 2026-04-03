"""RAG Research service — web scraping + multi-pass LLM analysis."""

import json
import logging
from datetime import date
from pathlib import Path

from gandra_tools.core.config import get_settings
from gandra_tools.core.llm import LLMFactory, LLMResponse
from gandra_tools.core.publisher import PublisherService
from gandra_tools.core.publisher.schemas import PublishRequest
from gandra_tools.tools.research.schemas import (
    AnalysisDepth,
    AnalysisFocus,
    CredibilityReport,
    FactCheck,
    NarrativePerspective,
    ResearchAnalysisInput,
    ResearchAnalysisOutput,
    SourceAnalysis,
)

logger = logging.getLogger(__name__)


async def scrape_url(url: str, max_chars: int = 8000) -> dict:
    """Scrape content from a URL. Returns {url, title, text}."""
    import httpx

    try:
        try:
            from trafilatura import extract, fetch_url

            downloaded = fetch_url(url)
            if downloaded:
                text = extract(downloaded, include_comments=False, include_tables=True) or ""
                title = extract(downloaded, output_format="xmltei") or ""
                # Extract title from TEI if available
                import re

                title_match = re.search(r"<title[^>]*>(.*?)</title>", title)
                title = title_match.group(1) if title_match else url
                return {"url": url, "title": title, "text": text[:max_chars]}
        except ImportError:
            pass

        # Fallback: raw httpx + basic text extraction
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text

        from html.parser import HTMLParser

        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.texts = []
                self._skip = False

            def handle_starttag(self, tag, attrs):
                if tag in ("script", "style", "nav", "footer", "header"):
                    self._skip = True

            def handle_endtag(self, tag):
                if tag in ("script", "style", "nav", "footer", "header"):
                    self._skip = False

            def handle_data(self, data):
                if not self._skip:
                    text = data.strip()
                    if text:
                        self.texts.append(text)

        parser = TextExtractor()
        parser.feed(html)
        text = " ".join(parser.texts)

        # Extract title
        import re

        title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE)
        title = title_match.group(1) if title_match else url

        return {"url": url, "title": title, "text": text[:max_chars]}

    except Exception as e:
        logger.warning("Failed to scrape %s: %s", url, e)
        return {"url": url, "title": url, "text": f"[Failed to fetch: {e}]"}


class ResearchService:
    """Multi-link RAG analysis with multi-pass LLM processing."""

    def __init__(self) -> None:
        self.publisher = PublisherService()

    async def analyze(self, input_data: ResearchAnalysisInput) -> ResearchAnalysisOutput:
        """Run full analysis pipeline."""
        settings = get_settings()

        # 1. Scrape all links
        scraped = []
        for link in input_data.links:
            result = await scrape_url(link, input_data.max_tokens_per_source)
            scraped.append(result)

        # 2. Get LLM client
        llm = LLMFactory.get_client(
            provider=input_data.llm_provider,
            model=input_data.llm_model,
            api_key=input_data.llm_api_key,
            settings=settings,
        )

        # 3. Multi-pass analysis
        source_analyses = await self._pass1_summarize(llm, scraped, input_data)
        executive_summary, conclusion, recommendations = await self._pass2_synthesize(
            llm, source_analyses, input_data
        )

        narratives = None
        credibility = None

        if input_data.depth in (AnalysisDepth.MEDIUM, AnalysisDepth.DEEP):
            if AnalysisFocus.ALL in input_data.focus or AnalysisFocus.NARRATIVE in input_data.focus:
                narratives = await self._pass3_narratives(llm, source_analyses, input_data)

        if input_data.depth == AnalysisDepth.DEEP:
            if AnalysisFocus.ALL in input_data.focus or AnalysisFocus.CREDIBILITY in input_data.focus:
                credibility = await self._pass4_credibility(llm, source_analyses, input_data)

        confidence = sum(s.reliability_score for s in source_analyses) / max(len(source_analyses), 1)

        output = ResearchAnalysisOutput(
            executive_summary=executive_summary,
            confidence_score=round(confidence, 2),
            sources_analyzed=len(scraped),
            detailed_analysis=source_analyses,
            narrative_perspectives=narratives,
            credibility_assessment=credibility,
            conclusion=conclusion,
            recommendations=recommendations,
            metadata={"depth": input_data.depth.value, "focus": [f.value for f in input_data.focus]},
        )

        # Publish
        file_name = input_data.file_name or f"analysis_{date.today():%Y%m%d}"
        output_path = Path(input_data.output_dir) / f"{file_name}.{input_data.output_format.value}"
        Path(output_path.parent).mkdir(parents=True, exist_ok=True)

        pub_content = {
            "executive_summary": output.executive_summary,
            "sources_analyzed": output.sources_analyzed,
            "confidence_score": output.confidence_score,
            "detailed_analysis": [s.model_dump() for s in source_analyses],
            "conclusion": output.conclusion,
            "recommendations": output.recommendations,
        }
        if narratives:
            pub_content["narrative_perspectives"] = [n.model_dump() for n in narratives]
        if credibility:
            pub_content["credibility_assessment"] = credibility.model_dump()

        pub_resp = self.publisher.publish(
            PublishRequest(
                content=pub_content,
                content_type="research_analysis",
                format=input_data.output_format,
                output_path=str(output_path),
                metadata={"title": f"Analysis: {len(input_data.links)} sources"},
            )
        )
        output.file_path = pub_resp.file_path
        return output

    async def _pass1_summarize(
        self, llm, scraped: list[dict], input_data: ResearchAnalysisInput
    ) -> list[SourceAnalysis]:
        """Pass 1: Summarize each source individually."""
        results = []
        for source in scraped:
            annotations = ""
            if input_data.annotations:
                for ann in input_data.annotations:
                    if ann.url == source["url"]:
                        annotations = f"\nUser notes: {ann.note or ''}"
                        if ann.key_quotes:
                            annotations += f"\nKey quotes: {', '.join(ann.key_quotes)}"

            prompt = (
                f"Analyze this article. Respond in JSON with fields: "
                f"summary, bias_indicators (list), tone (neutral/positive/negative/sensational), "
                f"reliability_score (0-1), key_claims (list).\n\n"
                f"Title: {source['title']}\nURL: {source['url']}\n"
                f"Content:\n{source['text'][:input_data.max_tokens_per_source]}"
                f"{annotations}"
            )

            try:
                resp = await llm.chat([{"role": "user", "content": prompt}])
                data = self._parse_json_response(resp.content)
                results.append(
                    SourceAnalysis(
                        url=source["url"],
                        title=source["title"],
                        summary=data.get("summary", source["text"][:200]),
                        bias_indicators=data.get("bias_indicators", []),
                        tone=data.get("tone", "neutral"),
                        reliability_score=min(1.0, max(0.0, float(data.get("reliability_score", 0.5)))),
                        key_claims=data.get("key_claims", []),
                    )
                )
            except Exception as e:
                logger.warning("Pass 1 failed for %s: %s", source["url"], e)
                results.append(
                    SourceAnalysis(url=source["url"], title=source["title"], summary=source["text"][:200])
                )
        return results

    async def _pass2_synthesize(
        self, llm, analyses: list[SourceAnalysis], input_data: ResearchAnalysisInput
    ) -> tuple[str, str, list[str]]:
        """Pass 2: Cross-source synthesis."""
        summaries = "\n\n".join(
            f"Source: {a.url}\nSummary: {a.summary}\nClaims: {', '.join(a.key_claims)}"
            for a in analyses
        )
        lang = "Serbian" if input_data.language == "sr" else "English"
        prompt = (
            f"Based on these {len(analyses)} source summaries, provide in {lang}:\n"
            f"1. executive_summary (3-5 sentences)\n"
            f"2. conclusion (2-3 sentences)\n"
            f"3. recommendations (list of 3-5 items)\n"
            f"Respond in JSON.\n\n{summaries}"
        )

        try:
            resp = await llm.chat([{"role": "user", "content": prompt}])
            data = self._parse_json_response(resp.content)
            return (
                data.get("executive_summary", "Analysis complete."),
                data.get("conclusion", ""),
                data.get("recommendations", []),
            )
        except Exception:
            return ("Analysis of provided sources.", "", [])

    async def _pass3_narratives(
        self, llm, analyses: list[SourceAnalysis], input_data: ResearchAnalysisInput
    ) -> list[NarrativePerspective]:
        """Pass 3: Identify narrative perspectives."""
        summaries = "\n".join(f"- {a.url}: {a.summary} (tone: {a.tone})" for a in analyses)
        lang = "Serbian" if input_data.language == "sr" else "English"
        prompt = (
            f"Identify 2-4 distinct narrative perspectives from these sources in {lang}. "
            f"For each: label, description, arguments, weaknesses, supporting_sources (URLs).\n"
            f"Respond as JSON array.\n\n{summaries}"
        )

        try:
            resp = await llm.chat([{"role": "user", "content": prompt}])
            data = self._parse_json_response(resp.content)
            if isinstance(data, list):
                return [NarrativePerspective(**item) for item in data]
            return [NarrativePerspective(**item) for item in data.get("perspectives", data.get("narratives", []))]
        except Exception:
            return []

    async def _pass4_credibility(
        self, llm, analyses: list[SourceAnalysis], input_data: ResearchAnalysisInput
    ) -> CredibilityReport:
        """Pass 4: Credibility and fact-checking."""
        claims = []
        for a in analyses:
            for claim in a.key_claims[:3]:
                claims.append(f"From {a.url}: {claim}")

        prompt = (
            f"Fact-check these claims. For each: claim, verdict (confirmed/unconfirmed/disputed/false), evidence.\n"
            f"Also provide overall_score (0-1) and list of extreme/outlier positions.\n"
            f"Respond in JSON.\n\n" + "\n".join(claims)
        )

        try:
            resp = await llm.chat([{"role": "user", "content": prompt}])
            data = self._parse_json_response(resp.content)
            facts = [FactCheck(**f) for f in data.get("verifiable_facts", data.get("fact_checks", []))]
            return CredibilityReport(
                overall_score=min(1.0, max(0.0, float(data.get("overall_score", 0.5)))),
                per_source_scores={a.url: a.reliability_score for a in analyses},
                extremes=data.get("extremes", []),
                verifiable_facts=facts,
            )
        except Exception:
            return CredibilityReport(
                overall_score=sum(a.reliability_score for a in analyses) / max(len(analyses), 1),
                per_source_scores={a.url: a.reliability_score for a in analyses},
            )

    @staticmethod
    def _parse_json_response(text: str) -> dict | list:
        """Extract JSON from LLM response (handles markdown code blocks)."""
        import re

        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting from code block
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try finding first { or [
        for i, c in enumerate(text):
            if c in ("{", "["):
                try:
                    return json.loads(text[i:])
                except json.JSONDecodeError:
                    pass

        return {}
