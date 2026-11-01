"""Validate or submit one native Nano FD inference. Never trains or downloads."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
from .contracts import validate_action

PROJECT = Path(__file__).resolve().parents[2]
DEFAULT_PROMPT = ('A low, ground-level forward-facing robot camera view along railway tracks. '
                  'Preserve the input camera viewpoint, visible track layout and surrounding structures.')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_runtime(path):
    runtime = json.loads(path.read_text())
    for key in ['python', 'framework', 'checkpoint', 'model_config', 'expected_weights', 'ffmpeg', 'guard_sources', 'bank']:
        p = Path(runtime[key]).expanduser()
        if not p.exists():
            raise ValueError(f'Missing runtime {key}: {p}')
        # Resolving bin/python's symlink would escape the virtualenv to system Python.
        runtime[key] = str(p.absolute() if key == 'python' else p.resolve())
    ckpt = Path(runtime['checkpoint'])
    for name in ['model/.metadata', 'COMMITTED', 'BASE_REFERENCE.json']:
        if not (ckpt / name).exists():
            raise ValueError(f'Incomplete checkpoint: {name}')
    reference = json.loads((ckpt / 'BASE_REFERENCE.json').read_text())
    for file, expected in reference['frozen_storage_dependencies'].items():
        if not Path(file).is_file() or Path(file).stat().st_size != expected['bytes']:
            raise ValueError(f'Missing or changed frozen checkpoint dependency: {file}')
    cfg = json.loads(Path(runtime['model_config']).read_text())['model']['config']
    if not cfg['lora_enabled'] or cfg['lora_rank'] != 16 or cfg['lora_alpha'] != 32:
        raise ValueError('Final B requires LoRA rank16 / alpha32')
    if not Path(cfg['tokenizer']['vae_path']).is_file():
        raise ValueError('Missing Wan VAE')
    return runtime


def prepare_request(args, runtime):
    image, action = args.image.expanduser().resolve(), args.action.expanduser().resolve()
    # Header validation is supplemented with full Pillow decoding in the native check.
    header = image.read_bytes()[:24]
    if len(header) != 24 or header[:8] != b'\x89PNG\r\n\x1a\n' or struct.unpack('>II', header[16:24]) != (832,480):
        raise ValueError('Input must be an unmodified 832x480 PNG; automatic resizing is disabled')
    validate_action(json.loads(action.read_text()), 188)
    if args.output.exists():
        raise ValueError('Output already exists; choose a fresh directory')
    prompt = args.prompt_file.read_text().strip() if args.prompt_file else DEFAULT_PROMPT
    if not prompt:
        raise ValueError('Prompt cannot be empty')
    row = dict(name='rail_fd',vision_path=str(image), action_path=str(action),
               model_mode='forward_dynamics',domain_name='camera_pose',action_chunk_size=188,
               num_frames=189,fps=24,image_size=480,view_point='ego_view',prompt=prompt,
               seed=args.seed,guidance=1.0,num_steps=30,shift=10.0,
               enable_sound=False,prompt_upsampling=False)
    return dict(runtime=runtime, sample=row, image_sha256=digest(image),action_sha256=digest(action),
                model_config_sha256=digest(runtime['model_config']),expected_weights_sha256=digest(runtime['expected_weights']),
                output=str(args.output.resolve()), training=False, downloads=False)


def worker_environment(runtime):
    env = dict(os.environ)
    env.update(runtime.get('environment', {}))
    env.update(LD_LIBRARY_PATH='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
               PYTHONDONTWRITEBYTECODE='1',TOKENIZERS_PARALLELISM='false',
               CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',
               PYTHONPATH=str(PROJECT/'src')+':'+runtime['framework'])
    env.pop('NANO_RAIL_TRAIN_AUTHORIZED', None)
    return env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime',type=Path,default=PROJECT/'internal/runtime.json')
    parser.add_argument('--image',type=Path)
    parser.add_argument('--action',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--prompt-file',type=Path)
    parser.add_argument('--seed',type=int,default=401)
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--check',action='store_true',help='CPU validation only; no model load or generation')
    modes.add_argument('--run',action='store_true',help='Submit detached GPU inference')
    modes.add_argument('--status',type=Path,metavar='JOB_DIR')
    modes.add_argument('--logs',type=Path,metavar='JOB_DIR')
    modes.add_argument('--cancel',type=Path,metavar='JOB_DIR')
    args=parser.parse_args()
    try:
        configured=json.loads(args.runtime.resolve().read_text())
        bank=Path(configured['bank'])
        runner=bank/'skills/platform/tao-run-on-virtualenv/references/virtualenv_runner.py'
        records=bank/'scripts/tao_job_record.py'
        for verb in ['status','logs','cancel']:
            job=getattr(args,verb)
            if job:
                completed=subprocess.run([sys.executable,str(runner),verb,'--job-dir',str(job)],capture_output=True,text=True)
                print(completed.stdout,end='')
                if completed.stderr:print(completed.stderr,file=sys.stderr,end='')
                if verb=='logs':
                    run_root=job.expanduser().resolve().parents[1]
                    for name in ['phase.json','worker.stdout.log','worker.stderr.log']:
                        path=run_root/name
                        if path.is_file():
                            with path.open('rb') as stream:
                                stream.seek(max(0,path.stat().st_size-8192))
                                tail=stream.read().decode(errors='replace').replace('\r','\n')
                            print(f'\n--- {name} ---\n'+'\n'.join(tail.splitlines()[-12:]))
                if completed.returncode==0 and verb!='logs':
                    response=json.loads(completed.stdout)
                    state=response.get('status')
                    if state in ['COMPLETE','ERROR','CANCELED']:
                        subprocess.run([sys.executable,str(records),'mark',job.name,'--state',state],check=True)
                raise SystemExit(completed.returncode)
        runtime=load_runtime(args.runtime.resolve())
        if any(getattr(args,k) is None for k in ['image','action','output']):
            parser.error('--image, --action and --output are required for --check / --run')
        args.output=args.output.expanduser().resolve()
        spec=prepare_request(args,runtime)
        env=worker_environment(runtime)
        command=[runtime['python'],str(PROJECT/'src/rail_world_model/native_worker.py'),'--check-stdin']
        checked=subprocess.run(command,input=json.dumps(spec),text=True,env=env,cwd=runtime['framework'],capture_output=True)
        if checked.returncode:
            raise ValueError('Native CPU check failed:\n'+checked.stdout+'\n'+checked.stderr)
        spec['cpu_check']=json.loads(checked.stdout.strip().splitlines()[-1])
        print(json.dumps(spec['cpu_check'],indent=2),flush=True)
        if args.check:
            return
        args.output.mkdir(parents=True,exist_ok=False)
        spec_path=args.output/'request.json'
        spec_path.write_text(json.dumps(spec,indent=2))
        lint=subprocess.run([sys.executable,str(bank/'scripts/redact_secrets.py'),'lint',str(spec_path)])
        if lint.returncode:
            raise ValueError('Launch spec secret lint failed')
        job_id=subprocess.check_output([sys.executable,str(records),'open','--platform','virtualenv',
               '--image',runtime['python'],'--network-arch','cosmos3-nano-native-fd','--action','inference',
               '--storage-tier','A','--results-root',str(args.output/'jobs')],text=True).strip()
        job_dir=args.output/'jobs'/job_id
        submitted=subprocess.run([sys.executable,str(runner),'submit','--job-dir',str(job_dir),
                '--venv',str(Path(runtime['python']).parent.parent),'--script',str(PROJECT/'src/rail_world_model/inference_supervisor.py'),
                '--job-id',job_id,'--config-path',str(spec_path),'--arg={config_path}',
                '--cwd',runtime['framework'],'--gpu-ids','0'],capture_output=True,text=True)
        (args.output/'submission.json').write_text(submitted.stdout)
        if submitted.returncode:
            subprocess.run([sys.executable,str(records),'mark',job_id,'--state','ERROR'])
            raise ValueError(submitted.stderr or submitted.stdout)
        receipt=json.loads(submitted.stdout)
        subprocess.run([sys.executable,str(records),'mark',job_id,'--state','RUNNING','--backend-ref',receipt['backend_ref']],check=True)
        print(json.dumps(dict(job_id=job_id,job_dir=str(job_dir),video=str(args.output/'video/vision.mp4'),status='SUBMITTED_NOT_COMPLETE'),indent=2))
    except (ValueError,OSError,KeyError,json.JSONDecodeError) as error:
        parser.exit(1,str(error)+'\n')
