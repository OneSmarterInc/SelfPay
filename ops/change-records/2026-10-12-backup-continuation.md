# Backup continuation and PITR drill — 12 October 2026

Status: PITR VERIFIED; daily export code prepared but not activated; dump restore pending.

## Requested scope
User requested continuation and implementation of MySelfPay-backup-tasks(2).md. Existing verified baseline: br-gentle-moon-b74wdsig. No live writes or app connection changes in this continuation.

## Actual point-in-time recovery evidence
- Project late-grass-13270808; created disposable restore-test-20261012 (br-weathered-field-b7ykycqf) as data-and-schema child of the retained backup.
- Created 2026-10-12T09:05:48Z (UI 14:35:48 Asia/Calcutta).
- Exact marker SQL ops/sql/restore-drill-marker-20261012.sql committed at 2fa1528a20ee56b039dd2824b33ee5f46a1a8923.
- Test-only marker creation succeeded; returned timestamp 2026-10-12T09:07:41.818337Z.
- Used standard Backup & Restore / From history on the test branch, selecting 2026-10-12T09:06:00Z (14:36:00 Asia/Calcutta).
- Restore completed about 2026-10-12T09:10:50Z. Neon preserved old state as restore-test-20261012_old_2026-10-12 14:40:49 +05:30, branch br-polished-flower-b7zjtyxv. Original test branch ID remains br-weathered-field-b7ykycqf.
- Exact read-only verification ops/sql/restore-drill-verification-20261012.sql at 2555c70b6af7d1eeca6ced47e97a70119c6a7448 completed successfully with ROLLBACK: active batch 4974b4d5-143c-4bf2-a198-28d4e366ecd9; entries 105; offers 57; located_entries 98; locations 132; programs 7; test_marker_absent=true.
- This demonstrates actual rewind before a known committed test mutation, with matching catalog counts. It is not an external dump restoration.
- Retained backup and live were not rewound or modified. Test branch and old-state branch remain; cleanup pending. Remove their dependency on the baseline during approved cleanup before deleting the baseline.

## Repository implementation
Prepared .github/workflows/database-backup.yml and ops/backup: PostgreSQL 18 custom-format pg_dump with shared exported snapshot for counts, age public-key encryption of dump plus manifest, private Vercel Blob upload, encrypted read-back hash verification and narrowly scoped 14-day retention cleanup only after a verified new upload. Locked SDK 2.8.1. Disabled unless BACKUPS_ENABLED=true. Schedule 02:30 UTC daily. No public Actions artifacts.

Local checks: Python and JavaScript syntax pass; workflow YAML parsed; two retention tests pass covering exact 14-day boundary, server upload time, foreign namespaces, plaintext and malformed dates; SDK installed successfully; missing credentials produce safe failure. No PostgreSQL/age export integration or real Blob transfer is claimed.

Updated both October 9 publication records with the owner's confirmation as supplied by the attachment; original execution evidence preserved.

## Concrete remaining blockers
No dedicated backup-reader credential, private Blob store token, age recipient/recovery-key custody, GitHub database-backups environment configuration, or workflow activation has been completed. Browser Neon console access does not supply GitHub Actions credentials. Vercel connector still returns Integration Resource not found for the known store; browser access works.

No prior-night dump exists from this workflow, so dump recovery cannot yet be tested. Monthly automated restore execution and seven-day branch deletion scheduling remain pending. The runbook describes secure setup and monthly recovery without claiming execution.

Plan remains Free with six-hour history. A plan/configuration supporting longer history is needed only if PITR must reach further back; the daily external dump provides a separate snapshot recovery path once tested. No paid upgrade purchased.
