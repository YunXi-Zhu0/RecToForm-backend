from datetime import datetime
from pathlib import Path

from src.services.maintenance import OutputCleanupService


def test_seconds_until_next_run_before_schedule() -> None:
    service = OutputCleanupService(run_hour=4, run_minute=0)

    now = datetime(2026, 4, 1, 3, 30)

    assert service.seconds_until_next_run(now) == 1800


def test_seconds_until_next_run_after_schedule_rolls_to_next_day() -> None:
    service = OutputCleanupService(run_hour=4, run_minute=0)

    now = datetime(2026, 4, 1, 4, 30)

    assert service.seconds_until_next_run(now) == 23 * 3600 + 30 * 60


def test_cleanup_outputs_deletes_children_and_keeps_root(tmp_path: Path) -> None:
    output_dir = tmp_path / "outputs"
    nested_dir = output_dir / "api" / "tasks"
    nested_dir.mkdir(parents=True)
    (nested_dir / "task.json").write_text("{}", encoding="utf-8")
    (output_dir / "top-level.txt").write_text("data", encoding="utf-8")

    service = OutputCleanupService(output_dir=output_dir)

    deleted_entries = service.cleanup_outputs()

    assert deleted_entries == 2
    assert output_dir.is_dir()
    assert list(output_dir.iterdir()) == []
