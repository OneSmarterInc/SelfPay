import unittest
from unittest.mock import patch
import core
import geo

class GeoTests(unittest.TestCase):
    def test_city_ambiguity_and_qualified(self):
        self.assertGreater(len(geo.lookup('Dayton')),1)
        r=geo.lookup('Dayton, OH');self.assertEqual(len(r),1);self.assertEqual(r[0]['state'],'OH')
        self.assertEqual(geo.lookup('dayton oh'),r)
    def test_zip_and_leading_zero(self):
        self.assertEqual(geo.lookup('45402')[0]['state'],'OH')
        self.assertEqual(geo.lookup('00601')[0]['zip'],'00601')
    def test_unknown_and_typo(self):
        self.assertEqual(geo.lookup('00000'),[])
        self.assertEqual(geo.lookup('4540'),[])
        self.assertEqual(geo.lookup('Cincinatti, OH')[0]['match'],'suggestion')
    def test_no_network(self):
        with patch('socket.socket',side_effect=AssertionError('Network forbidden')):
            geo._index.cache_clear();self.assertTrue(geo.lookup('Dayton, OH'))
    def test_cross_state_zip(self):
        zips=geo._index()[1];code=next(k for k,v in zips.items() if len(v)>1)
        self.assertGreater(len(geo.lookup(code)),1)
        for r in geo.lookup(code):self.assertEqual(len(geo.lookup(r['label'])),1)
    def test_shared_search(self):
        entry={'states':'OH','area':'Dayton'}
        offer={'id':'test','entry':entry,'mod':'MRI','type':'fixed','contrast':'without','amount':400,'region':'Dayton'}
        raw={'mod':'MRI','body':'Knee','location':'45402'}
        with patch.object(core,'catalog',return_value={'version':'synthetic','entries':[entry],'offers':[offer]}):
            result=core.search(raw);self.assertEqual(result['count'],1)
            self.assertIn('state-wide',result['location_notice']);self.assertEqual(result['resolved_location']['state'],'OH')
            for location in ['Dayton','00000','Cincinatti, OH']:
                self.assertEqual(core.search(dict(raw,location=location))['count'],0)
            self.assertEqual(core.search(dict(raw,location='Dayton, OH'))['count'],1)
            self.assertEqual(core.agent('Find knee MRI near 45402 without contrast',{})['count'],1)
            self.assertEqual(core.search(dict(raw,location='Dayton, KY'))['count'],0)

if __name__=='__main__':unittest.main()
