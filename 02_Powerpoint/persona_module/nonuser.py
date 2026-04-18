"""Non-User persona deep-dive (Engagement Gap)."""

from __future__ import annotations


def register():
    from . import PersonaModuleSpec

    return PersonaModuleSpec(
        key="nonuser",
        label="Non-User Deep Dive",
        gap="engagement",
        slide_ids=[
            "A7.11",
            "A7.12",
            "A7.10a",
            "A20.1",
            "A11.1",
        ],
        source_sections={
            "A7.11": "dctr",
            "A7.12": "dctr",
            "A7.10a": "dctr",
            "A20.1": "insights",
            "A11.1": "value",
        },
    )
