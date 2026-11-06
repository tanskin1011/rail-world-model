"""Restore an inference-only FD500 DCP from a delta bundle and exact Base shards.

Never downloads, trains or runs inference. Bundle metadata is JSON; PyTorch
metadata is created locally. Use trusted bundles with independently checked SHA256.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import pickle
import shutil


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def local_file(root, relative):
    root = Path(root).resolve()
    path = root / relative
    if Path(relative).is_absolute() or '..' in Path(relative).parts or path.is_symlink():
        raise ValueError('Invalid bundle path: ' + relative)
    path = path.resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('Missing/escaping bundle file: ' + relative)
    return path


def checked_sources(bundle, base):
    manifest = json.loads(local_file(bundle, 'manifest.json').read_text())
    if manifest['format'] != 'rail-world-model-fd500-dcp-delta-v1':
        raise ValueError('Unknown bundle format')
    for name, entry in manifest['files'].items():
        path = local_file(bundle, name)
        if path.stat().st_size != entry['bytes'] or digest(path) != entry['sha256']:
            raise ValueError('Bundle checksum mismatch: ' + name)
    sources = {'delta': local_file(bundle, 'model_delta.distcp')}
    for alias, entry in manifest['base_shards'].items():
        path = local_file(base, entry['file'])
        if path.stat().st_size != entry['bytes'] or digest(path) != entry['sha256']:
            raise ValueError('Exact original Base DCP shard required: ' + entry['file'])
        sources[alias] = path
    recipe = json.loads(local_file(bundle, 'metadata_recipe.json').read_text())
    if set(item['source'] for item in recipe['storage']) != set(sources):
        raise ValueError('Incomplete storage dependency mapping')
    return manifest, recipe, sources


def restore(bundle, base, output, vae, tokenizer, verify_tensors=False):
    import torch
    from torch.distributed.checkpoint.metadata import (
        ChunkStorageMetadata, Metadata, MetadataIndex, TensorProperties, TensorStorageMetadata)
    from torch.distributed.checkpoint.filesystem import _StorageInfo

    if not torch.__version__.startswith('2.10.'):
        raise ValueError('This native DCP recipe was prepared for PyTorch 2.10.x')
    if output.exists() or output.is_symlink():
        raise FileExistsError('Choose a fresh output: ' + str(output))
    if not vae.is_file() or not tokenizer.is_dir():
        raise ValueError('Existing Wan VAE file and tokenizer directory required')
    manifest, recipe, sources = checked_sources(bundle, base)
    state = {}
    for name, item in recipe['tensors'].items():
        dtype = getattr(torch, item['dtype'])
        state[name] = TensorStorageMetadata(
            TensorProperties(dtype=dtype), torch.Size(item['size']),
            [ChunkStorageMetadata(torch.Size(c['offsets']), torch.Size(c['sizes'])) for c in item['chunks']])
    # All validation above completes before a new output is created.
    output.mkdir(parents=True)
    model = output / 'checkpoint/model'
    model.mkdir(parents=True)
    try:
        os.link(sources['delta'], model / 'delta.distcp')
    except OSError:
        shutil.copy2(sources['delta'], model / 'delta.distcp')
    sources['delta'] = model / 'delta.distcp'
    storage = {}
    for item in recipe['storage']:
        index = MetadataIndex(item['fqn'], torch.Size(item['offset']), item['index'])
        storage[index] = _StorageInfo(str(sources[item['source']].resolve()), item['position'], item['length'])
    metadata = Metadata(state_dict_metadata=state,
                        planner_data={k: tuple(v) for k, v in recipe['planner_data'].items()},
                        storage_data=storage)
    (model / '.metadata').write_bytes(pickle.dumps(metadata))
    references = {str(sources[alias].resolve()): {'bytes': item['bytes'], 'sha256': item['sha256']}
                  for alias, item in manifest['base_shards'].items()}
    (output / 'checkpoint/BASE_REFERENCE.json').write_text(json.dumps(
        {'frozen_storage_dependencies': references, 'contract': 'inference-only; Base shards remain external'}, indent=2))
    config = json.loads(local_file(bundle, 'model_config.template.json').read_text())
    config['model']['config']['tokenizer']['vae_path'] = str(vae.resolve())
    config['model']['config']['vlm_config']['tokenizer']['pretrained_model_name'] = str(tokenizer.resolve())
    (output / 'model_config.json').write_text(json.dumps(config, indent=2))
    shutil.copy2(local_file(bundle, 'weights_manifest.json'), output / 'weights_manifest.json')
    verified = verify_all_tensors(recipe, sources, json.loads((output / 'weights_manifest.json').read_text())) if verify_tensors else 0
    (output / 'checkpoint/COMMITTED').write_text('FD500 inference-only restored view\n')
    report = dict(status='RESTORED_INFERENCE_ONLY',selected_model='FD500',tensors=len(state),
                  tensors_value_hash_verified=verified,checkpoint=str(output / 'checkpoint'),
                  original_base_files_unchanged=True,training=False,inference=False,
                  cuda_initialized=torch.cuda.is_initialized(),gpu_model_load_verified=False)
    (output / 'RESTORE_RESULT.json').write_text(json.dumps(report, indent=2))
    return report


def verify_all_tensors(recipe, sources, expected):
    import torch
    if set(recipe['tensors']) != set(expected):
        raise ValueError('Tensor key mismatch')
    seen = set()
    for item in recipe['storage']:
        name = item['fqn']
        shape = recipe['tensors'][name]['size']
        if name in seen or any(item['offset']) or len(recipe['tensors'][name]['chunks']) != 1:
            raise ValueError('This verifier requires one complete stored chunk per tensor')
        with sources[item['source']].open('rb') as stream:
            stream.seek(item['position'])
            raw = stream.read(item['length'])
        tensor = torch.load(io.BytesIO(raw), map_location='cpu', weights_only=True).contiguous()
        if list(tensor.shape) != shape:
            raise ValueError('Stored shape mismatch: ' + name)
        h = hashlib.sha256()
        h.update(str(tensor.dtype).encode())
        h.update(str(tuple(tensor.shape)).encode())
        h.update(memoryview(tensor.reshape(-1).view(torch.uint8).numpy()).cast('B'))
        if h.hexdigest() != expected[name]:
            raise ValueError('Stored tensor hash mismatch: ' + name)
        seen.add(name)
        del tensor, raw
    if seen != set(expected):
        raise ValueError('Missing tensors')
    return len(seen)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('bundle', 'base-model', 'output', 'vae', 'tokenizer'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--verify-tensors', action='store_true')
    args = parser.parse_args()
    print(json.dumps(restore(args.bundle, args.base_model, args.output, args.vae,
                             args.tokenizer, args.verify_tensors), indent=2))


if __name__ == '__main__':
    main()
