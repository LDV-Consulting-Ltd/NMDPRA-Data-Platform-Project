"""Audit middleware: log request path, method, status, duration to meta.api_audit_log."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from time import time
from uuid import uuid4
from app.database import SessionLocal
from sqlalchemy import text


async def audit_middleware(request: Request, call_next):
    request_id = str(uuid4())
    request.state.request_id = request_id
    start = time()
    response = await call_next(request)
    duration_ms = int((time() - start) * 1000)
    try:
        db = SessionLocal()
        try:
            db.execute(
                text("""
                    INSERT INTO meta.api_audit_log (id, request_id, path, method, user_agent, query_params, response_status, duration_ms)
                    VALUES (:id, :request_id, :path, :method, :user_agent, :query_params, :response_status, :duration_ms)
                """),
                {
                    "id": str(uuid4()),
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "user_agent": request.headers.get("user-agent"),
                    "query_params": dict(request.query_params) if request.query_params else None,
                    "response_status": response.status_code,
                    "duration_ms": duration_ms,
                },
            )
            db.commit()
        finally:
            db.close()
    except Exception:
        pass
    return response
