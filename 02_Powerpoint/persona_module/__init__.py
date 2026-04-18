"""Optional persona deep-dive module.

Toggled on via --persona-module on the deck assembler. When on, adds a
15-slide appendix pack (5 slides per persona for Non-User, Climber,
Decliner). When off, the main deck has no persona content beyond the
Persona Bridge slide.

Each sub-module defines a PersonaModuleSpec dataclass declaring which
slide IDs belong to that persona and which Diagnosis gap it maps to.
Slides themselves are absorbed from existing analytics folders --
this module is metadata only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .climber import register as _climber
from .decliner import register as _decliner
from .nonuser import register as _nonuser


@dataclass
class PersonaModuleSpec:
    """Declaration for one persona deep-dive appendix."""

    key: str                  # "nonuser" | "climber" | "decliner"
    label: str
    gap: str                  # "engagement" | "targeting" | "ecosystem"
    slide_ids: list[str] = field(default_factory=list)
    source_sections: dict[str, str] = field(default_factory=dict)
    # slide_id -> donor section (e.g. "A14.2": "mailer")


PERSONA_MODULES: list[PersonaModuleSpec] = [
    _nonuser(),
    _climber(),
    _decliner(),
]


def build_persona_appendix() -> list[str]:
    """Return every persona slide ID in order (non-user, climber, decliner)."""
    out: list[str] = []
    for mod in PERSONA_MODULES:
        out.extend(mod.slide_ids)
    return out


__all__ = ["PERSONA_MODULES", "PersonaModuleSpec", "build_persona_appendix"]
