# Manual directory update procedure (temporary)
Status: preparation only. NOT authorized for live execution.
Follow ops/change-records/POLICY.md. Directory sync remains disabled.

## 1. Prepare the change
Create a record from ops/change-records/TEMPLATE.md. Pin the exact importer/core commit, workbook SHA-256, source version and mappings SHA-256. Do not use seed/mappings.json simply because it exists: it is older seed data and has not been validated against the current 13 hosted offers.

Use reviewed mappings that preserve the active offers, their exact service/contrast/price scope and source entry hashes. Changed or missing source records cause offers to be withheld. Every withheld offer, deletion, rename and price change needs explicit review.

The importer executes SQL embedded in core.py. Under the committed policy, the SQL used for stage, publish, verification and rollback must also be captured in committed SQL files, referenced in the change record, and checked against the pinned code before live execution. That SQL review package is not yet prepared; do not treat these commands as permission to bypass it.

## 2. Create a test database branch
An authorized Neon operator creates a branch copy from the intended live branch. Record its ID, parent, copy time and target database. Confirm it differs from live. Use the secure connection selector to set DATABASE_URL to the COPY, without pasting it into chat, commits or logs.
Do not use a Vercel Preview as proof of database isolation.

## 3. Stage and review on the copy
Run from the pinned code checkout:
```sh
python import_directory.py stage /path/to/workbook.xlsx --mappings /path/to/reviewed-mappings.json
```
Capture the JSON report: id, status, entry_count, added, changed, removed, offer_count and withheld_offers.
Staging writes a proposed batch; it does not activate it. The hosted CLI no longer initializes schemas implicitly. The copy must have the expected schema.

Record the prior active batch using approved verification SQL. Compare actual content, not only counts. Review source links, dates, inclusions, exclusions and price types.

An unchanged=true result reuses an existing batch/report: that report may reflect its original staging baseline. Do not treat it as a fresh comparison against today's active batch. Obtain a new approved comparison before publication.

## 4. Rehearse publication and recovery on the copy
Test publish using the COPY batch ID, verify the catalog, then test rollback to the COPY prior active batch:
```sh
python import_directory.py publish <copy_batch_id>
python import_directory.py rollback <copy_prior_batch_id>
```
The current publish function has no expected-active concurrency guard. This remains a live-use risk: an exclusive maintenance procedure or an implemented/tested guard must be reviewed before approval. Rollback uses the same core publish operation to select a retained batch; it is not a full database restore. Explicitly verify rollback records and catalog contents.

## 5. Approval gate
Send the report and completed record to Vikram for explicit approval of exact files/commits, target, publication and recovery.
No live command, including list or staging, may run before approval.
Mock/unit tests do not replace Neon branch testing.

## 6. Approved live execution (future; currently blocked)
Use identical pinned code, workbook bytes and reviewed mappings. Change DATABASE_URL through a secure mechanism to the approved live target. Stage first and compare the report with the approved expectations. Stop on any unexpected result or changed baseline.
Use the batch ID returned by LIVE staging, not the test-copy ID. Publish only within approved scope. Record new and prior batch IDs from the publication result and verify the website/catalog.
Rollback is permitted only by the approved recovery plan and target state.

## 7. Cleanup
After successful verification and saved evidence, confirm the exact test branch is no longer needed and delete only that branch. Never delete the live or unrelated branches. No test branch was created or deleted by this documentation change.

## Current blockers
- No Neon branch-management or query connection is available in this session.
- Copy creation, branch testing and reports remain pending.
- Current reviewed mappings, source bundle and committed SQL review package remain pending.
- Publication concurrency protection/procedure requires review.
- Vikram approval and live execution remain pending.
