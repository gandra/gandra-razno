"""RAG Research schemas."""

from enum import Enum

from pydantic import BaseModel, Field

from gandra_tools.models.schemas import ToolInputBase

DEFAULT_OUTPUT_DIR = "gandra-output/research/"


class AnalysisDepth(str, Enum):
    SHALLOW = "shallow"
    MEDIUM = "medium"
    DEEP = "deep"


class AnalysisFocus(str, Enum):
    ALL = "all"
    CREDIBILITY = "credibility"
    NARRATIVE = "narrative"
    SUMMARY = "summary"
    FACT_CHECK = "fact_check"
    SENTIMENT = "sentiment"


class LinkAnnotation(BaseModel):
    """Optional annotation for a specific link."""

    url: str
    note: str | None = None
    key_quotes: list[str] | None = None


class ResearchAnalysisInput(ToolInputBase):
    """Input for RAG analysis of articles/news."""

    links: list[str] = Field(..., min_length=1, max_length=50)
    annotations: list[LinkAnnotation] | None = None
    depth: AnalysisDepth = AnalysisDepth.MEDIUM
    focus: list[AnalysisFocus] = Field(default=[AnalysisFocus.ALL])
    language: str = "sr"
    output_dir: str = Field(default=DEFAULT_OUTPUT_DIR)
    file_name: str | None = None
    max_tokens_per_source: int = Field(default=4000, le=16000)


class SourceAnalysis(BaseModel):
    """Analysis of a single source."""

    url: str
    title: str
    summary: str
    bias_indicators: list[str] = Field(default_factory=list)
    tone: str = "neutral"
    reliability_score: float = Field(default=0.5, ge=0.0, le=1.0)
    key_claims: list[str] = Field(default_factory=list)


class NarrativePerspective(BaseModel):
    """A narrative perspective identified across sources."""

    label: str
    description: str
    arguments: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    supporting_sources: list[str] = Field(default_factory=list)


class FactCheck(BaseModel):
    """A fact-check result for a specific claim."""

    claim: str
    verdict: str  # confirmed, unconfirmed, disputed, false
    evidence: str = ""


class CredibilityReport(BaseModel):
    """Credibility assessment across sources."""

    overall_score: float = Field(ge=0.0, le=1.0)
    per_source_scores: dict[str, float] = Field(default_factory=dict)
    extremes: list[str] = Field(default_factory=list)
    verifiable_facts: list[FactCheck] = Field(default_factory=list)


class ResearchAnalysisOutput(BaseModel):
    """Structured output of RAG analysis."""

    executive_summary: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    sources_analyzed: int
    detailed_analysis: list[SourceAnalysis] = Field(default_factory=list)
    narrative_perspectives: list[NarrativePerspective] | None = None
    credibility_assessment: CredibilityReport | None = None
    conclusion: str = ""
    recommendations: list[str] = Field(default_factory=list)
    file_path: str | None = None
    metadata: dict = Field(default_factory=dict)
