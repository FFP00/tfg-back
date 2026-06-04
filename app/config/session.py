import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from app.config.settings import settings

_ALGORITHM    = "HS256"
_COOKIE_NAME  = "admin_token"
_LOGIN_PATH   = "/views/login"
_VIEWS_PREFIX = "/views"

_PUBLIC_PREFIXES = (_LOGIN_PATH,)


class AdminSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if path.startswith(_VIEWS_PREFIX) and not any(
            path.startswith(p) for p in _PUBLIC_PREFIXES
        ):
            token = request.cookies.get(_COOKIE_NAME)
            if not token or not _valid_admin_token(token):
                return RedirectResponse(_LOGIN_PATH, status_code=302)
        return await call_next(request)


def _valid_admin_token(token: str) -> bool:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[_ALGORITHM])
        return payload.get("role") == "admin"
    except jwt.InvalidTokenError:
        return False
