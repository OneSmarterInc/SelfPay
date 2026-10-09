"""PostgreSQL integration checks. Skipped unless TEST_DATABASE_URL points at a throwaway database.

Runs the hosted setup and the code paths that differ from SQLite: upserts with ON CONFLICT,
RETURNING in the login limiter, transaction rollback, and ownership-scoped writes.
"""
import os
import unittest
from unittest.mock import patch

URL = os.environ.get('TEST_DATABASE_URL', '')


@unittest.skipUnless(URL.startswith(('postgres://', 'postgresql://')), 'TEST_DATABASE_URL not set')
class PostgresIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import core
        import setup_hosted
        cls.core = core
        with core.connect(URL) as db:
            for table in ('guest_usage', 'corrections', 'preferences', 'conversations', 'sessions', 'members', 'publish_events',
                          'settings', 'offers', 'entries', 'batches', 'login_limits'):
                db.execute(f'DROP TABLE IF EXISTS {table} CASCADE')
        with patch.dict(os.environ, {'DATABASE_URL': URL, 'REVIEW_PASSWORD': 'Synthetic-Review-1'}):
            setup_hosted.setup()

    def test_catalog_published(self):
        data = self.core.catalog(URL)
        self.assertEqual((len(data['entries']), len(data['offers'])), (74, 57))

    def test_guest_sessions_are_separate(self):
        core=self.core
        a=core.guest_login(URL);b=core.guest_login(URL)
        self.assertNotEqual(a['member']['id'],b['member']['id'])
        member=core.session(a['token'],URL)
        self.assertEqual(member['tenant'],'guest')
        with self.assertRaises(PermissionError):
            core.preference(member,{'location':'Cincinnati, OH'},path=URL)
        with core.connect(URL) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) AS n FROM preferences WHERE member_id=?',(member['id'],)).fetchone()['n'],0)
        self.assertEqual(core.preference(core.session(b['token'],URL),path=URL),{})

    def test_database_backed_rate_limit(self):
        from api.index import handler
        h = object.__new__(handler)
        with patch.dict(os.environ, {'DATABASE_URL': URL}):
            results = [h.login_allowed('pg-limit-test', 3) for _ in range(5)]
        self.assertEqual(results, [True, True, True, False, False])

    def test_retention_cleanup(self):
        from cleanup import cleanup
        core=self.core;a=core.guest_login(URL)
        with core.connect(URL) as db:db.execute('UPDATE sessions SET expires=0 WHERE member_id=?',(a['member']['id'],))
        self.assertGreaterEqual(cleanup(URL)['eligible_records']['sessions'],1)
        cleanup(URL,apply=True)
        self.assertIsNone(core.session(a['token'],URL))

    def test_guest_dependency_cleanup(self):
        from test_cleanup import check_guest_retention
        check_guest_retention(self, URL)

    def test_failed_transaction_rolls_back(self):
        core = self.core
        with self.assertRaises(RuntimeError):
            with core.connect(URL) as db:
                db.execute("INSERT INTO settings VALUES('rollback-probe','x')")
                raise RuntimeError('abort')
        with core.connect(URL) as db:
            self.assertIsNone(db.execute("SELECT 1 FROM settings WHERE key='rollback-probe'").fetchone())


if __name__ == '__main__':
    unittest.main(verbosity=2)

