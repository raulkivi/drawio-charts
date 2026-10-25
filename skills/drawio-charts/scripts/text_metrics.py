"""Approximate text measurement, shared by node sizing and the SVG renderer.

No font metrics are available without a browser, so widths use an average
character width. It errs wide, so labels fit rather than overflow.
"""

from __future__ import annotations

import html
import math
import re

FONT_SIZE = 12
CHAR_WIDTH = 7.0      # average px per character at FONT_SIZE
LINE_HEIGHT = 16.0


def text_width(text: str, font_size: float = FONT_SIZE) -> float:
    return len(text) * CHAR_WIDTH * font_size / FONT_SIZE


def label_lines(label: str) -> list[str]:
    """Plain lines from a label that may hold <br>, other tags or entities."""
    text = re.sub(r"<br\s*/?>", "\n", label, flags=re.IGNORECASE)
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    return text.split("\n")


def wrap(lines: list[str], max_width: float, font_size: float = FONT_SIZE) -> list[str]:
    max_chars = max(1, int(max_width / (CHAR_WIDTH * font_size / FONT_SIZE)))
    wrapped: list[str] = []
    for line in lines:
        words, current = line.split(" "), ""
        for word in words:
            candidate = f"{current} {word}" if current else word
            if len(candidate) <= max_chars or not current:
                current = candidate
            else:
                wrapped.append(current)
                current = word
        wrapped.append(current)
    return wrapped


def fit_box(label: str, min_width: float = 80, max_width: float = 200,
            pad_x: float = 24, pad_y: float = 20) -> tuple[float, float]:
    """Width and height (multiples of 10) of a box that fits the label."""
    lines = label_lines(label)
    natural = max((text_width(line) for line in lines), default=0) + pad_x
    width = min(max(natural, min_width), max_width)
    rows = len(wrap(lines, width - pad_x))
    height = rows * LINE_HEIGHT + pad_y
    return round_up(width), round_up(max(height, 40))


def round_up(value: float, step: int = 10) -> float:
    return float(math.ceil(value / step) * step)
