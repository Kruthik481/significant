"""HTTP API: run analyses on uploads or built-in samples, fetch shared reports, size experiments."""

import asyncio
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Annotated, Any, Literal

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.analysis import AnalysisOptions, analyze
from app.ingest import IngestError, parse_csv
from app.limits import RateLimiter
from app.samples import SAMPLES, sample_csv
from app.settings import Settings
from app.stats.power import sample_size
from app.store import Store

log = logging.getLogger("significant")

RETENTION = timedelta(days=90)
NAME_LIMIT = 120
RATE_WINDOW_SECONDS = 3600


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, headers: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.status, self.code, self.message, self.headers = status, code, message, headers


class PowerRequest(BaseModel):
    baseline: float
    mde: float
    alpha: float = 0.05
    power: float = 0.8
    kind: Literal["binary", "continuous"] = "binary"
    sd: float | None = None


def _envelope(status: int, code: str, message: str, headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status, headers=headers)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    # Render's proxy appends the address it saw; anything to its left is client-supplied
    last = forwarded.split(",")[-1].strip()
    return last or (request.client.host if request.client else "unknown")


def create_app(settings: Settings) -> FastAPI:
    limiter = RateLimiter(settings.rate_limit_per_hour, window=RATE_WINDOW_SECONDS)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        store = await Store.open(settings.database_url, settings.db_schema)
        await store.migrate()
        purged = await store.purge(RETENTION)
        if purged:
            log.info("purged %d expired reports", purged)
        app.state.store = store
        try:
            yield
        finally:
            await store.close()

    app = FastAPI(title="Significant", summary="A/B test analyzer API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.web_origin],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.exception_handler(ApiError)
    async def api_error(_: Request, e: ApiError) -> JSONResponse:
        return _envelope(e.status, e.code, e.message, e.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, e: RequestValidationError) -> JSONResponse:
        first = e.errors()[0] if e.errors() else {}
        where = ".".join(str(p) for p in first.get("loc", ()) if p not in ("body", "query", "path"))
        return _envelope(422, "bad_option", f"{where}: {first.get('msg', 'invalid value')}".strip(": "))

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, e: StarletteHTTPException) -> JSONResponse:
        code = "not_found" if e.status_code == 404 else "http_error"
        return _envelope(e.status_code, code, str(e.detail))

    @app.exception_handler(Exception)
    async def unexpected(_: Request, e: Exception) -> JSONResponse:
        log.exception("unhandled error", exc_info=e)
        return _envelope(500, "internal_error", "Something went wrong on our side. Please try again.")

    def store(request: Request) -> Store:
        result: Store = request.app.state.store
        return result

    def options(alpha: float | None, expected_split: float | None, tau: float | None) -> AnalysisOptions:
        try:
            return AnalysisOptions(
                alpha=0.05 if alpha is None else alpha,
                expected_split=0.5 if expected_split is None else expected_split,
                tau=tau,
            )
        except ValueError as e:
            raise ApiError(422, "bad_option", str(e)) from e

    # one analysis at a time keeps peak memory inside the 512 MB container
    analysis_slot = asyncio.Semaphore(1)

    def check_rate(request: Request) -> None:
        allowed, retry = limiter.allow(_client_ip(request))
        if not allowed:
            raise ApiError(
                429,
                "rate_limited",
                "Too many analyses from this address; try again later.",
                {"Retry-After": str(retry)},
            )

    async def run(
        request: Request, data: bytes, control: str | None, opts: AnalysisOptions, name: str, source: str
    ) -> JSONResponse:
        def work() -> dict[str, Any]:
            # size was already checked at the boundary; built-in samples are not uploads
            return analyze(parse_csv(data, control, max_bytes=len(data)), opts).model_dump(mode="json")

        try:
            async with analysis_slot:
                report = await asyncio.to_thread(work)
        except IngestError as e:
            raise ApiError(413 if e.code == "too_large" else 400, e.code, e.message) from e
        rid = await store(request).save(name[:NAME_LIMIT], source, report)
        return JSONResponse({"id": rid, "report": report}, status_code=201)

    @app.post("/analyses", status_code=201)
    async def analyze_upload(
        request: Request,
        file: Annotated[UploadFile, File()],
        name: Annotated[str | None, Form()] = None,
        control: Annotated[str | None, Form()] = None,
        expected_split: Annotated[float | None, Form()] = None,
        alpha: Annotated[float | None, Form()] = None,
        tau: Annotated[float | None, Form()] = None,
    ) -> JSONResponse:
        opts = options(alpha, expected_split, tau)
        data = await file.read(settings.max_upload_bytes + 1)
        if len(data) > settings.max_upload_bytes:
            limit_mb = settings.max_upload_bytes / (1024 * 1024)
            raise ApiError(413, "too_large", f"The file is larger than {limit_mb:g} MB.")
        check_rate(request)
        title = (name or "").strip() or (file.filename or "Uploaded experiment")
        return await run(request, data, control, opts, title, "upload")

    @app.post("/analyses/samples/{name}", status_code=201)
    async def analyze_sample(request: Request, name: str) -> JSONResponse:
        info = SAMPLES.get(name)
        if info is None:
            raise ApiError(404, "unknown_sample", f"No sample named '{name}'.")
        check_rate(request)
        return await run(request, sample_csv(name), None, AnalysisOptions(), info.title, f"sample:{name}")

    @app.get("/analyses/{rid}")
    async def get_report(request: Request, rid: str) -> dict[str, Any]:
        found = await store(request).get(rid)
        if found is None:
            raise ApiError(404, "not_found", "This report does not exist or has expired.")
        return {
            "id": found.id,
            "name": found.name,
            "source": found.source,
            "created_at": found.created_at.isoformat(),
            "report": found.report,
        }

    @app.get("/samples")
    async def list_samples() -> list[dict[str, str]]:
        return [
            {"name": s.name, "title": s.title, "description": s.description, "truth": s.truth}
            for s in SAMPLES.values()
        ]

    @app.get("/samples/{name}.csv")
    async def download_sample(name: str) -> Response:
        if name not in SAMPLES:
            raise ApiError(404, "unknown_sample", f"No sample named '{name}'.")
        return Response(
            sample_csv(name),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={name}.csv"},
        )

    @app.post("/power")
    async def power(body: PowerRequest) -> dict[str, int]:
        try:
            n = sample_size(body.baseline, body.mde, body.alpha, body.power, body.kind, body.sd)
        except ValueError as e:
            raise ApiError(422, "bad_option", str(e)) from e
        return {"n_per_arm": n, "total": 2 * n}

    @app.get("/healthz")
    async def healthz() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/readyz")
    async def readyz(request: Request) -> JSONResponse:
        try:
            await store(request).ping()
        except Exception:
            log.exception("readiness check failed")
            return JSONResponse({"ok": False, "postgres": False}, status_code=503)
        return JSONResponse({"ok": True, "postgres": True})

    return app


def app_from_env() -> FastAPI:
    logging.basicConfig(level=logging.INFO)
    return create_app(Settings.from_env(os.environ))
