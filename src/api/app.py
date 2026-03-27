from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import exports_router, fields_router, tasks_router, templates_router
from src.core.config import API_CORS_ORIGINS, API_PREFIX, API_TITLE


def create_app() -> FastAPI:
    app = FastAPI(title=API_TITLE)
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


app = create_app()


if __name__ == "__main__":
    import uvicorn
    from src.core.config import API_HOST, API_PORT

    uvicorn.run("src.api.app:app", host=API_HOST, port=API_PORT, reload=False)
