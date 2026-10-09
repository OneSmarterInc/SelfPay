# Manual directory update — preparation record
Status: BLOCKED before Neon branch testing and live approval.
Prepared by Codex on 9 October 2026 at the user's request.

Purpose: replace automatic sync temporarily with reviewed manual stage/publish/rollback.
Scope of this commit: CLI safety fixes, mock regression tests and a runbook. No database queries or changes.

Changes:
- Hosted CLI does not run core.initialize, including list.
- PostgreSQL URL strings passed through --db retain their original form.
- Stage requires explicit mappings rather than silently falling back to seed files.

Validation: three isolated mock unit tests passed. No database connection used. No Neon copy test performed.
Runbook: docs/manual-directory-updates.md.
Importer: import_directory.py; tests: test_import_directory_cli.py.
Live SQL file/commit package: pending.
Workbook and mappings fingerprints: pending selection and review.
Test branch ID/results: pending.
Executor, live window and rollback authorization: pending.
Vikram approval: PENDING, not implied by the request to prepare this workflow.
New/prior live batch IDs: no publication performed.

Do not mark this record approved or complete until the runbook blockers are resolved.
