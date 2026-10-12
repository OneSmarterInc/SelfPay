import unittest
from restore_download import validate_source


class RestoreSourceTests(unittest.TestCase):
    def test_exact_immutable_source(self):
        validate_source('2026-10-12', '892343ff15544204a5fab6fecb7369f255af35f9')

    def test_ref_and_date_injection_rejected(self):
        for day, commit in [('2026-10-12', 'main'), ('2026-10-12', 'a'*40+'\n'),
                            ('2026-02-30', 'a'*40), ('--upload-pack=x', 'a'*40)]:
            with self.subTest(day=day, commit=commit), self.assertRaises(ValueError):
                validate_source(day, commit)
