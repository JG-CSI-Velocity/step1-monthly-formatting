# Show files that will be loaded (trailing 12-month window from 02-file-config.py)
print(f"Files to load ({len(files_to_load)}):\n")
for file in sorted(files_to_load):
    file_size = file.stat().st_size / 1024  # Size in KB
    print(f"  • {file.name} ({file_size:.1f} KB)")

if older_files:
    print(f"\nExcluded (older than {TRAILING_MONTHS} months): {len(older_files)} file(s)")
