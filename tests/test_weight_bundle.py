import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from symlink_support import symlink_or_skip

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('restore_weights',ROOT/'scripts/restore_weights.py')
restore=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(restore)


class WeightBundleTests(unittest.TestCase):
    def test_selected_model_is_fd500_continued_from_fd300(self):
        plan=json.loads((ROOT/'configs/rail_world_model_protocol.json').read_text())
        self.assertEqual(plan['selected_checkpoint'],'FD500')
        self.assertEqual(plan['forward_dynamics']['optimizer_updates'],500)
        self.assertEqual(plan['forward_dynamics']['continuation_updates'],200)

    def test_reject_external_path_and_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'data').write_text('x')
            symlink_or_skip(root/'alias', 'data')
            for name in ['../data',str(root/'data'),'alias']:
                with self.assertRaises(ValueError):restore.local_file(root,name)
            self.assertEqual(restore.local_file(root,'data'),(root/'data').resolve())

    def test_reject_changed_bundle_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'model_delta.distcp').write_bytes(b'one')
            manifest=dict(format='rail-world-model-fd500-dcp-delta-v1',files={'model_delta.distcp':dict(bytes=3,sha256='0'*64)},base_shards={})
            (root/'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,'checksum mismatch'):
                restore.checked_sources(root,root)
