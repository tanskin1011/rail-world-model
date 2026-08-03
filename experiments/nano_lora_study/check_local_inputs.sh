#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

DATASET_PATH="${DATASET_PATH:-examples/data/BridgeData2-Subset-Synthetic-Captions/sft_dataset_bridge}"
BASE_CHECKPOINT_PATH="${BASE_CHECKPOINT_PATH:-examples/checkpoints/Cosmos3-Nano}"
WAN_VAE_PATH="${WAN_VAE_PATH:-examples/checkpoints/wan22_vae/Wan2.2_VAE.pth}"

required_paths=(
    "$DATASET_PATH/train/video_dataset_file.jsonl"
    "$BASE_CHECKPOINT_PATH"
    "$WAN_VAE_PATH"
    "examples/toml/sft_config/vision_sft_nano_official_smoke.toml"
    "examples/toml/sft_config/vision_sft_nano_lora_smoke.toml"
)

failed=0
for path in "${required_paths[@]}"; do
    if [[ -e "$path" ]]; then
        printf 'OK      %s\n' "$path"
    else
        printf 'MISSING %s\n' "$path" >&2
        failed=1
    fi
done

printf '\nSystem\n'
printf 'host:    %s\n' "$(hostname)"
printf 'commit:  %s\n' "$(git rev-parse HEAD)"
printf 'branch:  %s\n' "$(git branch --show-current)"
printf 'arch:    %s\n' "$(uname -m)"
printf 'kernel:  %s\n' "$(uname -r)"
printf 'python:  %s\n' "$(python --version 2>&1 || true)"
printf 'torch:   %s\n' "$(python -c 'import torch; print(torch.__version__)' 2>/dev/null || printf unavailable)"
printf 'cuda:    %s\n' "$(python -c 'import torch; print(torch.version.cuda)' 2>/dev/null || printf unavailable)"
printf 'gpu:     %s\n' "$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || printf unavailable)"
printf 'driver:  %s\n' "$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null || printf unavailable)"

exit "$failed"
