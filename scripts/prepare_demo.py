"""Prepare a public synthetic image, camera plan and prompt without loading a model."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from rail_world_model.actions import PROFILES, straight_action
from rail_world_model.contracts import validate_action

SOURCE = ROOT / 'assets/results/train_field.png'
PROMPT = ('A forward-facing camera view along railway tracks. '
          'Preserve the input camera viewpoint, visible track layout and surrounding structures.\n')


def prepare_demo(output, profile):
    output = Path(output).expanduser().absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError('Choose a new demo directory: ' + str(output))
    image = SOURCE.read_bytes()
    if image[:8] != b'\x89PNG\r\n\x1a\n' or len(image) < 24 or struct.unpack('>II', image[16:24]) != (832, 480):
        raise ValueError('Public demo source must be a PNG of size 832x480')
    action = straight_action(profile)
    validate_action(action)
    action_bytes = (json.dumps(action, indent=2) + '\n').encode('utf-8')
    prompt_bytes = PROMPT.encode('utf-8')
    manifest = {
        'status': 'DEMO_INPUTS_READY',
        'profile': profile,
        'image_source': SOURCE.relative_to(ROOT).as_posix(),
        'image_training_exposure': 'seen_synthetic_training_frame',
        'action_source': 'mathematical_straight_camera_plan_not_pose_GT',
        'coordinate_convention': 'OpenCV camera-relative +Z forward; identity rotation',
        'translation_unit': 'metres_per_transition',
        'image_size': [832, 480],
        'video_frames': 189,
        'fps': 24,
        'action_shape': [188, 9],
        'planned_path_length_m': sum(row[2] for row in action),
        'files_sha256': {name: hashlib.sha256(data).hexdigest() for name, data in (
            ('input.png', image), ('action.json', action_bytes), ('scene.txt', prompt_bytes))},
        'scope': 'Input smoke test; not a reconstruction of the published FD500 showcase or an unseen-scene evaluation',
        'model_loaded': False,
        'inference_run': False,
    }
    output.mkdir(parents=True, exist_ok=False)
    for name, data in (('input.png', image), ('action.json', action_bytes), ('scene.txt', prompt_bytes)):
        (output / name).write_bytes(data)
    (output / 'demo_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=PROFILES, default='decel')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = prepare_demo(args.output, args.profile)
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + '\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
