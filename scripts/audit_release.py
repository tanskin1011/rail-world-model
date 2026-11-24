"""Audit current public candidates, including untracked files and renames."""
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit
import re
import subprocess

PRIVATE = ('internal', 'local', 'nano', 'outputs', 'datasets', 'checkpoints', '.venv')
WEIGHTS = {'.pt', '.pth', '.safetensors', '.distcp', '.zip', '.tar'}


def candidate_paths(root):
    raw = subprocess.check_output(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=root)
    names = set(filter(None, raw.decode().split('\0')))
    return sorted(n for n in names if (root / n).exists() or (root / n).is_symlink())


def audit(root, names):
    root = Path(root).resolve()
    names = set(names)
    issues = []
    for relative in sorted(names):
        path = root / relative
        parts = PurePosixPath(relative).parts
        if '..' in parts or PurePosixPath(relative).is_absolute():
            issues.append((relative, 'path escapes export')); continue
        if any(p in PRIVATE for p in parts) or path.name.startswith('.env') or path.suffix in WEIGHTS:
            issues.append((relative, 'private asset included')); continue
        if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != root and root in p.parents):
            issues.append((relative, 'symlink not publishable')); continue
        if not path.is_file():
            issues.append((relative, 'missing file')); continue
        media = relative.startswith('assets/results/') and path.suffix.lower() in {'.mp4', '.png', '.jpg', '.gif'}
        if path.stat().st_size > (16 if media else 2) * 1024 * 1024:
            issues.append((relative, 'unexpected large payload')); continue
        if media:
            with path.open('rb') as stream:
                header = stream.read(16)
            if not (header.startswith(b'\x89PNG\r\n\x1a\n') or header.startswith(b'\xff\xd8') or header.startswith((b'GIF87a', b'GIF89a')) or header[4:8] == b'ftyp'):
                issues.append((relative, 'unrecognized media signature'))
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            issues.append((relative, 'unexpected binary file')); continue
        if re.search(r'/home/[a-zA-Z0-9_-]+/|100\.\d{1,3}\.\d{1,3}\.\d{1,3}', text):
            issues.append((relative, 'private absolute path or overlay-network IP'))
        if path.suffix == '.md':
            for target in re.findall(r'\]\(([^)]+)\)', text):
                url = urlsplit(target.strip('<>'))
                if url.scheme or url.netloc or not url.path:
                    continue
                linked = (path.parent / unquote(url.path)).resolve()
                try:
                    exported = linked.relative_to(root).as_posix()
                except ValueError:
                    issues.append((relative, 'document link outside repository: ' + target)); continue
                if not any(n == exported or n.startswith(exported.rstrip('/') + '/') for n in names):
                    issues.append((relative, 'document link absent from export: ' + target))
    return issues


def main():
    root = Path(__file__).resolve().parents[1]
    names = candidate_paths(root)
    issues = audit(root, names)
    for path, reason in issues:
        print(path + ': ' + reason)
    print(f'Inspected {len(names)} current candidate files; findings={len(issues)}')
    raise SystemExit(bool(issues))


if __name__ == '__main__':
    main()
