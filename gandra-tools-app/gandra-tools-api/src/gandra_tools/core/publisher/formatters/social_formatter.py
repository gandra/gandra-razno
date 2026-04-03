"""Social media formatters — Facebook, LinkedIn, Instagram, X (Twitter)."""

from gandra_tools.core.publisher.formatters.base import BaseFormatter
from gandra_tools.models.schemas import OutputFormat


def _extract_summary(content: dict) -> str:
    """Extract best summary text from content dict."""
    for key in ("executive_summary", "summary", "full_text", "text", "description"):
        if key in content and content[key]:
            return str(content[key])
    # Fallback: join all string values
    parts = [str(v) for v in content.values() if isinstance(v, str) and v]
    return " ".join(parts) if parts else str(content)


def _extract_title(content: dict, metadata: dict | None) -> str:
    if metadata and "title" in metadata:
        return metadata["title"]
    for key in ("title", "video_title", "name"):
        if key in content and content[key]:
            return str(content[key])
    return ""


def _truncate(text: str, max_len: int, suffix: str = "...") -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - len(suffix)] + suffix


class FacebookFormatter(BaseFormatter):
    format = OutputFormat.FACEBOOK
    mime_type = "text/plain"
    file_extension = ".facebook.txt"

    MAX_LENGTH = 63206

    def render(self, content: dict, content_type: str, metadata: dict | None = None, **options) -> str:
        title = _extract_title(content, metadata)
        summary = _extract_summary(content)
        hashtags = options.get("hashtags", [])

        lines = []
        if title:
            lines.append(f"📌 {title}")
            lines.append("")
        lines.append(summary)
        if hashtags:
            lines.append("")
            lines.append(" ".join(f"#{tag}" for tag in hashtags))

        result = "\n".join(lines)
        return _truncate(result, self.MAX_LENGTH)


class LinkedInFormatter(BaseFormatter):
    format = OutputFormat.LINKEDIN
    mime_type = "text/plain"
    file_extension = ".linkedin.txt"

    MAX_LENGTH = 3000

    def render(self, content: dict, content_type: str, metadata: dict | None = None, **options) -> str:
        title = _extract_title(content, metadata)
        summary = _extract_summary(content)
        hashtags = options.get("hashtags", [])

        lines = []
        if title:
            lines.append(title)
            lines.append("")

        # Bullet points from key findings if available
        key_items = content.get("key_claims") or content.get("recommendations") or []
        if key_items:
            lines.append("Key takeaways:")
            for item in key_items[:5]:
                lines.append(f"→ {item}")
            lines.append("")
        else:
            lines.append(summary)

        if hashtags:
            lines.append("")
            lines.append(" ".join(f"#{tag}" for tag in hashtags))

        result = "\n".join(lines)
        return _truncate(result, self.MAX_LENGTH)


class InstagramFormatter(BaseFormatter):
    format = OutputFormat.INSTAGRAM
    mime_type = "text/plain"
    file_extension = ".instagram.txt"

    MAX_LENGTH = 2200

    def render(self, content: dict, content_type: str, metadata: dict | None = None, **options) -> str:
        title = _extract_title(content, metadata)
        summary = _extract_summary(content)
        hashtags = options.get("hashtags", [])

        lines = []
        if title:
            lines.append(f"✨ {title}")
            lines.append("")
        lines.append(_truncate(summary, 1800))

        if hashtags:
            lines.append("")
            lines.append("·")
            lines.append(" ".join(f"#{tag}" for tag in hashtags[:30]))

        result = "\n".join(lines)
        return _truncate(result, self.MAX_LENGTH)


class XFormatter(BaseFormatter):
    """X (Twitter) formatter — thread format, 280 chars per tweet."""

    format = OutputFormat.X
    mime_type = "text/plain"
    file_extension = ".x.txt"

    TWEET_MAX = 280

    def render(self, content: dict, content_type: str, metadata: dict | None = None, **options) -> str:
        title = _extract_title(content, metadata)
        summary = _extract_summary(content)
        hashtags = options.get("hashtags", [])
        hashtag_str = " ".join(f"#{tag}" for tag in hashtags[:3]) if hashtags else ""

        # Build thread
        tweets = []

        # Tweet 1: title + hook
        tweet1 = f"🧵 {title}" if title else f"🧵 {_truncate(summary, 250)}"
        if hashtag_str:
            tweet1 = _truncate(tweet1, self.TWEET_MAX - len(hashtag_str) - 1)
            tweet1 = f"{tweet1} {hashtag_str}"
        tweets.append(_truncate(tweet1, self.TWEET_MAX))

        # Split remaining summary into tweet-sized chunks
        remaining = summary if title else summary[250:]
        words = remaining.split()
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip() if current else word
            if len(candidate) > self.TWEET_MAX - 6:  # Room for " (X/N)"
                if current:
                    tweets.append(current)
                current = word
            else:
                current = candidate
        if current:
            tweets.append(current)

        # Number the tweets
        total = len(tweets)
        if total > 1:
            numbered = []
            for i, tweet in enumerate(tweets, 1):
                suffix = f" ({i}/{total})"
                numbered.append(_truncate(tweet, self.TWEET_MAX - len(suffix)) + suffix)
            return "\n\n---\n\n".join(numbered)

        return tweets[0] if tweets else ""
