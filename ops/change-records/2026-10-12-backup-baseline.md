# Backup baseline — 12 October 2026

Status: BACKUP CREATED; live comparison and export/restore setup pending.

## Authorization and scope
User requested implementation of the attached MySelfPay-backup-tasks(1).md on 12 October 2026, stating Neon access was connected. Earlier explicit request to create a backup branch remains applicable. Scope: copy the existing live database in the same Neon project and verify catalog counts; do not modify live catalog data.

## Target and backup
- Project: late-grass-13270808 (myselfpay-review), Vercel-connected Neon.
- Live parent: br-rapid-mouse-b7clh18t (main).
- Backup: backup-20261012-0846-baseline.
- Backup branch ID: br-gentle-moon-b74wdsig.
- Dashboard creation time: 2026-10-12 14:16:32 (browser local time, Asia/Calcutta); equivalent UTC: 2026-10-12T08:46:32Z.
- Data AND schema copied. No application connection switched.
- Automatic deletion disabled; retain at least until 2026-10-19T08:46:32Z. Deletion and its record are pending, not performed or scheduled.

## Verification
The requested ops/sql/directory-count-verification.sql was attempted on the backup and rejected by the installed status() function with 'directory sync: wrong database or Neon branch'. The failed read-only transaction was rolled back. The live-target safeguard was not changed.

Replacement: ops/sql/backup-catalog-counts.sql, committed at d23036e59230389d89587036316af3f53a4b17bd. Uses only SELECT in a read-only transaction, ends with ROLLBACK. Branch test succeeded on the new backup:
- active batch: 4974b4d5-143c-4bf2-a198-28d4e366ecd9
- entries: 105
- offers: 57
- located entries: 98
- location records: 132
- programs: 7

The same exact query is the live comparison step within the requested backup verification. No live write is authorized by this record.

## Plan observed
Free plan; PostgreSQL 18; six-hour history retention, directly displayed in Neon. This backup branch is a retained snapshot, distinct from the rolling history window. Recovery more than six hours back using PITR requires a longer configured history window/eligible plan; no upgrade purchased.

## Outstanding
Daily encrypted export destination and read-only export credentials, dump restoration, PITR drill, seven-day branch cleanup, fourteen-day external retention, and monthly restore scheduling remain unverified. No export or restore success is claimed.
