"""Quick layout preview -- generates a test PPTX in seconds.

No data loading, no analysis, no charts. Uses dummy content to test
template layouts, fonts, and placeholder positions.

Usage:
    python preview.py
    python preview.py --template "M:\ARS\02_Presentations\2025-CSI-PPT-Template.pptx"
    python preview.py --output preview_test.pptx
"""

import argparse
import glob
import os
import sys
from pathlib import Path

# Add 00-Scripts to path
sys.path.insert(0, str(Path(__file__).parent / "00-Scripts"))

# Create ars_analysis package alias
import types
_ars_pkg = types.ModuleType("ars_analysis")
_ars_pkg.__path__ = [str(Path(__file__).parent / "00-Scripts")]
sys.modules["ars_analysis"] = _ars_pkg

from output.deck_builder import (
    DeckBuilder,
    SlideContent,
    LAYOUT_TITLE_RPE,
    LAYOUT_SECTION_ALT,
    LAYOUT_CUSTOM,
    LAYOUT_CONTENT,
    LAYOUT_TITLE_DARK,
    LAYOUT_MAIL_SUMMARY,
    LAYOUT_TWO_CONTENT,
)


def _dummy_chart(output_dir: Path, name: str = "dummy_chart.png") -> str:
    """Create a simple placeholder chart image."""
    try:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(13, 7))
        ax.bar(["Category A", "Category B", "Category C", "Category D"],
               [42, 28, 35, 19], color=["#1B365D", "#0D9488", "#F39C12", "#95A5A6"])
        ax.set_ylabel("Value")
        path = output_dir / name
        fig.savefig(path, dpi=100, bbox_inches="tight")
        plt.close(fig)
        return str(path)
    except ImportError:
        return ""


def build_preview(template_path: str, output_path: str):
    """Build a preview PPTX with one slide per layout type."""

    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create dummy chart
    chart = _dummy_chart(output_dir, "preview_chart.png")

    slides = [
        # --- PREAMBLE SLIDES ---

        # P01: Master title (LAYOUT_TITLE_RPE = 17)
        SlideContent(
            slide_type="title",
            title="FIRST COMMUNITY BANK\nAccount Revenue Solution | March 2026",
            layout_index=LAYOUT_TITLE_RPE,
        ),

        # P02: Agenda (LAYOUT_CONTENT = 2)
        SlideContent(
            slide_type="blank",
            title="Agenda",
            layout_index=LAYOUT_CONTENT,
        ),

        # P03: Divider (LAYOUT_SECTION_ALT = 5)
        SlideContent(
            slide_type="title",
            title="FIRST COMMUNITY BANK\nProgram Performance | March 2026",
            layout_index=LAYOUT_SECTION_ALT,
        ),

        # P04: Executive Summary (LAYOUT_CUSTOM = 8)
        SlideContent(
            slide_type="blank",
            title="Executive Summary",
            layout_index=LAYOUT_CUSTOM,
        ),

        # P05: Monthly Revenue (LAYOUT_CUSTOM = 8)
        SlideContent(
            slide_type="blank",
            title="Monthly Revenue \u2013 Last 12 Months",
            layout_index=LAYOUT_CUSTOM,
        ),

        # P07: Mailer Revisit divider (LAYOUT_SECTION_ALT = 5)
        SlideContent(
            slide_type="title",
            title="FIRST COMMUNITY BANK\nARS Mailer Revisit | March 2026",
            layout_index=LAYOUT_SECTION_ALT,
        ),

        # P13: Data Check Overview (LAYOUT_CUSTOM = 8)
        SlideContent(
            slide_type="blank",
            title="Data Check Overview\nOur goal is turning non-users and light-users into heavy users",
            layout_index=LAYOUT_CUSTOM,
        ),

        # --- SECTION DIVIDER ---

        SlideContent(
            slide_type="section",
            title="How Effective Are the Mailer Campaigns?\nFIRST COMMUNITY BANK | March 2026",
            layout_index=LAYOUT_SECTION_ALT,
        ),

        # --- MAILER SUMMARY (LAYOUT_MAIL_SUMMARY = 20) ---

        SlideContent(
            slide_type="mailer_summary",
            title="ARS Response -- January 2026 Mailer Summary",
            images=[chart] if chart else None,
            kpis={"Mailed": "5,661", "Responded": "383", "Rate": "6.8%"},
            bullets=[
                "The January 2026 mailer reached 5,661 accounts with a 6.8% response rate (383 responders). TH-25 led with the highest response rate at 16.2%, while TH-10 contributed the most responders (109). This is a 1.2pp improvement over the prior mailer.",
                "36%|of Responders were accounts opened fewer than 2 years ago",
                "27%|of Responders aged 30-45",
                "32%|of Responders opted into Reg E",
                "41%|First-time responders",
            ],
            layout_index=LAYOUT_MAIL_SUMMARY,
        ),

        # --- SPEND/SWIPE (LAYOUT_MAIL_SUMMARY = 20) ---

        SlideContent(
            slide_type="screenshot",
            title="ARS Mailer Revisit \u2013 Swipes",
            images=[chart] if chart else None,
            layout_index=LAYOUT_MAIL_SUMMARY,
        ),

        SlideContent(
            slide_type="screenshot",
            title="ARS Mailer Revisit \u2013 Spend",
            images=[chart] if chart else None,
            layout_index=LAYOUT_MAIL_SUMMARY,
        ),

        # --- REGULAR ANALYSIS SLIDE (LAYOUT_CUSTOM = 8) ---

        SlideContent(
            slide_type="screenshot",
            title="Debit Card Penetration: 34.2% of eligible accounts actively use their debit card",
            images=[chart] if chart else None,
            layout_index=LAYOUT_CUSTOM,
        ),

        # --- SCREENSHOT WITH KPI ---

        SlideContent(
            slide_type="screenshot_kpi",
            title="Attrition Profile\n1,245 accounts closed this period",
            images=[chart] if chart else None,
            kpis={
                "Closed": "1,245",
                "Rate": "3.8%",
                "Revenue Lost": "$142K",
            },
            layout_index=LAYOUT_CUSTOM,
        ),

        # --- SUMMARY ---

        SlideContent(
            slide_type="section",
            title="Summary & Key Takeaways",
            layout_index=LAYOUT_SECTION_ALT,
        ),
    ]

    builder = DeckBuilder(template_path)
    builder.build(slides, output_path)
    print(f"Preview built: {output_path} ({len(slides)} slides)")


def main():
    parser = argparse.ArgumentParser(description="Quick layout preview")
    parser.add_argument("--template", type=str, default=None,
                        help="Path to PPTX template")
    parser.add_argument("--output", type=str, default=None,
                        help="Output PPTX path")
    args = parser.parse_args()

    # Find template
    template = args.template
    if not template:
        if os.name == "nt":
            candidates = glob.glob(r"M:\ARS\02_Presentations\*Template*.pptx")
        else:
            candidates = glob.glob("/Volumes/M/ARS/02_Presentations/*Template*.pptx")
        if candidates:
            template = candidates[0]
        else:
            # Fallback to embedded template
            fallback = Path(__file__).parent / "00-Scripts" / "output" / "template" / "2025-CSI-PPT-Template.pptx"
            if fallback.exists():
                template = str(fallback)

    if not template or not Path(template).exists():
        print(f"ERROR: Template not found. Use --template to specify.")
        sys.exit(1)

    print(f"Template: {template}")

    output = args.output or str(Path(__file__).parent / "preview_test.pptx")
    build_preview(template, output)


if __name__ == "__main__":
    main()
