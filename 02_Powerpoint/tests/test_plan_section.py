"""Smoke test for the Plan section module."""

from __future__ import annotations

from sections.plan import register
from sections._base import LAYOUT_CUSTOM, SectionSpec


def test_plan_registers_valid_spec():
    spec = register()
    assert isinstance(spec, SectionSpec)
    assert spec.key == "plan"
    assert spec.label == "The Plan"


def test_plan_owns_expected_slides():
    spec = register()
    for sid in ("PLAN-1", "A17.1", "A18.3", "CLOSE-1"):
        assert sid in spec.layout_map, f"{sid} missing from plan section"


def test_plan_has_mailer_prefix_fallback_for_dynamic_month():
    spec = register()
    assert spec.prefix_fallback is not None
    result = spec.prefix_fallback("A12.Mar26")
    assert result is not None
    layout_idx, slide_type = result
    assert layout_idx == LAYOUT_CUSTOM or layout_idx == 20  # LAYOUT_MAIL_SUMMARY


def test_plan_absorbs_reused_slides():
    spec = register()
    assert spec.absorb_ids.get("A17.1") == "mailer"
    assert spec.absorb_ids.get("A18.3") == "insights"
