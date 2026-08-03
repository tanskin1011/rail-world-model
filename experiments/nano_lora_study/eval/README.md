# Fixed BridgeData2 evaluation

Use `bridge_fixed_t2v.jsonl` unchanged for the base, 10-step, and 50-step checkpoints.

- Fixed sample names, prompts, resolution, frame count, fps, and seeds.
- `bridge_seen_*` probes BridgeData2-like robot manipulation.
- `bridge_unseen_rail_*` probes whether adaptation transfers to a rail-themed composition not present in the current training data.
- Compare temporal action completion, object identity, scene stability, camera stability, and visual artifacts. Loss alone is not a quality metric.
