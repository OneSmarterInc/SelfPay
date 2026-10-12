"""Export one consistent snapshot; requires a dedicated, audited read-only role."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from git_backup import backup_date, publish


def export():
    import psycopg2
    from psycopg2.extensions import parse_dsn
    os.umask(0o077)
    dsn = os.environ['BACKUP_DATABASE_URL']
    config = parse_dsn(dsn)
    if config.get('user') != 'selfpay_backup_reader':
        raise ValueError('Dedicated backup reader is required')
    if config.get('sslmode') not in ('require', 'verify-ca', 'verify-full'):
        raise ValueError('TLS is required')
    if config.get('host') != os.environ['BACKUP_EXPECTED_HOST'] or '-pooler.' in config['host']:
        raise ValueError('Use the approved direct live host')
    if os.environ.get('BACKUP_DATA_CLASS') != 'synthetic':
        raise ValueError('Only synthetic-data exports are approved')
    day = backup_date()
    with tempfile.TemporaryDirectory(prefix='selfpay-backup-') as tmp:
        root = Path(tmp)
        dump = root / 'database.sql'
        conn = psycopg2.connect(dsn, connect_timeout=30)
        try:
            conn.set_session(readonly=True, isolation_level='REPEATABLE READ')
            with conn.cursor() as cur:
                cur.execute("SELECT rolsuper, rolcreaterole, rolcreatedb, rolreplication, rolbypassrls FROM pg_roles WHERE rolname=current_user")
                if any(cur.fetchone()):
                    raise ValueError('Backup role must have no administrative privileges')
                cur.execute('SELECT pg_export_snapshot()')
                snapshot = cur.fetchone()[0]
                counts_sql = Path('ops/sql/backup-catalog-counts.sql').read_text()
                counts_sql = counts_sql.replace('BEGIN TRANSACTION READ ONLY;', '').replace('ROLLBACK;', '')
                cur.execute(counts_sql)
                if cur.fetchone() is None:
                    raise ValueError('Catalog verification returned no row')
                env = dict(os.environ, PGDATABASE=dsn, PGOPTIONS='-c default_transaction_read_only=on')
                # Never expose DSN in command arguments or subprocess error logs.
                subprocess.run(['pg_dump', '--format=plain', '--no-owner', '--no-acl',
                                '--snapshot=' + snapshot, '--file=' + str(dump)],
                               env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            conn.rollback()
        finally:
            conn.close()
        publish(dump, day)



if __name__ == '__main__':
    try:
        export()
    except Exception:
        print('Backup failed; no success recorded. Check configuration and credentials privately.', file=sys.stderr)
        sys.exit(1)
