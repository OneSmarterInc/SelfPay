import sqlite3
import unittest
from synthetic_guard import NonSyntheticData, require_synthetic


class SyntheticGuardTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.execute("ATTACH DATABASE ':memory:' AS public")
        self.db.executescript('CREATE TABLE public.members(tenant TEXT); CREATE TABLE public.conversations(id TEXT); CREATE TABLE public.corrections(created REAL);')
        self.addCleanup(self.db.close)

    def test_guest_only_allowed(self):
        self.db.execute("INSERT INTO public.members VALUES ('guest')")
        require_synthetic(self.db.cursor())

    def test_non_guest_stops(self):
        self.db.execute("INSERT INTO public.members VALUES ('member')")
        with self.assertRaises(NonSyntheticData): require_synthetic(self.db.cursor())

    def test_null_tenant_stops(self):
        self.db.execute('INSERT INTO public.members VALUES (NULL)')
        with self.assertRaises(NonSyntheticData): require_synthetic(self.db.cursor())

    def test_conversation_stops(self):
        self.db.execute("INSERT INTO public.conversations VALUES ('synthetic-test')")
        with self.assertRaises(NonSyntheticData): require_synthetic(self.db.cursor())

    def test_correction_date_boundary(self):
        self.db.execute('INSERT INTO public.corrections VALUES (1791829799)')
        require_synthetic(self.db.cursor())
        self.db.execute('INSERT INTO public.corrections VALUES (1791829800)')
        with self.assertRaises(NonSyntheticData): require_synthetic(self.db.cursor())

    def test_owner_test_exception_is_date_limited(self):
        self.db.execute("INSERT INTO public.members VALUES ('member')")
        self.db.execute("INSERT INTO public.conversations VALUES ('demo')")
        require_synthetic(self.db.cursor(), approved_test_date='2026-10-12', today='2026-10-12')
        for approval, today in [('', '2026-10-12'), ('2026-10-12', '2026-10-13'),
                                ('2026-10-13', '2026-10-13'), ('2026-10-12', '')]:
            with self.subTest(approval=approval, today=today):
                with self.assertRaises(NonSyntheticData):
                    require_synthetic(self.db.cursor(), approved_test_date=approval, today=today)

    def test_owner_exception_still_stops_recent_corrections(self):
        self.db.execute('INSERT INTO public.corrections VALUES (1791829800)')
        with self.assertRaises(NonSyntheticData):
            require_synthetic(self.db.cursor(), approved_test_date='2026-10-12', today='2026-10-12')
