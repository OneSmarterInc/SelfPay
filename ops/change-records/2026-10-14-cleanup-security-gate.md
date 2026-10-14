# October 14 cleanup authorization and security gate

Status: BLOCKED — no deletion, recovery-branch creation, or backup activation executed in this follow-up.

## Owner authorization

On October 14, 2026, the owner approved deletion of the four members, six conversations, one preference and one correction previously listed in 2026-10-14-test-row-cleanup.md, conditional on verification that all are synthetic, exact current counts, and documentation. Stop if any may be real. The owner approved one isolated seven-day Neon recovery branch as an exception to GitHub-file-only backups, with deletion after seven days only if recovery verification succeeds. Daily private GitHub backups may be enabled only after cleanup and synthetic checks pass. No paid services, budget changes, production credential changes, website changes or Vercel changes are authorized.

Exact proposed deletion SQL remains ops/sql/remove-test-members-2026-10-14.sql at 4b9fd22e30062c815ea8f4d613ce428eee484146. Conditional authorization does not establish completed prerequisites or synthetic provenance. The earlier DRAFT record has not been executed.

## Credential investigation

Using authenticated Neon management retrieval, compared the previously captured temporary-branch credential with the current production neondb_owner credential entirely in memory. Only equality booleans were emitted: same role true, same password true. No SQL login was attempted using the captured credential, no password was printed, and no production credential was changed. This confirms credential reuse with production, not evidence of unauthorized database access.

The temporary branch is br-hidden-mode-b77xkrb0, parent br-rapid-mouse-b7clh18t, with parent-data initialization. Temporary-branch password rotation performed during the preceding restore did not contain production reuse. Stop using the exposed credential. Coordinated rotation of the production role, updates to every dependent connection secret, verification of connections, and review of available access evidence require owner approval. Do not independently rotate a production password or alter Vercel.

## Synthetic classification gate

Earlier isolated clone check confirmed four listed non-guest members, six related conversations, one preference, one correction, and zero related sessions/guest_usage at clone time; this is not fresh live-state verification. A local inspection of the existing October 12 dump found no explicit is_test/is_synthetic/source metadata columns in these tables and no synthetic/fixture or reserved example-domain markers in member name/email fields. Only schema/count/marker aggregates were emitted; personal fields were not displayed. Absence of markers does not prove real data, but available evidence does not establish that these exact records are synthetic. Owner-provided test provenance mapped to the listed IDs is needed before deletion can safely proceed. Do not treat structural export checks as proof of synthetic provenance.

No new recovery branch was created because cleanup prerequisites remain unsatisfied; the seven-day authorization is retained for the immediately-preceding-live-write recovery point. No seven-day deletion task exists yet because there is no new branch or verified recovery outcome to target.

## Validation and unchanged systems

All 19 local backup Python tests passed in this follow-up. Main vercel.json was read and still disables main deployment and automatic aliasing. No workflow was dispatched, no budget or Usage blocked setting changed, no paid service enabled, no deployment made, no database rows deleted, and no production credential changed. Daily backup activation remains pending. Earlier successful isolated restore evidence remains run 38566059343, source backup commit 892343ff15544204a5fab6fecb7369f255af35f9; it is not a current pre-write backup.

October 9 session-log investigation remains deferred until the owner supplies the original log. Do not infer missing operator or approval evidence.
