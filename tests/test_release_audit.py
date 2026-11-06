import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('audit_release', Path(__file__).resolve().parents[1] / 'scripts/audit_release.py')
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


class ReleaseAuditTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('git'), 'Git required for candidate discovery')
    def test_untracked_rename_and_ignored_files(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            (root / '.gitignore').write_text('local/\n')
            (root / 'old.json').write_text('{}')
            subprocess.run(['git', 'add', '.gitignore', 'old.json'], cwd=root, check=True)
            (root / 'old.json').rename(root / 'new.json')
            (root / 'local').mkdir()
            (root / 'local/private.txt').write_text('not exported')
            self.assertEqual(release.candidate_paths(root), ['.gitignore', 'new.json'])

    def test_repository_external_and_ignored_links_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'README.md').write_text('[outside](../outside.md) [private](internal/existing.md)')
            (root / 'internal').mkdir()
            (root / 'internal/existing.md').write_text('exists locally, absent from export')
            reasons = [r for _, r in release.audit(root, ['README.md'])]
            self.assertEqual(len(reasons), 2)

    def test_public_relative_links_allowed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'README.md').write_text('[guide](docs/guide.md#usage) [web](https://example.org)')
            (root / 'docs').mkdir()
            (root / 'docs/guide.md').write_text('# Usage')
            self.assertEqual(release.audit(root, ['README.md', 'docs/guide.md']), [])

    def test_private_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'local').mkdir()
            (root / 'local/value.txt').write_text('private')
            (root / 'alias').symlink_to('local/value.txt')
            self.assertEqual(len(release.audit(root, ['local/value.txt', 'alias'])), 2)

    def test_paths_and_oversized_payload_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'path.md').write_text('/' + 'home/' + 'example_user/file')
            with (root / 'large.txt').open('wb') as stream:
                stream.truncate(2 * 1024 * 1024 + 1)
            self.assertEqual(len(release.audit(root, ['path.md', 'large.txt'])), 2)

    def test_unknown_binary_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'binary.bin').write_bytes(b'\xff\x00')
            self.assertEqual(len(release.audit(root, ['binary.bin'])), 1)

    def test_gif_preview_recognized(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            folder = root / 'assets/results'; folder.mkdir(parents=True)
            (folder / 'preview.gif').write_bytes(b'GIF89a' + b'\x00' * 10)
            self.assertEqual(release.audit(root, ['assets/results/preview.gif']), [])
