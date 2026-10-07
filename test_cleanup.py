import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import core
from cleanup import cleanup

class CleanupTests(unittest.TestCase):
    def test_dry_run_and_expiry_boundaries(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(core,'DEMO_PASSWORD',None):
            path=Path(folder)/'test.db';core.initialize(path)
            with core.connect(path) as db:
                self.assertEqual(db.execute('SELECT COUNT(*) AS n FROM members').fetchone()['n'],0)
                db.execute('CREATE TABLE login_limits(key TEXT, window_id INTEGER, attempts INTEGER)')
            a=core.guest_login(path)
            with core.connect(path) as db:
                db.execute('UPDATE sessions SET expires=100 WHERE member_id=?',(a['member']['id'],))
                db.execute('INSERT INTO sessions VALUES(?,?,?,?)',('live',a['member']['id'],'csrf',101))
                for ident,expiry in [('expired',100),('live',101)]:
                    db.execute('INSERT INTO conversations VALUES(?,?,?,?,?,?,?)',(ident,'guest',a['member']['id'],'test','{}',0,expiry))
                db.execute('INSERT INTO login_limits VALUES(?,?,?)',('old',-2,1))
            self.assertEqual(cleanup(path,now=100)['eligible_records']['sessions'],1)
            with core.connect(path) as db:self.assertEqual(db.execute('SELECT COUNT(*) AS n FROM sessions').fetchone()['n'],2)
            result=cleanup(path,apply=True,now=100)
            self.assertEqual(result['eligible_records'],{'sessions':1,'conversations':1,'login_limits':1,'guest_members':0,'preferences':0,'corrections':0})
            with core.connect(path) as db:
                self.assertEqual(db.execute('SELECT token_hash FROM sessions').fetchone()['token_hash'],'live')
                self.assertEqual(db.execute('SELECT id FROM conversations').fetchone()['id'],'live')
            self.assertEqual(sum(cleanup(path,apply=True,now=100)['eligible_records'].values()),0)

    def test_guest_dependencies_and_retention(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(core,'DEMO_PASSWORD',None):
            path=Path(folder)/'guests.db';core.initialize(path)
            with core.connect(path) as db:db.execute('CREATE TABLE login_limits(key TEXT, window_id INTEGER, attempts INTEGER)')
            check_guest_retention(self,path)


def check_guest_retention(test,path):
    import uuid
    prefix='cleanup-'+str(uuid.uuid4())
    ids={label:prefix+label for label in ('unused','session','conversation','registered')}
    with core.connect(path) as db:
        for label,ident in ids.items():
            tenant='review' if label=='registered' else 'guest'
            db.execute('INSERT INTO members VALUES(?,?,?,?,?,?)',(ident,tenant,ident+'@example.test','Synthetic','x','x'))
            db.execute('INSERT INTO preferences VALUES(?,?,?)',(ident,tenant,'{}'))
            db.execute('INSERT INTO corrections VALUES(?,?,?,?,?,?,?,?,?)',(ident,tenant,ident,'offer','batch','Other','Synthetic',0,'pending'))
        db.execute('INSERT INTO sessions VALUES(?,?,?,?)',(prefix+'expired',ids['unused'],'x',100))
        db.execute('INSERT INTO sessions VALUES(?,?,?,?)',(prefix+'live',ids['session'],'x',101))
        for label,expiry in [('unused',100),('conversation',101)]:
            db.execute('INSERT INTO conversations VALUES(?,?,?,?,?,?,?)',(prefix+label,'guest',ids[label],'Synthetic','{}',0,expiry))
    dry=cleanup(path,now=100)
    test.assertGreaterEqual(dry['eligible_records']['guest_members'],1)
    with core.connect(path) as db:test.assertIsNotNone(db.execute('SELECT id FROM members WHERE id=?',(ids['unused'],)).fetchone())
    cleanup(path,apply=True,now=100)
    with core.connect(path) as db:
        for table,col in [('members','id'),('preferences','member_id'),('corrections','member_id'),('sessions','member_id'),('conversations','member_id')]:
            test.assertEqual(db.execute(f'SELECT COUNT(*) AS n FROM {table} WHERE {col}=?',(ids['unused'],)).fetchone()['n'],0)
        for label in ('session','conversation','registered'):
            test.assertIsNotNone(db.execute('SELECT id FROM members WHERE id=?',(ids[label],)).fetchone())
            test.assertIsNotNone(db.execute('SELECT member_id FROM preferences WHERE member_id=?',(ids[label],)).fetchone())
            test.assertIsNotNone(db.execute('SELECT member_id FROM corrections WHERE member_id=?',(ids[label],)).fetchone())
    test.assertEqual(sum(cleanup(path,apply=True,now=100)['eligible_records'].values()),0)
