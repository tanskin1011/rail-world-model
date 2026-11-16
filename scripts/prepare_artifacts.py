"""Verify the pinned model download and optionally extract its runtime sources.

Standard library only. No downloads, package installation, model loading or GPU use.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import os
import stat
import zipfile

MODEL_REPO = 'tanskin02/rail-world-model-camera-500step'
REVISION = '379bea5f3a00a51a1aaea402bc774a4e27669f37'
MANIFEST_SHA256 = '1b5947046e647c2b4c268c6ef7bd2ff5d43ddae150632d434af15cc20fb9066e'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def safe_name(value):
    path = PurePosixPath(value)
    if not value or '\\' in value or ':' in value or path.is_absolute() or '..' in path.parts:
        raise ValueError('Unsafe relative path: ' + value)
    return path


def checked_file(root, name):
    relative = safe_name(name)
    path = root.joinpath(*relative.parts)
    if not path.resolve().is_relative_to(root) or not path.is_file():
        raise ValueError('Missing or escaping artifact: ' + name)
    # Do not follow artifact symlinks, including intermediate directories.
    if any(root.joinpath(*relative.parts[:i]).is_symlink() for i in range(1, len(relative.parts) + 1)):
        raise ValueError('Symlink in artifact path: ' + name)
    return path


def verify_artifacts(root, expected_manifest_sha256=MANIFEST_SHA256):
    root = Path(root).resolve()
    manifest_path = checked_file(root, 'deployment_manifest.json')
    if digest(manifest_path) != expected_manifest_sha256:
        raise ValueError('Download the manifest at the documented pinned revision')
    manifest = json.loads(manifest_path.read_text())
    if manifest.get('format') != 'rail-world-model-native-runtime-v1':
        raise ValueError('Unsupported artifact manifest')
    names = set()
    total = 0
    for row in manifest['files']:
        name = row['path_in_repo']
        if name in names:
            raise ValueError('Duplicate artifact: ' + name)
        path = checked_file(root, name)
        if path.stat().st_size != row['bytes'] or digest(path) != row['sha256']:
            raise ValueError('Artifact checksum mismatch: ' + name)
        names.add(name)
        total += row['bytes']
    return dict(status='ARTIFACTS_VERIFIED', files=len(names), bytes=total,
                repo_id=MODEL_REPO, revision=REVISION)


def extract_support(archive, output):
    output = Path(output).expanduser().absolute()
    if os.path.lexists(output):
        raise FileExistsError('Choose a new support directory: ' + str(output))
    with zipfile.ZipFile(archive) as bundle:
        members = bundle.infolist()
        if len(members) > 10000 or sum(item.file_size for item in members) > 256 << 20:
            raise ValueError('Runtime source archive exceeds limits')
        seen = set()
        for item in members:
            name = safe_name(item.filename)
            mode = item.external_attr >> 16
            if stat.S_ISLNK(mode) or (stat.S_IFMT(mode) and not (stat.S_ISREG(mode) or stat.S_ISDIR(mode))):
                raise ValueError('Unsupported archive entry: ' + item.filename)
            if name.parts[0] not in {'runtime_support', 'ENVIRONMENT.json'} or name.as_posix() in seen:
                raise ValueError('Unexpected archive entry: ' + item.filename)
            seen.add(name.as_posix())
        # Reject all unsafe members before creating any output.
        output.mkdir(parents=True)
        for item in members:
            target = output.joinpath(*PurePosixPath(item.filename).parts)
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(item) as source, target.open('xb') as dest:
                for block in iter(lambda: source.read(1 << 20), b''):
                    dest.write(block)
            target.chmod(0o755 if (item.external_attr >> 16) & 0o111 else 0o644)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts', type=Path, required=True)
    parser.add_argument('--support-output', type=Path)
    args = parser.parse_args()
    result = verify_artifacts(args.artifacts)
    if args.support_output:
        result['support_output'] = str(extract_support(
            checked_file(args.artifacts.resolve(), 'runtime_support.zip'), args.support_output))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
