"""Minimal two-node NCCL collective test for the DGX Spark pair."""

import socket

import torch
import torch.distributed as dist


def main() -> None:
    dist.init_process_group(backend="nccl")
    rank = dist.get_rank()
    world_size = dist.get_world_size()

    value = torch.tensor(float(rank + 1), device="cuda")
    dist.all_reduce(value, op=dist.ReduceOp.SUM)
    torch.cuda.synchronize()

    expected = world_size * (world_size + 1) / 2
    if value.item() != expected:
        raise RuntimeError(f"all_reduce={value.item()}, expected={expected}")

    print(
        f"host={socket.gethostname()} rank={rank}/{world_size} "
        f"device={torch.cuda.get_device_name()} all_reduce={value.item()} PASS",
        flush=True,
    )
    dist.barrier()
    dist.destroy_process_group()


if __name__ == "__main__":
    main()
