"""Decliner persona deep-dive (Ecosystem Gap / retention)."""

from __future__ import annotations


def register():
    from . import PersonaModuleSpec

    return PersonaModuleSpec(
        key="decliner",
        label="Decliner Deep Dive",
        gap="ecosystem",
        slide_ids=[
            "A9.1",
            "A9.5",
            "A9.9",
            "A9.10",
            "A20.2",
        ],
        source_sections={
            "A9.1": "attrition",
            "A9.5": "attrition",
            "A9.9": "attrition",
            "A9.10": "attrition",
            "A20.2": "insights",
        },
    )
