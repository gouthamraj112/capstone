from contextlib import asynccontextmanager
import logging

import json
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import agents, analytics, anomalies, dashboard, evaluation, forecast, query
from app.core.config import settings
from app.core.database import ensure_indexes


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        ensure_indexes()
    except Exception:
        pass
    yield


allowed_origins = [settings.frontend_url, "http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"]
app = FastAPI(title="Smart Grid Energy Intelligence", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def envelope_middleware(request: Request, call_next):
    response = await call_next(request)
    if not request.url.path.startswith("/api") or not response.headers.get("content-type", "").startswith("application/json"):
        return response
    if response.status_code == 200:
        body = [chunk async for chunk in response.body_iterator]
        try:
            raw_text = b"".join(body).decode("utf-8")
            payload = json.loads(raw_text)
            if isinstance(payload, dict):
                data_content = payload.get("data") if "data" in payload else {k: v for k, v in payload.items() if k not in ("success", "metadata", "error")}
                wrapped = {
                    "success": payload.get("success", True),
                    "data": data_content,
                    "metadata": payload.get("metadata", {}),
                    "error": payload.get("error", None),
                    **payload
                }
                new_body = json.dumps(wrapped).encode("utf-8")
                headers = dict(response.headers)
                headers["content-length"] = str(len(new_body))
                return Response(content=new_body, status_code=200, headers=headers, media_type="application/json")
        except Exception:
            return Response(content=b"".join(body), status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)
    return response


app.include_router(dashboard.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(anomalies.router, prefix="/api")
app.include_router(forecast.router, prefix="/api")
app.include_router(query.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(evaluation.router, prefix="/api")


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    code = {400: "BAD_REQUEST", 404: "NOT_FOUND", 422: "VALIDATION_ERROR", 503: "SERVICE_UNAVAILABLE"}.get(exc.status_code, "HTTP_ERROR")
    return JSONResponse(status_code=exc.status_code, content={
        "success": False, "data": None, "metadata": {},
        "error": {"code": code, "message": str(exc.detail)},
    }, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={
        "success": False, "data": None, "metadata": {},
        "error": {"code": "VALIDATION_ERROR", "message": "The request parameters are invalid."},
    })


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception):
    logging.getLogger("uvicorn.error").error("Unhandled API error", exc_info=(type(exc), exc, exc.__traceback__))
    return JSONResponse(status_code=500, content={
        "success": False, "data": None, "metadata": {},
        "error": {"code": "INTERNAL_ERROR", "message": "The request could not be completed."},
    })
