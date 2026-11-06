import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('configure_inference',PROJECT/'scripts/configure_inference.py')
configure=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(configure)


class ProjectLayoutTests(unittest.TestCase):
    def test_project_protocol_name(self):
        protocol=json.loads((PROJECT/'configs/rail_world_model_protocol.json').read_text())
        self.assertEqual(protocol['project'],'Rail World Model')
        self.assertEqual(protocol['model'],'Cosmos3-Nano')

    def test_native_legacy_artifacts_keep_exact_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'source';source.mkdir();output=root/'output'
            (source/'MODEL_CONFIG.json').write_bytes(b'{"model":{}}\n')
            (source/'EXPECTED_B1097_TYPED.json').write_bytes(b'{"weight":"hash"}\n')
            configure.copy_reference_configs(source,output)
            self.assertEqual((output/'model_config.json').read_bytes(),b'{"model":{}}\n')
            self.assertEqual((output/'weights_manifest.json').read_bytes(),b'{"weight":"hash"}\n')

    def test_current_artifact_names_supported(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'source';source.mkdir();output=root/'output'
            for name in ['model_config.json','weights_manifest.json']:
                (source/name).write_text('{}')
            configure.copy_reference_configs(source,output)
            self.assertEqual(sorted(p.name for p in output.iterdir()),['model_config.json','weights_manifest.json'])

    def test_existing_file_not_overwritten_or_partially_imported(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'source';source.mkdir();output=root/'output';output.mkdir()
            for name in ['model_config.json','weights_manifest.json']:
                (source/name).write_text('{}')
            (output/'weights_manifest.json').write_text('original')
            with self.assertRaises(FileExistsError):
                configure.copy_reference_configs(source,output)
            self.assertEqual((output/'weights_manifest.json').read_text(),'original')
            self.assertFalse((output/'model_config.json').exists())
