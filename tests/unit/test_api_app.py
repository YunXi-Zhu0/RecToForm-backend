import asyncio

from src.api.app import create_app


class FakeStopEvent:
    def __init__(self) -> None:
        self.was_set = False

    def set(self) -> None:
        self.was_set = True


class FakeThread:
    def __init__(self) -> None:
        self.join_timeout = None

    def join(self, timeout=None) -> None:
        self.join_timeout = timeout


def test_create_app_starts_and_stops_output_cleanup_scheduler(monkeypatch) -> None:
    fake_thread = FakeThread()
    fake_stop_event = FakeStopEvent()
    started = {"value": False}

    def fake_start_output_cleanup_scheduler():
        started["value"] = True
        return fake_thread, fake_stop_event

    monkeypatch.setattr(
        "src.api.app._start_output_cleanup_scheduler",
        fake_start_output_cleanup_scheduler,
    )

    app = create_app(enable_output_cleanup_scheduler=True)

    async def run_lifespan() -> None:
        async with app.router.lifespan_context(app):
            return None

    asyncio.run(run_lifespan())

    assert started["value"] is True
    assert fake_stop_event.was_set is True
    assert fake_thread.join_timeout == 1
