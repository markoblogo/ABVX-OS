import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from abvx_harness.maintenance import category, inspect


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)

    def write(self, name, text='synthetic'):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def test_categories_require_review_and_retain_operational_data(self):
        expected = {'src/new.py':'CODE_REVIEW', 'books/draft.md':'WORKING_DATA_RETAIN',
                    'artifacts/out.json':'WORKING_DATA_RETAIN', 'docs/credential-broker.md':'PRIVATE_REVIEW',
                    '.codex/session.json':'PRIVATE_REVIEW', 'run.log':'DERIVED_REVIEW',
                    'unknown.bin':'UNCLASSIFIED_RETAIN'}
        for path, group in expected.items():
            self.assertEqual(category(path), group)

    def test_inspection_is_read_only_and_never_reads_dirty_file_contents(self):
        secret = self.write('docs/credential-note.txt', 'synthetic-private-canary')
        book = self.write('books/my draft.md')
        code = self.write('src/new.py')
        before = {p:p.read_bytes() for p in (secret, book, code)}
        original = Path.read_text
        def guarded(path, *args, **kwargs):
            if path in before:
                self.fail('Dirty file content was read')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', guarded):
            report = inspect(self.root)
        self.assertEqual(report['changes'], 3)
        self.assertEqual(report['groups']['PRIVATE_REVIEW']['files'], 1)
        self.assertFalse(report['writes_performed'])
        self.assertFalse(report['deletion_authorized'])
        self.assertEqual(report['portfolio_queue']['status'], 'UNKNOWN')
        self.assertEqual(before, {p:p.read_bytes() for p in before})

    def test_symlink_contents_are_not_followed(self):
        target = self.write('private.txt')
        (self.root / 'linked.txt').symlink_to(target)
        report = inspect(self.root)
        link = next(f for f in report['files'] if f['path'] == 'linked.txt')
        self.assertIsNone(link['bytes'])
        self.assertEqual(link['category'], 'UNCLASSIFIED_RETAIN')

    def test_staged_rename_and_spaces_are_counted_once(self):
        self.write('original.md')
        subprocess.run(['git', '-C', str(self.root), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Synthetic',
                        '-c', 'user.email=synthetic@example.invalid', 'commit', '-qm', 'fixture'], check=True)
        subprocess.run(['git', '-C', str(self.root), 'mv', 'original.md', 'renamed file.md'], check=True)
        report = inspect(self.root)
        self.assertEqual(report['changes'], 1)
        self.assertEqual(report['files'][0]['path'], 'renamed file.md')

    def test_reuses_existing_portfolio_projection(self):
        for name in ('state', 'strategy', 'human-queue'):
            self.write(f'portfolio/{name}.json', json.dumps({'entries':[]}))
        report = inspect(self.root)
        self.assertEqual(report['portfolio_queue'], {'status':'AVAILABLE', 'actionable_projects':0,
                          'waiting_projects':0, 'waiting_human_items':0})
        self.assertEqual(report['history']['status'], 'UNKNOWN')
