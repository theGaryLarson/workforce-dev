"""CLI entrypoint and run coordinator."""

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent run coordinator")
    parser.add_argument("action", choices=["run"], help="Execute an agent workflow")
    parser.add_argument("agent", choices=["intake", "reconciliation", "export"], help="Agent name")
    parser.add_argument("--platform", default="minimal", help="Agent platform to use")
    parser.add_argument("--partner", default="demo", help="Partner identifier")
    parser.add_argument("--quarter", default="Q1", help="Reporting period")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parents[1]
    run_id = f"{args.partner}-{args.quarter}-{args.platform}"
    evidence_dir = base_dir / "core" / "audit" / "runs" / run_id
    evidence_dir.mkdir(parents=True, exist_ok=True)
    print(f"Initialized evidence bundle at {evidence_dir}")


if __name__ == "__main__":
    main()
