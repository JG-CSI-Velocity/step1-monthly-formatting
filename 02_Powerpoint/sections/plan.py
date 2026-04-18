"""Plan section -- what we will do, ending with the CTA.

New slides:
  PLAN-1: 3-5 strategic pillars mapped to the three gaps
  CLOSE-1: final takeaway / CTA

Absorbed slides:
  A17.1 (mailer): reach -- evidence for targeting pillar
  A18.3 (insights): industry benchmark -- with denominator footnote
  A12.{most_recent_month}: dynamic mailer month, resolved at assembly time

Placeholders used:
  PLAN-1: pillar text only (no numbers)
  CLOSE-1: {{CLIENT_NAME}}
  A12.{month}: {{MOST_RECENT_MAILER_MONTH}} -- assembler picks newest month
"""

from __future__ import annotations

from ._base import LAYOUT_CUSTOM, LAYOUT_MAIL_SUMMARY, SectionSpec

_PREFIXES = ["plan", "close", "a17", "a18", "a12"]

_LAYOUT_MAP = {
    "PLAN-1":   (LAYOUT_CUSTOM, "screenshot"),
    "A17.1":    (LAYOUT_CUSTOM, "screenshot"),
    "A18.3":    (LAYOUT_CUSTOM, "screenshot"),
    "CLOSE-1":  (LAYOUT_CUSTOM, "kpi_hero"),
}

_ABSORB_IDS = {
    "A17.1": "mailer",
    "A18.3": "insights",
}


def _mailer_month_fallback(slide_id: str) -> tuple[int, str] | None:
    """Match the dynamic most-recent mailer month slide (A12.{month})."""
    if slide_id.startswith("A12."):
        return (LAYOUT_MAIL_SUMMARY, "mailer_summary")
    return None


def register() -> SectionSpec:
    return SectionSpec(
        key="plan",
        label="The Plan",
        prefixes=_PREFIXES,
        layout_map=_LAYOUT_MAP,
        prefix_fallback=_mailer_month_fallback,
        absorb_ids=_ABSORB_IDS,
    )
