# Third-party components and ownership

This repository contains project-level adapters and documentation, not a copy of the NVIDIA Cosmos Framework source tree or model weights.

- Native video generation API: NVIDIA Cosmos Framework, an external dependency. Follow the original repository and model terms for source, checkpoints and derived artifacts.
- Virtualenv process lifecycle: TAO Skill Bank helpers, an external dependency. The CLI invokes the installed bank's `tao_job_record.py` and `virtualenv_runner.py`; no SDK is installed by this project.
- Runtime libraries include PyTorch, Transformers, Pillow, OmegaConf and imageio-ffmpeg in the verified native environment.
- The fixed local resource guard and GPU inventory helpers remain runtime dependencies; their locations are configured locally, not distributed with private host provenance.

No general redistribution license for institution-owned assets or trained weights is granted here. A project source-code license must be selected after ownership review. The upstream framework and each model retain their own licenses.

## Source history

The previous repository tree included the upstream framework. The rebuild branch keeps that commit as its parent and replaces the working tree with a smaller project layer. It does not erase upstream attribution or change the terms of files retained in earlier commits. No force push or history rewrite is required.
