import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from rail_world_model.contracts import validate_action

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('prepare_demo', ROOT / 'scripts/prepare_demo.py')
demo = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(demo)


class PublicDemoTests(unittest.TestCase):
    def test_inputs_and_manifest_are_usable_by_inference(self):
        from argparse import Namespace
        from rail_world_model.infer_cli import prepare_request

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'demo'
            result = demo.prepare_demo(output, 'decel')
            action = json.loads((output / 'action.json').read_text(encoding='utf-8'))
            self.assertTrue(validate_action(action)['rotation_columns_valid'])
            self.assertGreater(action[0][2], action[-1][2])
            self.assertEqual(result['image_training_exposure'], 'seen_synthetic_training_frame')
            self.assertFalse(result['inference_run'])
            for name, digest in result['files_sha256'].items():
                self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), digest)
            config = root / 'config.json'
            config.write_text('{}', encoding='utf-8')
            args = Namespace(image=output / 'input.png', action=output / 'action.json',
                             prompt_file=output / 'scene.txt', output=root / 'generated', seed=401)
            request = prepare_request(args, {'model_config': str(config), 'expected_weights': str(config)})
            self.assertEqual(request['sample']['num_frames'], 189)
            self.assertFalse(args.output.exists())

    def test_existing_directory_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'keep.txt').write_text('keep', encoding='utf-8')
            with self.assertRaises(FileExistsError):
                demo.prepare_demo(root, 'stop')
            self.assertEqual(list(root.iterdir()), [root / 'keep.txt'])

    def test_invalid_profile_leaves_no_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'demo'
            with self.assertRaises(ValueError):
                demo.prepare_demo(output, 'unknown')
            self.assertFalse(output.exists())
