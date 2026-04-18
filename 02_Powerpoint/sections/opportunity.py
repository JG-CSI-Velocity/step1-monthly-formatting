"""Opportunity section -- size of the prize.

New slide: OPP-1 (Total Addressable Spend, KPI hero)
Absorbed slides:
  A11.2 (value): Reg E value
  S3 (insights): opportunity synthesis

Opens with the big number. Closes Diagnosis and sets up Plan.

Placeholders used:
  OPP-1: {{ADDRESSABLE_SPEND_USD}}, {{NOTEBOOK_PENETRATION}}
"""

from __future__ import annotations

from ._base import LAYOUT_CUSTOM, SectionSpec

_PREFIXES = ["opp"]

_LAYOUT_MAP = {
    "OPP-1": (LAYOUT_CUSTOM, "kpi_hero"),
    "A11.2": (LAYOUT_CUSTOM, "screenshot"),
    "S3":    (LAYOUT_CUSTOM, "screenshot"),
}

_ABSORB_IDS = {
    "A11.2": "value",
    "S3": "insights",
}


def register() -> SectionSpec:
    return SectionSpec(
        key="opportunity",
        label="The Opportunity",
        prefixes=_PREFIXES,
        layout_map=_LAYOUT_MAP,
        absorb_ids=_ABSORB_IDS,
    )
