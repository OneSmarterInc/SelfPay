# Coordinate-only publication for the Boise search

Status: tested and authorized for the scoped coordinate publication; live execution not yet performed.

## Authorization and scope

The user approved the proposed live coordinate import and empty-results message fix with “yes do it”. Earlier in this conversation the user explicitly requested doing the work directly in Vercel Storage without a Neon branch copy. This record documents that user-directed exception; it does not claim a Neon-copy test or independently verified Vikram identity.

Executor: Codex, acting through the authenticated Vercel Storage query UI after PostgreSQL integration checks pass.

## Exact change

- SQL: `ops/sql/publish-coordinates-2026-10-09.sql` at commit `410b3da4ad1f5a3ebd75a8a18268e7233823aa54`.
- Verification: `ops/sql/verify-coordinates-2026-10-09.sql`.
- Rollback: `ops/sql/rollback-coordinates-2026-10-09.sql`.
- Prior batch: `8e7d7758-6c76-4fb3-9803-825cc1f77567`.
- New batch: `85c7c95d-a9dd-5533-9427-6fdcefc74ab9`.
- Preserve all 103 entries and all 13 priced offers; add coordinates to 95 entries. Programs and unresolved locations retain empty location lists.
- Clone the current batch, adding only `locations` and `location_type`; preserve all original provider descriptions, prices, restrictions and source fields. Keep the prior batch intact for rollback.
- Reject changes to the expected active batch, entry/offer counts, full fingerprints, or individual source hashes. Execute atomically.
- Offline Census coordinates and the evidence rules already in this PR are used; no member location is sent externally.

The 99-entry directory-data bundle plus four additional live entries were used for geography. The full 103-entry/13-offer public catalog observed in the Storage status result is retained as the regression fixture. No member records or credentials are included.

## Validation

The Boise regression test uses the screenshot's MRI/knee/both-contrast/250-mile/$2,000 filters. With the coordinate patch it returns a nearby candidate within 10 miles. Contrast and price scope still require confirmation; this is not a guarantee that the requested protocol is included.

The exact SQL has disposable-local-PostgreSQL tests for preservation of every original entry field, canonical hashes, unchanged offers, rollback, changed-catalog rejection and stale-batch rejection. CI passed: https://github.com/OneSmarterInc/SelfPay/actions/runs/37922331687 (job 113792981476). The exact committed SQL passed on disposable local PostgreSQL, including all three publication/rollback/fail-closed integration tests. This is not a Neon branch-copy test; the user-directed exception above applies.

## Boundaries

This does not publish the repository's separate 57-offer mapping set, change prices, enable Directory sync, modify database roles, delete data, merge the data branch, or deploy production code. The improved empty-results explanation is a code change on PR #12.

## Execution evidence

Pending.
