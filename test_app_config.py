import json
import tempfile
import unittest
from pathlib import Path
from tools.generate_app_config import website_url, generate

class AppConfigTests(unittest.TestCase):
    def test_address_change_reaches_both_apps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'app-config.json').write_text(json.dumps({'website_url':'https://example.com'}))
            resources=root/'android/app/src/main/res/drawable'
            resources.mkdir(parents=True)
            icon=Path(__file__).parent/'android/launcher-icon.png.base64'
            (root/'android/launcher-icon.png.base64').write_text(icon.read_text())
            for platform in ['ios','android']:generate(platform,root)
            for p in [root/'ios/MySelfPay/AppConfig.swift',root/'android/app/src/main/java/com/onesmarter/myselfpay/AppConfig.java']:
                self.assertIn('https://example.com/',p.read_text())
    def test_reject_unsafe_addresses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for value in ['http://example.com','https://user@example.com','https://example.com:444','https://example.com/path','https://example.com/?token=x','https://example.com/\n']:
                with self.subTest(value=value):
                    (root/'app-config.json').write_text(json.dumps({'website_url':value}))
                    with self.assertRaises(ValueError):website_url(root)
