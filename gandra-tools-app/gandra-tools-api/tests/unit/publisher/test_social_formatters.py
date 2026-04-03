"""Tests for social media formatters."""

from gandra_tools.core.publisher.formatters.social_formatter import (
    FacebookFormatter,
    InstagramFormatter,
    LinkedInFormatter,
    XFormatter,
)


SAMPLE_CONTENT = {
    "title": "AI u Srbiji 2026",
    "summary": "Analiza pokazuje rast upotrebe AI alata u srpskim kompanijama.",
    "key_claims": ["Rast od 40%", "Najpopularniji OpenAI", "Ollama za privatnost"],
}


# ── Facebook ─────────────────────────────────────────────────

def test_facebook_includes_title():
    f = FacebookFormatter()
    result = f.render(SAMPLE_CONTENT, "research_analysis")
    assert "AI u Srbiji 2026" in result


def test_facebook_max_length():
    f = FacebookFormatter()
    long_content = {"summary": "x" * 70000}
    result = f.render(long_content, "generic")
    assert len(result) <= 63206


def test_facebook_hashtags():
    f = FacebookFormatter()
    result = f.render(SAMPLE_CONTENT, "generic", hashtags=["AI", "Serbia"])
    assert "#AI" in result
    assert "#Serbia" in result


# ── LinkedIn ─────────────────────────────────────────────────

def test_linkedin_bullet_points():
    f = LinkedInFormatter()
    result = f.render(SAMPLE_CONTENT, "research_analysis")
    assert "→" in result
    assert "Rast od 40%" in result


def test_linkedin_max_length():
    f = LinkedInFormatter()
    long_content = {"summary": "x" * 5000}
    result = f.render(long_content, "generic")
    assert len(result) <= 3000


# ── Instagram ────────────────────────────────────────────────

def test_instagram_has_emoji():
    f = InstagramFormatter()
    result = f.render(SAMPLE_CONTENT, "generic")
    assert "✨" in result


def test_instagram_max_length():
    f = InstagramFormatter()
    long_content = {"summary": "x" * 5000}
    result = f.render(long_content, "generic")
    assert len(result) <= 2200


def test_instagram_hashtags_max_30():
    f = InstagramFormatter()
    tags = [f"tag{i}" for i in range(50)]
    result = f.render(SAMPLE_CONTENT, "generic", hashtags=tags)
    assert result.count("#") <= 30


# ── X (Twitter) ──────────────────────────────────────────────

def test_x_thread_format():
    f = XFormatter()
    long_content = {"summary": " ".join(["word"] * 200)}
    result = f.render(long_content, "generic")
    assert "---" in result  # Thread separator
    assert "(1/" in result  # Numbered


def test_x_single_tweet_no_numbering():
    f = XFormatter()
    result = f.render({"summary": "Short tweet"}, "generic")
    assert "(1/" not in result


def test_x_max_tweet_length():
    f = XFormatter()
    long_content = {"title": "Test", "summary": " ".join(["word"] * 200)}
    result = f.render(long_content, "generic")
    tweets = result.split("\n\n---\n\n")
    for tweet in tweets:
        assert len(tweet) <= 280
