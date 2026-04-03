"""Tests for Research schemas."""

import pytest
from pydantic import ValidationError

from gandra_tools.tools.research.schemas import (
    AnalysisDepth,
    AnalysisFocus,
    CredibilityReport,
    FactCheck,
    NarrativePerspective,
    ResearchAnalysisInput,
    SourceAnalysis,
)


def test_valid_input():
    inp = ResearchAnalysisInput(links=["https://example.com/article1", "https://example.com/article2"])
    assert len(inp.links) == 2
    assert inp.depth == AnalysisDepth.MEDIUM
    assert inp.language == "sr"


def test_empty_links_rejected():
    with pytest.raises(ValidationError):
        ResearchAnalysisInput(links=[])


def test_too_many_links_rejected():
    urls = [f"https://example.com/{i}" for i in range(51)]
    with pytest.raises(ValidationError):
        ResearchAnalysisInput(links=urls)


def test_defaults():
    inp = ResearchAnalysisInput(links=["https://example.com"])
    assert inp.depth == AnalysisDepth.MEDIUM
    assert inp.focus == [AnalysisFocus.ALL]
    assert inp.output_dir == "gandra-output/research/"
    assert inp.max_tokens_per_source == 4000


def test_all_depth_values():
    for d in AnalysisDepth:
        inp = ResearchAnalysisInput(links=["https://x.com"], depth=d)
        assert inp.depth == d


def test_all_focus_values():
    for f in AnalysisFocus:
        inp = ResearchAnalysisInput(links=["https://x.com"], focus=[f])
        assert f in inp.focus


def test_source_analysis_model():
    sa = SourceAnalysis(url="https://x.com", title="Test", summary="A summary")
    assert sa.tone == "neutral"
    assert sa.reliability_score == 0.5


def test_narrative_perspective():
    np_ = NarrativePerspective(label="Side A", description="Pro argument")
    assert np_.label == "Side A"
    assert np_.arguments == []


def test_credibility_report():
    cr = CredibilityReport(
        overall_score=0.7,
        verifiable_facts=[FactCheck(claim="X is true", verdict="confirmed", evidence="Source Y")],
    )
    assert cr.overall_score == 0.7
    assert len(cr.verifiable_facts) == 1


def test_fact_check():
    fc = FactCheck(claim="Earth is round", verdict="confirmed")
    assert fc.verdict == "confirmed"
