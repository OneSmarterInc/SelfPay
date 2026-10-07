-- Run once as the owner in the intended MySelfPay database.
-- Intentionally fails if the role already exists: inspect it rather than reusing broad privileges.
CREATE ROLE selfpay_cleanup LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS;
DO $$ BEGIN
  EXECUTE format('GRANT CONNECT ON DATABASE %I TO selfpay_cleanup', current_database());
END $$;
GRANT USAGE ON SCHEMA public TO selfpay_cleanup;
GRANT SELECT, DELETE ON TABLE
  public.members, public.sessions, public.conversations,
  public.preferences, public.corrections, public.login_limits
TO selfpay_cleanup;
-- Set the password separately with psql: \password selfpay_cleanup
-- Never commit a password or a connection string.
-- No INSERT, UPDATE, schema CREATE, provider-table access or settings access granted.
-- PUBLIC grants and role memberships must also be reviewed by the database owner.
