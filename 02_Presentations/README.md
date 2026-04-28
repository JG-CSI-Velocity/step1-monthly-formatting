# Deck Polish

Post-hoc PowerPoint polish pass that enforces CSI slide-style rules.

## Quick start (no command line)

1. Drop your `.pptx` decks into `decks_to_polish/`.
2. Double-click the launcher:
   - **Windows:** `polish_windows.bat`
   - **Mac:** `polish_mac.command`
3. Polished copies and reports appear in `polished/`.

## What you get per deck

| File | What's in it |
|------|--------------|
| `<deck>.pptx` | The polished copy (fonts fixed, colors snapped to palette) |
| `<deck>__polish_report.md` | Per-slide scores (consultative / performance / focal) + rule violations |
| `<deck>__polish_diff.md` | Text-level before/after per slide |

## What polish fixes automatically (with launcher)

- **Fonts:** anything not in the Montserrat family is switched to Montserrat
- **Colors:** near-palette colors (within threshold 5 in RGB space) snap to the exact CSI palette

## What polish flags but doesn't rewrite

These are analyst judgment calls -- read the report, fix the slide yourself:

- Fragment headlines (no metric / no direction / no driver clause)
- Missing bottom annotation or speaker note
- Too many bold colors on a slide
- Chart images below 150 DPI
- Client name missing from title slide

## Command-line use (advanced)

```
python polish.py <deck.pptx>                 # dry-run report only
python polish.py <deck.pptx> --apply         # polish + report + diff
python polish.py --batch <dir> --apply       # process a whole folder
python polish.py <deck.pptx> --strict        # exit 1 if anything flagged
```

## Style rules

See `docs/superpowers/specs/2026-04-17-deck-polish-design.md` (the compliance-rule source of truth: Montserrat scale, CSI palette, slide zones, headline rules).
