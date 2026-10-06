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
            self.assertEqual(result['eligible_records'],{'sessions':1,'conversations':1,'login_limits':1})
            with core.connect(path) as db:
                self.assertEqual(db.execute('SELECT token_hash FROM sessions').fetchone()['token_hash'],'live')
                self.assertEqual(db.execute('SELECT id FROM conversations').fetchone()['id'],'live')
            self.assertEqual(sum(cleanup(path,apply=True,now=100)['eligible_records'].values()),0)
