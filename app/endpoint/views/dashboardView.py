from fastapi import APIRouter, Request
from starlette.responses import Response

from app.config.templates import templates

router = APIRouter()


@router.get("/")
def dashboard(request: Request) -> Response:
    return templates.TemplateResponse(request, "dashboard.html")
