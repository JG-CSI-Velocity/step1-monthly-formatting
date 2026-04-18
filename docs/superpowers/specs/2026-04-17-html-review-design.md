# HTML Review — Design Spec

**Date:** 2026-04-17
**Repo:** `JG-CSI-Velocity/ars-production-pipeline`
**Branch (primary):** `feature/html-review` — branches from `feature/deck-polish` until that PR merges to `main`, then rebases onto `main`.
**Status:** Draft — pending user review
**Aesthetic:** Restrained business-report feel. No slideshows, no card-flip animations, no chip pills. Sidebar + scroll + analysis blocks, quiet typography, CSI palette used sparingly.
**Sibling spec:** `docs/superpowers/specs/2026-04-17-deck-polish-design.md`

---

## 1. Problem

The ars-production-pipeline runs ~400 analysis cells per client per month. Each cell produces a matplotlib PNG, KPIs, Excel data, and speaker notes (all wrapped in an `AnalysisResult` from `01_Analysis/00-Scripts/analytics/base.py`). Today `deck_builder.py` assembles these into PPTX decks, then the analyst hand-polishes the PPTX for delivery.

That workflow:

- Produces a monolithic PPTX the analyst must edit slide-by-slide to curate for each audience
- Has no internal-review medium between "pipeline finished" and "deck is ready"
- Can't isolate a subset of analyses for a specific client conversation without duplicating slides

## 2. Goal

Ship a new consumer of `AnalysisResult` that renders a **single self-contained HTML file per client-month** — a navigable review interface. The analyst opens it in a browser, explores all ~400 analyses across 9 sections, selects the ones relevant to a given conversation, and exports a PDF of just those. The PDF is the client deliverable. The HTML is the analyst's workbench.

## 3. Scope decomposition

This is the third of three sibling sub-projects sharing the `style/` module.

| Sub-project | Spec | Branch | Role |
|---|---|---|---|
| `deck-polish` | [`2026-04-17-deck-polish-design.md`](2026-04-17-deck-polish-design.md) | `feature/deck-polish` | Post-hoc PPTX polish pass. Ships first. |
| `style-system` | future | `feature/builder-style-shared` | Extract `style/` to a shared module; refactor `deck_builder.py` to consume it. |
| **`html-review`** | **this spec** | **`feature/html-review`** | **Interactive HTML review UI + PDF export. Branches off `feature/deck-polish` to inherit `style/`.** |

## 4. Non-goals (this spec)

- GitHub Pages deployment / client-facing hosting (phase later when needed)
- Plotly/interactive chart re-rendering (cells still emit PNG; interactivity is *navigation*, not chart-level zoom/hover)
- Replacing `deck_builder.py` (additive — PPTX path remains intact)
- Server-side PDF generation (client-side browser print is sufficient for Phase 1)
- Multi-client overview pages / cross-client comparisons
- Authentication, password gating, signed URLs

## 5. Architecture

### 5.1 File layout

New package inside `02_Presentations/` (alongside `polish.py` + `style/`):

```
02_Presentations/
├── polish.py                     # existing — deck polish
├── style/                        # existing — shared with html_review
└── html_review/                  # NEW
    ├── __init__.py
    ├── builder.py                # CLI entrypoint; reads AnalysisResult list -> HTML
    ├── model.py                  # Pydantic/dataclass: client meta + renderable blocks
    ├── templates/
    │   ├── index.html            # jinja2 master template
    │   ├── partials/
    │   │   ├── sidebar.html
    │   │   ├── section.html
    │   │   └── analysis.html     # standard block (chart + optional data table + notes)
    │   └── print.css             # print stylesheet embedded into index.html
    ├── static/
    │   ├── app.js                # selection tray + keyboard shortcut + scroll-spy
    │   ├── print.js              # Export-PDF click handler (applies print class, calls print())
    │   └── styles.css            # imports CSS vars from style/ (Montserrat, CSI palette)
    ├── view_latest.bat           # one-click launcher: opens the most recent report
    └── tests/
        ├── fixtures/             # synthetic AnalysisResult lists
        │   ├── tiny_deck.py      # 3 analyses for unit tests
        │   └── representative.py # 1 analysis from each of the 9 sections
        ├── test_blocks.py
        ├── test_builder.py
        └── test_output.py        # asserts HTML structure, selection tray, print CSS
```

### 5.2 Module boundaries

- `model.py` — data shapes (jinja2 context dataclass, section + block types); no I/O
- `builder.py` — the only module touching disk (reads PNGs, writes HTML + assets)
- `templates/` — jinja2 only; no logic beyond rendering
- `static/` — browser-only JS/CSS; no build step (no webpack, no bundler, no npm)

### 5.3 Dependencies

Added to `requirements.txt`:
- `jinja2` (template rendering) — already transitively present via FastAPI in existing requirements; verify at build time.
- No other new deps. `python-pptx`, `Pillow`, `pandas` are reused from the existing pipeline.

Browser-side:
- Vanilla JS. No frameworks, no npm, no Alpine.js.
- `app.js` is ~100 lines covering: checkbox toggle, localStorage persistence, keyboard shortcut, scroll-spy. Hand-written, fully self-contained. No CDN dependencies.

## 6. Data flow

```
Pipeline run finishes
  |
  v
html_review/builder.py --client <id> --month <YYYY-MM> --results <path-to-results.pkl>
  |
  v
1. Load list[AnalysisResult] from the pickled pipeline output
2. Group by AnalysisResult.section (9 canonical sections)
3. Every analysis uses the same `analysis.html` template:
     - Headline (slide title)
     - PNG chart
     - If `excel_data` is non-empty: the first sheet rendered as an HTML table directly below the chart (collapsible `<details>` if long — default collapsed)
     - `notes` field as italic paragraph below, if present
4. Render jinja2 templates/index.html with the full model
5. Copy every chart_path (PNG) into reports/<client>/<YYYY-MM>/assets/
6. Inline static/app.js, static/print.js, static/styles.css, and templates/print.css
   into the HTML head — fully self-contained output (no external scripts, no CDNs)
7. Write reports/<client>/<YYYY-MM>/index.html
```

The builder is pure: same input results + same client metadata → byte-identical HTML. No random IDs, no timestamps in the output (client metadata has the date).

## 7. Templates

Each template is a focused partial. Shape of the data passed in:

### 7.1 `index.html`
```
{
  client: {id, display_name, month_display, run_date},
  sections: [
    {
      id, title, eyebrow, lede,
      kpi_row: [{label, value, delta}],
      blocks: [<rendered block>]
    }
  ],
  styles_css: "<inline bundle>",
  app_js: "<inline bundle>",
  print_js: "<inline bundle>"
}
```

### 7.2 `partials/analysis.html`
The only block type. Contains in order:

1. **Headline** — `<h3>` with the slide title (`t-slide-title` class from `style/typography.py`)
2. **Chart** — `<img>` with the PNG from `chart_path`
3. **Data table** (optional) — if `excel_data` is non-empty, a `<details>` element (collapsed by default) containing the first sheet as a plain HTML table. If multiple sheets exist, a small `<select>` above the table switches between them.
4. **Notes** (optional) — `<p class="t-annotation">` with the `notes` field in italic, if present

Wrapped in `.analysis-wrapper` with a selection checkbox at the top-left.

No tabs. No card flips. No slideshows. Every datum visible at a glance or one click away.

### 7.3 `partials/sidebar.html`
One `<a>` per section with cell count. Highlights active section via scroll spy (IntersectionObserver in app.js).

## 8. Selection tray + PDF export

### 8.1 Selection tray behavior

- Sticky at top of main column (not overlapping sidebar)
- Shows: badge count + Preview / Export PDF / Clear buttons
- Per-block checkbox (to the left of each `.analysis-wrapper`)
- "Select entire section" checkbox at each section header
- Keyboard: pressing `S` toggles the block currently in the viewport center
- State persisted in `localStorage` key `deck-polish-selection-<client>-<month>` — refresh doesn't lose picks
- Selecting a block adds green outline + light shadow ring

### 8.2 Export PDF flow

1. User clicks **Export PDF**
2. `print.js` applies `body.classList.add('exporting')`
3. `print.css` (loaded but only active with `@media print`):
   - Hides sidebar, selection tray, section headers with no selected children, all unselected `.analysis-wrapper` elements
   - Adds CSI letterhead on every page (logo from static asset + client name + month + page number)
   - Sets page size 8.5" x 11" portrait, 0.5" margins
   - Forces `page-break-after` after each visible analysis block
   - Data table `<details>` elements: if expanded in the HTML view, they render in the PDF; if collapsed, they don't. User controls per-analysis data-inclusion by expanding or collapsing before export.
4. `print.js` calls `window.print()` — browser's native print dialog opens
5. User picks "Save as PDF" (Chrome, Edge, Safari all support this)
6. `print.js` removes `body.exporting` class after `afterprint` event fires

### 8.3 Export quality

- PNG charts render at native resolution — same DPI as the deck_builder uses (150 DPI at 12" wide = 1800px). Print renders at 1:1.
- Tables from `excel_data` use the same CSS as the HTML view.
- Browser rendering matches Chrome. Safari and Edge produce visually identical PDFs. Firefox's PDF engine has slightly different kerning — acceptable but noted.

## 9. Output location & view-latest

`builder.py` writes to:

```
M:\ARS\02_Presentations\reports\<client_id>\<YYYY-MM>\
    index.html          # self-contained HTML (3-8 MB with embedded PNGs + JS)
    assets/             # copies of the PNG charts (optional if --embed-images)
```

Embedding behavior:
- `--embed-images` (default): PNGs base64-encoded inline. One file, email-able.
- `--no-embed-images`: PNGs live in `assets/`. `index.html` references them. Smaller HTML, folder must be copied together.

### 9.1 `view_latest.bat`

One-click launcher at `M:\ARS\02_Presentations\html_review\view_latest.bat`. Behavior:
- Scans `reports/*/20*-*/index.html`
- Picks the most recently modified one
- Opens it with `start "" <path>` (default browser)

## 10. Shared `style/` module usage

- `style/palette.py` constants exported as CSS custom properties in `static/styles.css`:
  ```css
  :root {
    --navy: #1B365D;
    --teal: #0D9488;
    --coral: #E7433C;
    ...
  }
  ```
- `style/typography.py` factories map to CSS classes via a small adapter in `builder.py` that emits:
  ```css
  .t-slide-title { font-family: Montserrat; font-size: 20pt; font-weight: 800; }
  .t-subtitle { font-family: Montserrat; font-size: 14pt; font-weight: 400; }
  ...
  ```
  So templates can use `<h3 class="t-chart-title">` and stay in sync with the type scale.
- `style/layout.py` constants — unused by HTML (layout.py is for PPTX zones). Skipped.
- `style/headline.py` — reused at build time to **flag** weak headlines in an internal-only "quality" pill next to each block. Analyst can see "Fragment headline" as a hint when picking what to export. Not shown in export.
- `style/narrative.py` — same: scores displayed inline as small badges (C/P/F color-coded) in the HTML, hidden in export.

## 11. Testing

### 11.1 Fixtures

`tests/fixtures/tiny_deck.py` — builds 3 synthetic `AnalysisResult` instances:
- One with PNG + notes only
- One with PNG + excel_data (one sheet)
- One with PNG + excel_data (multiple sheets — tests the `<select>` sheet switcher)

`tests/fixtures/representative.py` — one analysis per canonical section (9 total); used to assert that every section renders and the sidebar lists them in order.

### 11.2 Unit tests

- `test_builder.py` — given `tiny_deck`, builder produces an `index.html` with expected structure (3 `.analysis-wrapper` elements, correct section heading, data table `<details>` present when excel_data is non-empty)
- `test_output.py` — rendered HTML passes a cheap structural lint: no unresolved jinja2 `{{ }}` markers, selection-tray markup present, print.css embedded, no external `<script src="...">` tags (everything inline)

### 11.3 No client data

All tests use synthetic fixtures. No real client PNGs or data in the repo.

### 11.4 Smoke test

`pytest` + an end-to-end build against `representative.py` → open the resulting HTML manually and confirm all 9 section templates render. Logged in PR description as manual verification step.

## 12. Branch strategy

- `feature/html-review` branches from `feature/deck-polish` (because `style/` lives there until PR #57 merges)
- Once `feature/deck-polish` merges to `main`, rebase `feature/html-review` onto `main`
- Commits are atomic per file/submodule
- PR into `main` when:
  - All tests pass
  - `representative.py` smoke test produces a visually valid HTML
  - Style-system extraction (sibling sub-project) is either not-yet-started (OK) or completed (rebase to consume the shared location)

## 13. Acceptance criteria

- [ ] `html_review/` package with builder, templates, static assets, tests
- [ ] `view_latest.bat` opens the most recent report in the browser
- [ ] 3 committed fixtures produce expected HTML
- [ ] Selection tray with localStorage persistence works
- [ ] Export PDF via browser print produces a correctly-filtered PDF
- [ ] PNGs render at 150+ DPI in both HTML view and PDF output
- [ ] No client data in the repo
- [ ] Shared `style/` module used for colors and typography
- [ ] PR merged into `main`

## 14. Open questions (none blocking)

1. Whether the builder should accept input as a pickled list of `AnalysisResult` objects or re-run the analytics pipeline internally. Default: pickled input (avoids re-running costly analytics just to refresh HTML).
2. Handling slides that the `deck_builder.py` consolidates (some paired slides merge into one PPTX slide). In HTML: stack vertically with a subtle "Related" label between them. Revisit if it looks bad.
3. Phase 2 placeholder: a `cell.plotly_json` field on `AnalysisResult` will let the HTML swap in interactive charts when present. Out of scope for this spec.
