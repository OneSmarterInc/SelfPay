# Daily backup readiness — 2026-10-14

Destination confirmed by owner: OneSmarterInc/MySelfPay_Backup (private).

Status: CONFIGURED; ACTIVATION BLOCKED. Owner requested preparation for daily backups. This does not establish synthetic provenance or a passing live-data check.

Verified current database-backup.yml schedules 02:30 UTC / 08:00 Asia/Kolkata daily. Export requires BACKUPS_ENABLED=true, the database-backups environment, dedicated selfpay_backup_reader, direct TLS host, private destination and a synthetic-data check within the exported snapshot. The October 12 exception is date-limited and cannot authorize today's recurring exports. Existing export.py retains these checks.

Reran the existing local backup-review unit suite: 19 tests passed. These are local unit results, not fresh live database or export verification. Existing October 12 dump has successful isolated restoration evidence in run 38566059343.

Before activation: obtain creation evidence for each of the four target member IDs; complete coordinated credential containment; verify a fresh pre-write recovery point and isolated cleanup test; perform only the specifically approved cleanup after exact-count checks; pass fresh synthetic-data checks; confirm included Actions allowance and required configuration, then enable and verify the first scheduled/manual standard backup. Do not bypass guards or delete records to make checks pass without provenance.

No BACKUPS_ENABLED change, workflow dispatch, database operation, production change or budget change performed. Keep $0 and Usage blocked unchanged. No new repository or backup branch created during preparation.
