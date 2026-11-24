from pathlib import Path
import importlib.util
import json
import os
import tempfile
import unittest
from symlink_support import symlink_or_skip

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/create_runtime.py'
spec = importlib.util.spec_from_file_location('create_runtime', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RuntimeProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ['profile/checkpoint/model', 'framework', 'base', 'guard', 'inventory',
                     'tokenizer', 'bank/scripts', 'bank/skills/platform/tao-run-on-virtualenv/references', 'venv/bin']:
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self.python = self.root / 'venv/bin/python'
        symlink_or_skip(self.python, Path(os.sys.executable).resolve())
        self.profile = self.root / 'profile'
        (self.profile / 'RESTORE_RESULT.json').write_text(json.dumps(dict(status='RESTORED_INFERENCE_ONLY', selected_model='FD500')))
        for name in ['model/.metadata', 'COMMITTED']:
            (self.profile / 'checkpoint' / name).write_text('test-only')
        (self.root / 'base/shard').write_text('base')
        (self.profile / 'checkpoint/BASE_REFERENCE.json').write_text(json.dumps(dict(
            frozen_storage_dependencies={str(self.root / 'base/shard'): {'bytes': 4}})))
        (self.root / 'vae').write_text('test-only')
        cfg = dict(lora_enabled=True, lora_rank=16, lora_alpha=32,
                   tokenizer={'vae_path': str(self.root / 'vae')},
                   vlm_config={'tokenizer': {'pretrained_model_name': str(self.root / 'tokenizer')}})
        (self.profile / 'model_config.json').write_text(json.dumps({'model': {'config': cfg}}))
        (self.profile / 'weights_manifest.json').write_text('{}')
        for name in ['guard/telemetry.py', 'guard/monitor_candidate.py', 'inventory/gpu_inventory.py',
                     'bank/scripts/tao_job_record.py', 'bank/scripts/redact_secrets.py',
                     'bank/skills/platform/tao-run-on-virtualenv/references/virtualenv_runner.py']:
            (self.root / name).write_text('# test-only\n')
        self.args = dict(model_profile=self.profile, python=self.python, framework=self.root / 'framework',
                         base_checkpoint=self.root / 'base', ffmpeg=self.python,
                         guard_sources=self.root / 'guard', inventory_sources=self.root / 'inventory',
                         bank=self.root / 'bank', output=self.root / 'new/runtime.json')

    def test_creates_profile_without_resolving_venv_python(self):
        result = module.create_runtime(**self.args)
        self.assertEqual(result['python'], str(self.python))
        self.assertEqual(result['environment']['HF_HUB_OFFLINE'], '1')
        self.assertTrue(self.args['output'].is_file())

    def test_refuses_existing_output(self):
        self.args['output'].parent.mkdir()
        self.args['output'].write_text('preserve')
        with self.assertRaises(FileExistsError):
            module.create_runtime(**self.args)
        self.assertEqual(self.args['output'].read_text(), 'preserve')

    def test_missing_helpers_leave_no_partial_output(self):
        (self.root / 'guard/telemetry.py').unlink()
        with self.assertRaises(ValueError):
            module.create_runtime(**self.args)
        self.assertFalse(self.args['output'].exists())

    def test_wrong_model_rejected(self):
        (self.profile / 'RESTORE_RESULT.json').write_text(json.dumps(dict(status='RESTORED_INFERENCE_ONLY', selected_model='FD300')))
        with self.assertRaises(ValueError):
            module.create_runtime(**self.args)
        self.assertFalse(self.args['output'].exists())

    def test_missing_base_dependency_rejected(self):
        (self.root / 'base/shard').unlink()
        with self.assertRaises(ValueError):
            module.create_runtime(**self.args)
        self.assertFalse(self.args['output'].exists())


if __name__ == '__main__':
    unittest.main()
