import argparse,json,struct,tempfile,unittest
from unittest.mock import patch
from types import SimpleNamespace
from pathlib import Path
from rail_world_model.infer_cli import prepare_request,load_runtime


class InferenceCliTests(unittest.TestCase):
    def test_logs_are_plain_text_not_json(self):
        from rail_world_model.infer_cli import main
        with tempfile.TemporaryDirectory() as directory:
            profile=Path(directory)/'runtime.json';profile.write_text(json.dumps({'bank':directory}))
            with patch('sys.argv',['infer.py','--runtime',str(profile),'--logs','jobs/example']),patch('subprocess.run',return_value=SimpleNamespace(returncode=0,stdout='plain log\n',stderr='')):
                with self.assertRaises(SystemExit) as result:main()
                self.assertEqual(result.exception.code,0)

    def test_valid_request_fixed_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)
            image=p/'input.png';image.write_bytes(b'\x89PNG\r\n\x1a\n'+b'\0'*8+struct.pack('>II',832,480))
            action=p/'action.json';action.write_text(json.dumps([[0,0,0,1,0,0,0,1,0]]*188))
            config=p/'config.json';config.write_text('{}')
            args=argparse.Namespace(image=image,action=action,output=p/'new',prompt_file=None,seed=401)
            spec=prepare_request(args,{'model_config':str(config),'expected_weights':str(config)})
            self.assertEqual(spec['sample']['model_mode'],'forward_dynamics')
            self.assertEqual(spec['sample']['num_frames'],189)
            self.assertFalse(spec['training'])
            self.assertFalse(args.output.exists())
            args.output.mkdir()
            with self.assertRaises(ValueError):prepare_request(args,{'model_config':str(config),'expected_weights':str(config)})

    def test_wrong_image_size(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'input.png';p.write_bytes(b'\x89PNG\r\n\x1a\n'+b'\0'*8+struct.pack('>II',640,480))
            args=argparse.Namespace(image=p,action=p,output=p.parent/'new',prompt_file=None,seed=401)
            with self.assertRaises(ValueError):prepare_request(args,{})

    def test_virtualenv_python_symlink_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory);python=p/'python';python.symlink_to('/usr/bin/python3')
            config=p/'config.json';config.write_text(json.dumps({'model':{'config':{'lora_enabled':True,'lora_rank':16,'lora_alpha':32,'tokenizer':{'vae_path':str(config)}}}}))
            (p/'model').mkdir();(p/'model/.metadata').touch();(p/'COMMITTED').touch()
            (p/'BASE_REFERENCE.json').write_text(json.dumps({'frozen_storage_dependencies':{}}))
            runtime={key:str(p) for key in ['framework','checkpoint','guard_sources','bank']}
            runtime.update(python=str(python),model_config=str(config),expected_weights=str(config),ffmpeg=str(config))
            path=p/'runtime.json';path.write_text(json.dumps(runtime))
            self.assertEqual(load_runtime(path)['python'],str(python))
