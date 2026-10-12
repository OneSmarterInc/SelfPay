"""Exact coordinate publication against a disposable local PostgreSQL database.

The fixture contains public directory data observed through the storage UI;
no member records or credentials. Local/reset guards are inherited from base.
"""
import json
import unittest
from unittest.mock import patch
from pathlib import Path
import core
import test_directory_sync_postgres as base

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT/'tests/fixtures/coordinate-baseline-2026-10-09.json').read_text())
SQL = (ROOT/'ops/sql/publish-coordinates-2026-10-09.sql').read_text()
ROLLBACK = (ROOT/'ops/sql/rollback-coordinates-2026-10-09.sql').read_text()
NEW = '85c7c95d-a9dd-5533-9427-6fdcefc74ab9'

class BoiseSearchRegression(unittest.TestCase):
    def test_coordinate_patch_restores_nearby_candidate(self):
        patches=json.loads((ROOT/'ops/sql/coordinate-patches-2026-10-09.json').read_text())
        entries={e['entry_key']:json.loads(e['payload']) for e in DATA['entries']}
        for p in patches:
            entries[p['key']].update(locations=json.loads(p['locations_text']),location_type=p['location_type'])
        offers=[]
        for row in DATA['offers']:
            o=json.loads(row['payload']);o.update(entry=entries[row['entry_key']],version=NEW)
            offers.append(o)
        with patch.object(core,'catalog',return_value=dict(version=NEW,entries=list(entries.values()),offers=offers)):
            r=core.search(dict(mod='MRI',body='knee',contrast='unknown',location='Boise City, ID',radius=250,budget=2000))
        self.assertTrue(r['offers'])
        self.assertLess(r['offers'][0]['distance_miles'],10)
        self.assertIn('Boise',r['offers'][0]['entry']['name'])

@unittest.skipUnless(base.ENABLED, 'explicit local throwaway PostgreSQL/reset opt-in required')
class CoordinatePublication(unittest.TestCase):
    reset_roles = classmethod(base.DirectorySyncPostgres.reset_roles.__func__)
    setUpClass = classmethod(base.DirectorySyncPostgres.setUpClass.__func__)
    tearDownClass = classmethod(base.DirectorySyncPostgres.tearDownClass.__func__)

    def setUp(self):
        base.DirectorySyncPostgres.setUp(self)
        self.db.execute('TRUNCATE public.publish_events, public.offers, public.entries, public.batches, public.settings CASCADE')
        old = DATA['active_batch']
        self.db.execute('INSERT INTO public.batches VALUES(%s,%s,%s,0,%s,%s)', (old,'fixture','public-catalog','published','{}'))
        with self.db.cursor() as cur:
            cur.executemany('INSERT INTO public.entries VALUES(%s,%s,%s,%s)', [(old,e['entry_key'],e['content_hash'],e['payload']) for e in DATA['entries']])
            cur.executemany('INSERT INTO public.offers VALUES(%s,%s,%s,%s,%s,%s,%s)', [(old,o['id'],o['entry_key'],o['amount_cents'],o['max_cents'],o['price_type'],o['payload']) for o in DATA['offers']])
        self.db.execute("INSERT INTO public.settings VALUES('active_batch',%s)",(old,))

    def active(self):
        return self.db.execute("SELECT value FROM public.settings WHERE key='active_batch'").fetchone()[0]

    def test_exact_sql_preserves_catalog_and_rollback(self):
        self.db.execute(SQL)
        self.assertEqual(self.active(),NEW)
        rows = self.db.execute('SELECT entry_key,content_hash,payload FROM public.entries WHERE batch_id=%s',(NEW,)).fetchall()
        originals = {e['entry_key']:json.loads(e['payload']) for e in DATA['entries']}
        self.assertEqual(len(rows),103)
        located = 0
        for key,h,payload in rows:
            e=json.loads(payload)
            self.assertEqual(payload,core.canonical(e))
            self.assertEqual(h,core.digest({k:v for k,v in e.items() if k!='row'}))
            located += bool(e['locations'])
            e.pop('locations');e.pop('location_type')
            self.assertEqual(e,originals[key])
        self.assertEqual(located,95)
        fp=self.db.execute('SELECT selfpay_directory_sync.catalog_fingerprints(%s)',(NEW,)).fetchone()[0]
        self.assertEqual(fp['offer_fingerprint'],DATA['offer_fingerprint'])
        self.assertEqual(self.db.execute('SELECT count(*) FROM public.offers WHERE batch_id=%s',(NEW,)).fetchone()[0],13)
        self.db.execute(ROLLBACK)
        self.assertEqual(self.active(),DATA['active_batch'])
        self.assertEqual(self.db.execute('SELECT count(*) FROM public.entries WHERE batch_id=%s',(NEW,)).fetchone()[0],103)

    def test_changed_catalog_stops_without_partial_publication(self):
        self.db.execute("UPDATE public.entries SET payload=payload||' ' WHERE entry_key=%s",(DATA['entries'][0]['entry_key'],))
        with self.assertRaisesRegex(Exception,'entry fingerprint changed'):
            self.db.execute(SQL)
        self.assertEqual(self.active(),DATA['active_batch'])
        self.assertEqual(self.db.execute('SELECT count(*) FROM public.batches WHERE id=%s',(NEW,)).fetchone()[0],0)

    def test_stale_active_batch_stops(self):
        self.db.execute("UPDATE public.settings SET value='changed' WHERE key='active_batch'")
        with self.assertRaisesRegex(Exception,'active batch changed'):
            self.db.execute(SQL)
        self.assertEqual(self.active(),'changed')

if __name__=='__main__':unittest.main()
