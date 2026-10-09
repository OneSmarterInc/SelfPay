import unittest
from unittest.mock import patch
from pathlib import Path
import core

class PrivacyTests(unittest.TestCase):
    def test_guest_read_and_write_do_not_connect(self):
        with patch.object(core,'connect',side_effect=AssertionError('Unexpected storage access')):
            self.assertEqual(core.preference({'tenant':'guest','id':'synthetic'}),{})
            with self.assertRaises(PermissionError):core.preference({'tenant':'guest','id':'synthetic'},{'location':'45402'})
    def test_no_geolocation_or_remember_control(self):
        js=Path('static/app.js').read_text()
        self.assertNotIn('navigator.geolocation',js)
        self.assertNotIn('id="remember"',js)
    def test_access_logging_disabled(self):
        import server
        from contextlib import redirect_stderr,redirect_stdout
        import io
        out=io.StringIO()
        with redirect_stdout(out),redirect_stderr(out):server.Handler.log_message(None,'synthetic location %s','45402')
        self.assertEqual(out.getvalue(),'')

if __name__=='__main__':unittest.main()
