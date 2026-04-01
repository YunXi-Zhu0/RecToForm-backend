from contextlib import asynccontextmanager
from threading import Event, Thread

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import exports_router, fields_router, tasks_router, templates_router
from src.core.config import API_CORS_ORIGINS, API_PREFIX, API_TITLE
from src.services.maintenance import OutputCleanupService


def _start_output_cleanup_scheduler() -> tuple[Thread, Event]:
    stop_event = Event()
    service = OutputCleanupService()
    thread = Thread(
        target=service.run_forever,
        kwargs={"stop_event": stop_event},
        name="output-cleanup-scheduler",
        daemon=True,
    )
    thread.start()
    return thread, stop_event


def create_app(enable_output_cleanup_scheduler: bool = False) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        cleanup_thread = None
        cleanup_stop_event = None
        if enable_output_cleanup_scheduler:
            cleanup_thread, cleanup_stop_event = _start_output_cleanup_scheduler()

        try:
            yield
        finally:
            if cleanup_stop_event is not None:
                cleanup_stop_event.set()
            if cleanup_thread is not None:
                cleanup_thread.join(timeout=1)

    app = FastAPI(title=API_TITLE, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=API_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["health"])
    def health_check():
        return {"status": "ok"}

    app.include_router(templates_router, prefix=API_PREFIX)
    app.include_router(fields_router, prefix=API_PREFIX)
    app.include_router(tasks_router, prefix=API_PREFIX)
    app.include_router(exports_router, prefix=API_PREFIX)
    return app


app = create_app(enable_output_cleanup_scheduler=True)


if __name__ == "__main__":
    import uvicorn
    from src.core.config import API_HOST, API_PORT

    uvicorn.run("src.api.app:app", host=API_HOST, port=API_PORT, reload=False)
