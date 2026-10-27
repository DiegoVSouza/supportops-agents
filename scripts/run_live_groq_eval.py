"""Legacy smoke entrypoint: inspect the current allocation boundary offline."""

from __future__ import annotations

import argparse
import json


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    print(
        json.dumps(
            {
                "status": "INCOMPLETE",
                "reason": "legacy_smoke_not_allocated; accounted campaign dispatch is required",
                "runner": "core",
                "provider_accessed": False,
                "credentials_read": False,
                "generation_calls": 0,
                "authorized_paid_spend_usd": "0.00",
                "safe_next_step": "uv run --locked python scripts/run_live_campaign.py --stage pilot --dry-run",
                "quality_and_promotion": "PENDING",
            },
            sort_keys=True,
        )
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
