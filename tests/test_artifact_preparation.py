from pathlib import Path
import hashlib
import importlib.util
import json
import stat
import tempfile
import unittest
import zipfile
from symlink_support import symlink_or_skip

spec = importlib.util.spec_from_file_location('prepare_artifacts', Path(__file__).resolve().parents[1] / 'scripts/prepare_artifacts.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ArtifactPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'weights').write_bytes(b'test-only')
        self.manifest = {'format': 'rail-world-model-native-runtime-v1', 'files': [
            {'path_in_repo': 'weights', 'bytes': 9, 'sha256': hashlib.sha256(b'test-only').hexdigest()}]}

    def write_manifest(self):
        path = self.root / 'deployment_manifest.json'
        path.write_text(json.dumps(self.manifest))
        return module.digest(path)

    def test_valid_inventory(self):
        result = module.verify_artifacts(self.root, self.write_manifest())
        self.assertEqual(result['files'], 1)
        self.assertEqual(result['bytes'], 9)

    def test_wrong_manifest_rejected(self):
        self.write_manifest()
        with self.assertRaises(ValueError):
            module.verify_artifacts(self.root)

    def test_modified_artifact_rejected(self):
        checksum = self.write_manifest()
        (self.root / 'weights').write_bytes(b'bad-value')
        with self.assertRaises(ValueError):
            module.verify_artifacts(self.root, checksum)

    def test_parent_path_rejected(self):
        self.manifest['files'][0]['path_in_repo'] = '../weights'
        with self.assertRaises(ValueError):
            module.verify_artifacts(self.root, self.write_manifest())

    def test_symlink_rejected(self):
        symlink_or_skip(self.root / 'alias', 'weights')
        self.manifest['files'][0]['path_in_repo'] = 'alias'
        with self.assertRaises(ValueError):
            module.verify_artifacts(self.root, self.write_manifest())

    def test_support_extract_and_no_overwrite(self):
        archive = self.root / 'support.zip'
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr('runtime_support/native_framework/example.py', '# test-only')
            z.writestr('ENVIRONMENT.json', '{}')
        output = self.root / 'unpacked'
        module.extract_support(archive, output)
        self.assertEqual((output / 'ENVIRONMENT.json').read_text(), '{}')
        with self.assertRaises(FileExistsError):
            module.extract_support(archive, output)

    def test_unsafe_archives_leave_no_output(self):
        for name in ('../escape', '/escape', 'runtime_support/../../escape', 'unexpected.txt'):
            archive = self.root / 'bad.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr(name, 'test-only')
            with self.assertRaises(ValueError):
                module.extract_support(archive, self.root / 'no_output')
            self.assertFalse((self.root / 'no_output').exists())

    def test_raw_backslash_path_rejected(self):
        # zipfile normalizes separators on Windows before returning member names.
        with self.assertRaises(ValueError):
            module.safe_name('runtime_support\\escape')

    def test_archive_symlink_rejected(self):
        archive = self.root / 'bad.zip'
        with zipfile.ZipFile(archive, 'w') as z:
            item = zipfile.ZipInfo('runtime_support/link')
            item.external_attr = (stat.S_IFLNK | 0o777) << 16
            z.writestr(item, '../escape')
        with self.assertRaises(ValueError):
            module.extract_support(archive, self.root / 'no_output')
        self.assertFalse((self.root / 'no_output').exists())


if __name__ == '__main__':
    unittest.main()
