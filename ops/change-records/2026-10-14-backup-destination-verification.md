# Backup destination verification and remaining tasks — 2026-10-14

## Requested destination

The owner requests the existing separate repository SelfPay_Backup as the backup destination, not a new backup branch in the application repository. Do not create another repository or branch unnecessarily.

Verification is BLOCKED on the exact repository identity/access: authenticated GitHub metadata lookup for OneSmarterInc/SelfPay_Backup returned HTTP 404, and repository search for SelfPay_Backup returned no results. A private repository may be inaccessible; this is not proof it does not exist. Obtain the exact URL and connected GitHub access before changing operational backup configuration.

## Confirmed existing recovery point

OneSmarterInc/MySelfPay_Backup exists and is private (repository ID 1415505379). Its default branch is backup-2026-10-12. The default root contains database-2026-10-12.sql, 1,168,881 bytes, Git blob b66604c89b430ea7f172f3038719b2c1bcb2bd25. This matches the immutable dump previously restored from commit 892343ff15544204a5fab6fecb7369f255af35f9.

Restore run https://github.com/OneSmarterInc/SelfPay/actions/runs/38566059343 was rechecked and is completed/success. The earlier isolated restore verified 105 entries, 57 offers, 98 located entries, 132 locations and 7 programs, with sessions/login_limits/guest_usage empty. See 2026-10-14-dev-task-status.md, Successful isolated restore section. This establishes an October 12 recovery point in MySelfPay_Backup, not the existence or contents of SelfPay_Backup and not a current pre-deletion recovery point. No new restore was run during this verification.

## Remaining task list

- Verify the exact URL, private visibility, immutable backup files and restore evidence for the requested SelfPay_Backup repository. Treat it as the requested destination pending verification; do not silently substitute or change the currently configured destination.
- Complete coordinated production credential containment using the authorized maintenance plan; the existing access/handoff blocker remains. See 2026-10-14-maintenance-containment.md.
- Obtain creation evidence linking each of the four member IDs to synthetic test accounts. Leave all records untouched until evidence is sufficient.
- Before any deletion, create and verify a fresh recovery point and perform isolated restoration/copy testing. Preserve the approved seven-day recovery-branch exception and retention requirements; the October 12 dump alone is insufficient for a later deletion.
- Only after the cleanup and synthetic checks pass, configure daily backups to the verified requested repository and verify a successful backup. Keep the GitHub Actions budget at $0 and Usage blocked unchanged.
- Complete the remaining recovery-drill scheduling and branch-protection review, and obtain the October 9 original session log when available.

## Changes and limits this turn

Documentation only. No repository or branch created, no database rows deleted, no production or Vercel change, no workflow dispatched, and no budget setting changed. No dump contents or database credentials were retrieved for this verification.
