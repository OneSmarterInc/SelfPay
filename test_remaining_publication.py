"""Guarded completion publication, using public fixtures and local PostgreSQL only."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch
import core
import test_coordinate_publication as prior
import test_directory_sync_postgres as base

ROOT=Path(__file__).resolve().parent
SQL=(ROOT/'ops/sql/publish-remaining-2026-10-09.sql').read_text()
EXPECTED=json.loads((ROOT/'tests/fixtures/remaining-expected.json').read_text())
NEW='395c84be-d26d-5432-bddb-bff7c58c1200'

class CompletedCatalogSearch(unittest.TestCase):
    def test_dayton_city_zip_and_agent(self):
        entries={e['entry_key']:json.loads(e['payload']) for e in EXPECTED['entries']}
        offers=[dict(json.loads(o['payload']),entry=entries[o['entry_key']],version=NEW) for o in EXPECTED['offers']]
        catalog=dict(entries=list(entries.values()),offers=offers,version=NEW)
        required={'dir-58-mri-0','dir-59-mri-0','dir-63-mri-0','dir-64-mri-0'}
        with patch.object(core,'catalog',return_value=catalog):
            for location in ['Kettering, OH','45402']:
                r=core.search(dict(mod='MRI',body='knee',location=location))
                self.assertTrue(required <= {o['id'] for o in r['offers'] if o['distance_miles']<15})
            r=core.agent('knee MRI near Kettering, OH',{})
            self.assertTrue(required <= {o['id'] for o in r['offers'] if o['distance_miles']<15})
    def test_source_verified_sites_only(self):
        entries={json.loads(e['payload'])['name']:json.loads(e['payload']) for e in EXPECTED['entries']}
        self.assertEqual({x['zip'] for x in entries['Mosaic Diagnostics']['locations']},{'10460','11204','11414','11570'})
        self.assertTrue(any(x.get('zip')=='92037' for x in entries['Imaging Healthcare Specialists']['locations']))

@unittest.skipUnless(base.ENABLED,'local disposable PostgreSQL opt-in required')
class RemainingPublication(unittest.TestCase):
    reset_roles=classmethod(base.DirectorySyncPostgres.reset_roles.__func__)
    setUpClass=classmethod(base.DirectorySyncPostgres.setUpClass.__func__)
    tearDownClass=classmethod(base.DirectorySyncPostgres.tearDownClass.__func__)
    def setUp(self):
        prior.CoordinatePublication.setUp(self)
        self.db.execute(prior.SQL)
    def test_exact_sql_and_rollback(self):
        self.db.execute(SQL)
        for table,fields,key in [('entries','entry_key,content_hash,payload','entry_key'),('offers','id,entry_key,amount_cents,max_cents,price_type,payload','id')]:
            rows=self.db.execute(f'SELECT {fields} FROM public.{table} WHERE batch_id=%s ORDER BY {key}',(NEW,)).fetchall()
            expected=[tuple(e[f] for f in fields.split(',')) for e in sorted(EXPECTED[table],key=lambda e:e[key])]
            self.assertEqual(rows,expected)
        self.db.execute((ROOT/'ops/sql/rollback-remaining-2026-10-09.sql').read_text())
        self.assertEqual(self.db.execute("SELECT value FROM public.settings WHERE key='active_batch'").fetchone()[0],prior.NEW)
    def test_changed_entry_rejects_atomically(self):
        self.db.execute("UPDATE public.entries SET content_hash='changed' WHERE batch_id=%s",(prior.NEW,))
        with self.assertRaisesRegex(Exception,'Source entry changed'):self.db.execute(SQL)
        self.assertEqual(self.db.execute('SELECT count(*) FROM public.batches WHERE id=%s',(NEW,)).fetchone()[0],0)

if __name__=='__main__':unittest.main()
