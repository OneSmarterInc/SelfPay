import io
import unittest
from pathlib import Path
from unittest.mock import patch
import core
from server import Handler

class PublicPagesTests(unittest.TestCase):
    def test_pages_are_public_and_contact_links_are_present(self):
        for slug in ('about','contact','privacy','terms','privacy-terms','for-imaging-centers'):
            h=object.__new__(Handler);h.path='/'+slug;h.validate_origin=lambda:True
            h.database_path=lambda:self.fail('Public page must not access database')
            output=[];h.respond=lambda status,data,**kw:output.append((status,data,kw))
            with patch.object(core,'ROOT',Path(__file__).resolve().parent):h.route_selfpay_request('GET')
            self.assertEqual(output[0][0],200)
            page=output[0][1].decode()
            self.assertIn('mailto:' + ('partners@onesmarter.com' if slug == 'for-imaging-centers' else 'care@onesmarter.com'),page)
            self.assertNotIn('src="/app.js"',page)
            self.assertNotIn('<button id="profile"',page)

    def test_map_policy_is_limited_to_openstreetmap(self):
        h=object.__new__(Handler);h.wfile=io.BytesIO();headers={}
        h.send_response=lambda status:None;h.send_header=lambda k,v:headers.update({k:v});h.end_headers=lambda:None
        h.respond(200,{'ok':True})
        self.assertIn('frame-src https://www.openstreetmap.org;',headers['Content-Security-Policy'])
        self.assertIn("frame-ancestors 'none'",headers['Content-Security-Policy'])
