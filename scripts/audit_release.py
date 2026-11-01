"""Inspect staged/tracked public candidates; do not follow private symlinks."""
from pathlib import Path
import re,subprocess,sys

root=Path(__file__).resolve().parents[1]
paths=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
issues=[]
for relative in filter(None,paths):
    path=root/relative
    if relative.startswith(('internal/','outputs/','datasets/','checkpoints/')):
        issues.append((relative,'private directory tracked'));continue
    if not path.is_file() or path.is_symlink():
        issues.append((relative,'missing file or symlink'));continue
    media=relative.startswith('assets/results/') and path.suffix.lower() in ['.mp4','.png','.jpg']
    if path.stat().st_size>(16 if media else 2)*1024*1024:
        issues.append((relative,'unexpected large payload'));continue
    if media:
        header=path.read_bytes()[:16]
        if not (header.startswith(b'\x89PNG\r\n\x1a\n') or header.startswith(b'\xff\xd8') or header[4:8]==b'ftyp'):
            issues.append((relative,'unrecognized media signature'))
        continue
    text=path.read_text()
    # Match concrete local identities, not generic /path/to documentation placeholders.
    if re.search(r'/home/[a-zA-Z0-9_-]+/|100\.\d{1,3}\.\d{1,3}\.\d{1,3}',text):
        issues.append((relative,'private absolute path or overlay-network IP'))
for path,reason in issues:print(path+': '+reason)
print(f'Inspected {sum(bool(p) for p in paths)} files; findings={len(issues)}')
raise SystemExit(bool(issues))
