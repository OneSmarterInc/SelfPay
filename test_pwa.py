import io
import json
import struct
import unittest
from unittest.mock import Mock
from api.index import handler
from core import ROOT

class PwaTests(unittest.TestCase):
    def request(self, path):
        h=object.__new__(handler)
        h.path=path
        h.headers={}
        h.wfile=io.BytesIO()
        h.sent={}
        h.status=None
        h.send_response=lambda status:setattr(h,'status',status)
        h.send_header=lambda k,v:h.sent.update({k:v})
        h.end_headers=lambda:None
        h.validate_origin=lambda:True
        h.database_path=Mock(side_effect=AssertionError('Static assets must not use database configuration'))
        h.do_GET()
        h.database_path.assert_not_called()
        self.assertEqual(h.status,200)
        return h

    def test_manifest_and_all_icons_are_public_and_binary_safe(self):
        h=self.request('/manifest.webmanifest')
        self.assertTrue(h.sent['Content-Type'].startswith('application/manifest+json'))
        manifest=json.loads(h.wfile.getvalue())
        self.assertEqual(manifest['display'],'standalone')
        self.assertEqual(manifest['start_url'],'/')
        self.assertEqual(manifest['scope'],'/')
        for icon in manifest['icons']:
            with self.subTest(icon=icon['src']):
                h=self.request(icon['src'])
                data=h.wfile.getvalue()
                self.assertEqual(h.sent['Content-Type'],'image/png')
                self.assertEqual(data[:8],b'\x89PNG\r\n\x1a\n')
                width,height=struct.unpack('>II',data[16:24])
                self.assertEqual(icon['sizes'],f'{width}x{height}')
                self.assertEqual(data,(ROOT/'static'/icon['src'].lstrip('/')).read_bytes())
        h=self.request('/icons/apple-touch-icon.png')
        self.assertEqual(struct.unpack('>II',h.wfile.getvalue()[16:24]),(180,180))

    def test_worker_and_offline_page_work_without_database(self):
        for path,mime in [('/sw.js','text/javascript'),('/pwa.js','text/javascript'),('/offline.html','text/html')]:
            h=self.request(path)
            self.assertTrue(h.sent['Content-Type'].startswith(mime))
            self.assertEqual(h.sent['Cache-Control'],'no-store')
            self.assertNotIn('Set-Cookie',h.sent)

    def test_home_links_pwa_assets(self):
        body=self.request('/').wfile.getvalue()
        for value in [b'/manifest.webmanifest',b'/pwa.js',b'/icons/apple-touch-icon.png',b'installHelp']:
            self.assertIn(value,body)
