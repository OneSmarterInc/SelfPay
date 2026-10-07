# Cleanup database role setup

Current application access is guest-only. The historical register, login,
change_password and PBKDF2 functions in core.py are explicitly marked legacy
compatibility code. Their HTTP routes return 410. They are not active sign-in
paths; removing historical schema/test compatibility is a separate migration.

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
6. Verify the role can SELECT/DELETE on the six named tables but cannot
   INSERT/UPDATE there, read provider entries/offers/settings, or CREATE tables.
   SELECT/DELETE permissions also support the table locks introduced in PR #5.

No live role, password or GitHub secret has been provisioned by this change.
The old cleanup secret remains in effect until the owner replaces it.

These grants restrict table operations, not which rows may be deleted: the
cleanup program enforces expiry and guest eligibility. A stored-procedure-only
role would provide tighter row-level control if required before real data use.
This setup alone does not authorize PHI use or establish regulatory compliance.
