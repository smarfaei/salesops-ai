from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


class DemoWriteRateLimitMiddleware(BaseHTTPMiddleware):
    """Small per-process limiter for state-changing public-demo requests."""

    def __init__(self, app, *, requests: int, window_seconds: int) -> None:
        super().__init__(app)
        self.requests = requests
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            client = request.client.host if request.client else "unknown"
            key = client
            now = monotonic()
            with self._lock:
                events = self._events[key]
                cutoff = now - self.window_seconds
                while events and events[0] <= cutoff:
                    events.popleft()
                if len(events) >= self.requests:
                    retry_after = max(1, int(self.window_seconds - (now - events[0])))
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": {
                                "code": "rate_limit_exceeded",
                                "message": "Too many demo write requests; try again shortly",
                            }
                        },
                        headers={"Retry-After": str(retry_after)},
                    )
                events.append(now)
        return await call_next(request)


class LoginRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, requests: int, window_seconds: int) -> None:
        super().__init__(app)
        self.requests = requests
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method == "POST" and request.url.path == "/auth/login":
            client = request.client.host if request.client else "unknown"
            now = monotonic()
            with self._lock:
                events = self._events[client]
                cutoff = now - self.window_seconds
                while events and events[0] <= cutoff:
                    events.popleft()
                if len(events) >= self.requests:
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": {
                                "code": "login_rate_limit_exceeded",
                                "message": "Too many login attempts; try again shortly",
                            }
                        },
                        headers={"Retry-After": str(self.window_seconds)},
                    )
                events.append(now)
        return await call_next(request)
