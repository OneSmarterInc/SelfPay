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
