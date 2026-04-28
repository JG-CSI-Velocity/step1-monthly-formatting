#!/usr/bin/env bash
# One-click polish launcher for macOS.
# Drop .pptx files in ./decks_to_polish/ then double-click this file.

set -e
cd "$(dirname "$0")"

mkdir -p decks_to_polish

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found on PATH."
    echo "Install Python 3.12+ and re-run."
    read -rp "Press Enter to close..." _
    exit 1
fi

shopt -s nullglob
pptx_files=(decks_to_polish/*.pptx)
if [ ${#pptx_files[@]} -eq 0 ]; then
    echo "No .pptx files found in decks_to_polish/"
    echo ""
    echo "1. Drop your decks into:"
    echo "   $(pwd)/decks_to_polish/"
    echo "2. Double-click polish_mac.command again."
    echo ""
    read -rp "Press Enter to close..." _
    exit 0
fi

echo "Polishing ${#pptx_files[@]} deck(s)..."
python3 polish.py --batch decks_to_polish --out polished --apply

echo ""
echo "Done. Opening polished/ folder..."
open polished
read -rp "Press Enter to close..." _
