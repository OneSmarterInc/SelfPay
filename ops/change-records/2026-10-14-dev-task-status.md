# October 14 developer-task execution record

Status: PARTIAL — source and artifact audit complete; database execution and historical log evidence pending.

## A — App-repository dump removal

Deleted SelfPay branch backup-2026-10-12 on October 14, 2026. Previous head:
63071bc9f7b756cef4a2ba7a44fdcbbf87177939. GitHub displayed Deleted with a Restore
control; REST branch listing confirmed absence. No open PR references this branch.
The approved destination MySelfPay_Backup branch backup-2026-10-12 remains at
892343ff15544204a5fab6fecb7369f255af35f9. GitHub app-repo page displayed 0 forks.
Reviewed all 271 run metadata records; all 12 backup/restore runs returned empty
artifact lists. This is not proof that old commits/caches/clones have been purged;
deleting a branch does not erase Git objects. Other workflow artifact contents
were not exhaustively inspected. Do not claim complete sensitive-data eradication.

## B/C — Restore and cleanup

No new restore database was created or used. The task document conflicts with the
owner's explicit GitHub-file-only/no-restore-database direction. RESTORE_DATABASE_URL
removal is pending action-time confirmation because deleting its saved value is
irreversible through GitHub's UI. No secret value was read.

Prepared exact ID-scoped SQL and review record:
ops/sql/remove-test-members-2026-10-14.sql and
ops/change-records/2026-10-14-test-row-cleanup.md.
SQL commit: 4b9fd22e30062c815ea8f4d613ce428eee484146.
No live SQL, deletion, new backup branch, copy test or recurring export activation
was performed. Latest two scheduled backup runs were skipped. Daily backups must
remain disabled until reviewed cleanup, synthetic checks and recurring-job
approval succeed. A current pre-write backup and copy test/waiver are still required.

## D — City ranking

Bundled Census 2025 incorporated-place population estimates with provenance and
checksums. Multiple covered same-name cities rank population-first; state choice
remains explicit. Dayton OH and Columbus OH rank first even if another city's
facility is closer. Springfield still asks for a state. 27 local tests passed
(search, proximity and shared-address generation). No production deployment.

## E — Apps

Android PR #21 converted to draft (verify final API state). iOS PR #23 was already
merged and build 4 uploaded before this task document, with explicit owner approval.
A merged PR cannot be converted to an open draft. No rollback or new submission.
PWA #22 remains closed pending reconciliation of the earlier cancellation with
this document. Do not silently restore its Install app UI.

Shared app-config.json and generator added for native app builds. iOS source wired
on main; Android source wired on its unmerged branch. PWA wiring remains pending.
No new native binary compilation or upload is claimed for these source changes.

## F — Publication and production attribution

Original October 9 16:00–16:10 UTC agent execution log was not found in available
workspace files or targeted Personal Context retrieval. Publication operator,
exact SQL and prior approval remain unverified; retrospective remains open.

Authenticated Vercel deployment history identifies production deployment
 dpl_32kg64VmPERotu7wY8j9i5Zar8sk
created 2026-10-13T07:40:08.954Z, creator account 1smarterinc-2822,
source redeploy, commit ae1b9ef09de5eefc86fe4e18779a891c46190447,
branch fix/restore-stage-diagnostics. This identifies the account, not the human
operator. Production URL: https://myselfpay-review.vercel.app/.
The five inspected production history entries use the same creator account.

Production remains paused; directory-data preserved; Directory sync remains paused.
Synthetic data only. GitHub budget was not changed; no paid service was enabled.

## Follow-up execution — October 14, 2026

Owner requested remaining work now. Reopened and finished PWA PR #22; merged at
f46a608573c44aca7a92165dff62d92083feed01. PWA manifest now reads website_url from
app-config.json, shared with iOS and Android source generation. Cross-domain PWA
migration requires deploying at the new origin and reinstalling; documented.
31 local Python tests passed plus service-worker offline/network privacy checks.
No native build or app store submission was run. Main and PWA branch Vercel
deployment are disabled; merge carries skip-ci. Production deployment rechecked:
dpl_32kg64VmPERotu7wY8j9i5Zar8sk, unchanged ae1b9ef09de5eefc86fe4e18779a891c46190447.

Completed artifact inventory across all 272 runs returned by GitHub. All artifact
list calls succeeded. Seven artifacts remain: three IPA, two simulator ZIP and
two APK bundles. Downloaded and recursively inspected all seven archives, including
nested application archives, for SQL/dump/database filenames and PostgreSQL dump
signatures. No database dump found. This does not prove absence of deliberately
obfuscated data or copies outside these artifacts. No artifacts deleted.
Artifact IDs: 11887525479, 11886991696, 11885977545, 11880315230,
11880190608, 11811854334, 11813160919.

RESTORE_DATABASE_URL remains present (name only inspected). GitHub deletion
confirmation is prepared; final removal awaits required action-time confirmation.
No temporary Neon branch or live SQL was executed. Exact cleanup SQL and record
remain DRAFT until branch testing, current pre-write backup, and owner approval
of the concrete record. Recurring backups remain disabled; no guard bypass.
Original October 9 agent publication log is still unavailable.
GitHub budget and Usage blocked settings were not modified; no paid service enabled.

## Secret removal and fresh backup checks — October 14, 2026

Owner explicitly authorized safe removal of RESTORE_DATABASE_URL. GitHub required
account reauthentication, completed by the owner through secure entry. The secret
was removed and the environment UI verified to contain only BACKUP_DATABASE_URL
and BACKUP_REPO_TOKEN. No secret values were read or recorded.

Fetched backup/restore sources and SQL from main 832918cab82a2c7f2a1fa57e5692c19fd3efdea0.
All 19 backup Python unit tests passed. An initial incomplete local source copy
lacked the synthetic-check SQL; after fetching that committed dependency, all tests
passed. These are unit tests, not proof of an actual Neon restore.

MySelfPay_Backup privacy reverified. No Actions workflow was dispatched, budget
or Usage blocked setting changed, deployment made, or database row deleted.
Neon plugin discovered but not connected; connection requested. Temporary restore
branch identity, endpoint, empty database and included allowance remain unverified.
No restore can run until those checks and credentials are available. Recurring
exports remain disabled until approved cleanup and synthetic checks pass.

Targeted workspace session-log search found only historical SQL/change records,
not the October 9 16:00–16:10 UTC execution session. The available remaining-publication
record documents earlier batch 395c84be, not the later 4974b4d5 publication; it does
not close the attribution gap. Original session evidence remains needed.

## Successful isolated restore — October 14, 2026

Neon connection verified project late-grass-13270808 (myselfpay-review), owned by
the Vercel-managed organization, free_v3/free plan, branch limit 10, four existing
branches before this test. No billing or production settings changed.
Created restore-verify-20261014, br-hidden-mode-b77xkrb0, parent live
br-rapid-mouse-b7clh18t, created 2026-10-14T12:38:52Z, parent LSN 0/2C7F7A8.
Expiry: 2026-10-15T12:38:52Z. New database selfpay_restore_20261014 verified empty.
Endpoint ep-wandering-paper-b7934uxi; min/max compute 0.25 CU, account defaults.
Custom suspend setting was rejected without creating a branch; defaults succeeded.

GitHub Actions budget freshly verified $0 with Usage blocked; 717.3/2000 included
minutes and 0.3/0.5 GB storage used before run; $0 billable usage.
Successful restore run: https://github.com/OneSmarterInc/SelfPay/actions/runs/38566059343
Job 115858922173. Source main 305b247a029af6754afb20f76e2a102d7591b1d7.
Restored exact approved GitHub backup commit 892343ff15544204a5fab6fecb7369f255af35f9.
Workflow verified immutable dump, branch identity, direct TLS endpoint, empty target,
transactional restore, catalog equality and empty excluded tables.
Result: active batch 4974b4d5-143c-4bf2-a198-28d4e366ecd9; entries 105; offers 57;
located entries 98; locations 132; programs 7. sessions/login_limits/guest_usage all 0.
Independent read-only checks on restored database matched those results.

RESTORE_DATABASE_URL was removed again after success. A browser diagnostic captured
the temporary connection value while the save dialog was still closing. It was not
repeated in prose or committed. Rotated neondb_owner password on the temporary
branch only and removed the local credential file. Production credentials were
not changed. Inherited credential reuse across branches has not been ruled out;
owner review of production credential rotation is needed without silently changing
the website's credentials. Temporary compute suspended; branch remains expiring.

Read-only scope check on the branch's fresh neondb clone found 4 non-guest members,
all 4 listed IDs present, 6 related conversations, 1 related preference, 1 related
correction, 0 related sessions and 0 related guest_usage rows. This confirms scope
at clone time, not synthetic classification and not later live state.
No DELETE was run on either database. Cleanup SQL remains awaiting explicit owner
approval and branch testing. Daily export activation remains blocked until cleanup
and all synthetic checks pass. POLICY.md's seven-day Neon pre-write recovery branch
also needs reconciliation with the owner's GitHub-file-only backup requirement.
The restore branch is temporary validation, not a daily backup destination.

Production alias rechecked unchanged: dpl_32kg64VmPERotu7wY8j9i5Zar8sk,
commit ae1b9ef09de5eefc86fe4e18779a891c46190447. No deployment or app submission.
October 9 original agent session log remains unavailable; attribution not inferred.
