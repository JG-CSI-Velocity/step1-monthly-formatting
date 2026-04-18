"""Smoke test for the Opportunity section module."""

from __future__ import annotations

from sections.opportunity import register
from sections._base import LAYOUT_CUSTOM, SectionSpec


def test_opportunity_registers_valid_spec():
    spec = register()
    assert isinstance(spec, SectionSpec)
    assert spec.key == "opportunity"
    assert spec.label == "The Opportunity"


def test_opportunity_owns_three_slides():
    spec = register()
    for sid in ("OPP-1", "A11.2", "S3"):
        assert sid in spec.layout_map


def test_opportunity_absorbs_reused_slides():
    spec = register()
    assert spec.absorb_ids.get("A11.2") == "value"
    assert spec.absorb_ids.get("S3") == "insights"


def test_opportunity_opp1_uses_kpi_hero():
    spec = register()
    layout_idx, slide_type = spec.layout_map["OPP-1"]
    assert layout_idx == LAYOUT_CUSTOM
    assert slide_type == "kpi_hero"
