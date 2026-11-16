"""Create a new local runtime from a restored model profile; no GPU or downloads."""
from pathlib import Path
import argparse
import json
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from rail_world_model.infer_cli import load_runtime


def create_runtime(model_profile, python, framework, base_checkpoint, ffmpeg,
                   guard_sources, inventory_sources, bank, output):
    output = Path(output).expanduser().absolute()
    if os.path.lexists(output):
        raise FileExistsError('Choose a new runtime file: ' + str(output))
    profile = Path(model_profile).expanduser().resolve()
    restored = json.loads((profile / 'RESTORE_RESULT.json').read_text())
    if restored.get('status') != 'RESTORED_INFERENCE_ONLY' or restored.get('selected_model') != 'FD500':
        raise ValueError('Expected a restored Rail World Model 500step profile')
    paths = {key: Path(value).expanduser().absolute() for key, value in dict(
        python=python, framework=framework, base_checkpoint=base_checkpoint, ffmpeg=ffmpeg,
        guard_sources=guard_sources, inventory_sources=inventory_sources, bank=bank).items()}
    for key, path in paths.items():
        if not path.exists():
            raise ValueError('Missing ' + key + ': ' + str(path))
    for key in ['python', 'ffmpeg']:
        if not paths[key].is_file() or not os.access(paths[key], os.X_OK):
            raise ValueError('Expected an executable for ' + key)
    for key in ['framework', 'base_checkpoint', 'guard_sources', 'inventory_sources', 'bank']:
        if not paths[key].is_dir():
            raise ValueError('Expected a directory for ' + key)
    required = {
        'guard_sources': ['telemetry.py', 'monitor_candidate.py'],
        'inventory_sources': ['gpu_inventory.py'],
        'bank': ['scripts/tao_job_record.py', 'scripts/redact_secrets.py',
                 'skills/platform/tao-run-on-virtualenv/references/virtualenv_runner.py'],
    }
    for key, names in required.items():
        for name in names:
            if not (paths[key] / name).is_file():
                raise ValueError('Missing runtime helper: ' + str(paths[key] / name))
    config = json.loads((profile / 'model_config.json').read_text())['model']['config']
    tokenizer = Path(config['vlm_config']['tokenizer']['pretrained_model_name'])
    if not tokenizer.is_dir():
        raise ValueError('Missing tokenizer directory: ' + str(tokenizer))
    data = {key: str(paths[key]) for key in ['python', 'framework', 'ffmpeg', 'guard_sources', 'inventory_sources', 'bank']}
    data.update(checkpoint=str(profile / 'checkpoint'), model_config=str(profile / 'model_config.json'),
                expected_weights=str(profile / 'weights_manifest.json'))
    cache = output.parent / 'offline_cache'
    data['environment'] = dict(
        BASE_CHECKPOINT_PATH=str(paths['base_checkpoint']), WAN_VAE_PATH=config['tokenizer']['vae_path'],
        IMAGEIO_FFMPEG_EXE=str(paths['ffmpeg']), HF_HOME=str(cache), HF_HUB_CACHE=str(cache / 'hub'),
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_DATASETS_OFFLINE='1',
        WANDB_MODE='disabled', AWS_EC2_METADATA_DISABLED='true')
    # Validate through the same reader used by infer.py, without writing a partial profile.
    class PendingConfig:
        def read_text(self):
            return json.dumps(data)
    load_runtime(PendingConfig())
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as stream:
        json.dump(data, stream, indent=2)
        stream.write('\n')
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['model-profile', 'python', 'framework', 'base-checkpoint', 'ffmpeg',
                 'guard-sources', 'inventory-sources', 'bank', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    create_runtime(**vars(args))
    print(json.dumps(dict(status='RUNTIME_CREATED', runtime=str(args.output.absolute()),
                          gpu_initialized=False, model_loaded=False)))


if __name__ == '__main__':
    main()
