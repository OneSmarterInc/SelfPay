# Daily private SQL backups

Destination: **OneSmarterInc/MySelfPay_Backup**, private. Each `backup-YYYY-MM-DD`
branch has one plain SQL file and a parentless commit; the date is Asia/Kolkata.
The owner selected this name instead of the task sheet's `SelfPay-backups`.

## Activation prerequisites

1. Make the destination private. On 12 October its API reported public; the
   requested privacy change was blocked by automatic approval review because
   GitHub disclosed that Advanced Security would be disabled. Owner decision is
   required before that browser action can proceed. Do not upload while public.
2. Confirm the owner and named developer GitHub usernames. Restrict collaborators
   accordingly; do not guess identities or grant access to unnamed people.
3. The owner creates a fine-grained token with **Contents read/write on
   MySelfPay_Backup only** and stores it as `BACKUP_REPO_TOKEN` in SelfPay's
   `database-backups` environment. Never put the token in chat or a Git file.
4. Keep `BACKUP_DATABASE_URL` as the dedicated `selfpay_backup_reader` URL, with
   TLS and the approved direct host. Keep `BACKUP_EXPECTED_HOST` and
   `BACKUP_DATA_CLASS=synthetic`. The declaration is not a substitute for checks.
5. Review `ops/change-records/2026-10-12-task-review.md` and the retrospective
   publication record. Complete POLICY.md's branch testing/approval for the new
   operational SQL before running the changed export against live.
6. Keep `BACKUPS_ENABLED=false` until all prerequisites pass. On 12 October the
   attempt to save this setting hit GitHub reauthentication; do not assume the
   schedule is paused until the saved setting is verified.

The workflow runs at 02:30 UTC / 08:00 IST daily once enabled. Its normal
GITHUB_TOKEN has Contents read only; only the destination token can publish.
The PostgreSQL image is pinned to the official registry digest resolved on
12 October 2026.

## Data checks and contents

Before pg_dump, in the same repeatable-read snapshot, stop on any non-guest
member, any conversation, or a correction created on/after 13 October 2026
00:00 Asia/Kolkata. Print the fixed stop message without row contents. Today's
old-format dump meets the first two stop conditions, so migration is blocked;
this does not establish whether those records are real or demo records.

All database schema and other table data are exported, except **data only** for
public.sessions, public.login_limits and public.guest_usage. Ownership/ACL
commands and cluster roles/passwords are not included. The dump contains a
comment with six catalog fields from its own consistent snapshot.

After verifying upload, retain the newest 14 daily branches plus the earliest
available daily branch in each month. Other refs, invalid dates and future dates
are untouched. Pruning verifies a one-file parentless tree and uses a ref lease.
Existing date branches are never overwritten. Retention applies only to the
new private destination, not the previous backup in SelfPay.

## Restore verification

`restore_verify.py` is prepared; **no actual SQL restore is yet verified**.
Create a new isolated Neon branch with an empty database and record its parent,
branch ID and direct endpoint. A normal branch copy containing existing tables
is intentionally rejected. Follow POLICY.md before running approved SQL.

Set `RESTORE_DATABASE_URL`, `RESTORE_BRANCH_ID`, and `RESTORE_EXPECTED_HOST`
privately for that disposable database. Do not use the live endpoint or backup
reader credentials. Download a trusted new-format SQL dump from the private
backup repository, then run with PostgreSQL 18 tools and psycopg2 installed:

```sh
python3 ops/backup/restore_verify.py /secure/path/database-YYYY-MM-DD.sql
```

The script checks Neon branch identity and an empty destination, restores in one
transaction with ON_ERROR_STOP, and compares all six fields with the dump's
snapshot manifest. It does not create/delete branches or connect to live. Record
actual results and independently compare with live only under an approved query
record; live may have changed since the snapshot. The old October 12 dump has
no manifest and requires a separately reviewed restore plan using its recorded
snapshot counts; it must not be edited or passed off as a newly checked dump.

Monthly restore scheduling remains blocked on working Neon restore access and
completion of the first drill. No scheduled restore success is claimed. Preserve
the October 12 baseline and test branches until the baseline is no longer needed
and the minimum retention deadline (19 October 08:46:32 UTC) has passed.

## Local verification

```sh
python3 -m unittest discover -s ops/backup -p 'test_*.py'
```
