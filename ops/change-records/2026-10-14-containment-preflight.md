# Credential containment preflight and member provenance — October 14, 2026

Status: BLOCKED before mutation. Owner authorized coordinated production credential rotation and dependent-secret updates, with a mandatory stop if any step risks downtime or data loss. No password was rotated, no secret updated, and no deployment made in this follow-up.

## Containment prerequisite

Authenticated Vercel team discovery returned team_mDffZ9InDqmbPNVwRaFJvgEC / 1smarterincs-projects. Environment metadata lookup (decrypt=false) for myselfpay-review returned 404 Project not found both with the team slug and explicit verified team ID. Project discovery under that team with search=selfpay returned zero projects. This is an access/target-discovery blocker, not evidence that the deployed site no longer exists.

Without verified access to update all dependent connection configurations and verify the deployed website, an in-place database password reset risks connection failures. Per the owner's instruction, stop before rotation. Reconnect Vercel with access to the actual SelfPay project or identify its current project/team. Browser fallback has not been used. Prepare and review the deployment cutover before invalidating the old password; no zero-downtime guarantee is established. The previously confirmed exposed production credential remains uncontained.

## Provenance search

Reviewed current main tree c35e49ca58b5daaa5db0300df5c9d68535fec6be and searched 54 source/test/fixture/change-record files plus 10 non-CSV seed files, all retrieved successfully. Also searched available local source copies. Matching IDs occur only in the prepared cleanup record among these inspected files. No original member-creation log linking any target ID to a synthetic test run was located. This does not claim an exhaustive search of inaccessible external logs or all Git history.

- f8f89ee1-66e7-4e42-a848-ca3d6e4f5c51 — reference: ops/change-records/2026-10-14-test-row-cleanup.md; identifies deletion scope, not creation provenance.
- 12dca885-1548-43d2-b219-46d04095c26e — same reference; no creation provenance found.
- 24651e6b-7cf9-43b5-8b90-6a521679c6a7 — same reference; no creation provenance found.
- bcd03d50-9604-43a7-be0b-5f1ec5594794 — same reference; no creation provenance found.

Supporting scope references: setup_hosted.py initializes directory data and explicitly reports no local member data copied; tests/fixtures contains directory fixtures; core.py allocates member IDs dynamically with uuid4. Generic test scripts do not prove which run created these exact database rows.

Missing for each ID: an original test execution/creation record mapping the returned ID to a synthetic test case, with run timestamp and script/test reference (or equivalent reliable creation audit evidence). Do not infer synthetic status from names, activity, or deletion-scope counts. Records remain untouched.

## Safeguards

No production SQL, data deletion, recovery branch creation, Actions dispatch, budget change, paid-service activation, or Vercel mutation occurred. The approved seven-day pre-write recovery requirement and GitHub-only daily backup destination remain in force. Daily backups remain blocked on synthetic verification and cleanup. No new executable code was changed; the immediately preceding backup suite result remains 19 passing tests. No post-rotation connection verification is claimed because no rotation occurred.
