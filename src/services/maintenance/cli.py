import argparse
import logging
from pathlib import Path

from src.services.maintenance.service import OutputCleanupService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Delete the contents under the outputs directory on a fixed daily schedule.",
    )
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run cleanup immediately once and exit.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Override the outputs directory path.",
    )
    return parser


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    args = build_parser().parse_args()
    service = OutputCleanupService(output_dir=args.output_dir)
    if args.run_once:
        service.cleanup_outputs()
        return
    service.run_forever()


if __name__ == "__main__":
    main()
