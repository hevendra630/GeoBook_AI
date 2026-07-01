from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI, Request

from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler

from slowapi.errors import RateLimitExceeded

from slowapi.middleware import SlowAPIMiddleware

from slowapi.util import get_remote_address

from app.api.router import api_router

from app.core.config import settings

from app.core.logging import configure_logging, logger

from app.db.base import Base

from app.db.session import engine

from sqlalchemy import create_engine

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_default])

def create_app() -> FastAPI:

    configure_logging(settings.log_level)

    if settings.database_url.startswith("sqlite"):
        sync_url = settings.database_url.replace("sqlite+aiosqlite://", "sqlite://")
        sync_engine = create_engine(sync_url)
        Base.metadata.create_all(bind=sync_engine)
        sync_engine.dispose()

    app = FastAPI(title=settings.app_name)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ------------------------------------------------------------------ #
    # Global 500 handler — registered as the OUTERMOST middleware so that  #
    # the CORS middleware (added next) always runs on the way back out,    #
    # stamping Access-Control-Allow-Origin on every response including     #
    # unhandled 500s.  Using @app.exception_handler(Exception) instead    #
    # would fire *inside* the CORS middleware and produce CORS-less 500s. #
    # ------------------------------------------------------------------ #
    @app.middleware("http")
    async def global_exception_handler(request: Request, call_next):
        import traceback
        try:
            return await call_next(request)
        except Exception:
            logger.exception("Unhandled exception", path=request.url.path)
            try:
                with open("critical_error.log", "a") as f:
                    f.write(f"\n--- ERROR AT {datetime.now()} ---\n")
                    f.write(traceback.format_exc())
            except Exception:
                pass
            # CORS middleware runs *outside* this handler (registered after),
            # so the 500 response will automatically receive CORS headers.
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error."},
            )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(SlowAPIMiddleware)

    app.include_router(api_router)

    @app.get("/health")

    async def health() -> dict[str, str]:

        return {"status": "ok"}

    @app.middleware("http")

    async def request_logging(request: Request, call_next):

        logger.info(

            "http.request.headers",

            origin=request.headers.get("origin"),

            auth=request.headers.get("authorization")[:15] + "..." if request.headers.get("authorization") else None,

        )

        response = await call_next(request)

        logger.info(

            "http.response",

            method=request.method,

            path=request.url.path,

            status_code=response.status_code,

        )

        return response

    return app

app = create_app()

