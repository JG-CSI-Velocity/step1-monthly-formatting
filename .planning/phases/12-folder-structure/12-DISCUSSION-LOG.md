# Phase 12: Folder Structure - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md -- this log preserves the alternatives considered.

**Date:** 2026-04-10
**Phase:** 12-folder-structure
**Areas discussed:** Config file handling, Root file cleanup, 02_Powerpoint location, UI move strategy, Push gate

---

## Config File Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Copy, don't move | Put copies in 03_Config/ but leave originals | |
| Move originals | Move to 03_Config/ and update all imports | ✓ |
| Symlink/reference | 03_Config/ has files, old location gets symlinks | |

**User's choice:** Move originals
**Notes:** Also move clients_config.json from root to 03_Config/. Make sure analysis scripts work with new paths.

## Root File Cleanup

| Option | Description | Selected |
|--------|-------------|----------|
| Remove mockups/old UI | Delete mockup_*.html, velocity_app.html, ui_mockup.py | ✓ |
| Keep everything | Leave all root files as-is | |
| Move to archive | Move to docs/ or archive/ folder | |

**User's choice:** Remove mockups/old UI
**Notes:** Keep setup.bat, SETUP.md, SLIDE_MAPPING.md, organize_m_drive.bat

## 02_Powerpoint Location

**User's choice:** Code exists in local "Step 3 - Powerpoint/ars-production-pipeline/02_Powerpoint/". Copy to GitHub. Work PC already has 00-05 structure; GitHub needs to match.

## UI Move Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| git mv | Renames ui/ to 05_UI/, preserves history | ✓ |
| Copy then delete | Copy files, delete old. Loses history. | |

**User's choice:** git mv -- just get it in the right folder without conflicts.

## Push Gate

| Option | Description | Selected |
|--------|-------------|----------|
| Show then push | Show file list and diff, wait for approval | ✓ |
| Auto-push | Push automatically, verify after | |

**User's choice:** Show then push. JG reviews on GitHub, pulls to M:\ARS\, verifies structure matches.

## Claude's Discretion

- .gitignore updates for new paths
- __init__.py files in new directories
- Commit message granularity

## Deferred Ideas

None
