import unittest
from types import SimpleNamespace
from unittest.mock import patch
import io, json
import directory_sync as d

class GuardDiagnostics(unittest.TestCase):
    def test_exact_messages_only(self):
        for message, code in d.DATABASE_GUARD_ERRORS.items():
            exc = RuntimeError('PRIVATE URL AND PASSWORD')
            exc.sqlstate = 'P0001'
            exc.diag = SimpleNamespace(message_primary=message)
            self.assertEqual(d.database_guard_error(exc), code)
            exc.diag.message_primary += ' PRIVATE'
            self.assertIsNone(d.database_guard_error(exc))
            exc.diag.message_primary = message
            exc.sqlstate = '08001'
            self.assertIsNone(d.database_guard_error(exc))
    def test_output_redaction(self):
        exc = RuntimeError('PRIVATE URL AND PASSWORD')
        exc.sqlstate = 'P0001'
        exc.diag = SimpleNamespace(message_primary='directory sync: bootstrap requires the reviewed active batch')
        out = io.StringIO()
        with patch.object(d, 'sync', side_effect=exc), patch('sys.stderr', out), patch('sys.argv', ['directory_sync.py','sync','unused.json']):
            self.assertEqual(d.main(), 1)
        self.assertEqual(json.loads(out.getvalue())['error'], 'bootstrap_active_batch_mismatch')
        self.assertNotIn('PRIVATE', out.getvalue())
