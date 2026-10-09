# Cleanup database role setup

The old password authentication functions and their tests have been removed.

## Activate the restricted cleanup connection

1. As database owner, run ops/create_cleanup_role.sql in the intended review
   database. It creates selfpay_cleanup without owner/superuser privileges.
2. Set a generated password securely using psql's interactive
   \password selfpay_cleanup command, or the database provider's role editor.
   Do not put it in a SQL file, shell command, chat or repository.
3. Review inherited PUBLIC privileges and role memberships. The role must not
   own tables, inherit privileged roles, or have CREATE rights on public schema.
4. Set GitHub secret SELFPAY_CLEANUP_DATABASE_URL to a TLS connection for this
   role and the intended database. Do not change the application's DATABASE_URL.
5. Run Daily retention cleanup manually with apply=false. Review counts, then
   run with apply=true. Confirm the next scheduled run succeeds.
6. Verify the role can SELECT/DELETE on the seven named tables (including guest_usage) but cannot
   INSERT/UPDATE there, read provider entries/offers/settings, or CREATE tables.
   SELECT/DELETE permissions also support the table locks introduced in PR #5.

No live role, password or GitHub secret has been provisioned by this change.
As verified on 9 October 2026, SELFPAY_CLEANUP_DATABASE_URL is absent in GitHub Actions. Manual dry run 37929614670 stopped before connecting. Configure the restricted connection securely before retrying; never substitute the importer or owner URL.

These grants restrict table operations, not which rows may be deleted: the
cleanup program enforces expiry and guest eligibility (no live session). A stored-procedure-only
role would provide tighter row-level control if required before real data use.
This setup alone does not authorize PHI use or establish regulatory compliance.


## Verified follow-up (9 October 2026, 13:02 UTC)

After the user added SELFPAY_CLEANUP_DATABASE_URL and reported creating selfpay_cleanup, manual dry run 37934081076 passed. The earlier missing-secret finding is resolved. Full result: ops/change-records/2026-10-09-cleanup-dry-run.md. This read-only run does not independently verify role identity, DELETE grants or a successful scheduled deletion.
