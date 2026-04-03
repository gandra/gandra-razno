"""YouTube transcript extraction service."""

import re
from pathlib import Path

from gandra_tools.core.publisher import PublisherService
from gandra_tools.core.publisher.schemas import PublishRequest
from gandra_tools.tools.youtube.schemas import (
    TranscriptInput,
    TranscriptOutput,
    TranscriptSegment,
)


def _format_time(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL."""
    patterns = [
        r"(?:v=|/v/)([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from: {url}")


def _merge_segments(
    raw_segments: list[dict], interval_minutes: int, merge_short: bool
) -> list[TranscriptSegment]:
    """Group raw transcript segments by time intervals."""
    if not raw_segments:
        return []

    interval_seconds = interval_minutes * 60
    groups: list[TranscriptSegment] = []
    current_texts: list[str] = []
    current_start = 0.0
    current_end = 0.0
    group_boundary = interval_seconds

    for seg in raw_segments:
        start = seg.get("start", 0.0)
        duration = seg.get("duration", 0.0)
        text = seg.get("text", "").strip()

        if not text:
            continue

        if start >= group_boundary and current_texts:
            groups.append(
                TranscriptSegment(
                    start_time=current_start,
                    end_time=current_end,
                    start_formatted=_format_time(current_start),
                    end_formatted=_format_time(current_end),
                    text=" ".join(current_texts),
                )
            )
            current_texts = []
            current_start = start
            group_boundary = start + interval_seconds

        if not current_texts:
            current_start = start

        current_texts.append(text)
        current_end = start + duration

    # Last group
    if current_texts:
        groups.append(
            TranscriptSegment(
                start_time=current_start,
                end_time=current_end,
                start_formatted=_format_time(current_start),
                end_formatted=_format_time(current_end),
                text=" ".join(current_texts),
            )
        )

    return groups


class YouTubeTranscriptService:
    """Extract transcripts from YouTube videos."""

    def __init__(self) -> None:
        self.publisher = PublisherService()

    def extract(self, input_data: TranscriptInput) -> TranscriptOutput:
        """Extract transcript from YouTube video."""
        from youtube_transcript_api import YouTubeTranscriptApi

        video_id = _extract_video_id(input_data.url)

        # Fetch transcript
        if input_data.language == "auto":
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            try:
                transcript = transcript_list.find_manually_created_transcript(
                    ["sr", "en", "de", "fr", "es"]
                )
            except Exception:
                transcript = transcript_list.find_generated_transcript(
                    ["sr", "en", "de", "fr", "es"]
                )
            raw_segments = transcript.fetch()
            language = transcript.language_code
        else:
            raw_segments = YouTubeTranscriptApi.get_transcript(
                video_id, languages=[input_data.language]
            )
            language = input_data.language

        # Get video title via yt-dlp (optional, fallback to video_id)
        video_title = self._get_video_title(input_data.url, video_id)

        # Merge segments by interval
        segments = _merge_segments(
            raw_segments, input_data.interval_minutes, input_data.merge_short_segments
        )

        full_text = "\n\n".join(seg.text for seg in segments)
        total_duration = raw_segments[-1]["start"] + raw_segments[-1].get("duration", 0) if raw_segments else 0
        word_count = sum(len(seg.text.split()) for seg in segments)

        output = TranscriptOutput(
            video_title=video_title,
            video_url=input_data.url,
            video_duration_seconds=int(total_duration),
            duration_formatted=_format_time(total_duration),
            language=language,
            segment_count=len(segments),
            word_count=word_count,
            segments=segments,
            full_text=full_text,
            metadata={"video_id": video_id, "interval_minutes": input_data.interval_minutes},
        )

        # Publish to file if output configured
        output_path = input_data.get_full_output_path(video_title)
        Path(output_path.parent).mkdir(parents=True, exist_ok=True)

        pub_content = self._build_publish_content(output, input_data.include_timestamps)
        pub_resp = self.publisher.publish(
            PublishRequest(
                content=pub_content,
                content_type="youtube_transcript",
                format=input_data.output_format,
                output_path=str(output_path),
                metadata={"title": video_title, "video_id": video_id},
            )
        )
        output.file_path = pub_resp.file_path
        return output

    def _get_video_title(self, url: str, fallback_id: str) -> str:
        try:
            import yt_dlp

            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True}) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get("title", fallback_id)
        except Exception:
            return fallback_id

    @staticmethod
    def _build_publish_content(output: TranscriptOutput, include_timestamps: bool) -> dict:
        if include_timestamps:
            segments_text = []
            for seg in output.segments:
                segments_text.append(f"[{seg.start_formatted} - {seg.end_formatted}]\n{seg.text}")
            transcript_body = "\n\n".join(segments_text)
        else:
            transcript_body = output.full_text

        return {
            "title": output.video_title,
            "url": output.video_url,
            "duration": output.duration_formatted,
            "language": output.language,
            "segments": f"{output.segment_count} segments, {output.word_count} words",
            "transcript": transcript_body,
        }
