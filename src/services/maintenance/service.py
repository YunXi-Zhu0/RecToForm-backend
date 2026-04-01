import logging
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from threading import Event
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from src.core.config import (
    DEFAULT_OUTPUT_DIR,
    OUTPUT_CLEANUP_HOUR,
    OUTPUT_CLEANUP_MINUTE,
    OUTPUT_CLEANUP_TIMEZONE,
)


logger = logging.getLogger(__name__)


class OutputCleanupService:
    def __init__(
        self,
        output_dir: Optional[Path] = None,
        timezone_name: str = OUTPUT_CLEANUP_TIMEZONE,
        run_hour: int = OUTPUT_CLEANUP_HOUR,
        run_minute: int = OUTPUT_CLEANUP_MINUTE,
    ) -> None:
        if not 0 <= run_hour <= 23:
            raise ValueError("Cleanup hour must be between 0 and 23.")
        if not 0 <= run_minute <= 59:
            raise ValueError("Cleanup minute must be between 0 and 59.")

        self.output_dir = Path(output_dir or DEFAULT_OUTPUT_DIR)
        self.timezone_name = timezone_name
        self.run_hour = run_hour
        self.run_minute = run_minute
        self.timezone = self._resolve_timezone(timezone_name)

    def cleanup_outputs(self) -> int:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        deleted_entries = 0
        for child in self.output_dir.iterdir():
            if child.is_symlink() or child.is_file():
                child.unlink()
            else:
                shutil.rmtree(child)
            deleted_entries += 1

        logger.info(
            "Cleanup completed for %s, deleted %s entries.",
            self.output_dir,
            deleted_entries,
        )
        return deleted_entries

    def seconds_until_next_run(self, now: Optional[datetime] = None) -> float:
        current_time = self._normalize_datetime(now or datetime.now(self.timezone))
        next_run = current_time.replace(
            hour=self.run_hour,
            minute=self.run_minute,
            second=0,
            microsecond=0,
        )
        if next_run <= current_time:
            next_run += timedelta(days=1)
        return (next_run - current_time).total_seconds()

    def run_forever(self, stop_event: Optional[Event] = None) -> None:
        logger.info(
            "Output cleanup scheduler started. target_dir=%s schedule=%02d:%02d timezone=%s",
            self.output_dir,
            self.run_hour,
            self.run_minute,
            self.timezone_name,
        )
        while True:
            sleep_seconds = self.seconds_until_next_run()
            logger.info("Next cleanup for %s is in %.0f seconds.", self.output_dir, sleep_seconds)
            if stop_event is None:
                time.sleep(sleep_seconds)
            elif stop_event.wait(timeout=sleep_seconds):
                logger.info("Output cleanup scheduler stopped before next run.")
                break
            try:
                self.cleanup_outputs()
            except Exception:
                logger.exception("Output cleanup failed for %s.", self.output_dir)

    def _resolve_timezone(self, timezone_name: str) -> ZoneInfo:
        try:
            return ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Invalid cleanup timezone: %s" % timezone_name) from exc

    def _normalize_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=self.timezone)
        return value.astimezone(self.timezone)
