-- Run as database owner before using this Preview with an existing database.
-- No member text is added or copied.
CREATE TABLE IF NOT EXISTS guest_usage (
 session_hash TEXT PRIMARY KEY REFERENCES sessions(token_hash),
 member_id TEXT NOT NULL REFERENCES members(id), payload TEXT NOT NULL
);
-- If the restricted cleanup role already exists, grant access to the new table.
DO $$ BEGIN
 IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='selfpay_cleanup') THEN
   GRANT SELECT, DELETE ON public.guest_usage TO selfpay_cleanup;
 END IF;
END $$;
