from datetime import date, timedelta
import io
import unittest
from unittest.mock import patch
from git_backup import retention_candidates, verify_destination


class RetentionTests(unittest.TestCase):
    def test_month_boundary_and_newest_fourteen(self):
        branches=['backup-'+(date(2026,9,20)+timedelta(days=i)).isoformat() for i in range(30)]
        removed=set(retention_candidates(branches,'2026-10-19'))
        kept=set(branches)-removed
        self.assertEqual(kept,set(branches[-14:])|{'backup-2026-09-20','backup-2026-10-01'})

    def test_year_boundary_and_missing_first_day(self):
        branches=['backup-2025-12-31']+['backup-2026-01-%02d'%i for i in range(3,25)]
        removed=set(retention_candidates(branches,'2026-01-24'))
        self.assertNotIn('backup-2025-12-31',removed)
        self.assertNotIn('backup-2026-01-03',removed)
        self.assertIn('backup-2026-01-04',removed)

    def test_unrelated_invalid_and_future_refs_untouched(self):
        branches=['main','directory-data','backup-2026-02-30','backup-2026-10-20','backup-not-a-date']
        self.assertEqual(retention_candidates(branches,'2026-10-12'),[])

    @patch.dict('os.environ',{'BACKUP_REPO_TOKEN':'test-only'})
    def test_public_destination_rejected(self):
        with patch('urllib.request.urlopen',return_value=io.StringIO('{"full_name":"OneSmarterInc/MySelfPay_Backup","private":false,"permissions":{"push":true}}')):
            with self.assertRaises(ValueError): verify_destination()
