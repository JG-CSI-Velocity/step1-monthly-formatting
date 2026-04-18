"""Climber persona deep-dive (Targeting Gap)."""

from __future__ import annotations


def register():
    from . import PersonaModuleSpec

    return PersonaModuleSpec(
        key="climber",
        label="Climber Deep Dive",
        gap="targeting",
        slide_ids=[
            "A14.2",
            "A16.1",
            "A16.3",
            "A16.5",
            "A19.2",
        ],
        source_sections={
            "A14.2": "mailer",
            "A16.1": "mailer",
            "A16.3": "mailer",
            "A16.5": "mailer",
            "A19.2": "insights",
        },
    )
