"""Step 1: Retrieve and Format ODD files.

Usage:
    python run.py                    # current month, all CSMs
    python run.py --month 2026.03    # specific month
    python run.py --csm JamesG       # single CSM only
    python run.py --client 1200      # single client only
    python run.py --skip-retrieve    # format only (already retrieved)
    python run.py --skip-format      # retrieve only (don't format yet)
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add repo root to path so imports work
sys.path.insert(0, str(Path(__file__).parent))

from configs.settings import load_settings
from pipeline.retrieve import retrieve_all
from pipeline.format import format_all


def main():
    parser = argparse.ArgumentParser(description="Step 1: Retrieve & Format ODD files")
    parser.add_argument("--month", type=str, default=None,
                        help="Target month in YYYY.MM format (default: current month)")
    parser.add_argument("--csm", type=str, default=None,
                        help="Process only this CSM (default: all)")
    parser.add_argument("--client", type=str, default=None,
                        help="Process only this client ID (default: all)")
    parser.add_argument("--config", type=str, default=None,
                        help="Path to ars_config.json (default: configs/ars_config.json)")
    parser.add_argument("--skip-retrieve", action="store_true",
                        help="Skip retrieve step (files already in 01-Data-Ready)")
    parser.add_argument("--skip-format", action="store_true",
                        help="Skip format step (retrieve only)")
    parser.add_argument("--max-per-csm", type=int, default=0,
                        help="Max files per CSM (0 = no limit)")
    args = parser.parse_args()

    month = args.month or datetime.now().strftime("%Y.%m")

    print()
    print("=" * 70)
    print("  STEP 1: RETRIEVE & FORMAT ODD FILES")
    print(f"  Month: {month}")
    print("=" * 70)
    print()

    # Load settings
    settings = load_settings(args.config)
    print(f"  Config loaded:")
    print(f"    ars_base:     {settings.paths.ars_base}")
    print(f"    retrieve_dir: {settings.paths.retrieve_dir}")
    print(f"    watch_root:   {settings.paths.watch_root}")

    active_csms = [name for name, path in settings.csm_sources.sources.items()
                   if str(path) != "UPDATE_THIS_PATH"]
    print(f"    CSM sources:  {len(active_csms)} configured ({', '.join(active_csms)})")
    print()

    # Step 1a: Retrieve
    if not args.skip_retrieve:
        print("=" * 70)
        print("  STEP 1a: RETRIEVE (copy from CSM M: drive folders)")
        print("=" * 70)
        retrieve_result = retrieve_all(settings, target_month=month,
                                        max_per_csm=args.max_per_csm)
    else:
        print("  Skipping retrieve (--skip-retrieve)")
        print()

    # Step 1b: Format
    if not args.skip_format:
        print("=" * 70)
        print("  STEP 1b: FORMAT (7-step ODD formatting)")
        print("=" * 70)
        format_result = format_all(settings, target_month=month,
                                    max_per_csm=args.max_per_csm)
    else:
        print("  Skipping format (--skip-format)")
        print()

    # Summary
    print("=" * 70)
    print("  STEP 1 COMPLETE")
    print("=" * 70)
    if not args.skip_retrieve:
        print(f"    Retrieved: {len(retrieve_result.copied)} files")
    if not args.skip_format:
        print(f"    Formatted: {len(format_result.formatted)} files")
        if format_result.errors:
            print(f"    Errors:    {len(format_result.errors)}")
            for csm, fname, err in format_result.errors:
                print(f"      {csm}/{fname}: {err}")
    print()
    print(f"  Formatted files are in:")
    print(f"    {settings.paths.watch_root}")
    print()


if __name__ == "__main__":
    main()
