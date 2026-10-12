import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from git_backup import backup_date, create_commit, git

class BackupTests(unittest.TestCase):
    def test_india_date(self):
        self.assertEqual(backup_date(datetime(2026,10,12,19,tzinfo=timezone.utc)), '2026-10-13')
    def test_dump_only_parentless_commit(self):
        with tempfile.TemporaryDirectory() as root:
            source=Path(root)/'ciphertext'; source.write_bytes(b'age-encryption.org/v1\n' + b'fake encrypted fixture')
            repo=Path(root)/'repo'; repo.mkdir()
            create_commit(repo,source,'2026-10-12')
            self.assertEqual(git(['ls-tree','-r','--name-only','HEAD'],repo).stdout.strip(),'database-2026-10-12.dump.age')
            self.assertEqual(git(['rev-list','--count','HEAD'],repo).stdout.strip(),'1')
    def test_plaintext_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            source=Path(root)/'plain'; source.write_bytes(b'PGDMP plaintext')
            with self.assertRaises(ValueError): create_commit(root,source,'2026-10-12')

if __name__ == '__main__': unittest.main()
