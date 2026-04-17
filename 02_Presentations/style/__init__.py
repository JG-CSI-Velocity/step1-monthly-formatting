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
