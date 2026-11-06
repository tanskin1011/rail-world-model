# Rail World Model

- Use **Rail World Model** as the project/model name in current documentation, UI labels, guides, and artifact titles.
- `Cosmos3-Nano` is the upstream NVIDIA backbone name, not the project's name.
- A/B and older stage labels are historical experiment identifiers. Keep those identifiers in original logs and evidence; do not present them as the current model name.
- The canonical project is this repository. The desktop `rail-world-model` entry points here.
- Host-specific datasets, checkpoint links, and archived training code live in ignored `local/`; runtime profiles and weight manifests live in ignored `internal/`.
- The selected final checkpoint is FD500 (FD300 plus 200 continuation updates), selected by the user on 2026-11-06. Preserve FD300 and its historical results.
- Use `configs/rail_world_model_protocol.json` and the model config/weight manifest referenced by `internal/runtime.json`. The active manifest is `internal/weights_fd500.json`; `weights_manifest.json` is preserved FD300 evidence.
- Preserve historical checkpoint paths, frozen shard dependencies, and compatibility links. Never bulk-rewrite experiment IDs inside original evidence or checkpoints as a cosmetic rename.
- Renaming or documentation work does not authorize training, inference submission, or publishing internal assets.
