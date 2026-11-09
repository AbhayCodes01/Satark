"""P0-05a: export a tiny model to ExecuTorch (.pte) and check it against PyTorch.

Run from the repo root with the venv active:
    python scripts\\p0_toy_export.py

STATUS: UNTESTED. Written from the ExecuTorch export flow; the first run on this
machine is the test. Paste the full output (or any error) back into the chat.
"""
import json
import sys
from importlib.metadata import version
from pathlib import Path

import torch


class Toy(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = torch.nn.Linear(8, 16)
        self.fc2 = torch.nn.Linear(16, 2)

    def forward(self, x):
        return self.fc2(torch.relu(self.fc1(x)))


def main() -> int:
    print("python     :", sys.version.split()[0])
    print("torch      :", torch.__version__)
    print("executorch :", version("executorch"))

    torch.manual_seed(0)
    model = Toy().eval()
    # Fixed, easy-to-reproduce input so the same values can be used on Android later.
    x = (torch.arange(8, dtype=torch.float32) / 8.0).unsqueeze(0)
    with torch.no_grad():
        eager_out = model(x)

    from executorch.backends.xnnpack.partition.xnnpack_partitioner import XnnpackPartitioner
    from executorch.exir import to_edge_transform_and_lower
    from torch.export import export

    exported = export(model, (x,))
    et_program = to_edge_transform_and_lower(
        exported, partitioner=[XnnpackPartitioner()]
    ).to_executorch()

    out_dir = Path("build")
    out_dir.mkdir(exist_ok=True)
    pte_path = out_dir / "toy.pte"
    pte_path.write_bytes(et_program.buffer)
    print(f"wrote {pte_path} ({pte_path.stat().st_size} bytes)")

    # Run the .pte with the ExecuTorch Python runtime and compare with eager PyTorch.
    from executorch.runtime import Runtime

    runtime = Runtime.get()
    program = runtime.load_program(str(pte_path))
    method = program.load_method("forward")
    et_out = method.execute([x])[0]

    max_diff = (et_out - eager_out).abs().max().item()
    print("eager out  :", eager_out.flatten().tolist())
    print("pte out    :", et_out.flatten().tolist())
    print("max |diff| :", max_diff)

    evidence = {
        "input": x.flatten().tolist(),
        "expected_output_pte": et_out.flatten().tolist(),
        "expected_output_eager": eager_out.flatten().tolist(),
        "max_abs_diff": max_diff,
        "torch": torch.__version__,
        "executorch": version("executorch"),
    }
    ev_path = Path("docs/evidence/P0-05-toy-expected.json")
    ev_path.parent.mkdir(parents=True, exist_ok=True)
    ev_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print("saved      :", ev_path)

    print("RESULT     :", "PASS" if max_diff < 1e-4 else "CHECK DIFFERENCE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
