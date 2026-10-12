# October 12 developer-task implementation and blockers

## Current status — supersedes historical notes below

- UI PR #18 merged into main at 1f42ac44fd0c9fa0a8b4dd1af1a4c62cbc31c98a after
  passing checks. Concise 105-provider/50-state card replaces the FAQ and appears
  below initial search and the welcome no-order button. No production deployment.
- Backup uploaded and verified in private MySelfPay_Backup: backup-2026-10-12,
  commit 892343ff15544204a5fab6fecb7369f255af35f9, exactly one SQL file and no
  parent history. Run 38261101819 attempt 2 succeeded at 14:16:52Z.
- Owner's explicit 19:34:50 Asia/Kolkata waiver authorized the one-day test-data
  exception. See 2026-10-12-one-time-test-backup.md. Original failed guard
  preflight remains recorded; daily scheduling stays disabled.
- Safe upload diagnostics are included from the successful backup branch.
- Manual restore workflow and immutable-source validation are prepared; all
  six catalog values and three empty transient tables are checked after restore.
- Separate Neon branch br-lively-recipe-b7948zn5 and new database
  restore_20261012 created. It expires October 13 at 14:25:39Z. See
  2026-10-12-dump-restore.md. RESTORE_DATABASE_URL must be saved securely before
  execution; no successful SQL restore is claimed.
- Local backup tests: 19 passed. This is not actual Neon restore evidence.

### Remaining external or owner-dependent work

1. Save the verified disposable target credential and execute/record SQL restore.
2. Monthly restore/PITR automation needs fresh-target provisioning/credentials;
   it is not enabled. A manual workflow is not a completed recurring drill.
3. Retain baseline until October 19 08:46:32Z, then review test branch dependencies
   before cleanup. No retained baseline was deleted early.
4. Confirm the named developer's GitHub username and restrict destination access;
   confirm PAT is fine-grained and scoped only to MySelfPay_Backup.
5. Main protection is configured but GitHub reports it not enforced by the
   current private-repository plan. No paid upgrade authorized or purchased.
6. Vercel deployment-list request still returns 403. Production deployer remains
   unknown; browser fallback needs owner authorization. Deployment remains paused.
7. Publication actor, exact historical SQL and preceding backup remain unknown.
   The publication retrospective is available for owner review; no identity is
   inferred from the Git committer. The original reader-role creation process
   also remains unverified, although export with the read-only role worked.
8. Recurring exports require a compliant data-handling decision; the one-day
   exception does not authorize tomorrow's export. No records were removed to
   force the synthetic guard to pass.

## Historical review (preserved; use current status above)

Status: CODE MERGED; exports paused; operational verification and owner review pending.

Owner requested implementation of MySelfPay-dev-tasks-2026-10-12.md and selected
`OneSmarterInc/MySelfPay_Backup` as the new backup destination. This supersedes
the prior same-repository/full-table export preference, but does not waive the
new document's live-write or production-deployment approval gates.

## Owner correction and status update — 2026-10-12 (Asia/Kolkata)

The owner corrected the earlier statement that the users were real: the users
are not real users. Record this as an owner-provided classification of the user
records as test/demo data, not as an independently verified database finding.
This correction supersedes the earlier real-user statement. The conversation
contents have not been independently classified or verified.

The earlier saved dump contains 4 non-guest members and 6 conversations.
These structural conditions still trigger the committed synthetic-data guard,
regardless of the owner-provided classification. This documentation update does
not change the guard, alter database records, authorize a bypass, or enable
exports. BACKUPS_ENABLED remains false; no new backup or SQL restore has been
completed in MySelfPay_Backup.

Other verified updates today, superseding the earlier pending status below:
- PR #16 was merged into main at commit
  `9ff7de313afe5641dc4ed54da021abe9fcbab893`.
- MySelfPay_Backup was subsequently confirmed private through the GitHub API.
- BACKUP_REPO_TOKEN is present in SelfPay's database-backups environment;
  its permissions and runtime use have not yet been tested.

## Prepared changes

- Fixed private destination and dedicated BACKUP_REPO_TOKEN; workflow contents
  read; official PostgreSQL 18 Bookworm image pinned by registry digest.
- Snapshot-consistent synthetic checks, excluded transient table data with schema
  retained, latest-14 plus first-available-of-month retention, and tests.
- Dump snapshot catalog manifest and guarded empty-Neon-database restore verifier.
- Backup policy and activation/restore instructions aligned with the new task sheet.
- Search alternatives preserve modality, exam and explicit contrast. Unknown
  contrast does not satisfy an explicit contrast request. Browsing with contrast
  unknown remains possible; published scope still requires confirmation.
- No matching exam price: show the requested message and nearest modality-listed
  facilities to call. Radius and price-type fallbacks cannot substitute procedures.
- Ambiguous exact city names ranked by nearest listed facility; auto-select only
  one candidate within radius. Spelling suggestions still require confirmation.
- Prepared Vercel configuration disables automatic Git deployments for main and
  backup-*; this configuration is not effective on main until merged. No production
  deployment was performed. Production usage/necessity remains an owner decision.

## Findings requiring action

1. Destination API reported `private=false`. Browser change to private was blocked
   by automatic approval review because GitHub disclosed disabling Advanced
   Security as a side effect. No backup data was uploaded. Owner must approve
   that specific consequence or make the repository private independently.
2. Today's saved dump has **4 non-guest members and 6 conversations**. This meets
   the new guard's stop conditions; it does not determine whether the rows are
   real people or seeded demo data. No contents were printed or committed. Do not
   bypass the guard or copy this dump into the new destination. Owner must decide
   an approved data-handling plan before exports resume.
3. GitHub reauthentication completed and `BACKUPS_ENABLED=false` was saved and
   visibly verified on 12 October. Scheduled exports are paused.
4. BACKUP_REPO_TOKEN must be created and saved by the owner. Token creation is not
   completed. Required scope: only MySelfPay_Backup, Contents read/write.
5. Named developer username is unspecified; access restriction is unverified.
6. Created a `main` protection rule through authenticated GitHub settings: PR
   required, one approval, passing `test`, up-to-date branch, no admin bypass,
   no force pushes or deletions. **GitHub marks it Not enforced** on the current
   private-repository plan and requires a Team/Enterprise organization account.
   No upgrade was purchased. Do not claim that direct pushes are prevented.
7. Backup reader already exists and today's earlier export succeeded. Do not
   recreate it or claim that its original creation followed an unobserved process.
8. Actual SQL restore, separate-Neon-branch test of the new operational checks,
   live comparisons and monthly restore scheduling remain unperformed. Access
   and owner review are required. Keep exports disabled meanwhile.
9. October 12 baseline/test branches retained. Baseline minimum retention expires
   October 19 at 08:46:32Z; no premature cleanup was done.
10. Vercel connector denied deployment listing (403). Production deployer is not
    verified; no identity is inferred from Git commits. No CLI credentials were
    available. Owner can provide deployment activity evidence or authorize browser
    fallback; do not deploy while this question is open.

## Validation

- Python suite: 230 discovered, 168 passed, 62 PostgreSQL-dependent skipped.
- Backup unit tests: 15 passed (guard conditions, date cutoff, destination privacy,
  dated root commit, retention month/year boundaries, restore-target rejection).
- Node client workflow checks passed with stub transport; no visual browser QA.
- Both GitHub `test` checks on code commit
  `1a6b0793093229e6e5f5dbff2010649a6f2643d3` completed successfully.
- These checks are not a live export, Neon test or restore proof.

## Approval sequence

Review the retrospective publication record first. The new SELECT is committed
as ops/sql/backup-synthetic-check.sql; record its exact commit SHA and test it on
an isolated Neon branch before owner-approved live execution under POLICY.md.
Do not merge to trigger production deployment; the owner requested a production
pause. Resolve privacy, credentials, data handling and protection before activation.
