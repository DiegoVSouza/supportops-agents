#!/usr/bin/env python3
"""Export the P00 golden set from an installed, versioned wheel for P01 comparison."""

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path

from supportops_foundation.testkit import generate_dataset


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--wheel-sha256", required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts/fixtures/p00-golden-1.0.1.json"))
    args = parser.parse_args()

    digest = hashlib.sha256(args.wheel.read_bytes()).hexdigest().upper()
    if digest != args.wheel_sha256.upper():
        raise SystemExit(f"wheel SHA-256 mismatch: expected {args.wheel_sha256}, got {digest}")
    version = importlib.metadata.version("supportops-foundation")
    if version != "1.0.1":
        raise SystemExit(f"unsupported P00 package version: {version}")
    dataset = generate_dataset(seed=7)
    payload = {
        "package": "supportops-foundation",
        "version": version,
        "source_commit": args.source_commit,
        "wheel_sha256": digest,
        "seed": dataset.seed,
        "case_count": len(dataset.golden_cases),
        "cases": [case.model_dump(mode="json") for case in dataset.golden_cases],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"exported={payload['case_count']} package={version} source_commit={args.source_commit} sha256={digest}")


if __name__ == "__main__":
    main()
