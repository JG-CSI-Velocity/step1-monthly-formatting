"""Smoke test for the optional persona deep-dive module."""

from __future__ import annotations

from persona_module import PERSONA_MODULES, build_persona_appendix
from persona_module.climber import register as register_climber
from persona_module.decliner import register as register_decliner
from persona_module.nonuser import register as register_nonuser


def test_three_personas_registered():
    keys = {m.key for m in PERSONA_MODULES}
    assert keys == {"nonuser", "climber", "decliner"}


def test_each_persona_has_five_slides():
    for module in PERSONA_MODULES:
        assert len(module.slide_ids) == 5, (
            f"{module.key} should contribute 5 deep-dive slides, "
            f"got {len(module.slide_ids)}"
        )


def test_nonuser_maps_to_engagement_gap():
    mod = register_nonuser()
    assert mod.gap == "engagement"


def test_climber_maps_to_targeting_gap():
    mod = register_climber()
    assert mod.gap == "targeting"


def test_decliner_maps_to_ecosystem_gap():
    mod = register_decliner()
    assert mod.gap == "ecosystem"


def test_build_persona_appendix_returns_fifteen_slide_ids():
    slide_ids = build_persona_appendix()
    assert len(slide_ids) == 15
