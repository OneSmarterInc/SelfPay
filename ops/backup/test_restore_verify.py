import unittest
from restore_verify import LIVE_BRANCH, LIVE_HOST, validate_target


class RestoreTargetTests(unittest.TestCase):
    def test_live_branch_rejected(self):
        with self.assertRaises(ValueError):
            validate_target({'host':'ep-test.neon.tech','sslmode':'require'}, LIVE_BRANCH, 'ep-test.neon.tech')

    def test_live_host_rejected(self):
        with self.assertRaises(ValueError):
            validate_target({'host':LIVE_HOST,'sslmode':'require'}, 'br-test', LIVE_HOST)

    def test_verified_disposable_endpoint(self):
        validate_target({'host':'ep-test.neon.tech','sslmode':'verify-full'}, 'br-test', 'ep-test.neon.tech')
