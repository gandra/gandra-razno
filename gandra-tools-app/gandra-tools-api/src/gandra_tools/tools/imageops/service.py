"""Image text extraction service — OCR + transparent PNG rendering."""

import time
from pathlib import Path

from gandra_tools.tools.imageops.schemas import (
    ImageExtractMode,
    ImageTextExtractInput,
    ImageTextExtractOutput,
    TextRegion,
)


def _detect_dominant_color(image, bbox: tuple[int, int, int, int]) -> str:
    """Detect dominant text color in a bounding box region."""
    try:
        from PIL import ImageStat

        x1, y1, x2, y2 = bbox
        region = image.crop((x1, y1, x2, y2))
        stat = ImageStat.Stat(region)
        # Use median as approximation of text color (darkest channel)
        r, g, b = [int(c) for c in stat.median[:3]]
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return "#000000"


def _parse_color(color_str: str) -> tuple[int, int, int]:
    """Parse color string to RGB tuple."""
    if color_str.startswith("#") and len(color_str) == 7:
        return (
            int(color_str[1:3], 16),
            int(color_str[3:5], 16),
            int(color_str[5:7], 16),
        )
    colors = {"black": (0, 0, 0), "white": (255, 255, 255), "red": (255, 0, 0)}
    return colors.get(color_str.lower(), (0, 0, 0))


class ImageTextExtractService:
    """Extract text from images and render on transparent background."""

    def extract(self, input_data: ImageTextExtractInput) -> ImageTextExtractOutput:
        from PIL import Image

        start = time.time()

        # Load image
        if input_data.image_path.startswith(("http://", "https://")):
            image = self._download_image(input_data.image_path)
        else:
            image = Image.open(input_data.image_path).convert("RGB")

        width, height = image.size

        # Detect text regions via OCR
        all_regions = self._ocr_detect(image, input_data.language)

        # Filter by confidence
        included = [r for r in all_regions if r.confidence >= input_data.min_confidence]

        # Detect colors if auto
        if input_data.font_color == "auto":
            for region in included:
                region.color_hex = _detect_dominant_color(image, region.bbox)

        # Render text on transparent canvas
        output_path = input_data.get_full_output_path()
        Path(output_path.parent).mkdir(parents=True, exist_ok=True)

        self._render_transparent(
            regions=included,
            width=width,
            height=height,
            output_path=output_path,
            font_color=input_data.font_color,
            preserve_layout=input_data.preserve_layout,
            dpi=input_data.dpi,
        )

        elapsed_ms = int((time.time() - start) * 1000)
        file_size = output_path.stat().st_size

        extracted_text = None
        if input_data.extract_text:
            extracted_text = " ".join(r.text for r in included)

        return ImageTextExtractOutput(
            output_path=str(output_path),
            input_path=input_data.image_path,
            mode=input_data.mode,
            image_dimensions=(width, height),
            regions_detected=len(all_regions),
            regions_included=len(included),
            extracted_text=extracted_text,
            regions=included,
            processing_time_ms=elapsed_ms,
            file_size_bytes=file_size,
        )

    def _ocr_detect(self, image, language: str) -> list[TextRegion]:
        """Run EasyOCR on image and return TextRegion list."""
        import numpy as np

        try:
            import easyocr
        except ImportError:
            raise RuntimeError(
                "EasyOCR is required. Install with: uv sync --extra imageops"
            )

        lang_map = {"auto": ["en"], "sr": ["rs_latin"], "en": ["en"], "de": ["de"]}
        langs = lang_map.get(language, ["en"])

        reader = easyocr.Reader(langs, gpu=False)
        img_array = np.array(image)
        results = reader.readtext(img_array)

        regions = []
        for bbox_points, text, confidence in results:
            # EasyOCR returns [[x1,y1],[x2,y1],[x2,y2],[x1,y2]]
            xs = [p[0] for p in bbox_points]
            ys = [p[1] for p in bbox_points]
            x1, y1 = int(min(xs)), int(min(ys))
            x2, y2 = int(max(xs)), int(max(ys))
            font_size = max(1, y2 - y1)

            regions.append(
                TextRegion(
                    text=text,
                    confidence=confidence,
                    bbox=(x1, y1, x2, y2),
                    font_size_estimate=font_size,
                )
            )
        return regions

    def _render_transparent(
        self,
        regions: list[TextRegion],
        width: int,
        height: int,
        output_path: Path,
        font_color: str,
        preserve_layout: bool,
        dpi: int,
    ) -> None:
        """Render text regions on a transparent RGBA canvas."""
        from PIL import Image, ImageDraw, ImageFont

        canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        for region in regions:
            x1, y1, x2, y2 = region.bbox
            font_size = region.font_size_estimate or max(1, y2 - y1)

            # Try to load a font at the right size
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            except Exception:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                except Exception:
                    font = ImageFont.load_default()

            # Determine color
            if font_color == "auto":
                color = _parse_color(region.color_hex or "#000000")
            else:
                color = _parse_color(font_color)

            if preserve_layout:
                draw.text((x1, y1), region.text, fill=(*color, 255), font=font)
            else:
                draw.text((x1, y1), region.text, fill=(*color, 255), font=font)

        canvas.save(str(output_path), "PNG", dpi=(dpi, dpi))

    def _download_image(self, url: str):
        """Download image from URL."""
        import io

        import httpx
        from PIL import Image

        resp = httpx.get(url, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content)).convert("RGB")
