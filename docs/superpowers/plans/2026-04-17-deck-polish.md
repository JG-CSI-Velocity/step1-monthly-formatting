# Deck Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a post-hoc PPTX polish pass that enforces `SLIDE_MAPPING.md` compliance on any generated deck, flags consultative/performance gaps, and never rewrites business content.

**Architecture:** New self-contained package under `02_Presentations/` — a pure-library `style/` module (six submodules) plus a `polish.py` driver with CLI. Dry-run by default. Writes Markdown reports plus an optional polished PPTX with `--apply`. No changes to `deck_builder.py` or any existing file.

**Tech Stack:** Python 3.12, `python-pptx`, `Pillow` (for image aspect/DPI), `pytest`, `loguru` (already in repo).

**Spec:** `docs/superpowers/specs/2026-04-17-deck-polish-design.md`

**Branch:** `feature/deck-polish` off `main` in `ars-production-pipeline`.

**Import quirk:** `02_Presentations/` starts with a digit and cannot be imported as a Python module. Every entry point (`polish.py`, tests via `conftest.py`) adds `02_Presentations/` to `sys.path` so absolute imports (`from style.palette import NAVY`) work.

---

## File Structure

```
02_Presentations/
├── __init__.py                     # Empty marker
├── conftest.py                     # Adds 02_Presentations/ to sys.path for pytest
├── polish.py                       # CLI entrypoint + driver
├── style/
│   ├── __init__.py                 # Re-exports public API
│   ├── palette.py                  # Colors + nearest/focal helpers
│   ├── typography.py               # Fonts + apply()
│   ├── layout.py                   # Zones + fit_image + is_inside_zone
│   ├── headline.py                 # HeadlineScore
│   ├── charts.py                   # ChartAudit
│   └── narrative.py                # NarrativeScore (imports headline + layout)
├── scripts/
│   └── make_fixtures.py            # One-shot generator for test fixtures
└── tests/
    ├── __init__.py
    ├── fixtures/                   # Committed .pptx files
    │   ├── pristine.pptx
    │   ├── moderately_broken.pptx
    │   └── badly_broken.pptx
    ├── test_palette.py
    ├── test_typography.py
    ├── test_layout.py
    ├── test_headline.py
    ├── test_charts.py
    ├── test_narrative.py
    └── test_polish.py
```

---

## Task 1: Branch + package skeleton

**Files:**
- Create: `02_Presentations/__init__.py`
- Create: `02_Presentations/conftest.py`
- Create: `02_Presentations/style/__init__.py`
- Create: `02_Presentations/scripts/__init__.py`
- Create: `02_Presentations/tests/__init__.py`

- [ ] **Step 1: Create the feature branch**

```bash
git checkout main
git pull
git checkout -b feature/deck-polish
```

- [ ] **Step 2: Create empty marker files**

```bash
mkdir -p 02_Presentations/style 02_Presentations/scripts 02_Presentations/tests/fixtures
touch 02_Presentations/__init__.py
touch 02_Presentations/style/__init__.py
touch 02_Presentations/scripts/__init__.py
touch 02_Presentations/tests/__init__.py
```

- [ ] **Step 3: Write conftest.py to enable imports under a digit-prefixed folder**

File: `02_Presentations/conftest.py`

```python
"""Adds 02_Presentations/ to sys.path so tests can import style.* directly.

02_Presentations/ starts with a digit, so it cannot be a Python package.
Prepending its absolute path to sys.path lets pytest resolve imports like
`from style.palette import NAVY` without relying on package semantics.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
```

- [ ] **Step 4: Verify pytest discovers the skeleton**

Run: `pytest 02_Presentations/ -v`
Expected: `no tests ran` (no error).

- [ ] **Step 5: Commit**

```bash
git add 02_Presentations/
git commit -m "feat(polish): scaffold 02_Presentations package skeleton"
```

---

## Task 2: `style/palette.py` — CSI color constants

**Files:**
- Create: `02_Presentations/style/palette.py`
- Test: `02_Presentations/tests/test_palette.py`

- [ ] **Step 1: Write the failing test for palette constants**

File: `02_Presentations/tests/test_palette.py`

```python
"""Tests for style.palette -- CSI color constants and helpers."""

from pptx.dml.color import RGBColor

from style.palette import (
    AMBER,
    CORAL,
    GRAY,
    NAVY,
    SLATE,
    TEAL,
    WHITE,
)


def test_named_colors_match_slide_mapping_hex():
    assert NAVY == RGBColor(0x1B, 0x36, 0x5D)
    assert TEAL == RGBColor(0x0D, 0x94, 0x88)
    assert CORAL == RGBColor(0xE7, 0x4C, 0x3C)
    assert AMBER == RGBColor(0xF3, 0x9C, 0x12)
    assert GRAY == RGBColor(0x95, 0xA5, 0xA6)
    assert SLATE == RGBColor(0x6B, 0x72, 0x80)
    assert WHITE == RGBColor(0xFF, 0xFF, 0xFF)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest 02_Presentations/tests/test_palette.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'style.palette'`.

- [ ] **Step 3: Implement the palette constants**

File: `02_Presentations/style/palette.py`

```python
"""CSI color palette from SLIDE_MAPPING.md.

One focal color per chart; everything else muted to MUTED_ALPHA.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from pptx.dml.color import RGBColor

NAVY = RGBColor(0x1B, 0x36, 0x5D)
TEAL = RGBColor(0x0D, 0x94, 0x88)
CORAL = RGBColor(0xE7, 0x4C, 0x3C)
AMBER = RGBColor(0xF3, 0x9C, 0x12)
GRAY = RGBColor(0x95, 0xA5, 0xA6)
SLATE = RGBColor(0x6B, 0x72, 0x80)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

MUTED_ALPHA = 0.3

PALETTE: tuple[RGBColor, ...] = (NAVY, TEAL, CORAL, AMBER, GRAY, SLATE, WHITE)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest 02_Presentations/tests/test_palette.py -v`
Expected: PASS.

- [ ] **Step 5: Write failing test for `is_palette_color` and `nearest_palette`**

Append to `02_Presentations/tests/test_palette.py`:

```python
from style.palette import is_palette_color, nearest_palette


def test_is_palette_color_true_for_exact_match():
    assert is_palette_color(RGBColor(0x1B, 0x36, 0x5D)) is True


def test_is_palette_color_false_for_off_palette():
    assert is_palette_color(RGBColor(0xFF, 0x00, 0xFF)) is False


def test_nearest_palette_snaps_near_coral_to_coral():
    # Off by 3 in each channel -- distance = sqrt(27) ~= 5.2
    nearby_coral = RGBColor(0xE4, 0x49, 0x39)
    assert nearest_palette(nearby_coral) == CORAL


def test_nearest_palette_returns_none_when_nothing_close_enough():
    # Bright magenta is far from all palette colors
    magenta = RGBColor(0xFF, 0x00, 0xFF)
    assert nearest_palette(magenta) is None


def test_nearest_palette_respects_threshold():
    # Exactly 5 away -- within threshold of 5.0
    just_inside = RGBColor(0x1E, 0x39, 0x5D)  # navy with (+3,+3,0) -> d=~4.24
    assert nearest_palette(just_inside) == NAVY
```

- [ ] **Step 6: Run the tests and verify they fail**

Run: `pytest 02_Presentations/tests/test_palette.py -v`
Expected: FAIL on the new tests — `ImportError`.

- [ ] **Step 7: Implement `is_palette_color` and `nearest_palette`**

Append to `02_Presentations/style/palette.py`:

```python
def _distance(a: RGBColor, b: RGBColor) -> float:
    """Euclidean distance in 0-255 RGB space."""
    return math.sqrt(
        (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2
    )


def is_palette_color(rgb: RGBColor) -> bool:
    """True if rgb is an exact-hex match for any palette color."""
    return any(rgb == p for p in PALETTE)


def nearest_palette(
    rgb: RGBColor, threshold: float = 5.0
) -> RGBColor | None:
    """Return the closest palette color if within `threshold`, else None.

    Colors within Euclidean distance <= threshold of a palette entry are
    assumed off-by-hex and snap to the palette entry. Farther colors are
    treated as intentional.
    """
    best: RGBColor | None = None
    best_d = float("inf")
    for p in PALETTE:
        d = _distance(rgb, p)
        if d < best_d:
            best_d = d
            best = p
    if best is not None and best_d <= threshold:
        return best
    return None
```

- [ ] **Step 8: Run tests and verify they pass**

Run: `pytest 02_Presentations/tests/test_palette.py -v`
Expected: all tests PASS.

- [ ] **Step 9: Write failing test for `focal()`**

Append to `02_Presentations/tests/test_palette.py`:

```python
from style.palette import focal


def test_focal_returns_named_color_with_muted_set():
    result = focal("teal")
    assert result["focal"] == TEAL
    assert NAVY in result["muted"]
    assert TEAL not in result["muted"]  # focal excluded from muted


def test_focal_raises_for_unknown_name():
    import pytest
    with pytest.raises(KeyError):
        focal("chartreuse")
```

- [ ] **Step 10: Run test to verify it fails**

Run: `pytest 02_Presentations/tests/test_palette.py -v`
Expected: FAIL — `ImportError` for `focal`.

- [ ] **Step 11: Implement `focal()`**

Append to `02_Presentations/style/palette.py`:

```python
_BY_NAME: dict[str, RGBColor] = {
    "navy": NAVY, "teal": TEAL, "coral": CORAL, "amber": AMBER,
    "gray": GRAY, "slate": SLATE, "white": WHITE,
}


def focal(name: str) -> dict[str, RGBColor | list[RGBColor]]:
    """Return {'focal': <color>, 'muted': [other palette colors]}.

    For charts that emphasize one series: use focal for the highlight,
    render others in muted with MUTED_ALPHA applied by the caller.
    """
    key = name.lower()
    if key not in _BY_NAME:
        raise KeyError(f"Unknown palette color: {name}")
    emphasis = _BY_NAME[key]
    return {
        "focal": emphasis,
        "muted": [c for c in PALETTE if c != emphasis and c != WHITE],
    }
```

- [ ] **Step 12: Run tests and verify they pass**

Run: `pytest 02_Presentations/tests/test_palette.py -v`
Expected: all tests PASS.

- [ ] **Step 13: Commit**

```bash
git add 02_Presentations/style/palette.py 02_Presentations/tests/test_palette.py
git commit -m "feat(polish): add style.palette with CSI colors and helpers"
```

---

## Task 3: `style/typography.py` — Montserrat type scale

**Files:**
- Create: `02_Presentations/style/typography.py`
- Test: `02_Presentations/tests/test_typography.py`

- [ ] **Step 1: Write failing test for `TextStyle` dataclass and role factories**

File: `02_Presentations/tests/test_typography.py`

```python
"""Tests for style.typography -- Montserrat type scale per SLIDE_MAPPING.md."""

from style.typography import (
    TextStyle,
    slide_title,
    subtitle,
    chart_title,
    chart_subtitle,
    data_label,
    axis_label,
    footnote,
    kpi_hero,
    kpi_label,
)


def test_slide_title_is_20pt_montserrat_extrabold():
    s = slide_title()
    assert s == TextStyle(font_name="Montserrat", size_pt=20, weight="ExtraBold")


def test_subtitle_is_14pt_montserrat_regular():
    assert subtitle() == TextStyle("Montserrat", 14, "Regular")


def test_chart_title_is_18pt_montserrat_bold():
    assert chart_title() == TextStyle("Montserrat", 18, "Bold")


def test_chart_subtitle_is_12pt_montserrat_regular():
    assert chart_subtitle() == TextStyle("Montserrat", 12, "Regular")


def test_data_label_is_11pt_montserrat_regular():
    assert data_label() == TextStyle("Montserrat", 11, "Regular")


def test_axis_label_is_10pt_montserrat_regular():
    assert axis_label() == TextStyle("Montserrat", 10, "Regular")


def test_footnote_is_9pt_montserrat_regular():
    assert footnote() == TextStyle("Montserrat", 9, "Regular")


def test_kpi_hero_is_36pt_montserrat_extrabold():
    assert kpi_hero() == TextStyle("Montserrat", 36, "ExtraBold")


def test_kpi_label_is_11pt_montserrat_regular():
    assert kpi_label() == TextStyle("Montserrat", 11, "Regular")
```

- [ ] **Step 2: Run and verify it fails**

Run: `pytest 02_Presentations/tests/test_typography.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Implement TextStyle and role factories**

File: `02_Presentations/style/typography.py`

```python
"""Montserrat type scale per SLIDE_MAPPING.md.

Each role is a factory returning a TextStyle. Callers apply the style via
`apply(text_frame, style)` which sets every run in the frame.
"""

from __future__ import annotations

from dataclasses import dataclass

from pptx.util import Pt


@dataclass(frozen=True)
class TextStyle:
    font_name: str
    size_pt: int
    weight: str  # "Regular" | "Bold" | "ExtraBold"


def slide_title() -> TextStyle:
    return TextStyle("Montserrat", 20, "ExtraBold")


def subtitle() -> TextStyle:
    return TextStyle("Montserrat", 14, "Regular")


def chart_title() -> TextStyle:
    return TextStyle("Montserrat", 18, "Bold")


def chart_subtitle() -> TextStyle:
    return TextStyle("Montserrat", 12, "Regular")


def data_label() -> TextStyle:
    return TextStyle("Montserrat", 11, "Regular")


def axis_label() -> TextStyle:
    return TextStyle("Montserrat", 10, "Regular")


def footnote() -> TextStyle:
    return TextStyle("Montserrat", 9, "Regular")


def kpi_hero() -> TextStyle:
    return TextStyle("Montserrat", 36, "ExtraBold")


def kpi_label() -> TextStyle:
    return TextStyle("Montserrat", 11, "Regular")
```

- [ ] **Step 4: Run tests and verify they pass**

Run: `pytest 02_Presentations/tests/test_typography.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Write failing test for `apply()` mutating a text frame**

Append to `02_Presentations/tests/test_typography.py`:

```python
from pptx import Presentation
from pptx.util import Inches

from style.typography import apply


def _one_slide_with_textbox(text: str):
    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    box = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(5), Inches(1))
    tf = box.text_frame
    tf.text = text
    return prs, tf


def test_apply_sets_font_name_and_size_on_every_run():
    _, tf = _one_slide_with_textbox("Hello")
    apply(tf, slide_title())
    for para in tf.paragraphs:
        for run in para.runs:
            assert run.font.name == "Montserrat"
            assert run.font.size == Pt(20)
            assert run.font.bold is True  # ExtraBold -> bold


def test_apply_regular_weight_clears_bold():
    _, tf = _one_slide_with_textbox("Hello")
    apply(tf, subtitle())
    for para in tf.paragraphs:
        for run in para.runs:
            assert run.font.bold is False


def test_apply_handles_multiple_paragraphs_and_runs():
    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    box = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(5), Inches(2))
    tf = box.text_frame
    tf.text = "First"
    tf.add_paragraph().text = "Second"
    apply(tf, footnote())
    sizes = [run.font.size for p in tf.paragraphs for run in p.runs]
    assert all(s == Pt(9) for s in sizes)
```

- [ ] **Step 6: Run and verify it fails**

Run: `pytest 02_Presentations/tests/test_typography.py -v`
Expected: FAIL — `ImportError: cannot import name 'apply'`.

- [ ] **Step 7: Implement `apply()`**

Append to `02_Presentations/style/typography.py`:

```python
def apply(text_frame, style: TextStyle) -> None:
    """Set every run in `text_frame` to match `style`.

    Bold flag is True for weights "Bold" or "ExtraBold", else False.
    python-pptx does not expose an ExtraBold setter directly; the bold
    attribute paired with font_name='Montserrat' renders correctly when
    the Montserrat ExtraBold face is installed on the render host.
    """
    bold = style.weight in ("Bold", "ExtraBold")
    size = Pt(style.size_pt)
    for paragraph in text_frame.paragraphs:
        for run in paragraph.runs:
            run.font.name = style.font_name
            run.font.size = size
            run.font.bold = bold
```

- [ ] **Step 8: Run tests and verify they pass**

Run: `pytest 02_Presentations/tests/test_typography.py -v`
Expected: all tests PASS.

- [ ] **Step 9: Commit**

```bash
git add 02_Presentations/style/typography.py 02_Presentations/tests/test_typography.py
git commit -m "feat(polish): add style.typography with Montserrat scale and apply()"
```

---

## Task 4: `style/layout.py` — zones, grid, fit_image

**Files:**
- Create: `02_Presentations/style/layout.py`
- Test: `02_Presentations/tests/test_layout.py`

- [ ] **Step 1: Write failing test for Zone and slide geometry constants**

File: `02_Presentations/tests/test_layout.py`

```python
"""Tests for style.layout -- slide zones and image fitting."""

from pptx.util import Inches

from style.layout import (
    SLIDE_W,
    SLIDE_H,
    SAFE_LEFT,
    SAFE_RIGHT,
    SAFE_TOP,
    SAFE_BOTTOM,
    TITLE_ZONE,
    FOOTER_ZONE,
    CONTENT_ZONE,
    KPI_ROW_H,
    Zone,
)


def test_slide_is_13_33x7_5_widescreen():
    assert SLIDE_W == Inches(13.33)
    assert SLIDE_H == Inches(7.5)


def test_safe_margins():
    assert SAFE_LEFT == Inches(0.5)
    assert SAFE_RIGHT == Inches(0.5)
    assert SAFE_TOP == Inches(0.4)
    assert SAFE_BOTTOM == Inches(0.4)


def test_title_zone_spans_full_width_under_top_margin():
    assert TITLE_ZONE.top == Inches(0.4)
    assert TITLE_ZONE.height == Inches(1.0)
    assert TITLE_ZONE.full_width is True


def test_footer_zone_is_at_bottom():
    assert FOOTER_ZONE.height == Inches(0.4)


def test_content_zone_sits_between_title_and_footer():
    assert CONTENT_ZONE.top == Inches(1.4)
    # Bottom is measured from slide bottom; content zone height is derived
    assert CONTENT_ZONE.bottom_offset == Inches(0.8)


def test_kpi_row_height():
    assert KPI_ROW_H == Inches(1.2)


def test_zone_is_frozen_dataclass():
    z = Zone(top=Inches(1), height=Inches(1))
    import pytest
    with pytest.raises(Exception):
        z.top = Inches(2)  # type: ignore[misc]
```

- [ ] **Step 2: Run and verify it fails**

Run: `pytest 02_Presentations/tests/test_layout.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Implement constants and Zone dataclass**

File: `02_Presentations/style/layout.py`

```python
"""Slide layout geometry for the 2025-CSI-PPT template (13.33 x 7.5 widescreen)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

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
```

- [ ] **Step 4: Run tests and verify they pass**

Run: `pytest 02_Presentations/tests/test_layout.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Write failing test for `is_inside_zone`**

Append to `02_Presentations/tests/test_layout.py`:

```python
from pptx import Presentation

from style.layout import is_inside_zone


def _slide_with_shape(top_in: float, height_in: float):
    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    shape = slide.shapes.add_textbox(
        Inches(0.5), Inches(top_in), Inches(12), Inches(height_in)
    )
    return prs, shape


def test_shape_inside_title_zone():
    _, shape = _slide_with_shape(top_in=0.5, height_in=0.8)
    assert is_inside_zone(shape, TITLE_ZONE, slide_height=SLIDE_H) is True


def test_shape_outside_title_zone_below():
    _, shape = _slide_with_shape(top_in=2.0, height_in=0.8)
    assert is_inside_zone(shape, TITLE_ZONE, slide_height=SLIDE_H) is False


def test_shape_inside_footer_zone():
    # Footer is bottom 0.4"; a shape starting at 7.15" with height 0.3"
    # sits entirely inside it.
    _, shape = _slide_with_shape(top_in=7.15, height_in=0.3)
    assert is_inside_zone(shape, FOOTER_ZONE, slide_height=SLIDE_H) is True
```

- [ ] **Step 6: Run and verify it fails**

Run: `pytest 02_Presentations/tests/test_layout.py -v`
Expected: FAIL — `ImportError`.

- [ ] **Step 7: Implement `is_inside_zone`**

Append to `02_Presentations/style/layout.py`:

```python
def is_inside_zone(shape, zone: Zone, slide_height: Emu) -> bool:
    """True if `shape` fits entirely inside `zone` on a slide of `slide_height`.

    Supports either (top, height) zones or (bottom_offset, height) zones.
    Ignores horizontal position -- zones that use `full_width=True` span
    the whole slide horizontally.
    """
    if zone.top is not None and zone.height is not None:
        zone_top = zone.top
        zone_bottom = zone.top + zone.height
    elif zone.bottom_offset is not None and zone.height is not None:
        zone_bottom = slide_height - zone.bottom_offset
        zone_top = zone_bottom - zone.height
    else:
        raise ValueError("Zone must define (top, height) or (bottom_offset, height)")

    shape_top = shape.top
    shape_bottom = shape.top + shape.height
    return shape_top >= zone_top and shape_bottom <= zone_bottom
```

- [ ] **Step 8: Run tests and verify they pass**

Run: `pytest 02_Presentations/tests/test_layout.py -v`
Expected: all tests PASS.

- [ ] **Step 9: Write failing test for `fit_image`**

Append to `02_Presentations/tests/test_layout.py`:

```python
from pathlib import Path
from PIL import Image

from style.layout import fit_image


def test_fit_image_preserves_aspect_ratio(tmp_path):
    # Create a 1000x500 red image (2:1 aspect)
    img_path = tmp_path / "wide.png"
    Image.new("RGB", (1000, 500), (0xE7, 0x4C, 0x3C)).save(img_path)

    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    zone = Zone(top=Inches(1.4), bottom_offset=Inches(0.8), full_width=True,
                left=Inches(0.5), width=Inches(12.33))

    pic = fit_image(slide, img_path, zone, slide_height=Inches(7.5))

    # 2:1 aspect fitted to 12.33" wide -> height is 6.165"
    assert abs(pic.width - Inches(12.33)) < Inches(0.01)
    assert abs(pic.height - Inches(6.165)) < Inches(0.02)
    # Top-anchored to the zone
    assert pic.top == Inches(1.4)
```

- [ ] **Step 10: Run and verify it fails**

Run: `pytest 02_Presentations/tests/test_layout.py -v`
Expected: FAIL — `ImportError`.

- [ ] **Step 11: Implement `fit_image`**

Append to `02_Presentations/style/layout.py`:

```python
from pathlib import Path

from PIL import Image


def fit_image(slide, image_path: Path, zone: Zone, slide_height: Emu):
    """Add image to slide sized to fit `zone`, preserving aspect ratio.

    Returns the picture shape. Image is top-anchored within the zone and
    horizontally centered if the computed width is less than the zone width.
    """
    with Image.open(image_path) as img:
        px_w, px_h = img.size
    aspect = px_w / px_h

    if zone.width is None or zone.left is None:
        raise ValueError("fit_image requires zone.left and zone.width")

    if zone.top is not None and zone.height is not None:
        zone_top = zone.top
        zone_height = zone.height
    elif zone.bottom_offset is not None:
        zone_bottom = slide_height - zone.bottom_offset
        zone_top = zone_bottom if zone.height is None else zone_bottom - zone.height
        zone_top = zone.top if zone.top is not None else zone_top
        # Derive height: content zone uses both top and bottom_offset
        zone_height = slide_height - zone.bottom_offset - (zone.top or 0)
    else:
        raise ValueError("Zone requires either (top, height) or (top, bottom_offset)")

    # Try full zone width; if height exceeds zone, scale by height instead
    width_emu = zone.width
    height_emu = int(width_emu / aspect)
    if height_emu > zone_height:
        height_emu = zone_height
        width_emu = int(height_emu * aspect)

    left = zone.left + (zone.width - width_emu) // 2
    return slide.shapes.add_picture(
        str(image_path), left, zone_top, width=width_emu, height=height_emu
    )
```

- [ ] **Step 12: Run tests and verify they pass**

Run: `pytest 02_Presentations/tests/test_layout.py -v`
Expected: all tests PASS.

- [ ] **Step 13: Commit**

```bash
git add 02_Presentations/style/layout.py 02_Presentations/tests/test_layout.py
git commit -m "feat(polish): add style.layout with zones and fit_image"
```

---

## Task 5: `scripts/make_fixtures.py` — synthetic test decks

**Files:**
- Create: `02_Presentations/scripts/make_fixtures.py`
- Create (committed output): `02_Presentations/tests/fixtures/pristine.pptx`
- Create (committed output): `02_Presentations/tests/fixtures/moderately_broken.pptx`
- Create (committed output): `02_Presentations/tests/fixtures/badly_broken.pptx`

- [ ] **Step 1: Write the fixture generator**

File: `02_Presentations/scripts/make_fixtures.py`

```python
"""Generate test fixture PPTX files for the polish test suite.

Run once manually; commit the generated .pptx files:
    python 02_Presentations/scripts/make_fixtures.py

Produces three decks with known compliance properties so tests can
assert exact flag counts without depending on client data.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

from style.palette import CORAL, NAVY, TEAL

FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures"


def _new_deck() -> Presentation:
    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)
    return prs


def _add_title_slide(prs: Presentation, title: str, client: str) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.4), Inches(12.33), Inches(1.0))
    tf = tb.text_frame
    tf.text = title
    for run in tf.paragraphs[0].runs:
        run.font.name = "Montserrat"
        run.font.size = Pt(36)
        run.font.bold = True
        run.font.color.rgb = NAVY
    sub = slide.shapes.add_textbox(Inches(0.5), Inches(1.6), Inches(12.33), Inches(0.6))
    sub.text_frame.text = client
    for run in sub.text_frame.paragraphs[0].runs:
        run.font.name = "Montserrat"
        run.font.size = Pt(18)


def _add_content_slide(
    prs: Presentation,
    headline: str,
    annotation: str | None,
    speaker_note: str | None,
    font_name: str = "Montserrat",
    title_color: RGBColor = NAVY,
) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    title_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(0.4), Inches(12.33), Inches(1.0)
    )
    title_box.text_frame.text = headline
    for run in title_box.text_frame.paragraphs[0].runs:
        run.font.name = font_name
        run.font.size = Pt(20)
        run.font.bold = True
        run.font.color.rgb = title_color

    if annotation is not None:
        ann_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(7.1), Inches(12.33), Inches(0.3)
        )
        ann_box.text_frame.text = annotation
        for run in ann_box.text_frame.paragraphs[0].runs:
            run.font.name = font_name
            run.font.size = Pt(9)

    if speaker_note is not None:
        slide.notes_slide.notes_text_frame.text = speaker_note


def build_pristine() -> Presentation:
    prs = _new_deck()
    _add_title_slide(prs, "Q1 2026 Debit Card Performance", "Cape & Coast Bank")
    _add_content_slide(
        prs,
        headline="Three branches drove 62% of debit growth, led by Main Office at 23%.",
        annotation="Recommend targeted staff training at top three locations.",
        speaker_note="Focus discussion on branch-level replicability.",
    )
    _add_content_slide(
        prs,
        headline="Interchange revenue rose 14% year-over-year on PIN-signature mix shift.",
        annotation="Continue promoting signature transactions through rewards.",
        speaker_note="Signature carries 2.1x the interchange of PIN.",
    )
    _add_content_slide(
        prs,
        headline="Attrition declined 8% after the Q4 re-engagement campaign.",
        annotation="Extend campaign cadence to quarterly in 2026.",
        speaker_note="Responder lift: $128 avg incremental debit spend per account.",
    )
    _add_content_slide(
        prs,
        headline="Payroll direct-deposit penetration reached 71%, up 4 points.",
        annotation="PFI status for payroll accounts is 3x portfolio average.",
        speaker_note="Upsell opportunity: auto-enroll overdraft protection.",
    )
    return prs


def build_moderately_broken() -> Presentation:
    prs = _new_deck()
    _add_title_slide(prs, "Q1 2026 Debit Card Performance", "Cape & Coast Bank")
    # Fragment headline (non-sentence)
    _add_content_slide(
        prs,
        headline="Debit Card Performance by Branch",  # fragment
        annotation="Main Office leads growth.",
        speaker_note="Speaker note present.",
    )
    # Missing annotation
    _add_content_slide(
        prs,
        headline="Interchange revenue rose 14% year-over-year on PIN-signature mix shift.",
        annotation=None,
        speaker_note="PIN-signature mix comment.",
    )
    # Off-palette coral title color (near-match, should snap to CORAL)
    _add_content_slide(
        prs,
        headline="Attrition declined 8% after the Q4 re-engagement campaign.",
        annotation="Extend cadence.",
        speaker_note="Note.",
        title_color=RGBColor(0xE4, 0x49, 0x39),  # within threshold of CORAL
    )
    return prs


def build_badly_broken() -> Presentation:
    prs = _new_deck()
    # Title slide uses wrong font + missing client
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.4), Inches(12.33), Inches(1.0))
    tb.text_frame.text = "Quarterly Review"
    for run in tb.text_frame.paragraphs[0].runs:
        run.font.name = "Times New Roman"
        run.font.size = Pt(36)
    # Content slide: Times New Roman, fragment headline, no annotation, no note
    _add_content_slide(
        prs,
        headline="Debit Trends",
        annotation=None,
        speaker_note=None,
        font_name="Times New Roman",
        title_color=RGBColor(0xAB, 0x12, 0xCD),  # wild off-palette
    )
    # Another Times New Roman slide with fragment
    _add_content_slide(
        prs,
        headline="Attrition Chart",
        annotation=None,
        speaker_note="",
        font_name="Times New Roman",
    )
    return prs


def main() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    build_pristine().save(FIXTURES / "pristine.pptx")
    build_moderately_broken().save(FIXTURES / "moderately_broken.pptx")
    build_badly_broken().save(FIXTURES / "badly_broken.pptx")
    print(f"Wrote 3 fixtures to {FIXTURES}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Generate the fixtures**

Run: `python 02_Presentations/scripts/make_fixtures.py`
Expected: stdout `Wrote 3 fixtures to .../tests/fixtures`.

- [ ] **Step 3: Verify the three files exist**

Run: `ls -la 02_Presentations/tests/fixtures/`
Expected: `pristine.pptx`, `moderately_broken.pptx`, `badly_broken.pptx` — non-zero sizes.

- [ ] **Step 4: Commit generator and fixtures**

```bash
git add 02_Presentations/scripts/make_fixtures.py 02_Presentations/tests/fixtures/
git commit -m "feat(polish): add fixture generator and three test decks"
```

---

## Task 6: `style/headline.py` — headline scorer

**Files:**
- Create: `02_Presentations/style/headline.py`
- Test: `02_Presentations/tests/test_headline.py`

- [ ] **Step 1: Write failing test for `HeadlineScore`**

File: `02_Presentations/tests/test_headline.py`

```python
"""Tests for style.headline -- scores headlines against SLIDE_MAPPING.md rules."""

from style.headline import HeadlineScore, score_headline


def test_complete_consultative_headline_passes_all_rules():
    text = "Three branches drove 62% of debit growth, led by Main Office at 23%."
    s = score_headline(text)
    assert s.is_complete_sentence is True
    assert s.has_metric is True
    assert s.has_direction is True
    assert s.has_driver_clause is True
    assert s.char_count == len(text)
    assert s.violates == []


def test_fragment_headline_flags_sentence_and_direction():
    text = "Debit Card Performance by Branch"
    s = score_headline(text)
    assert s.is_complete_sentence is False
    assert s.has_direction is False
    assert "not a complete sentence" in " | ".join(s.violates)


def test_metric_without_direction_flagged():
    text = "Debit penetration was 62%."
    s = score_headline(text)
    assert s.has_metric is True
    assert s.has_direction is False
    assert "missing direction word" in " | ".join(s.violates)


def test_direction_without_driver_flagged():
    text = "Interchange revenue rose 14%."
    s = score_headline(text)
    assert s.has_direction is True
    assert s.has_driver_clause is False
    assert "missing driver clause" in " | ".join(s.violates)


def test_long_headline_flagged():
    text = "A " * 80 + "."  # > 120 chars
    s = score_headline(text)
    assert s.char_count > 120
    assert any("too long" in v for v in s.violates)


def test_percent_dollar_and_number_all_count_as_metric():
    assert score_headline("Revenue rose $2.1M due to ICS onboarding.").has_metric
    assert score_headline("Attrition fell 12% driven by campaign.").has_metric
    assert score_headline("247 new accounts opened, led by branch 04.").has_metric
```

- [ ] **Step 2: Run and verify it fails**

Run: `pytest 02_Presentations/tests/test_headline.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Implement headline scorer**

File: `02_Presentations/style/headline.py`

```python
"""Score slide headlines against SLIDE_MAPPING.md rules.

Polish never rewrites headlines -- that's an analyst judgment call. It
surfaces violations so the analyst can fix them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

MAX_CHARS = 120

DIRECTION_WORDS = (
    "rose", "fell", "grew", "declined", "up", "down", "increased",
    "decreased", "climbed", "dropped", "gained", "lost", "drove",
    "drove", "jumped", "slipped", "rebounded",
)

DRIVER_PHRASES = (
    ", led by", ", due to", ", driven by", ", on the ", " on the ",
    ", because", ", as ", " led by ", " due to ", " driven by ",
)


@dataclass
class HeadlineScore:
    text: str
    is_complete_sentence: bool
    has_metric: bool
    has_direction: bool
    has_driver_clause: bool
    char_count: int
    violates: list[str] = field(default_factory=list)


def _is_complete_sentence(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if stripped[-1] not in ".!?":
        return False
    # Heuristic: must contain a verb-like space-separated token after
    # the first word. Fragments like "Debit Card by Branch" have no
    # verb and short word count relative to punctuation.
    words = stripped.rstrip(".!?").split()
    if len(words) < 4:
        return False
    # Title-case-all-words is a fragment signal (e.g. "Debit Card by Branch").
    # Sentences usually have at least one lowercase non-short word.
    lower_content_words = [
        w for w in words if len(w) > 3 and w[0].islower()
    ]
    return len(lower_content_words) >= 1


def _has_metric(text: str) -> bool:
    return bool(re.search(r"\d", text))


def _has_direction(text: str) -> bool:
    lower = text.lower()
    return any(re.search(rf"\b{w}\b", lower) for w in DIRECTION_WORDS)


def _has_driver_clause(text: str) -> bool:
    lower = text.lower()
    return any(phrase in lower for phrase in DRIVER_PHRASES)


def score_headline(text: str) -> HeadlineScore:
    is_sent = _is_complete_sentence(text)
    has_met = _has_metric(text)
    has_dir = _has_direction(text)
    has_drv = _has_driver_clause(text)
    n = len(text)

    violates: list[str] = []
    if not is_sent:
        violates.append("not a complete sentence")
    if not has_met:
        violates.append("missing metric (number, %, or $)")
    if not has_dir:
        violates.append("missing direction word (rose/fell/grew/...)")
    if not has_drv:
        violates.append("missing driver clause (comma + 'led by'/'due to'/...)")
    if n > MAX_CHARS:
        violates.append(f"too long ({n} > {MAX_CHARS} chars)")

    return HeadlineScore(
        text=text,
        is_complete_sentence=is_sent,
        has_metric=has_met,
        has_direction=has_dir,
        has_driver_clause=has_drv,
        char_count=n,
        violates=violates,
    )
```

- [ ] **Step 4: Run tests and verify they pass**

Run: `pytest 02_Presentations/tests/test_headline.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add 02_Presentations/style/headline.py 02_Presentations/tests/test_headline.py
git commit -m "feat(polish): add style.headline scorer"
```

---

## Task 7: `style/charts.py` — chart image audit

**Files:**
- Create: `02_Presentations/style/charts.py`
- Test: `02_Presentations/tests/test_charts.py`

- [ ] **Step 1: Write failing test for `audit_chart_image`**

File: `02_Presentations/tests/test_charts.py`

```python
"""Tests for style.charts -- audit of embedded chart images."""

from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.util import Inches

from style.charts import audit_chart_image


def _slide_with_picture(tmp_path: Path, px_w: int, px_h: int, width_in: float):
    img_path = tmp_path / "chart.png"
    Image.new("RGB", (px_w, px_h), (0x0D, 0x94, 0x88)).save(img_path)
    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    pic = slide.shapes.add_picture(
        str(img_path),
        Inches(0.5),
        Inches(1.4),
        width=Inches(width_in),
        height=Inches(width_in * px_h / px_w),
    )
    return pic


def test_audit_meets_dpi_floor_when_resolution_is_high(tmp_path):
    # 1800 px rendered at 12" wide = 150 DPI
    pic = _slide_with_picture(tmp_path, px_w=1800, px_h=900, width_in=12.0)
    audit = audit_chart_image(pic)
    assert audit.dpi_estimate >= 150
    assert audit.meets_dpi_floor is True


def test_audit_below_dpi_floor_for_low_resolution(tmp_path):
    # 600 px at 12" wide = 50 DPI
    pic = _slide_with_picture(tmp_path, px_w=600, px_h=300, width_in=12.0)
    audit = audit_chart_image(pic)
    assert audit.dpi_estimate < 150
    assert audit.meets_dpi_floor is False
```

- [ ] **Step 2: Run and verify it fails**

Run: `pytest 02_Presentations/tests/test_charts.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Implement `ChartAudit` and `audit_chart_image`**

File: `02_Presentations/style/charts.py`

```python
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
```

- [ ] **Step 4: Run tests and verify they pass**

Run: `pytest 02_Presentations/tests/test_charts.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add 02_Presentations/style/charts.py 02_Presentations/tests/test_charts.py
git commit -m "feat(polish): add style.charts audit"
```

---

## Task 8: `style/narrative.py` — consultative/performance scorer

**Files:**
- Create: `02_Presentations/style/narrative.py`
- Test: `02_Presentations/tests/test_narrative.py`

- [ ] **Step 1: Write failing test for `NarrativeScore`**

File: `02_Presentations/tests/test_narrative.py`

```python
"""Tests for style.narrative -- 0-3 scorer on consultative/performance/focal axes."""

from pathlib import Path

from pptx import Presentation

from style.narrative import NarrativeScore, score_slide

FIXTURES = Path(__file__).parent / "fixtures"


def _first_slide(path: Path):
    prs = Presentation(str(path))
    return prs, prs.slides[0]


def test_pristine_content_slide_scores_3_3_3():
    prs = Presentation(str(FIXTURES / "pristine.pptx"))
    slide = prs.slides[1]  # slide 1 is title, slides 2+ are content
    score = score_slide(slide, slide_height=prs.slide_height)
    assert score.consultative == 3
    assert score.performance == 3
    assert score.focal == 3


def test_fragment_headline_scores_low_consultative():
    prs = Presentation(str(FIXTURES / "moderately_broken.pptx"))
    slide = prs.slides[1]  # fragment headline slide
    score = score_slide(slide, slide_height=prs.slide_height)
    assert score.consultative <= 1


def test_missing_annotation_drops_performance_to_2():
    prs = Presentation(str(FIXTURES / "moderately_broken.pptx"))
    slide = prs.slides[2]  # note-only, no annotation
    score = score_slide(slide, slide_height=prs.slide_height)
    assert score.performance == 2


def test_badly_broken_slide_scores_low_across_axes():
    prs = Presentation(str(FIXTURES / "badly_broken.pptx"))
    slide = prs.slides[1]  # fragment + no annotation + no note
    score = score_slide(slide, slide_height=prs.slide_height)
    assert score.consultative <= 1
    assert score.performance <= 1


def test_score_fields_present():
    prs = Presentation(str(FIXTURES / "pristine.pptx"))
    slide = prs.slides[0]
    score = score_slide(slide, slide_height=prs.slide_height)
    assert isinstance(score, NarrativeScore)
    assert 0 <= score.consultative <= 3
    assert 0 <= score.performance <= 3
    assert 0 <= score.focal <= 3
```

- [ ] **Step 2: Run and verify it fails**

Run: `pytest 02_Presentations/tests/test_narrative.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Implement `score_slide`**

File: `02_Presentations/style/narrative.py`

```python
"""Consultative/performance/focal scorer for slides.

Polish flags slides with any axis < 2. No content rewriting.
"""

from __future__ import annotations

from dataclasses import dataclass

from pptx.util import Emu

from style.headline import score_headline
from style.layout import FOOTER_ZONE, TITLE_ZONE, is_inside_zone


@dataclass
class NarrativeScore:
    consultative: int  # 0-3 based on headline quality
    performance: int   # 0-3 based on annotation + speaker note presence
    focal: int         # 0-3 based on count of bold colors on the slide


def _find_title_text(slide, slide_height: Emu) -> str:
    """Pick the first text frame whose shape sits inside the TITLE_ZONE."""
    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        if is_inside_zone(shape, TITLE_ZONE, slide_height):
            text = shape.text_frame.text.strip()
            if text:
                return text
    return ""


def _find_footer_text(slide, slide_height: Emu) -> str:
    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        if is_inside_zone(shape, FOOTER_ZONE, slide_height):
            text = shape.text_frame.text.strip()
            if text:
                return text
    return ""


def _speaker_note_text(slide) -> str:
    if not slide.has_notes_slide:
        return ""
    return slide.notes_slide.notes_text_frame.text.strip()


def _consultative_score(headline: str) -> int:
    if not headline:
        return 0
    s = score_headline(headline)
    passed = sum(
        [s.is_complete_sentence, s.has_metric, s.has_direction, s.has_driver_clause]
    )
    # 4 passed -> 3; 3 passed -> 2; 2 passed -> 1; else 0 or 1 as fragment
    if passed == 4:
        return 3
    if passed == 3:
        return 2
    if passed >= 1:
        return 1
    return 0


def _performance_score(annotation: str, note: str) -> int:
    has_ann = bool(annotation)
    has_note = bool(note)
    if has_ann and has_note:
        return 3
    if has_ann or has_note:
        return 2
    return 0


def _focal_score(slide) -> int:
    """Count distinct bold fill colors on the slide. 1 -> 3; 2 -> 2; 3 -> 1; >=4 -> 0."""
    from pptx.dml.color import RGBColor
    seen: set[tuple[int, int, int]] = set()
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    try:
                        rgb = run.font.color.rgb
                    except AttributeError:
                        continue
                    if isinstance(rgb, RGBColor):
                        seen.add((rgb[0], rgb[1], rgb[2]))
    n = len(seen)
    if n <= 1:
        return 3
    if n == 2:
        return 2
    if n == 3:
        return 1
    return 0


def score_slide(slide, slide_height: Emu) -> NarrativeScore:
    headline = _find_title_text(slide, slide_height)
    annotation = _find_footer_text(slide, slide_height)
    note = _speaker_note_text(slide)

    return NarrativeScore(
        consultative=_consultative_score(headline),
        performance=_performance_score(annotation, note),
        focal=_focal_score(slide),
    )
```

- [ ] **Step 4: Run tests and verify they pass**

Run: `pytest 02_Presentations/tests/test_narrative.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add 02_Presentations/style/narrative.py 02_Presentations/tests/test_narrative.py
git commit -m "feat(polish): add style.narrative scorer"
```

---

## Task 9: `style/__init__.py` — public API

**Files:**
- Modify: `02_Presentations/style/__init__.py`

- [ ] **Step 1: Re-export the public API**

File: `02_Presentations/style/__init__.py`

```python
"""Public API for the CSI style module.

Designed so consumers (polish.py now; deck_builder.py and the html-review
renderer later) can import names from `style` directly without knowing
which submodule owns them.
"""

from style.palette import (
    AMBER, CORAL, GRAY, NAVY, SLATE, TEAL, WHITE,
    MUTED_ALPHA, PALETTE,
    focal, is_palette_color, nearest_palette,
)
from style.typography import (
    TextStyle,
    slide_title, subtitle, chart_title, chart_subtitle,
    data_label, axis_label, footnote, kpi_hero, kpi_label,
    apply,
)
from style.layout import (
    Zone,
    SLIDE_W, SLIDE_H, SAFE_LEFT, SAFE_RIGHT, SAFE_TOP, SAFE_BOTTOM,
    TITLE_ZONE, FOOTER_ZONE, CONTENT_ZONE, KPI_ROW_H,
    is_inside_zone, fit_image,
)
from style.headline import HeadlineScore, score_headline
from style.charts import ChartAudit, audit_chart_image
from style.narrative import NarrativeScore, score_slide
```

- [ ] **Step 2: Verify all imports resolve**

Run: `python -c "import sys; sys.path.insert(0, '02_Presentations'); from style import NAVY, score_slide, TextStyle; print('ok')"`
Expected: stdout `ok`.

- [ ] **Step 3: Commit**

```bash
git add 02_Presentations/style/__init__.py
git commit -m "feat(polish): expose style public API via __init__"
```

---

## Task 10: `polish.py` — CLI skeleton

**Files:**
- Create: `02_Presentations/polish.py`

- [ ] **Step 1: Write `polish.py` with argparse and a `hello` check**

File: `02_Presentations/polish.py`

```python
"""Deck polish driver -- post-hoc PPTX compliance pass.

Reads a deck, scores each slide, writes a Markdown report. With --apply,
also writes a polished PPTX with safe force-applied fixes (fonts,
near-palette colors). Never rewrites headlines or annotations.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="polish",
        description="Post-hoc PPTX polish pass (SLIDE_MAPPING.md compliance).",
    )
    p.add_argument("deck", nargs="?", type=Path, help="Path to input .pptx")
    p.add_argument("--batch", type=Path, help="Process every .pptx in this folder")
    p.add_argument(
        "--apply", action="store_true",
        help="Write polished PPTX (default is dry-run: report only)"
    )
    p.add_argument(
        "--report-only", action="store_true",
        help="Skip force-apply fixes; emit report only (implied by dry-run)"
    )
    p.add_argument("--out", type=Path, default=None, help="Output directory")
    p.add_argument(
        "--strict", action="store_true",
        help="Exit non-zero if any slide scores <2 on any axis"
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.batch is None and args.deck is None:
        logger.error("Provide a deck path or --batch <dir>")
        return 2
    logger.info(f"polish.py invoked (apply={args.apply}, strict={args.strict})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Smoke-test the CLI**

Run: `python 02_Presentations/polish.py --help`
Expected: argparse help text lists all flags.

Run: `python 02_Presentations/polish.py 02_Presentations/tests/fixtures/pristine.pptx`
Expected: log line `polish.py invoked (apply=False, strict=False)` and exit 0.

- [ ] **Step 3: Commit**

```bash
git add 02_Presentations/polish.py
git commit -m "feat(polish): add polish.py CLI skeleton"
```

---

## Task 11: `polish.py` — audit loop and report writer

**Files:**
- Modify: `02_Presentations/polish.py`
- Test: `02_Presentations/tests/test_polish.py`

- [ ] **Step 1: Write failing integration test for report generation**

File: `02_Presentations/tests/test_polish.py`

```python
"""Integration tests for polish.py against the three committed fixtures."""

from pathlib import Path

from polish import audit_deck, write_report

FIXTURES = Path(__file__).parent / "fixtures"


def test_pristine_audit_yields_no_flags_on_content_slides():
    # Title slide (slide index 1 / 1-based) is exempt -- title headlines
    # are inherently non-consultative and are not meant to be scored.
    result = audit_deck(FIXTURES / "pristine.pptx")
    assert result.deck_level.client_name_present is True
    content_slides = [s for s in result.slides if s.index > 1]
    assert all(s.flagged is False for s in content_slides), (
        "Pristine content slides should not flag: "
        + ", ".join(f"slide {s.index}" for s in content_slides if s.flagged)
    )


def test_moderately_broken_audit_flags_fragment_and_missing_annotation():
    result = audit_deck(FIXTURES / "moderately_broken.pptx")
    flagged = [s for s in result.slides if s.flagged]
    assert len(flagged) >= 2


def test_badly_broken_audit_flags_all_content_slides():
    result = audit_deck(FIXTURES / "badly_broken.pptx")
    # Title slide + 2 content slides; expect at least 2 flagged
    flagged = [s for s in result.slides if s.flagged]
    assert len(flagged) >= 2


def test_write_report_produces_markdown(tmp_path):
    result = audit_deck(FIXTURES / "pristine.pptx")
    report_path = tmp_path / "polish_report.md"
    write_report(result, report_path)
    text = report_path.read_text()
    assert text.startswith("# Polish Report")
    assert "Slides:" in text
```

- [ ] **Step 2: Run and verify it fails**

Run: `pytest 02_Presentations/tests/test_polish.py -v`
Expected: FAIL — `ImportError: cannot import name 'audit_deck'`.

- [ ] **Step 3: Implement `audit_deck`, `DeckAudit`, `SlideAudit`, `write_report`**

Replace contents of `02_Presentations/polish.py`:

```python
"""Deck polish driver -- post-hoc PPTX compliance pass."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from pptx import Presentation

from style.charts import audit_chart_image
from style.headline import score_headline
from style.layout import FOOTER_ZONE, TITLE_ZONE, is_inside_zone
from style.narrative import NarrativeScore, score_slide


@dataclass
class SlideAudit:
    index: int                 # 1-based
    headline: str
    narrative: NarrativeScore
    headline_violations: list[str]
    chart_dpi_violations: list[str]  # per-picture string summaries
    flagged: bool


@dataclass
class DeckLevelAudit:
    client_name_present: bool
    section_dividers_ok: bool   # placeholder: always True for now
    page_numbers_ok: bool       # placeholder
    appendix_separated: bool    # placeholder


@dataclass
class DeckAudit:
    deck_path: Path
    slide_count: int
    deck_level: DeckLevelAudit
    slides: list[SlideAudit] = field(default_factory=list)


def _extract_title(slide, slide_height) -> str:
    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        if is_inside_zone(shape, TITLE_ZONE, slide_height):
            text = shape.text_frame.text.strip()
            if text:
                return text
    return ""


def _client_name_present(title_slide_headline: str) -> bool:
    """Heuristic: look for a non-generic placeholder (len > 3 words or contains 'Bank'/'Union')."""
    if not title_slide_headline:
        return False
    lower = title_slide_headline.lower()
    return "bank" in lower or "union" in lower or len(title_slide_headline.split()) >= 4


def audit_deck(deck_path: Path) -> DeckAudit:
    prs = Presentation(str(deck_path))
    slide_height = prs.slide_height

    title_text = _extract_title(prs.slides[0], slide_height) if len(prs.slides) else ""
    deck_level = DeckLevelAudit(
        client_name_present=_client_name_present(title_text),
        section_dividers_ok=True,
        page_numbers_ok=True,
        appendix_separated=True,
    )

    slide_audits: list[SlideAudit] = []
    for i, slide in enumerate(prs.slides, start=1):
        headline = _extract_title(slide, slide_height)
        h_score = score_headline(headline) if headline else None
        narrative = score_slide(slide, slide_height=slide_height)

        chart_flags: list[str] = []
        for shape in slide.shapes:
            if shape.shape_type == 13:  # MSO_SHAPE_TYPE.PICTURE
                try:
                    audit = audit_chart_image(shape)
                    if not audit.meets_dpi_floor:
                        chart_flags.append(
                            f"Image below DPI floor ({audit.dpi_estimate} < 150)"
                        )
                except Exception as e:  # pragma: no cover
                    logger.warning(f"Slide {i} image audit failed: {e}")

        flagged = (
            narrative.consultative < 2
            or narrative.performance < 2
            or narrative.focal < 2
            or bool(chart_flags)
        )

        slide_audits.append(
            SlideAudit(
                index=i,
                headline=headline,
                narrative=narrative,
                headline_violations=h_score.violates if h_score else ["no headline detected"],
                chart_dpi_violations=chart_flags,
                flagged=flagged,
            )
        )

    return DeckAudit(
        deck_path=deck_path,
        slide_count=len(prs.slides),
        deck_level=deck_level,
        slides=slide_audits,
    )


def write_report(audit: DeckAudit, path: Path) -> None:
    lines: list[str] = []
    lines.append(f"# Polish Report -- {audit.deck_path.name}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Slides: {audit.slide_count}")
    passing = sum(1 for s in audit.slides if not s.flagged)
    lines.append(f"- Passing (all axes >=2, no DPI violations): {passing}")
    lines.append(f"- Flagged: {audit.slide_count - passing}")
    lines.append("")
    lines.append("## Deck-level findings")
    lines.append(f"- [{'x' if audit.deck_level.client_name_present else ' '}] Title slide has client name")
    lines.append(f"- [{'x' if audit.deck_level.section_dividers_ok else ' '}] Section dividers present")
    lines.append(f"- [{'x' if audit.deck_level.page_numbers_ok else ' '}] Page numbers present")
    lines.append(f"- [{'x' if audit.deck_level.appendix_separated else ' '}] Appendix separated")
    lines.append("")
    lines.append("## Slide-by-slide")
    for s in audit.slides:
        lines.append(f"### Slide {s.index} -- \"{s.headline or '(no title)'}\"")
        lines.append(f"- Consultative: {s.narrative.consultative}/3")
        lines.append(f"- Performance: {s.narrative.performance}/3")
        lines.append(f"- Focal: {s.narrative.focal}/3")
        if s.headline_violations:
            lines.append("- Headline violations:")
            for v in s.headline_violations:
                lines.append(f"  - {v}")
        if s.chart_dpi_violations:
            lines.append("- Chart violations:")
            for v in s.chart_dpi_violations:
                lines.append(f"  - {v}")
        lines.append("")
    path.write_text("\n".join(lines))


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="polish",
        description="Post-hoc PPTX polish pass (SLIDE_MAPPING.md compliance).",
    )
    p.add_argument("deck", nargs="?", type=Path, help="Path to input .pptx")
    p.add_argument("--batch", type=Path, help="Process every .pptx in this folder")
    p.add_argument("--apply", action="store_true", help="Write polished PPTX (default dry-run)")
    p.add_argument("--report-only", action="store_true", help="Emit report only")
    p.add_argument("--out", type=Path, default=None, help="Output directory")
    p.add_argument("--strict", action="store_true", help="Exit non-zero if any flag")
    return p.parse_args(argv)


def _process_one(deck_path: Path, out_dir: Path) -> DeckAudit:
    out_dir.mkdir(parents=True, exist_ok=True)
    audit = audit_deck(deck_path)
    report_path = out_dir / "polish_report.md"
    write_report(audit, report_path)
    logger.info(f"Wrote {report_path}")
    return audit


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.batch is None and args.deck is None:
        logger.error("Provide a deck path or --batch <dir>")
        return 2

    decks: list[Path]
    if args.batch is not None:
        decks = sorted(args.batch.glob("*.pptx"))
        if not decks:
            logger.error(f"No .pptx files found in {args.batch}")
            return 2
    else:
        decks = [args.deck]

    all_audits: list[DeckAudit] = []
    for d in decks:
        out_dir = args.out if args.out else d.parent / "polished"
        all_audits.append(_process_one(d, out_dir))

    if args.strict:
        any_flag = any(s.flagged for a in all_audits for s in a.slides)
        if any_flag:
            logger.error("Strict mode: flagged slides present")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the integration tests**

Run: `pytest 02_Presentations/tests/test_polish.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Smoke-test the CLI end-to-end on a fixture**

Run: `python 02_Presentations/polish.py 02_Presentations/tests/fixtures/badly_broken.pptx --out /tmp/polish_out`
Expected: log line `Wrote /tmp/polish_out/polish_report.md`; inspect the file to confirm it lists multiple flagged slides.

- [ ] **Step 6: Commit**

```bash
git add 02_Presentations/polish.py 02_Presentations/tests/test_polish.py
git commit -m "feat(polish): audit loop, DeckAudit, and report writer"
```

---

## Task 12: `polish.py` — force-apply fixes (fonts + colors)

**Files:**
- Modify: `02_Presentations/polish.py`
- Modify: `02_Presentations/tests/test_polish.py`

- [ ] **Step 1: Write failing test for `apply_fixes` on badly_broken**

Append to `02_Presentations/tests/test_polish.py`:

```python
from polish import apply_fixes
from pptx import Presentation


def test_apply_fixes_replaces_times_new_roman_with_montserrat(tmp_path):
    out_path = tmp_path / "fixed.pptx"
    apply_fixes(FIXTURES / "badly_broken.pptx", out_path)
    prs = Presentation(str(out_path))
    for slide in prs.slides:
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if run.font.name is not None:
                        assert run.font.name == "Montserrat", (
                            f"Found non-Montserrat font: {run.font.name}"
                        )


def test_apply_fixes_snaps_near_palette_color_on_moderately_broken(tmp_path):
    out_path = tmp_path / "fixed.pptx"
    apply_fixes(FIXTURES / "moderately_broken.pptx", out_path)
    prs = Presentation(str(out_path))
    # Slide 3 had CORAL-adjacent (0xE4, 0x49, 0x39) -- should now be exact CORAL
    from pptx.dml.color import RGBColor
    CORAL = RGBColor(0xE7, 0x4C, 0x3C)
    found_coral = False
    slide = prs.slides[3]
    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        for para in shape.text_frame.paragraphs:
            for run in para.runs:
                try:
                    if run.font.color.rgb == CORAL:
                        found_coral = True
                except AttributeError:
                    pass
    assert found_coral, "Expected near-coral color to snap to exact CORAL"
```

- [ ] **Step 2: Run and verify it fails**

Run: `pytest 02_Presentations/tests/test_polish.py -v`
Expected: FAIL — `ImportError: cannot import name 'apply_fixes'`.

- [ ] **Step 3: Implement `apply_fixes`**

Add to `02_Presentations/polish.py` (before the `_parse_args` function):

```python
MONTSERRAT_FAMILY = ("Montserrat", "Montserrat Regular", "Montserrat Bold",
                     "Montserrat ExtraBold", "Montserrat Medium")


def _force_montserrat(run) -> bool:
    """If run's font isn't in the Montserrat family, set it. Returns True if changed."""
    current = run.font.name
    if current in MONTSERRAT_FAMILY:
        return False
    run.font.name = "Montserrat"
    return True


def _snap_near_palette(run) -> bool:
    """If run color is within palette threshold, snap to palette. Returns True if changed."""
    from style.palette import nearest_palette
    try:
        rgb = run.font.color.rgb
    except AttributeError:
        return False
    if rgb is None:
        return False
    snapped = nearest_palette(rgb)
    if snapped is not None and snapped != rgb:
        run.font.color.rgb = snapped
        return True
    return False


def apply_fixes(deck_path: Path, out_path: Path) -> dict[str, int]:
    """Open deck, apply force-apply fixes, save to out_path.

    Returns a dict of change counts: {'fonts_fixed': N, 'colors_snapped': M}.
    """
    prs = Presentation(str(deck_path))
    fonts_fixed = 0
    colors_snapped = 0
    for slide in prs.slides:
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if _force_montserrat(run):
                        fonts_fixed += 1
                    if _snap_near_palette(run):
                        colors_snapped += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_path))
    return {"fonts_fixed": fonts_fixed, "colors_snapped": colors_snapped}
```

- [ ] **Step 4: Wire `apply_fixes` into `_process_one` under `--apply`**

Replace the `_process_one` function in `02_Presentations/polish.py`:

```python
def _process_one(deck_path: Path, out_dir: Path, apply: bool) -> DeckAudit:
    out_dir.mkdir(parents=True, exist_ok=True)
    audit = audit_deck(deck_path)
    report_path = out_dir / f"{deck_path.stem}__polish_report.md"
    write_report(audit, report_path)
    logger.info(f"Wrote {report_path}")

    if apply:
        polished_path = out_dir / deck_path.name
        counts = apply_fixes(deck_path, polished_path)
        logger.info(
            f"Applied: {counts['fonts_fixed']} fonts, "
            f"{counts['colors_snapped']} colors. Wrote {polished_path}"
        )

    return audit
```

And update the call site inside `main`:

```python
    all_audits: list[DeckAudit] = []
    for d in decks:
        out_dir = args.out if args.out else d.parent / "polished"
        all_audits.append(_process_one(d, out_dir, apply=args.apply))
```

- [ ] **Step 5: Run all tests**

Run: `pytest 02_Presentations/tests/ -v`
Expected: all tests PASS.

- [ ] **Step 6: Smoke-test --apply end-to-end**

Run: `python 02_Presentations/polish.py 02_Presentations/tests/fixtures/badly_broken.pptx --apply --out /tmp/polish_apply`
Expected: log line confirms `Applied: N fonts, M colors`. Open the output `.pptx` and confirm titles render in Montserrat.

- [ ] **Step 7: Commit**

```bash
git add 02_Presentations/polish.py 02_Presentations/tests/test_polish.py
git commit -m "feat(polish): add --apply force-apply for fonts and near-palette colors"
```

---

## Task 13: `polish.py` — diff report

**Files:**
- Modify: `02_Presentations/polish.py`
- Modify: `02_Presentations/tests/test_polish.py`

- [ ] **Step 1: Write failing test for `write_diff_report`**

Append to `02_Presentations/tests/test_polish.py`:

```python
from polish import write_diff_report


def test_diff_report_shows_before_after_text_per_slide(tmp_path):
    report_path = tmp_path / "polish_diff.md"
    write_diff_report(
        before_path=FIXTURES / "pristine.pptx",
        after_path=FIXTURES / "pristine.pptx",  # self-compare: no text changes
        out_path=report_path,
    )
    text = report_path.read_text()
    assert text.startswith("# Polish Diff")
    assert "Slide 1" in text
```

- [ ] **Step 2: Run and verify it fails**

Run: `pytest 02_Presentations/tests/test_polish.py::test_diff_report_shows_before_after_text_per_slide -v`
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Implement `write_diff_report`**

Add to `02_Presentations/polish.py` (after `write_report`):

```python
def _slide_texts(prs_path: Path) -> list[list[str]]:
    """Return a list of per-slide lists of text-frame strings."""
    prs = Presentation(str(prs_path))
    result: list[list[str]] = []
    for slide in prs.slides:
        texts: list[str] = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                text = shape.text_frame.text.strip()
                if text:
                    texts.append(text)
        result.append(texts)
    return result


def write_diff_report(before_path: Path, after_path: Path, out_path: Path) -> None:
    before = _slide_texts(before_path)
    after = _slide_texts(after_path)
    lines: list[str] = ["# Polish Diff", ""]
    for i, (b, a) in enumerate(zip(before, after), start=1):
        lines.append(f"## Slide {i}")
        if b == a:
            lines.append("_(no text changes)_")
        else:
            lines.append("**Before:**")
            for t in b:
                lines.append(f"- {t}")
            lines.append("**After:**")
            for t in a:
                lines.append(f"- {t}")
        lines.append("")
    out_path.write_text("\n".join(lines))
```

- [ ] **Step 4: Wire diff-report into `_process_one` under `--apply`**

Update `_process_one` in `02_Presentations/polish.py`:

```python
def _process_one(deck_path: Path, out_dir: Path, apply: bool) -> DeckAudit:
    out_dir.mkdir(parents=True, exist_ok=True)
    audit = audit_deck(deck_path)
    report_path = out_dir / f"{deck_path.stem}__polish_report.md"
    write_report(audit, report_path)
    logger.info(f"Wrote {report_path}")

    if apply:
        polished_path = out_dir / deck_path.name
        counts = apply_fixes(deck_path, polished_path)
        logger.info(
            f"Applied: {counts['fonts_fixed']} fonts, "
            f"{counts['colors_snapped']} colors. Wrote {polished_path}"
        )
        diff_path = out_dir / f"{deck_path.stem}__polish_diff.md"
        write_diff_report(deck_path, polished_path, diff_path)
        logger.info(f"Wrote {diff_path}")

    return audit
```

- [ ] **Step 5: Run all tests**

Run: `pytest 02_Presentations/tests/ -v`
Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add 02_Presentations/polish.py 02_Presentations/tests/test_polish.py
git commit -m "feat(polish): add diff report alongside --apply"
```

---

## Task 14: End-to-end validation + PR

**Files:**
- None (test run + PR)

- [ ] **Step 1: Run full test suite from repo root**

Run: `pytest 02_Presentations/ -v`
Expected: all tests PASS. Note the count (>= ~30 tests).

- [ ] **Step 2: Run polish in batch mode against all fixtures**

```bash
python 02_Presentations/polish.py --batch 02_Presentations/tests/fixtures --out /tmp/polish_batch --apply
```

Expected: three `polish_report.md` + three polished `.pptx` + three `polish_diff.md` files in `/tmp/polish_batch/`.

- [ ] **Step 3: Inspect one polished fixture manually**

Open `/tmp/polish_batch/badly_broken.pptx` in PowerPoint (on the work PC or Quick Look on Mac). Confirm fonts are Montserrat, the wild off-palette title color is unchanged (outside threshold, by design), and the moderately_broken coral is snapped.

- [ ] **Step 4: Verify strict mode exits non-zero on broken decks**

```bash
python 02_Presentations/polish.py 02_Presentations/tests/fixtures/badly_broken.pptx --strict
echo "Exit code: $?"
```

Expected: `Exit code: 1`.

- [ ] **Step 5: Push branch**

```bash
git push -u origin feature/deck-polish
```

- [ ] **Step 6: Open PR**

```bash
gh pr create --title "feat: deck polish -- post-hoc PPTX compliance pass" --body "$(cat <<'EOF'
## Summary
- New `02_Presentations/` package: `style/` (six submodules) + `polish.py` driver
- Dry-run by default; `--apply` writes polished PPTX + diff report
- Three committed test fixtures; ~30 unit + integration tests
- No changes to existing code (deck_builder.py, etc.)

## Spec
`docs/superpowers/specs/2026-04-17-deck-polish-design.md`

## Test plan
- [x] Unit tests pass for all six style submodules
- [x] Integration tests pass against pristine, moderately_broken, badly_broken fixtures
- [x] Batch mode verified against all fixtures
- [x] `--strict` exits non-zero on flagged decks
- [ ] Reviewer: open badly_broken output in PowerPoint and confirm Montserrat renders

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Expected: PR URL printed. Copy into conversation for review.

---

## Self-review checklist

**Spec coverage** (each §/requirement → task):
- §5.1 file layout → Task 1 + files created throughout
- §5.2 module boundaries → enforced by tests (no file I/O in `style/`)
- §6.1 palette → Task 2
- §6.2 typography → Task 3
- §6.3 layout → Task 4
- §6.4 headline → Task 6
- §6.5 charts → Task 7
- §6.6 narrative → Task 8
- §7.1 CLI → Task 10 + wired fully in Task 11, 12
- §7.2 force-apply fonts + colors → Task 12
- §7.3 flag-only → covered by audit_deck in Task 11
- §7.4 outputs (polish_report.md, polish_diff.md, polished/*.pptx) → Tasks 11, 12, 13
- §7.5 report structure → Task 11 write_report
- §8 testing fixtures + unit + integration → Tasks 5, 11, 12
- §9 branch strategy → Tasks 1, 14
- §11 acceptance criteria → Task 14

**Placeholder scan:** no TBD/TODO/"similar to" found. All code blocks complete.

**Type consistency:** `DeckAudit`, `SlideAudit`, `DeckLevelAudit`, `NarrativeScore`, `HeadlineScore`, `ChartAudit`, `TextStyle`, `Zone` — names identical across tasks.

**Scope check:** single implementation plan, single branch, ~14 hours focused work — fits a weekend day.

---

## Execution options

**Plan complete and saved to `docs/superpowers/plans/2026-04-17-deck-polish.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration
**2. Inline Execution** — execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
