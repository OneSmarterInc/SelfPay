# Dry-run archive repair

Archives the exact current.json bytes from cba0655359c7226ced81e425acf2e6fe0b4a11c3; no directory records or source metadata were changed by this repair. All 99 entries match the supplied database snapshot; all 13 offer mappings passed comparison.

This repairs immutable_archive_missing only. The inherited version-7 workbook hash and export timestamp have NOT been verified against a 99-entry workbook. This archive is not evidence of workbook provenance. Before live publishing, obtain the updated source workbook and generate a new version with its actual hash and matching immutable archive. Preserve earlier archives.

The snapshot has source=null and active batch b8696fb4-5db5-4de0-8c4e-6c65e8fc8cb4. Repository SQL pins an older bootstrap batch; verify the installed function before preparing any reviewed baseline migration. Do not bypass this safeguard. Keep apply=false and live/scheduled publishing disabled.
