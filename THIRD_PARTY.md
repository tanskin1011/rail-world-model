# Third-party components and ownership

This repository contains project-level adapters and documentation, not a copy of the NVIDIA Cosmos Framework source tree or model weights.

- Native video generation API: NVIDIA Cosmos Framework, an external dependency. Follow the original repository and model terms for source, checkpoints and derived artifacts.
- Virtualenv process lifecycle: TAO Skill Bank helpers, an external dependency. The CLI invokes the installed bank's `tao_job_record.py` and `virtualenv_runner.py`; no SDK is installed by this project.
- Runtime libraries include PyTorch, Transformers, Pillow, OmegaConf and imageio-ffmpeg in the verified native environment.
- The fixed local resource guard and GPU inventory helpers remain runtime dependencies; their locations are configured locally, not distributed with private host provenance.

No general redistribution license for institution-owned assets or trained weights is granted here. A project source-code license must be selected after ownership review. The upstream framework and each model retain their own licenses.

## Representative media

The selected representative comparisons and synthetic training frames in `assets/results/` are included at the user's explicit publication request. A/B clips are generated outputs conditioned on a curated frame originating from NRK Nordlandsbanen's autumn synchronized video; they are not recordings of the real future. Full upstream real video is not included. Simulator references and synthetic training frames are existing project assets. See `docs/MEDIA_GALLERY.md` and the media manifest for provenance and limits. No blanket license for source datasets, institutional maps or model checkpoints is implied.

### FD500 showcase additions

Two existing FD500 deceleration outputs are included as full-length MP4s and lower-resolution GIF previews. The photographic-input result uses the project's existing `real_b03` image; its SHA-256 and generated output hashes are recorded in `assets/results/portfolio_manifest.json` and internal provenance records. The original real-world video is not included, and its source/licensing history must be checked before broad public redistribution. The synthetic scene is a seen training image, not an unseen-scene generalization result. Neither preview is a recording of an actual future event.

## Source history details

The previous repository tree included the upstream framework. The rebuild branch keeps that commit as its parent and replaces the working tree with a smaller project layer. It does not erase upstream attribution or change the terms of files retained in earlier commits. No force push or history rewrite is required.
