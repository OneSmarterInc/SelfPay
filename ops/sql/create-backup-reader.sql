-- Preparation for a dedicated backup reader. No password and no LOGIN.
-- Test on a separate branch first; obtain live approval and a fresh verified backup.
BEGIN;
DO $$
BEGIN
  IF current_database() <> 'neondb' THEN
    RAISE EXCEPTION 'Expected neondb';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'selfpay_backup_reader') THEN
    RAISE EXCEPTION 'Role already exists: inspect it instead of overwriting permissions';
  END IF;
END $$;
CREATE ROLE selfpay_backup_reader NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
GRANT CONNECT ON DATABASE neondb TO selfpay_backup_reader;
GRANT pg_read_all_data TO selfpay_backup_reader;
ALTER ROLE selfpay_backup_reader SET default_transaction_read_only = on;
COMMENT ON ROLE selfpay_backup_reader IS 'Dedicated MySelfPay backup reader; enable LOGIN only after approval and secure password setup.';
COMMIT;
