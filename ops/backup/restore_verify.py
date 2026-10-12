"""Restore a trusted dump into an explicitly identified EMPTY disposable Neon branch.

Requires separate restore-owner credentials. Never use the read-only export URL.
Does not create branches or execute any query against live.
"""
import json
import os
from pathlib import Path
import subprocess
import sys

LIVE_BRANCH = 'br-rapid-mouse-b7clh18t'
LIVE_HOST = 'ep-blue-mouse-b7pil6vd.c-13.us-east-1.aws.neon.tech'


def validate_target(config, expected_branch, expected_host):
    if not expected_branch.startswith('br-') or expected_branch == LIVE_BRANCH:
        raise ValueError('A separate disposable Neon branch is required')
    host = config.get('host', '')
    if host != expected_host or host == LIVE_HOST or '-pooler.' in host or not host.endswith('.neon.tech'):
        raise ValueError('Use the verified disposable direct Neon endpoint')
    if config.get('sslmode') not in ('require', 'verify-ca', 'verify-full'):
        raise ValueError('TLS is required')


def restore(dump):
    import psycopg2
    from psycopg2.extensions import parse_dsn
    dsn = os.environ['RESTORE_DATABASE_URL']
    expected_branch = os.environ['RESTORE_BRANCH_ID']
    config = parse_dsn(dsn)
    validate_target(config, expected_branch, os.environ['RESTORE_EXPECTED_HOST'])
    marker = '-- SelfPay catalog snapshot: '
    manifests = [line[len(marker):] for line in Path(dump).read_text().splitlines() if line.startswith(marker)]
    if len(manifests) != 1:
        raise ValueError('Dump must contain exactly one snapshot count manifest')
    expected = json.loads(manifests[0])
    if not isinstance(expected, list) or len(expected) != 6 or not all(isinstance(x, str) for x in expected):
        raise ValueError('Invalid snapshot count manifest')
    with psycopg2.connect(dsn, connect_timeout=30) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_setting('neon.branch_id', true)")
            if cur.fetchone()[0] != expected_branch:
                raise ValueError('Restore branch identity mismatch')
            cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema')")
            if cur.fetchone()[0] != 0:
                raise ValueError('Restore target must be empty; no existing data will be deleted')
    env = {key: value for key, value in os.environ.items() if not key.startswith('PG')}
    for key, variable in {'host':'PGHOST','port':'PGPORT','user':'PGUSER','password':'PGPASSWORD',
                          'dbname':'PGDATABASE','sslmode':'PGSSLMODE','channel_binding':'PGCHANNELBINDING',
                          'sslrootcert':'PGSSLROOTCERT'}.items():
        if key in config: env[variable] = config[key]
    subprocess.run(['psql', '-X', '--set=ON_ERROR_STOP=1', '--single-transaction', '--file='+str(dump)],
                   env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    with psycopg2.connect(dsn, connect_timeout=30) as conn:
        conn.set_session(readonly=True)
        with conn.cursor() as cur:
            sql = (Path(__file__).parents[1]/'sql'/'backup-catalog-counts.sql').read_text()
            cur.execute(sql.replace('BEGIN TRANSACTION READ ONLY;', '').replace('ROLLBACK;', ''))
            actual = [str(value) for value in cur.fetchone()]
            if actual != expected:
                raise ValueError('Restored catalog counts differ from export snapshot')
            cur.execute('SELECT (SELECT count(*) FROM public.sessions), '
                        '(SELECT count(*) FROM public.login_limits), '
                        '(SELECT count(*) FROM public.guest_usage)')
            if tuple(cur.fetchone()) != (0, 0, 0):
                raise ValueError('Transient tables must exist with no restored rows')
    print('Restore verified: all six catalog fields match; transient tables exist and are empty.')


if __name__ == '__main__':
    try:
        restore(sys.argv[1])
    except Exception:
        # psql errors can contain row values and credentials. Never echo them.
        print('Restore failed. No success recorded; inspect the disposable branch privately.', file=sys.stderr)
        sys.exit(1)
