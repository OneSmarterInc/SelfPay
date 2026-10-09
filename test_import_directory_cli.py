import contextlib
import io
import unittest
from unittest.mock import patch, MagicMock
import import_directory


class ImportCommandTests(unittest.TestCase):
    def test_hosted_stage_never_initializes_and_preserves_url(self):
        url = 'postgresql://example.invalid/test'
        with patch('sys.argv', ['import_directory.py', '--db', url, 'stage',
                                'catalog.xlsx', '--mappings', 'reviewed.json']), \
             patch.object(import_directory.core, 'initialize') as init, \
             patch.object(import_directory.core, 'stage_import', return_value={'id': 'test'}) as stage, \
             contextlib.redirect_stdout(io.StringIO()):
            import_directory.main()
        init.assert_not_called()
        self.assertEqual(stage.call_args.args[2], url)

    def test_missing_mapping_rejected_before_database_access(self):
        with patch('sys.argv', ['import_directory.py', 'stage', 'catalog.xlsx']), \
             patch.object(import_directory.core, 'initialize') as init, \
             patch.object(import_directory.core, 'stage_import') as stage, \
             contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            import_directory.main()
        init.assert_not_called()
        stage.assert_not_called()

    def test_hosted_list_never_initializes(self):
        connection = MagicMock()
        connection.__enter__.return_value.execute.return_value = []
        with patch('sys.argv', ['import_directory.py', '--db',
                                'postgresql://example.invalid/test', 'list']), \
             patch.object(import_directory.core, 'initialize') as init, \
             patch.object(import_directory.core, 'connect', return_value=connection), \
             patch.object(import_directory.core, 'active_batch', return_value='prior'), \
             contextlib.redirect_stdout(io.StringIO()):
            import_directory.main()
        init.assert_not_called()
