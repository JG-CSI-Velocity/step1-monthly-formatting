"""Sample Deck Builder -- generates a review PPTX showing all slide variants per section.

For each section, creates divider slides labeling each variant:
  "SECTION: Mailer -- Slide 1 of 33 -- slide_id: A12.Jan26.Swipes -- type: screenshot -- layout: 8"

JG reviews the sampler, picks winners per section, and those choices
get locked into the master deck_builder.py.

Usage (from command line):
    cd M:\\ARS\\01_Analysis
    python -m ars_analysis.output.sample_deck_builder --month 2026.04 --csm JamesG --client 1776

Or called from Python:
    from ars_analysis.output.sample_deck_builder import build_sample_deck
    build_sample_deck(ctx)
"""

from __future__ import annotations

import calendar
from pathlib import Path

from loguru import logger
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

from ars_analysis.pipeline.context import PipelineContext
from ars_analysis.output.deck_builder import (
    DeckBuilder,
    SlideContent,
    _group_by_section,
    _result_to_slide,
    _SECTION_LABELS,
    SECTION_ORDER,
    LAYOUT_SECTION,
    LAYOUT_CUSTOM,
    LAYOUT_CONTENT,
    LAYOUT_BLANK,
)

# Layout name lookup for labels
_LAYOUT_NAMES = {
    0: "TITLE_DARK",
    1: "TITLE",
    2: "CONTENT",
    3: "CONTENT_ALT",
    4: "SECTION",
    5: "SECTION_ALT",
    6: "SECTION_GRAY",
    7: "TITLE_VARIANT",
    8: "CUSTOM",
    9: "TWO_CONTENT",
    10: "COMPARISON",
    11: "BLANK",
    12: "BULLETS",
    13: "PICTURE",
    14: "2_PICTURES",
    15: "3_PICTURES",
    16: "WIDE_TITLE",
    17: "TITLE_RPE",
    18: "TITLE_ARS",
    19: "TITLE_ICS",
}


def _label_slide(section_name: str, idx: int, total: int, result) -> SlideContent:
    """Create a label slide that describes the next variant."""
    slide_id = getattr(result, "slide_id", "unknown")
    slide_type = getattr(result, "slide_type", "screenshot")
    layout_idx = getattr(result, "layout_index", LAYOUT_CUSTOM)
    layout_name = _LAYOUT_NAMES.get(layout_idx, str(layout_idx))
    title_text = getattr(result, "title", "")
    has_chart = bool(getattr(result, "chart_path", None))
    has_kpis = bool(getattr(result, "kpis", None))
    has_bullets = bool(getattr(result, "bullets", None))

    label = (
        f"SECTION: {section_name}\n"
        f"Option {idx + 1} of {total}\n"
        f"\n"
        f"slide_id: {slide_id}\n"
        f"type: {slide_type}\n"
        f"layout: {layout_idx} ({layout_name})\n"
        f"title: {title_text[:80]}{'...' if len(title_text) > 80 else ''}\n"
        f"has_chart: {has_chart}\n"
        f"has_kpis: {has_kpis}\n"
        f"has_bullets: {has_bullets}"
    )

    return SlideContent(
        slide_type="section",
        title=label,
        layout_index=LAYOUT_SECTION,
    )


def build_sample_deck(ctx: PipelineContext) -> Path | None:
    """Build a sample/review PPTX showing all slide variants per section.

    For each section:
    1. Section divider: "SECTION: {name} -- {N} variants"
    2. For each variant: label slide (metadata) + actual rendered slide
    """
    if not ctx.all_slides:
        logger.warning("No slides to build sample deck from")
        return None

    # Resolve template
    from ars_analysis.output.deck_builder import _FALLBACK_TEMPLATE
    template = _FALLBACK_TEMPLATE
    if ctx.settings and hasattr(ctx.settings, "paths"):
        cfg_template = getattr(ctx.settings.paths, "template_path", None)
        if cfg_template and Path(cfg_template).exists():
            template = Path(cfg_template)

    if not template.exists():
        logger.warning("Template not found: {name}", name=template.name)
        return None

    # Group results by section
    sections = _group_by_section(ctx.all_slides)
    _ctx_results = ctx.results if ctx else {}

    # Build month/client info
    client_name = ctx.client.client_name
    month = ctx.client.month
    try:
        month_num = int(month.split(".")[1]) if "." in month else 1
        year = month.split(".")[0] if "." in month else ""
        month_name = calendar.month_name[month_num]
        subtitle = f"{client_name} | {month_name} {year}"
    except (ValueError, IndexError):
        subtitle = client_name

    all_slides: list[SlideContent] = []

    # Title slide
    all_slides.append(SlideContent(
        slide_type="title",
        title=f"SLIDE SAMPLER\n{subtitle}",
        layout_index=0,
    ))

    # Summary slide showing section counts
    summary_lines = []
    for section_key in SECTION_ORDER:
        results = sections.get(section_key, [])
        if results:
            label = _SECTION_LABELS.get(section_key, section_key.title())
            summary_lines.append(f"{label}: {len(results)} variants")

    other = sections.get("other", [])
    if other:
        summary_lines.append(f"Other/Uncategorized: {len(other)} variants")

    total = sum(len(v) for v in sections.values())
    summary_lines.insert(0, f"TOTAL: {total} slide variants across {len([s for s in sections if sections[s]])} sections\n")

    all_slides.append(SlideContent(
        slide_type="section",
        title="\n".join(summary_lines),
        layout_index=LAYOUT_SECTION,
    ))

    # For each section, show all variants
    for section_key in SECTION_ORDER:
        results = sections.get(section_key, [])
        if not results:
            continue

        label = _SECTION_LABELS.get(section_key, section_key.title())

        # Section header
        all_slides.append(SlideContent(
            slide_type="section",
            title=f"SECTION: {label}\n{len(results)} variants to review\n\nPick your favorites from the following slides.",
            layout_index=LAYOUT_SECTION,
        ))

        # Each variant: label + actual slide
        for i, result in enumerate(results):
            # Label slide with metadata
            all_slides.append(_label_slide(section_key, i, len(results), result))

            # Actual rendered slide
            sc = _result_to_slide(result, ctx_results=_ctx_results)
            if sc:
                all_slides.append(sc)

    # Handle "other" section
    other = sections.get("other", [])
    if other:
        all_slides.append(SlideContent(
            slide_type="section",
            title=f"UNCATEGORIZED\n{len(other)} variants",
            layout_index=LAYOUT_SECTION,
        ))
        for i, result in enumerate(other):
            all_slides.append(_label_slide("other", i, len(other), result))
            sc = _result_to_slide(result, ctx_results=_ctx_results)
            if sc:
                all_slides.append(sc)

    # Build the PPTX
    output_dir = ctx.paths.pptx_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{ctx.client.client_id}_{ctx.client.month}_SAMPLER.pptx"

    try:
        builder = DeckBuilder(str(template))
        builder.build(all_slides, str(output_path))
        logger.info(
            "Sample deck built: {path} ({n} slides)",
            path=output_path.name,
            n=len(all_slides),
        )
        print(f"\n  SAMPLER: {output_path}")
        print(f"  Slides:  {len(all_slides)} ({total} variants + labels + dividers)")
        print(f"  Review each section, note which option numbers you want to keep.\n")
        return output_path
    except Exception as exc:
        logger.error("Sample deck build failed: {err}", err=exc)
        return None


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import argparse
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    parser = argparse.ArgumentParser(description="Build a sample/review deck showing all slide variants")
    parser.add_argument("--month", required=True, help="Month in YYYY.MM format")
    parser.add_argument("--csm", required=True, help="CSM name")
    parser.add_argument("--client", required=True, help="Client ID")
    args = parser.parse_args()

    # Run the pipeline up to analysis (no deck generation), then build sampler
    from ars_analysis.pipeline.runner import run_pipeline
    from ars_analysis.pipeline.context import PipelineContext

    print(f"\n  Running analysis for {args.client} ({args.month})...")
    print(f"  This may take several minutes.\n")

    ctx = PipelineContext(
        client_id=args.client,
        month=args.month,
        csm=args.csm,
    )

    # Run analysis steps (skip deck generation)
    run_pipeline(ctx, skip_generate=True)

    if not ctx.all_slides:
        print("  ERROR: No analysis results produced. Cannot build sampler.")
        sys.exit(1)

    # Build sampler deck
    result = build_sample_deck(ctx)
    if result:
        print(f"  Done! Open the PPTX and review each section.")
    else:
        print("  ERROR: Sample deck build failed.")
        sys.exit(1)
