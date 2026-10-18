import io
import json
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import core
from server import Handler

class DirectorySummaryTests(unittest.TestCase):
    def test_active_counts_update_without_authentication(self):
        with tempfile.NamedTemporaryFile(suffix='.sqlite3') as f:
            db=sqlite3.connect(f.name)
            db.executescript("CREATE TABLE settings(key TEXT,value TEXT); CREATE TABLE entries(batch_id TEXT,payload TEXT); INSERT INTO settings VALUES('active_batch','new');")
            db.executemany('INSERT INTO entries VALUES(?,?)', [('old',json.dumps({'states':'TX'})),('new',json.dumps({'states':'CA; NY; DC','locations':[{'state':'CA'}]}))])
            db.commit()
            self.assertEqual(core.directory_summary(f.name),{'listing_count':1,'state_count':2})
            db.execute('INSERT INTO entries VALUES(?,?)',('new',json.dumps({'states':'TX'})));db.commit()
            h=object.__new__(Handler);h.path='/api/directory-summary'
            h.validate_origin=lambda:True;h.database_path=lambda:f.name
            result=[];h.respond=lambda status,data:result.append((status,data))
            with patch.object(core,'session',side_effect=AssertionError('Must not require a session')):
                h.route_selfpay_request('GET')
            self.assertEqual(result,[(200,{'listing_count':2,'state_count':3})])
            db.close()
