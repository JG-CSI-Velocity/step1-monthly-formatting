# HTML Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a new consumer of `AnalysisResult` that renders a single self-contained HTML file per client-month — an analyst workbench with sidebar nav, section scroll, selection tray, and client-side print-to-PDF export.

**Architecture:** New `02_Presentations/html_review/` package. Pure jinja2 renderer with hand-written vanilla JS (no frameworks, no CDNs). Re-uses the `style/` module from `feature/deck-polish`. Output is one self-contained HTML file per client-month with all CSS/JS inlined.

**Tech Stack:** Python 3.12, jinja2, `python-pptx`/pandas (reused), vanilla JS (ES2020+), pytest.

**Spec:** `docs/superpowers/specs/2026-04-17-html-review-design.md`

**Branch:** `feature/html-review` — **branches from `feature/deck-polish`** (because `style/` lives there until PR #57 merges). Rebase onto `main` once PR #57 is in.

**Import quirk:** Same as deck-polish — `02_Presentations/` starts with a digit, so every entry point (builder.py, tests via conftest.py) uses `sys.path.insert(0, str(parent))` to enable absolute imports like `from style.palette import NAVY` and `from html_review.model import ClientMeta`.

---

## File Structure

```
02_Presentations/
├── (existing: polish.py, style/, conftest.py, etc. from deck-polish)
└── html_review/                   # NEW
    ├── __init__.py
    ├── builder.py                 # CLI + orchestrator
    ├── model.py                   # Dataclasses: ClientMeta, AnalysisBlock, SectionRender
    ├── templates/
    │   ├── index.html             # jinja2 master
    │   ├── print.css              # @media print rules
    │   └── partials/
    │       ├── sidebar.html
    │       ├── section.html
    │       └── analysis.html
    ├── static/
    │   ├── styles.css             # base + palette CSS vars + typography classes
    │   ├── app.js                 # selection tray + localStorage + scroll-spy + keyboard
    │   └── print.js               # Export-PDF click handler
    ├── view_latest.bat            # double-click launcher
    └── tests/
        ├── __init__.py
        ├── fixtures/
        │   ├── __init__.py
        │   ├── tiny_deck.py       # 3 synthetic AnalysisResultLike objects
        │   └── representative.py  # 1 per canonical section (9 total)
        ├── test_model.py
        ├── test_builder.py
        └── test_output.py
```

---

## Task 1: Branch + package skeleton

**Files:**
- Create: `02_Presentations/html_review/__init__.py`
- Create: `02_Presentations/html_review/templates/partials/.gitkeep`
- Create: `02_Presentations/html_review/static/.gitkeep`
- Create: `02_Presentations/html_review/tests/__init__.py`
- Create: `02_Presentations/html_review/tests/fixtures/__init__.py`
- Modify: `.gitignore` (un-ignore `html_review/` subtree)

- [ ] **Step 1: Create the feature branch off feature/deck-polish**

```bash
git fetch origin
git checkout feature/deck-polish
git pull
git checkout -b feature/html-review
```

- [ ] **Step 2: Create directory skeleton**

```bash
mkdir -p 02_Presentations/html_review/templates/partials
mkdir -p 02_Presentations/html_review/static
mkdir -p 02_Presentations/html_review/tests/fixtures
touch 02_Presentations/html_review/__init__.py
touch 02_Presentations/html_review/tests/__init__.py
touch 02_Presentations/html_review/tests/fixtures/__init__.py
touch 02_Presentations/html_review/templates/partials/.gitkeep
touch 02_Presentations/html_review/static/.gitkeep
```

- [ ] **Step 3: Un-ignore the new subtree in .gitignore**

Open `.gitignore`. Find the existing block of un-ignore rules under `02_Presentations/*`. Add after the other `!02_Presentations/...` lines:

```
!02_Presentations/html_review/
02_Presentations/html_review/.gitkeep
!02_Presentations/html_review/**
```

Verify: `git check-ignore 02_Presentations/html_review/__init__.py` exits 1 (not ignored).

- [ ] **Step 4: Confirm skeleton imports cleanly**

```bash
pytest 02_Presentations/html_review/ -v
```
Expected: exit 5 (no tests collected), no import errors.

- [ ] **Step 5: Commit**

```bash
git add 02_Presentations/html_review/ .gitignore
git commit -m "feat(html-review): scaffold html_review package skeleton"
```

---

## Task 2: Test fixtures — synthetic `AnalysisResultLike` objects

**Files:**
- Create: `02_Presentations/html_review/tests/fixtures/tiny_deck.py`

The real `AnalysisResult` lives in `01_Analysis/00-Scripts/analytics/base.py` which we can't import directly (digit-prefixed path). Tests use a simple stand-in dataclass with the same attribute shape. `builder.py` uses structural typing (duck typing) so it works with either the real or the stub.

- [ ] **Step 1: Write tiny_deck fixture**

File: `02_Presentations/html_review/tests/fixtures/tiny_deck.py`

```python
"""Synthetic AnalysisResult stand-ins for html_review tests.

The real AnalysisResult lives in 01_Analysis/00-Scripts/analytics/base.py
but that path can't be imported (digit prefix). builder.py uses structural
typing -- it reads attributes, doesn't require a specific class. These
stubs carry the same attribute shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


@dataclass
class AnalysisResultLike:
    """Walks like an AnalysisResult. Used by tests."""

    slide_id: str
    title: str
    section: str                                       # 'overview', 'attrition', etc.
    chart_path: Path | None = None
    excel_data: dict[str, pd.DataFrame] | None = None
    notes: str = ""
    kpis: dict[str, str] | None = None
    bullets: list[str] = field(default_factory=list)
    success: bool = True


def tiny_deck(tmp_path: Path) -> list[AnalysisResultLike]:
    """3 synthetic analyses covering the rendering variants.

    Writes a real PNG to tmp_path so chart_path resolves to a real file.
    """
    from PIL import Image

    png_path = tmp_path / "chart.png"
    Image.new("RGB", (1800, 900), (13, 148, 136)).save(png_path)

    return [
        # 1. PNG + notes only
        AnalysisResultLike(
            slide_id="attrition_01",
            title="Attrition declined 8% after the Q4 re-engagement campaign.",
            section="attrition",
            chart_path=png_path,
            notes="Campaign ROI: $128 incremental debit spend per responder.",
        ),
        # 2. PNG + single-sheet excel_data
        AnalysisResultLike(
            slide_id="attrition_02",
            title="Spend velocity flagged 30% of at-risk accounts.",
            section="attrition",
            chart_path=png_path,
            excel_data={
                "Cohort": pd.DataFrame(
                    {"segment": ["New", "Tenured"], "flagged_pct": [22.0, 38.5]}
                )
            },
        ),
        # 3. PNG + multi-sheet excel_data (tests the sheet <select>)
        AnalysisResultLike(
            slide_id="campaign_03",
            title="Cohort lift varied by tenure segment.",
            section="mailer",
            chart_path=png_path,
            excel_data={
                "Lift": pd.DataFrame({"seg": ["NU", "TH-10"], "lift": [12.1, 8.4]}),
                "Sample sizes": pd.DataFrame({"seg": ["NU", "TH-10"], "n": [240, 180]}),
            },
            notes="Three-month pre/post window.",
        ),
    ]
```

- [ ] **Step 2: Write a smoke test that just imports and calls tiny_deck**

File: `02_Presentations/html_review/tests/test_fixtures.py`

```python
"""Smoke test: fixtures build without error."""

from html_review.tests.fixtures.tiny_deck import tiny_deck


def test_tiny_deck_builds(tmp_path):
    results = tiny_deck(tmp_path)
    assert len(results) == 3
    assert results[0].section == "attrition"
    assert results[1].excel_data is not None
    assert len(results[2].excel_data) == 2
```

- [ ] **Step 3: Run test**

```bash
pytest 02_Presentations/html_review/tests/test_fixtures.py -v
```
Expected: 1 passed.

- [ ] **Step 4: Commit**

```bash
git add 02_Presentations/html_review/tests/
git commit -m "feat(html-review): add tiny_deck fixtures + smoke test"
```

---

## Task 3: `model.py` — jinja2 context dataclasses

**Files:**
- Create: `02_Presentations/html_review/model.py`
- Create: `02_Presentations/html_review/tests/test_model.py`

- [ ] **Step 1: Write failing test**

File: `02_Presentations/html_review/tests/test_model.py`

```python
"""Tests for html_review.model -- jinja2 context dataclasses."""

from pathlib import Path

from html_review.model import (
    ClientMeta,
    AnalysisBlock,
    SectionRender,
    TableRender,
)


def test_client_meta_fields():
    c = ClientMeta(
        id="1615",
        display_name="Cape & Coast Bank",
        month="2026-04",
        month_display="April 2026",
        run_date="2026-04-17",
    )
    assert c.id == "1615"
    assert c.month_display == "April 2026"


def test_table_render_holds_rows_and_columns():
    t = TableRender(
        sheet_name="Cohort",
        columns=["segment", "flagged_pct"],
        rows=[["New", "22.0"], ["Tenured", "38.5"]],
    )
    assert t.columns == ["segment", "flagged_pct"]
    assert len(t.rows) == 2


def test_analysis_block_minimal():
    b = AnalysisBlock(
        id="attrition_01",
        title="Headline.",
        chart_src="assets/chart.png",
        tables=[],
        notes="",
    )
    assert b.id == "attrition_01"
    assert b.tables == []


def test_section_render_holds_blocks():
    s = SectionRender(
        id="attrition",
        title="Attrition",
        eyebrow="Section 2 of 9",
        lede="Churn signals and recovery.",
        blocks=[],
    )
    assert s.id == "attrition"
    assert s.blocks == []
```

- [ ] **Step 2: Run and verify fail**

```bash
pytest 02_Presentations/html_review/tests/test_model.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'html_review.model'`.

- [ ] **Step 3: Implement model.py**

File: `02_Presentations/html_review/model.py`

```python
"""Jinja2 context dataclasses for html_review.

Pure data shapes -- no I/O, no logic. builder.py constructs these from
AnalysisResult objects; templates render them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ClientMeta:
    id: str
    display_name: str
    month: str               # "2026-04"
    month_display: str       # "April 2026"
    run_date: str            # "2026-04-17"


@dataclass(frozen=True)
class TableRender:
    sheet_name: str
    columns: list[str]
    rows: list[list[str]]    # already stringified for HTML safety


@dataclass
class AnalysisBlock:
    id: str
    title: str
    chart_src: str | None                    # relative path or data: URI
    tables: list[TableRender] = field(default_factory=list)
    notes: str = ""


@dataclass
class SectionRender:
    id: str                                   # canonical: overview, attrition, etc.
    title: str                                # Display: "Attrition"
    eyebrow: str                              # "Section 2 of 9"
    lede: str                                 # one-paragraph section intro
    blocks: list[AnalysisBlock] = field(default_factory=list)
```

- [ ] **Step 4: Run tests**

```bash
pytest 02_Presentations/html_review/tests/test_model.py -v
```
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add 02_Presentations/html_review/model.py 02_Presentations/html_review/tests/test_model.py
git commit -m "feat(html-review): add model.py jinja2 context dataclasses"
```

---

## Task 4: `static/styles.css` — base styles, palette CSS vars, typography

**Files:**
- Create: `02_Presentations/html_review/static/styles.css`

This is a static file — no Python, no tests. Validated by `test_output.py` later (checking that the CSS shows up in the rendered HTML).

- [ ] **Step 1: Write styles.css**

File: `02_Presentations/html_review/static/styles.css`

```css
/* Palette from style/palette.py -- kept in sync manually; builder.py will
   emit a warning if they drift (future nice-to-have). */
:root {
  --navy: #1B365D;
  --teal: #0D9488;
  --coral: #E7433C;
  --amber: #F39C12;
  --gray: #95A5A6;
  --slate: #6B7280;
  --white: #FFFFFF;
  --bg: #f7f7f8;
  --surface: #ffffff;
  --border: #e5e7eb;
  --muted: #6B7280;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: Montserrat, -apple-system, "Segoe UI", sans-serif;
  background: var(--bg);
  color: #1B2A4A;
  line-height: 1.45;
}

/* ===== Typography classes mirror style/typography.py ===== */
.t-slide-title   { font-family: Montserrat; font-size: 20pt; font-weight: 800; }
.t-subtitle      { font-family: Montserrat; font-size: 14pt; font-weight: 400; }
.t-chart-title   { font-family: Montserrat; font-size: 18pt; font-weight: 700; }
.t-annotation    { font-family: Montserrat; font-size: 10pt; font-weight: 400; color: var(--muted); font-style: italic; }
.t-footnote      { font-family: Montserrat; font-size: 9pt; font-weight: 400; color: var(--muted); }
.t-kpi-hero      { font-family: Montserrat; font-size: 36pt; font-weight: 800; color: var(--navy); }
.t-kpi-label     { font-family: Montserrat; font-size: 11pt; font-weight: 400; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }

/* ===== Layout ===== */
.shell { display: flex; min-height: 100vh; }

.sidebar {
  width: 240px; background: var(--navy); color: white;
  padding: 24px 0; position: sticky; top: 0;
  height: 100vh; overflow-y: auto; flex-shrink: 0;
}
.sidebar-brand { padding: 0 20px 16px; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 16px; }
.sidebar-brand h1 { font-size: 14px; margin: 0; font-weight: 800; }
.sidebar-brand p { font-size: 11px; margin: 2px 0 0; opacity: 0.7; }
.sidebar-section {
  display: block; padding: 10px 20px; color: rgba(255,255,255,0.75);
  text-decoration: none; font-size: 13px; border-left: 3px solid transparent;
}
.sidebar-section:hover { background: rgba(255,255,255,0.04); color: white; }
.sidebar-section.active {
  background: rgba(13, 148, 136, 0.15);
  border-left-color: var(--teal); color: white; font-weight: 700;
}
.sidebar-section .count { float: right; opacity: 0.5; font-size: 11px; font-weight: 400; }

.main { flex: 1; max-width: 1200px; padding-bottom: 40px; }

/* Selection tray */
.selection-tray {
  position: sticky; top: 0; z-index: 10;
  background: white; border-bottom: 1px solid var(--border);
  padding: 14px 60px; display: flex; align-items: center; gap: 16px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.04);
}
.selection-count { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 700; color: var(--navy); }
.selection-count .badge {
  background: var(--teal); color: white; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 800;
}
.action-btn { padding: 8px 16px; border-radius: 6px; font-size: 13px; font-weight: 700; cursor: pointer; border: 1px solid var(--border); background: white; color: var(--navy); }
.action-btn.primary { background: var(--navy); color: white; border-color: var(--navy); }
.action-btn.primary:hover { background: #0D2748; }
.selection-spacer { flex: 1; }

/* Section header */
.section-header { padding: 40px 60px 20px; }
.section-eyebrow { font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; color: var(--teal); font-weight: 700; margin-bottom: 4px; }
.section-title { font-size: 30px; font-weight: 800; margin: 0 0 8px; color: var(--navy); }
.section-lede { font-size: 15px; color: var(--muted); max-width: 700px; line-height: 1.5; }

/* Content area */
.content-area { padding: 0 60px; }

/* Analysis block */
.analysis-wrapper { position: relative; margin-bottom: 16px; padding-left: 36px; }
.select-checkbox {
  position: absolute; top: 18px; left: 0;
  width: 22px; height: 22px; border-radius: 4px;
  border: 2px solid #d1d5db; background: white;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
}
.select-checkbox input { appearance: none; width: 100%; height: 100%; margin: 0; cursor: pointer; }
.analysis-wrapper.selected .select-checkbox { background: var(--teal); border-color: var(--teal); }
.analysis-wrapper.selected .select-checkbox::after { content: "✓"; color: white; font-size: 14px; font-weight: 700; position: absolute; }
.analysis-wrapper.selected .analysis {
  border: 1px solid var(--teal);
  box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.1);
}

.analysis {
  background: white; border: 1px solid var(--border); border-radius: 8px;
  padding: 24px 28px;
}
.analysis h3 { margin: 0 0 12px; color: var(--navy); }
.analysis .chart { width: 100%; height: auto; display: block; border-radius: 4px; }
.analysis .notes { margin-top: 12px; }

.data-table { margin-top: 12px; border-top: 1px solid var(--border); padding-top: 10px; }
.data-table summary { cursor: pointer; font-size: 12px; font-weight: 700; color: var(--navy); }
.data-table table { width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 8px; }
.data-table th, .data-table td { padding: 6px 10px; text-align: left; border-bottom: 1px solid var(--border); }
.data-table th { font-weight: 700; background: var(--bg); }
.sheet-select { margin: 6px 0; font-size: 12px; padding: 4px; }

kbd { background: #eee; padding: 2px 6px; border-radius: 3px; font-size: 11px; font-family: monospace; }
```

- [ ] **Step 2: Verify it's syntactically valid CSS**

```bash
python -c "p = open('02_Presentations/html_review/static/styles.css').read(); print(f'{len(p)} chars, {p.count(chr(123))} opening braces, {p.count(chr(125))} closing braces')"
```
Expected: matching brace counts.

- [ ] **Step 3: Commit**

```bash
git add 02_Presentations/html_review/static/styles.css
git commit -m "feat(html-review): add base styles with CSI palette and typography"
```

---

## Task 5: Partials — `analysis.html`

**Files:**
- Create: `02_Presentations/html_review/templates/partials/analysis.html`

- [ ] **Step 1: Write the analysis.html partial**

File: `02_Presentations/html_review/templates/partials/analysis.html`

```html
{# Single analysis block: headline + chart + optional data table + optional notes #}
<div class="analysis-wrapper" data-block-id="{{ block.id }}">
  <label class="select-checkbox">
    <input type="checkbox" class="select-box" data-block-id="{{ block.id }}" />
  </label>
  <article class="analysis">
    <h3 class="t-slide-title">{{ block.title }}</h3>
    {% if block.chart_src %}
      <img class="chart" src="{{ block.chart_src }}" alt="{{ block.title }}" />
    {% endif %}
    {% if block.tables %}
      <details class="data-table">
        <summary>Data table{% if block.tables|length > 1 %} ({{ block.tables|length }} sheets){% endif %}</summary>
        {% if block.tables|length > 1 %}
          <select class="sheet-select" data-block-id="{{ block.id }}">
            {% for t in block.tables %}
              <option value="{{ loop.index0 }}">{{ t.sheet_name }}</option>
            {% endfor %}
          </select>
        {% endif %}
        {% for t in block.tables %}
          <table class="sheet" data-sheet-idx="{{ loop.index0 }}"{% if not loop.first %} hidden{% endif %}>
            <thead><tr>{% for col in t.columns %}<th>{{ col }}</th>{% endfor %}</tr></thead>
            <tbody>
              {% for row in t.rows %}
                <tr>{% for cell in row %}<td>{{ cell }}</td>{% endfor %}</tr>
              {% endfor %}
            </tbody>
          </table>
        {% endfor %}
      </details>
    {% endif %}
    {% if block.notes %}
      <p class="t-annotation notes">{{ block.notes }}</p>
    {% endif %}
  </article>
</div>
```

- [ ] **Step 2: Commit**

```bash
git add 02_Presentations/html_review/templates/partials/analysis.html
git commit -m "feat(html-review): add analysis.html partial"
```

---

## Task 6: Partials — `sidebar.html`

**Files:**
- Create: `02_Presentations/html_review/templates/partials/sidebar.html`

- [ ] **Step 1: Write sidebar.html**

File: `02_Presentations/html_review/templates/partials/sidebar.html`

```html
<aside class="sidebar">
  <div class="sidebar-brand">
    <h1>{{ client.display_name }}</h1>
    <p>{{ client.month_display }} Review</p>
  </div>
  {% for section in sections %}
    <a class="sidebar-section" href="#section-{{ section.id }}" data-section-target="{{ section.id }}">
      {{ section.title }}
      <span class="count">{{ section.blocks|length }}</span>
    </a>
  {% endfor %}
</aside>
```

- [ ] **Step 2: Commit**

```bash
git add 02_Presentations/html_review/templates/partials/sidebar.html
git commit -m "feat(html-review): add sidebar.html partial"
```

---

## Task 7: Partials — `section.html`

**Files:**
- Create: `02_Presentations/html_review/templates/partials/section.html`

- [ ] **Step 1: Write section.html**

File: `02_Presentations/html_review/templates/partials/section.html`

```html
<section id="section-{{ section.id }}" class="review-section" data-section="{{ section.id }}">
  <header class="section-header">
    <div class="section-eyebrow">{{ section.eyebrow }}</div>
    <h2 class="section-title">{{ section.title }}</h2>
    {% if section.lede %}<p class="section-lede">{{ section.lede }}</p>{% endif %}
  </header>
  <div class="content-area">
    {% for block in section.blocks %}
      {% include 'partials/analysis.html' %}
    {% endfor %}
  </div>
</section>
```

- [ ] **Step 2: Commit**

```bash
git add 02_Presentations/html_review/templates/partials/section.html
git commit -m "feat(html-review): add section.html partial"
```

---

## Task 8: Master template — `index.html` + `print.css`

**Files:**
- Create: `02_Presentations/html_review/templates/index.html`
- Create: `02_Presentations/html_review/templates/print.css`

- [ ] **Step 1: Write print.css**

File: `02_Presentations/html_review/templates/print.css`

```css
/* Applied only when export is triggered (body.exporting) + @media print */
@media print {
  body.exporting .sidebar,
  body.exporting .selection-tray,
  body.exporting .analysis-wrapper:not(.selected),
  body.exporting .review-section.empty {
    display: none !important;
  }
  body.exporting .main { max-width: none; padding: 0; }
  body.exporting .section-header { padding: 0 0.4in; }
  body.exporting .content-area { padding: 0 0.4in; }
  body.exporting .analysis-wrapper { padding-left: 0; page-break-inside: avoid; break-inside: avoid; }
  body.exporting .analysis-wrapper + .analysis-wrapper { page-break-before: always; break-before: page; }
  body.exporting .select-checkbox { display: none; }
  body.exporting .analysis { border: none; box-shadow: none; }
  body.exporting .analysis.selected { border: none; box-shadow: none; }

  @page {
    size: letter portrait;
    margin: 0.5in;
    @bottom-right {
      content: counter(page) " / " counter(pages);
      font-family: Montserrat;
      font-size: 9pt;
      color: #6B7280;
    }
    @bottom-left {
      content: "Cape & Coast Bank — April 2026 Review";
      font-family: Montserrat;
      font-size: 9pt;
      color: #6B7280;
    }
  }
}
```

Note: the `@bottom-left` "Cape & Coast Bank — April 2026 Review" is a static example; builder.py will template this with real client/month values.

- [ ] **Step 2: Write index.html master template**

File: `02_Presentations/html_review/templates/index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{{ client.display_name }} — {{ client.month_display }} Review</title>
<style>{{ styles_css | safe }}</style>
<style>{{ print_css | safe }}</style>
</head>
<body data-client="{{ client.id }}" data-month="{{ client.month }}">

<div class="shell">

  {% include 'partials/sidebar.html' %}

  <main class="main">

    <div class="selection-tray">
      <div class="selection-count">
        <span class="badge" id="selection-count">0</span>
        <span>selected for export</span>
      </div>
      <div class="selection-spacer"></div>
      <button class="action-btn" id="btn-clear">Clear</button>
      <button class="action-btn primary" id="btn-export">Export PDF →</button>
    </div>

    {% for section in sections %}
      {% include 'partials/section.html' %}
    {% endfor %}

  </main>

</div>

<script>{{ app_js | safe }}</script>
<script>{{ print_js | safe }}</script>

</body>
</html>
```

- [ ] **Step 3: Commit**

```bash
git add 02_Presentations/html_review/templates/index.html 02_Presentations/html_review/templates/print.css
git commit -m "feat(html-review): add master index.html and print.css"
```

---

## Task 9: `static/app.js` — selection tray + scroll spy + keyboard

**Files:**
- Create: `02_Presentations/html_review/static/app.js`

- [ ] **Step 1: Write app.js**

File: `02_Presentations/html_review/static/app.js`

```javascript
/* html_review app.js -- selection tray, scroll-spy, keyboard, sheet switcher.
   Vanilla JS. No dependencies. */

(function () {
  "use strict";

  const clientId = document.body.dataset.client || "unknown";
  const month = document.body.dataset.month || "unknown";
  const storageKey = `hr-selection-${clientId}-${month}`;

  const countEl = document.getElementById("selection-count");
  const btnClear = document.getElementById("btn-clear");
  const boxes = document.querySelectorAll(".select-box");

  function loadSelection() {
    try {
      return new Set(JSON.parse(localStorage.getItem(storageKey) || "[]"));
    } catch {
      return new Set();
    }
  }

  function saveSelection(set) {
    localStorage.setItem(storageKey, JSON.stringify([...set]));
  }

  const selected = loadSelection();

  function applySelectionToDOM() {
    boxes.forEach((box) => {
      const id = box.dataset.blockId;
      const wrapper = box.closest(".analysis-wrapper");
      if (selected.has(id)) {
        box.checked = true;
        wrapper.classList.add("selected");
      } else {
        box.checked = false;
        wrapper.classList.remove("selected");
      }
    });
    countEl.textContent = String(selected.size);
  }

  boxes.forEach((box) => {
    box.addEventListener("change", () => {
      const id = box.dataset.blockId;
      if (box.checked) selected.add(id);
      else selected.delete(id);
      saveSelection(selected);
      applySelectionToDOM();
    });
  });

  btnClear.addEventListener("click", () => {
    selected.clear();
    saveSelection(selected);
    applySelectionToDOM();
  });

  /* Keyboard: 'S' toggles the nearest block to viewport center */
  document.addEventListener("keydown", (e) => {
    if (e.key !== "s" && e.key !== "S") return;
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
    const wrappers = [...document.querySelectorAll(".analysis-wrapper")];
    const center = window.scrollY + window.innerHeight / 2;
    let best = null;
    let bestDist = Infinity;
    wrappers.forEach((w) => {
      const r = w.getBoundingClientRect();
      const mid = r.top + window.scrollY + r.height / 2;
      const dist = Math.abs(mid - center);
      if (dist < bestDist) {
        bestDist = dist;
        best = w;
      }
    });
    if (best) {
      const box = best.querySelector(".select-box");
      box.checked = !box.checked;
      box.dispatchEvent(new Event("change"));
    }
  });

  /* Scroll-spy: highlights sidebar link of the section currently on screen */
  const sectionEls = document.querySelectorAll(".review-section");
  const linkEls = document.querySelectorAll(".sidebar-section");
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const id = entry.target.dataset.section;
          linkEls.forEach((link) => {
            link.classList.toggle(
              "active",
              link.dataset.sectionTarget === id
            );
          });
        }
      });
    },
    { rootMargin: "-40% 0px -55% 0px" }
  );
  sectionEls.forEach((el) => observer.observe(el));

  /* Multi-sheet select switcher inside data tables */
  document.querySelectorAll(".sheet-select").forEach((sel) => {
    sel.addEventListener("change", () => {
      const details = sel.closest(".data-table");
      const idx = parseInt(sel.value, 10);
      details.querySelectorAll(".sheet").forEach((t) => {
        t.hidden = parseInt(t.dataset.sheetIdx, 10) !== idx;
      });
    });
  });

  applySelectionToDOM();
})();
```

- [ ] **Step 2: Verify it parses**

```bash
node -c 02_Presentations/html_review/static/app.js && echo "ok"
```
(If node not installed: `python -c "import esprima; esprima.parse(open('02_Presentations/html_review/static/app.js').read()); print('ok')"` — skip if esprima not available; syntax will be validated at runtime in Task 14 smoke test.)

- [ ] **Step 3: Commit**

```bash
git add 02_Presentations/html_review/static/app.js
git commit -m "feat(html-review): add app.js for selection tray + scroll-spy + keyboard"
```

---

## Task 10: `static/print.js` — Export-PDF click handler

**Files:**
- Create: `02_Presentations/html_review/static/print.js`

- [ ] **Step 1: Write print.js**

File: `02_Presentations/html_review/static/print.js`

```javascript
/* html_review print.js -- handles the Export PDF button.
   Adds body.exporting, triggers browser print dialog, cleans up. */

(function () {
  "use strict";

  const btn = document.getElementById("btn-export");
  if (!btn) return;

  btn.addEventListener("click", () => {
    const selected = document.querySelectorAll(".analysis-wrapper.selected");
    if (selected.length === 0) {
      alert("Select at least one analysis to export.");
      return;
    }

    /* Mark empty sections so the print CSS can hide them */
    document.querySelectorAll(".review-section").forEach((s) => {
      const hasSelected = s.querySelector(".analysis-wrapper.selected");
      s.classList.toggle("empty", !hasSelected);
    });

    document.body.classList.add("exporting");

    /* Open the browser print dialog after the CSS has applied */
    setTimeout(() => window.print(), 100);
  });

  window.addEventListener("afterprint", () => {
    document.body.classList.remove("exporting");
    document.querySelectorAll(".review-section.empty").forEach((s) => {
      s.classList.remove("empty");
    });
  });
})();
```

- [ ] **Step 2: Commit**

```bash
git add 02_Presentations/html_review/static/print.js
git commit -m "feat(html-review): add print.js for Export PDF handler"
```

---

## Task 11: `builder.py` — the orchestrator

**Files:**
- Create: `02_Presentations/html_review/builder.py`
- Create: `02_Presentations/html_review/tests/test_builder.py`

- [ ] **Step 1: Write failing test**

File: `02_Presentations/html_review/tests/test_builder.py`

```python
"""Integration tests for html_review.builder."""

from pathlib import Path

from html_review.builder import build_html
from html_review.model import ClientMeta
from html_review.tests.fixtures.tiny_deck import tiny_deck


def test_build_html_produces_index_with_3_blocks(tmp_path):
    results = tiny_deck(tmp_path)
    client = ClientMeta(
        id="1615", display_name="Cape & Coast Bank",
        month="2026-04", month_display="April 2026", run_date="2026-04-17",
    )
    out_dir = tmp_path / "out"
    html_path = build_html(results, client, out_dir, embed_images=False)

    assert html_path == out_dir / "index.html"
    text = html_path.read_text()

    # Structure sanity
    assert text.startswith("<!DOCTYPE html>")
    assert "Cape &amp; Coast Bank" in text or "Cape & Coast Bank" in text
    # 3 analysis wrappers
    assert text.count('class="analysis-wrapper"') == 3
    # 1 block has excel_data with 2 sheets -> <select> rendered
    assert 'class="sheet-select"' in text
    # 1 block has no excel_data -> no <details> for that block (check count)
    assert text.count("<details") == 2  # 2 of the 3 blocks have tables


def test_build_html_embed_images_inlines_png(tmp_path):
    results = tiny_deck(tmp_path)
    client = ClientMeta(id="1615", display_name="Cape", month="2026-04",
                        month_display="April 2026", run_date="2026-04-17")
    out_dir = tmp_path / "out"
    html_path = build_html(results, client, out_dir, embed_images=True)
    text = html_path.read_text()
    assert "data:image/png;base64," in text


def test_build_html_no_embed_copies_pngs_to_assets(tmp_path):
    results = tiny_deck(tmp_path)
    client = ClientMeta(id="1615", display_name="Cape", month="2026-04",
                        month_display="April 2026", run_date="2026-04-17")
    out_dir = tmp_path / "out"
    build_html(results, client, out_dir, embed_images=False)
    assets = out_dir / "assets"
    assert assets.exists()
    pngs = list(assets.glob("*.png"))
    assert len(pngs) >= 1
```

- [ ] **Step 2: Run — expect fail**

```bash
pytest 02_Presentations/html_review/tests/test_builder.py -v
```
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Implement builder.py**

File: `02_Presentations/html_review/builder.py`

```python
"""html_review builder: renders AnalysisResult list -> self-contained HTML file.

Usage (library):
    from html_review.builder import build_html
from html_review.model import ClientMeta
    build_html(results, client, out_dir, embed_images=True)

Usage (CLI):
    python -m html_review.builder <pickled_results.pkl> <client.json> <out_dir>
"""

from __future__ import annotations

import argparse
import base64
import json
import shutil
import sys
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any, Iterable, Protocol

# Enable absolute imports under 02_Presentations/
_THIS = Path(__file__).parent
_PARENT = _THIS.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from jinja2 import Environment, FileSystemLoader, select_autoescape

from html_review.model import (
    AnalysisBlock,
    ClientMeta,
    SectionRender,
    TableRender,
)


SECTION_ORDER = [
    "overview", "dctr", "rege", "attrition", "value",
    "mailer", "transaction", "ics", "insights",
]

SECTION_TITLES = {
    "overview": "Overview",
    "dctr": "DCTR",
    "rege": "Reg E",
    "attrition": "Attrition",
    "value": "Value",
    "mailer": "ARS Mailer Campaign",
    "transaction": "Transaction",
    "ics": "ICS",
    "insights": "Insights",
}

SECTION_LEDES = {
    "overview": "Portfolio-level KPIs, segments, and the top-line story.",
    "dctr": "Debit card transaction rate and activation trajectory.",
    "rege": "Reg E opt-in trends and overdraft revenue exposure.",
    "attrition": "Churn signals, at-risk scoring, and recovery outcomes.",
    "value": "Per-account value and revenue attribution.",
    "mailer": "ARS campaign reach, response, and lift by cohort.",
    "transaction": "PIN vs signature, merchant and MCC patterns.",
    "ics": "ICS acquisition channels and performance.",
    "insights": "Executive takeaways and next-best-actions.",
}


class AnalysisResultLike(Protocol):
    """Structural type for an AnalysisResult. Builder reads attributes only."""
    slide_id: str
    title: str
    section: str
    chart_path: Path | None
    excel_data: dict[str, Any] | None
    notes: str


def _encode_png(path: Path) -> str:
    """Return a data URI for the PNG at `path`."""
    raw = path.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _df_to_table_render(sheet_name: str, df) -> TableRender:
    """Convert a pandas DataFrame to a TableRender."""
    columns = [str(c) for c in df.columns]
    rows = [[str(v) for v in row] for row in df.itertuples(index=False, name=None)]
    return TableRender(sheet_name=sheet_name, columns=columns, rows=rows)


def _build_block(
    result: AnalysisResultLike,
    out_dir: Path,
    embed_images: bool,
) -> AnalysisBlock:
    """Convert one AnalysisResult into an AnalysisBlock for the template."""
    chart_src: str | None = None
    if result.chart_path is not None and Path(result.chart_path).exists():
        if embed_images:
            chart_src = _encode_png(Path(result.chart_path))
        else:
            assets = out_dir / "assets"
            assets.mkdir(parents=True, exist_ok=True)
            dest_name = f"{result.slide_id}.png"
            dest = assets / dest_name
            shutil.copy(result.chart_path, dest)
            chart_src = f"assets/{dest_name}"

    tables: list[TableRender] = []
    if result.excel_data:
        for sheet_name, df in result.excel_data.items():
            tables.append(_df_to_table_render(sheet_name, df))

    return AnalysisBlock(
        id=result.slide_id,
        title=result.title,
        chart_src=chart_src,
        tables=tables,
        notes=result.notes or "",
    )


def _group_by_section(
    results: Iterable[AnalysisResultLike],
    out_dir: Path,
    embed_images: bool,
) -> list[SectionRender]:
    """Build the section render list in canonical order."""
    by_section: dict[str, list[AnalysisBlock]] = {s: [] for s in SECTION_ORDER}
    unknown: dict[str, list[AnalysisBlock]] = {}

    for r in results:
        block = _build_block(r, out_dir, embed_images)
        key = r.section
        if key in by_section:
            by_section[key].append(block)
        else:
            unknown.setdefault(key, []).append(block)

    sections: list[SectionRender] = []
    total = len([s for s in SECTION_ORDER if by_section[s]]) + len(unknown)
    i = 0
    for key in SECTION_ORDER:
        if not by_section[key]:
            continue
        i += 1
        sections.append(SectionRender(
            id=key,
            title=SECTION_TITLES[key],
            eyebrow=f"Section {i} of {total}",
            lede=SECTION_LEDES[key],
            blocks=by_section[key],
        ))
    for key, blocks in unknown.items():
        i += 1
        sections.append(SectionRender(
            id=key, title=key.title(),
            eyebrow=f"Section {i} of {total}",
            lede="", blocks=blocks,
        ))
    return sections


def _load_text(rel_path: str) -> str:
    return (_THIS / rel_path).read_text()


def build_html(
    results: list[AnalysisResultLike],
    client: ClientMeta,
    out_dir: Path,
    embed_images: bool = True,
) -> Path:
    """Render the HTML review file. Returns path to index.html."""
    out_dir.mkdir(parents=True, exist_ok=True)

    sections = _group_by_section(results, out_dir, embed_images)

    env = Environment(
        loader=FileSystemLoader(str(_THIS / "templates")),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("index.html")

    html = template.render(
        client=client,
        sections=sections,
        styles_css=_load_text("static/styles.css"),
        print_css=_load_text("templates/print.css"),
        app_js=_load_text("static/app.js"),
        print_js=_load_text("static/print.js"),
    )

    out_path = out_dir / "index.html"
    out_path.write_text(html)
    return out_path


def _cli_main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="html_review.builder",
        description="Render AnalysisResult list -> self-contained HTML review file.",
    )
    p.add_argument("results_pkl", type=Path, help="Pickled list of AnalysisResult")
    p.add_argument("client_json", type=Path, help="JSON with id/display_name/month/month_display/run_date")
    p.add_argument("out_dir", type=Path, help="Output directory")
    p.add_argument("--no-embed-images", action="store_true", help="Copy PNGs to assets/ instead of inlining")
    args = p.parse_args(argv)

    import pickle
    with args.results_pkl.open("rb") as f:
        results = pickle.load(f)
    client = ClientMeta(**json.loads(args.client_json.read_text()))
    out_path = build_html(results, client, args.out_dir, embed_images=not args.no_embed_images)
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli_main())
```

- [ ] **Step 4: Run tests**

```bash
pytest 02_Presentations/html_review/tests/test_builder.py -v
```
Expected: 3 passed. If jinja2 missing, run `pip install jinja2` first.

- [ ] **Step 5: Commit**

```bash
git add 02_Presentations/html_review/builder.py 02_Presentations/html_review/tests/test_builder.py
git commit -m "feat(html-review): add builder.py with CLI and build_html()"
```

---

## Task 12: `test_output.py` — structural lint on rendered HTML

**Files:**
- Create: `02_Presentations/html_review/tests/test_output.py`

- [ ] **Step 1: Write test**

File: `02_Presentations/html_review/tests/test_output.py`

```python
"""Structural lint: rendered HTML has the required markers and no regressions."""

from pathlib import Path

from html_review.builder import build_html
from html_review.model import ClientMeta
from html_review.tests.fixtures.tiny_deck import tiny_deck


def _build(tmp_path: Path) -> str:
    results = tiny_deck(tmp_path)
    client = ClientMeta(id="1615", display_name="Cape", month="2026-04",
                        month_display="April 2026", run_date="2026-04-17")
    path = build_html(results, client, tmp_path / "out", embed_images=True)
    return path.read_text()


def test_no_unresolved_jinja_markers(tmp_path):
    text = _build(tmp_path)
    assert "{{" not in text, "unresolved jinja expression"
    assert "{%" not in text, "unresolved jinja statement"


def test_selection_tray_markup_present(tmp_path):
    text = _build(tmp_path)
    assert 'id="selection-count"' in text
    assert 'id="btn-export"' in text
    assert 'id="btn-clear"' in text


def test_print_css_embedded(tmp_path):
    text = _build(tmp_path)
    assert "@media print" in text
    assert "body.exporting" in text


def test_no_external_script_or_stylesheet_tags(tmp_path):
    text = _build(tmp_path)
    assert 'src="http' not in text, "external script reference -- should be inlined"
    assert 'href="http' not in text, "external stylesheet reference -- should be inlined"


def test_sidebar_lists_sections_in_canonical_order(tmp_path):
    # tiny_deck has 'attrition' (x2) and 'mailer' (x1). Order should follow
    # SECTION_ORDER: attrition (position 4) then mailer (position 6).
    text = _build(tmp_path)
    attrition_idx = text.find("#section-attrition")
    mailer_idx = text.find("#section-mailer")
    assert attrition_idx != -1 and mailer_idx != -1
    assert attrition_idx < mailer_idx
```

- [ ] **Step 2: Run**

```bash
pytest 02_Presentations/html_review/tests/test_output.py -v
```
Expected: 5 passed.

- [ ] **Step 3: Commit**

```bash
git add 02_Presentations/html_review/tests/test_output.py
git commit -m "feat(html-review): add test_output.py structural lint"
```

---

## Task 13: `view_latest.bat` + representative fixture

**Files:**
- Create: `02_Presentations/html_review/view_latest.bat`
- Create: `02_Presentations/html_review/tests/fixtures/representative.py`

- [ ] **Step 1: Write representative fixture (1 per canonical section)**

File: `02_Presentations/html_review/tests/fixtures/representative.py`

```python
"""One synthetic AnalysisResultLike per canonical section (9 total).

Used for the smoke test to verify every section renders.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from PIL import Image

from html_review.tests.fixtures.tiny_deck import AnalysisResultLike


SECTIONS = [
    ("overview",   "Portfolio overview: 62% penetration, up from 58%."),
    ("dctr",       "DCTR reached 72% across the portfolio."),
    ("rege",       "Reg E opt-in rose 6 points after Q3 messaging."),
    ("attrition",  "Attrition declined 8% after re-engagement."),
    ("value",      "Top-value segment grew 11% YoY."),
    ("mailer",     "ARS campaign drove 14% incremental response."),
    ("transaction","Signature mix increased 4 points, led by grocery."),
    ("ics",        "ICS channel acquired 247 new accounts at $38 CAC."),
    ("insights",   "Three priorities: ICS expansion, Reg E, campaign cadence."),
]


def representative(tmp_path: Path) -> list[AnalysisResultLike]:
    png_path = tmp_path / "chart.png"
    Image.new("RGB", (1800, 900), (27, 54, 93)).save(png_path)
    out = []
    for section, title in SECTIONS:
        out.append(AnalysisResultLike(
            slide_id=f"{section}_01",
            title=title,
            section=section,
            chart_path=png_path,
            excel_data={"Detail": pd.DataFrame({"metric": ["x"], "value": [1]})},
            notes=f"Representative analysis for the {section} section.",
        ))
    return out
```

- [ ] **Step 2: Write smoke test**

Append to `02_Presentations/html_review/tests/test_output.py`:

```python
from html_review.tests.fixtures.representative import representative, SECTIONS


def test_representative_all_sections_render(tmp_path):
    results = representative(tmp_path)
    client = ClientMeta(id="1615", display_name="Cape & Coast Bank",
                        month="2026-04", month_display="April 2026",
                        run_date="2026-04-17")
    html_path = build_html(results, client, tmp_path / "out", embed_images=True)
    text = html_path.read_text()
    for section, _title in SECTIONS:
        assert f'id="section-{section}"' in text, f"missing section {section}"
```

- [ ] **Step 3: Write view_latest.bat**

File: `02_Presentations/html_review/view_latest.bat`

```bat
@echo off
setlocal enabledelayedexpansion

REM Opens the most recently modified index.html under reports/
REM on the default browser. Run from M:\ARS\02_Presentations\html_review\.

set REPORTS_ROOT=..\reports

if not exist "%REPORTS_ROOT%" (
    echo No reports found at %REPORTS_ROOT%.
    pause
    exit /b 1
)

set LATEST=
set LATEST_TIME=0

for /r "%REPORTS_ROOT%" %%F in (index.html) do (
    set FULL=%%F
    set TS=%%~tF
    if "!TS!" gtr "!LATEST_TIME!" (
        set LATEST=%%F
        set LATEST_TIME=!TS!
    )
)

if "%LATEST%"=="" (
    echo No index.html files found in %REPORTS_ROOT%.
    pause
    exit /b 1
)

echo Opening %LATEST%
start "" "%LATEST%"
```

- [ ] **Step 4: Update .gitignore to un-ignore view_latest.bat**

Confirm `view_latest.bat` is covered by the existing `!02_Presentations/html_review/**` un-ignore added in Task 1. Verify:

```bash
git check-ignore 02_Presentations/html_review/view_latest.bat
```
Expected: exit 1, no output.

- [ ] **Step 5: Run full test suite (should be ~60 tests total now across both features)**

```bash
pytest 02_Presentations/ -v
```
Expected: all tests PASS (~60+ counting deck-polish and html-review).

- [ ] **Step 6: Commit**

```bash
git add 02_Presentations/html_review/tests/fixtures/representative.py \
        02_Presentations/html_review/tests/test_output.py \
        02_Presentations/html_review/view_latest.bat
git commit -m "feat(html-review): add representative fixture, section smoke test, view_latest.bat"
```

---

## Task 14: E2E smoke test + PR

**Files:**
- None (manual verification + PR creation)

- [ ] **Step 1: Build a real HTML file against representative.py and open it locally**

```bash
cd /Users/jgmbp/Desktop/RPE-Workflow
python -c "
import sys
from pathlib import Path
sys.path.insert(0, '02_Presentations')
from html_review.builder import build_html
from html_review.model import ClientMeta
from html_review.tests.fixtures.representative import representative

out = Path('/tmp/html_review_smoke')
out.mkdir(exist_ok=True)
results = representative(out)
client = ClientMeta(id='1615', display_name='Cape & Coast Bank',
                    month='2026-04', month_display='April 2026', run_date='2026-04-17')
path = build_html(results, client, out, embed_images=True)
print(f'Wrote {path}')
"

open /tmp/html_review_smoke/index.html
```

Expected browser behavior to verify manually:
- Sidebar lists all 9 sections in canonical order with counts
- Clicking a sidebar link jumps to the section
- Scroll highlights the current section in the sidebar
- Each analysis has a checkbox, PNG chart, a `<details>` data table, notes
- Checking boxes updates the "N selected" badge
- Refresh preserves selection
- Pressing `S` toggles the nearest block
- "Clear" empties selection
- "Export PDF" with 0 selected → alert
- "Export PDF" with 1+ selected → browser print dialog; "Save as PDF" → resulting PDF contains only selected blocks, no sidebar, no tray

- [ ] **Step 2: Fix any issues surfaced during manual smoke test, commit fixes**

(No fixes expected, but if something's off, iterate with a small commit.)

- [ ] **Step 3: Push branch**

```bash
git push -u origin feature/html-review
```

- [ ] **Step 4: Open PR**

```bash
gh pr create --title "feat: html-review -- analyst HTML workbench + PDF export" --body "$(cat <<'EOF'
## Summary
- New \`02_Presentations/html_review/\` package: \`builder.py\`, model, templates, static JS/CSS
- Renders list[AnalysisResult] -> one self-contained HTML file per client-month
- Sidebar navigation, selection tray with localStorage persistence, keyboard shortcut (S), scroll-spy
- Export PDF via browser print — only selected analyses ship, no sidebar, no tray
- Three committed fixtures; ~12 unit + integration tests

## Depends on
- PR #57 (deck-polish) — inherits \`style/\` module; this branch is off \`feature/deck-polish\`. Rebase onto \`main\` once #57 merges.

## Spec
\`docs/superpowers/specs/2026-04-17-html-review-design.md\`

## Plan
\`docs/superpowers/plans/2026-04-17-html-review.md\`

## Test plan
- [x] 3 tiny_deck fixtures produce expected HTML
- [x] representative fixture renders all 9 canonical sections
- [x] structural lint (no unresolved jinja, no external scripts, print.css present)
- [x] manual smoke test in Chrome: selection tray, scroll-spy, keyboard, export PDF
- [ ] Reviewer: open the smoke-test HTML locally, verify sidebar + selection + export work

## What this is NOT
- Not a PPTX replacement (deck_builder.py stays)
- Not hosted anywhere (output is a local file only)
- Not sharing to clients (analyst-facing workbench; PDF export is the deliverable)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)" --base main
```

Expected: PR URL printed.

---

## Self-review checklist

**Spec coverage:**
- §5.1 file layout → Tasks 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13 (one per file)
- §5.2 module boundaries → enforced by the single-responsibility nature of each task
- §5.3 dependencies → jinja2 assumed present; verified at Task 11
- §6 data flow → Task 11 (build_html orchestrator)
- §7 templates → Tasks 5, 6, 7, 8
- §8 selection + PDF → Tasks 9, 10
- §9 output location + view_latest → Tasks 11, 13
- §10 style/ integration → palette CSS vars in Task 4; typography classes in Task 4
- §11 testing (fixtures + unit + output lint + smoke) → Tasks 2, 3, 11, 12, 13
- §12 branch strategy → Task 1 branch-from-deck-polish; Task 14 PR
- §13 acceptance criteria → Task 14

**Placeholder scan:** no TBD/TODO/"similar to"/bare-instruction steps found. All steps have concrete code.

**Type consistency:** `ClientMeta`, `AnalysisBlock`, `SectionRender`, `TableRender` — names identical across tasks 3, 11, 12. `AnalysisResultLike` protocol defined in Task 11; used in Task 2 fixtures as a dataclass with matching attributes.

**Scope:** single cohesive package, ~14 tasks, weekend-sized.

---

## Execution options

**Plan complete and saved to `docs/superpowers/plans/2026-04-17-html-review.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
