# Phase 12: Folder Structure - Context

**Gathered:** 2026-04-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Restructure the GitHub repo from its current a314c50 state to mirror the M:\ARS\ 00-05 layout. Create missing directories, move config and UI files, copy deck assembly code from local Step 3 folder, and remove design artifact files from root. Each change committed so JG can review before pushing to GitHub, then pull to work PC.

</domain>

<decisions>
## Implementation Decisions

### Config File Handling
- **D-01:** Move originals of ars_config.json and settings.py from 00_Formatting/00-Scripts/configs/ to 03_Config/. Do NOT leave copies behind.
- **D-02:** Move clients_config.json from repo root to 03_Config/.
- **D-03:** Update ALL import paths in scripts that reference these config files (00_Formatting/run.py, 01_Analysis code, etc.) to point to new 03_Config/ locations.

### Root File Cleanup
- **D-04:** Delete mockup_1_editorial.html, mockup_2_terminal.html, mockup_3_warm.html, mockup_4_warm_refined.html, velocity_app.html, ui_mockup.py from repo root.
- **D-05:** Keep setup.bat, SETUP.md, SLIDE_MAPPING.md, organize_m_drive.bat at repo root.

### 02_Powerpoint Directory
- **D-06:** Copy deck assembly code from local "Step 3 - Powerpoint/ars-production-pipeline/02_Powerpoint/" into 02_Powerpoint/ in the repo. This includes deck_assembler.py, sections/ directory (with _base.py, preamble.py, dctr.py, transaction.py, __init__.py, overview.py, attrition.py, value.py, insights.py, ics.py, rege.py, mailer.py), and SECTION_GUIDE.md.

### 02_Presentations Directory
- **D-07:** Create 02_Presentations/ as an empty directory (with .gitkeep) for generated PPTX output.

### 04_Logs Directory
- **D-08:** Create 04_Logs/ as an empty directory (with .gitkeep) for run logs.

### UI Move
- **D-09:** Use git mv to rename ui/ to 05_UI/. Preserves file history.

### Push Gate
- **D-10:** After all changes are committed, show JG the exact file list and diff BEFORE pushing to GitHub. Wait for explicit "push" approval. JG will then pull on work PC and verify folder structure matches M:\ARS\.

### Claude's Discretion
- Whether to update .gitignore for new 03_Config/, 04_Logs/, 05_UI/ paths
- Whether to add __init__.py files to new directories
- Commit message style and granularity within the phase

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs -- requirements fully captured in decisions above.

### Source Files
- `Step 3 - Powerpoint/ars-production-pipeline/02_Powerpoint/` -- Source for deck assembly code to copy
- `00_Formatting/00-Scripts/configs/ars_config.json` -- Config file to move
- `00_Formatting/00-Scripts/configs/settings.py` -- Settings module to move
- `ui/app.py` -- FastAPI app to move to 05_UI/
- `ui/index.html` -- UI page to move to 05_UI/

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- ui/app.py: FastAPI app with static file serving and REST endpoints
- ui/index.html: Main UI page
- 00_Formatting/00-Scripts/configs/settings.py: Pydantic settings loader
- 00_Formatting/00-Scripts/configs/ars_config.json: Base path configuration

### Established Patterns
- Config loading: settings.py uses Pydantic BaseSettings, reads from ars_config.json
- Import pattern: 00_Formatting code imports from configs/ relative path

### Integration Points
- 00_Formatting/run.py imports from configs/settings.py -- needs path update after move
- 01_Analysis code reads clients_config.json -- needs path update after move
- ui/app.py serves static files -- path may need update in 05_UI/

</code_context>

<specifics>
## Specific Ideas

- JG's work PC at M:\ARS\ already has the full 00-05 structure. GitHub needs to match it.
- The "Step 3 - Powerpoint" local folder is a copy of the ars-production-pipeline repo with 02_Powerpoint/ code that was never pushed to GitHub.
- After this phase, JG will pull to work PC and visually verify the folder structure matches.

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope.

</deferred>

---

*Phase: 12-folder-structure*
*Context gathered: 2026-04-10*
