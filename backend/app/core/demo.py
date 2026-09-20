from fastapi import HTTPException, Request, status

from app.core.config import Settings


DEMO_WRITE_BLOCKED_MESSAGE = "This operation is disabled in the public demo"


def get_request_settings(request: Request) -> Settings:
    return request.app.state.settings


def block_in_demo_mode(request: Request) -> None:
    if get_request_settings(request).demo_mode:
        raise HTTPException(status.HTTP_403_FORBIDDEN, DEMO_WRITE_BLOCKED_MESSAGE)
