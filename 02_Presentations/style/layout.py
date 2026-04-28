"""Slide layout geometry for the 2025-CSI-PPT template (13.33 x 7.5 widescreen)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PIL import Image
from pptx.util import Emu, Inches


@dataclass(frozen=True)
class Zone:
    """A rectangular region on a slide.

    Attributes are optional because different zones are specified in
    different ways (e.g. title zone has `top`+`height`; footer zone is
    anchored to the bottom via `bottom_offset`+`height`).
    """
    top: Optional[Emu] = None
    bottom_offset: Optional[Emu] = None  # from slide bottom
    height: Optional[Emu] = None
    left: Optional[Emu] = None
    width: Optional[Emu] = None
    full_width: bool = False


SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)

SAFE_LEFT = Inches(0.5)
SAFE_RIGHT = Inches(0.5)
SAFE_TOP = Inches(0.4)
SAFE_BOTTOM = Inches(0.4)

TITLE_ZONE = Zone(top=Inches(0.4), height=Inches(1.0), full_width=True)
FOOTER_ZONE = Zone(bottom_offset=Inches(0.4), height=Inches(0.4), full_width=True)
CONTENT_ZONE = Zone(top=Inches(1.4), bottom_offset=Inches(0.8), full_width=True)

KPI_ROW_H = Inches(1.2)


def is_inside_zone(shape, zone: Zone, slide_height: Emu) -> bool:
    """True if `shape` fits entirely inside `zone` on a slide of `slide_height`.

    Supports either (top, height) zones or (bottom_offset, height) zones.
    For the (bottom_offset, height) form, `bottom_offset` is the distance
    from the slide bottom up to the zone's top edge, and the zone extends
    downward by `height` (ending at `bottom_offset - height` above the
    slide bottom, i.e. may reach the slide bottom when those values are
    equal). Ignores horizontal position -- zones that use `full_width=True`
    span the whole slide horizontally.
    """
    if zone.top is not None and zone.height is not None:
        zone_top = zone.top
        zone_bottom = zone.top + zone.height
    elif zone.bottom_offset is not None and zone.height is not None:
        zone_top = slide_height - zone.bottom_offset
        zone_bottom = zone_top + zone.height
    else:
        raise ValueError("Zone must define (top, height) or (bottom_offset, height)")

    shape_top = shape.top
    shape_bottom = shape.top + shape.height
    return shape_top >= zone_top and shape_bottom <= zone_bottom


def fit_image(slide, image_path: Path, zone: Zone, slide_height: Emu):
    """Add image to slide sized to fit `zone`'s width, preserving aspect ratio.

    Returns the picture shape. Image width is set to `zone.width`, height is
    computed from the image's aspect ratio. The image is top-anchored at the
    zone's top edge and horizontally centered within the zone.
    """
    with Image.open(image_path) as img:
        px_w, px_h = img.size
    aspect = px_w / px_h

    if zone.width is None or zone.left is None:
        raise ValueError("fit_image requires zone.left and zone.width")

    if zone.top is not None:
        zone_top = zone.top
    elif zone.bottom_offset is not None and zone.height is not None:
        zone_top = slide_height - zone.bottom_offset - zone.height
    else:
        raise ValueError(
            "Zone requires `top`, or both `bottom_offset` and `height`, "
            "to compute the vertical anchor"
        )

    width_emu = zone.width
    height_emu = int(width_emu / aspect)

    left = zone.left + (zone.width - width_emu) // 2
    return slide.shapes.add_picture(
        str(image_path), left, zone_top, width=width_emu, height=height_emu
    )
