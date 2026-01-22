"""
Color Extraction Service

Extracts dominant colors from images using:
1. LLM Vision (Gemini) for intelligent brand color analysis
2. Fallback to K-means clustering if LLM unavailable

Used for generating color themes from logos and brand images.
"""
import io
import base64
import colorsys
import json
import re
from typing import List, Tuple, Optional
import logging
import httpx

from PIL import Image
from collections import Counter

from app.core.config import settings

logger = logging.getLogger(__name__)


class ExtractedColor:
    """Represents an extracted color with various format representations."""

    def __init__(self, rgb: Tuple[int, int, int], frequency: float = 0.0):
        self.rgb = rgb
        self.frequency = frequency

    @property
    def hex(self) -> str:
        """Convert to hex color string."""
        return '#{:02x}{:02x}{:02x}'.format(*self.rgb)

    @property
    def hsl(self) -> Tuple[float, float, float]:
        """Convert to HSL (Hue, Saturation, Lightness)."""
        r, g, b = [x / 255.0 for x in self.rgb]
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        return (round(h * 360, 1), round(s * 100, 1), round(l * 100, 1))

    @property
    def hsl_css(self) -> str:
        """Return HSL as CSS value."""
        h, s, l = self.hsl
        return f"hsl({h}, {s}%, {l}%)"

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "rgb": self.rgb,
            "hex": self.hex,
            "hsl": self.hsl,
            "hsl_css": self.hsl_css,
            "frequency": round(self.frequency, 3)
        }


class ColorExtractionService:
    """Service for extracting dominant colors from images."""

    def __init__(self, num_colors: int = 5, resize_size: int = 100, use_llm: bool = True):
        """
        Initialize the color extraction service.

        Args:
            num_colors: Number of dominant colors to extract
            resize_size: Size to resize images to for processing (performance)
            use_llm: Whether to use LLM vision for intelligent extraction
        """
        self.num_colors = num_colors
        self.resize_size = resize_size
        self.use_llm = use_llm
        self.llm_model = getattr(settings, 'VISION_MODEL', 'google/gemini-2.0-flash-exp:free')

    def extract_from_bytes(self, image_bytes: bytes) -> List[ExtractedColor]:
        """
        Extract dominant colors from image bytes.

        Args:
            image_bytes: Raw image bytes (PNG, JPEG, etc.)

        Returns:
            List of ExtractedColor objects sorted by frequency
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            return self._extract_colors(image)
        except Exception as e:
            logger.error(f"Failed to extract colors from image: {e}")
            raise ValueError(f"Failed to process image: {str(e)}")

    def extract_from_base64(self, base64_data: str) -> List[ExtractedColor]:
        """
        Extract dominant colors from base64-encoded image (sync fallback).

        Args:
            base64_data: Base64 encoded image (with or without data URL prefix)

        Returns:
            List of ExtractedColor objects sorted by frequency
        """
        # Remove data URL prefix if present
        if base64_data.startswith('data:image'):
            base64_data = base64_data.split(',')[1]

        image_bytes = base64.b64decode(base64_data)
        return self.extract_from_bytes(image_bytes)

    async def extract_from_base64_async(self, base64_data: str) -> List[ExtractedColor]:
        """
        Extract dominant colors using LLM vision with fallback to algorithmic extraction.

        Args:
            base64_data: Base64 encoded image (with or without data URL prefix)

        Returns:
            List of ExtractedColor objects sorted by frequency
        """
        if self.use_llm:
            try:
                colors = await self._extract_with_llm(base64_data)
                if colors:
                    logger.info(f"Successfully extracted {len(colors)} colors using LLM vision")
                    return colors
            except Exception as e:
                logger.warning(f"LLM extraction failed, falling back to algorithmic: {e}")

        # Fallback to algorithmic extraction
        return self.extract_from_base64(base64_data)

    async def _extract_with_llm(self, base64_data: str) -> Optional[List[ExtractedColor]]:
        """
        Use LLM vision to intelligently extract brand colors from an image.

        Args:
            base64_data: Base64 encoded image

        Returns:
            List of ExtractedColor objects or None if extraction fails
        """
        # Ensure proper base64 format for API
        if base64_data.startswith('data:image'):
            image_url = base64_data
        else:
            # Detect image type and add appropriate prefix
            image_url = f"data:image/png;base64,{base64_data}"

        prompt = f"""Analyze this brand image/logo and extract the {self.num_colors} most important brand colors.

For each color, provide:
1. The exact RGB values (0-255)
2. The hex code
3. The relative importance/frequency in the brand (0.0 to 1.0, must sum to 1.0)

Focus on:
- Primary brand colors (most prominent)
- Secondary/accent colors
- Ignore white, black, or transparent backgrounds unless they're clearly part of the brand

Return ONLY a JSON array with this exact format:
[
  {{"rgb": [R, G, B], "hex": "#RRGGBB", "frequency": 0.4}},
  {{"rgb": [R, G, B], "hex": "#RRGGBB", "frequency": 0.3}},
  ...
]

Return the colors sorted by importance (most important first). Ensure frequencies sum to approximately 1.0."""

        try:
            request_payload = {
                "model": self.llm_model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            }
                        ]
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            }

            logger.info(f"Calling LLM vision for color extraction with model: {self.llm_model}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:8000",
                        "X-Title": "AI Analytics Platform - Color Extraction"
                    },
                    json=request_payload
                )

                if response.status_code != 200:
                    logger.error(f"LLM API error: {response.status_code} - {response.text}")
                    return None

                result = response.json()

                # Extract content from response
                if 'choices' in result:
                    content = result['choices'][0]['message']['content']
                else:
                    logger.warning(f"Unexpected response format: {result}")
                    return None

                logger.info(f"LLM response: {content[:200]}...")

                # Parse JSON from response
                json_match = re.search(r'\[[\s\S]*\]', content)
                if not json_match:
                    logger.warning("Could not find JSON array in LLM response")
                    return None

                colors_data = json.loads(json_match.group(0))

                # Convert to ExtractedColor objects
                colors = []
                for color_info in colors_data[:self.num_colors]:
                    rgb = tuple(color_info['rgb'])
                    frequency = color_info.get('frequency', 1.0 / len(colors_data))
                    colors.append(ExtractedColor(rgb, frequency))

                return colors

        except httpx.TimeoutException:
            logger.error("LLM request timed out")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM color extraction failed: {e}")
            return None

    def _extract_colors(self, image: Image.Image) -> List[ExtractedColor]:
        """
        Extract dominant colors using K-means-like clustering.

        Uses a simplified approach without sklearn dependency:
        1. Resize image for performance
        2. Convert to RGB
        3. Quantize colors using Pillow's quantize
        4. Get most common colors
        """
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Resize for faster processing
        image = image.resize(
            (self.resize_size, self.resize_size),
            Image.Resampling.LANCZOS
        )

        # Get all pixels
        pixels = list(image.getdata())
        total_pixels = len(pixels)

        # Filter out near-white and near-black pixels (often backgrounds)
        filtered_pixels = [
            p for p in pixels
            if not self._is_near_white(p) and not self._is_near_black(p)
        ]

        # If too many pixels filtered, use original
        if len(filtered_pixels) < total_pixels * 0.1:
            filtered_pixels = pixels

        # Count color frequencies using quantization
        # Round colors to reduce noise
        quantized = [self._quantize_color(p) for p in filtered_pixels]
        color_counts = Counter(quantized)

        # Get top colors
        top_colors = color_counts.most_common(self.num_colors * 2)

        # Filter similar colors and take top N
        unique_colors = self._filter_similar_colors(top_colors)[:self.num_colors]

        # Calculate frequencies
        total = sum(count for _, count in unique_colors)
        result = []
        for color, count in unique_colors:
            frequency = count / total if total > 0 else 0
            result.append(ExtractedColor(color, frequency))

        return result

    def _quantize_color(self, rgb: Tuple[int, int, int], levels: int = 32) -> Tuple[int, int, int]:
        """Quantize a color to reduce the number of unique colors."""
        step = 256 // levels
        return (
            (rgb[0] // step) * step + step // 2,
            (rgb[1] // step) * step + step // 2,
            (rgb[2] // step) * step + step // 2
        )

    def _is_near_white(self, rgb: Tuple[int, int, int], threshold: int = 240) -> bool:
        """Check if color is near white."""
        return all(c > threshold for c in rgb)

    def _is_near_black(self, rgb: Tuple[int, int, int], threshold: int = 15) -> bool:
        """Check if color is near black."""
        return all(c < threshold for c in rgb)

    def _color_distance(self, c1: Tuple[int, int, int], c2: Tuple[int, int, int]) -> float:
        """Calculate Euclidean distance between two colors."""
        return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5

    def _filter_similar_colors(
        self,
        color_counts: List[Tuple[Tuple[int, int, int], int]],
        min_distance: float = 50
    ) -> List[Tuple[Tuple[int, int, int], int]]:
        """Filter out colors that are too similar to each other."""
        if not color_counts:
            return []

        result = [color_counts[0]]

        for color, count in color_counts[1:]:
            is_unique = True
            for existing_color, _ in result:
                if self._color_distance(color, existing_color) < min_distance:
                    is_unique = False
                    break
            if is_unique:
                result.append((color, count))

        return result

    def generate_theme_palette(self, colors: List[ExtractedColor]) -> dict:
        """
        Generate a theme palette from extracted colors.

        Creates CSS custom property values for use in dashboards.

        Args:
            colors: List of extracted colors

        Returns:
            Dictionary with theme CSS variables
        """
        if not colors:
            return {}

        # Sort by lightness to assign roles
        sorted_colors = sorted(colors, key=lambda c: c.hsl[2])

        palette = {
            "colors": [c.to_dict() for c in colors],
            "css_variables": {}
        }

        # Assign semantic roles based on color characteristics
        if len(sorted_colors) >= 1:
            # Primary: most frequent non-extreme color
            primary = max(colors, key=lambda c: c.frequency)
            palette["css_variables"]["--theme-primary"] = primary.hex
            palette["css_variables"]["--theme-primary-hsl"] = primary.hsl_css

        if len(sorted_colors) >= 2:
            # Secondary: second most frequent
            secondary = sorted(colors, key=lambda c: c.frequency, reverse=True)[1]
            palette["css_variables"]["--theme-secondary"] = secondary.hex
            palette["css_variables"]["--theme-secondary-hsl"] = secondary.hsl_css

        if len(sorted_colors) >= 3:
            # Accent: most saturated color
            accent = max(colors, key=lambda c: c.hsl[1])
            palette["css_variables"]["--theme-accent"] = accent.hex
            palette["css_variables"]["--theme-accent-hsl"] = accent.hsl_css

        # Background and text colors (light/dark variants)
        lightest = sorted_colors[-1] if sorted_colors else None
        darkest = sorted_colors[0] if sorted_colors else None

        if lightest:
            # Create a lighter version for backgrounds
            h, s, l = lightest.hsl
            light_bg = f"hsl({h}, {min(s, 20)}%, {max(l, 95)}%)"
            palette["css_variables"]["--theme-background"] = light_bg

        if darkest:
            # Create a darker version for text
            h, s, l = darkest.hsl
            dark_text = f"hsl({h}, {min(s, 10)}%, {min(l, 20)}%)"
            palette["css_variables"]["--theme-text"] = dark_text

        return palette


# Singleton instance
_color_service: Optional[ColorExtractionService] = None


def get_color_extraction_service() -> ColorExtractionService:
    """Get or create the color extraction service singleton."""
    global _color_service
    if _color_service is None:
        _color_service = ColorExtractionService()
    return _color_service
