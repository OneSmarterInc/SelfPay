import unittest
from unittest.mock import patch
import core
import geo


class RegionSearchTests(unittest.TestCase):
    def setUp(self):
        mi = dict(name='Michigan', state='MI', kind='state', label='Michigan', latitude=44, longitude=-85)
        il = dict(name='Illinois', state='IL', kind='state', label='Illinois', latitude=40, longitude=-89)
        chicago = dict(name='Chicago', state='IL', kind='place', label='Chicago, IL', latitude=41.88, longitude=-87.63)
        self.index = patch.object(geo, '_index', return_value=({'chicago': [chicago]}, {}, {'michigan': mi, 'mi': mi, 'illinois': il, 'il': il}))
        self.index.start()
        self.addCleanup(self.index.stop)

    def test_state_prefix_offers_confirmation(self):
        self.assertEqual(geo.lookup('mich')[0]['label'], 'Michigan')
        self.assertEqual(geo.lookup('mich')[0]['match'], 'suggestion')
        self.assertEqual(geo.lookup('Michigan')[0]['match'], 'exact')
        self.assertEqual(geo.lookup('IL')[0]['label'], 'Illinois')

    def test_suburbs_use_known_center_with_notice(self):
        for text in ['Chicago suburbs, IL', 'Chicago metro area IL', 'Chicago area, Illinois']:
            result = geo.lookup(text)
            self.assertEqual(result[0]['label'], 'Chicago, IL')
            self.assertEqual(result[0]['match'], 'exact')
            self.assertIn('city center', result[0]['notice'])
        self.assertEqual(geo.lookup('Chicago suburbs, MI'), [])
        self.assertEqual(geo.lookup('00000'), [])

    def test_catalog_replaces_area_label_and_includes_states(self):
        choices = dict(core.location_choices([{'states': 'IL', 'area': 'Chicago suburbs', 'locations': []}]))
        self.assertIn('Chicago, IL', choices)
        self.assertNotIn('Chicago suburbs, IL', choices)
        self.assertIn('Michigan', choices)
        self.assertIn('Illinois', choices)

    def test_search_resolves_region_and_keeps_notice(self):
        with patch.object(core, 'catalog', return_value={'version': 'test', 'entries': [], 'offers': []}):
            result = core.search(dict(mod='MRI', body='Knee', location='Chicago suburbs, IL'))
            self.assertEqual(result['resolved_location']['label'], 'Chicago, IL')
            self.assertIn('city center', result['location_notice'])
            result = core.search(dict(mod='MRI', body='Knee', location='mich'))
            self.assertEqual(result['location_suggestions'], ['Michigan'])


if __name__ == '__main__':
    unittest.main()
