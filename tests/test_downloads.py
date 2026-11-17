import importlib.util
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        spec = importlib.util.spec_from_file_location('get_fastas', ROOT / 'get_fastas.py')
        self.module = importlib.util.module_from_spec(spec)
        with patch.object(sys, 'argv', ['get_fastas.py', 'config.csv', str(self.root)]):
            spec.loader.exec_module(self.module)
        self.module.progress = Mock()
        self.module.total_entries = Mock(return_value=None)
        self.module.time = Mock()

    def error(self, code, headers=None):
        return urllib.error.HTTPError('https://example.org', code, 'failure', headers or {}, None)

    def test_rate_limit_retries_and_honors_retry_after(self):
        def fetch(*args):
            if self.module.fetch.call_count == 1:
                raise self.error(429, {'Retry-After': '12'})
            (self.root / 'test_{cnt}.fasta').write_text('>A\nAAA\n')
            return 1

        self.module.fetch = Mock(side_effect=fetch)
        result = self.module.download_or_pass(('test', 'https://example.org', 'test_{cnt}.fasta', '20261113'))
        self.assertEqual(result, ('test', 'test_1.fasta', 1))
        self.assertEqual((self.root / 'test_1.fasta').read_text(), '>A\nAAA\n')
        self.module.time.sleep.assert_called_once_with(12)

    def test_retry_limit_cleans_partial_file(self):
        partial = self.root / 'test.fasta'
        partial.write_text('partial')
        self.module.fetch = Mock(side_effect=self.error(503))
        self.assertIsNone(self.module.download_or_pass(('test', 'https://example.org', partial.name, '20261113')))
        self.assertEqual(self.module.fetch.call_count, 4)
        self.assertEqual(self.module.time.sleep.call_count, 3)
        self.assertFalse(partial.exists())

    def test_missing_url_is_not_retried(self):
        self.module.fetch = Mock(side_effect=self.error(404))
        self.assertIsNone(self.module.download_or_pass(('test', 'https://example.org', 'test.fasta', '20261113')))
        self.module.fetch.assert_called_once()
        self.module.time.sleep.assert_not_called()

    def test_failed_download_exits_nonzero(self):
        config = self.root / 'config.csv'
        config.write_text(f'TAG,URL,NAME\nmissing,{(self.root / "missing.fasta").as_uri()},missing.fasta\n')
        result = subprocess.run([sys.executable, str(ROOT / 'get_fastas.py'), str(config), str(self.root)],
                                text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 1)
        self.assertIn('Download failed for: missing', result.stderr)
        self.assertIn('FASTA build incomplete', result.stderr)


if __name__ == '__main__':
    unittest.main()
