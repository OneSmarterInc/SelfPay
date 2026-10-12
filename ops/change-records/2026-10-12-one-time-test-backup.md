# October 12 backup preflight on isolated Neon branch

Status: BLOCKED — synthetic-data precondition failed; no dump or restore executed.

## Owner instruction

On 2026-10-12 at 18:49 Asia/Kolkata, the owner stated:
"I do not waive the Neon branch test. Please perform the required test on a separate Neon branch first, verify the backup and restore process, and ensure the synthetic-data check passes. Do not upload anything to MySelfPay_Backup until the required checks are complete and I approve proceeding."

No waiver is recorded. The proposed date-limited exception has been removed
from this PR. The original guard and workflow remain unchanged.

## Executed test

At approximately 18:50 Asia/Kolkata (13:20 UTC), the assistant executed the exact
committed ops/sql/backup-synthetic-check.sql from commit
9ff7de313afe5641dc4ed54da021abe9fcbab893 using Neon's SQL editor.

Verified UI target:
- Project: myselfpay-review / late-grass-13270808
- Separate existing branch: restore-test-20261012
- Branch ID: br-weathered-field-b7ykycqf
- Compute ID displayed: ep-twilight-grass-b7rwzqpf
- Database: neondb
- This is not live branch br-rapid-mouse-b7clh18t.
- The existing test branch comes from the retained Oct 12 baseline and earlier
  PITR drill; this test does not establish the latest live state.

Result: one row, 123 ms, in SQL column order:
1. Non-guest members exist: true.
2. Conversations exist: true.
3. Corrections at/after 2026-10-13 00:00 Asia/Kolkata exist: false.

The SQL executed successfully, but the synthetic-data acceptance condition FAILED.
The owner describes the users as test users; that classification does not make
the original structural checks pass. No private record contents were displayed.

## Consequences and remaining work

The original guard requires stopping before pg_dump on either of the first two
true results. No dump, SQL restore or upload was attempted during this test.
No database records were changed. No backup was uploaded to MySelfPay_Backup.
BACKUPS_ENABLED remains false. No production deployment or live SQL was run.

To continue under the existing rule, an approved data-handling plan must resolve
the non-guest and conversation records. Do not delete records merely to obtain
a passing result, and do not claim that a sanitized test fixture validates a
full-data export of the current dataset.

After the precondition is legitimately satisfied, remaining tests include a
same-snapshot export, restore into an empty isolated Neon target, comparison of
the six catalog fields and transient-data exclusions, and an evidence review.
The owner must explicitly approve proceeding before any destination upload.

## Subsequent explicit approval — 2026-10-12 19:34:50 Asia/Kolkata

Owner: "yes confirm I waive the branch test and approve today’s test-data backup to MySelfPay_Backup."

This later instruction supersedes the earlier refusal of a branch-test waiver.
Restore the previously prepared manual exception from c8ec81940489b87ca97b9c365aba41a458b4df1e
for today's owner-confirmed test dataset only. It permits non-guest accounts and
conversations on October 12; recent corrections still stop export. Scheduled
backups stay paused. Private destination and read-only role checks remain.
SQL is unchanged at 9ff7de313afe5641dc4ed54da021abe9fcbab893:
ops/sql/backup-synthetic-check.sql and ops/sql/backup-catalog-counts.sql,
plus existing role-privilege and pg_export_snapshot SELECTs in export.py.
The earlier failed structural preflight remains valid historical evidence;
no successful restore is claimed. Approved output: backup-2026-10-12 containing
database-2026-10-12.sql in private OneSmarterInc/MySelfPay_Backup.
Status: APPROVED FOR ONE-TIME EXECUTION; execution outcome pending.

## Execution outcome — 2026-10-12 14:16:52Z

Status: EXPORT AND UPLOAD VERIFIED; SQL restore pending credentials.
This supersedes the earlier pending/no-upload status above, without changing
the historical failed structural preflight.

- Source run: https://github.com/OneSmarterInc/SelfPay/actions/runs/38261101819
  (attempt 2), job 114853523461, code 21ba0f87b57abfaf6c27c07fd042ce3ab2d4d14a.
- Snapshot/catalog checks passed at 14:16:49.7266389Z; export completed at
  14:16:50.2105109Z; upload and retention verified at 14:16:52.4416135Z.
- Private destination: OneSmarterInc/MySelfPay_Backup.
- Branch: backup-2026-10-12.
- Commit: 892343ff15544204a5fab6fecb7369f255af35f9; no parents.
- Exactly one file: database-2026-10-12.sql, 1,168,881 bytes.
- Data for sessions, login_limits and guest_usage is excluded; schemas retained.
  Export does not include cluster roles/passwords or ownership/ACL restoration.
- Earlier upload attempt failed with HTTP 403; owner updated token access and
  the retry succeeded. Token's repository-only scope remains unverified.
- Scheduled backups remain paused. No production deployment occurred.
- Actual restore has not passed; a successful export is not restore evidence.
