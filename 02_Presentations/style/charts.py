"""Audit embedded chart images. Polish cannot re-render charts -- it flags only.

The Python cells that render charts own the aesthetic (colors, fonts, labels).
Polish only checks what it can measure from the picture shape itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from PIL import Image
from pptx.util import Emu

DPI_FLOOR = 150


@dataclass
class ChartAudit:
    dpi_estimate: int
    meets_dpi_floor: bool
    width_px: int
    width_inches: float


def _emu_to_inches(emu: Emu) -> float:
    return emu / 914400  # python-pptx constant


def audit_chart_image(picture) -> ChartAudit:
    """Inspect a picture shape, return an audit of render quality."""
    blob = picture.image.blob
    with Image.open(BytesIO(blob)) as img:
        px_w = img.size[0]
    width_in = _emu_to_inches(picture.width)
    dpi = int(px_w / width_in) if width_in > 0 else 0
    return ChartAudit(
        dpi_estimate=dpi,
        meets_dpi_floor=dpi >= DPI_FLOOR,
        width_px=px_w,
        width_inches=round(width_in, 2),
    )
